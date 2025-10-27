// frontend/src/index.js

import React from 'react';
// 【关键修正点】将 'client' 替换为 'react-dom/client'
import ReactDOM from 'react-dom/client';
// import './index.css'; // (如果你创建了 index.css 文件，则保留)
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);