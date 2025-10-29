#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单API测试 - 用于诊断API响应问题
支持本地和Docker环境
"""

import requests
import time
import os

def test_simple_question():
    """测试一个简单问题"""
    # 自动检测环境
    if os.path.exists('/.dockerenv') or os.environ.get('DOCKER_ENV'):
        base_url = "http://localhost:8000"
        print("🐳 Docker环境检测")
    else:
        base_url = "http://localhost:8000"
        print("💻 本地环境检测")
    
    print(f"🔗 使用后端地址: {base_url}")
    
    print("🔍 测试简单API调用")
    print("=" * 30)
    
    # 测试一个非常简单的问题
    simple_questions = [
        "查看打印界面",
        "打印界面",
        "你好"
    ]
    
    for question in simple_questions:
        print(f"\n📝 测试问题: '{question}'")
        
        try:
            start_time = time.time()
            
            response = requests.post(
                f"{base_url}/assistant",
                json={"user_input": question},
                timeout=30  # 增加超时时间
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"   响应时间: {duration:.2f}秒")
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ 成功")
                print(f"   响应类型: {data.get('response_type')}")
                print(f"   任务ID: {data.get('recognized_task_id')}")
                print(f"   置信度: {data.get('confidence')}")
                
                # 如果是任务引导响应，显示步骤信息
                if data.get('response_type') == 'task_guidance':
                    task_data = data.get('data', {})
                    steps = task_data.get('steps', [])
                    print(f"   任务名称: {task_data.get('task_name')}")
                    print(f"   步骤数量: {len(steps)}")
                    if steps:
                        print(f"   第一步: {steps[0].get('step_name')}")
                
                # 如果是RAG响应，检查答案长度
                elif data.get('response_type') == 'open_qa':
                    answer = data.get('data', {}).get('answer', '')
                    sources = data.get('data', {}).get('sources', [])
                    print(f"   答案长度: {len(answer)} 字符")
                    print(f"   知识源数量: {len(sources)}")
                    
                # 显示响应文本的前100个字符
                response_text = data.get('data', {}).get('response_text', '')
                if response_text:
                    print(f"   响应预览: {response_text[:100]}...")
                    
                break  # 成功一个就够了
                
            else:
                print(f"   ❌ 失败: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   错误: {error_data.get('error')}")
                except:
                    print(f"   响应: {response.text[:200]}")
                    
        except requests.exceptions.Timeout:
            print(f"   ❌ 超时 (30秒)")
        except Exception as e:
            print(f"   ❌ 异常: {str(e)}")

def test_with_curl():
    """提供curl命令进行手动测试"""
    print("\n🔧 手动测试命令")
    print("=" * 30)
    print("您也可以使用以下curl命令手动测试:")
    print()
    print('curl -X POST http://localhost:8000/assistant \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"user_input": "你好"}\'')
    print()
    print("或者使用PowerShell:")
    print('$body = @{user_input="你好"} | ConvertTo-Json')
    print('Invoke-RestMethod -Uri "http://localhost:8000/assistant" -Method Post -Body $body -ContentType "application/json"')

if __name__ == "__main__":
    test_simple_question()
    test_with_curl()