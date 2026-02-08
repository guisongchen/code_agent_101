# Wegent Backend Web UI

A web-based interface for managing CRD resources (Ghost, Model, Shell, Bot, Team, Skill) in the Wegent Backend.

## Features

- **Dashboard** - Overview of all resources with quick navigation
- **Authentication** - JWT-based login/logout
- **Resource Management** - Create, list, and delete CRD resources:
  - **Ghosts** - System prompts and AI personalities
  - **Models** - AI model configurations (OpenAI, Anthropic, Google)
  - **Shells** - Runtime environments (Chat, Task, Agent)
  - **Bots** - AI agents combining Ghost + Model + Shell
  - **Teams** - Multi-bot teams for collaborative workflows
  - **Skills** - Reusable capabilities and tools

## Quick Start

### 1. Start the Backend Server

```bash
# From the project root
uv run python -m backend.main
```

The server will start on `http://localhost:8000`

### 2. Access the Web UI

Open your browser and navigate to:

```
http://localhost:8000/ui
```

### 3. Login

You'll need to register a user first via the API:

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "yourpassword"
  }'
```

Then login through the web UI with your credentials.

## File Structure

```
frontend/
├── index.html          # Dashboard
├── login.html          # Login page
├── css/
│   └── styles.css      # Main stylesheet
├── js/
│   ├── auth.js         # JWT authentication utilities
│   ├── api.js          # API client functions
│   └── app.js          # Main application utilities
└── pages/
    ├── ghosts.html     # Ghost management
    ├── models.html     # Model management
    ├── shells.html     # Shell management
    ├── bots.html       # Bot management
    ├── teams.html      # Team management
    └── skills.html     # Skill management
```

## Usage Guide

### Creating Resources

1. **Create a Ghost** (AI Personality)
   - Go to Ghosts page
   - Click "Create Ghost"
   - Enter name, description, and system prompt
   - Save

2. **Create a Model** (AI Configuration)
   - Go to Models page
   - Click "Create Model"
   - Select provider (OpenAI, Anthropic, Google)
   - Enter model name and parameters
   - Save

3. **Create a Shell** (Runtime Environment)
   - Go to Shells page
   - Click "Create Shell"
   - Select type (Chat, Task, Agent)
   - Save

4. **Create a Bot** (Combine resources)
   - Go to Bots page
   - Click "Create Bot"
   - Select Ghost, Model, and Shell references
   - Save

### Namespace Support

All resources are organized by namespace. The default namespace is `default`. To use a different namespace, modify the URL:

```
http://localhost:8000/ui/pages/ghosts.html?namespace=mynamespace
```

## API Integration

The UI communicates with the Backend API at `/api/v1`. Authentication uses JWT tokens stored in localStorage.

### API Endpoints Used

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/login` | POST | User authentication |
| `/api/v1/auth/me` | GET | Get current user |
| `/api/v1/kinds/ghosts` | GET/POST | Ghost CRUD |
| `/api/v1/kinds/models` | GET/POST | Model CRUD |
| `/api/v1/kinds/shells` | GET/POST | Shell CRUD |
| `/api/v1/kinds/bots` | GET/POST | Bot CRUD |
| `/api/v1/kinds/teams` | GET/POST | Team CRUD |
| `/api/v1/kinds/skills` | GET/POST | Skill CRUD |

## Development

### Technology Stack

- **HTML5** - Semantic markup
- **Vanilla JavaScript** - No frameworks
- **CSS3** - Custom styling with CSS variables
- **FastAPI StaticFiles** - Static file serving

### Adding New Features

1. Add new page in `frontend/pages/`
2. Update navigation in `index.html` and all page sidebars
3. Add API functions in `js/api.js`
4. Add styles in `css/styles.css` if needed

## Troubleshooting

### UI not loading

- Verify the backend server is running
- Check browser console for errors
- Ensure you're accessing `http://localhost:8000/ui`

### Authentication issues

- Clear browser localStorage and try again
- Verify user exists via API
- Check JWT token expiration

### API errors

- Check backend logs
- Verify database is initialized
- Ensure all migrations are applied

## Next Steps

This UI provides basic CRUD operations for Phase 1 verification. Future enhancements (Phase 2) will include:

- Real-time chat interface via WebSocket
- Task management and execution
- Message history viewer
- Session management
- Streaming message display
