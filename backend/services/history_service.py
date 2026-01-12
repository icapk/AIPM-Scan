"""
面试历史记录服务
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from database import Candidate, Interview, InterviewRound, QuestionRecord, CompanyScale
from models.schemas import EvaluationResult
import json

class HistoryService:
    
    def create_candidate(self, db: Session, name: str = "Unknown", resume_text: str = None) -> Candidate:
        candidate = Candidate(name=name, resume_text=resume_text)
        db.add(candidate)
        db.commit()
        db.refresh(candidate)
        return candidate

    def create_interview(
        self, 
        db: Session, 
        candidate_id: int, 
        job_title: str, 
        jd_text: str,
        company_scale: str
    ) -> Interview:
        interview = Interview(
            candidate_id=candidate_id,
            job_title=job_title,
            jd_text=jd_text,
            company_scale=company_scale
        )
        db.add(interview)
        db.commit()
        db.refresh(interview)
        return interview

    def create_round(self, db: Session, interview_id: int, round_number: int) -> InterviewRound:
        round_obj = InterviewRound(
            interview_id=interview_id,
            round_number=round_number
        )
        db.add(round_obj)
        db.commit()
        db.refresh(round_obj)
        return round_obj

    def add_questions(
        self, 
        db: Session, 
        round_id: int, 
        questions: List[Dict[str, Any]]
    ):
        records = []
        for q in questions:
            record = QuestionRecord(
                round_id=round_id,
                text=q["text"],
                dimension=q["dimension"],
                difficulty=q["difficulty"],
                reference_context=q.get("reference_context")
            )
            records.append(record)
        
        db.add_all(records)
        db.commit()

    def update_answer_and_evaluation(
        self, 
        db: Session, 
        round_id: int, 
        question_text: str, # Using text as identifier for simplicity in MVP, ideally use ID
        answer: str,
        evaluation: Dict[str, Any]
    ):
        # Find the question record
        # Note: In a real app we should use ID. For MVP we might need to query by round_id + text
        record = db.query(QuestionRecord).filter(
            QuestionRecord.round_id == round_id,
            QuestionRecord.text == question_text
        ).first()
        
        if record:
            record.answer = answer
            record.score = evaluation.get("score")
            record.evaluation_json = evaluation
            db.commit()

    def get_candidate_history(self, db: Session, candidate_id: int) -> List[Interview]:
        return db.query(Interview).filter(Interview.candidate_id == candidate_id).all()

    def get_all_interviews(self, db: Session) -> List[Interview]:
         return db.query(Interview).order_by(Interview.created_at.desc()).all()

history_service = HistoryService()
