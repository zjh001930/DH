#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化数据导入脚本 - ingest_data_simple.py
暂时跳过 Weaviate 部分，只导入 PostgreSQL 数据
"""

import os
import sys
import json
import time
import logging

# 添加当前目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# 导入本地模块
from db.sql_repo import initialize_db, insert_task, insert_task_steps, insert_ui_element

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ingest_data_simple.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SimpleDataIngester:
    """简化数据导入器（仅 PostgreSQL）"""
    
    def __init__(self):
        # 数据目录
        self.data_dir = os.path.join(current_dir, "data")
        self.initial_data_dir = os.path.join(self.data_dir, "initial_data")
        self.images_dir = os.path.join(self.data_dir, "images")
        
        logger.info(f"[SIMPLE_INGESTER] 初始化完成")
        logger.info(f"[SIMPLE_INGESTER] 数据目录: {self.data_dir}")
    
    def check_services(self) -> bool:
        """检查必要服务的状态"""
        logger.info("检查服务状态...")
        
        # 检查数据目录
        if not os.path.exists(self.data_dir):
            logger.error(f"✗ 数据目录不存在: {self.data_dir}")
            return False
        
        if not os.path.exists(self.initial_data_dir):
            logger.error(f"✗ 初始数据目录不存在: {self.initial_data_dir}")
            return False
        
        logger.info("✓ 数据目录检查通过")
        return True
    
    def ingest_task_data(self) -> bool:
        """导入任务数据到 PostgreSQL"""
        logger.info("开始导入任务数据...")
        
        # 扫描所有任务文件
        task_files = []
        try:
            for filename in os.listdir(self.initial_data_dir):
                if filename.startswith('task_') and filename.endswith('.json'):
                    task_files.append(filename)
        except Exception as e:
            logger.error(f"扫描任务文件失败: {e}")
            return False
        
        if not task_files:
            logger.warning(f"在 {self.initial_data_dir} 中未找到任务文件")
            return False
        
        logger.info(f"找到 {len(task_files)} 个任务文件")
        
        success_count = 0
        total_count = len(task_files)
        
        for task_filename in task_files:
            task_file = os.path.join(self.initial_data_dir, task_filename)
            logger.info(f"处理任务文件: {task_filename}")
            
            try:
                with open(task_file, 'r', encoding='utf-8') as f:
                    task_data = json.load(f)
                
                # 检查必要字段
                if 'task_id' not in task_data:
                    logger.warning(f"跳过文件 {task_filename}: 缺少 task_id")
                    continue
                
                # 插入任务基本信息
                task_info = {
                    'task_id': task_data['task_id'],
                    'task_name': task_data.get('task_name', task_data['task_id']),
                    'description': task_data.get('description', '')
                }
                
                task_success = insert_task(task_info)
                
                if not task_success:
                    logger.error(f"插入任务基本信息失败: {task_filename}")
                    continue
                
                # 处理任务步骤（如果存在）
                if 'steps' in task_data and task_data['steps']:
                    steps_data = []
                    for step in task_data['steps']:
                        # 查找对应的截图文件
                        screenshot_path = None
                        if 'element_id' in step:
                            screenshot_file = f"{step['element_id']}.png"
                            screenshot_full_path = os.path.join(self.images_dir, screenshot_file)
                            if os.path.exists(screenshot_full_path):
                                screenshot_path = f"/tasks/screenshots/{screenshot_file}"
                        
                        steps_data.append({
                            'step': step.get('step', 0),
                            'step_name': step.get('step_name', ''),
                            'element_id': step.get('element_id'),
                            'action': step.get('action'),
                            'dialogue_copy_id': step.get('dialogue_copy_id'),
                            'screenshot_path': screenshot_path
                        })
                    
                    # 插入任务步骤
                    steps_success = insert_task_steps(task_data['task_id'], steps_data)
                    
                    if steps_success:
                        logger.info(f"✓ 任务数据导入成功: {task_filename}")
                        success_count += 1
                    else:
                        logger.error(f"✗ 任务步骤导入失败: {task_filename}")
                else:
                    # 没有步骤数据，但任务基本信息已导入
                    logger.info(f"✓ 任务基本信息导入成功: {task_filename} (无步骤数据)")
                    success_count += 1
                
            except Exception as e:
                logger.error(f"✗ 处理任务文件失败 {task_filename}: {e}")
                continue
        
        logger.info(f"任务数据导入完成: {success_count}/{total_count} 成功")
        return success_count > 0
    
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
    
    def run(self) -> bool:
        """执行简化的数据导入流程"""
        logger.info("=" * 60)
        logger.info("AI 助手简化数据导入工具")
        logger.info("注意: 此版本跳过 Weaviate 向量数据库导入")
        logger.info("=" * 60)
        
        # 1. 检查服务状态
        if not self.check_services():
            logger.error("服务检查失败，退出")
            return False
        
        # 2. 初始化 PostgreSQL 数据库
        logger.info("初始化 PostgreSQL 数据库...")
        if not initialize_db():
            logger.error("PostgreSQL 数据库初始化失败")
            return False
        
        # 3. 导入数据（跳过 RAG 数据）
        logger.info("开始数据导入...")
        
        task_success = self.ingest_task_data()
        ui_success = self.ingest_ui_elements()
        
        # 4. 总结
        logger.info("=" * 60)
        if task_success and ui_success:
            logger.info("✓ 简化数据导入完成！任务和UI数据已成功导入")
            logger.info("✓ 您的 AI 助手现在可以提供任务引导服务")
            logger.info("⚠ 注意: RAG 知识问答功能需要修复 Weaviate 后重新导入")
        else:
            logger.warning("⚠ 数据导入部分成功，请检查上述错误信息")
            logger.info(f"任务数据: {'✓' if task_success else '✗'}")
            logger.info(f"UI元素: {'✓' if ui_success else '✗'}")
        logger.info("=" * 60)
        
        return task_success and ui_success

def main():
    """主函数"""
    try:
        print("=" * 50)
        print("简化数据导入脚本启动")
        print("=" * 50)
        
        # 检查数据目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"当前目录: {current_dir}")
        data_dir = os.path.join(current_dir, "data")
        print(f"数据目录: {data_dir}")
        
        if not os.path.exists(data_dir):
            print(f"错误: 数据目录不存在 {data_dir}")
            print("请确保在 backend 目录运行此脚本")
            return 1
        
        print("开始执行数据导入...")
        # 执行数据导入
        ingester = SimpleDataIngester()
        success = ingester.run()
        
        if success:
            print("✅ 数据导入完成!")
        else:
            print("❌ 数据导入失败!")
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n用户中断操作")
        return 1
    except Exception as e:
        print(f"程序执行出错: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())