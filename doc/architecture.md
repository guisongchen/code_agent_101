# Chat Shell 软件架构文档

## 1. 系统概述

Chat Shell 是一个基于 LangGraph 的 AI 聊天代理服务，提供完整的聊天引擎功能。它是 Wegent（微博智能助手）项目的核心组件，负责处理用户与 AI 的对话交互、工具调用、知识库检索等功能。

### 核心特性

- **多模型支持**：集成 OpenAI、Anthropic Claude、Google Gemini 等多个 LLM 提供商
- **工具系统**：内置工具（Web 搜索、知识库、数据表格、文件读取等）+ MCP 协议动态工具加载
- **技能系统**：支持动态加载和卸载技能（Skills），扩展 Agent 能力
- **多种部署模式**：支持 HTTP 服务、Python 包导入、命令行工具三种模式
- **流式响应**：基于 SSE（Server-Sent Events）的实时流式输出
- **会话管理**：支持会话恢复、取消、历史记录管理
- **智能压缩**：自动消息压缩机制，应对上下文长度限制
- **可观测性**：集成 OpenTelemetry，提供完整的分布式追踪

## 2. 系统架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         Chat Shell Service                       │
│                                                                   │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐    │
│  │   CLI 接口  │  │  HTTP API    │  │  Package Interface  │    │
│  │  (Click)    │  │  (FastAPI)   │  │  (Direct Import)    │    │
│  └──────┬──────┘  └──────┬───────┘  └──────────┬──────────┘    │
│         │                │                      │                │
│         └────────────────┼──────────────────────┘                │
│                          │                                        │
│                  ┌───────▼────────┐                              │
│                  │  Chat Service  │                              │
│                  │  (ChatInterface)│                             │
│                  └───────┬────────┘                              │
│                          │                                        │
│         ┌────────────────┼────────────────┐                     │
│         │                │                │                      │
│    ┌────▼─────┐   ┌─────▼──────┐  ┌─────▼────────┐            │
│    │ ChatAgent│   │  Streaming │  │  Session     │            │
│    │          │   │   Core     │  │  Manager     │            │
│    └────┬─────┘   └─────┬──────┘  └──────────────┘            │
│         │               │                                        │
│    ┌────▼─────────────┐ │                                       │
│    │  LangGraph Agent │ │                                       │
│    │  (ReAct Workflow)│ │                                       │
│    └────┬─────────────┘ │                                       │
│         │               │                                        │
│    ┌────▼────┐    ┌─────▼──────┐                               │
│    │  Tools  │    │  Emitter   │                               │
│    │ Registry│    │  (SSE)     │                               │
│    └─────────┘    └────────────┘                               │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
         │                    │                    │
         │                    │                    │
    ┌────▼────┐          ┌───▼────┐         ┌────▼─────┐
    │  LLM    │          │ Storage│         │ External │
    │Providers│          │Backend │         │  Tools   │
    │(API)    │          │        │         │  (MCP)   │
    └─────────┘          └────────┘         └──────────┘
