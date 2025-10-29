#!/usr/bin/env python3
"""
Weaviate 状态监控脚本
用于诊断和监控 Weaviate 容器的运行状态
"""

import requests
import time
import subprocess
import json
from datetime import datetime

def check_container_status():
    """检查 Weaviate 容器状态"""
    try:
        result = subprocess.run(
            ['docker', 'ps', '--filter', 'name=ai_assistant_weaviate', '--format', 'json'],
            capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore'
        )
        
        if result.stdout and result.stdout.strip():
            container_info = json.loads(result.stdout.strip())
            print(f"✅ 容器状态: {container_info.get('Status', 'Unknown')}")
            return True
        else:
            print("❌ Weaviate 容器未运行")
            return False
    except Exception as e:
        print(f"❌ 检查容器状态失败: {e}")
        return False

def check_weaviate_health():
    """检查 Weaviate 健康状态"""
    try:
        # 检查就绪状态
        response = requests.get('http://localhost:8080/v1/.well-known/ready', timeout=5)
        if response.status_code == 200:
            print("✅ Weaviate 服务就绪")
            return True
        else:
            print(f"⚠️ Weaviate 未就绪，状态码: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Weaviate 健康检查失败: {e}")
        return False

def check_weaviate_schema():
    """检查 Weaviate Schema"""
    try:
        response = requests.get('http://localhost:8080/v1/schema', timeout=5)
        if response.status_code == 200:
            schema = response.json()
            classes = schema.get('classes', [])
            print(f"✅ Schema 正常，包含 {len(classes)} 个类")
            for cls in classes:
                print(f"   - {cls.get('class', 'Unknown')}")
            return True
        else:
            print(f"⚠️ Schema 检查失败，状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Schema 检查失败: {e}")
        return False

def get_container_logs():
    """获取容器日志"""
    try:
        result = subprocess.run(
            ['docker', 'logs', '--tail', '20', 'ai_assistant_weaviate'],
            capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore'
        )
        print("\n📋 最近的容器日志:")
        print("-" * 50)
        print(result.stdout)
        if result.stderr:
            print("错误日志:")
            print(result.stderr)
        print("-" * 50)
    except Exception as e:
        print(f"❌ 获取日志失败: {e}")

def monitor_weaviate(duration_minutes=5):
    """持续监控 Weaviate 状态"""
    print(f"🔍 开始监控 Weaviate，持续 {duration_minutes} 分钟...")
    print(f"监控开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    start_time = time.time()
    check_interval = 30  # 30秒检查一次
    
    while time.time() - start_time < duration_minutes * 60:
        print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')} - 状态检查:")
        
        container_ok = check_container_status()
        if container_ok:
            health_ok = check_weaviate_health()
            if health_ok:
                check_weaviate_schema()
        else:
            print("🔄 尝试重启 Weaviate 容器...")
            try:
                subprocess.run(['docker-compose', 'restart', 'weaviate'], 
                             check=True, encoding='utf-8', errors='ignore')
                print("✅ 重启命令已发送")
            except Exception as e:
                print(f"❌ 重启失败: {e}")
        
        print(f"⏳ 等待 {check_interval} 秒后继续监控...")
        time.sleep(check_interval)
    
    print(f"\n✅ 监控完成，总时长: {duration_minutes} 分钟")

def main():
    print("🔧 Weaviate 状态诊断工具")
    print("=" * 50)
    
    # 初始状态检查
    print("\n1️⃣ 容器状态检查:")
    container_ok = check_container_status()
    
    print("\n2️⃣ 服务健康检查:")
    if container_ok:
        health_ok = check_weaviate_health()
        
        if health_ok:
            print("\n3️⃣ Schema 检查:")
            check_weaviate_schema()
        else:
            print("\n📋 查看容器日志:")
            get_container_logs()
    else:
        print("\n📋 查看容器日志:")
        get_container_logs()
    
    # 询问是否开始监控
    print("\n" + "=" * 50)
    choice = input("是否开始持续监控？(y/n): ").lower().strip()
    
    if choice == 'y':
        try:
            duration = int(input("监控时长（分钟，默认5）: ") or "5")
            monitor_weaviate(duration)
        except KeyboardInterrupt:
            print("\n\n⏹️ 监控已停止")
        except ValueError:
            print("❌ 无效的时长，使用默认值5分钟")
            monitor_weaviate(5)

if __name__ == "__main__":
    main()