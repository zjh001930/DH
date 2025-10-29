#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速RAG验证测试
用于快速验证RAG是否从知识库检索信息
支持本地和Docker环境
"""

import requests
import json
import os
import time

def quick_rag_test():
    """快速RAG测试"""
    # 自动检测环境
    if os.path.exists('/.dockerenv') or os.environ.get('DOCKER_ENV'):
        base_url = "http://localhost:8000"
        print("🐳 Docker环境检测")
    else:
        base_url = "http://localhost:8000"
        print("💻 本地环境检测")
    
    print(f"🔗 使用后端地址: {base_url}")
    
    # 测试问题：这些答案只能从您的知识库中获得
    test_questions = [
        {
            "question": "东华测试软件安装对电脑配置有什么要求？",
            "expected_in_answer": ["I5处理器", "16G内存"]
        },
        {
            "question": "应变片最常用的桥路方式是哪种？", 
            "expected_in_answer": ["1/4桥", "方式一"]
        },
        {
            "question": "东华测试软件的抗混滤波是什么？",
            "expected_in_answer": ["低通滤波器", "混叠"]
        }
    ]
    
    print("🔍 快速RAG有效性测试")
    print("=" * 50)
    
    # 检查后端服务状态
    print("🔍 检查后端服务...")
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ 后端服务正常")
            if not data.get('modules_initialized', False):
                print("⚠️  等待模块初始化...")
                time.sleep(3)
        else:
            print(f"❌ 后端服务异常: HTTP {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 无法连接后端: {str(e)}")
        return
    
    rag_working_count = 0
    
    for i, test in enumerate(test_questions, 1):
        print(f"\n📝 测试 {i}: {test['question']}")
        
        try:
            # 发送请求
            response = requests.post(
                f"{base_url}/assistant",
                json={"user_input": test['question']},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # 检查响应类型
                response_type = data.get('response_type')
                confidence = data.get('confidence', 1.0)
                answer = data.get('data', {}).get('answer', '')
                sources = data.get('data', {}).get('sources', [])
                
                print(f"   响应类型: {response_type}")
                print(f"   置信度: {confidence}")
                print(f"   知识源数量: {len(sources)}")
                
                # 检查是否是RAG响应
                is_rag = (
                    response_type == 'open_qa' and 
                    confidence < 0.75 and 
                    len(sources) > 0
                )
                
                # 检查答案中是否包含预期关键词
                keywords_found = []
                for keyword in test['expected_in_answer']:
                    if keyword in answer:
                        keywords_found.append(keyword)
                
                if is_rag and keywords_found:
                    print(f"   ✅ RAG有效 - 找到关键词: {keywords_found}")
                    rag_working_count += 1
                elif is_rag:
                    print(f"   ⚠️  RAG响应但缺少预期关键词")
                else:
                    print(f"   ❌ 非RAG响应 (可能是任务指导或模型自答)")
                    
            else:
                print(f"   ❌ 请求失败: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ 错误: {str(e)}")
    
    print("\n" + "=" * 50)
    print("📊 测试结果")
    print("=" * 50)
    
    success_rate = rag_working_count / len(test_questions) * 100
    print(f"RAG有效测试: {rag_working_count}/{len(test_questions)} ({success_rate:.1f}%)")
    
    if rag_working_count >= len(test_questions) * 0.7:
        print("🎉 结论: RAG系统正常工作！")
        print("✅ 系统能够从知识库检索信息回答问题")
    else:
        print("⚠️  结论: RAG系统可能有问题")
        print("❌ 建议检查知识库数据和向量检索功能")

if __name__ == "__main__":
    quick_rag_test()