"""
AIPM-Scan Streamlit 应用
AI 产品经理能力识别与评估系统
"""
import streamlit as st
import pandas as pd
import asyncio
from datetime import datetime
from services.llm_service import llm_service
from services.profile_parser import parse_profile
from services.question_generator import generate_questions
from services.evaluator import evaluate_answer
from services.history_service import history_service
from config import ABILITY_DIMENSIONS
from database import init_db, SessionLocal
from models.schemas import CompanyScale

# 初始化数据库
init_db()

# 页面配置
st.set_page_config(
    page_title="AIPM-Scan Pro",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义样式 - Apple 风格简约设计
st.markdown("""
<style>
    /* === 全局样式 === */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    .stApp {
        background: linear-gradient(180deg, #fafafa 0%, #f5f5f7 100%);
    }
    
    /* === 侧边栏 === */
    section[data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e5e5e7;
    }
    section[data-testid="stSidebar"] .stMarkdown {
        color: #1d1d1f;
    }
    
    /* === 主标题 === */
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: #1d1d1f;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.25rem;
        font-weight: 400;
        color: #86868b;
        text-align: center;
        margin-bottom: 2.5rem;
    }
    
    /* === 卡片样式 === */
    .metric-card {
        background: #ffffff;
        padding: 2rem;
        border-radius: 18px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
        text-align: center;
        border: 1px solid rgba(0, 0, 0, 0.04);
    }
    .metric-value {
        font-size: 3.5rem;
        font-weight: 700;
        color: #1d1d1f;
        letter-spacing: -0.02em;
    }
    .metric-label {
        font-size: 0.9rem;
        font-weight: 500;
        color: #86868b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }
    
    /* === 强调卡片 (渐变) === */
    .metric-card-accent {
        background: linear-gradient(135deg, #007aff 0%, #5856d6 100%);
        padding: 2rem;
        border-radius: 18px;
        text-align: center;
        color: white;
    }
    .metric-card-accent .metric-value {
        color: white;
    }
    .metric-card-accent .metric-label {
        color: rgba(255, 255, 255, 0.8);
    }
    
    /* === 按钮样式 === */
    .stButton > button {
        background: #007aff;
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.2s ease;
        box-shadow: 0 2px 8px rgba(0, 122, 255, 0.3);
    }
    .stButton > button:hover {
        background: #0056b3;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 122, 255, 0.4);
    }
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* === 文本输入框 === */
    .stTextArea textarea, .stTextInput input {
        border: 1px solid #d2d2d7;
        border-radius: 12px;
        padding: 1rem;
        font-size: 1rem;
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #007aff;
        box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.1);
    }
    
    /* === 进度条 === */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #007aff, #5856d6);
        border-radius: 10px;
    }
    
    /* === 警告/成功/错误框 === */
    .stAlert {
        border-radius: 12px;
        border: none;
    }
    
    /* === 选择框和滑块 === */
    .stSelectbox > div > div, .stSlider > div {
        border-radius: 12px;
    }
    
    /* === 分隔线 === */
    hr {
        border: none;
        height: 1px;
        background: #e5e5e7;
        margin: 2rem 0;
    }
    
    /* === 展开器 === */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: #1d1d1f;
        border-radius: 12px;
    }
    
    /* === 隐藏 Streamlit 默认元素 === */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* === 响应式调整 === */
    @media (max-width: 768px) {
        .main-header { font-size: 2rem; }
        .metric-value { font-size: 2.5rem; }
    }
</style>
""", unsafe_allow_html=True)

def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

def get_db_session():
    return SessionLocal()

# --- Session State ---
def init_session_state():
    defaults = {
        "step": "setup",  # setup, profile, interview, report
        "mode": "new",    # new, history
        "job_profile": None,
        "interview_id": None,
        "round": 1,
        "max_rounds": 1,
        "questions_per_round": 5,
        "company_scale": "中型公司",
        "questions": [],  # List of current round questions
        "current_idx": 0,
        "answers": {},    # {q_id: answer}
        "evaluations": {},# {q_id: evaluation}
        "history_view_id": None
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# --- Components ---

def render_sidebar():
    with st.sidebar:
        st.markdown("### 🎯 模式选择")
        mode = st.radio("选择功能", ["开始新面试", "历史记录"], index=0 if st.session_state.mode == "new" else 1)
        
        if mode == "开始新面试" and st.session_state.mode != "new":
            st.session_state.mode = "new"
            st.session_state.step = "setup"
            st.rerun()
        elif mode == "历史记录" and st.session_state.mode != "history":
            st.session_state.mode = "history"
            st.rerun()
            
        st.markdown("---")
        if st.session_state.mode == "new":
            st.markdown("### ⚙️ 面试配置")
            st.session_state.max_rounds = st.slider("面试轮数", 1, 3, 1)
            st.session_state.questions_per_round = st.slider("每轮题目数", 3, 10, 5)
            st.session_state.company_scale = st.selectbox(
                "目标公司规模", 
                [e.value for e in CompanyScale],
                index=2
            )
            
            st.markdown("---")
            st.markdown("### 📍 当前进度")
            steps = {
                "setup": "1️⃣ 简历 & JD",
                "profile": "2️⃣ 匹配分析",
                "interview": "3️⃣ 模拟面试",
                "report": "4️⃣ 评估报告"
            }
            for k, v in steps.items():
                if st.session_state.step == k:
                    st.markdown(f"**→ {v}**")
                else:
                    st.markdown(f"　{v}")

def render_setup():
    st.markdown('<p class="main-header">🎯 AIPM-Scan Pro</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">基于 RAG 的 AI 产品经理深度评估系统</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📄 职位描述 (JD)")
        jd_text = st.text_area("粘贴职位描述", height=300, value="""岗位职责:
1.负责AI智能客服工具(对标LiveChat/
Smartsalely等)全生命周期规划、设计与迭代，聚焦全渠道交互、AI对话引擎、工单自动化等核心功能设计。
2.挖掘B端客户客服痛点，结合大模型/RAG技术，落地"降本增效+客户体验"双目标。
3.跨团队协同算法/研发/设计，推动产品迭代与技术落地，数据驱动优化。
4.构建并维护与关键用户及合作伙伴的关系，收集反馈，持续改进产品体验。
任职要求:
1.对AI技术有深刻理解，具备敏锐的市场洞察力。
2.优秀的项目管理能力，能够有效协调团队工作，推动项目落地。
3.有B端的SaaS产品经验，AI客服/智能交互产品核心经验。
4.熟悉LiveChat/HelpShift等竞品，理解大模型、意图识别等AI技术原理。""")
    
    with col2:
        st.markdown("### 👤 候选人简历")
        resume_text = st.text_area("粘贴简历内容 (可选)", height=300, value="""个人总结：
1.熟悉从Prompt Engineering到模型评估的全链路 AI 产品设计，具备数据飞轮和Bad Case 优化的实战经验。
2.熟悉 LLM 应用、RAG 知识检索、私有化部署 等 AI 技术栈，能结合业务需求进行技术选型与落地。
3.主导过 千万级营收的 AI 标书助手 与 500 万元商业化闭环的智慧场馆 SaaS，具备从 战略规划 → 产品设计 → 技术实现 → 商业化 的全链路经验。

工作经历： 
2025.04-至今                戴思乐科技集团有限公司                  岗位：AI产品经理
核心成果：企业级 AI 标书助手落地，创造千万级营收增长空间
1.通过 LLM+RAG 架构，将传统标书制作的知识密集型工作转化为高效自动化流程，驱动投标部效率提升 50% 。
2.主导技术选型，基于 DeepSeek-V2 决策，平衡模型性能与私有化部署成本，确保了企业数据安全和项目快速交付 。
3.构建 Bad Case 闭环优化机制，将用户反馈转化为结构化数据，驱动算法与数据策略迭代，通过精准标注和回流，持续提升模型准确率和内容质量，确保产品的高可用性与持续进化 。

2022.07-至今                戴思乐科技集团有限公司                  岗位：产品经理
核心成果：乐泳智慧场馆 SaaS 系统商业化闭环
从0到1构建“乐泳”智慧场馆SaaS产品体系，并完成商业化闭环。颠覆性地引入掌静脉生物识别技术，重构“刷掌入场-储物-消费”全链路无人化服务，独立负责完成从竞品分析、原型设计到项目交付的全流程。产品上线后迅速占据市场，截止目前累计实现商业化收入500万元，为单个场馆年均节约10万元管理与耗材成本。

2018.03-2022.07     深圳市金财全文化发展有限公司            岗位：运营
·  负责教育类产品的运营，提升曝光与转化。
· 策划学员课程与品牌峰会，提升用户粘性与市场影响力。

2017.03-2017.12          深圳旭辉信息技术有限公司             岗位：测试
负责访客机系统的软硬件测试，售前及技术支持工作。

项目经验：
AI标书助手（LLM+RAG）         AI产品经理                     2025.04 - 至今         
【项目名称】：AI标书助手
【项目背景】：为打破传统标书制作“高耗时、低效率”的业务瓶颈，主导设计并落地了基于LLM与RAG架构的AI标书助手。项目旨在重构内容生产流程，将投标能力转化为企业的核心竞争壁垒。
【工作内容】：
1.战略定位： 主导0-1产品规划，通过市场与竞品分析，精准定位“AI生成标书”为战略突破口。 
2.技术选型： 负责核心技术方案评估，决策采用DeepSeek-V2模型及私有化部署方案，为产品性能与数据安全奠定基石。 
3.产品设计： 独立负责产品架构与PRD撰写，通过精密的Prompt工程优化RAG内容生成逻辑，推动产品3个月内成功上线。 
4.迭代优化： 构建Bad Case闭环优化机制，驱动算法与数据策略迭代，确保产品高可用性与持续进化。 
5.商业规划： 制定清晰的商业化蓝图，规划以“会员年费”与“私有化部署”模式切入B端市场，开辟新营收曲线。 主要成果：
【项目成果】：
1.效率提升： 驱动投标部标书制作效率提升50%，人均产出提升1.5倍。 
2.营收赋能： 赋能团队年增产120份标书，创造千万级营收增长潜力。 
3.极速落地： 3个月内完成从0到1的AI产品完整交付。

乐泳体育                            产品经理                                     2022.07 - 至今         
【项目名称】：游泳馆SaaS系统 
【项目背景】：利用新兴技术【掌静脉】替代手环作为身份识别方案，配合客户/票务管理系统，C端客户直接刷掌开闸、储物，无需专人管理、发放手环，减少手环丢失的成本，提升客户体验及游泳馆运营管理效率，降低运营管理难度和管理成本。
【工作内容】：
1.需求分析：项目前期对4家游泳馆举行实地采访调查，线下（游泳馆）线上（微信），与5位游泳馆运营负责人及店长分别沟通整理需求，做资料分类汇总和用户的核心需求梳理以及优先排序结果；
2.竞品分析：对“菠菜”、“勤鸟”、“微健”三个竞品进行产品分析，主要对“会员管理”和“财务报表”两个板块进行比较分析；
3.产品设计：使用 墨刀 做主线核心功能的流程图，经过用户需求调研创新设计了游泳馆后台管理功能的具体实现流程和场景需求分析。独立负责整个项目的原型设计工作，使用墨刀工具共计设计48个原型页面；
4.需求文档：负责撰写PRD需求文档，以方便研发和UI后续工作；
5.产品规划：与老板以及公司高层共同制定产品一期、二期计划，并确定各产品优先级与实施计划；
【项目成果】：根据微信官方数据统计，场馆智慧化升级后，刷掌进场的客户使用率达到90%，复用率达到99%，为每个场馆平均节约2名人力成本，多维度报表为场馆运营策略、财务管理功能提供有力的数据支持。""")

    if st.button("🚀 开始解析与匹配", type="primary", use_container_width=True):
        if len(jd_text) < 50:
            st.error("JD 内容太短，请提供更多信息")
            return
            
        with st.spinner("正在分析 JD 和简历..."):
            try:
                result = run_async(parse_profile(jd_text, resume_text))
                if result:
                    # Save to DB
                    db = get_db_session()
                    try:
                        # Create Candidate (Simplified)
                        candidate = history_service.create_candidate(db, name="Candidate", resume_text=resume_text)
                        
                        # Create Interview
                        interview = history_service.create_interview(
                            db,
                            candidate_id=candidate.id,
                            job_title=result.get("job_title", "未命名岗位"),
                            jd_text=jd_text,
                            company_scale=st.session_state.company_scale
                        )
                        st.session_state.interview_id = interview.id
                    finally:
                        db.close()
                    
                    st.session_state.job_profile = result
                    st.session_state.step = "profile"
                    st.rerun()
                else:
                    st.error("解析失败")
            except Exception as e:
                st.error(f"发生错误: {str(e)}")

def render_profile_view():
    st.markdown("### 📊 岗位与人才匹配分析")
    profile = st.session_state.job_profile
    
    # Top Metrics
    c1, c2, c3 = st.columns(3)
    with c1:
        match_score = profile.get("match_score")
        if match_score is not None:
             st.markdown(f"""
            <div class="metric-card-accent">
                <div class="metric-label">人岗匹配度</div>
                <div class="metric-value">{match_score}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("未提供简历，仅进行岗位分析")
            
    with c2:
        st.markdown(f"**岗位**: {profile.get('job_title')}")
        st.markdown(f"**公司规模**: {st.session_state.company_scale}")
        
    with c3:
        if profile.get("resume_summary"):
            with st.expander("查看简历摘要"):
                st.write(profile.get("resume_summary"))

    col_l, col_r = st.columns([1, 1])
    with col_l:
        st.markdown("#### 🎯 能力Gap分析 (面试重点)")
        gaps = profile.get("gap_analysis", [])
        if gaps:
            for gap in gaps:
                st.warning(f"⚠️ {gap}")
        else:
            st.success("暂无明显能力缺失，或未提供简历")
            
    with col_r:
        st.markdown("#### ⚖️ 能力考察权重")
        weights = profile.get("ability_weights", {})
        data = [{"维度": ABILITY_DIMENSIONS.get(k, {}).get("name", k), "权重": v} for k,v in weights.items()]
        st.bar_chart(pd.DataFrame(data).set_index("维度"))

    if st.button("开始第 1 轮面试 ➡️", type="primary"):
        start_round(1)

def start_round(round_num):
    st.session_state.round = round_num
    st.session_state.current_idx = 0
    st.session_state.answers = {}
    st.session_state.evaluations = {}
    
    # DB: Create Round
    db = get_db_session()
    try:
        round_obj = history_service.create_round(db, st.session_state.interview_id, round_num)
        st.session_state.round_id = round_obj.id
    finally:
        db.close()
    
    with st.spinner(f"正在生成第 {round_num} 轮面试题..."):
        weights = st.session_state.job_profile.get("ability_weights", {})
        gaps = st.session_state.job_profile.get("gap_analysis", [])
        
        qt = run_async(generate_questions(
            ability_weights=weights,
            count=st.session_state.questions_per_round,
            resume_gap_analysis=gaps,
            company_scale=st.session_state.company_scale,
            current_round=round_num,
            total_rounds=st.session_state.max_rounds
        ))
        
        # Save questions to DB
        db = get_db_session()
        try:
            history_service.add_questions(db, st.session_state.round_id, qt)
        finally:
            db.close()
            
        st.session_state.questions = qt
        st.session_state.step = "interview"
        st.rerun()

def render_interview():
    round_num = st.session_state.round
    q_len = len(st.session_state.questions)
    idx = st.session_state.current_idx
    
    if idx >= q_len:
        # Round Complete
        st.success(f"🎉 第 {round_num} 轮面试结束")
        
        c1, c2 = st.columns(2)
        with c1:
            if round_num < st.session_state.max_rounds:
                if st.button(f"进入第 {round_num+1} 轮 (进阶追问)", type="primary"):
                    start_round(round_num + 1)
            else:
                 if st.button("生成最终报告 📊", type="primary"):
                     st.session_state.step = "report"
                     st.rerun()
        return

    question = st.session_state.questions[idx]
    
    st.markdown(f"### 🎙️ 第 {round_num} 轮面试 - 问题 {idx + 1}/{q_len}")
    st.progress((idx + 1) / q_len)
    
    st.info(f"**[{question['difficulty']}]** {question['text']}")
    
    answer_key = f"r{round_num}_q{idx}"
    answer = st.text_area("你的回答", height=200, key=answer_key)
    
    if st.button("提交回答", type="primary"):
        if len(answer) < 5:
            st.warning("请多说一点...")
        else:
            with st.spinner("正在评估..."):
                res = run_async(evaluate_answer(question, answer))
                
                # Save to DB
                db = get_db_session()
                try:
                    history_service.update_answer_and_evaluation(
                        db, st.session_state.round_id, question["text"], answer, res
                    )
                finally:
                    db.close()
                
                # Store locally
                st.session_state.evaluations[question["id"]] = res
                st.session_state.answers[question["id"]] = answer
                
                st.session_state.current_idx += 1
                st.rerun()

def render_report():
    st.markdown("### 📊 综合评估报告")
    
    # Calculate Overall Score (Simplified, just average of current session evaluations)
    evals = st.session_state.evaluations.values()
    if not evals:
        st.warning("暂无数据")
        return
        
    avg_score = sum([e['score'] for e in evals]) / len(evals)
    
    st.markdown(f"""
    <div class="metric-card-accent">
        <div class="metric-label">整体表现得分</div>
        <div class="metric-value">{avg_score:.1f}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 💡 核心亮点与建议")
    # Simple consolidation
    all_strengths = set()
    all_weaknesses = set()
    for e in evals:
        all_strengths.update(e.get("strengths", []))
        all_weaknesses.update(e.get("weaknesses", []))
    
    c1, c2 = st.columns(2)
    with c1:
        st.success("**✅ 优势**\n\n" + "\n".join([f"- {s}" for s in list(all_strengths)[:5]]))
    with c2:
        st.error("**⚠️ 改进空间**\n\n" + "\n".join([f"- {w}" for w in list(all_weaknesses)[:5]]))

    st.markdown("---")
    if st.button("⬅️ 返回首页"):
        st.session_state.step = "setup"
        st.rerun()

def render_history():
    st.markdown("### 📜 历史面试记录")
    
    db = get_db_session()
    interviews = history_service.get_all_interviews(db)
    db.close()
    
    if not interviews:
        st.info("暂无历史记录")
        return
        
    for i in interviews:
        with st.expander(f"{i.created_at.strftime('%Y-%m-%d %H:%M')} - {i.job_title} ({i.company_scale})"):
            st.write(f"ID: {i.id}")
            # In a real app, clicking here would load the details.
            # MVP: Just show basic info
            st.info("（详细报告查看功能开发中...）")

# --- Main ---

def main():
    init_session_state()
    render_sidebar()
    
    if st.session_state.mode == "history":
        render_history()
    else:
        if st.session_state.step == "setup":
            render_setup()
        elif st.session_state.step == "profile":
            render_profile_view()
        elif st.session_state.step == "interview":
            render_interview()
        elif st.session_state.step == "report":
            render_report()

if __name__ == "__main__":
    main()
