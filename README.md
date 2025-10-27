
## 🔧 开发指南

### 后端开发

1. 安装 Python 依赖：
```bash
cd backend
pip install -r requirements.txt
```

2. 本地运行后端：
```bash
python app.py
```

### 前端开发

1. 安装 Node.js 依赖：
```bash
cd frontend
npm install
```

2. 启动开发服务器：
```bash
npm start
```

### 数据库操作

连接 PostgreSQL 数据库：
```bash
docker exec -it postgres_db psql -U assistant_user -d assistant_db
```

查看数据表：
```sql
\dt
SELECT COUNT(*) FROM tasks;
SELECT COUNT(*) FROM task_steps;
SELECT COUNT(*) FROM ui_elements;
```

## 🧪 测试验证

### 1. 功能测试

运行测试脚本验证各项功能：

**Windows:**
```cmd
test_data_import.bat
```

**手动测试:**
```bash
# 测试知识问答
curl -X POST http://localhost:8000/assistant \
  -H "Content-Type: application/json" \
  -d '{"query": "如何安装软件？", "conversation_id": "test"}'

# 测试任务引导
curl -X POST http://localhost:8000/assistant \
  -H "Content-Type: application/json" \
  -d '{"query": "我想进行FFT分析", "conversation_id": "test"}'
```

### 2. 健康检查

检查所有服务状态：
```bash
docker-compose ps
```

查看服务日志：
```bash
docker-compose logs -f [service-name]
```

## 🔍 API 接口

### 主要端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/assistant` | POST | 智能助手对话接口 |
| `/tasks` | GET | 获取任务列表 |
| `/tasks/screenshots/<filename>` | GET | 获取任务截图 |

### 请求示例

```json
POST /assistant
{
  "query": "用户问题或指令",
  "conversation_id": "会话ID"
}
```

### 响应示例

```json
{
  "response": "助手回复内容",
  "intent": "识别的意图类型",
  "confidence": 0.85,
  "conversation_id": "会话ID"
}
```

## 🐛 故障排除

### 常见问题

1. **容器启动失败**
   - 检查 Docker 服务是否运行
   - 确认端口未被占用
   - 查看容器日志：`docker-compose logs`

2. **数据导入失败**
   - 确认 PostgreSQL 容器正常运行
   - 检查数据文件是否存在
   - 查看导入日志：`backend/ingest_data_simple.log`

3. **LLM 响应异常**
   - 确认 Ollama 容器正常运行
   - 检查模型是否已下载
   - 验证 API 连接：`curl http://localhost:11434/api/tags`

4. **RAG 功能异常**
   - 确认 Weaviate 容器正常运行
   - 检查向量数据是否已导入
   - 访问 Weaviate 控制台：http://localhost:8080

### 日志查看

```bash
# 查看所有服务日志
docker-compose logs

# 查看特定服务日志
docker-compose logs ollama
docker-compose logs weaviate
docker-compose logs postgres_db

# 查看后端应用日志
docker-compose logs api-layer
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支：`git checkout -b feature/new-feature`
3. 提交更改：`git commit -am 'Add new feature'`
4. 推送分支：`git push origin feature/new-feature`
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 支持

如有问题或建议，请：

1. 查看 [故障排除](#-故障排除) 部分
2. 创建 [Issue](../../issues)
3. 联系项目维护者

---

**注意**: 首次启动可能需要较长时间下载 Docker 镜像和 LLM 模型，请耐心等待。
