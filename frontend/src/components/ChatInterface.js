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
        <p className="task-description">{taskData.description}</p>
      </div>
      <div className="task-steps">
        <h5>操作步骤：</h5>
        <ol>
          {taskData.steps.map((step, index) => (
            <li key={index} className="task-step">
              <div className="step-content">
                <strong>步骤 {step.step}：</strong> {step.step_name}
                {step.screenshot_path && (
                  <div className="step-screenshot">
                    <img 
                      src={`http://localhost:8000${step.screenshot_path}`} 
                      alt={`步骤 ${step.step} 截图`}
                      className="step-image"
                      onError={(e) => {
                        e.target.style.display = 'none';
                      }}
                    />
                  </div>
                )}
              </div>
            </li>
          ))}
        </ol>
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
        url: 'http://localhost:8000/chat',
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