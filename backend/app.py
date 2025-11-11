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
    
    # 1. 尝试初始化数据库连接（可选）
    db_initialized = False
    try:
        from db.sql_repo import initialize_db
        if initialize_db():
            print("✓ PostgreSQL 数据库连接成功")
            db_initialized = True
        else:
            print("⚠️ PostgreSQL 数据库连接失败，但继续初始化其他模块")
    except Exception as e:
        print(f"⚠️ 数据库初始化失败: {e}，但继续初始化其他模块")
    
    # 2. 初始化核心模块（即使数据库失败也要继续）
    try:
        intent_recognizer = IntentRecognizer()
        print("✓ IntentRecognizer 初始化成功")
        
        workflow_engine = WorkflowEngine()
        print("✓ WorkflowEngine 初始化成功")
        
        # RAG Handler 可能需要向量数据库，如果失败就跳过
        try:
            rag_handler = RAGHandler()
            print("✓ RAGHandler 初始化成功")
        except Exception as e:
            print(f"⚠️ RAGHandler 初始化失败: {e}")
            rag_handler = None
        
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
# backend/app.py
def _is_greeting(text: str) -> bool:
    text = (text or "").strip().lower()
    greetings = ["你好", "您好", "hi", "hello", "hey", "嗨", "在吗"]
    return any(g in text for g in greetings)

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

    # 问候拦截：避免进入意图识别/RAG，直接返回固定短句
    if _is_greeting(user_input):
        return jsonify({
            "response_type": "open_qa",
            "recognized_task_id": None,
            "confidence": 1.0,
            "data": {"answer": "你好，有什么可以帮助你的吗？"}
        })

    # 下面继续原有意图识别与路由
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


