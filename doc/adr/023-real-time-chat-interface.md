# ADR 023: Real-time Chat Interface

## Status

Accepted

## Context

Epic 23 required implementing a WebSocket-based chat interface for real-time task communication. The backend already provided a WebSocket chat endpoint (Epic 14) with support for:

- Bidirectional messaging between client and AI assistant
- Streaming AI responses (chunked content delivery)
- Tool call execution with real-time results
- Message history synchronization
- Session management and recovery
- Chat cancellation during generation

The frontend needed to:
1. Establish and maintain WebSocket connections
2. Handle streaming message content in real-time
3. Display different message types (user, assistant, system, tool)
4. Support tool call visualization
5. Provide chat cancellation functionality
6. Allow switching between task-based chat rooms
7. Synchronize message history on connection

The challenge was designing a robust WebSocket client architecture that handles connection lifecycle, message streaming, and UI state synchronization.

## Decision

### 1. Native WebSocket API with Custom Hook

**Decision:** Use the browser's native WebSocket API wrapped in a custom `useChat` hook rather than a third-party library like Socket.IO.

**Rationale:**
- Backend uses standard WebSocket protocol (not Socket.IO)
- Native WebSocket provides full control over connection lifecycle
- No additional dependencies required
- Easier to debug and understand connection issues

**Hook Design:**

```typescript
export function useChat({ taskId, token, onError }: UseChatOptions): UseChatReturn {
  const [messages, setMessages] = useState<MessageResponse[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    const url = `${wsUrl}/api/v1/tasks/${taskId}/chat?token=${token || ""}`;
    const ws = new WebSocket(url);

    ws.onopen = () => setIsConnected(true);
    ws.onmessage = (event) => handleWebSocketMessage(JSON.parse(event.data));
    ws.onclose = () => setIsConnected(false);
    ws.onerror = (error) => onError?.("Connection error");

    wsRef.current = ws;
  }, [taskId, token]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);
}
```

**Location:** `frontend/src/hooks/useChat.ts`

### 2. Optimistic Message Updates

**Decision:** Implement optimistic UI updates for user messages, adding them to the message list immediately before server confirmation.

**Rationale:**
- Provides immediate visual feedback to users
- Creates the appearance of a responsive, real-time interface
- Matches user expectations from modern chat applications

**Implementation:**

```typescript
const sendMessage = useCallback((content: string) => {
  // Add user message optimistically
  const userMessage: MessageResponse = {
    id: generateTempId(),
    taskId,
    role: "user",
    messageType: "text",
    content,
    threadId: taskId,
    sequence: messages.length + 1,
    meta: {},
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };
  setMessages((prev) => [...prev, userMessage]);

  // Send to server
  wsRef.current?.send(JSON.stringify({ type: "chat:send", content }));
}, [taskId, messages.length]);
```

### 3. Streaming Content Accumulation

**Decision:** Accumulate streaming content chunks in a ref and update the message list incrementally for assistant responses.

**Rationale:**
- WebSocket sends content as incremental chunks (chat:chunk events)
- Accumulating in a ref prevents unnecessary re-renders
- Updates are batched to the message list for display

**Implementation:**

```typescript
const currentAssistantMessageRef = useRef<Partial<MessageResponse> | null>(null);

const handleWebSocketMessage = useCallback((data: ChatMessageEvent) => {
  switch (data.type) {
    case "chat:start":
      setIsStreaming(true);
      currentAssistantMessageRef.current = {
        id: generateTempId(),
        role: "assistant",
        content: "",
        // ...
      };
      break;

    case "chat:chunk":
      if (currentAssistantMessageRef.current) {
        currentAssistantMessageRef.current.content += data.content || "";
        // Update messages with new content
        setMessages((prev) => {
          const lastMessage = prev[prev.length - 1];
          if (lastMessage?.role === "assistant") {
            return [...prev.slice(0, -1), { ...lastMessage, content: currentAssistantMessageRef.current?.content }];
          }
          return [...prev, currentAssistantMessageRef.current as MessageResponse];
        });
      }
      break;

    case "chat:done":
      setIsStreaming(false);
      currentAssistantMessageRef.current = null;
      break;
  }
}, []);
```

