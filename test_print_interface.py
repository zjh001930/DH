#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试"查看打印界面"任务的处理
"""

import requests
import json
import sys
import os

# 添加backend目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_print_interface_api():
    """测试API接口"""
    print("🧪 测试 /chat 接口 - 查看打印界面")
    print("=" * 60)
    
    url = "http://localhost:8000/chat"
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
            print(f"✅ API响应成功")
            print(f"响应类型: {result.get('response_type', 'N/A')}")
            print(f"识别的任务ID: {result.get('recognized_task_id', 'N/A')}")
            print(f"置信度: {result.get('confidence', 'N/A')}")
            
            data = result.get('data', {})
            print(f"任务名称: {data.get('task_name', 'N/A')}")
            print(f"任务描述: {data.get('description', 'N/A')}")
            
            steps = data.get('steps', [])
            print(f"步骤数量: {len(steps)}")
            
            if steps:
                print("\n📋 步骤详情:")
                for step in steps:
                    print(f"  {step.get('step_number', '?')}. {step.get('step_name', '未知')}")
                    print(f"     元素ID: {step.get('element_id', '无')}")
                    print(f"     图片路径: {step.get('image_path', '无')}")
            
            response_text = data.get('response_text', '')
            print(f"\n💬 响应文本:")
            print(response_text)
            
        else:
            print(f"❌ API响应失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")

def test_intent_recognition():
    """测试意图识别"""
    print("\n🧠 测试意图识别")
    print("=" * 60)
    
    try:
        from workflow.intent_recognizer import IntentRecognizer
        
        recognizer = IntentRecognizer()
        result = recognizer.recognize_intent("查看打印界面")
        
        print(f"识别结果: {result.get('task_id', 'N/A')}")
        print(f"置信度: {result.get('confidence', 'N/A')}")
        
        task_id = result.get('task_id')
        if task_id and task_id in recognizer.task_data:
            task_data = recognizer.task_data[task_id]
            print(f"任务名称: {task_data.get('name', 'N/A')}")
            print(f"步骤数量: {len(task_data.get('steps', []))}")
        
    except Exception as e:
        print(f"❌ 意图识别测试失败: {e}")

def test_database_task():
    """测试数据库中的任务数据"""
    print("\n🗄️ 测试数据库任务数据")
    print("=" * 60)
    
    try:
        from db.sql_repo import get_task_details
        
        task_details = get_task_details("task_view_print_interface")
        
        if task_details:
            print(f"✅ 数据库中找到任务")
            print(f"任务名称: {task_details.get('task_name', 'N/A')}")
            print(f"任务描述: {task_details.get('description', 'N/A')}")
            
            steps = task_details.get('steps', [])
            print(f"步骤数量: {len(steps)}")
            
            if steps:
                print("\n📋 数据库步骤详情:")
                for step in steps:
                    print(f"  {step.get('step', '?')}. {step.get('step_name', '未知')}")
                    print(f"     元素ID: {step.get('element_id', '无')}")
                    print(f"     动作: {step.get('action', '无')}")
        else:
            print("❌ 数据库中未找到任务")
            
    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")

if __name__ == "__main__":
    test_intent_recognition()
    test_database_task()
    test_print_interface_api()