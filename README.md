# Chat Shell 101

一个简化的命令行AI聊天工具，基于LangGraph和OpenAI GPT-4。

## 功能特性

- 交互式命令行聊天界面
- 支持多轮对话（历史记录）
- 显示AI思考过程（可选）
- 内置计算器工具
- JSON文件存储历史记录

## 安装

1. 克隆项目：
```bash
git clone <repository-url>
cd chat_shell_101
```

2. 创建虚拟环境并安装依赖：
```bash
# 确保使用 Python 3.10-3.13 版本（Python 3.14 与 LangChain 不兼容）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows
# 使用 uv 安装依赖（更快更可靠）
uv sync
```

3. 配置环境变量：
```bash
cp .env.example .env
# 编辑 .env 文件，设置你的 OpenAI API 密钥
```

**注意**：本项目使用 [uv](https://github.com/astral-sh/uv) 作为包管理工具，它比 pip 更快更可靠。如果你还没有安装 uv，可以使用以下命令安装：
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 使用方法

启动交互式聊天：
```bash
chat-shell chat
```

启动聊天并显示思考过程：
```bash
chat-shell chat --show-thinking
```

使用特定模型：
```bash
chat-shell chat --model gpt-4-turbo
```

## 聊天会话中的命令

- `exit` 或 `quit`：退出聊天
- `/clear`：清除当前会话的历史记录
- `/history`：显示当前会话的历史记录

## 项目结构

```
chat_shell_101/
├── src/chat_shell_101/     # 源代码
├── tests/                  # 测试文件
├── pyproject.toml          # 项目配置
├── .env.example           # 环境变量示例
└── README.md              # 项目说明
```

## 开发

安装开发依赖：
```bash
uv sync --extra dev
```

运行测试：
```bash
pytest
```

## 许可证

Apache 2.0