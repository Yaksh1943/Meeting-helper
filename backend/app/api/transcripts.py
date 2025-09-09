from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.models.db import get_session
from app.models.schema import TranscriptSegment, Summary,SummaryType
from app.services.summarizer import summarize_window

router = APIRouter()

@router.post("/{meeting_id}/ingest-transcript")
def ingest_transcript(meeting_id: int, data: dict,session: Session = Depends(get_session)):
    ts_start = data.get("ts_start")
    ts_end = data.get("ts_end")
    speaker = data.get("speaker")
    text = data.get("text")
    if not text:
        raise HTTPException(400 , "Missing transcripts text")
    
    seg = TranscriptSegment(
        meeting_id=meeting_id, ts_start=ts_start, ts_end=ts_end, speaker=speaker,text=text
    )
    session.add(seg)
    session.commit()
    session.refresh(seg)

    # Generate rolling summary
    summary_text = summarize_window(text)
    summary = Summary(
        meeting_id=meeting_id, start_min=ts_start or 0, end_min=ts_end or 0, type=SummaryType.TIMELINE, text=summary_text
    )
    session.add(summary)
    session.commit()

    return {"segment_id": seg.id, "summary": summary_text}
