import React, { useState, useEffect } from 'react';
import ChatInterface from './components/ChatInterface';
import './index.css';

function App() {
  const [backendConnected, setBackendConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('检查中...');

  useEffect(() => {
    checkBackendConnection();
  }, []);

  const checkBackendConnection = async () => {
    try {
      const baseUrl = process.env.REACT_APP_BACKEND_URL || '/api';
      const response = await fetch(`${baseUrl}/`);
      if (response.ok) {
        setBackendConnected(true);
        setConnectionStatus('已连接');
      } else {
        setBackendConnected(false);
        setConnectionStatus('连接失败');
      }
    } catch (error) {
      setBackendConnected(false);
      setConnectionStatus('无法连接到后端服务');
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>AI 助手</h1>
        <div className={`connection-status ${backendConnected ? 'connected' : 'disconnected'}`}>
          后端状态: {connectionStatus}
        </div>
      </header>

      {backendConnected ? (
        <main className="app-main">
          {/* 删除侧栏：不再渲染 TaskList */}
          <div className="chat-section">
            <ChatInterface />
          </div>
        </main>
      ) : (
        <div className="connection-error">
          <h2>无法连接到后端服务</h2>
          <p>请确保后端服务正在运行在 http://localhost:8000</p>
          <button onClick={checkBackendConnection}>重新连接</button>
        </div>
      )}
    </div>
  );
}

export default App;

async function sendMessage(text) {
    const resp = await fetch(`${backendUrl}/chat`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ user_input: text }) });
    const data = await resp.json();
    if (data.response_type === 'greeting') {
        setMessages(prev => [...prev, { role: 'assistant', content: data.data?.answer || '你好，有什么可以帮助你的吗？' }]);
        return;
    }
}