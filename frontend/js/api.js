// API client for Backend CRD operations

const API_BASE = '/api/v1';

// Helper for authenticated requests
async function apiRequest(url, options = {}) {
    const token = getToken();
    if (!token) {
        throw new Error('Not authenticated');
    }

    const response = await fetch(url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
            ...options.headers
        }
    });

    if (response.status === 401) {
        clearToken();
        window.location.href = '/ui/login.html';
        throw new Error('Session expired');
    }

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(error.detail || `HTTP ${response.status}`);
    }

    if (response.status === 204) {
        return null;
    }

    return response.json();
}

// Authentication
async function login(username, password) {
    const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Login failed' }));
        throw new Error(error.detail || 'Login failed');
    }

    return response.json();
}

// Ghosts
async function listGhosts(namespace = 'default') {
    return apiRequest(`${API_BASE}/kinds/ghosts?namespace=${namespace}`);
}

async function getGhost(name, namespace = 'default') {
    return apiRequest(`${API_BASE}/kinds/ghosts/${name}?namespace=${namespace}`);
}

async function createGhost(data) {
    return apiRequest(`${API_BASE}/kinds/ghosts`, {
        method: 'POST',
        body: JSON.stringify(data)
    });
}

async function deleteGhost(name, namespace = 'default') {
    return apiRequest(`${API_BASE}/kinds/ghosts/${name}?namespace=${namespace}`, {
        method: 'DELETE'
    });
}

// Models
async function listModels(namespace = 'default') {
    return apiRequest(`${API_BASE}/kinds/models?namespace=${namespace}`);
}

async function getModel(name, namespace = 'default') {
    return apiRequest(`${API_BASE}/kinds/models/${name}?namespace=${namespace}`);
}

async function createModel(data) {
    return apiRequest(`${API_BASE}/kinds/models`, {
        method: 'POST',
        body: JSON.stringify(data)
    });
}

async function deleteModel(name, namespace = 'default') {
    return apiRequest(`${API_BASE}/kinds/models/${name}?namespace=${namespace}`, {
        method: 'DELETE'
    });
}

// Shells
async function listShells(namespace = 'default') {
    return apiRequest(`${API_BASE}/kinds/shells?namespace=${namespace}`);
}

async function getShell(name, namespace = 'default') {
    return apiRequest(`${API_BASE}/kinds/shells/${name}?namespace=${namespace}`);
}

async function createShell(data) {
    return apiRequest(`${API_BASE}/kinds/shells`, {
        method: 'POST',
        body: JSON.stringify(data)
    });
}

async function deleteShell(name, namespace = 'default') {
    return apiRequest(`${API_BASE}/kinds/shells/${name}?namespace=${namespace}`, {
        method: 'DELETE'
    });
}

// Bots
async function listBots(namespace = 'default') {
    return apiRequest(`${API_BASE}/kinds/bots?namespace=${namespace}`);
}

async function getBot(name, namespace = 'default') {
    return apiRequest(`${API_BASE}/kinds/bots/${name}?namespace=${namespace}`);
}

async function createBot(data) {
    return apiRequest(`${API_BASE}/kinds/bots`, {
        method: 'POST',
        body: JSON.stringify(data)
    });
}

async function deleteBot(name, namespace = 'default') {
    return apiRequest(`${API_BASE}/kinds/bots/${name}?namespace=${namespace}`, {
        method: 'DELETE'
    });
}

// Teams
async function listTeams(namespace = 'default') {
    return apiRequest(`${API_BASE}/kinds/teams?namespace=${namespace}`);
}

async function getTeam(name, namespace = 'default') {
    return apiRequest(`${API_BASE}/kinds/teams/${name}?namespace=${namespace}`);
}

async function createTeam(data) {
    return apiRequest(`${API_BASE}/kinds/teams`, {
        method: 'POST',
        body: JSON.stringify(data)
    });
}

async function deleteTeam(name, namespace = 'default') {
    return apiRequest(`${API_BASE}/kinds/teams/${name}?namespace=${namespace}`, {
        method: 'DELETE'
    });
}

// Skills
async function listSkills(namespace = 'default') {
    return apiRequest(`${API_BASE}/kinds/skills?namespace=${namespace}`);
}

async function getSkill(name, namespace = 'default') {
    return apiRequest(`${API_BASE}/kinds/skills/${name}?namespace=${namespace}`);
}

async function createSkill(data) {
    return apiRequest(`${API_BASE}/kinds/skills`, {
        method: 'POST',
        body: JSON.stringify(data)
    });
}

async function deleteSkill(name, namespace = 'default') {
    return apiRequest(`${API_BASE}/kinds/skills/${name}?namespace=${namespace}`, {
        method: 'DELETE'
    });
}
