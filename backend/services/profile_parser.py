"""
岗位与简历解析服务
"""
from typing import Dict, Any, Optional
from services.llm_service import llm_service
from config import ABILITY_DIMENSIONS

# JD + Resume Matching Prompt
PROFILE_MATCH_SYSTEM_PROMPT = """你是一位资深的 AI 产品经理面试官。
你需要对比候选人简历和职位描述（JD），进行人岗匹配分析。

请分析：
1. 提取简历核心摘要
2. 计算匹配度 (0-100)
3. 识别能力差距（Gap Analysis），这将作为后续面试提问的重点"""

PROFILE_MATCH_USER_PROMPT = """
【职位描述】
{jd_text}

【候选人简历】
{resume_text}

【输出要求】
以严格的 JSON 格式输出：
{{
  "job_title": "岗位名称",
  "responsibilities": ["职责1", "职责2"],
  "skills": ["技能1", "技能2"],
  "experience": "经验要求",
  "ability_weights": {{
     "business_decomposition": 0.2,
     ...
  }},
  "resume_summary": "简历核心能力摘要...",
  "match_score": 85,
  "gap_analysis": [
    "候选人缺乏B端经验，需重点考察商业意识",
    "技术背景较强，但缺乏大模型落地经验"
  ]
}}
"""

async def parse_profile(jd_text: str, resume_text: Optional[str] = None) -> Dict[str, Any]:
    """
    解析 JD 和 简历（如果有）
    """
    if not resume_text:
        # 仅解析 JD (复用原有逻辑，为了保持兼容，还是用新的 JSON 结构)
        # 这里为了简化，我们让 LLM 即使没有简历也返回统一结构，只是 resume 部分为空
        user_prompt = f"""
【职位描述】
{jd_text}

【候选人简历】
未提供

【输出要求】
忽略简历相关字段（resume_summary, match_score, gap_analysis 置为空或 null），
重点提取 job_title, responsibilities, skills, experience, ability_weights。
确保 ability_weights 总和为 1.0。
以 JSON 格式输出。
        """
    else:
        user_prompt = PROFILE_MATCH_USER_PROMPT.format(
            jd_text=jd_text,
            resume_text=resume_text
        )

    result = await llm_service.chat_completion_json(
        system_prompt=PROFILE_MATCH_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.3
    )
    
    if result:
        # 权重归一化检查
        weights = result.get("ability_weights", {})
        if weights:
            total = sum(weights.values())
            if abs(total - 1.0) > 0.01 and total > 0:
                for key in weights:
                    weights[key] = round(weights[key] / total, 2)
    
    return result
