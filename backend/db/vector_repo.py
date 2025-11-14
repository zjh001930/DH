from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List

import requests

# 统一从 config.settings 读取；若 WEAVIATE_RAG_CLASS 不存在，用默认类名
try:
    from config.settings import WEAVIATE_URL, WEAVIATE_RAG_CLASS, WEAVIATE_AUTO_VECTORIZE  # type: ignore
except Exception:
    from config.settings import WEAVIATE_URL  # type: ignore
    WEAVIATE_RAG_CLASS = "Knowledge"
    WEAVIATE_AUTO_VECTORIZE = False

logger = logging.getLogger(__name__)


# ---------- URL 回退（容器名 -> localhost） ----------
def _get_fallback_url(base_url: str) -> str:
    """
    如果 URL 指向容器名（weaviate/weaviate-service），改用 localhost:port 作为回退。
    """
    try:
        if re.search(r'://(weaviate|weaviate-service)', base_url):
            m = re.search(r':(\d+)(?:/|$)', base_url)
            if m:
                return f"http://localhost:{m.group(1)}"
    except Exception:
        pass
    return base_url


# ---------- 健康检查 ----------
def _http_is_ready(timeout: int = 5) -> bool:
    url = f"{WEAVIATE_URL}/v1/.well-known/ready"
    try:
        r = requests.get(url, timeout=timeout)
        return r.status_code == 200
    except Exception as e:
        logger.error("[WEAVIATE-HTTP] 就绪检查失败: %s", e)
        fb = _get_fallback_url(WEAVIATE_URL)
        if fb != WEAVIATE_URL:
            try:
                r = requests.get(f"{fb}/v1/.well-known/ready", timeout=timeout)
                return r.status_code == 200
            except Exception as e2:
                logger.error("[WEAVIATE-HTTP] 回退URL就绪检查失败: %s", e2)
        return False


# ---------- Schema 相关 ----------
def _http_get_schema() -> dict[str, Any]:
    url = f"{WEAVIATE_URL}/v1/schema"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error("[WEAVIATE-HTTP] 获取 schema 失败: %s", e)
        fb = _get_fallback_url(WEAVIATE_URL)
        if fb != WEAVIATE_URL:
            try:
                r = requests.get(f"{fb}/v1/schema", timeout=10)
                r.raise_for_status()
                return r.json()
            except Exception as e2:
                logger.error("[WEAVIATE-HTTP] 回退URL获取 schema 失败: %s", e2)
        return {}


def _http_create_class(knowledge_class: dict[str, Any]) -> bool:
    url = f"{WEAVIATE_URL}/v1/schema"
    try:
        r = requests.post(url, json=knowledge_class, timeout=15)
        if r.status_code in (200, 201):
            return True
        logger.error("[WEAVIATE-HTTP] 创建类失败: %s %s", r.status_code, r.text)
    except Exception as e:
        logger.error("[WEAVIATE-HTTP] 创建类异常: %s", e)
        fb = _get_fallback_url(WEAVIATE_URL)
        if fb != WEAVIATE_URL:
            try:
                r = requests.post(f"{fb}/v1/schema", json=knowledge_class, timeout=15)
                return r.status_code in (200, 201)
            except Exception as e2:
                logger.error("[WEAVIATE-HTTP] 回退URL创建类异常: %s", e2)
    return False


