# ==== 新增：HTTP 回退工具 ====
import requests
import re


def _get_fallback_url(base_url: str) -> str:
    """获取回退URL，如果原始URL是容器内地址，则尝试使用localhost"""
    # 如果URL包含容器名（如weaviate），则添加localhost作为回退
    if re.search(r'://(weaviate|weaviate-service)', base_url):
        # 提取端口号
        match = re.search(r':(\d+)$', base_url)
        if match:
            port = match.group(1)
            return f"http://localhost:{port}"
    return base_url


def _http_is_ready(timeout: int = 5) -> bool:
    try:
        r = requests.get(f"{WEAVIATE_URL}/v1/.well-known/ready", timeout=timeout)
        return r.status_code == 200
    except Exception as e:
        logger.error(f"[WEAVIATE-HTTP] 就绪检查失败: {e}")
        # 尝试回退URL
        try:
            fallback_url = _get_fallback_url(WEAVIATE_URL)
            if fallback_url != WEAVIATE_URL:
                logger.info(f"[WEAVIATE-HTTP] 尝试回退URL: {fallback_url}")
                r = requests.get(f"{fallback_url}/v1/.well-known/ready", timeout=timeout)
                return r.status_code == 200
        except Exception as fallback_e:
            logger.error(f"[WEAVIATE-HTTP] 回退URL检查失败: {fallback_e}")
        return False


def _http_get_schema() -> Dict[str, Any]:
    try:
        r = requests.get(f"{WEAVIATE_URL}/v1/schema", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error(f"[WEAVIATE-HTTP] 获取 schema 失败: {e}")
        # 尝试回退URL
        try:
            fallback_url = _get_fallback_url(WEAVIATE_URL)
            if fallback_url != WEAVIATE_URL:
                logger.info(f"[WEAVIATE-HTTP] 尝试回退URL: {fallback_url}")
                r = requests.get(f"{fallback_url}/v1/schema", timeout=10)
                r.raise_for_status()
                return r.json()
        except Exception as fallback_e:
            logger.error(f"[WEAVIATE-HTTP] 回退URL获取 schema 失败: {fallback_e}")
        return {}


def _http_create_class(knowledge_class: Dict[str, Any]) -> bool:
    try:
        r = requests.post(f"{WEAVIATE_URL}/v1/schema", json=knowledge_class, timeout=15)
        if r.status_code in (200, 201):
            return True
        logger.error(f"[WEAVIATE-HTTP] 创建类失败: {r.status_code} {r.text}")
        return False
    except Exception as e:
        logger.error(f"[WEAVIATE-HTTP] 创建类异常: {e}")
        # 尝试回退URL
        try:
            fallback_url = _get_fallback_url(WEAVIATE_URL)
            if fallback_url != WEAVIATE_URL:
                logger.info(f"[WEAVIATE-HTTP] 尝试回退URL: {fallback_url}")
                r = requests.post(f"{fallback_url}/v1/schema", json=knowledge_class, timeout=15)
                if r.status_code in (200, 201):
                    return True
                logger.error(f"[WEAVIATE-HTTP] 回退URL创建类失败: {r.status_code} {r.text}")
        except Exception as fallback_e:
            logger.error(f"[WEAVIATE-HTTP] 回退URL创建类异常: {fallback_e}")
        return False


def _http_batch_insert(knowledge_list: List[Dict[str, Any]], vectors: List[List[float]]) -> int:
    try:
        objects = []
        for data, vec in zip(knowledge_list, vectors):
            objects.append({
                "class": WEAVIATE_RAG_CLASS,
"properties": data,
                "vector": vec
            })
        payload = {"objects": objects}
        r = requests.post(f"{WEAVIATE_URL}/v1/objects/batch", json=payload, timeout=30)
        if r.status_code not in (200, 202):
            logger.error(f"[WEAVIATE-HTTP] 批量写入失败: {r.status_code} {r.text}")
            return 0
        body = r.json()
        # Weaviate 会返回 per-object 结果，尽量统计成功数
        results = body.get("objects", []) or body.get("results", [])
        success = 0
        for item in results:
            status = item.get("status") or item.get("result", {}).get("status")
            if (isinstance(status, str) and status.upper() == "SUCCESS") or ("errors" not in item):
                success += 1
        if not results:  # 某些版本无逐项回执，认为整体成功
            success = len(objects)
        return success
    except Exception as e:
        logger.error(f"[WEAVIATE-HTTP] 批量写入异常: {e}")
        # 尝试回退URL
        try:
            fallback_url = _get_fallback_url(WEAVIATE_URL)
            if fallback_url != WEAVIATE_URL:
                logger.info(f"[WEAVIATE-HTTP] 尝试回退URL: {fallback_url}")
                objects = []
                for data, vec in zip(knowledge_list, vectors):
                    objects.append({
                        "class": WEAVIATE_RAG_CLASS,
                        "properties": data,
                        "vector": vec
                    })
                payload = {"objects": objects}
                r = requests.post(f"{fallback_url}/v1/objects/batch", json=payload, timeout=30)
                if r.status_code not in (200, 202):
                    logger.error(f"[WEAVIATE-HTTP] 回退URL批量写入失败: {r.status_code} {r.text}")
                    return 0
                body = r.json()
                # Weaviate 会返回 per-object 结果，尽量统计成功数
                results = body.get("objects", []) or body.get("results", [])
                success = 0
                for item in results:
                    status = item.get("status") or item.get("result", {}).get("status")
                    if (isinstance(status, str) and status.upper() == "SUCCESS") or ("errors" not in item):
                        success += 1
                if not results:  # 某些版本无逐项回执，认为整体成功
                    success = len(objects)
                return success
        except Exception as fallback_e:
            logger.error(f"[WEAVIATE-HTTP] 回退URL批量写入异常: {fallback_e}")
        return 0


def _http_graphql(query: str) -> Dict[str, Any]:
    try:
        r = requests.post(f"{WEAVIATE_URL}/v1/graphql", json={"query": query}, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error(f"[WEAVIATE-HTTP] GraphQL 请求失败: {e}")
        # 尝试回退URL
        try:
            fallback_url = _get_fallback_url(WEAVIATE_URL)
            if fallback_url != WEAVIATE_URL:
                logger.info(f"[WEAVIATE-HTTP] 尝试回退URL: {fallback_url}")
                r = requests.post(f"{fallback_url}/v1/graphql", json={"query": query}, timeout=15)
                r.raise_for_status()
                return r.json()
        except Exception as fallback_e:
            logger.error(f"[WEAVIATE-HTTP] 回退URL GraphQL 请求失败: {fallback_e}")
        return {}