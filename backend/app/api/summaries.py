from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.models.db import get_session
from app.models.schema import Summary,ActionItem, Participant, SummaryType
from app.services.email_service import send_email

router = APIRouter()


@router.get("/{meeting_id}/summaries")
def get_summaries(meeting_id: int, session: Session = Depends(get_session)):
    summaries = session.exec(select(Summary).where(Summary.meeting_id == meeting_id)).all()
    return summaries

@router.get("/{meeting_id}/final-summary")
def get_final_summary(meeting_id: int, session: Session = Depends(get_session)):
    summary = session.exec(
        select(Summary).where(Summary.meeting_id == meeting_id, Summary.type == SummaryType.FINAL)
    ).first()
    if not summary:
        raise HTTPException(404, "Final summary not found")

    from app.models.schema import ActionItem
    action_items = session.exec(
        select(ActionItem.text).where(ActionItem.meeting_id == meeting_id)
    ).all()

    return {
        "summary": summary.text,
        "action_items": action_items,
        "decisions": [] 
    }


@router.post("/{meeting_id}/send-summary")
def send_final_summary(meeting_id: int, session: Session = Depends(get_session)):
    # Get final summary
    summary = session.exec(
        select(Summary).where(Summary.meeting_id == meeting_id, Summary.type == SummaryType.FINAL)
    ).first()

    if not summary:
        raise HTTPException(404, "Final summary not found")

    # Get action items
    action_items = session.exec(
        select(ActionItem.text).where(ActionItem.meeting_id == meeting_id)
    ).all()

    # Get participants
    participants = session.exec(
        select(Participant).where(Participant.meeting_id == meeting_id)
    ).all()
    if not participants:
        raise HTTPException(404, "No participants found")

    # Construct email body
    body = f"Final Meeting Summary:\n\n{summary.text}\n\n"
    if action_items:
        body += "Action Items:\n" + "\n".join([f"- {ai}" for ai in action_items])

    # Send email to all participants
    for p in participants:
        send_email(
            p.email,
            f"Final Summary for Meeting {meeting_id}",
            body
        )

    return {"status": "sent", "recipients": [p.email for p in participants]}
