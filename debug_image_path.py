#!/usr/bin/env python3
"""
调试图片路径问题
"""

import os
import requests
from backend.config.settings import IMAGE_STORAGE_PATH

def debug_image_path():
    """调试图片路径配置"""
    
    print("=== 图片路径调试 ===")
    print(f"IMAGE_STORAGE_PATH: {IMAGE_STORAGE_PATH}")
    print(f"当前工作目录: {os.getcwd()}")
    
    # 检查本地文件系统中的图片
    local_image_path = "backend/data/images"
    print(f"\n本地图片目录: {local_image_path}")
    
    if os.path.exists(local_image_path):
        print("✓ 本地图片目录存在")
        files = os.listdir(local_image_path)
        target_files = ["btn_nav_analysis.png", "btn_subnav_signal_processing.png"]
        
        for target_file in target_files:
            if target_file in files:
                print(f"✓ {target_file} 存在于本地")
                file_path = os.path.join(local_image_path, target_file)
                file_size = os.path.getsize(file_path)
                print(f"  文件大小: {file_size} bytes")
            else:
                print(f"✗ {target_file} 不存在于本地")
    else:
        print("✗ 本地图片目录不存在")
    
    # 检查容器内的路径（如果在容器中运行）
    if os.path.exists(IMAGE_STORAGE_PATH):
        print(f"\n✓ 容器图片目录存在: {IMAGE_STORAGE_PATH}")
        try:
            files = os.listdir(IMAGE_STORAGE_PATH)
            print(f"容器图片目录文件数量: {len(files)}")
            
            target_files = ["btn_nav_analysis.png", "btn_subnav_signal_processing.png"]
            for target_file in target_files:
                if target_file in files:
                    print(f"✓ {target_file} 存在于容器")
                    file_path = os.path.join(IMAGE_STORAGE_PATH, target_file)
                    file_size = os.path.getsize(file_path)
                    print(f"  文件大小: {file_size} bytes")
                else:
                    print(f"✗ {target_file} 不存在于容器")
        except Exception as e:
            print(f"✗ 读取容器图片目录失败: {e}")
    else:
        print(f"✗ 容器图片目录不存在: {IMAGE_STORAGE_PATH}")

def test_image_api():
    """测试图片API访问"""
    
    print("\n=== 测试图片API ===")
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

if __name__ == "__main__":
    debug_image_path()
    test_image_api()