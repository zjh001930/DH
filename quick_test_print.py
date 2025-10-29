#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试"查看打印界面"任务
"""

import requests
import json

def test_print_interface():
    """测试查看打印界面任务"""
    print("🧪 快速测试 - 查看打印界面")
    print("=" * 50)
    
    url = "http://localhost:8000/assistant"
    test_data = {"user_input": "查看打印界面"}
    
    try:
        response = requests.post(
            url, 
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 响应成功")
            print(f"响应类型: {result.get('response_type')}")
            print(f"任务ID: {result.get('recognized_task_id')}")
            print(f"置信度: {result.get('confidence')}")
            
            data = result.get('data', {})
            steps = data.get('steps', [])
            print(f"步骤数量: {len(steps)}")
            
            response_text = data.get('response_text', '')
            print(f"\n💬 响应文本:")
            print(response_text)
            
            if steps:
                print(f"\n📋 步骤详情:")
                for step in steps:
                    print(f"  {step.get('step_number')}. {step.get('step_name')}")
                    if step.get('image_path'):
                        print(f"     图片: {step.get('image_path')}")
            
        else:
            print(f"❌ 响应失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")

if __name__ == "__main__":
    test_print_interface()