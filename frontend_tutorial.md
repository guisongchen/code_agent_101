# Wegent Frontend MVP - User Tutorial

A step-by-step guide to using the Wegent platform frontend for managing AI agents, tasks, and real-time chat.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Authentication](#authentication)
3. [Dashboard Overview](#dashboard-overview)
4. [Managing CRD Resources](#managing-crd-resources)
   - [Ghosts](#ghosts)
   - [Models](#models)
   - [Shells](#shells)
   - [Bots](#bots)
   - [Teams](#teams)
   - [Skills](#skills)
5. [Task Management](#task-management)
6. [Real-time Chat](#real-time-chat)
7. [Error Handling & Feedback](#error-handling--feedback)
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

---

## Authentication

### Registering a New Account

1. Click **"Register"** on the login page
2. Fill in the registration form:
   - **Username**: 3-32 characters, alphanumeric
   - **Email**: Valid email address
   - **Password**: Minimum 8 characters with uppercase, lowercase, and number
   - **Confirm Password**: Must match password
3. Click **"Register"** button
4. You'll be automatically logged in and redirected to the dashboard

### Logging In

1. Enter your **username** and **password**
2. Click **"Login"**
3. On successful login, you'll be redirected to the dashboard

### Logging Out

1. Click your **username** in the top-right corner of the header
2. Select **"Logout"** from the dropdown menu
3. You'll be redirected to the login page

### Session Management

- Your session is maintained via JWT token stored securely
- Token automatically refreshes to maintain your session
- If your session expires, you'll be redirected to login

---

## Dashboard Overview

The dashboard is your central hub for monitoring the platform.

### Resource Statistics Cards

At the top of the dashboard, you'll see cards showing counts of:
- **Ghosts** - AI agent configurations
- **Models** - LLM model definitions
- **Shells** - Execution environments
- **Bots** - Complete AI agent instances
- **Teams** - Multi-agent teams
- **Skills** - Reusable agent capabilities

### Quick Actions

The dashboard provides quick action buttons:
- **Create Task** - Jump directly to task creation
- **Open Chat** - Navigate to the chat interface

### Recent Activity

The **Recent Tasks** section shows:
- Latest tasks created
- Current execution status
- Quick links to task details

### Navigation Sidebar

The left sidebar provides access to all sections:
- Dashboard (home icon)
- Tasks
- Chat
- Ghosts
- Models
- Shells
- Bots
- Teams
- Skills

---

## Managing CRD Resources

All CRD resources follow the same management pattern:
1. **List View** - See all resources in a table
2. **Create** - Add new resources via form
3. **Edit** - Modify existing resources
4. **Delete** - Remove resources with confirmation

### Resource List Features

Each resource page includes:
- **Search** - Filter by name or description
- **Namespace Filter** - Isolate resources by namespace
- **Pagination** - Navigate large resource sets
- **Actions** - Edit and delete buttons per row

### Common Form Fields

Most resources have these standard fields:
- **Name** - Unique identifier (Kubernetes DNS name format)
- **Namespace** - Resource isolation group
- **Labels** - Key-value metadata tags
- **Spec** - YAML configuration (with syntax highlighting)

---

### Ghosts

Ghosts define AI agent personalities and behaviors.

**Creating a Ghost:**
1. Navigate to **Ghosts** in the sidebar
2. Click **"Create Ghost"** button
3. Fill in the form:
   - **Name**: `my-assistant`
   - **Namespace**: `default`
   - **Spec YAML**:
     ```yaml
     system_prompt: "You are a helpful AI assistant."
     temperature: 0.7
     max_tokens: 2048
     ```
4. Click **"Submit"**

**Use Case:** Define different personalities for different tasks (e.g., coding assistant, creative writer, data analyst).

---

### Models

Models define LLM configurations and API connections.

**Creating a Model:**
1. Navigate to **Models**
2. Click **"Create Model"**
3. Configure:
   - **Name**: `gpt-4-config`
   - **Provider**: `openai`, `anthropic`, etc.
   - **Model ID**: `gpt-4`
   - **API Configuration**: Endpoint and credentials
4. Click **"Submit"**

**Use Case:** Switch between different LLM providers or model versions.

---

### Shells

Shells define execution environments for running code or commands.

**Creating a Shell:**
1. Navigate to **Shells**
2. Click **"Create Shell"**
3. Configure:
   - **Name**: `python-env`
   - **Image**: `python:3.11`
   - **Resources**: CPU/memory limits
   - **Environment Variables**: Key-value pairs
4. Click **"Submit"**

**Use Case:** Provide isolated environments for code execution.

---

### Bots

Bots combine Ghosts, Models, and Shells into complete AI agents.

**Creating a Bot:**
1. Navigate to **Bots**
2. Click **"Create Bot"**
3. Configure:
   - **Name**: `coding-assistant`
   - **Ghost**: Select from dropdown (creates personality)
   - **Model**: Select LLM configuration
   - **Shell**: Select execution environment (optional)
4. Click **"Submit"**

**Validation:** The system validates that referenced Ghosts, Models, and Shells exist.

**Use Case:** Create deployable AI agents with specific capabilities.

---

### Teams

Teams group multiple Bots for collaborative tasks.

**Creating a Team:**
1. Navigate to **Teams**
2. Click **"Create Team"**
3. Configure:
   - **Name**: `dev-team`
   - **Members**: Add bots by selecting from dropdown
   - **Coordinator**: Choose which bot leads the team
4. Click **"Submit"**

**Validation:** All bot references are validated at creation time.

**Use Case:** Create multi-agent workflows where different bots handle different aspects of a task.

---

### Skills

Skills define reusable capabilities that can be attached to Bots.

**Creating a Skill:**
1. Navigate to **Skills**
2. Click **"Create Skill"**
3. Configure:
   - **Name**: `web-search`
   - **Description**: What the skill does
   - **Parameters**: Input schema
   - **Implementation**: Code or configuration
4. Click **"Submit"**

**Use Case:** Build a library of reusable capabilities (web search, database queries, API calls).

---

## Task Management

Tasks represent units of work executed by Bots or Teams.

### Creating a Task

1. Navigate to **Tasks** in the sidebar
2. Click **"Create Task"** button
3. Fill in the task form:
   - **Name**: Unique task identifier
   - **Team**: Select which bot/team executes the task
   - **Instruction**: What the bot should do
   - **Context**: Additional background information
4. Click **"Submit"**

### Task Lifecycle

Tasks progress through these states:
- **Pending** - Waiting to start
- **Running** - Currently executing
- **Completed** - Finished successfully
- **Failed** - Encountered an error
- **Cancelled** - Stopped by user

### Monitoring Tasks

The Tasks page shows:
- **Status indicators** - Color-coded status (green=completed, blue=running, red=failed)
- **Progress** - Real-time updates during execution
- **Created/Updated times** - Track task history

### Task Details

Click on a task name to view:
- **Full task configuration**
- **Execution logs** - Output from the bot
- **Chat history** - Conversation with the AI
- **Cancel button** - Stop running tasks

### Cancelling Tasks

1. Find the running task in the list
2. Click the **"Cancel"** button
3. Confirm the cancellation
4. Task status changes to **Cancelled**

---

## Real-time Chat

The Chat interface provides real-time communication with AI agents during task execution.

### Opening Chat

1. Navigate to **Chat** in the sidebar
2. Select a **Task** from the dropdown (only running/completed tasks appear)
3. The chat history loads automatically

### Sending Messages

1. Type your message in the input box at the bottom
2. Press **Enter** or click the **Send** button
3. Message appears in the chat history
4. AI response streams in real-time

### Chat Features

- **Message History** - Scroll to see previous messages
- **Role Indicators** - Messages show who sent them (User, Assistant, System)
- **Streaming Display** - Watch AI responses appear character by character
- **Tool Calls** - See when the AI uses tools (highlighted specially)
- **Timestamps** - Each message shows when it was sent

### Chat Cancellation

During AI response generation:
1. Click the **"Stop"** button (appears while AI is responding)
2. Generation stops immediately
3. Partial response is preserved

### Switching Tasks

1. Use the **Task Selector** dropdown at the top
2. Select a different task
3. Chat history updates to show the new task's conversation

### WebSocket Connection

The chat uses WebSocket for real-time communication:
- **Connection Status** - Green dot indicates connected
- **Auto-reconnect** - Automatically reconnects if connection drops
- **Session Recovery** - Restores chat state on reconnection

---

## Error Handling & Feedback

The application provides comprehensive error handling and user feedback.

### Error Boundaries

If a component crashes:
- The error is caught gracefully
- A user-friendly error page displays
- Options to **Try Again**, **Go Home**, or **Reload Page**
- Error details shown for debugging

### Toast Notifications

Various operations show toast notifications:
- **Success** (green) - Operations completed successfully
- **Error** (red) - Something went wrong
- **Warning** (orange) - Attention needed
- **Info** (blue) - General information

### Loading States

While data loads:
- **Skeleton screens** show placeholder content
- **Spinners** indicate loading on buttons
- **Progress indicators** show long-running operations

### Form Validation

Forms validate input in real-time:
- **Required fields** - Highlighted if empty
- **Format validation** - Email, URL, Kubernetes names
- **Error messages** - Clear descriptions of what's wrong
- **Password requirements** - Strength indicators

### Network Status

The application detects online/offline status:
- **Offline warning** - Appears when connection is lost
- **Auto-retry** - Attempts to reconnect automatically
- **Retry button** - Manual reconnection option
- **Restored notification** - Confirms when back online

### Confirmation Dialogs

Destructive actions require confirmation:
- **Delete operations** - "Are you sure?" with item name
- **Unsaved changes** - Warns before leaving forms
- **Dangerous actions** - Extra confirmation for critical operations

---

## Troubleshooting

### Cannot Log In

**Problem:** Login fails with error message

**Solutions:**
1. Check username and password are correct
2. Ensure backend is running on port 8000
3. Check browser console for API errors
4. Clear browser cache and try again

### Resources Not Loading

**Problem:** Resource list shows empty or error

**Solutions:**
1. Verify backend API is accessible
2. Check network connection
3. Refresh the page
4. Check browser console for errors

### Chat Not Connecting

**Problem:** Chat shows "Disconnected" or messages not sending

**Solutions:**
1. Check WebSocket connection in browser dev tools
2. Ensure backend WebSocket endpoint is running
3. Refresh the page to reconnect
4. Check if task is still running

### Form Validation Errors

**Problem:** Cannot submit form due to validation errors

**Solutions:**
1. Check all required fields are filled
2. Ensure names follow Kubernetes naming (lowercase, alphanumeric, hyphens)
3. Verify YAML syntax in spec fields
4. Check reference fields point to existing resources

### Task Not Starting

**Problem:** Task stays in "Pending" state

**Solutions:**
1. Check task queue is running on backend
2. Verify the selected Bot/Team exists and is valid
3. Check backend logs for errors
4. Try creating a new task

### 404 Not Found

**Problem:** Page shows "404 - Page Not Found"

**Solutions:**
1. Check URL is correct
2. Navigate using sidebar menu
3. Resource may have been deleted
4. Go back to Dashboard and try again

### Session Expired

**Problem:** Redirected to login with "Session expired" message

**Solutions:**
1. Log in again
2. Your session automatically renews with activity
3. Long periods of inactivity cause expiration

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + Enter` | Submit form (when in form) |
| `Enter` | Send chat message (when in chat input) |
| `Esc` | Close modal/dialog |
| `Ctrl + /` | Focus search box |

---

## Tips & Best Practices

1. **Use Namespaces** - Organize resources by project or team
2. **Label Resources** - Add metadata for easier filtering
3. **Start Small** - Create simple bots before complex teams
4. **Monitor Tasks** - Watch task logs for debugging
5. **Save Often** - Forms don't auto-save
6. **Use Chat** - Real-time chat helps debug task issues
7. **Check Validation** - Fix form errors before submitting
8. **Stay Online** - Network issues can interrupt operations

---

## Support

For issues or questions:
1. Check this troubleshooting guide
2. Review backend logs for API errors
3. Check browser console for frontend errors
4. Refer to the ADR documentation in `doc/adr/`

---

**Happy AI Agent Building! 🤖**
