import React, { useState, useEffect, useRef } from 'react';
import { useApi } from '../hooks/useApi';

// 任务执行消息组件
const TaskExecutionMessage = ({ taskData }) => {
  if (!taskData || !taskData.steps) {
    return <div>任务数据加载失败</div>;
  }

  return (
    <div className="task-execution-message">
      <div className="task-header">
        <h4>{taskData.task_name}</h4>
        {taskData.description && <p className="task-description">{taskData.description}</p>}
      </div>
      
      {/* 显示AI生成的回答文本 */}
      {taskData.response_text && (
        <div className="task-response-text">
          <p>{taskData.response_text}</p>
        </div>
      )}
      
      <div className="task-steps">
        <h5>操作步骤：</h5>
        <div className="steps-container">
          {taskData.steps.map((step, index) => (
            <div key={index} className="task-step">
              <div className="step-header">
                <span className="step-number">{step.step_number}</span>
                <div className="step-info">
                  <strong className="step-title">
                    {step.step_name || step.description}
                  </strong>
                  {step.action && (
                    <span className="step-action">
                      {step.action === 'click' ? '点击操作' : 
                       step.action === 'input' ? '输入操作' : step.action}
                    </span>
                  )}
                </div>
              </div>
              
              {step.image_path && (
                <div className="step-screenshot">
                  <img 
                    src={`${process.env.REACT_APP_BACKEND_URL || '/api'}${step.image_path}`} 
                    alt={`步骤 ${step.step_number} 截图`}
                    className="step-image"
                    onError={(e) => {
                      e.target.style.display = 'none';
                      // 显示备用文本
                      const fallback = document.createElement('div');
                      fallback.className = 'image-fallback';
                      fallback.textContent = '图片加载失败';
                      e.target.parentNode.appendChild(fallback);
                    }}
                    onLoad={(e) => {
                      // 图片加载成功，移除可能存在的错误提示
                      const fallback = e.target.parentNode.querySelector('.image-fallback');
                      if (fallback) fallback.remove();
                    }}
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const ChatInterface = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'assistant',
      content: '你好！我是你的AI助手，有什么可以帮助你的吗？',
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const { loading, error, request } = useApi();
  const messagesEndRef = useRef(null);
  const backendUrl = process.env.REACT_APP_BACKEND_URL || '/api';

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: input.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');

    try {
      const response = await request({
        url: '/chat',
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        data: { user_input: input.trim() }
      });

      // 根据后端响应类型处理消息内容
      let assistantMessage;
      
      if (response.response_type === 'task_execution') {
        // 任务执行响应 - 结构化数据
        assistantMessage = {
          id: Date.now() + 1,
          type: 'assistant',
          responseType: 'task_execution',
          taskData: response.data,
          timestamp: new Date()
        };
      } else if (response.response_type === 'open_qa') {
        // RAG问答响应 - 纯文本
        assistantMessage = {
          id: Date.now() + 1,
          type: 'assistant',
          responseType: 'open_qa',
          content: response.data?.answer || response.data?.response || '抱歉，我无法回答这个问题。',
          timestamp: new Date()
        };
      } else {
        // 默认响应
        assistantMessage = {
          id: Date.now() + 1,
          type: 'assistant',
          responseType: 'default',
          content: '抱歉，我现在无法处理你的请求。',
          timestamp: new Date()
        };
      }

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      const errorMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: '抱歉，发生了错误。请稍后再试。',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  const formatTime = (timestamp) => {
    return timestamp.toLocaleTimeString('zh-CN', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h2>AI 助手对话</h2>
      </div>
      
      <div className="chat-messages">
        {messages.map((message) => (
          <div key={message.id} className={`message ${message.type}`}>
            <div className="message-content">
              {message.responseType === 'task_execution' ? (
                <TaskExecutionMessage taskData={message.taskData} />
              ) : (
                message.content
              )}
            </div>
            <div className="message-time">
              {formatTime(message.timestamp)}
            </div>
          </div>
        ))}
        {loading && (
          <div className="message assistant">
            <div className="message-content loading">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
              正在思考...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {error && (
        <div className="error-message">
          连接错误: {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="chat-input-form">
        <div className="chat-input-container">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="输入消息..."
            className="chat-input"
            disabled={loading}
          />
          <button 
            type="submit" 
            className="send-button"
            disabled={loading || !input.trim()}
          >
            发送
          </button>
        </div>
      </form>
    </div>
  );
};

export default ChatInterface;