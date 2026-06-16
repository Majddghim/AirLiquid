////////////////////////////////////////////////////////////////////////////////////////////////
// FLOATING CHAT WIDGET — single panel

let chatListPolling     = null;
let currentChatPolling   = null;
let currentChatEmployeeId = null;
let conversationsCache   = [];
let allEmployeesCache    = [];

document.addEventListener('DOMContentLoaded', () => {
    refreshConversationsList();
    chatListPolling = setInterval(refreshConversationsList, 8000);
});

////////////////////////////////////////////////////////////////////////////////////////////////
// TOGGLE PANEL

function toggleChatPanel() {
    const panel   = document.getElementById('chat_widget_panel');
    const chevron = document.getElementById('chat_widget_chevron');
    const isOpen  = panel.classList.contains('open');

    if (isOpen) {
        panel.classList.remove('open');
        chevron.classList.remove('open');
        stopCurrentChatPolling();
    } else {
        panel.classList.add('open');
        chevron.classList.add('open');
        showListView();
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// VIEW SWITCHING

function showListView() {
    stopCurrentChatPolling();
    currentChatEmployeeId = null;
    document.getElementById('cw_view_list').style.display = 'flex';
    document.getElementById('cw_view_new').style.display  = 'none';
    document.getElementById('cw_view_chat').style.display  = 'none';
    refreshConversationsList();
}

async function showNewMessageView() {
    document.getElementById('cw_view_list').style.display = 'none';
    document.getElementById('cw_view_new').style.display  = 'flex';
    document.getElementById('cw_view_chat').style.display  = 'none';
    document.getElementById('cw_employee_search').value   = '';

    try {
        const res  = await fetch('/employe/get-all-employes');
        const data = await res.json();
        if (data.status === 'success') {
            allEmployeesCache = data.data;
            renderEmployeeResults(allEmployeesCache);
        }
    } catch (e) {
        console.error('showNewMessageView error:', e);
    }
}

function filterEmployeeSearch() {
    const q = document.getElementById('cw_employee_search').value.toLowerCase().trim();
    const filtered = !q ? allEmployeesCache : allEmployeesCache.filter(e =>
        `${e.prenom} ${e.nom}`.toLowerCase().includes(q) ||
        (e.email || '').toLowerCase().includes(q)
    );
    renderEmployeeResults(filtered);
}

function renderEmployeeResults(list) {
    const el = document.getElementById('cw_employee_results');
    if (!list.length) {
        el.innerHTML = `<div class="text-center text-muted small py-4">Aucun employé trouvé</div>`;
        return;
    }
    el.innerHTML = list.map(e => {
        const initials = `${(e.prenom || 'E')[0]}${(e.nom || 'P')[0]}`.toUpperCase();
        return `
        <div class="chat-widget-conv-item" onclick="openChat(${e.id}, '${escapeHtmlJs(e.prenom)} ${escapeHtmlJs(e.nom)}')">
            <div class="chat-widget-conv-avatar">${initials}</div>
            <div class="chat-widget-conv-info">
                <div class="chat-widget-conv-name">${escapeHtmlJs(e.prenom)} ${escapeHtmlJs(e.nom)}</div>
                <div class="chat-widget-conv-sub">${escapeHtmlJs(e.poste || '')}</div>
            </div>
        </div>`;
    }).join('');
}

////////////////////////////////////////////////////////////////////////////////////////////////
// CONVERSATIONS LIST

async function refreshConversationsList() {
    try {
        const res  = await fetch('/messages/conversations-list');
        const data = await res.json();
        if (data.status !== 'success') return;

        conversationsCache = data.data;
        renderConversationsList();
        updateTotalBadge();
    } catch (e) {
        console.error('refreshConversationsList error:', e);
    }
}

function renderConversationsList() {
    const el = document.getElementById('chat_widget_list_body');
    if (!el || document.getElementById('cw_view_list').style.display === 'none') {
        updateTotalBadge();
        return;
    }

    if (!conversationsCache.length) {
        el.innerHTML = `
            <div class="text-center text-muted small py-4">
                <i class="fas fa-comments fa-2x mb-2 opacity-25 d-block"></i>
                Aucune conversation<br>
                <button class="btn btn-sm btn-primary mt-2" onclick="showNewMessageView()">
                    Nouveau message
                </button>
            </div>`;
        return;
    }

    el.innerHTML = conversationsCache.map(c => {
        const initials = `${(c.prenom || 'E')[0]}${(c.nom || 'P')[0]}`.toUpperCase();
        const time     = formatRelativeTime(c.last_message_at);
        const preview  = c.last_sender_type === 'admin'
            ? `Vous: ${c.last_message}`
            : c.last_message;

        return `
        <div class="chat-widget-conv-item" onclick="openChat(${c.employee_id}, '${escapeHtmlJs(c.prenom)} ${escapeHtmlJs(c.nom)}')">
            <div class="chat-widget-conv-avatar">${initials}</div>
            <div class="chat-widget-conv-info">
                <div class="chat-widget-conv-name">${escapeHtmlJs(c.prenom)} ${escapeHtmlJs(c.nom)}</div>
                <div class="chat-widget-conv-preview">${escapeHtmlJs(preview || '')}</div>
            </div>
            <div class="chat-widget-conv-meta">
                <div class="chat-widget-conv-time">${time}</div>
                ${c.unread_count > 0 ? `<div class="chat-widget-conv-unread">${c.unread_count}</div>` : ''}
            </div>
        </div>`;
    }).join('');
}

function updateTotalBadge() {
    const total = conversationsCache.reduce((sum, c) => sum + (c.unread_count || 0), 0);
    const badge = document.getElementById('chat_widget_total_badge');
    if (total > 0) {
        badge.style.display = 'flex';
        badge.innerText = total > 9 ? '9+' : total;
    } else {
        badge.style.display = 'none';
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// OPEN CHAT (replaces panel content — list disappears, chat appears)

function openChat(employeeId, employeeName) {
    currentChatEmployeeId = employeeId;

    document.getElementById('cw_view_list').style.display = 'none';
    document.getElementById('cw_view_new').style.display  = 'none';
    document.getElementById('cw_view_chat').style.display  = 'flex';

    const initials = employeeName.split(' ').map(p => p[0]).join('').toUpperCase().slice(0, 2);
    document.getElementById('cw_chat_avatar').innerText = initials;
    document.getElementById('cw_chat_name').innerText   = employeeName;
    document.getElementById('cw_chat_input').value      = '';  // ADD THIS LINE
    document.getElementById('cw_chat_body').innerHTML = `
        <div class="text-center text-muted small py-4">
            <div class="spinner-border spinner-border-sm me-2"></div>
            Chargement...
        </div>`;

    loadCurrentChatMessages();
    stopCurrentChatPolling();
    currentChatPolling = setInterval(loadCurrentChatMessages, 5000);
}

function stopCurrentChatPolling() {
    if (currentChatPolling) {
        clearInterval(currentChatPolling);
        currentChatPolling = null;
    }
}

async function loadCurrentChatMessages() {
    if (!currentChatEmployeeId) return;
    try {
        const res  = await fetch(`/messages/conversation/${currentChatEmployeeId}`);
        const data = await res.json();
        if (data.status !== 'success') return;

        const body = document.getElementById('cw_chat_body');
        const messages = data.data;

        if (!messages.length) {
            body.innerHTML = `
                <div class="text-center text-muted small py-4">
                    Aucun message — commencez la conversation
                </div>`;
        } else {
            body.innerHTML = messages.map(m => {
                const isAdmin = m.sender_type === 'admin';
                const time    = new Date(m.created_at).toLocaleTimeString('fr-TN', {
                    hour: '2-digit', minute: '2-digit'
                });
                return `
                <div class="chat-bubble ${isAdmin ? 'admin' : 'employee'}">
                    <div class="bubble-content">${escapeHtmlJs(m.content)}</div>
                    <div class="bubble-time">${time}</div>
                </div>`;
            }).join('');
            body.scrollTop = body.scrollHeight;
        }

        refreshConversationsList();
    } catch (e) {
        console.error('loadCurrentChatMessages error:', e);
    }
}

async function sendCurrentChatMessage() {
    if (!currentChatEmployeeId) return;
    const input   = document.getElementById('cw_chat_input');
    const content = input.value.trim();
    if (!content) return;

    input.value = '';

    try {
        await fetch('/messages/send', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({
                sender_type: 'admin',
                employee_id: currentChatEmployeeId,
                content:     content
            })
        });
        await loadCurrentChatMessages();
    } catch (e) {
        console.error('sendCurrentChatMessage error:', e);
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// HELPERS

function escapeHtmlJs(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;').replace(/'/g, '&#039;');
}

function formatRelativeTime(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now  = new Date();
    const diffMin = Math.floor((now - date) / 60000);

    if (diffMin < 1)   return 'maintenant';
    if (diffMin < 60)  return `${diffMin}min`;
    const diffH = Math.floor(diffMin / 60);
    if (diffH < 24)    return `${diffH}h`;
    const diffD = Math.floor(diffH / 24);
    return `${diffD}j`;
}