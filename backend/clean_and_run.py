import os
import shutil
import sys

def clean_pycache():
    """清理所有 __pycache__ 目录"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    for root, dirs, files in os.walk(current_dir):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            print(f"删除缓存目录: {pycache_path}")
            try:
                shutil.rmtree(pycache_path)
                print(f"成功删除: {pycache_path}")
            except Exception as e:
                print(f"删除失败: {pycache_path}, 错误: {e}")
            dirs.remove('__pycache__')  # 避免重复遍历

def main():
    print("=" * 50)
    print("清理Python缓存并启动应用")
    print("=" * 50)
    
    print("1. 清理Python缓存...")
    clean_pycache()
    
    print("\n2. 设置Python路径...")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    print(f"当前工作目录: {current_dir}")
    print(f"Python路径: {sys.path[:3]}...")  # 只显示前3个路径
    
    print("\n3. 测试导入...")
    try:
        print("测试导入 config.settings...")
        from config.settings import OLLAMA_API_URL
        print(f"✓ config.settings 导入成功, OLLAMA_API_URL: {OLLAMA_API_URL}")
        
        print("测试导入 llm.ollama_client...")
        from llm.ollama_client import OllamaClient
        print("✓ llm.ollama_client 导入成功")
        
        print("测试导入 workflow.intent_recognizer...")
        from workflow.intent_recognizer import IntentRecognizer
        print("✓ workflow.intent_recognizer 导入成功")
        
    except Exception as e:
        print(f"✗ 导入测试失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n4. 启动Flask应用...")
    try:
        import app
        print("✓ 应用模块导入成功，Flask应用应该已经启动！")
    except Exception as e:
        print(f"✗ 应用启动失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()