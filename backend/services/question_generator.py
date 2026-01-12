"""
题库生成服务
"""
import asyncio
from typing import Dict, Any, List, Optional
from services.llm_service import llm_service
from services.rag_service import rag_service
from config import ABILITY_DIMENSIONS


# 题目生成的系统提示
QUESTION_GEN_SYSTEM_PROMPT = """你是一位专业的 AI 产品经理面试官。
你需要基于给定的[参考资料]（来自知识库的真题或知识点），为候选人生成或选择一道面试题。

面试场景配置：
- 公司规模：{company_scale}
- 侧重点：{scale_focus}

难度控制指南：
- [基础]：重点考察基本概念理解和基础业务常识，避免深究技术原理或复杂架构。
- [进阶]：考察具体场景下的应用能力、简单的方案设计或问题分析。
- [高级]：考察系统性思维、复杂权衡、商业价值判断或底层技术逻辑。

要求：
1. 严格遵守上述[难度控制指南]，确保第一轮面试（通常为基础/进阶）不会过难
2. 优先改编[参考资料]中的题目，如果参考资料不相关，则根据维度自行生成
3. 结合[简历差距分析]（如有），针对候选人的薄弱点进行追问
4. 题目表述要专业、清晰
5. 不要返回答案，只返回问题文本"""

QUESTION_GEN_USER_PROMPT = """请生成一道面试题。

【考察维度】
{dimension}（{dimension_name}）

【难度级别】
{difficulty}

【候选人简历差距分析】
{resume_context}

【参考资料】
{context}

【输出要求】
直接输出问题文本，不要包含任何前缀或后缀。"""


def get_scale_focus(scale: str) -> str:
    """获取不同规模公司的面试侧重点"""
    focus_map = {
        "初创公司": "强调落地执行力、混沌环境下的决策能力、一专多能",
        "小型公司": "强调业务闭环能力、快速迭代验证、成本意识",
        "中型公司": "强调跨部门协作、标准化流程、数据驱动决策",
        "大型公司": "强调系统性思维、长期规划、复杂利益相关方管理、合规风控"
    }
    return focus_map.get(scale, "通用标准")


async def get_questions_for_dimension(
    dimension: str,
    count: int,
    start_id: int,
    resume_context: str = "无",
    company_scale: str = "中型公司",
    current_round: int = 1,
    total_rounds: int = 1
) -> List[Dict[str, Any]]:
    """生成指定维度的题目"""
    questions = []
    dimension_info = ABILITY_DIMENSIONS.get(dimension, {})
    dim_name = dimension_info.get("name", dimension)
    scale_focus = get_scale_focus(company_scale)
    
    # 定义难度分布（逐步递进）
    if total_rounds > 1:
        if current_round == 1:
            # 第一轮：主要是基础，少量进阶
            difficulties = ["基础"] * max(1, int(count * 0.7)) + ["进阶"] * count
        elif current_round == total_rounds:
            # 最后一轮：主要是进阶和高级
            difficulties = ["进阶"] * max(0, int(count * 0.3)) + ["高级"] * count
        else:
            # 中间轮：进阶为主
            difficulties = ["进阶"] * max(1, int(count * 0.8)) + ["高级"] * count
    else:
        # 只有一轮的情况：混合分布
        difficulties = ["基础"] * max(1, count // 3) + \
                       ["进阶"] * max(1, count // 2) + \
                       ["高级"] * max(0, count - count // 3 - count // 2)
                       
    # 截取需要的数量
    difficulties = difficulties[:count]
    
    for i, difficulty in enumerate(difficulties):
        # 1. RAG 检索 (加入公司规模上下文检索)
        query = f"AI产品经理面试题 {dim_name} {difficulty} {company_scale}"
        chunks = await rag_service.retrieve(query, top_k=3)
        
        # 构建上下文
        context = "\n".join([c.get("content_with_weight", "") for c in chunks])
        if not context:
            context = "暂无知识库相关记录，请基于通用知识生成。"
            
        # 2. LLM 生成题目
        system_prompt = QUESTION_GEN_SYSTEM_PROMPT.format(
            company_scale=company_scale,
            scale_focus=scale_focus
        )
        
        # 增加轮次上下文提示，强化递进感
        round_context = f"当前是第 {current_round}/{total_rounds} 轮面试。"
        if current_round == 1:
            round_context += "请侧重考察基础知识广度和业务常识。"
        elif current_round == total_rounds:
            round_context += "请侧重考察深度思考、复杂问题解决和抗压能力。"
        
        user_prompt = QUESTION_GEN_USER_PROMPT.format(
            dimension=dimension,
            dimension_name=dim_name,
            difficulty=difficulty,
            resume_context=resume_context,
            context=context
        ) + f"\n\n【特别提示】\n{round_context}"
        
        q_text = await llm_service.chat_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7
        )
        
        if q_text:
            questions.append({
                "id": f"q{start_id + i:03d}",
                "text": q_text.strip(),
                "dimension": dimension,
                "difficulty": difficulty,
                "reference_context": context  # 保存RAG检索到的上下文供评估使用
            })
            
    return questions


async def generate_questions(
    ability_weights: Dict[str, float],
    count: int = 10,
    resume_gap_analysis: list[str] = None,
    company_scale: str = "中型公司",
    current_round: int = 1,
    total_rounds: int = 1
) -> List[Dict[str, Any]]:
    """
    根据能力权重生成面试题目（RAG + 简历增强版 + 难度递进）
    """
    questions = []
    resume_context = "无"
    if resume_gap_analysis:
        resume_context = "\n".join([f"- {gap}" for gap in resume_gap_analysis])
    
    # 1. 计算各维度题目数量
    dimension_counts = {}
    total_weight = sum(ability_weights.values())
    
    for dim, weight in ability_weights.items():
        dim_count = max(1, int(count * weight / total_weight))
        dimension_counts[dim] = dim_count
    
    # 调整总数
    current_total = sum(dimension_counts.values())
    while current_total != count:
        if current_total > count:
            max_dim = max(dimension_counts, key=dimension_counts.get)
            dimension_counts[max_dim] -= 1
            current_total -= 1
        else:
            max_dim = max(ability_weights, key=ability_weights.get)
            dimension_counts[max_dim] += 1
            current_total += 1
            
    # 2. 并行生成各维度题目
    tasks = []
    current_id = 1
    
    for dim, dim_count in dimension_counts.items():
        if dim_count > 0:
            tasks.append(get_questions_for_dimension(
                dimension=dim, 
                count=dim_count, 
                start_id=current_id,
                resume_context=resume_context,
                company_scale=company_scale,
                current_round=current_round,
                total_rounds=total_rounds
            ))
            current_id += dim_count
            
    # 等待所有生成任务完成
    results = await asyncio.gather(*tasks)
    
    # 展平结果
    for res in results:
        questions.extend(res)
        
    return questions[:count]
