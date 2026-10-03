# Multi-Agent-Research-Assistant
本项目是一个基于多 Agent 协作（Orchestrator-Workers 模式）的智能信息搜集与报告生成系统。用户只需输入一个研究主题，系统即可自动完成本地资料检索、互联网实时搜索、核心要点提炼，并最终生成一份结构化的行业研究报告。
## ✨ 核心功能
- **多 Agent 协作**：搜索官（负责采集）、总结官（负责提炼）、首席顾问（负责撰写报告），职责分明，协同工作。
- **双路信息检索**：优先读取本地文件（RAG机制）；若本地文件缺失，自动降级为联网搜索（Tavily API），确保信息完整。
- **轻量级持久化记忆**：手搓 `MiniMemory` 模块，基于 JSON 实现长短期记忆存储、滑动窗口截断，并支持历史对话检索。
- **高容错工具调用**：解决了大模型传参丢失、工具选择困难、死循环等实际工程问题。

## 🛠️ 技术栈
- **AI 框架**：HelloAgents (SimpleAgent, Tool)
- **大语言模型**：DeepSeek V4.1
- **后端服务**：FastAPI (支持前后端分离)
- **外部工具**：Tavily Search API
- **语言**：Python 3.11

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install hello-agents fastapi uvicorn requests
2. 配置环境变量
在项目根目录创建 .env 文件：

env
DASHSCOPE_API_KEY=your_api_key
TAVILY_API_KEY=your_tavily_key
3. 运行项目（终端模式）
bash
python study_assistant.py
输入你感兴趣的话题，例如："2026年AI Agent的最新发展趋势"，即可看到多 Agent 协同工作并输出报告。

4. 运行后端服务（Web 模式）
bash
python server.py
# 浏览器访问 http://localhost:8000/docs 测试 API
