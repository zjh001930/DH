# backend/config/settings.py
import os

# --- LLM/Ollama 配置 (来自 docker-compose.yml) ---
# 默认使用 Docker 内部网络的服务名
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://ollama_host:11434")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "llama3")           # 用于生成回答
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "bge-m3") # 用于向量化

# --- 数据库配置 ---
# 使用 docker-compose.yml 中设置的 DATABASE_URL 环境变量
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/ai_assistant")

# --- Weaviate 配置 ---
WEAVIATE_HOST = os.getenv("WEAVIATE_HOST", "weaviate:8080")
WEAVIATE_URL = f"http://{WEAVIATE_HOST}"
WEAVIATE_RAG_CLASS = "AssistantKnowledge" # RAG 知识库的 Weaviate 类名

# --- 业务逻辑配置 ---
INTENT_CONFIDENCE_THRESHOLD = 0.75
IMAGE_STORAGE_PATH = os.getenv("IMAGE_STORAGE_PATH", "/app/data/images")