# ---------- 批量写入 ----------
def _http_batch_insert(
    knowledge_list: list[dict[str, Any]],
    vectors: list[list[float]]
) -> int:
    try:
        if vectors and len(vectors) == len(knowledge_list):
            objects = [
                {"class": WEAVIATE_RAG_CLASS, "properties": data, "vector": vec}
                for data, vec in zip(knowledge_list, vectors)
            ]
        else:
            objects = [
                {"class": WEAVIATE_RAG_CLASS, "properties": data}
                for data in knowledge_list
            ]
        payload = {"objects": objects}
        r = requests.post(f"{WEAVIATE_URL}/v1/batch/objects", json=payload, timeout=30)
        if r.status_code not in (200, 202):
            logger.error("[WEAVIATE-HTTP] 批量写入失败: %s %s", r.status_code, r.text)
            return 0
        body = r.json()
        if isinstance(body, list):
            results = body
        else:
            results = body.get("objects") or body.get("results") or body.get("Object") or []
        if not results:
            return len(objects)
        success = 0
        for item in results:
            status = item.get("status") or (item.get("result") or {}).get("status")
            if isinstance(status, str) and status.upper() == "SUCCESS":
                success += 1
            elif "errors" not in item:
                success += 1
        return success
    except Exception as e:
        logger.error("[WEAVIATE-HTTP] 批量写入异常: %s", e)
        fb = _get_fallback_url(WEAVIATE_URL)
        if fb != WEAVIATE_URL:
            try:
                if vectors and len(vectors) == len(knowledge_list):
                    payload = {
                        "objects": [
                            {"class": WEAVIATE_RAG_CLASS, "properties": d, "vector": v}
                            for d, v in zip(knowledge_list, vectors)
                        ]
                    }
                else:
                    payload = {
                        "objects": [
                            {"class": WEAVIATE_RAG_CLASS, "properties": d}
                            for d in knowledge_list
                        ]
                    }
                r = requests.post(f"{fb}/v1/batch/objects", json=payload, timeout=30)
                if r.status_code not in (200, 202):
                    logger.error("[WEAVIATE-HTTP] 回退URL批量写入失败: %s %s", r.status_code, r.text)
                    return 0
                body = r.json()
                if isinstance(body, list):
                    results = body
                else:
                    results = body.get("objects") or body.get("results") or body.get("Object") or []
                if not results:
                    return len(payload["objects"])
                success = 0
                for item in results:
                    status = item.get("status") or (item.get("result") or {}).get("status")
                    if isinstance(status, str) and status.upper() == "SUCCESS":
                        success += 1
                    elif "errors" not in item:
                        success += 1
                return success
            except Exception as e2:
                logger.error("[WEAVIATE-HTTP] 回退URL批量写入异常: %s", e2)
        return 0


