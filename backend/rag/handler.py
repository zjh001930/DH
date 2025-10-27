# backend/rag/handler.py
# 从 llm 导入 Ollama 客户端
from llm.ollama_client import OllamaClient
# 从 db 导入 Weaviate 检索函数
from db.vector_repo import retrieve_context


class RAGHandler:
    def __init__(self):
        # 实例化 Ollama 客户端，用于向量化和生成
        self.ollama_client = OllamaClient()

    def answer_question(self, query: str) -> dict:
        """
        执行 RAG (检索增强生成) 流程。
        Args:
            query: 用户的开放性问题。
        Returns:
            包含答案和来源的字典。
        """
        print(f"[RAG] Processing query: {query}")

        try:
            # 1. 向量化查询 (使用 BGE-3)
            # OllamaClient 会处理连接错误
            query_vector = self.ollama_client.get_embedding(query)
        except ConnectionError as e:
            return {"answer": f"抱歉，AI 服务连接失败，请检查 Ollama 服务器状态。错误: {e}", "sources": []}

        # 2. 检索上下文 (使用 Weaviate)
        # 模拟调用 Weaviate 仓库进行向量搜索
        context = retrieve_context(query_vector, limit=3)
        context_str = "\n".join(context)

        # 3. 构建 Prompt (用于 Llama 3)
        prompt = (
            f"你是一个专业的AI助手，请用中文回答用户的问题。根据以下知识片段回答用户的问题，如果信息不足，请礼貌地用中文说明。\n\n"
            f"知识片段:\n{context_str}\n\n"
            f"用户问题: {query}\n\n"
            f"请用中文回答："
        )

        # 4. 生成答案
        # OllamaClient 调用 Llama 3 模型
        answer = self.ollama_client.generate_response(prompt)

        return {
            "answer": answer,
            "sources": context  # 返回检索到的知识片段作为来源
        }
