# backend/config/settings.py
import os

# --- LLM/Ollama 配置 (来自 docker-compose.yml) ---
# 默认使用 Docker 内部网络的服务名
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://ollama_service:11434")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "llama3")           # 用于生成回答
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "bge-3") # 用于向量化

# --- 数据库配置 ---
# 注意：在 Docker 容器内使用 'db'，本地运行时使用 'localhost'
DB_HOST = os.getenv("DB_HOST", "localhost")  # 默认改为 localhost 以支持本地运行
DB_USER = os.getenv("DB_USER", "assistant_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "strong_password")
DB_NAME = os.getenv("DB_NAME", "assistant_db")
SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"

# --- Weaviate 配置 ---
WEAVIATE_HOST = os.getenv("WEAVIATE_HOST", "weaviate:8080")
WEAVIATE_URL = f"http://{WEAVIATE_HOST}"
WEAVIATE_RAG_CLASS = "AssistantKnowledge" # RAG 知识库的 Weaviate 类名

# --- 业务逻辑配置 ---
INTENT_CONFIDENCE_THRESHOLD = 0.75
IMAGE_STORAGE_PATH = os.getenv("IMAGE_STORAGE_PATH", "/app/data/images")