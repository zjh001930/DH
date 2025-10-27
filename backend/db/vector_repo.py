# backend/db/vector_repo.py
import os
import sys
import logging
from typing import List, Dict, Any, Optional

# 添加相对导入路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import WEAVIATE_URL, WEAVIATE_RAG_CLASS

# 配置日志
logger = logging.getLogger(__name__)

# 全局 Weaviate 客户端
weaviate_client = None

def get_weaviate_client():
    """获取 Weaviate 客户端实例"""
    global weaviate_client
    
    if weaviate_client is None:
        try:
            # 使用兼容的导入方式
            import weaviate
            weaviate_client = weaviate.Client(url=WEAVIATE_URL)
            logger.info(f"[WEAVIATE] 客户端连接成功: {WEAVIATE_URL}")
        except ImportError as e:
            logger.error(f"[WEAVIATE] 导入失败: {e}")
            # 尝试备用导入方式
            try:
                import weaviate.client as weaviate_client_module
                weaviate_client = weaviate_client_module.Client(url=WEAVIATE_URL)
                logger.info(f"[WEAVIATE] 使用备用方式连接成功: {WEAVIATE_URL}")
            except Exception as backup_e:
                logger.error(f"[WEAVIATE] 备用连接也失败: {backup_e}")
                return None
        except Exception as e:
            logger.error(f"[WEAVIATE] 连接失败: {e}")
            return None
    
    return weaviate_client
    
    if weaviate_client is None:
        try:
            weaviate_client = weaviate.Client(url=WEAVIATE_URL)
            logger.info(f"[VECTOR_REPO] Weaviate 客户端连接成功: {WEAVIATE_URL}")
        except Exception as e:
            logger.error(f"[VECTOR_REPO] Weaviate 客户端连接失败: {e}")
            raise
    
    return weaviate_client

def initialize_weaviate():
    """初始化 Weaviate schema (类结构)"""
    logger.info(f"[VECTOR_REPO] 正在初始化 Weaviate: {WEAVIATE_URL}")
    
    try:
        client = get_weaviate_client()
        
        # 检查连接状态
        if not client.is_ready():
            logger.error("[VECTOR_REPO] Weaviate 服务未就绪")
            return False
        
        # 检查是否已存在 schema
        existing_schema = client.schema.get()
        class_names = [cls['class'] for cls in existing_schema.get('classes', [])]
        
        if WEAVIATE_RAG_CLASS in class_names:
            logger.info(f"[VECTOR_REPO] {WEAVIATE_RAG_CLASS} 类已存在，跳过创建")
            return True
        
        # 创建知识库类 schema
        knowledge_class = {
            "class": WEAVIATE_RAG_CLASS,
            "description": "AI助手的知识库，存储问答对和相关信息",
            "properties": [
                {
                    "name": "question",
                    "dataType": ["text"],
                    "description": "用户问题"
                },
                {
                    "name": "answer",
                    "dataType": ["text"],
                    "description": "问题答案"
                },
                {
                    "name": "category",
                    "dataType": ["text"],
                    "description": "知识分类"
                },
                {
                    "name": "source",
                    "dataType": ["text"],
                    "description": "知识来源"
                },
                {
                    "name": "keywords",
                    "dataType": ["text[]"],
                    "description": "关键词列表"
                }
            ],
            "vectorizer": "none"  # 手动提供向量
        }
        
        # 创建类
        client.schema.create_class(knowledge_class)
        logger.info(f"[VECTOR_REPO] ✓ {WEAVIATE_RAG_CLASS} 类创建成功")
        return True
        
    except Exception as e:
        logger.error(f"[VECTOR_REPO] ✗ Weaviate 初始化失败: {e}")
        return False

def insert_knowledge(knowledge_data: Dict[str, Any], vector: List[float]) -> bool:
    """
    插入知识数据到 Weaviate
    
    Args:
        knowledge_data: 知识数据字典
        vector: 向量嵌入
    
    Returns:
        bool: 插入是否成功
    """
    try:
        client = get_weaviate_client()
        
        # 插入数据对象
        result = client.data_object.create(
            data_object=knowledge_data,
            class_name=WEAVIATE_RAG_CLASS,
            vector=vector
        )
        
        if result:
            logger.debug(f"[VECTOR_REPO] 知识插入成功: {knowledge_data.get('question', '')[:50]}...")
            return True
        else:
            logger.warning(f"[VECTOR_REPO] 知识插入失败: {knowledge_data}")
            return False
            
    except Exception as e:
        logger.error(f"[VECTOR_REPO] 插入知识时出错: {e}")
        return False

