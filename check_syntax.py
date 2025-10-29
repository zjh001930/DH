#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查Python语法
"""

import ast
import sys

def check_syntax(file_path):
    """检查Python文件语法"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 尝试解析AST
        ast.parse(content)
        print(f"✅ {file_path} 语法正确")
        return True
        
    except SyntaxError as e:
        print(f"❌ {file_path} 语法错误:")
        print(f"   行 {e.lineno}: {e.text}")
        print(f"   错误: {e.msg}")
        return False
    except Exception as e:
        print(f"❌ {file_path} 检查失败: {e}")
        return False

if __name__ == "__main__":
    files_to_check = [
        "backend/app.py",
        "backend/workflow/intent_recognizer.py"
    ]
    
    print("🔍 检查Python语法")
    print("=" * 50)
    
    all_good = True
    for file_path in files_to_check:
        if not check_syntax(file_path):
            all_good = False
    
    if all_good:
        print("\n✅ 所有文件语法正确")
    else:
        print("\n❌ 发现语法错误，请修复后重试")