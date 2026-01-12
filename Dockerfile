# 使用官方 Python 基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装必要的系统库 (如果需要 SQLite 支持或其他编译依赖)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY backend/requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制后端代码
COPY backend/ ./backend/
# 复制知识库文件 (如果 RAGFlow 需要本地文件索引，或者应用需要读取本地 Markdown)
COPY knowledge_base/ ./knowledge_base/

# 设置 Python 路径，确保 backend 包可被导入
ENV PYTHONPATH=/app

# 暴露 Streamlit 默认端口
EXPOSE 8501

# 启动命令
CMD ["streamlit", "run", "backend/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
