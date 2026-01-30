/* GETOLS v1.0.0 - Main JavaScript */

// Sidebar toggle for mobile
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('open');
}

// Close sidebar when clicking outside (mobile)
document.addEventListener('click', function(e) {
    const sidebar = document.getElementById('sidebar');
    const toggle = document.querySelector('.sidebar-toggle');
    
    if (sidebar && sidebar.classList.contains('open')) {
        if (!sidebar.contains(e.target) && !toggle.contains(e.target)) {
            sidebar.classList.remove('open');
        }
    }
});

// Show changelog modal
function showChangelog() {
    const modal = document.getElementById('changelog-modal');
    const content = document.getElementById('changelog-content');
    
    // Fetch changelog via HTMX
    htmx.ajax('GET', '/system/changelog', {target: '#changelog-content', swap: 'innerHTML'});
    
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

// Hide changelog modal
function hideChangelog() {
    const modal = document.getElementById('changelog-modal');
    modal.style.display = 'none';
    document.body.style.overflow = '';
}

// Close modal on escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        hideChangelog();
        hideConfirmModal();
    }
});

// Confirm modal handling
let confirmCallback = null;

function showConfirmModal(title, message, callback) {
    const modal = document.getElementById('confirm-modal');
    const titleEl = document.getElementById('confirm-title');
    const messageEl = document.getElementById('confirm-message');
    
    if (titleEl) titleEl.textContent = title;
    if (messageEl) messageEl.textContent = message;
    
    confirmCallback = callback;
    
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }
}

function hideConfirmModal() {
    const modal = document.getElementById('confirm-modal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }
    confirmCallback = null;
}

function executeConfirm() {
    if (confirmCallback && typeof confirmCallback === 'function') {
        confirmCallback();
    }
    hideConfirmModal();
}

// Delete confirmation - supports both form ID and URL
function confirmDelete(target, message) {
    showConfirmModal(
        'Confirm Delete',
        message || 'Are you sure you want to delete this item? This action cannot be undone.',
        function() {
            // Check if target is a URL or form ID
            if (target.startsWith('/')) {
                // Create and submit a form
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = target;
                document.body.appendChild(form);
                form.submit();
            } else {
                // Submit existing form by ID
                const form = document.getElementById(target);
                if (form) form.submit();
            }
        }
    );
}

// Auto-dismiss alerts after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert-success');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.style.transition = 'opacity 0.5s ease';
            alert.style.opacity = '0';
            setTimeout(function() {
                alert.remove();
            }, 500);
        }, 5000);
    });
});

// HTMX event handlers
document.body.addEventListener('htmx:beforeRequest', function(e) {
    // Add loading indicator
    const target = e.detail.target;
    if (target) {
        target.classList.add('htmx-request');
    }
});

document.body.addEventListener('htmx:afterRequest', function(e) {
    // Remove loading indicator
    const target = e.detail.target;
    if (target) {
        target.classList.remove('htmx-request');
    }
});

// Handle HTMX redirect headers
document.body.addEventListener('htmx:beforeOnLoad', function(e) {
    const xhr = e.detail.xhr;
    const redirectUrl = xhr.getResponseHeader('HX-Redirect');
    if (redirectUrl) {
        window.location.href = redirectUrl;
    }
});

// Form validation helpers
function validatePasswordMatch(password, confirm) {
    return password === confirm;
}

function validatePasswordPolicy(password) {
    const minLength = password.length >= 8;
    const hasUpper = /[A-Z]/.test(password);
    const hasLower = /[a-z]/.test(password);
    const hasNumber = /\d/.test(password);
    
    return minLength && hasUpper && hasLower && hasNumber;
}

// Toggle password visibility
function togglePasswordVisibility(inputId, buttonEl) {
    const input = document.getElementById(inputId);
    if (input.type === 'password') {
        input.type = 'text';
        buttonEl.textContent = 'Hide';
    } else {
        input.type = 'password';
        buttonEl.textContent = 'Show';
    }
}

// Format timestamp
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString();
}

// Copy to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        // Show success feedback
        console.log('Copied to clipboard');
    }).catch(function(err) {
        console.error('Failed to copy:', err);
    });
}

// Telnet warning
function showTelnetWarning() {
    alert('Warning: Telnet is not encrypted. Your credentials will be sent in plain text. Use SSH whenever possible.');
}

// Connection type change handler
function onConnectionTypeChange(select) {
    const value = select.value;
    const portInput = document.getElementById('cli_port');
    
    if (value === 'telnet') {
        showTelnetWarning();
        if (portInput.value === '22') {
            portInput.value = '23';
        }
    } else {
        if (portInput.value === '23') {
            portInput.value = '22';
        }
    }
}
