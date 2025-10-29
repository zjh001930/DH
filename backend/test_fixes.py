#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复效果的脚本
"""

import os
import sys

# 添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_intent_recognition_fixes():
    """测试意图识别修复效果"""
    print("=" * 50)
    print("测试意图识别修复效果")
    print("=" * 50)
    
    try:
        from workflow.intent_recognizer import IntentRecognizer
        
        recognizer = IntentRecognizer()
        
        print(f"已加载任务数量: {len(recognizer.task_data)}")
        
        # 测试一些常见输入
        test_cases = [
            "新建工程",
            "创建项目",
            "我想新建一个工程",
            "如何新建项目",
            "删除工程",
            "删除项目",
            "怎么删除工程项目",
            "FFT分析",
            "频谱分析",
            "模态分析",
            "什么是FFT",
            "软件安装要求"
        ]
        
        print("\n意图识别测试结果:")
        for user_input in test_cases:
            result = recognizer.recognize_intent(user_input)
            task_id = result.get('task_id')
            confidence = result.get('confidence', 0.0)
            
            # 获取任务名称
            task_name = "未知"
            if task_id and task_id in recognizer.task_data:
                task_name = recognizer.task_data[task_id].get('name', '未知')
            elif task_id == "generic_qa":
                task_name = "通用问答"
            
            print(f"输入: '{user_input}'")
            print(f"  -> 任务ID: {task_id}")
            print(f"  -> 任务名: {task_name}")
            print(f"  -> 置信度: {confidence:.2f}")
            
            # 判断是否会触发任务执行还是RAG
            if confidence >= 0.5 and task_id and task_id != "generic_qa":
                print(f"  -> 处理方式: 任务执行")
            else:
                print(f"  -> 处理方式: RAG问答")
            print()
            
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_chat_simulation():
    """模拟chat接口处理"""
    print("=" * 50)
    print("模拟chat接口处理")
    print("=" * 50)
    
    test_inputs = [
        "新建工程",
        "删除项目",
        "FFT分析怎么做",
        "软件安装要求是什么"
    ]
    
    for user_input in test_inputs:
        print(f"\n处理输入: '{user_input}'")
        print("-" * 30)
        
        try:
            # 模拟chat接口逻辑
            from workflow.intent_recognizer import IntentRecognizer
            recognizer = IntentRecognizer()
            intent_result = recognizer.recognize_intent(user_input)
            
            task_id = intent_result.get('task_id')
            confidence = intent_result.get('confidence', 0.0)
            
            print(f"意图识别: task_id={task_id}, confidence={confidence:.2f}")
            
            confidence_threshold = 0.5
            
            if confidence >= confidence_threshold and task_id and task_id != "generic_qa":
                print("-> 高置信度，返回任务步骤")
                
                task_data = recognizer.task_data.get(task_id, {})
                if task_data:
                    task_name = task_data.get('name', '未知任务')
                    steps = task_data.get('steps', [])
                    print(f"   任务名称: {task_name}")
                    print(f"   步骤数量: {len(steps)}")
                    if steps:
                        print("   前3个步骤:")
                        for i, step in enumerate(steps[:3]):
                            print(f"     {i+1}. {step}")
                else:
                    print("   未找到任务数据")
            else:
                print("-> 低置信度，使用RAG问答")
                try:
                    from rag.handler import RAGHandler
                    rag_handler = RAGHandler()
                    rag_result = rag_handler.answer_question(user_input)
                    
                    answer = rag_result.get('answer', '无答案')
                    sources = rag_result.get('sources', [])
                    
                    print(f"   RAG答案长度: {len(answer)}")
                    print(f"   知识源数量: {len(sources)}")
                    print(f"   答案预览: {answer[:100]}...")
                    
                except Exception as e:
                    print(f"   RAG处理失败: {e}")
                
        except Exception as e:
            print(f"处理失败: {e}")

if __name__ == "__main__":
    test_intent_recognition_fixes()
    test_chat_simulation()