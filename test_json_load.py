#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_json_loading():
    print("=== JSON任务文件加载测试 ===")
    
    # 模拟意图识别器的路径计算
    intent_recognizer_path = os.path.join(project_root, 'backend', 'workflow', 'intent_recognizer.py')
    json_dir = os.path.join(os.path.dirname(intent_recognizer_path), '..', 'data', 'initial_data')
    json_dir = os.path.abspath(json_dir)  # 转换为绝对路径
    
    print(f"意图识别器文件: {intent_recognizer_path}")
    print(f"计算的JSON目录: {json_dir}")
    print(f"JSON目录是否存在: {os.path.exists(json_dir)}")
    
    if not os.path.exists(json_dir):
        print(f"✗ JSON目录不存在")
        return
    
    # 统计JSON文件
    try:
        json_files = [f for f in os.listdir(json_dir) if f.endswith('.json')]
        print(f"找到 {len(json_files)} 个JSON文件")
        
        # 显示前5个文件
        print("前5个JSON文件:")
        for i, filename in enumerate(json_files[:5]):
            print(f"  {i+1}. {filename}")
        
        # 尝试加载第一个文件
        if json_files:
            first_file = json_files[0]
            file_path = os.path.join(json_dir, first_file)
            print(f"\n尝试加载: {first_file}")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    task_data = json.load(f)
                
                print(f"✓ 成功加载 {first_file}")
                print(f"  task_id: {task_data.get('task_id')}")
                print(f"  task_name: {task_data.get('task_name')}")
                print(f"  steps数量: {len(task_data.get('steps', []))}")
                
            except Exception as e:
                print(f"✗ 加载失败: {e}")
        
    except Exception as e:
        print(f"✗ 读取目录失败: {e}")

if __name__ == "__main__":
    test_json_loading()