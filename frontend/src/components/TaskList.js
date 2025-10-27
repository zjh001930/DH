import React, { useState, useEffect } from 'react';
import { useApi } from '../hooks/useApi';

const TaskList = () => {
  const [tasks, setTasks] = useState([]);
  const { loading, error, request } = useApi();

  useEffect(() => {
    fetchTasks();
  }, []);

  const fetchTasks = async () => {
    try {
      const response = await request({
        url: 'http://localhost:8000/tasks',
        method: 'GET'
      });
      setTasks(response.tasks || []);
    } catch (err) {
      console.error('获取任务失败:', err);
    }
  };

  const handleTaskClick = (task) => {
    console.log('点击任务:', task);
  };

  if (loading) {
    return (
      <div className="task-list">
        <h3>任务列表</h3>
        <div className="loading">加载中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="task-list">
        <h3>任务列表</h3>
        <div className="error-message">
          加载失败: {error}
        </div>
      </div>
    );
  }

  return (
    <div className="task-list">
      <h3>任务列表</h3>
      {tasks.length === 0 ? (
        <div className="no-tasks">暂无任务</div>
      ) : (
        <ul className="tasks">
          {tasks.map((task, index) => (
            <li 
              key={index} 
              className="task-item"
              onClick={() => handleTaskClick(task)}
            >
              <div className="task-content">
                {typeof task === 'string' ? task : task.title || task.name || '未知任务'}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default TaskList;