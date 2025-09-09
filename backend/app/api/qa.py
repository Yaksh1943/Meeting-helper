from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from app.models.db import get_session
from app.models.schema import Summary, SummaryType
from app.services.embeddings import query_index
from app.services.summarizer import rag_answer

router = APIRouter()


@router.post("/{meeting_id}/ask")
def ask_question(meeting_id: int, data: dict, session: Session = Depends(get_session)):
    question = data.get("question")
    if not question:
        return {"answer": "Question missing."}

    # Get the latest final summary
    final_summary = session.exec(
        select(Summary)
        .where(Summary.meeting_id == meeting_id, Summary.type == SummaryType.FINAL)
        .order_by(Summary.id.desc())
    ).first()

    if not final_summary:
        return {"answer": "Final summary not available yet."}

    context = final_summary.text
    answer = rag_answer(question, context)
    return {"answer": answer}
