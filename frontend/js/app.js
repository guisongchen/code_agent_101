// Main application utilities

// Show toast notification
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    if (!toast) return;

    toast.textContent = message;
    toast.className = `toast ${type}`;
    toast.classList.add('show');

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Format date
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString();
}

// Format JSON for display
function formatJSON(obj) {
    return JSON.stringify(obj, null, 2);
}

// Confirm dialog
function confirmDelete(name) {
    return confirm(`Are you sure you want to delete "${name}"?`);
}

// Show modal
function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
    }
}

// Hide modal
function hideModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
    }
}

// Get namespace from URL or default
function getNamespace() {
    const params = new URLSearchParams(window.location.search);
    return params.get('namespace') || 'default';
}

// Update URL with namespace
function setNamespace(namespace) {
    const url = new URL(window.location);
    if (namespace && namespace !== 'default') {
        url.searchParams.set('namespace', namespace);
    } else {
        url.searchParams.delete('namespace');
    }
    window.history.pushState({}, '', url);
}

// Create table row HTML
function createTableRow(cells, actions = []) {
    const tr = document.createElement('tr');

    cells.forEach(cell => {
        const td = document.createElement('td');
        td.innerHTML = cell;
        tr.appendChild(td);
    });

    if (actions.length > 0) {
        const td = document.createElement('td');
        td.innerHTML = actions.join(' ');
        tr.appendChild(td);
    }

    return tr;
}

// Show loading state
function showLoading(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                Loading...
            </div>
        `;
    }
}

// Show empty state
function showEmpty(containerId, message, icon = '📭') {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">${icon}</div>
                <h3>No items found</h3>
                <p>${message}</p>
            </div>
        `;
    }
}

// Handle API errors
function handleError(error, defaultMessage = 'Operation failed') {
    console.error(error);
    showToast(error.message || defaultMessage, 'error');
}
