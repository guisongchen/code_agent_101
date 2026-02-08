// Authentication utilities

const TOKEN_KEY = 'wegant_token';
const USER_KEY = 'wegant_user';

function getToken() {
    return localStorage.getItem(TOKEN_KEY);
}

function setToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
}

function clearToken() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
}

function isAuthenticated() {
    return !!getToken();
}

function checkAuth() {
    if (!isAuthenticated()) {
        window.location.href = '/ui/login.html';
        return false;
    }
    return true;
}

function logout() {
    clearToken();
    window.location.href = '/ui/login.html';
}

function setUser(user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
}

function getUser() {
    const user = localStorage.getItem(USER_KEY);
    return user ? JSON.parse(user) : null;
}

async function loadUserInfo() {
    const user = getUser();
    if (user) {
        const usernameEl = document.getElementById('username');
        if (usernameEl) {
            usernameEl.textContent = user.username;
        }
        return;
    }

    // Fetch user info from API
    try {
        const response = await fetch('/api/v1/auth/me', {
            headers: {
                'Authorization': `Bearer ${getToken()}`
            }
        });

        if (response.ok) {
            const userData = await response.json();
            setUser(userData);
            const usernameEl = document.getElementById('username');
            if (usernameEl) {
                usernameEl.textContent = userData.username;
            }
        }
    } catch (error) {
        console.error('Failed to load user info:', error);
    }
}
