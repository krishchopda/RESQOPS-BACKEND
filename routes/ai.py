from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from services.ai_assistant import ask_ai_assistant
from pydantic import BaseModel

router = APIRouter(prefix="/ai", tags=["AI Assistant"])

class QuestionRequest(BaseModel):
    question: str

@router.post("/ask")
def ask(request: QuestionRequest, db: Session = Depends(get_db)):
    answer = ask_ai_assistant(request.question, db)
    return {"question": request.question, "answer": answer}