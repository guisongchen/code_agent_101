# Wegent Frontend - User Tutorial (Simplified)

A step-by-step guide to using the simplified Wegent frontend for personal AI agent management.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Dashboard Overview](#dashboard-overview)
3. [Managing Agents](#managing-agents)
4. [Managing Teams](#managing-teams)
5. [Task Management](#task-management)
6. [Chat Interface](#chat-interface)
7. [Error Handling](#error-handling)
8. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites

- Backend API running on `http://localhost:8000`
- Frontend running on `http://localhost:3000`
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Starting the Application

1. **Start the Backend:**
   ```bash
   cd /home/ccc/vibe_projects/code_agent_101
   source .venv/bin/activate
   python -m backend.main
   ```

2. **Start the Frontend:**
   ```bash
   cd /home/ccc/vibe_projects/code_agent_101/frontend
   npm run dev
   ```

3. **Open Browser:**
   Navigate to `http://localhost:3000`

**Note:** This is a simplified personal-use version. No login required - you start directly on the dashboard!

---

## Dashboard Overview

The dashboard is your central hub for managing AI agents and tasks.

### Statistics Cards

At the top of the dashboard, you'll see cards showing:
- **Agents** - Number of configured AI agents
- **Tasks** - Number of created tasks

### Quick Actions

The dashboard provides quick action buttons:
- **New Agent** - Create a new AI agent
- **New Task** - Create a new task
- **Open Chat** - Navigate to the chat interface

### Recent Tasks

The **Recent Tasks** section shows:
- Latest tasks created
- Current execution status (pending, running, completed, failed)
- Quick links to open task chat

### Navigation Sidebar

The left sidebar provides access to all sections:
- Dashboard (home icon)
- Agents
- Tasks
- Chat
- Teams

---

## Managing Agents

Agents are AI configurations that combine model settings, system prompts, and tool capabilities.

### Creating an Agent

1. Navigate to **Agents** in the sidebar
2. Click **"New Agent"** button
3. Fill in the form:
   - **Name**: Unique identifier (e.g., `my-assistant`)
   - **Description**: Optional description
   - **Provider**: Select from OpenAI, Anthropic, Google, Ollama
   - **Model**: Model name (e.g., `gpt-4`, `claude-3-opus`)
   - **API Key**: Optional - uses default if not set
   - **System Prompt**: Instructions for the AI (e.g., "You are a helpful assistant")
   - **Temperature**: Creativity level (0-2, default 0.7)
   - **Auto Tools**: Enable automatic tool invocation
   - **Max Iterations**: Maximum tool call iterations
4. Click **"OK"** to create

### Editing an Agent

1. Find the agent in the list
2. Click the **Edit** button (pencil icon)
3. Modify the fields
4. Click **"OK"** to save

### Deleting an Agent

1. Find the agent in the list
2. Click the **Delete** button (trash icon)
3. Confirm the deletion

**Note:** Deleting an agent does not delete associated tasks.

---

## Managing Teams

Teams group multiple agents for collaborative tasks.

### Creating a Team

1. Navigate to **Teams** in the sidebar
2. Click **"New Team"** button
3. Fill in the form:
   - **Name**: Unique identifier (e.g., `dev-team`)
   - **Description**: Optional description
   - **Agents**: Select multiple agents from the dropdown
4. Click **"OK"** to create

### Editing a Team

1. Find the team in the list
2. Click the **Edit** button (pencil icon)
3. Modify the team members or details
4. Click **"OK"** to save

### Deleting a Team

1. Find the team in the list
2. Click the **Delete** button (trash icon)
3. Confirm the deletion

---

## Task Management

Tasks represent units of work executed by Agents.

### Creating a Task

1. Navigate to **Tasks** in the sidebar
2. Click **"New Task"** button
3. Fill in the form:
   - **Name**: Unique task identifier
   - **Description**: Optional description
   - **Agent**: Select which agent executes the task
   - **Initial Input**: Optional starting message for the agent
4. Click **"OK"** to create

### Task Lifecycle

Tasks progress through these states:
- **Pending** - Waiting to start
- **Running** - Currently executing
- **Completed** - Finished successfully
- **Failed** - Encountered an error
- **Cancelled** - Stopped by user

### Monitoring Tasks

The Tasks page shows:
- **Status badges** - Color-coded status (green=completed, blue=running, red=failed)
- **Agent** - Which agent is handling the task
- **Input** - Initial task instruction
- **Created time** - When the task was created

### Opening Task Chat

1. Find the task in the list
2. Click the **"Open"** button
3. You'll be taken to the chat interface for that task

### Deleting Tasks

1. Find the task in the list
2. Click the **Delete** button (trash icon)
3. Confirm the deletion

---

## Chat Interface

The Chat interface provides communication with AI agents during task execution.

### Opening Chat

1. Navigate to **Chat** in the sidebar
2. Select a **Task** from the dropdown
3. The chat history loads automatically

**Alternative:** Click "Open" on a task from the Tasks page.

### Sending Messages

1. Type your message in the input box at the bottom
2. Press **Enter** (or Shift+Enter for new line)
3. Message appears in the chat history
4. AI response appears after processing

### Chat Features

- **Message History** - Scroll to see previous messages
- **Role Indicators** - User messages (blue) vs Assistant messages (gray)
- **Auto-scroll** - Automatically scrolls to latest message
- **Task Status** - Shows current task status in the header

### Switching Tasks

1. Use the **Task Selector** dropdown at the top
2. Select a different task
3. Chat history updates to show the new task's conversation

### How It Works

The chat uses HTTP polling (not WebSocket):
- Messages are fetched every 2 seconds
- No persistent connection to maintain
- Simpler and more reliable for personal use

---

## Error Handling

The application provides simple error handling.

### Toast Notifications

Various operations show toast notifications:
- **Success** (green) - Operations completed successfully
- **Error** (red) - Something went wrong

### Common Errors

**Failed to load agents/tasks:**
- Check that the backend is running
- Refresh the page

**Failed to save:**
- Check that all required fields are filled
- Check browser console for details

**Message failed to send:**
- Ensure a task is selected
- Check that the backend is accessible

---

## Troubleshooting

### Page Not Loading

**Problem:** Blank page or error on load

**Solutions:**
1. Check that backend is running on port 8000
2. Check browser console for errors
3. Refresh the page

### Cannot Create Agent/Task

**Problem:** Form submission fails

**Solutions:**
1. Check that all required fields are filled
2. Ensure name is unique
3. Check browser console for API errors

### Chat Not Updating

**Problem:** Messages not appearing or not sending

**Solutions:**
1. Ensure a task is selected
2. Check that the task exists
3. Refresh the page
4. Check backend logs

### API Errors

**Problem:** Operations fail with error messages

**Solutions:**
1. Verify backend API is accessible at `http://localhost:8000`
2. Check network connection
3. Check browser console for error details
4. Restart backend if needed

---

## Tips & Best Practices

1. **Start Simple** - Create a basic agent before complex configurations
2. **Use Descriptive Names** - Makes it easier to identify agents/tasks later
3. **Monitor Tasks** - Check task status to ensure agents are responding
4. **Save API Keys** - Set API keys on agents for different providers
5. **Use Teams** - Group related agents for multi-step workflows
6. **Check Console** - Browser console shows detailed error information

---

## Differences from Full Version

This simplified version differs from the enterprise version:

| Feature | Simplified | Enterprise |
|---------|------------|------------|
| Authentication | None | JWT-based login |
| Namespaces | None (implicit default) | Multi-tenant |
| Resource Types | 3 (Agent, Team, Task) | 6 (Ghost, Model, Shell, Bot, Team, Skill) |
| Chat | HTTP polling | WebSocket |
| Error Handling | Simple try/catch | Error boundaries, retry logic |
| CRUD | Inline per page | Generic reusable components |

---

## Support

For issues or questions:
1. Check this troubleshooting guide
2. Review backend logs for API errors
3. Check browser console for frontend errors
4. Refer to the ADR documentation in `doc/adr/`

---

**Happy AI Agent Building! 🤖**