```

### 2.2 三种部署模式

#### HTTP 模式（默认）
- **场景**：独立 HTTP 服务，与后端（Backend）解耦
- **通信**：Backend 通过 HTTP API 调用 Chat Shell
- **存储**：Remote Storage（调用 Backend 的 `/internal/chat/*` APIs）
- **启动**：`uvicorn chat_shell.main:app --port 8001`

#### Package 模式
- **场景**：Backend 直接导入 Chat Shell 作为 Python 包
- **通信**：Backend 直接调用 Python 函数，无 HTTP 开销
- **存储**：Backend 直接传递消息，无需存储层
- **优势**：性能更高，调试更方便

#### CLI 模式
- **场景**：开发者本地测试和调试
- **通信**：命令行交互界面
- **存储**：SQLite 本地存储（`~/.chat_shell/history.db`）
- **启动**：`chat-shell chat` 或 `chat-shell query "问题"`

## 3. 核心模块

### 3.1 Agent 模块 (`agent.py`, `agents/`)

**职责**：AI Agent 的核心实现，负责创建和执行 LangGraph Agent

**核心组件**：
- `ChatAgent`：主 Agent 类，提供同步和流式执行接口
- `AgentConfig`：Agent 配置数据类
- `LangGraphAgentBuilder`：使用 LangGraph 的 `create_react_agent` 构建 ReAct 工作流
- `MessageCompressor`：自动消息压缩，处理上下文长度限制

**关键特性**：
- ReAct（Reasoning + Acting）工作流
- 工具循环迭代限制（默认 10 次）
- 动态提示词注入（PromptModifierTool）
- State Checkpointing 支持会话恢复

### 3.2 Tools 模块 (`tools/`)

**职责**：工具注册、管理和执行

**工具类型**：

1. **内置工具** (`builtin/`)
   - `WebSearchTool`：网络搜索
   - `KnowledgeBaseTool`：知识库检索（RAG）
   - `DataTableTool`：数据表格查询
   - `FileReaderTool`：文件读取和解析
   - `LoadSkillTool`：动态加载技能
   - `CreateSubscriptionTool`：创建订阅任务
   - `SilentExitTool`：静默退出（用于订阅任务）
   - `EvaluationTool`：评估工具

2. **MCP 工具** (`mcp/`)
   - 基于 Model Context Protocol 的动态工具加载
   - 支持远程工具服务器连接

3. **技能工具** (`skill_factory.py`)
   - 从后端动态加载的自定义工具
   - 支持预加载（preload）机制

**核心类**：
- `ToolRegistry`：工具注册表，管理所有可用工具
- `PromptModifierTool`：协议接口，支持工具动态修改系统提示词
- `KnowledgeInjectionStrategy`：知识注入策略（相关性排序、时间排序等）

### 3.3 Services 模块 (`services/`)

**职责**：业务逻辑层，协调 Agent、Storage、Streaming

**核心组件**：

1. **ChatService** (`chat_service.py`)
   - 实现 `ChatInterface` 接口
   - 处理聊天请求、恢复、取消操作
   - 协调 Agent 执行和事件流输出

2. **ChatContext** (`context.py`)
   - 上下文管理器，负责 Agent 创建和配置
   - 工具初始化和依赖注入
   - 模型配置和选择

3. **Storage** (`storage/`)
   - `MemoryStorage`：内存存储（测试用）
   - `SQLiteStorage`：本地 SQLite 存储（CLI 模式）
   - `RemoteStorage`：远程存储（HTTP 模式，调用 Backend API）
   - `SessionManager`：会话管理器，支持流式会话的恢复和取消

4. **Streaming** (`streaming/`)
   - `StreamingCore`：流式响应核心逻辑
   - `SSEEmitter`：SSE 事件发射器
   - `StreamingState`：流式会话状态管理

### 3.4 API 模块 (`api/`)

**职责**：HTTP API 接口层

**结构**：
- `api/v1/response.py`：`/v1/response` 端点，处理聊天请求
- `api/health.py`：健康检查端点
- `api/schemas.py`：API 请求/响应模型定义

**主要端点**：
- `POST /v1/response`：创建聊天会话，返回 SSE 流
- `GET /v1/response/{subtask_id}`：恢复聊天会话
- `DELETE /v1/response/{subtask_id}`：取消聊天会话

### 3.5 CLI 模块 (`cli/`)

**职责**：命令行工具接口

**命令**：
- `chat-shell serve`：启动 HTTP 服务器
- `chat-shell chat`：交互式聊天会话
- `chat-shell query "问题"`：单次查询
- `chat-shell history`：查看历史记录
- `chat-shell config`：配置管理

### 3.6 核心基础模块 (`core/`)

- `config.py`：配置管理（基于 Pydantic Settings）
- `database.py`：数据库连接管理
- `logging.py`：结构化日志配置（Structlog）
- `shutdown.py`：优雅关闭处理

### 3.7 辅助模块

- **Messages** (`messages/`)：消息格式转换，适配不同 LLM 提供商
- **Models** (`models/`)：LLM 模型工厂，统一创建不同提供商的模型实例
- **Compression** (`compression/`)：消息压缩策略和 Token 计数
- **Prompts** (`prompts/`)：提示词模板管理
- **History** (`history/`)：历史记录管理
- **Schemas** (`schemas/`)：数据结构定义
- **Tables** (`tables/`)：表格数据处理
- **DB Models** (`db_models/`)：数据库模型定义（SQLAlchemy）

## 4. 数据流

### 4.1 聊天请求处理流程

```
1. 接收请求
   ├─ HTTP API: POST /v1/response
   ├─ Package: create_chat_agent().chat(request)
   └─ CLI: chat-shell chat

2. ChatService 处理
   ├─ 创建 StreamingCore 和 SSEEmitter
   ├─ 通过 ChatContext 创建 ChatAgent
   └─ 初始化 StreamingState

3. ChatAgent 执行
   ├─ 加载历史消息（从 Storage）
   ├─ 构建提示词（系统提示 + 动态注入）
   ├─ 初始化工具（ToolRegistry）
   └─ 创建 LangGraph Agent（ReAct 工作流）

4. LangGraph 执行循环
   ├─ Model 思考 → AIMessage
   ├─ 决定工具调用 → ToolCall
   ├─ 执行工具 → ToolResult
   ├─ Model 综合结果 → AIMessage
   └─ 循环直到输出最终答案或达到迭代限制

5. 流式输出
   ├─ Token 级别流式输出（Chunk）
   ├─ 工具调用事件（ToolStart/ToolResult）
   ├─ 思考过程事件（Thinking）
   └─ 保存到 Storage（RemoteStorage → Backend）

6. 返回响应
   ├─ SSE 流式输出到客户端
   └─ 会话状态持久化
```

### 4.2 工具调用流程

```
1. Agent 决定调用工具
   ├─ Model 输出带有 tool_calls 的 AIMessage
   └─ LangGraph 自动提取工具调用

2. ToolRegistry 查找工具
   ├─ 根据 tool_name 查找注册的工具
   └─ 验证工具参数

3. 执行工具
   ├─ 调用工具的 _run() 或 _arun() 方法
   ├─ 工具可能触发子操作（如 API 调用、数据库查询）
   └─ 返回 ToolResult

4. 工具结果处理
   ├─ 包装为 ToolMessage
   ├─ 返回给 LangGraph
   └─ Model 继续推理

5. 特殊工具处理
   ├─ PromptModifierTool：动态修改提示词
   ├─ SilentExitTool：抛出 SilentExitException，静默退出
   └─ LoadSkillTool：动态加载新工具到 ToolRegistry
```

## 5. 技术栈

### 5.1 核心框架

- **Web 框架**：FastAPI + Uvicorn
- **AI 框架**：LangChain + LangGraph（ReAct Agent）
- **CLI 框架**：Click
- **异步运行时**：asyncio + aiohttp + httpx

### 5.2 LLM 集成

- **OpenAI**：`langchain-openai`
- **Anthropic Claude**：`langchain-anthropic`
- **Google Gemini**：`langchain-google-genai`
- **MCP 协议**：`langchain-mcp-adapters` + `mcp`

### 5.3 数据与存储

- **数据库 ORM**：SQLAlchemy 2.0 + asyncmy (MySQL) + aiosqlite (SQLite)
- **数据验证**：Pydantic 2.x
- **向量数据库**：Elasticsearch, Qdrant（通过 llama-index）
- **RAG**：llama-index-core, llama-index-embeddings-openai

### 5.4 文档处理

- **PDF**：pypdf2
- **Word**：python-docx
- **Excel**：openpyxl
- **Markdown**：markdown + beautifulsoup4
- **编码检测**：chardet
- **图片**：Pillow

### 5.5 开发与监控

- **配置管理**：python-dotenv + pydantic-settings
- **日志**：structlog
- **追踪**：OpenTelemetry（API + SDK + OTLP Exporter）
- **重试**：tenacity
- **测试**：pytest + pytest-asyncio + pytest-httpx + pytest-mock
- **代码质量**：black, isort, flake8, mypy

### 5.6 其他

- **JSON 处理**：orjson（高性能）
- **SSE**：sse-starlette
- **沙盒执行**：e2b + e2b-code-interpreter
- **HTTP 代理**：httpx[socks]
- **时间处理**：python-dateutil
- **YAML**：pyyaml

## 6. 关键设计决策

### 6.1 接口抽象

- **ChatInterface**：统一接口，支持 HTTP、Package、CLI 三种模式
- **StorageProvider**：存储抽象，支持 Memory、SQLite、Remote 三种后端
- **PromptModifierTool**：工具协议，允许工具动态修改提示词

### 6.2 流式响应

- **SSE 协议**：实时推送事件（Token、工具调用、思考过程）
- **会话恢复**：支持客户端断线重连，从指定 offset 继续
- **取消支持**：支持用户取消长时间运行的请求

### 6.3 工具扩展性

- **静态工具**：内置工具，编译时确定
- **动态技能**：运行时从后端加载
- **MCP 工具**：通过 MCP 协议连接外部工具服务器
- **PromptModifierTool**：工具可以动态注入提示词（如知识库检索结果）

### 6.4 上下文管理

- **自动压缩**：当上下文超过限制时，自动触发消息压缩
- **历史截断**：支持限制历史消息数量（history_limit）
- **知识注入**：检索到的知识通过 PromptModifierTool 注入到系统提示

### 6.5 可观测性

- **分布式追踪**：OpenTelemetry 集成，跟踪每次请求的完整链路
- **结构化日志**：Structlog 提供可搜索的 JSON 格式日志
- **健康检查**：`/health` 端点，支持 Kubernetes liveness/readiness probe

## 7. 配置说明

### 7.1 环境变量

```bash
# 运行模式
CHAT_SHELL_MODE=http              # http | package | cli

# 存储类型
CHAT_SHELL_STORAGE_TYPE=remote    # memory | sqlite | remote

# Remote Storage（HTTP 模式）
REMOTE_STORAGE_URL=http://backend:8000/api/internal
REMOTE_STORAGE_TOKEN=<token>

# SQLite Storage（CLI 模式）
SQLITE_DB_PATH=~/.chat_shell/history.db

# HTTP 服务器
HTTP_HOST=0.0.0.0
HTTP_PORT=8001

# LLM API Keys
ANTHROPIC_API_KEY=<key>
OPENAI_API_KEY=<key>
GOOGLE_API_KEY=<key>

# 默认模型配置
DEFAULT_MODEL=claude-3-5-sonnet-20241022
DEFAULT_TEMPERATURE=0.7
DEFAULT_MAX_TOKENS=4096

# 聊天配置
MAX_CONCURRENT_CHATS=50
CHAT_HISTORY_MAX_MESSAGES=50
```

### 7.2 项目结构

```
chat_shell/
├── __init__.py           # 包入口，导出主要接口
├── main.py               # FastAPI 应用入口
├── agent.py              # ChatAgent 核心实现
├── interface.py          # ChatInterface 抽象接口
├── agents/               # LangGraph Agent 构建器
├── api/                  # HTTP API 层
│   ├── v1/               # v1 版本 API
│   └── health.py         # 健康检查
├── cli/                  # 命令行工具
│   └── commands/         # CLI 命令实现
├── core/                 # 核心基础设施
├── services/             # 业务服务层
│   ├── chat_service.py   # 聊天服务
│   ├── context.py        # 上下文管理
│   ├── storage/          # 存储层
│   └── streaming/        # 流式响应
├── tools/                # 工具系统
│   ├── builtin/          # 内置工具
│   ├── mcp/              # MCP 工具
│   └── base.py           # 工具基类和注册表
├── models/               # LLM 模型工厂
├── messages/             # 消息转换
├── compression/          # 消息压缩
├── history/              # 历史管理
├── prompts/              # 提示词模板
├── schemas/              # 数据结构
├── storage/              # 存储实现
├── tables/               # 表格处理
└── db_models/            # 数据库模型
```

## 8. 总结

Chat Shell 是一个设计良好的模块化 AI Agent 服务，具有以下特点：

1. **灵活的部署模式**：支持 HTTP、Package、CLI 三种模式，适应不同场景
2. **可扩展的工具系统**：内置工具 + 动态技能 + MCP 协议，满足多样化需求
3. **强大的流式能力**：SSE 实时推送 + 会话恢复 + 取消支持
4. **完善的可观测性**：OpenTelemetry + Structlog，便于问题排查
5. **清晰的分层架构**：API → Service → Agent → Tools，职责明确
6. **生产就绪**：配置管理、错误处理、资源清理、优雅关闭

该架构为构建企业级 AI Agent 应用提供了坚实的基础，同时保持了良好的可扩展性和可维护性。
