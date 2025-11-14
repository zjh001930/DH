import os
import sys
import logging
from typing import List, Dict, Any

# === 修正 Python 模块路径（容器内以 /app 运行） ===
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# === 统一使用绝对导入（不要再有 .. 相对导入） ===
from llm.ollama_client import OllamaClient
from db.vector_repo import retrieve_context, get_knowledge_count
from config.settings import LLM_MODEL_NAME, WEAVIATE_AUTO_VECTORIZE  # 若未使用也保留以便配置集中

# === 配置日志 ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(filename)s] %(message)s"
)
logger = logging.getLogger(__name__)


class RAGHandler:
    """
    RAG (检索增强生成) 处理器
    负责协调 Ollama (向量化 + 生成) 和 Weaviate (检索)
    """

    def __init__(self):
        self.ollama_client = OllamaClient()
        logger.info("[RAG_HANDLER] RAG 处理器已初始化.")

    def _check_knowledge_base(self) -> bool:
        """检查知识库是否有数据"""
        try:
            count = get_knowledge_count()
            if count > 0:
                logger.info(f"知识库检查通过, 共 {count} 条记录.")
                return True
            logger.warning("知识库检查失败: Weaviate 中记录为 0.")
            return False
        except Exception as e:
            logger.error(f"检查知识库时出错: {e}")
            return False

    def _build_prompt(self, user_input: str, contexts: List[str]) -> str:
        """构建最终 Prompt"""
        if not contexts:
            return f"请基于你的知识回答以下问题: {user_input}"

        context_str = "\n\n".join(contexts)
        prompt = f"""
你是一个专业的 AI 助手。请遵守以下规则：
- 如果用户只是打招呼或寒暄（如“你好”、“您好”、“hi”），只回复“你好，有什么可以帮助你的吗？”
- 不要复述历史；避免引用会话记忆。
- 仅在用户提出明确问题或任务时，基于上下文提供答案。

【上下文信息】:
{context_str}

【用户问题】:
{user_input}

【你的回答】:
"""
        return prompt.strip()

    def answer_question(self, user_input: str) -> Dict[str, Any]:
        """主流程：检索 + 生成"""
        t = (user_input or "").strip().lower()
        if any(g in t for g in ["你好", "您好", "hi", "hello", "hey", "嗨", "在吗"]):
            return {"answer": "你好，有什么可以帮助你的吗？", "sources": []}

        # 1. 检查知识库
        if not self._check_knowledge_base():
            logger.warning("[RAG_HANDLER] 知识库为空，终止流程。")
            return {
                "answer": "抱歉，知识库尚未导入。请先导入知识库文件。",
                "sources": []
            }

        try:
            if WEAVIATE_AUTO_VECTORIZE:
                contexts = retrieve_context(user_input)
            else:
                query_vector = self.ollama_client.get_embedding(user_input)
                logger.info("[RAG_HANDLER] 用户问题向量化成功。")
                contexts = retrieve_context(query_vector)
            logger.info(f"[RAG_HANDLER] 检索到 {len(contexts)} 条上下文。")
        except Exception as e:
            try:
                contexts = retrieve_context(user_input)
                logger.info(f"[RAG_HANDLER] 检索到 {len(contexts)} 条上下文。")
            except Exception as e2:
                logger.error(f"[RAG_HANDLER] 调用 Weaviate 检索失败: {e2}")
                return {"answer": "抱歉，连接向量数据库出错。", "sources": []}

        # 4. 构建 Prompt
        prompt = self._build_prompt(user_input, contexts)

        # 5. 调用 LLM 生成答案
        try:
            answer = self.ollama_client.generate_response(prompt)
            logger.info("[RAG_HANDLER] Ollama 生成答案成功。")
            return {
                "answer": answer,
                "sources": [ctx.split('\n')[0] for ctx in contexts]
            }
        except Exception as e:
            logger.error(f"[RAG_HANDLER] 调用 Ollama 生成模型失败: {e}")
            return {"answer": "抱歉，生成答案时出错。", "sources": []}
