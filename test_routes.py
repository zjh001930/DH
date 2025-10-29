#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试后端路由
"""

import requests
import json

def test_all_routes():
    """测试所有路由"""
    base_url = "http://localhost:8000"
    
    routes_to_test = [
        ("GET", "/", "健康检查"),
        ("POST", "/assistant", "助手接口"),
        ("POST", "/chat", "聊天接口"),
        ("GET", "/tasks", "任务列表")
    ]
    
    print("🔍 测试所有后端路由")
    print("=" * 50)
    
    for method, path, name in routes_to_test:
        try:
            if method == "GET":
                response = requests.get(f"{base_url}{path}", timeout=5)
            else:
                test_data = {"user_input": "测试"}
                response = requests.post(
                    f"{base_url}{path}", 
                    json=test_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
            
            print(f"{name} ({method} {path}): {response.status_code}")
            
            if response.status_code == 404:
                print(f"   ❌ 路由不存在")
            elif response.status_code >= 400:
                print(f"   ⚠️  错误: {response.text[:100]}")
            else:
                print(f"   ✅ 正常")
                
        except Exception as e:
            print(f"{name} ({method} {path}): ❌ 连接失败 - {e}")
        
        print()

if __name__ == "__main__":
    test_all_routes()