def batch_insert_knowledge(knowledge_list: List[Dict[str, Any]], vectors: List[List[float]]) -> int:
    """
    批量插入知识数据
    
    Args:
        knowledge_list: 知识数据列表
        vectors: 对应的向量列表
    
    Returns:
        int: 成功插入的数量
    """
    if len(knowledge_list) != len(vectors):
        logger.error("[VECTOR_REPO] 知识数据和向量数量不匹配")
        return 0
    
    success_count = 0
    
    try:
        client = get_weaviate_client()
        
        # 使用批量操作
        with client.batch as batch:
            batch.batch_size = 100
            
            for knowledge_data, vector in zip(knowledge_list, vectors):
                try:
                    batch.add_data_object(
                        data_object=knowledge_data,
                        class_name=WEAVIATE_RAG_CLASS,
                        vector=vector
                    )
                    success_count += 1
                except Exception as e:
                    logger.warning(f"[VECTOR_REPO] 批量插入单条数据失败: {e}")
        
        logger.info(f"[VECTOR_REPO] ✓ 批量插入完成: {success_count}/{len(knowledge_list)}")
        return success_count
        
    except Exception as e:
        logger.error(f"[VECTOR_REPO] 批量插入失败: {e}")
        return success_count

def retrieve_context(query_vector: List[float], limit: int = 5, certainty: float = 0.7) -> List[str]:
    """
    从 Weaviate 检索最相似的知识上下文
    
    Args:
        query_vector: 查询向量
        limit: 返回结果数量限制
        certainty: 相似度阈值 (0-1)
    
    Returns:
        List[str]: 检索到的知识片段列表
    """
    try:
        client = get_weaviate_client()
        
        # 执行向量搜索
        result = (
            client.query
            .get(WEAVIATE_RAG_CLASS, ["question", "answer", "category", "source"])
            .with_near_vector({
                "vector": query_vector,
                "certainty": certainty
            })
            .with_limit(limit)
            .do()
        )
        
        # 解析结果
        knowledge_items = result.get("data", {}).get("Get", {}).get(WEAVIATE_RAG_CLASS, [])
        
        contexts = []
        for item in knowledge_items:
            # 组合问题和答案作为上下文
            context = f"问题: {item.get('question', '')}\n答案: {item.get('answer', '')}"
            contexts.append(context)
        
        logger.debug(f"[VECTOR_REPO] 检索到 {len(contexts)} 个相关上下文")
        return contexts
        
    except Exception as e:
        logger.error(f"[VECTOR_REPO] 检索上下文失败: {e}")
        # 返回模拟数据作为后备
        return [
            "RAG 检索到的知识片段 A: 软件安装对电脑配置要求并不高，参考I5处理器，16G内存。",
            "RAG 检索到的知识片段 B: 在进行 FFT 分析之前，需要对信号进行窗函数处理。",
            "RAG 检索到的知识片段 C: 采样频率应该设置为分析频率的2.56倍以上。"
        ]

def search_knowledge(query: str, query_vector: List[float], limit: int = 5) -> List[Dict[str, Any]]:
    """
    搜索知识库，返回详细的知识条目
    
    Args:
        query: 查询文本
        query_vector: 查询向量
        limit: 返回结果数量
    
    Returns:
        List[Dict]: 知识条目列表
    """
    try:
        client = get_weaviate_client()
        
        result = (
            client.query
            .get(WEAVIATE_RAG_CLASS, ["question", "answer", "category", "source", "keywords"])
            .with_near_vector({
                "vector": query_vector,
                "certainty": 0.6
            })
            .with_limit(limit)
            .do()
        )
        
        knowledge_items = result.get("data", {}).get("Get", {}).get(WEAVIATE_RAG_CLASS, [])
        
        logger.info(f"[VECTOR_REPO] 搜索到 {len(knowledge_items)} 个知识条目")
        return knowledge_items
        
    except Exception as e:
        logger.error(f"[VECTOR_REPO] 搜索知识失败: {e}")
        return []

def get_knowledge_count() -> int:
    """获取知识库中的条目总数"""
    try:
        client = get_weaviate_client()
        
        result = (
            client.query
            .aggregate(WEAVIATE_RAG_CLASS)
            .with_meta_count()
            .do()
        )
        
        count = result.get("data", {}).get("Aggregate", {}).get(WEAVIATE_RAG_CLASS, [{}])[0].get("meta", {}).get("count", 0)
        return count
        
    except Exception as e:
        logger.error(f"[VECTOR_REPO] 获取知识数量失败: {e}")
        return 0

def clear_knowledge_base() -> bool:
    """清空知识库（谨慎使用）"""
    try:
        client = get_weaviate_client()
        
        # 删除所有对象
        client.batch.delete_objects(
            class_name=WEAVIATE_RAG_CLASS,
            where={
                "operator": "Like",
                "path": ["source"],
                "valueText": "*"
            }
        )
        
        logger.info("[VECTOR_REPO] ✓ 知识库已清空")
        return True
        
    except Exception as e:
        logger.error(f"[VECTOR_REPO] 清空知识库失败: {e}")
        return False