# ---------- GraphQL ----------
def _http_graphql(query: str) -> dict[str, Any]:
    try:
        r = requests.post(f"{WEAVIATE_URL}/v1/graphql", json={"query": query}, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error("[WEAVIATE-HTTP] GraphQL 请求失败: %s", e)
        fb = _get_fallback_url(WEAVIATE_URL)
        if fb != WEAVIATE_URL:
            try:
                r = requests.post(f"{fb}/v1/graphql", json={"query": query}, timeout=15)
                r.raise_for_status()
                return r.json()
            except Exception as e2:
                logger.error("[WEAVIATE-HTTP] 回退URL GraphQL 请求失败: %s", e2)
        return {}

# ---------- Public API for Data Ingestion ----------

KNOWLEDGE_CLASS_SCHEMA = {
    "class": WEAVIATE_RAG_CLASS,
    "description": "A class to store knowledge base articles (question-answer pairs).",
    "properties": [
        {"name": "question", "dataType": ["text"], "description": "The question part of the QA pair."},
        {"name": "answer", "dataType": ["text"], "description": "The answer part of the QA pair."},
        {"name": "category", "dataType": ["text"], "description": "Category of the knowledge."},
        {"name": "source", "dataType": ["text"], "description": "Source of the knowledge (e.g., filename)."},
        {"name": "keywords", "dataType": ["text[]"], "description": "Keywords associated with the knowledge."},
    ],
}
if not WEAVIATE_AUTO_VECTORIZE:
    KNOWLEDGE_CLASS_SCHEMA["vectorizer"] = "none"

def initialize_weaviate() -> bool:
    """
    Initializes Weaviate by checking readiness and ensuring the schema class exists.
    """
    logger.info("[WEAVIATE] Initializing Weaviate...")
    if not _http_is_ready(timeout=30):
        logger.error("[WEAVIATE] Weaviate instance is not ready.")
        return False
    
    logger.info("[WEAVIATE] Weaviate is ready.")
    
    schema = _http_get_schema()
    if schema and "classes" in schema:
        if any(c["class"] == WEAVIATE_RAG_CLASS for c in schema["classes"]):
            logger.info(f"[WEAVIATE] Class '{WEAVIATE_RAG_CLASS}' already exists.")
            return True
    
    logger.info(f"[WEAVIATE] Class '{WEAVIATE_RAG_CLASS}' not found. Creating it...")
    if _http_create_class(KNOWLEDGE_CLASS_SCHEMA):
        logger.info(f"[WEAVIATE] Class '{WEAVIATE_RAG_CLASS}' created successfully.")
        return True
    else:
        logger.error(f"[WEAVIATE] Failed to create class '{WEAVIATE_RAG_CLASS}'.")
        return False

def batch_insert_knowledge(
    knowledge_list: list[dict[str, Any]],
    vectors: list[list[float]]
) -> int:
    """
    Public function to batch insert knowledge. Wraps the internal HTTP function.
    """
    if not knowledge_list:
        return 0
    return _http_batch_insert(knowledge_list, vectors)


# ---------- 导出给 RAG 使用 ----------
def retrieve_context(query: Any, top_k: int = 3) -> list[str]:
    """
    兼容两种输入：
    - 若 query 是向量(list[float])：使用 nearVector 检索；
    - 若 query 是字符串：使用 bm25 检索。
    统一返回：每条上下文以字符串形式给到上层（便于拼接 Prompt）。
    """
    if not _http_is_ready():
        logger.warning("[WEAVIATE] 实例未就绪，返回空上下文。")
        return []

    try:
        if isinstance(query, (list, tuple)):  # nearVector
            gql = f"""
            {{
              Get {{
                {WEAVIATE_RAG_CLASS}(
                  nearVector: {{ vector: {json.dumps(list(query))} }}
                  limit: {int(top_k)}
                ) {{
                  question
                  answer
                  source
                }}
              }}
            }}
            """
        else:
            if WEAVIATE_AUTO_VECTORIZE:
                gql = f"""
                {{
                  Get {{
                    {WEAVIATE_RAG_CLASS}(
                      nearText: {{ concepts: [{json.dumps(str(query))}] }}
                      limit: {int(top_k)}
                    ) {{
                      question
                      answer
                      source
                    }}
                  }}
                }}
                """
            else:
                gql = f"""
                {{
                  Get {{
                    {WEAVIATE_RAG_CLASS}(
                      bm25: {{ query: {json.dumps(str(query))} }}
                      limit: {int(top_k)}
                    ) {{
                      question
                      answer
                      source
                    }}
                  }}
                }}
                """

        data = _http_graphql(gql)
        hits = (((data or {}).get("data") or {}).get("Get") or {}).get(WEAVIATE_RAG_CLASS, []) or []
        if WEAVIATE_AUTO_VECTORIZE and not isinstance(query, (list, tuple)) and not hits:
            gql_bm25 = f"""
            {{
              Get {{
                {WEAVIATE_RAG_CLASS}(
                  bm25: {{ query: {json.dumps(str(query))} }}
                  limit: {int(top_k)}
                ) {{
                  question
                  answer
                  source
                }}
              }}
            }}
            """
            data2 = _http_graphql(gql_bm25)
            hits = (((data2 or {}).get("data") or {}).get("Get") or {}).get(WEAVIATE_RAG_CLASS, []) or []
        contexts: list[str] = []
        for h in hits:
            question = h.get("question")
            answer = h.get("answer")
            source = h.get("source")
            if answer:
                ctx = f"{answer}"
                if question:
                    ctx = f"{question}\n{answer}"
                if source:
                    ctx = f"{source}\n{ctx}"
                contexts.append(ctx)
        return contexts
    except Exception as e:
        logger.error("[WEAVIATE] retrieve_context 失败: %s", e)
        return []


def get_knowledge_count() -> int:
    """
    返回类 {WEAVIATE_RAG_CLASS} 的对象数量
    """
    if not _http_is_ready():
        return 0
    try:
        gql = f"""
        {{
          Aggregate {{
            {WEAVIATE_RAG_CLASS} {{
              meta {{ count }}
            }}
          }}
        }}
        """
        data = _http_graphql(gql)
        agg = (((data or {}).get("data") or {}).get("Aggregate") or {}).get(WEAVIATE_RAG_CLASS, [])
        if agg and isinstance(agg, list):
            meta = agg[0].get("meta") or {}
            return int(meta.get("count") or 0)
        return 0
    except Exception as e:
        logger.error("[WEAVIATE] get_knowledge_count 失败: %s", e)
        return 0