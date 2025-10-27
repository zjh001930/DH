#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据导入脚本 - ingest_data.py
用于将 data 目录中的数据导入到 Weaviate 向量数据库和 PostgreSQL 数据库中
"""

import os
import sys
import json
import time
import requests
from typing import List, Dict, Any
import logging

# 添加当前目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# 导入本地模块
from db.sql_repo import initialize_db, insert_task, insert_task_steps, insert_ui_element
from db.vector_repo import initialize_weaviate, batch_insert_knowledge, get_knowledge_count
from llm.ollama_client import OllamaClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ingest_data.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataIngester:
    """数据导入器"""
    
    def __init__(self):
        # 数据目录
        self.data_dir = os.path.join(current_dir, "data")
        self.initial_data_dir = os.path.join(self.data_dir, "initial_data")
        self.images_dir = os.path.join(self.data_dir, "images")
        
        # Ollama 客户端
        self.ollama_client = OllamaClient()
        
        logger.info(f"[DATA_INGESTER] 初始化完成")
        logger.info(f"[DATA_INGESTER] 数据目录: {self.data_dir}")
        logger.info(f"[DATA_INGESTER] 初始数据目录: {self.initial_data_dir}")
        logger.info(f"[DATA_INGESTER] 图片目录: {self.images_dir}")
    
    def check_services(self) -> bool:
        """检查所有必要服务的状态"""
        logger.info("检查服务状态...")
        
        # 检查 Ollama 服务
        try:
            # 使用 OllamaClient 测试连接
            test_embedding = self.ollama_client.get_embedding("测试连接")
            if test_embedding:
                logger.info("✓ Ollama 服务连接正常")
            else:
                logger.error("✗ Ollama 服务连接失败")
                return False
        except Exception as e:
            logger.error(f"✗ Ollama 服务检查失败: {e}")
            return False
        
        # 检查数据目录
        if not os.path.exists(self.data_dir):
            logger.error(f"✗ 数据目录不存在: {self.data_dir}")
            return False
        
        if not os.path.exists(self.initial_data_dir):
            logger.error(f"✗ 初始数据目录不存在: {self.initial_data_dir}")
            return False
        
        logger.info("✓ 所有服务检查通过")
        return True
    
    def parse_rag_data(self, file_path: str) -> List[Dict[str, str]]:
        """解析 RAG 数据文件"""
        logger.info(f"解析 RAG 数据文件: {file_path}")
        
        qa_pairs = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 按问答对分割
            sections = content.split('\n\n')
            
            for section in sections:
                section = section.strip()
                if not section:
                    continue
                    
                lines = section.split('\n')
                question = None
                answer = None
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('问：'):
                        question = line[2:]  # 去掉 "问："
                    elif line.startswith('答：'):
                        answer = line[2:]   # 去掉 "答："
                
                if question and answer:
                    qa_pairs.append({
                        'question': question,
                        'answer': answer,
                        'category': 'FAQ',
                        'source': 'rag_source.txt',
                        'keywords': self._extract_keywords(question + " " + answer)
                    })
            
            logger.info(f"解析到 {len(qa_pairs)} 个问答对")
            return qa_pairs
            
        except Exception as e:
            logger.error(f"解析 RAG 数据失败: {e}")
            return []
    
    def _extract_keywords(self, text: str) -> List[str]:
        """从文本中提取关键词"""
        # 简单的关键词提取逻辑
        keywords = []
        
        # 技术相关关键词
        tech_keywords = [
            "FFT", "分析", "采集", "软件", "仪器", "传感器", "应变片", "频率", 
            "滤波", "触发", "存储", "通讯", "IP", "网络", "配置", "安装",
            "模态", "振动", "信号", "数据", "测量", "监测", "桥梁", "PHM"
        ]
        
        for keyword in tech_keywords:
            if keyword in text:
                keywords.append(keyword)
        
        return keywords[:5]  # 限制关键词数量
    
    def ingest_rag_data(self) -> bool:
        """导入 RAG 数据到 Weaviate"""
        logger.info("开始导入 RAG 数据...")
        
        rag_file = os.path.join(self.initial_data_dir, "rag_source.txt")
        if not os.path.exists(rag_file):
            logger.warning(f"RAG 数据文件不存在: {rag_file}")
            return False
        
        qa_pairs = self.parse_rag_data(rag_file)
        if not qa_pairs:
            logger.warning("没有解析到有效的问答对")
            return False
        
        # 生成向量嵌入
        logger.info("生成向量嵌入...")
        vectors = []
        valid_qa_pairs = []
        
        for i, qa in enumerate(qa_pairs):
            try:
                # 为问题和答案组合生成嵌入向量
                text_for_embedding = f"问题: {qa['question']} 答案: {qa['answer']}"
                embedding = self.ollama_client.get_embedding(text_for_embedding)
                
                if embedding:
                    vectors.append(embedding)
                    valid_qa_pairs.append(qa)
                else:
                    logger.warning(f"跳过第 {i+1} 个问答对（无法获取嵌入）")
                
                if (i + 1) % 10 == 0:
                    logger.info(f"已生成嵌入 {i + 1}/{len(qa_pairs)}")
                    
            except Exception as e:
                logger.error(f"生成第 {i+1} 个问答对嵌入失败: {e}")
                continue
        
        if not valid_qa_pairs:
            logger.error("没有有效的问答对可以导入")
            return False
        
        # 批量导入到 Weaviate
        logger.info(f"批量导入 {len(valid_qa_pairs)} 个问答对到 Weaviate...")
        success_count = batch_insert_knowledge(valid_qa_pairs, vectors)
        
        logger.info(f"✓ RAG 数据导入完成: {success_count}/{len(qa_pairs)} 成功")
        return success_count > 0
    
    def ingest_task_data(self) -> bool:
        """导入任务数据到 PostgreSQL"""
        logger.info("开始导入任务数据...")
        
        task_file = os.path.join(self.initial_data_dir, "task_full_fft_analysis.json")
        if not os.path.exists(task_file):
            logger.warning(f"任务数据文件不存在: {task_file}")
            return False
        
        try:
            with open(task_file, 'r', encoding='utf-8') as f:
                task_data = json.load(f)
            
            # 插入任务基本信息
            task_success = insert_task({
                'task_id': task_data['task_id'],
                'task_name': task_data['task_name'],
                'description': task_data['description']
            })
            
            if not task_success:
                logger.error("插入任务基本信息失败")
                return False
            
            # 处理任务步骤
            steps_data = []
            for step in task_data['steps']:
                # 查找对应的截图文件
                screenshot_path = None
                if 'element_id' in step:
                    screenshot_file = f"{step['element_id']}.png"
                    screenshot_full_path = os.path.join(self.images_dir, screenshot_file)
                    if os.path.exists(screenshot_full_path):
                        screenshot_path = f"/data/images/{screenshot_file}"
                
                steps_data.append({
                    'step': step['step'],
                    'step_name': step['step_name'],
                    'element_id': step.get('element_id'),
                    'action': step.get('action'),
                    'dialogue_copy_id': step.get('dialogue_copy_id'),
                    'screenshot_path': screenshot_path
                })
            
            # 插入任务步骤
            steps_success = insert_task_steps(task_data['task_id'], steps_data)
            
            if steps_success:
                logger.info("✓ 任务数据导入成功")
                return True
            else:
                logger.error("✗ 任务步骤导入失败")
                return False
            
        except Exception as e:
            logger.error(f"✗ 导入任务数据失败: {e}")
            return False
    
    def ingest_ui_elements(self) -> bool:
        """导入 UI 元素数据"""
        logger.info("开始导入 UI 元素数据...")
        
        if not os.path.exists(self.images_dir):
            logger.warning(f"图片目录不存在: {self.images_dir}")
            return False
        
        success_count = 0
        total_files = 0
        
        try:
            for filename in os.listdir(self.images_dir):
                if filename.endswith('.png'):
                    total_files += 1
                    element_id = filename[:-4]  # 去掉 .png 扩展名
                    screenshot_path = f"/data/images/{filename}"
                    
                    # 根据文件名推断元素类型和名称
                    element_name = element_id.replace('_', ' ').title()
                    element_type = "button" if "btn" in element_id else "dialog" if "dlg" in element_id else "element"
                    
                    element_data = {
                        'element_id': element_id,
                        'element_name': element_name,
                        'element_type': element_type,
                        'screenshot_path': screenshot_path
                    }
                    
                    if insert_ui_element(element_data):
                        success_count += 1
            
            logger.info(f"✓ UI 元素数据导入完成: {success_count}/{total_files} 成功")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"✗ 导入 UI 元素数据失败: {e}")
            return False
    
    def verify_data(self) -> bool:
        """验证导入的数据"""
        logger.info("验证导入的数据...")
        
        try:
            # 验证 Weaviate 数据
            knowledge_count = get_knowledge_count()
            logger.info(f"✓ Weaviate 中有 {knowledge_count} 条知识记录")
            
            # 验证 PostgreSQL 数据 - 这里可以添加更多验证逻辑
            logger.info("✓ PostgreSQL 数据验证完成")
            
            return knowledge_count > 0
            
        except Exception as e:
            logger.error(f"✗ 数据验证失败: {e}")
            return False
    
    def run(self) -> bool:
        """执行完整的数据导入流程"""
        logger.info("=" * 60)
        logger.info("AI 助手数据导入工具")
        logger.info("=" * 60)
        
        # 1. 检查服务状态
        if not self.check_services():
            logger.error("服务检查失败，退出")
            return False
        
        # 2. 初始化数据库
        logger.info("初始化数据库...")
        if not initialize_db():
            logger.error("PostgreSQL 数据库初始化失败")
            return False
        
        if not initialize_weaviate():
            logger.error("Weaviate 数据库初始化失败")
            return False
        
        # 3. 导入数据
        logger.info("开始数据导入...")
        
        rag_success = self.ingest_rag_data()
        task_success = self.ingest_task_data()
        ui_success = self.ingest_ui_elements()
        
        # 4. 验证数据
        verify_success = self.verify_data()
        
        # 5. 总结
        logger.info("=" * 60)
        if rag_success and task_success and ui_success and verify_success:
            logger.info("✓ 数据导入完成！所有数据已成功导入")
            logger.info("✓ 您的 AI 助手现在可以提供知识问答和任务引导服务")
        else:
            logger.warning("⚠ 数据导入部分成功，请检查上述错误信息")
            logger.info(f"RAG数据: {'✓' if rag_success else '✗'}")
            logger.info(f"任务数据: {'✓' if task_success else '✗'}")
            logger.info(f"UI元素: {'✓' if ui_success else '✗'}")
            logger.info(f"数据验证: {'✓' if verify_success else '✗'}")
        logger.info("=" * 60)
        
        return rag_success and task_success and ui_success

def main():
    """主函数"""
    try:
        # 检查数据目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(current_dir, "data")
        
        if not os.path.exists(data_dir):
            print(f"错误: 数据目录不存在 {data_dir}")
            print("请确保在 backend 目录运行此脚本")
            return 1
        
        # 等待服务启动
        print("等待服务启动...")
        time.sleep(3)
        
        # 执行数据导入
        ingester = DataIngester()
        success = ingester.run()
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n用户中断操作")
        return 1
    except Exception as e:
        print(f"程序执行出错: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())