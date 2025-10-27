from llm.ollama_client import OllamaClient  # 从 llm 目录导入 Ollama 客户端
from config.settings import INTENT_CONFIDENCE_THRESHOLD  # 从 config 目录导入配置
from db.sql_repo import get_all_tasks  # 从数据库获取任务数据
import logging
import re

logger = logging.getLogger(__name__)


class IntentRecognizer:
    def __init__(self):
        # 实例化 Ollama 客户端，用于获取 Embedding 向量 (使用 bge-3)
        self.ollama_client = OllamaClient()
        
        # 从数据库加载任务数据
        self.task_data = {}
        self.task_keywords = {}
        self._load_tasks_from_database()
        
        logger.info(f"[INTENT] Intent Recognizer initialized with {len(self.task_data)} tasks")

    def _load_tasks_from_database(self):
        """从数据库加载任务数据"""
        try:
            tasks = get_all_tasks()
            for task in tasks:
                task_id = task['task_id']
                task_name = task['task_name']
                description = task['description'] or ""
                
                # 存储任务信息
                self.task_data[task_id] = {
                    'name': task_name,
                    'description': description,
                    'full_text': f"{task_name} {description}"
                }
                
                # 提取关键词用于简单匹配
                self.task_keywords[task_id] = self._extract_keywords(task_name, description)
                
            logger.info(f"[INTENT] Loaded {len(self.task_data)} tasks from database")
            
        except Exception as e:
            logger.error(f"[INTENT] Failed to load tasks from database: {e}")
            # 使用备用的硬编码任务数据
            self.task_data = {
                "task_full_fft_analysis": {
                    'name': "FFT分析任务",
                    'description': "描述了从数据采集到FFT分析的完整操作流程",
                    'full_text': "FFT分析任务 描述了从数据采集到FFT分析的完整操作流程"
                }
            }
            self.task_keywords = {
                "task_full_fft_analysis": ["FFT", "分析", "数据采集", "频谱"]
            }

    def _extract_keywords(self, task_name: str, description: str) -> list:
        """从任务名称和描述中提取关键词"""
        text = f"{task_name} {description}".lower()
        # 简单的关键词提取（可以后续改进为更复杂的NLP处理）
        keywords = []
        
        # 提取中文词汇
        chinese_words = re.findall(r'[\u4e00-\u9fff]+', text)
        keywords.extend([word for word in chinese_words if len(word) >= 2])
        
        # 提取英文词汇
        english_words = re.findall(r'[a-zA-Z]+', text)
        keywords.extend([word.lower() for word in english_words if len(word) >= 3])
        
        return list(set(keywords))

    def recognize(self, user_input: str) -> dict:
        """根据用户输入判断意图"""
        logger.info(f"[INTENT] Recognizing input: {user_input}")

        # 简单的关键词匹配逻辑
        best_match = None
        best_score = 0.0
        
        user_input_lower = user_input.lower()
        
        for task_id, keywords in self.task_keywords.items():
            score = 0.0
            matched_keywords = 0
            
            for keyword in keywords:
                if keyword.lower() in user_input_lower:
                    matched_keywords += 1
                    # 根据关键词长度给予不同权重
                    score += len(keyword) * 0.1
            
            # 计算匹配度
            if len(keywords) > 0:
                keyword_coverage = matched_keywords / len(keywords)
                score = score * keyword_coverage
            
            if score > best_score:
                best_score = score
                best_match = task_id
        
        # 根据匹配分数确定置信度
        if best_match and best_score > 0.3:  # 调整阈值
            confidence = min(0.95, 0.5 + best_score)  # 置信度在0.5-0.95之间
            logger.info(f"[INTENT] Matched task {best_match} with confidence {confidence:.2f}")
            return {
                "recognized_task_id": best_match,
                "confidence": confidence
            }
        
        # 低置信度匹配 (触发 RAG 问答)
        logger.info(f"[INTENT] No high-confidence match found, routing to RAG")
        return {
            "recognized_task_id": "generic_qa",
            "confidence": 0.20
        }
