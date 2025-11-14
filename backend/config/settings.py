# backend/config/settings.py
import os

# --- LLM策略配置 ---
LLM_STRATEGY = os.getenv("LLM_STRATEGY", "local")  # "local" 或 "api"

# --- LLM/Ollama 配置 (本地策略) ---
# 默认使用 Docker 内部网络的服务名
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "qwen2.5:3b-instruct")           # 用于生成回答
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "bge-m3") # 用于向量化

# --- API策略配置 ---
API_KEY = os.getenv("API_KEY", "")  # OpenAI/Claude等API密钥
API_MODEL_NAME = os.getenv("API_MODEL_NAME", "gpt-3.5-turbo")  # API模型名称
API_EMBEDDING_MODEL = os.getenv("API_EMBEDDING_MODEL", "text-embedding-ada-002")  # API嵌入模型

# --- 数据库配置 ---
# 使用 docker-compose.yml 中设置的 DATABASE_URL 环境变量
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/ai_assistant")

# --- Weaviate 配置 ---
WEAVIATE_HOST = os.getenv("WEAVIATE_HOST", "weaviate:8080")
WEAVIATE_URL = os.getenv("WEAVIATE_URL", f"http://{WEAVIATE_HOST}")
WEAVIATE_RAG_CLASS = os.getenv("WEAVIATE_RAG_CLASS", "AssistantKnowledge")
WEAVIATE_AUTO_VECTORIZE = os.getenv("WEAVIATE_AUTO_VECTORIZE", "false").lower() == "true"

# # --- 向量生成策略 ---
# WEAVIATE_AUTO_VECTORIZE = os.getenv("WEAVIATE_AUTO_VECTORIZE", "false").lower() == "true"

# --- 业务逻辑配置 ---
INTENT_CONFIDENCE_THRESHOLD = 0.65
IMAGE_STORAGE_PATH = os.getenv("IMAGE_STORAGE_PATH", "/app/data/images")