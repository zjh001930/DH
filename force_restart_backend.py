#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
强制重启后端
"""

import os
import sys
import subprocess
import time
import requests

def kill_backend_processes():
    """杀死所有可能的后端进程"""
    try:
        # 在Windows上杀死占用8000端口的进程
        result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        for line in lines:
            if ':8000' in line and 'LISTENING' in line:
                parts = line.split()
                if len(parts) > 4:
                    pid = parts[-1]
                    print(f"发现占用8000端口的进程 PID: {pid}")
                    try:
                        subprocess.run(['taskkill', '/F', '/PID', pid], check=True)
                        print(f"已杀死进程 {pid}")
                    except:
                        print(f"无法杀死进程 {pid}")
    except Exception as e:
        print(f"检查进程时出错: {e}")

def start_backend():
    """启动后端"""
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
    app_path = os.path.join(backend_dir, 'app.py')
    
    print(f"启动后端: {app_path}")
    
    # 切换到backend目录并启动
    os.chdir(backend_dir)
    process = subprocess.Popen([sys.executable, 'app.py'])
    
    # 等待启动
    print("等待后端启动...")
    for i in range(10):
        time.sleep(1)
        try:
            response = requests.get('http://localhost:8000/', timeout=2)
            if response.status_code == 200:
                print("✅ 后端启动成功!")
                return process
        except:
            pass
        print(f"等待中... ({i+1}/10)")
    
    print("❌ 后端启动失败")
    return None

def test_chat_route():
    """测试chat路由"""
    try:
        response = requests.post(
            'http://localhost:8000/chat',
            json={'user_input': '测试'},
            timeout=5
        )
        print(f"Chat路由测试: {response.status_code}")
        if response.status_code == 200:
            print("✅ Chat路由正常工作!")
            return True
        else:
            print(f"❌ Chat路由错误: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Chat路由测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🔄 强制重启后端服务")
    print("=" * 50)
    
    # 1. 杀死现有进程
    print("1. 杀死现有后端进程...")
    kill_backend_processes()
    time.sleep(2)
    
    # 2. 启动新进程
    print("2. 启动新的后端进程...")
    process = start_backend()
    
    if process:
        # 3. 测试chat路由
        print("3. 测试chat路由...")
        test_chat_route()
        
        print("\n后端已启动，按Ctrl+C停止")
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\n正在停止后端...")
            process.terminate()
    else:
        print("后端启动失败!")