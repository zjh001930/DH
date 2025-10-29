#!/usr/bin/env python3
"""
测试图片访问
"""

import requests
import time

def test_image_access():
    """测试图片API访问"""
    
    print("=== 测试图片API访问 ===")
    
    # 等待服务启动
    print("等待服务启动...")
    time.sleep(2)
    
    test_images = ["btn_nav_analysis.png", "btn_subnav_signal_processing.png"]
    
    for img_name in test_images:
        try:
            url = f"http://localhost:8000/tasks/screenshots/{img_name}"
            print(f"\n测试URL: {url}")
            
            response = requests.get(url, timeout=10)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                print(f"✓ 图片可访问")
                print(f"Content-Type: {response.headers.get('Content-Type')}")
                print(f"Content-Length: {response.headers.get('Content-Length')}")
            else:
                print(f"✗ 图片不可访问")
                print(f"响应内容: {response.text[:200]}")
                
        except Exception as e:
            print(f"✗ 请求失败: {e}")

def test_chat_with_image():
    """测试聊天接口返回的图片路径"""
    
    print("\n=== 测试聊天接口图片路径 ===")
    
    try:
        url = "http://localhost:8000/chat"
        data = {"user_input": "查看事后信号处理界面"}
        
        print(f"发送请求到: {url}")
        print(f"请求数据: {data}")
        
        response = requests.post(url, json=data, timeout=30)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"响应类型: {result.get('response_type')}")
            
            if result.get('response_type') == 'task_execution':
                steps = result.get('data', {}).get('steps', [])
                print(f"步骤数量: {len(steps)}")
                
                for i, step in enumerate(steps):
                    print(f"\n步骤 {i+1}:")
                    print(f"  描述: {step.get('description')}")
                    print(f"  图片路径: {step.get('image_path')}")
                    print(f"  元素ID: {step.get('element_id')}")
                    
                    # 测试图片路径
                    if step.get('image_path'):
                        img_url = f"http://localhost:8000{step['image_path']}"
                        try:
                            img_response = requests.get(img_url, timeout=5)
                            if img_response.status_code == 200:
                                print(f"  ✓ 图片可访问")
                            else:
                                print(f"  ✗ 图片不可访问 (状态码: {img_response.status_code})")
                        except Exception as e:
                            print(f"  ✗ 图片访问失败: {e}")
            else:
                print("响应不是任务执行类型")
        else:
            print(f"请求失败: {response.text}")
            
    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == "__main__":
    test_image_access()
    test_chat_with_image()