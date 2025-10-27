# backend/db/sql_repo.py
import os
import sys
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import logging

# 添加相对导入路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import SQLALCHEMY_DATABASE_URL

# 配置日志
logger = logging.getLogger(__name__)

# SQLAlchemy 基础配置
Base = declarative_base()
engine = None
SessionLocal = None

# 数据库模型定义
class Task(Base):
    """任务表模型"""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(100), unique=True, nullable=False, index=True)
    task_name = Column(String(200), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联任务步骤
    steps = relationship("TaskStep", back_populates="task", cascade="all, delete-orphan")

class TaskStep(Base):
    """任务步骤表模型"""
    __tablename__ = "task_steps"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(100), ForeignKey("tasks.task_id"), nullable=False)
    step_number = Column(Integer, nullable=False)
    step_name = Column(String(200), nullable=False)
    element_id = Column(String(100))
    action = Column(String(50))
    dialogue_copy_id = Column(String(100))
    screenshot_path = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联任务
    task = relationship("Task", back_populates="steps")

class UIElement(Base):
    """UI元素表模型"""
    __tablename__ = "ui_elements"
    
    id = Column(Integer, primary_key=True, index=True)
    element_id = Column(String(100), unique=True, nullable=False, index=True)
    element_name = Column(String(200))
    element_type = Column(String(50))
    screenshot_path = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)

def initialize_db():
    """初始化数据库连接和表结构"""
    global engine, SessionLocal
    
    try:
        logger.info(f"[SQL_REPO] 正在初始化数据库: {SQLALCHEMY_DATABASE_URL}")
        
        # 创建数据库引擎
        engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=False)
        
        # 创建会话工厂
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        
        logger.info("[SQL_REPO] ✓ 数据库初始化成功")
        return True
        
    except Exception as e:
        logger.error(f"[SQL_REPO] ✗ 数据库初始化失败: {e}")
        return False

def get_db_session():
    """获取数据库会话"""
    if SessionLocal is None:
        initialize_db()
    return SessionLocal()

def insert_task(task_data: dict) -> bool:
    """插入任务数据"""
    session = get_db_session()
    try:
        # 检查任务是否已存在
        existing_task = session.query(Task).filter(Task.task_id == task_data['task_id']).first()
        
        if existing_task:
            # 更新现有任务
            existing_task.task_name = task_data['task_name']
            existing_task.description = task_data['description']
            task = existing_task
            logger.info(f"[SQL_REPO] 更新任务: {task_data['task_id']}")
        else:
            # 创建新任务
            task = Task(
                task_id=task_data['task_id'],
                task_name=task_data['task_name'],
                description=task_data['description']
            )
            session.add(task)
            logger.info(f"[SQL_REPO] 创建新任务: {task_data['task_id']}")
        
        session.commit()
        return True
        
    except Exception as e:
        logger.error(f"[SQL_REPO] 插入任务失败: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def insert_task_steps(task_id: str, steps_data: list) -> bool:
    """插入任务步骤数据"""
    session = get_db_session()
    try:
        # 删除现有步骤
        session.query(TaskStep).filter(TaskStep.task_id == task_id).delete()
        
        # 插入新步骤
        for step_data in steps_data:
            step = TaskStep(
                task_id=task_id,
                step_number=step_data['step'],
                step_name=step_data['step_name'],
                element_id=step_data.get('element_id'),
                action=step_data.get('action'),
                dialogue_copy_id=step_data.get('dialogue_copy_id'),
                screenshot_path=step_data.get('screenshot_path')
            )
            session.add(step)
        
        session.commit()
        logger.info(f"[SQL_REPO] 插入 {len(steps_data)} 个任务步骤")
        return True
        
    except Exception as e:
        logger.error(f"[SQL_REPO] 插入任务步骤失败: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def insert_ui_element(element_data: dict) -> bool:
    """插入UI元素数据"""
    session = get_db_session()
    try:
        # 检查元素是否已存在
        existing_element = session.query(UIElement).filter(
            UIElement.element_id == element_data['element_id']
        ).first()
        
        if existing_element:
            # 更新现有元素
            existing_element.element_name = element_data['element_name']
            existing_element.element_type = element_data['element_type']
            existing_element.screenshot_path = element_data['screenshot_path']
        else:
            # 创建新元素
            element = UIElement(
                element_id=element_data['element_id'],
                element_name=element_data['element_name'],
                element_type=element_data['element_type'],
                screenshot_path=element_data['screenshot_path']
            )
            session.add(element)
        
        session.commit()
        return True
        
    except Exception as e:
        logger.error(f"[SQL_REPO] 插入UI元素失败: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def get_task_details(task_id: str) -> dict:
    """从数据库获取任务详情"""
    session = get_db_session()
    try:
        task = session.query(Task).filter(Task.task_id == task_id).first()
        
        if not task:
            return None
        
        # 获取任务步骤
        steps = session.query(TaskStep).filter(
            TaskStep.task_id == task_id
        ).order_by(TaskStep.step_number).all()
        
        return {
            "task_id": task.task_id,
            "task_name": task.task_name,
            "description": task.description,
            "steps": [
                {
                    "step": step.step_number,
                    "step_name": step.step_name,
                    "element_id": step.element_id,
                    "action": step.action,
                    "dialogue_copy_id": step.dialogue_copy_id,
                    "screenshot_url": step.screenshot_path
                }
                for step in steps
            ]
        }
        
    except Exception as e:
        logger.error(f"[SQL_REPO] 获取任务详情失败: {e}")
        return None
    finally:
        session.close()

def get_all_tasks() -> list:
    """获取所有任务列表"""
    session = get_db_session()
    try:
        tasks = session.query(Task).all()
        return [
            {
                "task_id": task.task_id,
                "task_name": task.task_name,
                "description": task.description
            }
            for task in tasks
        ]
    except Exception as e:
        logger.error(f"[SQL_REPO] 获取任务列表失败: {e}")
        return []
    finally:
        session.close()

def get_ui_element(element_id: str) -> dict:
    """获取UI元素信息"""
    session = get_db_session()
    try:
        element = session.query(UIElement).filter(
            UIElement.element_id == element_id
        ).first()
        
        if not element:
            return None
            
        return {
            "element_id": element.element_id,
            "element_name": element.element_name,
            "element_type": element.element_type,
            "screenshot_path": element.screenshot_path
        }
        
    except Exception as e:
        logger.error(f"[SQL_REPO] 获取UI元素失败: {e}")
        return None
    finally:
        session.close()
