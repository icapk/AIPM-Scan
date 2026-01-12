"""
能力评估服务
基于 LLM + 知识库进行结构化评分
"""
from typing import Dict, Any, Optional
from services.llm_service import llm_service
from config import ABILITY_DIMENSIONS


# 评估的系统提示
EVALUATE_SYSTEM_PROMPT = """你是一位资深的 AI 产品经理面试官，负责评估候选人的回答质量。

你需要：
1. 基于评分标准给出 0-10 分的评分
2. 从回答中抽取证据句（直接引用原文）
3. 分析优势和不足
4. 给出综合评价

评分标准：
- 9-10 分：深刻理解，有独到见解，超出预期
- 7-8 分：理解准确，表达清晰，有亮点
- 5-6 分：基本理解，有遗漏，深度不足
- 3-4 分：理解偏差，关键点缺失
- 0-2 分：完全不理解或答非所问

证据句规则：
1. 必须直接引用原文，使用「」标记
2. 每句证据后简要说明（10-20字）
3. 亮点用 ✓ 标记，不足用 ✗ 标记
4. 证据句数量 2-4 句"""


EVALUATE_USER_PROMPT = """请评估候选人对以下问题的回答。

【面试问题】
{question_text}

【考察维度】
{dimension}（{dimension_name}）

【参考资料】
{context}

【候选人回答】
{answer}

【输出要求】
以严格的 JSON 格式输出：
{{
  "score": X.X,
  "dimension": "{dimension}",
  "evidence_sentences": [
    "「引用原文1」- 说明亮点/不足✓/✗",
    "「引用原文2」- 说明亮点/不足✓/✗"
  ],
  "strengths": ["优势1", "优势2"],
  "weaknesses": ["不足1"],
  "comment": "综合评价（100-150字）"
}}

注意：
1. 分数必须是 0.0 到 10.0 之间的浮点数
2. 证据句必须是候选人回答的原文
3. 评价要具体客观，有建设性"""


async def evaluate_answer(
    question: Dict[str, Any],
    answer: str
) -> Optional[Dict[str, Any]]:
    """
    评估候选人回答
    
    Args:
        question: 问题信息（包含 id, text, dimension, reference_context）
        answer: 候选人回答
        
    Returns:
        评估结果字典
    """
    dimension = question.get("dimension", "")
    dimension_info = ABILITY_DIMENSIONS.get(dimension, {})
    dimension_name = dimension_info.get("name", dimension)
    
    # 获取参考上下文
    context = question.get("reference_context", "无参考资料")
    
    user_prompt = EVALUATE_USER_PROMPT.format(
        question_text=question.get("text", ""),
        dimension=dimension,
        dimension_name=dimension_name,
        context=context,
        answer=answer
    )
    
    result = await llm_service.chat_completion_json(
        system_prompt=EVALUATE_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.3
    )
    
    if result:
        # 确保分数在合理范围
        score = result.get("score", 0)
        if isinstance(score, (int, float)):
            result["score"] = max(0, min(10, float(score)))
        else:
            result["score"] = 0.0
        
        # 确保维度正确
        result["dimension"] = dimension
        
        # 确保列表字段存在
        if "evidence_sentences" not in result:
            result["evidence_sentences"] = []
        if "strengths" not in result:
            result["strengths"] = []
        if "weaknesses" not in result:
            result["weaknesses"] = []
        if "comment" not in result:
            result["comment"] = ""
    
    return result


async def evaluate_batch(
    questions_and_answers: list
) -> Dict[str, Any]:
    """
    批量评估多道题目
    
    Args:
        questions_and_answers: 问题和回答列表 [{"question": {...}, "answer": "..."}]
        
    Returns:
        综合评估结果
    """
    results = []
    dimension_scores = {}
    
    for qa in questions_and_answers:
        result = await evaluate_answer(
            question=qa["question"],
            answer=qa["answer"]
        )
        if result:
            results.append(result)
            
            # 汇总各维度得分
            dim = result.get("dimension", "")
            if dim not in dimension_scores:
                dimension_scores[dim] = []
            dimension_scores[dim].append(result.get("score", 0))
    
    # 计算各维度平均分
    dimension_averages = {}
    for dim, scores in dimension_scores.items():
        dimension_averages[dim] = {
            "average_score": round(sum(scores) / len(scores), 1),
            "question_count": len(scores)
        }
    
    # 计算加权总分
    total_score = 0
    total_questions = len(results)
    if total_questions > 0:
        total_score = round(sum(r.get("score", 0) for r in results) / total_questions, 1)
    
    return {
        "overall_score": total_score,
        "dimension_scores": dimension_averages,
        "individual_results": results,
        "total_questions": total_questions
    }