### 4. Role-Based Message Styling

**Decision:** Create a role configuration object that defines styling (colors, icons, alignment) for each message role.

**Rationale:**
- Centralizes role-specific styling logic
- Makes it easy to add new roles or modify existing ones
- Ensures consistent presentation across the application

**Configuration:**

```typescript
const roleConfig = {
  user: {
    icon: <UserOutlined />,
    color: "#1890ff",
    bgColor: "#e6f7ff",
    label: "You",
    align: "right" as const,
  },
  assistant: {
    icon: <RobotOutlined />,
    color: "#52c41a",
    bgColor: "#f6ffed",
    label: "Assistant",
    align: "left" as const,
  },
  tool: {
    icon: <ToolOutlined />,
    color: "#722ed1",
    bgColor: "#f9f0ff",
    label: "Tool",
    align: "left" as const,
  },
  system: {
    icon: <InfoCircleOutlined />,
    color: "#faad14",
    bgColor: "#fffbe6",
    label: "System",
    align: "left" as const,
  },
};
```

**Location:** `frontend/src/components/chat/ChatMessage.tsx`

### 5. Tool Call and Result Display

**Decision:** Render tool calls and results as special message types with collapsible JSON content.

**Rationale:**
- Tool calls are distinct from regular chat messages
- JSON content needs special formatting for readability
- Collapsible view prevents cluttering the chat history

**Implementation:**

```typescript
if (isToolCall) {
  return (
    <Card size="small" style={{ background: config.bgColor }}>
      <Space>
        <Avatar icon={config.icon} style={{ backgroundColor: config.color }} />
        <Tag color={config.color}>{config.label}</Tag>
        <Text strong>{message.toolName || "Tool"}</Text>
      </Space>
      <pre style={{ background: "rgba(0,0,0,0.05)", padding: 8 }}>
        {JSON.stringify(message.meta, null, 2)}
      </pre>
    </Card>
  );
}
```

### 6. Task-Based Chat Rooms

**Decision:** Implement chat as a task-scoped feature where users select a task to chat with its associated AI assistant.

**Rationale:**
- Tasks already have bot configurations and execution context
- WebSocket endpoint is scoped to `/tasks/{task_id}/chat`
- Allows multiple concurrent chat sessions for different tasks

**Implementation:**

```typescript
export default function ChatPage() {
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const { tasks } = useTasks();

  return (
    <Row gutter={[16, 16]}>
      <Col span={24}>
        <Select
          placeholder="Select a task to chat with"
          value={selectedTaskId || undefined}
          onChange={setSelectedTaskId}
        >
          {tasks.map((task) => (
            <Option key={task.id} value={task.id}>
              {task.name} ({task.status}) - {task.namespace}
            </Option>
          ))}
        </Select>
      </Col>
      <Col span={24}>
        {selectedTaskId ? (
          <ChatContainer taskId={selectedTaskId} />
        ) : (
          <Empty description="Select a task to start chatting" />
        )}
      </Col>
    </Row>
  );
}
```

**Location:** `frontend/src/app/(dashboard)/chat/page.tsx`

### 7. Auto-Scroll with User Override

**Decision:** Implement auto-scroll to the latest message, but disable it when the user scrolls up to read history.

**Rationale:**
- Users expect to see new messages automatically
- Users need to be able to read history without fighting auto-scroll
- Detecting scroll position provides the best of both behaviors

**Implementation:**

```typescript
const [autoScroll, setAutoScroll] = useState(true);
const messagesEndRef = useRef<HTMLDivElement>(null);

// Auto-scroll to bottom when new messages arrive
useEffect(() => {
  if (autoScroll && messagesEndRef.current) {
    messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
  }
}, [messages, autoScroll]);

// Handle scroll to detect if user scrolled up
const handleScroll = () => {
  if (messagesContainerRef.current) {
    const { scrollTop, scrollHeight, clientHeight } = messagesContainerRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;
    setAutoScroll(isAtBottom);
  }
};
```

## Consequences

### Positive

