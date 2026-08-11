from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.models.db import get_session
from app.models.schema import TranscriptSegment

router = APIRouter()


@router.post("/{meeting_id}/ingest-transcript")
def ingest_transcript(meeting_id: int, data: dict, session: Session = Depends(get_session)):
    ts_start = data.get("ts_start")
    ts_end = data.get("ts_end")
    speaker = data.get("speaker")
    text = data.get("text")
    if not text:
        raise HTTPException(400, "Missing transcripts text")

    seg = TranscriptSegment(
        meeting_id=meeting_id, ts_start=ts_start, ts_end=ts_end, speaker=speaker, text=text
    )
    session.add(seg)
    session.commit()
    session.refresh(seg)

    # No per-utterance summarization here. The background scheduler in
    # main.py aggregates all new segments into a real timeline summary
    # every 2 minutes, giving the LLM enough context to summarize
    # meaningfully instead of choking on single short fragments.
    return {"segment_id": seg.id}