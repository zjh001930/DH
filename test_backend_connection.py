#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试后端连接状态
"""

import requests
import json

def test_backend():
    """测试后端连接"""
    base_url = "http://localhost:8000"
    
    print("🔍 测试后端连接状态")
    print("=" * 50)
    
    # 1. 测试健康检查
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"✅ 健康检查: {response.status_code}")
        print(f"   响应: {response.text}")
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False
    
    # 2. 测试chat接口
    try:
        test_data = {"user_input": "添加分析方法进行信号处理"}
        response = requests.post(
            f"{base_url}/chat", 
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        print(f"✅ Chat接口: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   任务ID: {result.get('task_id')}")
            print(f"   置信度: {result.get('confidence')}")
            print(f"   响应: {result.get('response', '')[:100]}...")
        else:
            print(f"   错误: {response.text}")
            
    except Exception as e:
        print(f"❌ Chat接口测试失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_backend()