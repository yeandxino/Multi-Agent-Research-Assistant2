import os
import json
from datetime import datetime
from dotenv import load_dotenv
from typing import List, Any, Dict
import requests
from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.tools import Tool, ToolParameter

load_dotenv()

# ==================== 1. 记忆系统 ====================
class MiniMemory:
    def __init__(self, user_id: str, memory_file: str = "mini_memory.json"):
        self.user_id = user_id
        self.memory_file = memory_file
        self.working_memory = []
        self.episodic_memory = self.load_memory()

    def load_memory(self):
        if os.path.exists(self.memory_file):
            with open(self.memory_file, 'r', encoding="utf-8") as f:
                try:
                    return json.load(f)
                except:
                    return []
        return []

    def add_interaction(self, user_input: str, response: str):
        record = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user": user_input,
            "assistant": response
        }
        self.working_memory.append(record)
        if len(self.working_memory) > 5:
            self.working_memory.pop(0)
        self.episodic_memory.append(record)
        if len(self.episodic_memory) > 100:
            self.episodic_memory.pop(0)
        self.save_memory()

    def save_memory(self):
        with open(self.memory_file, "w", encoding="utf-8") as f:
            json.dump(self.episodic_memory, f, ensure_ascii=False, indent=2)

class MemoryAddTool(Tool):
    def __init__(self, memory_system: MiniMemory):
        super().__init__(name="save_memory", description="保存重要的个人信息或喜好到长期记忆。")
        self.memory = memory_system
    def run(self, parameters: Dict[str, Any]) -> str:
        content = parameters.get("content", "")
        self.memory.add_interaction(content, "（系统自动记录）")
        return f"已经成功存入记忆：{content}"
    def get_parameters(self) -> List[ToolParameter]:
        return [ToolParameter(name="content", type="string", description="需要记住的信息", required=True)]

class MemorySearchTool(Tool):
    def __init__(self, memory_system: MiniMemory):
        super().__init__(name="search_memory", description="回忆用户以前说过的信息。")
        self.memory = memory_system
    def run(self, parameters: Dict[str, Any]) -> str:
        query = parameters.get("query", "")
        return self.memory.retrieve_relevant_memory(query)
    def get_parameters(self) -> List[ToolParameter]:
        return [ToolParameter(name="query", type="string", description="检索关键词", required=True)]

# ==================== 2. 读取文件的工具 ====================
class ReadFileTool(Tool):
    def __init__(self):
        super().__init__(name="read_local_file", description="读取本地文件内容。")
    def run(self, parameters: Dict[str, Any]) -> str:
        file_path = parameters.get("file_path") or parameters.get("path") or parameters.get("filename") or ""
        file_path = file_path.strip().strip('"').strip("'")
        if not file_path:
            return "错误：未提供文件路径。"
        if not os.path.exists(file_path):
            return f"错误：文件 '{file_path}' 不存在。"
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f"文件 '{file_path}' 的内容如下：\n{f.read()}"
        except Exception as e:
            return f"读取文件失败：{str(e)}"
    def get_parameters(self) -> List[ToolParameter]:
        return [ToolParameter(name="file_path", type="string", description="文件路径，例如 'text.md'", required=True)]


