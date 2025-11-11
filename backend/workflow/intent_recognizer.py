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
        """从数据库或JSON文件加载任务数据"""
        try:
            # 首先尝试从数据库加载
            tasks = get_all_tasks()
            print(f"[DEBUG] 从数据库获取到 {len(tasks)} 个任务")
            
            if not tasks:
                print(f"[DEBUG] 数据库中没有任务，尝试从JSON文件加载...")
                self._load_tasks_from_json_files()
                return
                
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
            print(f"[DEBUG] 数据库加载失败，尝试从JSON文件加载任务...")
            # 从JSON文件加载任务数据
            self._load_tasks_from_json_files()

    def _load_tasks_from_json_files(self):
        """从JSON文件加载任务数据"""
        import json
        import os
        
        try:
            # JSON文件目录
            json_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'initial_data')
            
            if not os.path.exists(json_dir):
                logger.error(f"[INTENT] JSON directory not found: {json_dir}")
                return
            
            # 遍历所有JSON文件
            for filename in os.listdir(json_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(json_dir, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            task_data = json.load(f)
                        
                        task_id = task_data.get('task_id')
                        task_name = task_data.get('task_name', '')
                        description = task_data.get('description', '')
                        steps = task_data.get('steps', [])
                        
                        if task_id and task_name:
                            # 提取步骤文本
                            step_texts = []
                            for step in steps:
                                if isinstance(step, dict):
                                    step_name = step.get('step_name', '')
                                    if step_name:
                                        step_texts.append(step_name)
                                elif isinstance(step, str):
                                    step_texts.append(step)
                            
                            # 构建完整的搜索文本，包含任务名称、描述和步骤
                            full_text_parts = [task_name]
                            if description:
                                full_text_parts.append(description)
                            if step_texts:
                                full_text_parts.extend(step_texts)
                            full_text = " ".join(full_text_parts)
                            
                            # 存储任务信息
                            self.task_data[task_id] = {
                                'name': task_name,
                                'description': description,
                                'full_text': full_text,
                                'steps': step_texts
                            }
                            
                            # 提取关键词（包含步骤信息）
                            self.task_keywords[task_id] = self._extract_keywords(task_name, description, step_texts)
                            
                    except Exception as file_error:
                        logger.warning(f"[INTENT] Failed to load {filename}: {file_error}")
                        continue
            
            logger.info(f"[INTENT] Loaded {len(self.task_data)} tasks from JSON files")
            print(f"[DEBUG] JSON加载完成，共加载 {len(self.task_data)} 个任务")
            
        except Exception as e:
            logger.error(f"[INTENT] Failed to load tasks from JSON files: {e}")
            # 最后的备用数据
            self.task_data = {
                "task_signal_add_spectrum_analysis": {
                    'name': "添加分析方法进行信号处理",
                    'description': "为信号处理系统添加新的分析方法和算法",
                    'full_text': "添加分析方法进行信号处理 为信号处理系统添加新的分析方法和算法",
                    'steps': ["分析当前信号处理需求", "选择合适的分析算法", "实现分析方法代码"]
                }
            }
            self.task_keywords = {
                "task_signal_add_spectrum_analysis": ["添加", "分析", "方法", "信号", "处理", "算法", "频谱"]
            }

    def _extract_keywords(self, task_name: str, description: str, steps: list = None) -> list:
        """从任务名称、描述和步骤中提取关键词"""
        # 合并文本
        text_parts = [task_name, description or ""]
        if steps:
            text_parts.extend(steps)
        
        text = " ".join(text_parts).lower()
        
        # 简单的关键词提取（可以后续改进为更复杂的NLP处理）
        keywords = []
        
        # 提取中文词汇
        chinese_words = re.findall(r'[\u4e00-\u9fff]+', text)
        keywords.extend([word for word in chinese_words if len(word) >= 2])
        
        # 提取英文词汇
        english_words = re.findall(r'[a-zA-Z]+', text)
        keywords.extend([word.lower() for word in english_words if len(word) >= 3])
        
        # 添加一些特殊的关键词组合
        special_keywords = []
        if "新建" in text and "工程" in text:
            special_keywords.extend(["新建工程", "创建工程", "新项目", "创建项目"])
        if "删除" in text and ("工程" in text or "项目" in text):
            special_keywords.extend(["删除工程", "删除项目"])
        if "fft" in text.lower() or "频谱" in text:
            special_keywords.extend(["fft", "频谱分析", "频域分析"])
        if "模态" in text:
            special_keywords.extend(["模态分析", "振型分析"])
        if "分析" in text:
            special_keywords.append("分析")
        if "设置" in text or "配置" in text:
            special_keywords.extend(["设置", "配置"])
            
        keywords.extend(special_keywords)
        
        return list(set(keywords))

    def recognize(self, user_input: str) -> dict:
        """根据用户输入判断意图"""
        logger.info(f"[INTENT] Recognizing input: {user_input}")

        ui_lower = (user_input or "").lower().strip()
        if any(g in ui_lower for g in ["你好", "您好", "hi", "hello", "hey", "嗨", "在吗"]):
            return {"recognized_task_id": "greeting", "confidence": 1.0}
        
        best_match = None
        best_score = 0.0
        
        user_input_lower = user_input.lower()
        user_input_clean = user_input.replace(" ", "").replace("，", "").replace("。", "")
        
        # 1. 首先尝试任务名称的精确匹配
        for task_id, task_info in self.task_data.items():
            task_name = task_info['name']
            task_description = task_info['description']
            
            # 清理文本用于匹配
            task_name_clean = task_name.replace(" ", "").replace("，", "").replace("。", "")
            user_clean = user_input_clean.replace(" ", "").replace("，", "").replace("。", "")
            
            # 1.1 完全匹配或高度相似匹配
            if task_name_clean == user_clean:
                confidence = 0.95
                logger.info(f"[INTENT] Exact name match: {task_id} with confidence {confidence:.2f}")
                return {
                    "recognized_task_id": task_id,
                    "confidence": confidence
                }
            
            # 1.2 任务名称包含用户输入或用户输入包含任务名称
            if task_name_clean in user_clean or user_clean in task_name_clean:
                confidence = 0.90
                logger.info(f"[INTENT] Direct name match: {task_id} with confidence {confidence:.2f}")
                return {
                    "recognized_task_id": task_id,
                    "confidence": confidence
                }
            
            # 1.3 检查描述中的匹配
            if task_description:
                desc_clean = task_description.replace(" ", "").replace("，", "").replace("。", "")
                if user_clean in desc_clean or desc_clean in user_clean:
                    confidence = 0.85
                    logger.info(f"[INTENT] Description match: {task_id} with confidence {confidence:.2f}")
                    return {
                        "recognized_task_id": task_id,
                        "confidence": confidence
                    }
            
            # 1.4 计算任务名称中关键词的匹配度
            task_words = re.findall(r'[\u4e00-\u9fff]+', task_name)
            matched_words = 0
            total_word_score = 0
            
            for word in task_words:
                if len(word) >= 2 and word in user_input:
                    matched_words += 1
                    # 根据词语重要性给予不同权重
                    if word in ['添加', '分析', '信号', '处理', '频谱', 'FFT']:
                        total_word_score += 0.4  # 重要词汇高权重
                    else:
                        total_word_score += 0.2  # 普通词汇低权重
            
            if len(task_words) > 0:
                # 综合考虑匹配词数和词汇重要性
                coverage_score = matched_words / len(task_words)
                name_match_score = (coverage_score * 0.6 + total_word_score * 0.4) * 2.0
                
                if name_match_score > best_score:
                    best_score = name_match_score
                    best_match = task_id
        
        # 2. 如果没有直接匹配，使用关键词匹配
        if best_score < 1.0:  # 如果任务名称匹配度不高，尝试关键词匹配
            for task_id, keywords in self.task_keywords.items():
                score = 0.0
                matched_keywords = 0
                
                for keyword in keywords:
                    if len(keyword) >= 2 and keyword.lower() in user_input_lower:
                        matched_keywords += 1
                        # 根据关键词长度和重要性给予不同权重
                        if len(keyword) >= 4:
                            score += 0.3  # 长关键词权重高
                        else:
                            score += 0.1  # 短关键词权重低
                
                # 计算匹配度
                if len(keywords) > 0:
                    keyword_coverage = matched_keywords / len(keywords)
                    final_score = score * keyword_coverage
                    
                    if final_score > best_score:
                        best_score = final_score
                        best_match = task_id
        
        # 3. 根据匹配分数确定置信度
        if best_match and best_score > 0.1:  # 进一步降低阈值以提高识别率
            # 动态计算置信度
            if best_score >= 1.5:
                confidence = 0.90
            elif best_score >= 1.0:
                confidence = 0.85
            elif best_score >= 0.6:
                confidence = 0.80
            elif best_score >= 0.4:
                confidence = 0.75
            else:
                confidence = 0.70
                
            logger.info(f"[INTENT] Matched task {best_match} with score {best_score:.2f} and confidence {confidence:.2f}")
            return {
                "recognized_task_id": best_match,
                "confidence": confidence
            }
        
        # 低置信度匹配 (触发 RAG 问答)
        logger.info(f"[INTENT] No high-confidence match found (best score: {best_score:.2f}), routing to RAG")
        return {
            "recognized_task_id": "generic_qa",
            "confidence": 0.20
        }

    def recognize_intent(self, user_input: str) -> dict:
        """意图识别方法 - 为了兼容app.py中的调用"""
        result = self.recognize(user_input)
        return {
            "task_id": result.get("recognized_task_id"),
            "confidence": result.get("confidence", 0.0)
        }
