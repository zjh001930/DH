import os
import sys
import logging
from typing import List, Dict, Any

# 修复 Python 模块的相对导入路径
# 将 .. 添加到 sys.path, 允许 Python 找到 llm, db, config 文件夹
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from llm.ollama_client import OllamaClient
    from db.vector_repo import retrieve_context, get_knowledge_count
    from config.settings import LLM_MODEL_NAME
except ImportError as e:
    logging.error(f"RAGHandler 导入失败: {e}")
    # This is a fallback for PyCharm's linter
    from ..llm.ollama_client import OllamaClient
    from ..db.vector_repo import retrieve_context, get_knowledge_count
    from ..config.settings import LLM_MODEL_NAME

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(filename)s] %(message)s')
logger = logging.getLogger(__name__)


class RAGHandler:
    """
    RAG (检索增强生成) 处理器.
    负责协调 Ollama (向量化 + 生成) 和 Weaviate (检索).
    """

    def __init__(self):
        """
        初始化 RAG 处理器.
        """
        self.ollama_client = OllamaClient()
        logger.info("[RAG_HANDLER] RAG 处理器已初始化.")

    def _check_knowledge_base(self) -> bool:
        """
        检查知识库中是否有数据。
        """
        try:
            count = get_knowledge_count()
            if count > 0:
                logger.info(f"知识库检查通过, 共有 {count} 条记录。")
                return True
            else:
                logger.warning("知识库检查失败: Weaviate 中有 0 条知识记录。")
                return False
        except Exception as e:
            logger.error(f"检查知识库时出错: {e}")
            return False

    def _build_prompt(self, user_input: str, contexts: List[str]) -> str:
        """
        根据检索到的上下文和用户问题构建最终的 Prompt。
        """
        if not contexts:
            # 如果没有检索到上下文，直接返回原始问题（或一个特定提示）
            return f"请基于你的知识回答以下问题: {user_input}"

        context_str = "\n\n".join(contexts)

        # Prompt 模板
        prompt = f"""
        你是一个专业的 AI 助手。请根据下面提供的上下文信息来回答用户的问题。
        如果上下文信息不足以回答问题，请使用 "根据我的知识..." 来回答。

        【上下文信息】:
        {context_str}

        【用户问题】:
        {user_input}

        【你的回答】:
        """
        return prompt.strip()

    def answer_question(self, user_input: str) -> Dict[str, Any]:
        """
        RAG 问答的主流程。
        """

        # 1. 检查知识库是否已导入数据
        if not self._check_knowledge_base():
            logger.warning("[RAG_HANDLER] 知识库为空, 终止 RAG 流程。")
            return {
                "answer": "抱歉，知识库尚未导入。请先导入知识库文件。",
                "sources": []
            }

        # 2. 向量化用户问题 (使用 Ollama BGE-3)
        try:
            query_vector = self.ollama_client.get_embedding(user_input)
            logger.info("[RAG_HANDLER] 用户问题向量化成功。")
        except Exception as e:
            logger.error(f"[RAG_HANDLER] 调用 Ollama 嵌入模型失败: {e}")
            return {
                "answer": "抱歉，连接嵌入模型时出错，无法处理您的问题。",
                "sources": []
            }

        # 3. 检索上下文 (调用 Weaviate)
        try:
            contexts = retrieve_context(query_vector)
            logger.info(f"[RAG_HANDLER] 从 Weaviate 检索到 {len(contexts)} 条上下文。")
        except Exception as e:
            logger.error(f"[RAG_HANDLER] 调用 Weaviate 检索失败: {e}")
            return {
                "answer": "抱歉，连接向量数据库时出错，无法检索知识。",
                "sources": []
            }

        # 4. 构建 Prompt
        prompt = self._build_prompt(user_input, contexts)

        # 5. 生成答案 (调用 Ollama Llama 3)
        try:
            answer = self.ollama_client.generate_response(prompt)

            # 【语法错误修复】
            # 替换掉之前导致崩溃的多行 f-string
            logger.info(f"[RAG_HANDLER] Ollama 生成答案成功。")

            return {
                "answer": answer,
                "sources": [ctx.split('\n')[0] for ctx in contexts]  # 提取来源 (简化)
            }
        except Exception as e:
            logger.error(f"[RAG_HANDLER] 调用 Ollama 生成模型失败: {e}")
            return {
                "answer": "抱歉，连接 LLM 生成模型时出错，无法生成答案。",
                "sources": []
            }