- **Real-time Experience**: WebSocket provides true bidirectional communication with minimal latency
- **Streaming Display**: Users see AI responses as they're generated, improving perceived performance
- **Tool Visibility**: Users can see when and how tools are being used by the AI
- **Multi-task Support**: Task-based chat rooms allow concurrent conversations
- **Optimistic UI**: Immediate feedback makes the interface feel responsive
- **No Extra Dependencies**: Native WebSocket keeps bundle size small

### Negative

- **Connection Complexity**: Managing WebSocket lifecycle (connect, reconnect, errors) adds complexity
- **No Built-in Reconnection**: Native WebSocket doesn't auto-reconnect; must implement manually
- **Browser Compatibility**: WebSocket is widely supported but requires fallback consideration
- **State Synchronization**: Keeping React state in sync with WebSocket events requires careful handling
- **Memory Management**: Refs for streaming content must be cleaned up to prevent leaks

## Alternatives Considered

### Alternative 1: Server-Sent Events (SSE)

Use SSE for server-to-client streaming and HTTP POST for client-to-server messages.

**Rejected:**
- SSE is unidirectional; would still need separate mechanism for sending messages
- WebSocket provides cleaner bidirectional abstraction
- SSE has limitations with HTTP/2 and proxy configurations

### Alternative 2: Socket.IO Client

Use Socket.IO client library for WebSocket communication.

**Rejected:**
- Backend uses native WebSocket, not Socket.IO
- Adds unnecessary dependency (~30KB gzipped)
- Socket.IO features (rooms, namespaces) not needed for this use case

### Alternative 3: Long Polling

Use HTTP long polling for real-time updates.

**Rejected:**
- Higher latency than WebSocket
- More server resource intensive
- Doesn't support true streaming
- Legacy technique not suitable for modern real-time chat

### Alternative 4: GraphQL Subscriptions

Use GraphQL subscriptions for real-time data.

**Rejected:**
- Backend doesn't use GraphQL
- Would require significant backend changes
- Overkill for simple chat messaging

## Implementation Notes

### Dependencies

No new dependencies required. Uses:
- Native browser WebSocket API
- React hooks (useState, useEffect, useRef, useCallback)
- Ant Design components (Card, Avatar, Tag, Input, Empty)

### WebSocket Event Types

**Client -> Server:**
- `chat:send` - Send a message
- `chat:cancel` - Cancel ongoing generation
- `history:request` - Request message history
- `session:recover` - Recover a previous session
- `ping` - Keep-alive ping

**Server -> Client:**
- `chat:start` - AI started generating
- `chat:chunk` - Streaming content chunk
- `chat:done` - AI response completed
- `chat:error` - Error occurred
- `chat:cancelled` - Stream was cancelled
- `chat:tool_start` - Tool execution started
- `chat:tool_result` - Tool execution completed
- `chat:thinking` - Agent thinking process
- `history:sync` - Message history response

### Testing Strategy

```bash
# Run chat interface tests
cd frontend && npm test -- ../tests/frontend/chat.test.ts

# All 44 tests passing:
# - useChat hook: 10 tests
# - ChatMessage component: 9 tests
# - ChatInput component: 6 tests
# - ChatContainer component: 8 tests
# - Chat page: 5 tests
# - Chat navigation: 2 tests
# - Chat components index: 4 tests
```

### Key Files

| File | Purpose |
|------|---------|
| `frontend/src/hooks/useChat.ts` | WebSocket connection and message handling |
| `frontend/src/components/chat/ChatMessage.tsx` | Message display with role-based styling |
| `frontend/src/components/chat/ChatInput.tsx` | Message input with send/cancel |
| `frontend/src/components/chat/ChatContainer.tsx` | Main chat interface container |
| `frontend/src/components/chat/index.ts` | Component exports |
| `frontend/src/app/(dashboard)/chat/page.tsx` | Chat page with task selector |
| `tests/frontend/chat.test.ts` | 44 chat interface tests |

## References

- Epic 14: WebSocket Chat Endpoint (`doc/adr/014-websocket-chat-endpoint.md`)
- Epic 15: Message History Management (`doc/adr/015-message-history-management.md`)
- Epic 16: Chat Session State Management (`doc/adr/016-chat-session-state-management.md`)
- MDN WebSocket API: https://developer.mozilla.org/en-US/docs/Web/API/WebSocket
