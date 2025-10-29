#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速调试意图识别
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

def test_intent_matching():
    """测试意图匹配"""
    try:
        from workflow.intent_recognizer import IntentRecognizer
        from config.settings import INTENT_CONFIDENCE_THRESHOLD
        
        print("🔍 快速调试意图识别")
        print("=" * 50)
        print(f"置信度阈值: {INTENT_CONFIDENCE_THRESHOLD}")
        
        # 初始化意图识别器
        recognizer = IntentRecognizer()
        print(f"已加载 {len(recognizer.task_data)} 个任务")
        
        # 显示前10个任务作为示例
        task_list = list(recognizer.task_data.keys())
        print(f"任务示例 (前10个): {task_list[:10]}")
        
        # 检查目标任务
        target_task = "task_signal_add_spectrum_analysis"
        if target_task in recognizer.task_data:
            task_info = recognizer.task_data[target_task]
            print(f"\n📋 目标任务:")
            print(f"   ID: {target_task}")
            print(f"   名称: {task_info['name']}")
            print(f"   描述: {task_info['description']}")
            print(f"   关键词: {recognizer.task_keywords.get(target_task, [])}")
            if 'steps' in task_info:
                print(f"   步骤数量: {len(task_info['steps'])}")
        else:
            print(f"\n❌ 未找到目标任务: {target_task}")
        
        # 测试匹配
        test_inputs = [
            "添加分析方法进行信号处理",
            "我想添加分析方法进行信号处理",
            "添加分析方法",
            "信号处理",
            "如何进行FFT分析",
            "帮我做频谱分析",
            "新建项目",
            "打开项目",
            "随便说点什么"
        ]
        
        print(f"\n🧪 测试匹配:")
        for test_input in test_inputs:
            result = recognizer.recognize(test_input)
            task_id = result.get("recognized_task_id")
            confidence = result.get("confidence")
            
            print(f"   输入: \"{test_input}\"")
            print(f"   结果: {task_id} (置信度: {confidence:.3f})")
            
            # 如果识别到任务，显示任务详细信息
            if confidence > 0.5 and task_id in recognizer.task_data:
                task_info = recognizer.task_data[task_id]
                print(f"   任务名称: {task_info['name']}")
                if 'steps' in task_info and task_info['steps']:
                    print(f"   第一步: {task_info['steps'][0]}")
            
            if confidence >= INTENT_CONFIDENCE_THRESHOLD:
                print(f"   ✅ 高置信度 - 会执行任务")
            else:
                print(f"   ❌ 低置信度 - 会走RAG")
            print()
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_intent_matching()