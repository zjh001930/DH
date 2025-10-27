# backend/llm/ollama_client.py

import requests
import json
# 使用相对导入来引用同父级或更高父级目录的模块
from config.settings import OLLAMA_API_URL, LLM_MODEL_NAME, EMBEDDING_MODEL_NAME


class OllamaClient:
    """封装与本地 Ollama 服务的 API 交互逻辑"""

    def __init__(self):
        self.api_url = OLLAMA_API_URL
        self.llm_model = LLM_MODEL_NAME
        self.embed_model = EMBEDDING_MODEL_NAME
        print(f"[OLLAMA_CLIENT] Initialized. LLM: {self.llm_model}, Embed: {self.embed_model}")

    def get_embedding(self, text: str) -> list:
        """调用 Ollama 的 /api/embeddings 接口获取文本向量。"""
        url = f"{self.api_url}/api/embeddings"
        payload = {"model": self.embed_model, "prompt": text}

        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()['embedding']
        except requests.exceptions.RequestException as e:
            # 给出更详细的错误信息，帮助调试
            raise ConnectionError(f"[OLLAMA_CLIENT] Embedding API 连接失败，请确认 Ollama 已启动并模型已加载: {e}")

    def generate_response(self, prompt: str) -> str:
        """调用 Ollama 的 /api/generate 接口生成回答。"""
        url = f"{self.api_url}/api/generate"
        payload = {"model": self.llm_model, "prompt": prompt, "stream": False}

        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            if 'response' in response.json():
                return response.json()['response']
            return str(response.json())  # 返回原始 JSON 字符串
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"[OLLAMA_CLIENT] Generate API 连接失败: {e}")
