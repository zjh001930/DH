#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试意图识别功能
检查数据库中的任务数据和意图识别逻辑
"""

import os
import sys
from dotenv import load_dotenv

# 加载本地环境配置
env_local_path = os.path.join(os.path.dirname(__file__), '.env.local')
if os.path.exists(env_local_path):
    load_dotenv(env_local_path)

# 添加backend目录到Python路径
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.append(backend_dir)

from db.sql_repo import get_all_tasks
from workflow.intent_recognizer import IntentRecognizer

def check_database_tasks():
    """检查数据库中的任务数据"""
    print("🔍 检查数据库中的任务数据...")
    print("=" * 60)
    
    try:
        tasks = get_all_tasks()
        print(f"✅ 数据库中共有 {len(tasks)} 个任务")
        
        # 查找信号处理相关任务
        signal_tasks = []
        for task in tasks:
            task_name = task.get('task_name', '')
            if '信号' in task_name or 'signal' in task_name.lower() or '分析' in task_name:
                signal_tasks.append(task)
        
        print(f"\n📊 找到 {len(signal_tasks)} 个信号处理相关任务:")
        for task in signal_tasks:
            print(f"   - {task['task_id']}: {task['task_name']}")
            print(f"     描述: {task.get('description', '无描述')}")
        
        return tasks
        
    except Exception as e:
        print(f"❌ 检查数据库任务失败: {e}")
        return []

def test_intent_recognizer():
    """测试意图识别器"""
    print("\n🧪 测试意图识别器...")
    print("=" * 60)
    
    try:
        recognizer = IntentRecognizer()
        
        # 显示加载的任务数据
        print(f"✅ 意图识别器已加载 {len(recognizer.task_data)} 个任务")
        
        # 检查特定任务
        target_task = "task_signal_add_spectrum_analysis"
        if target_task in recognizer.task_data:
            task_info = recognizer.task_data[target_task]
            print(f"\n📋 目标任务信息:")
            print(f"   任务ID: {target_task}")
            print(f"   任务名称: {task_info['name']}")
            print(f"   描述: {task_info['description']}")
            print(f"   完整文本: {task_info['full_text']}")
            
            # 显示关键词
            if target_task in recognizer.task_keywords:
                keywords = recognizer.task_keywords[target_task]
                print(f"   关键词: {keywords}")
        else:
            print(f"❌ 未找到目标任务: {target_task}")
        
        # 测试用例
        test_cases = [
            "我想添加分析方法进行信号处理",
            "添加分析方法",
            "信号处理",
            "添加频谱分析",
            "进行信号分析"
        ]
        
        print(f"\n🎯 测试意图识别:")
        for test_input in test_cases:
            result = recognizer.recognize(test_input)
            print(f"   输入: \"{test_input}\"")
            print(f"   结果: {result['recognized_task_id']} (置信度: {result['confidence']:.2f})")
            print()
        
    except Exception as e:
        print(f"❌ 测试意图识别器失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("🔧 意图识别调试工具")
    print("=" * 60)
    
    # 1. 检查数据库任务
    tasks = check_database_tasks()
    
    if not tasks:
        print("\n❌ 数据库中没有任务数据，请先运行数据导入脚本")
        return
    
    # 2. 测试意图识别器
    test_intent_recognizer()
    
    print("=" * 60)
    print("🎉 调试完成")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ 调试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()