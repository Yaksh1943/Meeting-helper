from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select 
from app.models.db import get_session
from app.models.schema import Meeting, Participant, CreateMeetingRequest, InviteParticipantsRequest, SummaryType
from app.services.livekit_tokens import generate_room_token
from app.services.email_service import send_email
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/")
def create_meeting(data: CreateMeetingRequest, session: Session = Depends(get_session)):
    title = getattr(data, "title", None)
    host_email = getattr(data, "host_email", None)

    if not title or not host_email:
        # Use named args for clarity
        raise HTTPException(status_code=400, detail="Missing title or host_email")

    meeting = Meeting(title=title, host_email=host_email)
    session.add(meeting)
    session.commit()
    session.refresh(meeting)

    token, room = generate_room_token(meeting.id, host_email)
    return {"meeting_id": meeting.id, "room": room, "token": token}


@router.post("/{meeting_id}/invite")
def invite_participants(meeting_id: int, data:InviteParticipantsRequest, session: Session = Depends(get_session)):
    emails = data.emails
    meeting = session.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(404, "Meeting not found")
    
    for email in emails:
        p = Participant(meeting_id=meeting_id, name= email.split("@")[0], email=email)
        session.add(p)
        send_email(email, f"Invitation to {meeting.title}",f"Join meeting {meeting.id}")
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


@router.post("/{meeting_id}/end")
def end_meeting(meeting_id: int, session: Session = Depends(get_session)):
    from app.models.schema import TranscriptSegment, Summary, ActionItem
    from app.services.summarizer import final_summary
    from app.services.embeddings import add_to_index
    from app.utils.time import now_ts

    meeting = session.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(404, "Meeting not found")
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
    session.commit()

    add_to_index(meeting_id, summary_data["summary"])

    send_email(meeting.host_email, "Final Meeting Summary", str(summary_data))

    logger.info("Endpoint return data: %s", summary_data)

    return {"status": "ended", "summary": summary_data}

