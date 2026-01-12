"""
数据库连接与模型定义
使用 SQLite + SQLAlchemy
"""
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, ForeignKey, JSON, DateTime, Enum as SAEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from config import BASE_DIR
import enum

# 数据库文件路径
DB_PATH = os.path.join(BASE_DIR, "aipm.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} # SQLite 特定配置
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# --- Enums ---

class CompanyScale(str, enum.Enum):
    STARTUP = "初创公司"
    SMALL = "小型公司"
    MEDIUM = "中型公司"
    LARGE = "大型公司"

class DifficultyLevel(str, enum.Enum):
    BASIC = "基础"
    INTERMEDIATE = "进阶"
    ADVANCED = "高级"

# --- Models ---

class Candidate(Base):
    """候选人表"""
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, default="Unknown") 
    resume_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    
    interviews = relationship("Interview", back_populates="candidate")

class Interview(Base):
    """面试会话表"""
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"))
    job_title = Column(String)
    jd_text = Column(Text)
    company_scale = Column(String, default=CompanyScale.MEDIUM.value)
    
    # 聚合画像（面试结束后生成）
    overall_score = Column(Float, nullable=True)
    summary = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.now)

    candidate = relationship("Candidate", back_populates="interviews")
    rounds = relationship("InterviewRound", back_populates="interview", cascade="all, delete-orphan")

class InterviewRound(Base):
    """面试轮次表"""
    __tablename__ = "rounds"

    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"))
    round_number = Column(Integer) # 1, 2, 3
    
    created_at = Column(DateTime, default=datetime.now)
    
    interview = relationship("Interview", back_populates="rounds")
    questions = relationship("QuestionRecord", back_populates="round", cascade="all, delete-orphan")

class QuestionRecord(Base):
    """题目记录表"""
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    round_id = Column(Integer, ForeignKey("rounds.id"))
    
    text = Column(Text)
    dimension = Column(String)
    difficulty = Column(String)
    reference_context = Column(Text, nullable=True)
    
    # 用户回答
    answer = Column(Text, nullable=True)
    
    # 评估结果
    score = Column(Float, nullable=True)
    evaluation_json = Column(JSON, nullable=True) # 存储完整的评估详情
    
    created_at = Column(DateTime, default=datetime.now)
    
    round = relationship("InterviewRound", back_populates="questions")

# --- Utils ---

def init_db():
    """初始化数据库表"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """依赖项：获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
