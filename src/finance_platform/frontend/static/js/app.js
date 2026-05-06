// Finance Platform — Frontend JavaScript

// ---- Configuration ----
function getToken() {
    return localStorage.getItem('fp_token') || document.getElementById('config-token')?.value || '';
}

function getCompanyId() {
    return localStorage.getItem('fp_company_id') || document.getElementById('config-company')?.value || '';
}

function saveConfig() {
    const token = document.getElementById('config-token')?.value || '';
    const company = document.getElementById('config-company')?.value || '';
    if (token) localStorage.setItem('fp_token', token);
    if (company) localStorage.setItem('fp_company_id', company);
    showAlert('success', 'Configuration saved.');
    testConnection();
}

function logout() {
    localStorage.removeItem('fp_token');
    localStorage.removeItem('fp_company_id');
    window.location.href = '/ui/login';
}

// ---- Alerts ----
function showAlert(type, message) {
    const area = document.getElementById('alert-area');
    if (!area) return;
    area.innerHTML = '<div class="alert alert-' + type + '">' + message + '</div>';
    setTimeout(() => { if (area) area.innerHTML = ''; }, 5000);
}

// ---- API Calls ----
async function apiCall(method, url, body) {
    const token = getToken();
    const companyId = getCompanyId();
    const headers = { 'Content-Type': 'application/json' };

    if (token) headers['Authorization'] = 'Bearer ' + token;
    if (companyId) headers['X-Company-Id'] = companyId;

    const opts = { method, headers };
    if (body && (method === 'POST' || method === 'PUT')) {
        opts.body = JSON.stringify(body);
    }

    try {
        const resp = await fetch(url, opts);
        const text = await resp.text();
        let data;
        try { data = JSON.parse(text); } catch { data = text; }

        const responseEl = document.getElementById('api-response');
        if (responseEl) {
            responseEl.textContent = JSON.stringify(data, null, 2);
            responseEl.style.color = resp.ok ? '#e2e8f0' : '#fca5a5';
        }
        return { ok: resp.ok, status: resp.status, data };
    } catch (err) {
        showAlert('error', 'API call failed: ' + err.message);
        return { ok: false, status: 0, data: { error: err.message } };
    }
}

function exploreApi() {
    const method = document.getElementById('api-method').value;
    const url = document.getElementById('api-url').value;
    let body = null;
    if (method === 'POST' || method === 'PUT') {
        try { body = JSON.parse(document.getElementById('api-body').value || '{}'); }
        catch { body = {}; }
    }
    apiCall(method, url, body);
}

async function testConnection() {
    const result = await apiCall('GET', '/health/ping');
    const statusEl = document.getElementById('health-status');
    if (statusEl) {
        if (result.ok) {
            statusEl.innerHTML = '<span style="color:var(--color-success)">✓ Connected — ' +
                (result.data?.status || 'ok') + '</span>';
        } else {
            statusEl.innerHTML = '<span style="color:var(--color-error)">✗ Error ' +
                result.status + '</span>';
        }
    }
    if (result.ok) {
        document.getElementById('user-info').textContent =
            'Company: ' + (getCompanyId() || 'none');
    }
}

// ---- Section-specific page init ----
document.addEventListener('DOMContentLoaded', function() {
    // Highlight active nav item
    const path = window.location.pathname;
    document.querySelectorAll('.nav-item').forEach(item => {
        if (item.getAttribute('href') === path) {
            item.classList.add('active');
        }
    });

    // Initialize config from storage
    const token = localStorage.getItem('fp_token');
    const company = localStorage.getItem('fp_company_id');
    if (document.getElementById('config-token') && token)
        document.getElementById('config-token').value = token;
    if (document.getElementById('config-company') && company)
        document.getElementById('config-company').value = company;

    if (token && company && document.getElementById('user-info')) {
        document.getElementById('user-info').textContent = 'Company: ' + company;
    }
});