class SearchWebTool(Tool):
    def __init__(self):
        super().__init__(
            name="search_web",
            description="联网搜索引擎。当用户询问最新信息、实时新闻或本地文件找不到的内容时，使用此工具。"
        )

    def run(self, parameters: Dict[str, Any]) -> str:
        query = parameters.get("query") or parameters.get("search_query") or parameters.get("keyword") or parameters.get("input") or ""
        if not query:
            return "❌ 错误：未收到搜索关键词！请务必传入 query 参数，例如：search_web(query='2026年AI Agent趋势')"

        print(f"\n🌐 【监控】搜索工具被触发了！正在搜索：{query}")  # 现在这里会有值了

        os.environ['TAVILY_API_KEY'] = 'TAVILY_API_KEY'
        print(f"\n🌐 【监控】搜索工具被触发了！正在搜索：{query}")
        api_key = os.getenv("TAVILY_API_KEY") or "TAVILY_API_KEY"
        if not api_key:
            return "错误：未配置 TAVILY_API_KEY。"
        try:
            url = "https://api.tavily.com/search"
            payload = {
                "api_key": api_key,
                "query": query,
                "search_depth": "basic",
                "include_answer": True,
                "max_results": 3
            }
            response = requests.post(url, json=payload)
            data = response.json()

            if data.get("answer"):
                return f"网络搜索结果总结：\n{data['answer']}"

            results = data.get("results", [])
            if not results:
                return "未找到相关网络信息。"

            formatted = []
            for r in results:
                formatted.append(f"- {r['title']}: {r['content'][:200]}...")
            return "网络搜索结果：\n" + "\n".join(formatted)
        except Exception as e:
            return f"网络搜索失败：{str(e)}"

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(name="query", type="string", description="搜索关键词", required=True)
        ]
# ==================== 3. 初始化系统核心 ====================
llm = HelloAgentsLLM(
    model="deepseek-ai/DeepSeek-V4.1-Flash",
    api_key="api_key",
    base_url="https://api-inference.modelscope.cn/v1"
)

# 创建全局的 memory 实例
memory = MiniMemory(user_id="student_user_001")

# ==================== 4. 创建并组装 Agent ====================

# --- 智囊团 1：搜索官（需要读文件和搜索记忆）---
search_agent = SimpleAgent(
    name="搜索官",
    llm=llm,
    system_prompt='''你是一个高效的信息搜集专家。
你有且只有两个工具：read_local_file 和 search_web。

⚠️ 极权统治级规则：
1. 遇到任何关于“最新趋势”、“资讯”、“新闻”、“2026年”等实时性问题时，**必须立刻调用 `search_web` 工具**。
2. **调用 search_web 时，必须严格传入 `query` 参数！** 例如：`search_web(query="2026年AI Agent趋势")`。
3. 如果读取本地文件失败，立刻转用 `search_web`。
4. 绝对禁止给用户写建议书、禁止问用户要资料。你唯一的工作就是直接调用工具，把搜到的结果交给下一位同事！'''
)
search_agent.add_tool(ReadFileTool())
search_agent.add_tool(SearchWebTool())        # 👈 新增这一行，让它能上网
search_agent.add_tool(MemorySearchTool(memory))
# --- 智囊团 2：总结官 ---
summary_agent = SimpleAgent(
    name="总结官",
    llm=llm,
    system_prompt="你是一个资料整理专家。请把用户提供的长篇信息，提炼成 3 个简短的核心要点。"
)

# --- 智囊团 3：首席顾问（需要保存重要信息到记忆）---
chief_agent = SimpleAgent(
    name="首席顾问",
    llm=llm,
    system_prompt="你是一个首席顾问。请根据用户提供的要点，撰写一份结构清晰的最终报告。"
)
chief_agent.add_tool(MemoryAddTool(memory))  # 👈 给顾问装上存记忆的手

# ==================== 5. 唯一的主循环 ====================
if __name__ == "__main__":
    print("\n=== 开启多 Agent 智囊团（输入 '退出' 结束）===\n")
    while True:
        user_input = input("👤 你：")
        if user_input.strip() == '退出':
            break
        if not user_input.strip():
            continue

        print("🔍 第一步：搜索官正在检索资料...")
        raw_data = search_agent.run(f"关于 '{user_input}' 的资料，本地有 text.md 可以读吗？")

        print("📝 第二步：总结官正在提炼要点...")
        key_points = summary_agent.run(f"请把以下资料提炼成 3 个核心要点：\n{raw_data}")

        print("👔 第三步：首席顾问正在撰写报告...")
        final_report = chief_agent.run(f"请基于以下要点撰写最终报告：\n{key_points}")

        print(f"\n🤖 最终报告：\n{final_report}\n")

        # 主循环兜底保存
        memory.add_interaction(user_input, final_report)