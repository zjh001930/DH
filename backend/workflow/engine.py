# backend/workflow/engine.py
from db.sql_repo import get_task_details, get_all_tasks
import logging

logger = logging.getLogger(__name__)


class WorkflowEngine:
    def __init__(self):
        """初始化工作流引擎"""
        logger.info("[WORKFLOW] WorkflowEngine initialized")
    
    def start_task(self, task_id: str) -> dict:
        """
        根据任务ID，从 PostgreSQL 获取结构化的步骤和截图 URL。
        """
        logger.info(f"[WORKFLOW] Starting task: {task_id}")
        
        try:
            task_details = get_task_details(task_id)
            if task_details and "error" not in task_details:
                logger.info(f"[WORKFLOW] Task {task_id} found with {len(task_details.get('steps', []))} steps")
                return task_details
            else:
                logger.warning(f"[WORKFLOW] Task {task_id} not found in database")
                return {"error": f"Task ID {task_id} not found in database."}
                
        except Exception as e:
            logger.error(f"[WORKFLOW] Error retrieving task {task_id}: {e}")
            return {"error": f"Database error while retrieving task {task_id}: {str(e)}"}
    
    def get_available_tasks(self) -> list:
        """
        获取所有可用的任务列表
        """
        try:
            tasks = get_all_tasks()
            logger.info(f"[WORKFLOW] Retrieved {len(tasks)} available tasks")
            return tasks
        except Exception as e:
            logger.error(f"[WORKFLOW] Error retrieving available tasks: {e}")
            return []

