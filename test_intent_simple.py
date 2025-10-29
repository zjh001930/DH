#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# 添加backend目录到Python路径
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.append(backend_dir)

from workflow.intent_recognizer import IntentRecognizer

def test_intent_recognition():
    print("🔍 测试意图识别功能...")
    print("=" * 50)
    
    # 初始化意图识别器
    recognizer = IntentRecognizer()
    
    # 测试用例
    test_cases = [
        "请问怎么添加分析方法进行信号处理",
        "查看打印界面",
        "添加分析方法",
        "信号处理",
        "打印界面"
    ]
    
    for query in test_cases:
        print(f"\n📝 测试查询: '{query}'")
        
        # 测试recognize方法
        result = recognizer.recognize(query)
        print(f"   recognize结果: {result}")
        
        # 测试recognize_intent方法
        result2 = recognizer.recognize_intent(query)
        print(f"   recognize_intent结果: {result2}")
        
        print("-" * 40)

if __name__ == "__main__":
    test_intent_recognition()