@app.route('/chat', methods=['POST'])
def chat_interface():
    """聊天接口 - 使用意图识别决定返回任务步骤还是RAG问答"""
    try:
        # 暂时跳过模块初始化检查，直接使用意图识别
        # if not modules_initialized:
        #     return jsonify({'error': 'Backend modules not initialized'}), 503
            
        data = request.get_json()
        user_input = data.get('user_input', '').strip()
            
        if not user_input:
            return jsonify({'error': 'Missing user_input'}), 400
        
        # 问候拦截：避免进入意图识别/RAG，直接返回固定短句
        if _is_greeting(user_input):
            return jsonify({
                'response_type': 'open_qa',
                'recognized_task_id': None,
                'confidence': 1.0,
                'data': {'answer': '你好，有什么可以帮助你的吗？'}
            })
        
        # 下面继续原有意图识别与RAG逻辑
        from workflow.intent_recognizer import IntentRecognizer
        recognizer = IntentRecognizer()
        intent_result = recognizer.recognize_intent(user_input)
        task_id = intent_result.get('task_id')
        confidence = intent_result.get('confidence', 0.0)
        
        print(f"Intent recognition - Task ID: {task_id}, Confidence: {confidence}")
        
        # 置信度阈值设为0.5（降低阈值以提高任务识别率）
        confidence_threshold = 0.5
        
        if confidence >= confidence_threshold and task_id:
            # 高置信度：返回任务步骤
            try:
                # 直接从意图识别器获取任务数据
                task_data = recognizer.task_data.get(task_id, {})
                
                if not task_data:
                    return jsonify({
                        'response_type': 'open_qa',
                        'recognized_task_id': task_id,
                        'confidence': confidence,
                        'data': {
                            'answer': f'抱歉，找不到任务ID为 {task_id} 的相关信息。'
                        }
                    })
                
                # 构建任务引导响应
                task_name = task_data.get('name', '未知任务')
                steps = task_data.get('steps', [])
                
                # 首先尝试从数据库获取详细步骤信息
                detailed_steps = []
                try:
                    from db.sql_repo import get_task_details
                    task_details = get_task_details(task_id)
                    
                    if task_details and 'steps' in task_details and task_details['steps']:
                        # 使用数据库中的详细步骤信息
                        db_steps = task_details['steps']
                        print(f"从数据库获取到 {len(db_steps)} 个步骤")
                        
                        for i, db_step in enumerate(db_steps):
                            step_info = {
                                'step_number': db_step.get('step', i + 1),
                                'step_name': db_step.get('step_name', f'步骤 {i + 1}'),
                                'description': db_step.get('step_name', f'步骤 {i + 1}'),
                                'element_id': db_step.get('element_id', ''),
                                'action': db_step.get('action', 'click'),
                                'image_path': None
                            }
                            
                            # 构建图片路径
                            element_id = db_step.get('element_id', '')
                            if element_id:
                                # 检查图片文件是否存在
                                image_filename = f"{element_id}.png"
                                image_path = f"/images/{image_filename}"
                                step_info['image_path'] = image_path
                                print(f"  步骤 {i+1}: {step_info['step_name']} -> 图片: {image_filename}")
                            else:
                                print(f"  步骤 {i+1}: {step_info['step_name']} -> 无图片")
                            
                            detailed_steps.append(step_info)
                    else:
                        # 如果数据库中没有详细步骤，使用意图识别器中的步骤
                        print(f"数据库中无详细步骤，使用意图识别器中的 {len(steps)} 个步骤")
                        for i, step in enumerate(steps):
                            step_info = {
                                'step_number': i + 1,
                                'step_name': step if isinstance(step, str) else str(step),
                                'description': step if isinstance(step, str) else str(step),
                                'element_id': '',
                                'action': 'click',
                                'image_path': None
                            }
                            detailed_steps.append(step_info)
                            
                except Exception as e:
                    print(f"获取步骤详情时出错: {e}")
                    # 使用基本步骤信息作为备用
                    for i, step in enumerate(steps):
                        step_info = {
                            'step_number': i + 1,
                            'step_name': step if isinstance(step, str) else str(step),
                            'description': step if isinstance(step, str) else str(step),
                            'element_id': '',
                            'action': 'click',
                            'image_path': None
                        }
                        detailed_steps.append(step_info)
                
                # 生成富文本响应
                if detailed_steps:
                    steps_text = []
                    for step_info in detailed_steps:
                        step_desc = f"{step_info['step_number']}. {step_info.get('step_name', step_info['description'])}"
                        if step_info.get('action') == 'click':
                            step_desc += " (点击操作)"
                        elif step_info.get('action') == 'input':
                            step_desc += " (输入操作)"
                        steps_text.append(step_desc)
                    
                    response_text = f"我来帮你完成「{task_name}」任务。\n\n操作步骤：\n" + "\n".join(steps_text)
                else:
                    response_text = f"我找到了「{task_name}」任务，但暂时没有详细步骤信息。"
                
                return jsonify({
                    'response_type': 'task_execution',
                    'recognized_task_id': task_id,
                    'confidence': confidence,
                    'data': {
                        'task_name': task_name,
                        'description': task_data.get('description', ''),
                        'steps': detailed_steps,
                        'response_text': response_text
                    }
                })
                
            except Exception as e:
                print(f"Error getting task data: {e}")
                return jsonify({
                    'response_type': 'open_qa',
                    'recognized_task_id': task_id,
                    'confidence': confidence,
                    'data': {
                        'answer': f'找到了相关任务（置信度: {confidence:.2f}），但获取详细信息时出现错误。'
                    }
                })
        else:
            # 低置信度：使用RAG问答
            try:
                from rag.handler import RAGHandler
                rag_handler = RAGHandler()
                rag_result = rag_handler.answer_question(user_input)
                
                answer = rag_result.get('answer', '抱歉，我无法找到相关信息。')
                sources = rag_result.get('sources', [])
                
                return jsonify({
                    'response_type': 'open_qa',
                    'recognized_task_id': task_id,
                    'confidence': confidence,
                    'data': {
                        'answer': answer,
                        'sources': sources
                    }
                })
                
            except Exception as e:
                print(f"RAG processing error: {e}")
                return jsonify({
                    'response_type': 'open_qa',
                    'recognized_task_id': task_id,
                    'confidence': confidence,
                    'data': {
                        'answer': f'抱歉，我对你的请求理解不够清楚（置信度: {confidence:.2f}）。请尝试更具体地描述你想要完成的任务，或者检查AI服务是否正常运行。'
                    }
                })
        
    except Exception as e:
        print(f"Chat endpoint error: {e}")
        return jsonify({'error': str(e)}), 500


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

# --- 5.2.4. 图片服务接口: /images/<filename> ---
@app.route('/images/<path:filename>', methods=['GET'])
def get_image(filename):
    """
    提供图片文件服务，用于前端加载步骤中的图片。
    路径映射到 data/images 目录
    """
    try:
        # 构建图片目录路径
        images_dir = os.path.join(os.path.dirname(__file__), 'data', 'images')
        return send_from_directory(images_dir, filename)
    except FileNotFoundError:
        logger.warning(f"Image not found: {filename}")
        return "Image not found.", 404
    except Exception as e:
        logger.error(f"Error serving image {filename}: {e}")
        return "Error serving image.", 500


if __name__ == '__main__':
    # Flask 启动 (注意：生产环境应使用 Gunicorn 或 uWSGI)
    app.run(host='0.0.0.0', port=8000)
