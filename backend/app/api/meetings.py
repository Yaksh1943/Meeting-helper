from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.models.db import get_session
from app.models.schema import Meeting, Participant, CreateMeetingRequest, InviteParticipantsRequest, SummaryType
from app.services.livekit_tokens import generate_room_token
from app.services.email_service import send_email
from app.utils.config import get_env
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("")
def create_meeting(data: CreateMeetingRequest, session: Session = Depends(get_session)):
    title = getattr(data, "title", None)
    host_email = getattr(data, "host_email", None)

    if not title or not host_email:
        raise HTTPException(status_code=400, detail="Missing title or host_email")

    meeting = Meeting(title=title, host_email=host_email)
    session.add(meeting)
    session.commit()
    session.refresh(meeting)

    token, room = generate_room_token(meeting.id, host_email)
    return {"meeting_id": meeting.id, "room": room, "token": token}


@router.post("/{meeting_id}/invite")
def invite_participants(meeting_id: int, data: InviteParticipantsRequest, session: Session = Depends(get_session)):
    emails = data.emails
    meeting = session.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(404, "Meeting not found")

    for email in emails:
        p = Participant(meeting_id=meeting_id, name=email.split("@")[0], email=email)
        session.add(p)
        frontend_url = get_env("FRONTEND_URL", "http://localhost:3000").rstrip("/")
        join_url = f"{frontend_url}/rooms/{meeting.id}"
        send_email(
            email,
            f"You're invited: {meeting.title}",
            f"You've been invited to a meeting: {meeting.title}\n\nJoin here: {join_url}\n\nSee you there!"
        )
    session.commit()
    return {"invited": emails}


@router.post("/{meeting_id}/start")
def start_meeting(meeting_id: int, session: Session = Depends(get_session)):
    meeting = session.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(404, "Meeting not found")
    from app.utils.time import now_ts

    meeting.start_ts = now_ts()
    session.add(meeting)
    session.commit()
    return {"status": "started"}


@router.post("/{meeting_id}/remind-missing")
def remind_missing(meeting_id: int, session: Session = Depends(get_session)):
    participants = session.exec(select(Participant).where(Participant.meeting_id == meeting_id)).all()
    missing = [p for p in participants if not p.reminder_sent]
    for p in missing:
        send_email(p.email, "Meeting Reminder", "You have a meeting to attend.")
        p.reminder_sent = True
        session.add(p)
    session.commit()
    return {"reminded": [p.email for p in missing]}


def _format_summary_email(summary_data: dict) -> str:
    """Builds a readable plain-text email body instead of dumping a raw dict."""
    parts = [f"Meeting Summary:\n\n{summary_data.get('summary', '')}"]

    action_items = summary_data.get("action_items") or []
    if action_items:
        parts.append("Action Items:\n" + "\n".join(f"- {item}" for item in action_items))

    decisions = summary_data.get("decisions") or []
    if decisions:
        parts.append("Decisions:\n" + "\n".join(f"- {d}" for d in decisions))

    return "\n\n".join(parts)


@router.post("/{meeting_id}/end")
def end_meeting(meeting_id: int, session: Session = Depends(get_session)):
    from app.models.schema import TranscriptSegment, Summary, ActionItem, Decision
    from app.services.summarizer import final_summary
    from app.services.chunking import chunk_text
    from app.services.embeddings import add_to_index
    from app.utils.time import now_ts

    meeting = session.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(404, "Meeting not found")
    if meeting.end_ts is not None:
        return {"status": "ended", "detail": "Meeting was already ended"}
    meeting.end_ts = now_ts()

    transcript_segments = session.exec(
        select(TranscriptSegment).where(TranscriptSegment.meeting_id == meeting_id)
    ).all()
    full_text = " ".join([seg.text for seg in transcript_segments])

    summary_data = final_summary(full_text)
    summary = Summary(
        meeting_id=meeting_id, start_min=0, end_min=0, type=SummaryType.FINAL, text=summary_data["summary"]
    )
    session.add(summary)
    for ai in summary_data.get("action_items", []):
        session.add(ActionItem(meeting_id=meeting_id, text=ai))
    for d in summary_data.get("decisions", []):
        session.add(Decision(meeting_id=meeting_id, text=d))
    session.commit()

    # Real RAG indexing: chunk the actual transcript (not just the summary)
    # so Q&A can retrieve specific details, not only high-level points.
    for chunk in chunk_text(full_text, max_len=120):
        add_to_index(meeting_id, chunk)

    add_to_index(meeting_id, summary_data["summary"])

    send_email(meeting.host_email, "Final Meeting Summary", _format_summary_email(summary_data))

    logger.info("Endpoint return data: %s", summary_data)

    return {"status": "ended", "summary": summary_data}
