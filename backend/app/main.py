from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from dotenv import load_dotenv
import logging

from app.api import meetings, transcripts, summaries, qa, livekit
from app.models.db import init_db, engine
from app.models.schema import Meeting, TranscriptSegment, Summary, SummaryType
from app.services.summarizer import summarize_window
from sqlmodel import Session, select

load_dotenv()
app = FastAPI(title="Meeting Helper API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(meetings.router, prefix="/api/meetings", tags=["meetings"])
app.include_router(transcripts.router, prefix="/api/meetings", tags=["transcripts"])
app.include_router(summaries.router, prefix="/api/meetings", tags=["summaries"])
app.include_router(qa.router, prefix="/api/meetings", tags=["qa"])
app.include_router(livekit.router)

scheduler = BackgroundScheduler()

def generate_live_summaries():
    with Session(engine) as db:
        active_meetings = db.exec(
            select(Meeting).where(Meeting.start_ts != None, Meeting.end_ts == None)
        ).all()

        for meeting in active_meetings:
            # last summary checkpoint
            last_summary = db.exec(
                select(Summary)
                .where(Summary.meeting_id == meeting.id, Summary.type == SummaryType.SUMMARY)
                .order_by(Summary.end_min.desc())
            ).first()
            last_ts = last_summary.end_min if last_summary else meeting.start_ts or 0

            # transcripts since last summary
            new_segments = db.exec(
                select(TranscriptSegment)
                .where(
                    TranscriptSegment.meeting_id == meeting.id,
                    TranscriptSegment.ts_end > last_ts,
                )
                .order_by(TranscriptSegment.ts_start)
            ).all()

            if not new_segments:
                continue

            text = " ".join(seg.text for seg in new_segments)
            summary_text = summarize_window(text)

            summary = Summary(
                meeting_id=meeting.id,
                start_min=new_segments[0].ts_start,
                end_min=new_segments[-1].ts_end,
                type=SummaryType.SUMMARY,
                text=summary_text,
            )
            db.add(summary)
            db.commit()
            logging.info(f"Generated live summary for meeting {meeting.id}")

@app.on_event("startup")
def on_startup():
    init_db()
    scheduler.add_job(generate_live_summaries, IntervalTrigger(minutes=2))
    scheduler.start()

@app.on_event("shutdown")
def on_shutdown():
    scheduler.shutdown()
