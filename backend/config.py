"""
AIPM-Scan 配置管理
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

# 获取当前文件所在目录的 .env 路径
BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"


def get_secret(key: str, default: str = "") -> str:
    """
    获取配置值，优先级：
    1. 环境变量
    2. Streamlit secrets (用于 Streamlit Cloud)
    3. 默认值
    """
    # 先检查环境变量
    value = os.environ.get(key)
    if value:
        return value
    
    # 再检查 Streamlit secrets
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    
    return default


class Settings(BaseSettings):
    """应用配置"""
    
    # LLM API 配置（OpenAI 兼容格式）
    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com"
    llm_model: str = "deepseek-chat"
    
    # RAGFlow API 配置
    ragflow_api_key: str = ""
    ragflow_api_base: str = "http://localhost:9380"
    ragflow_dataset_id: str = ""
    
    # 应用配置
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    
    class Config:
        env_file = str(ENV_FILE)
        env_file_encoding = "utf-8"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 如果 pydantic 没有从 .env 读取到值，尝试从 Streamlit secrets 读取
        if not self.llm_api_key:
            self.llm_api_key = get_secret("DEEPSEEK_API_KEY") or get_secret("LLM_API_KEY")
        if not self.llm_base_url or self.llm_base_url == "https://api.deepseek.com":
            self.llm_base_url = get_secret("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        if not self.ragflow_api_key:
            self.ragflow_api_key = get_secret("RAGFLOW_API_KEY")
        if not self.ragflow_api_base or self.ragflow_api_base == "http://localhost:9380":
            self.ragflow_api_base = get_secret("RAGFLOW_HOST", "http://localhost:9380")


# 全局配置实例
settings = Settings()


# 六维能力模型定义
ABILITY_DIMENSIONS = {
    "business_decomposition": {
        "name": "业务拆解能力",
        "name_en": "business_decomposition",
        "description": "将复杂问题分解为可执行任务的能力",
        "keywords": ["需求分析", "任务拆解", "优先级", "WBS", "可行性", "MVP"]
    },
    "ai_tech_understanding": {
        "name": "AI技术理解",
        "name_en": "ai_tech_understanding",
        "description": "对AI技术原理和应用的掌握程度",
        "keywords": ["机器学习", "深度学习", "NLP", "LLM", "算法", "模型", "训练", "推理", "RAG"]
    },
    "business_awareness": {
        "name": "商业意识",
        "name_en": "business_awareness",
        "description": "理解商业价值和ROI的能力",
        "keywords": ["ROI", "商业模式", "成本", "收益", "营收", "增长", "变现", "LTV"]
    },
    "system_thinking": {
        "name": "系统思维",
        "name_en": "system_thinking",
        "description": "全局视角和架构能力",
        "keywords": ["架构", "系统", "全局", "长期", "扩展性", "边界", "耦合"]
    },
    "execution_power": {
        "name": "推动能力",
        "name_en": "execution_power",
        "description": "跨团队协作和项目推进能力",
        "keywords": ["协作", "沟通", "推动", "协调", "资源", "冲突", "团队"]
    },
    "risk_awareness": {
        "name": "风险意识",
        "name_en": "risk_awareness",
        "description": "识别和应对潜在风险的能力",
        "keywords": ["风险", "安全", "合规", "预案", "隐私", "GDPR", "偏见"]
    }
}
