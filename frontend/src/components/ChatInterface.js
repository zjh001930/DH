import React, { useState, useEffect, useRef } from 'react';
import { useApi } from '../hooks/useApi';

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
        url: 'http://localhost:8000/assistant',
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        data: { user_input: input.trim() }
      });

      // 根据后端响应类型处理消息内容
      let content = '抱歉，我现在无法处理你的请求。';
      
      if (response.response_type === 'task_execution') {
        // 任务执行响应
        content = response.data?.message || response.data?.response || '任务已开始执行';
      } else if (response.response_type === 'open_qa') {
        // RAG问答响应
        content = response.data?.answer || response.data?.response || '抱歉，我无法回答这个问题。';
      }

      const assistantMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: content,
        timestamp: new Date()
      };

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
              {message.content}
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