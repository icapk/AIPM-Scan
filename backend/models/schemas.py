"""
AIPM-Scan 数据模型定义
使用 Pydantic 进行数据验证
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from enum import Enum


class DifficultyLevel(str, Enum):
    """题目难度级别"""
    BASIC = "基础"
    INTERMEDIATE = "进阶"
    ADVANCED = "高级"


class AbilityWeights(BaseModel):
    """六维能力权重"""
    business_decomposition: float = Field(ge=0, le=1, description="业务拆解能力权重")
    ai_tech_understanding: float = Field(ge=0, le=1, description="AI技术理解权重")
    business_awareness: float = Field(ge=0, le=1, description="商业意识权重")
    system_thinking: float = Field(ge=0, le=1, description="系统思维权重")
    execution_power: float = Field(ge=0, le=1, description="推动能力权重")
    risk_awareness: float = Field(ge=0, le=1, description="风险意识权重")


# ===== JD 解析相关 =====


class CompanyScale(str, Enum):
    """公司规模"""
    STARTUP = "初创公司"
    SMALL = "小型公司"
    MEDIUM = "中型公司"
    LARGE = "大型公司"


class InterviewConfig(BaseModel):
    """面试配置"""
    round_count: int = Field(default=1, ge=1, le=3, description="面试轮数")
    questions_per_round: int = Field(default=5, ge=3, le=10, description="每轮题目数量")
    company_scale: CompanyScale = Field(default=CompanyScale.MEDIUM, description="公司规模")


class ParseJDRequest(BaseModel):
    """JD解析请求"""
    jd_text: str = Field(..., min_length=50, description="职位描述文本")
    resume_text: Optional[str] = Field(None, description="候选人简历文本")
    config: Optional[InterviewConfig] = Field(None, description="面试配置")


class JobProfile(BaseModel):
    """岗位画像"""
    job_title: str = Field(..., description="岗位名称")
    responsibilities: List[str] = Field(default_factory=list, description="核心职责")
    skills: List[str] = Field(default_factory=list, description="技能要求")
    experience: str = Field(default="", description="经验要求")
    ability_weights: AbilityWeights = Field(..., description="六维能力权重")
    
    # 简历分析扩展
    resume_summary: Optional[str] = Field(None, description="简历摘要")
    match_score: Optional[float] = Field(None, description="人岗匹配度(0-100)")
    gap_analysis: List[str] = Field(default_factory=list, description="能力差距分析")


class ParseJDResponse(BaseModel):
    """JD解析响应"""
    success: bool = True
    data: Optional[JobProfile] = None
    interview_id: Optional[int] = None
    error: Optional[str] = None
    timestamp: str = ""


# ===== 题库生成相关 =====

class GenerateQuestionsRequest(BaseModel):
    """题库生成请求"""
    ability_weights: AbilityWeights = Field(..., description="六维能力权重")
    count: int = Field(default=10, ge=5, le=20, description="生成题目数量")
    resume_gap_analysis: List[str] = Field(default_factory=list, description="简历能力差距分析")
    company_scale: Optional[CompanyScale] = Field(default=CompanyScale.MEDIUM, description="公司规模")


class Question(BaseModel):
    """面试题目"""
    id: str = Field(..., description="题目ID")
    text: str = Field(..., description="题目内容")
    dimension: str = Field(..., description="考察能力维度")
    difficulty: DifficultyLevel = Field(..., description="难度级别")


class GenerateQuestionsResponse(BaseModel):
    """题库生成响应"""
    success: bool = True
    data: Optional[Dict] = None
    error: Optional[str] = None
    timestamp: str = ""


# ===== 能力评估相关 =====

class QuestionInfo(BaseModel):
    """问题信息"""
    id: str = Field(..., description="题目ID")
    text: str = Field(..., description="题目内容")
    dimension: str = Field(..., description="考察能力维度")


class EvaluateAnswerRequest(BaseModel):
    """能力评估请求"""
    question: QuestionInfo = Field(..., description="问题信息")
    answer: str = Field(..., min_length=10, description="用户回答")


class EvaluationResult(BaseModel):
    """评估结果"""
    score: float = Field(ge=0, le=10, description="得分(0-10)")
    dimension: str = Field(..., description="评估维度")
    evidence_sentences: List[str] = Field(default_factory=list, description="证据句")
    strengths: List[str] = Field(default_factory=list, description="优势")
    weaknesses: List[str] = Field(default_factory=list, description="不足")
    comment: str = Field(default="", description="综合评价")


class EvaluateAnswerResponse(BaseModel):
    """能力评估响应"""
    success: bool = True
    data: Optional[EvaluationResult] = None
    error: Optional[str] = None
    timestamp: str = ""


# ===== 综合报告相关 =====

class DimensionScore(BaseModel):
    """维度得分"""
    dimension: str
    dimension_name: str
    score: float
    evidence: List[str] = []
    comment: str = ""


class InterviewReport(BaseModel):
    """面试报告"""
    overall_score: float = Field(ge=0, le=10, description="总体得分")
    dimension_scores: List[DimensionScore] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    improvements: List[str] = Field(default_factory=list)
    summary: str = ""
