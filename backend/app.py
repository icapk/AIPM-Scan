"""
AIPM-Scan Streamlit 应用
AI 产品经理能力识别与评估系统
"""
import sys
import os

# 确保 backend 目录在 Python 路径中（解决 Streamlit Cloud 上的导入问题）
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

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
from database import init_db, SessionLocal, is_db_available
from models.schemas import CompanyScale

# 初始化数据库（带错误处理，失败时应用仍可运行）
try:
    init_db()
except Exception as e:
    print(f"数据库初始化失败: {e}")

# 页面配置
st.set_page_config(
    page_title="AIPM-Scan Pro",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义样式 - 清爽简约设计 (参考 Teal 主题)
st.markdown("""
<style>
    /* === 全局样式 === */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    :root {
        --primary: #00B8A9;
        --primary-dark: #00a399;
        --primary-light: #e6f7f6;
        --text-dark: #1a1a2e;
        --text-muted: #6b7280;
        --bg-main: #f8f9fb;
        --bg-card: #ffffff;
        --border-color: #e5e7eb;
        --shadow-sm: 0 1px 3px rgba(0,0,0,0.08);
        --shadow-md: 0 4px 12px rgba(0,0,0,0.1);
        --radius-sm: 8px;
        --radius-md: 12px;
        --radius-lg: 16px;
    }
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        -webkit-font-smoothing: antialiased;
    }
    
    .stApp {
        background: var(--bg-main);
    }
    
    /* === 主内容区 === */
    .main .block-container {
        background: var(--bg-card);
        border-radius: var(--radius-lg);
        padding: 2.5rem 3rem;
        margin: 1.5rem auto;
        max-width: 900px;
        box-shadow: var(--shadow-sm);
        border: 1px solid var(--border-color);
    }
    
    /* === 侧边栏 === */
    section[data-testid="stSidebar"] {
        background: var(--bg-card);
        border-right: 1px solid var(--border-color);
    }
    section[data-testid="stSidebar"] > div {
        padding: 1rem 0.8rem;
    }
    
    /* === 主标题 === */
    .main-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--text-dark);
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        font-size: 0.95rem;
        font-weight: 400;
        color: var(--text-muted);
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* === 步骤编号 === */
    .step-number {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 24px;
        height: 24px;
        background: var(--primary);
        color: white;
        border-radius: 50%;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 10px;
    }
    .step-title {
        display: flex;
        align-items: center;
        font-size: 1rem;
        font-weight: 600;
        color: var(--text-dark);
        margin-bottom: 0.8rem;
    }
    .step-hint {
        font-size: 0.85rem;
        color: var(--text-muted);
        margin-top: 0.5rem;
    }
    
    /* === 上传区域 === */
    .upload-area {
        border: 2px dashed var(--border-color);
        border-radius: var(--radius-md);
        padding: 2.5rem;
        text-align: center;
        background: var(--bg-main);
        transition: all 0.2s ease;
        cursor: pointer;
    }
    .upload-area:hover {
        border-color: var(--primary);
        background: var(--primary-light);
    }
    .upload-icon {
        font-size: 1.5rem;
        color: var(--text-muted);
        margin-bottom: 0.5rem;
    }
    .upload-text {
        color: var(--text-muted);
        font-size: 0.9rem;
    }
    
    /* === 卡片式选择 === */
    .mode-card {
        border: 2px solid var(--border-color);
        border-radius: var(--radius-md);
        padding: 1.2rem 1.5rem;
        cursor: pointer;
        transition: all 0.2s ease;
        background: var(--bg-card);
    }
    .mode-card:hover {
        border-color: var(--primary);
    }
    .mode-card.active {
        border-color: var(--primary);
        background: var(--primary-light);
    }
    .mode-card .mode-icon {
        font-size: 1.2rem;
        margin-right: 0.8rem;
    }
    .mode-card .mode-title {
        font-weight: 600;
        color: var(--text-dark);
    }
    .mode-card .mode-desc {
        font-size: 0.8rem;
        color: var(--text-muted);
    }
    .mode-card .check-icon {
        color: var(--primary);
        font-size: 1.2rem;
    }
    
    /* === 指标卡片 === */
    .metric-card {
        background: var(--bg-card);
        padding: 1.5rem;
        border-radius: var(--radius-md);
        box-shadow: var(--shadow-sm);
        text-align: center;
        border: 1px solid var(--border-color);
    }
    .metric-card-accent {
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
        padding: 1.5rem;
        border-radius: var(--radius-md);
        text-align: center;
        color: white;
        box-shadow: 0 4px 12px rgba(0, 184, 169, 0.3);
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--text-dark);
    }
    .metric-card-accent .metric-value {
        color: white;
    }
    .metric-label {
        font-size: 0.8rem;
        font-weight: 500;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.3rem;
    }
    .metric-card-accent .metric-label {
        color: rgba(255, 255, 255, 0.9);
    }
    
    /* === 按钮样式 === */
    .stButton > button {
        background: var(--primary);
        color: white;
        border: none;
        border-radius: var(--radius-md);
        padding: 0.9rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.2s ease;
        box-shadow: 0 2px 8px rgba(0, 184, 169, 0.3);
    }
    .stButton > button:hover {
        background: var(--primary-dark);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 184, 169, 0.4);
    }
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* === 文本输入框 === */
    .stTextArea textarea, .stTextInput input {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        padding: 0.9rem 1rem;
        font-size: 0.95rem;
        transition: all 0.2s ease;
    }
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: var(--primary);
        box-shadow: 0 0 0 3px rgba(0, 184, 169, 0.15);
    }
    
    /* === Slider 滑块 === */
    .stSlider > div > div > div > div {
        background: var(--primary) !important;
    }
    .stSlider > div > div > div > div > div {
        background: var(--primary) !important;
    }
    
    /* === 进度条 === */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, var(--primary), var(--primary-dark));
        border-radius: 10px;
    }
    
    /* === 选择框 === */
    .stSelectbox > div > div {
        background: var(--bg-card);
        border-radius: var(--radius-sm);
        border: 1px solid var(--border-color);
    }
    
    /* === 信息框 === */
    .stAlert {
        border-radius: var(--radius-md);
        border: none;
    }
    
    /* === 侧边栏按钮 === */
    .sidebar-btn {
        display: flex;
        align-items: center;
        padding: 0.7rem 1rem;
        border-radius: var(--radius-sm);
        margin-bottom: 0.3rem;
        cursor: pointer;
        transition: all 0.15s ease;
        font-size: 0.9rem;
        color: var(--text-dark);
    }
    .sidebar-btn:hover {
        background: var(--bg-main);
    }
    .sidebar-btn.active {
        background: var(--primary-light);
        color: var(--primary);
        font-weight: 500;
    }
    .sidebar-btn-primary {
        background: var(--primary);
        color: white;
        font-weight: 500;
        border-radius: var(--radius-sm);
        padding: 0.7rem 1rem;
        margin-bottom: 1rem;
        cursor: pointer;
    }
    .sidebar-btn-primary:hover {
        background: var(--primary-dark);
    }
    
    /* === 历史记录项 === */
    .history-item {
        padding: 0.6rem 0.8rem;
        border-radius: var(--radius-sm);
        margin-bottom: 0.3rem;
        cursor: pointer;
        font-size: 0.85rem;
        color: var(--text-dark);
        transition: all 0.15s ease;
    }
    .history-item:hover {
        background: var(--bg-main);
    }
    .history-item .tag {
        background: var(--primary);
        color: white;
        padding: 0.15rem 0.5rem;
        border-radius: 10px;
        font-size: 0.7rem;
        margin-left: 0.5rem;
    }
    
    /* === 分割线 === */
    .divider {
        height: 1px;
        background: var(--border-color);
        margin: 1rem 0;
    }
    
    /* === 隐藏 Streamlit 默认元素 === */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* === 标题 === */
    h1, h2, h3 {
        color: var(--text-dark);
        font-weight: 600;
    }
    
    /* === 展开器 === */
    .streamlit-expanderHeader {
        font-weight: 500;
        color: var(--text-dark);
        border-radius: var(--radius-sm);
        background: var(--bg-main);
    }
    
    /* === 响应式 === */
    @media (max-width: 768px) {
        .main-title { font-size: 1.5rem; }
        .main .block-container { padding: 1.5rem; margin: 0.5rem; }
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
    # 标题
    st.markdown('<p class="main-title">开启新的模拟面试</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">配置您的简历和目标岗位，AI 面试官将为您量身定制面试问题</p>', unsafe_allow_html=True)
    
    # Step 1: 上传简历
    st.markdown('''
    <div class="step-title">
        <span class="step-number">1</span>
        上传简历 (可选)
    </div>
    ''', unsafe_allow_html=True)
    
    resume_text = st.text_area(
        "粘贴简历内容",
        height=120,
        placeholder="粘贴您的简历内容，或留空仅基于 JD 生成面试题...",
        label_visibility="collapsed"
    )
    
    st.markdown('<div style="height: 1rem"></div>', unsafe_allow_html=True)
    
    # Step 2: 目标岗位
    st.markdown('''
    <div class="step-title">
        <span class="step-number">2</span>
        目标岗位
    </div>
    ''', unsafe_allow_html=True)
    
    jd_text = st.text_area(
        "职位描述",
        height=150,
        placeholder="例如：高级 AI 产品经理，要求熟悉 LLM 应用和 RAG 架构...",
        value="""岗位职责:
1.负责AI智能客服工具全生命周期规划、设计与迭代
2.挖掘B端客户客服痛点，结合大模型/RAG技术落地

任职要求:
1.对AI技术有深刻理解，具备敏锐的市场洞察力
2.有B端的SaaS产品经验，AI客服/智能交互产品核心经验""",
        label_visibility="collapsed"
    )
    
    # 公司信息 (可选)
    st.markdown('<p class="step-hint">选填：公司信息</p>', unsafe_allow_html=True)
    company_info = st.text_input(
        "公司信息",
        placeholder="大厂、创业公司、外企等（主要业务、规模大小）",
        label_visibility="collapsed"
    )
    st.markdown('<p style="font-size: 0.8rem; color: #9ca3af; margin-top: 0.3rem;">提供公司信息可以让面试题目更贴近实际场景</p>', unsafe_allow_html=True)
    
    st.markdown('<div style="height: 1rem"></div>', unsafe_allow_html=True)
    
    # Step 3: 面试问题数量
    st.markdown('''
    <div class="step-title">
        <span class="step-number">3</span>
        面试问题数量 (3-10)
    </div>
    ''', unsafe_allow_html=True)
    
    col_slider, col_value = st.columns([5, 1])
    with col_slider:
        st.session_state.questions_per_round = st.slider(
            "问题数量",
            min_value=3,
            max_value=10,
            value=st.session_state.questions_per_round,
            label_visibility="collapsed"
        )
    with col_value:
        st.markdown(f'<div style="text-align: center; font-size: 1.5rem; font-weight: 600; color: #00B8A9; padding-top: 0.5rem;">{st.session_state.questions_per_round}</div>', unsafe_allow_html=True)
    
    st.markdown('<p style="font-size: 0.8rem; color: #9ca3af;">建议设置为 5 个问题，既能充分展示能力，又不会过于疲劳</p>', unsafe_allow_html=True)
    
    st.markdown('<div style="height: 1rem"></div>', unsafe_allow_html=True)
    
    # Step 4: 面试模式
    st.markdown('''
    <div class="step-title">
        <span class="step-number">4</span>
        面试模式
    </div>
    ''', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('''
        <div class="mode-card active" style="display: flex; align-items: center; justify-content: space-between;">
            <div style="display: flex; align-items: center;">
                <span class="mode-icon">💬</span>
                <div>
                    <div class="mode-title">文字对话</div>
                    <div class="mode-desc">打字回答问题</div>
                </div>
            </div>
            <span class="check-icon">✓</span>
        </div>
        ''', unsafe_allow_html=True)
    with col2:
        st.markdown('''
        <div class="mode-card" style="display: flex; align-items: center; opacity: 0.5;">
            <span class="mode-icon">🎙️</span>
            <div>
                <div class="mode-title">语音对话</div>
                <div class="mode-desc">即将推出</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown('<div style="height: 1.5rem"></div>', unsafe_allow_html=True)
    
    # 开始面试按钮
    if st.button("🚀 开始面试", type="primary", use_container_width=True):
        if len(jd_text) < 30:
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
    
    # 检查数据库是否可用
    if not is_db_available():
        st.warning("⚠️ 数据库连接失败，历史记录功能暂不可用。\n\n请检查 DATABASE_URL 配置是否正确。")
        return
    
    try:
        db = get_db_session()
        interviews = history_service.get_all_interviews(db)
        
        if not interviews:
            st.info("暂无历史记录")
            db.close()
            return
        
        for interview in interviews:
            with st.expander(f"{interview.created_at.strftime('%Y-%m-%d %H:%M')} - {interview.job_title} ({interview.company_scale})"):
                # 基本信息
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**岗位**: {interview.job_title}")
                    st.markdown(f"**公司规模**: {interview.company_scale}")
                with col2:
                    if interview.overall_score:
                        st.markdown(f"**综合得分**: {interview.overall_score:.1f}")
                
                # 显示每一轮次
                for round_obj in interview.rounds:
                    st.markdown(f"---")
                    st.markdown(f"#### 🎙️ 第 {round_obj.round_number} 轮面试")
                    
                    # 显示每道题目
                    for q in round_obj.questions:
                        with st.container():
                            # 题目
                            st.markdown(f"**[{q.difficulty}] {q.text}**")
                            
                            # 用户回答
                            if q.answer:
                                st.markdown(f"💬 **候选人回答**: {q.answer[:200]}..." if len(q.answer or '') > 200 else f"💬 **候选人回答**: {q.answer}")
                            else:
                                st.markdown("💬 **候选人回答**: (未作答)")
                            
                            # 评估结果
                            if q.score is not None:
                                score_color = "🟢" if q.score >= 7 else ("🟡" if q.score >= 5 else "🔴")
                                st.markdown(f"{score_color} **得分**: {q.score}/10")
                                
                                # 如果有详细评估
                                if q.evaluation_json:
                                    eval_data = q.evaluation_json
                                    if isinstance(eval_data, dict):
                                        strengths = eval_data.get("strengths", [])
                                        weaknesses = eval_data.get("weaknesses", [])
                                        if strengths:
                                            st.success("✅ " + " | ".join(strengths[:3]))
                                        if weaknesses:
                                            st.warning("⚠️ " + " | ".join(weaknesses[:3]))
                            
                            st.markdown("")  # 间距
        
        db.close()
    except Exception as e:
        st.error(f"加载历史记录失败: {e}")

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
