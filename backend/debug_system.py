#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统诊断脚本 - 测试意图识别和RAG功能
"""

import os
import sys
import json
import traceback

# 添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_intent_recognition():
    """测试意图识别功能"""
    print("=" * 50)
    print("测试意图识别功能")
    print("=" * 50)
    
    try:
        from workflow.intent_recognizer import IntentRecognizer
        
        # 初始化意图识别器
        recognizer = IntentRecognizer()
        
        # 检查任务数据加载情况
        print(f"已加载任务数量: {len(recognizer.task_data)}")
        print(f"任务关键词数量: {len(recognizer.task_keywords)}")
        
        # 显示前5个任务
        print("\n前5个任务:")
        for i, (task_id, task_info) in enumerate(list(recognizer.task_data.items())[:5]):
            print(f"  {i+1}. {task_id}: {task_info.get('name', 'N/A')}")
        
        # 测试不同类型的输入
        test_inputs = [
            "新建工程",
            "创建新项目", 
            "我想新建一个工程",
            "如何新建项目",
            "帮我新建工程",
            "删除工程",
            "删除项目",
            "怎么删除工程",
            "FFT分析",
            "频谱分析",
            "模态分析",
            "什么是FFT",
            "软件安装要求",
            "系统配置",
            "随机问题测试"
        ]
        
        print("\n意图识别测试结果:")
        for user_input in test_inputs:
            try:
                result = recognizer.recognize_intent(user_input)
                task_id = result.get('task_id')
                confidence = result.get('confidence', 0.0)
                
                # 获取任务名称
                task_name = "未知"
                if task_id and task_id in recognizer.task_data:
                    task_name = recognizer.task_data[task_id].get('name', '未知')
                
                print(f"  输入: '{user_input}'")
                print(f"    -> 任务ID: {task_id}")
                print(f"    -> 任务名: {task_name}")
                print(f"    -> 置信度: {confidence:.2f}")
                print()
                
            except Exception as e:
                print(f"  输入: '{user_input}' - 错误: {e}")
                
    except Exception as e:
        print(f"意图识别测试失败: {e}")
        traceback.print_exc()

def test_rag_functionality():
    """测试RAG功能"""
    print("=" * 50)
    print("测试RAG功能")
    print("=" * 50)
    
    try:
        from rag.handler import RAGHandler
        
        # 初始化RAG处理器
        rag_handler = RAGHandler()
        
        # 测试不同类型的问题
        test_questions = [
            "软件安装要求是什么？",
            "FFT分析的原理是什么？",
            "如何设置采样频率？",
            "模态分析的步骤有哪些？",
            "什么是频谱分析？"
        ]
        
        print("RAG问答测试结果:")
        for question in test_questions:
            try:
                print(f"\n问题: {question}")
                result = rag_handler.answer_question(question)
                answer = result.get('answer', '无答案')
                sources = result.get('sources', [])
                
                print(f"答案: {answer}")
                print(f"知识源数量: {len(sources)}")
                if sources:
                    print("知识源:")
                    for i, source in enumerate(sources[:2]):  # 只显示前2个
                        print(f"  {i+1}. {source[:100]}...")
                
            except Exception as e:
                print(f"问题: '{question}' - 错误: {e}")
                traceback.print_exc()
                
    except Exception as e:
        print(f"RAG功能测试失败: {e}")
        traceback.print_exc()

def test_ollama_connection():
    """测试Ollama连接"""
    print("=" * 50)
    print("测试Ollama连接")
    print("=" * 50)
    
    try:
        from llm.ollama_client import OllamaClient
        
        client = OllamaClient()
        
        # 测试embedding
        print("测试embedding功能...")
        try:
            test_text = "测试文本"
            embedding = client.get_embedding(test_text)
            print(f"Embedding成功，向量维度: {len(embedding)}")
        except Exception as e:
            print(f"Embedding失败: {e}")
        
        # 测试生成
        print("\n测试生成功能...")
        try:
            test_prompt = "请简单回答：什么是FFT？"
            response = client.generate_response(test_prompt)
            print(f"生成成功，响应长度: {len(response)}")
            print(f"响应内容: {response[:200]}...")
        except Exception as e:
            print(f"生成失败: {e}")
            
    except Exception as e:
        print(f"Ollama连接测试失败: {e}")
        traceback.print_exc()

def test_weaviate_connection():
    """测试Weaviate连接"""
    print("=" * 50)
    print("测试Weaviate连接")
    print("=" * 50)
    
    try:
        from db.vector_repo import get_weaviate_client, retrieve_context
        
        # 测试客户端连接
        print("测试Weaviate客户端连接...")
        try:
            client = get_weaviate_client()
            print("Weaviate客户端连接成功")
        except Exception as e:
            print(f"Weaviate客户端连接失败: {e}")
        
        # 测试检索
        print("\n测试向量检索...")
        try:
            # 使用模拟向量进行测试
            test_vector = [0.1] * 384  # BGE模型通常是384维
            contexts = retrieve_context(test_vector, limit=3)
            print(f"检索成功，获得 {len(contexts)} 个上下文")
            for i, context in enumerate(contexts):
                print(f"  {i+1}. {context[:100]}...")
        except Exception as e:
            print(f"向量检索失败: {e}")
            
    except Exception as e:
        print(f"Weaviate连接测试失败: {e}")
        traceback.print_exc()

def test_chat_endpoint_simulation():
    """模拟chat接口的完整流程"""
    print("=" * 50)
    print("模拟chat接口完整流程")
    print("=" * 50)
    
    test_inputs = [
        "新建工程",
        "删除项目", 
        "FFT分析怎么做",
        "软件安装要求"
    ]
    
    for user_input in test_inputs:
        print(f"\n处理输入: '{user_input}'")
        print("-" * 30)
        
        try:
            # 1. 意图识别
            from workflow.intent_recognizer import IntentRecognizer
            recognizer = IntentRecognizer()
            intent_result = recognizer.recognize_intent(user_input)
            
            task_id = intent_result.get('task_id')
            confidence = intent_result.get('confidence', 0.0)
            
            print(f"意图识别结果: task_id={task_id}, confidence={confidence:.2f}")
            
            # 2. 根据置信度决定处理方式
            confidence_threshold = 0.6
            
            if confidence >= confidence_threshold and task_id:
                print("高置信度 - 返回任务步骤")
                
                # 获取任务数据
                task_data = recognizer.task_data.get(task_id, {})
                if task_data:
                    task_name = task_data.get('name', '未知任务')
                    steps = task_data.get('steps', [])
                    print(f"任务名称: {task_name}")
                    print(f"步骤数量: {len(steps)}")
                    if steps:
                        print("步骤:")
                        for i, step in enumerate(steps[:3]):  # 只显示前3步
                            print(f"  {i+1}. {step}")
                else:
                    print("未找到任务数据")
            else:
                print("低置信度 - 使用RAG问答")
                
                # RAG处理
                from rag.handler import RAGHandler
                rag_handler = RAGHandler()
                rag_result = rag_handler.answer_question(user_input)
                
                answer = rag_result.get('answer', '无答案')
                sources = rag_result.get('sources', [])
                
                print(f"RAG答案: {answer[:200]}...")
                print(f"知识源数量: {len(sources)}")
                
        except Exception as e:
            print(f"处理失败: {e}")
            traceback.print_exc()

def main():
    """主函数"""
    print("AI助手系统诊断开始")
    print("=" * 60)
    
    # 1. 测试意图识别
    test_intent_recognition()
    
    # 2. 测试Ollama连接
    test_ollama_connection()
    
    # 3. 测试Weaviate连接
    test_weaviate_connection()
    
    # 4. 测试RAG功能
    test_rag_functionality()
    
    # 5. 模拟完整流程
    test_chat_endpoint_simulation()
    
    print("\n" + "=" * 60)
    print("系统诊断完成")

if __name__ == "__main__":
    main()