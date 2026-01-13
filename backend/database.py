"""
数据库连接与模型定义
支持 PostgreSQL (云端) 和 SQLite (本地开发)
"""
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, ForeignKey, JSON, DateTime, Enum as SAEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from config import BASE_DIR
import enum


def get_database_url() -> str:
    """
    获取数据库连接 URL
    优先级：环境变量 > Streamlit secrets > SQLite 本地文件
    """
    # 1. 先检查环境变量
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        return db_url
    
    # 2. 再检查 Streamlit secrets
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and "DATABASE_URL" in st.secrets:
            return st.secrets["DATABASE_URL"]
    except Exception:
        pass
    
    # 3. 回退到本地 SQLite
    db_path = os.path.join(BASE_DIR, "aipm.db")
    return f"sqlite:///{db_path}"


# 获取数据库 URL
DATABASE_URL = get_database_url()

# 判断是否为 SQLite（需要特殊配置）
is_sqlite = DATABASE_URL.startswith("sqlite")

# 创建引擎
if is_sqlite:
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False}  # SQLite 特定配置
    )
else:
    # PostgreSQL (Supabase) - 需要 SSL
    # 如果 URL 中没有 sslmode 参数，添加它
    db_url = DATABASE_URL
    if "sslmode" not in db_url:
        separator = "&" if "?" in db_url else "?"
        db_url = f"{db_url}{separator}sslmode=require"
    
    engine = create_engine(
        db_url,
        pool_pre_ping=True,  # 自动检测断开的连接
        pool_size=5,
        max_overflow=10
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

# 数据库可用性标志
_db_available = None

def init_db():
    """初始化数据库表，带错误处理"""
    global _db_available
    try:
        Base.metadata.create_all(bind=engine)
        _db_available = True
        print("[DB] 数据库初始化成功")
    except Exception as e:
        _db_available = False
        print(f"[DB] 数据库初始化失败: {e}")
        # 不抛出异常，让应用继续运行（历史记录功能将不可用）

def is_db_available() -> bool:
    """检查数据库是否可用"""
    global _db_available
    if _db_available is None:
        init_db()
    return _db_available

def get_db():
    """依赖项：获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
