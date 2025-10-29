#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细测试/chat接口功能
"""

import requests
import json

def test_chat_detailed():
    """详细测试chat接口"""
    url = "http://localhost:8000/chat"
    
    test_cases = [
        {
            "name": "目标测试：添加分析方法进行信号处理",
            "data": {"user_input": "添加分析方法进行信号处理"}
        },
        {
            "name": "测试：普通消息",
            "data": {"user_input": "你好"}
        },
        {
            "name": "测试：空消息",
            "data": {"user_input": ""}
        }
    ]
    
    print("🧪 详细测试 /chat 接口")
    print("=" * 60)
    
    for test_case in test_cases:
        print(f"\n📋 {test_case['name']}")
        print("-" * 40)
        
        try:
            response = requests.post(
                url, 
                json=test_case['data'],
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 成功响应")
                print(f"响应内容: {result.get('response', 'N/A')}")
                print(f"任务ID: {result.get('task_id', 'N/A')}")
                print(f"置信度: {result.get('confidence', 'N/A')}")
                
                # 检查是否包含步骤信息
                if 'steps' in result:
                    print(f"步骤数量: {len(result['steps'])}")
                if 'task_name' in result:
                    print(f"任务名称: {result['task_name']}")
                    
            elif response.status_code == 400:
                result = response.json()
                print(f"⚠️ 客户端错误: {result.get('error', 'Unknown error')}")
            else:
                print(f"❌ 服务器错误: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ 连接失败 - 后端可能没有启动")
            break
        except Exception as e:
            print(f"❌ 请求失败: {e}")

if __name__ == "__main__":
    test_chat_detailed()