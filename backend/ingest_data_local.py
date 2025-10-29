#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据导入脚本 - 本地版本
用于在本地环境运行，使用 localhost 地址连接服务
"""

import os
import sys
import json
import time
import requests
from typing import List, Dict, Any
import logging
from dotenv import load_dotenv

# 加载本地环境配置
env_local_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.local')
if os.path.exists(env_local_path):
    load_dotenv(env_local_path)
    print(f"✅ 已加载本地环境配置: {env_local_path}")
else:
    print(f"❌ 本地环境配置文件不存在: {env_local_path}")
    print("将使用默认配置")

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
        logging.FileHandler('ingest_data_local.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LocalDataIngester:
    """本地数据导入器"""
    
    def __init__(self):
        # 数据目录
        self.data_dir = os.path.join(current_dir, "data")
        self.initial_data_dir = os.path.join(self.data_dir, "initial_data")
        self.images_dir = os.path.join(self.data_dir, "images")
        
        # Ollama 客户端
        self.ollama_client = OllamaClient()
        
        logger.info(f"[LOCAL_DATA_INGESTER] 初始化完成")
        logger.info(f"[LOCAL_DATA_INGESTER] 数据目录: {self.data_dir}")
        logger.info(f"[LOCAL_DATA_INGESTER] 初始数据目录: {self.initial_data_dir}")
        logger.info(f"[LOCAL_DATA_INGESTER] 图片目录: {self.images_dir}")
    
    def check_services(self) -> bool:
        """检查服务状态"""
        logger.info("检查本地服务状态...")
        
        # 检查 PostgreSQL
        try:
            import psycopg2
            database_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/ai_assistant")
            conn = psycopg2.connect(database_url)
            conn.close()
            logger.info("✓ PostgreSQL 连接成功")
        except Exception as e:
            logger.error(f"✗ PostgreSQL 连接失败: {e}")
            return False
        
        # 检查 Weaviate
        try:
            weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
            response = requests.get(f"{weaviate_url}/v1/.well-known/ready", timeout=5)
            if response.status_code == 200:
                logger.info("✓ Weaviate 连接成功")
            else:
                logger.error(f"✗ Weaviate 连接失败: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"✗ Weaviate 连接失败: {e}")
            return False
        
        # 检查 Ollama (可选，因为数据导入可能不需要)
        try:
            ollama_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
            response = requests.get(f"{ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info("✓ Ollama 连接成功")
            else:
                logger.warning(f"⚠ Ollama 连接失败: {response.status_code} (可能不影响数据导入)")
        except Exception as e:
            logger.warning(f"⚠ Ollama 连接失败: {e} (可能不影响数据导入)")
        
        return True
    
    def ingest_task_data(self) -> bool:
        """导入任务数据到 PostgreSQL"""
        logger.info("开始导入任务数据...")
        
        # 查找所有以task_开头的JSON文件
        task_files = []
        if os.path.exists(self.initial_data_dir):
            for filename in os.listdir(self.initial_data_dir):
                if filename.startswith('task_') and filename.endswith('.json'):
                    task_files.append(os.path.join(self.initial_data_dir, filename))
        
        if not task_files:
            logger.warning(f"在 {self.initial_data_dir} 中未找到任务数据文件")
            return False
        
        logger.info(f"找到 {len(task_files)} 个任务文件")
        
        success_count = 0
        total_count = len(task_files)
        
        for task_file in task_files:
            try:
                logger.info(f"正在导入: {os.path.basename(task_file)}")
                
                with open(task_file, 'r', encoding='utf-8') as f:
                    task_data = json.load(f)
                
                # 插入任务基本信息
                task_success = insert_task({
                    'task_id': task_data['task_id'],
                    'task_name': task_data['task_name'],
                    'description': task_data.get('description', '')
                })
                
                if not task_success:
                    logger.error(f"插入任务基本信息失败: {task_data['task_id']}")
                    continue
                
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
                    logger.info(f"✓ 任务 {task_data['task_id']} 导入成功")
                    success_count += 1
                else:
                    logger.error(f"✗ 任务 {task_data['task_id']} 步骤导入失败")
                
            except Exception as e:
                logger.error(f"✗ 导入任务文件 {os.path.basename(task_file)} 失败: {e}")
                continue
        
        logger.info(f"任务数据导入完成: {success_count}/{total_count} 成功")
        return success_count > 0
    
    def run(self) -> bool:
        """执行完整的数据导入流程"""
        logger.info("=" * 60)
        logger.info("AI 助手数据导入工具 - 本地版本")
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
        
        # 3. 导入任务数据
        logger.info("开始任务数据导入...")
        task_success = self.ingest_task_data()
        
        # 4. 总结
        logger.info("=" * 60)
        if task_success:
            logger.info("✓ 任务数据导入完成！")
            logger.info("✓ 您的 AI 助手现在可以提供任务引导服务")
        else:
            logger.warning("⚠ 任务数据导入失败，请检查上述错误信息")
        
        logger.info("=" * 60)
        return task_success

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
        
        # 执行数据导入
        ingester = LocalDataIngester()
        success = ingester.run()
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n用户中断操作")
        return 1
    except Exception as e:
        print(f"程序执行出错: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())