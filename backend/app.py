# backend/app.py

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sys
import logging

# 将 backend 目录添加到 Python 路径中，以便 PyCharm/本地调试可以找到相对导入
# 只有在本地运行 app.py 时才需要，在 Docker 环境中 /app 已经是根目录
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 如果在 backend 目录运行，添加父目录到路径
if os.path.basename(os.getcwd()) == 'backend':
    parent_dir = os.path.abspath(os.path.join(os.getcwd(), '..'))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

# 导入配置和核心模块 (使用绝对导入)
from config.settings import INTENT_CONFIDENCE_THRESHOLD, IMAGE_STORAGE_PATH
from workflow.intent_recognizer import IntentRecognizer
from workflow.engine import WorkflowEngine
from rag.handler import RAGHandler

# --- Flask 应用初始化 ---
app = Flask(__name__)
# 允许所有域的跨域请求 (用于本地开发)
CORS(app)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 核心模块的实例化 ---
# 警告：这些初始化会尝试连接 Ollama, PostgreSQL, Weaviate。如果服务未就绪，应用可能在启动时崩溃。
# 在生产环境中使用 gunicorn 等 WSGI 服务器时，应该有更健壮的连接重试逻辑。

# 全局变量用于存储模块实例
intent_recognizer = None
workflow_engine = None
rag_handler = None
modules_initialized = False

def initialize_modules():
    """初始化所有后端模块"""
    global intent_recognizer, workflow_engine, rag_handler, modules_initialized
    
    try:
        # 1. 初始化数据库连接
        from db.sql_repo import initialize_db
        if not initialize_db():
            raise Exception("PostgreSQL 数据库初始化失败")
        print("✓ PostgreSQL 数据库连接成功")
        
        # 2. 初始化核心模块
        intent_recognizer = IntentRecognizer()
        workflow_engine = WorkflowEngine()
        rag_handler = RAGHandler()
        
        modules_initialized = True
        print("✓ Backend modules initialized successfully.")
        return True
        
    except Exception as e:
        print(f"✗ CRITICAL ERROR during backend initialization: {e}")
        modules_initialized = False
        return False

# 尝试初始化模块
initialize_modules()


# --- 根路由: 健康检查 ---
@app.route('/', methods=['GET'])
def health_check():
    """
    健康检查接口，用于前端验证后端连接状态
    """
    global modules_initialized
    
    return jsonify({
        "status": "ok",
        "message": "AI Assistant Backend is running",
        "modules_initialized": modules_initialized,
        "version": "1.0.0"
    })


# --- 5.2.1. 主交互接口: /assistant ---
@app.route('/assistant', methods=['POST'])
def assistant_interface():
    global intent_recognizer, workflow_engine, rag_handler, modules_initialized
    
    # 检查模块初始化状态
    if not modules_initialized or intent_recognizer is None:
        # 尝试重新初始化
        if not initialize_modules():
            return jsonify({
                "error": "Backend modules failed to initialize. Please check database and service connections.",
                "details": "PostgreSQL, Ollama, or Weaviate services may be unavailable."
            }), 503

    data = request.get_json()
    user_input = data.get('user_input', '')

    if not user_input:
        return jsonify({"error": "Missing 'user_input' field"}), 400

    try:
        # 1. 意图识别
        result = intent_recognizer.recognize(user_input)
        task_id = result.get("recognized_task_id")
        confidence = result.get("confidence")

        # 2. 路由分发
        if confidence >= INTENT_CONFIDENCE_THRESHOLD:  # 高置信度 (>= 0.75)
            # 3. 执行任务引导模块
            task_data = workflow_engine.start_task(task_id)
            
            # 检查任务是否找到
            if "error" in task_data:
                return jsonify({
                    "error": f"Task not found: {task_id}",
                    "available_tasks": workflow_engine.get_available_tasks()
                }), 404

            response_data = {
                "response_type": "task_execution",  # 场景一：执行任务
                "recognized_task_id": task_id,
                "confidence": confidence,
                "data": task_data
            }
        else:  # 低置信度 (< 0.75)
            # 3. 执行知识问答模块 (RAG)
            qa_data = rag_handler.answer_question(user_input)

            response_data = {
                "response_type": "open_qa",  # 场景二：RAG 问答
                "recognized_task_id": task_id,
                "confidence": confidence,
                "data": qa_data
            }

        return jsonify(response_data)

    except ConnectionError as e:
        # 专门捕获 Ollama 或数据库连接失败导致的错误
        return jsonify({"error": f"Service connection error: {str(e)}"}), 503
    except Exception as e:
        # 捕获其他运行时错误
        print(f"Unhandled Error processing request: {e}")
        return jsonify({"error": "Internal Server Error during processing."}), 500


# --- 5.2.2. 获取任务列表接口: /tasks ---
@app.route('/tasks', methods=['GET'])
def get_tasks():
    """
    获取所有可用任务的列表
    """
    global workflow_engine, modules_initialized
    
    # 检查模块初始化状态
    if not modules_initialized or workflow_engine is None:
        if not initialize_modules():
            return jsonify({
                "error": "Backend modules not initialized",
                "tasks": []
            }), 503
    
    try:
        tasks = workflow_engine.get_available_tasks()
        return jsonify({
            "success": True,
            "count": len(tasks),
            "tasks": tasks
        })
    except Exception as e:
        logger.error(f"Error retrieving tasks: {e}")
        return jsonify({
            "error": f"Failed to retrieve tasks: {str(e)}",
            "tasks": []
        }), 500


# --- 5.2.3. 任务截图服务接口: /tasks/screenshots/<filename> ---
@app.route('/tasks/screenshots/<path:filename>', methods=['GET'])
def get_screenshot(filename):
    """
    提供静态文件服务，用于前端加载指南中的截图。
    路径映射到 Docker Volume 挂载点: IMAGE_STORAGE_PATH
    """
    # 确保文件路径安全
    try:
        # send_from_directory 会处理路径拼接和文件查找
        return send_from_directory(IMAGE_STORAGE_PATH, filename)
    except FileNotFoundError:
        return "Image not found in storage path.", 404


if __name__ == '__main__':
    # Flask 启动 (注意：生产环境应使用 Gunicorn 或 uWSGI)
    app.run(host='0.0.0.0', port=8000)
