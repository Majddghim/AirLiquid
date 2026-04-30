////////////////////////////////////////////////////////////////////////////////////////////////
// INIT

let currentSpec = null;

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('report_input').addEventListener('keydown', e => {
        if (e.key === 'Enter') sendRequest();
    });
});

////////////////////////////////////////////////////////////////////////////////////////////////
// EXAMPLES

function useExample(el) {
    document.getElementById('report_input').value = el.innerText;
    document.getElementById('report_input').focus();
}

////////////////////////////////////////////////////////////////////////////////////////////////
// CHAT HELPERS

function addMessage(text, type, isHTML = false) {
    const container = document.getElementById('chat_container');
    const div       = document.createElement('div');
    div.className   = `message ${type}`;
    const avatar    = type === 'bot'
        ? '<div class="avatar bot"><i class="fas fa-robot"></i></div>'
        : '<div class="avatar user"><i class="fas fa-user"></i></div>';
    div.innerHTML = `
        ${type === 'user' ? '' : avatar}
        <div class="message-bubble">${isHTML ? text : escapeHtml(text)}</div>
        ${type === 'user' ? avatar : ''}`;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return div;
}

function addTyping() {
    const container = document.getElementById('chat_container');
    const div       = document.createElement('div');
    div.className   = 'message bot';
    div.id          = 'typing_indicator';
    div.innerHTML   = `
        <div class="avatar bot"><i class="fas fa-robot"></i></div>
        <div class="message-bubble">
            <div class="typing-indicator">
                <span></span><span></span><span></span>
            </div>
        </div>`;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function removeTyping() {
    const el = document.getElementById('typing_indicator');
    if (el) el.remove();
}

////////////////////////////////////////////////////////////////////////////////////////////////
// SEND REQUEST

async function sendRequest() {
    const input   = document.getElementById('report_input');
    const sendBtn = document.getElementById('send_btn');
    const text    = input.value.trim();
    if (!text) return;

    addMessage(text, 'user');
    input.value      = '';
    sendBtn.disabled = true;
    addTyping();

    try {
        const res    = await fetch('/reports/analyze', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ request: text })
        });
        const result = await res.json();
        removeTyping();

        if (result.status !== 'success') {
            addMessage(result.message || 'Je n\'ai pas compris votre demande. Pouvez-vous reformuler ?', 'bot');
            sendBtn.disabled = false;
            return;
        }

        // store for generation
        currentSpec = { title: result.title, sql: result.sql };

        const html = `
            <div>
                <div class="fw-bold mb-1">✅ J'ai compris votre demande :</div>
                <div class="report-card">
                    <div class="fw-bold text-primary">${escapeHtml(result.title)}</div>
                    <div class="text-muted small mt-2" style="font-family:monospace;font-size:11px;word-break:break-all;">
                        ${escapeHtml(result.sql)}
                    </div>
                </div>
                <div class="mt-3 d-flex gap-2">
                    <button class="download-btn btn btn-primary" onclick="generateReport('pdf')">
                        <i class="fas fa-file-pdf me-2"></i>Télécharger PDF
                    </button>
                    <button class="download-btn btn btn-success" onclick="generateReport('excel')">
                        <i class="fas fa-file-excel me-2"></i>Télécharger Excel
                    </button>
                </div>
            </div>`;

        addMessage(html, 'bot', true);

    } catch (e) {
        removeTyping();
        addMessage('Erreur réseau. Veuillez réessayer.', 'bot');
    }

    sendBtn.disabled = false;
}

////////////////////////////////////////////////////////////////////////////////////////////////
// GENERATE REPORT

async function generateReport(format) {
    if (!currentSpec) return;

    addTyping();

    try {
        const res = await fetch('/reports/generate', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({
                sql:    currentSpec.sql,
                title:  currentSpec.title,
                format: format
            })
        });

        removeTyping();

        if (!res.ok) {
            const err = await res.json();
            addMessage(`Erreur: ${err.message}`, 'bot');
            return;
        }

        const blob = await res.blob();
        const url  = URL.createObjectURL(blob);
        const a    = document.createElement('a');
        a.href     = url;
        a.download = `rapport_${new Date().toISOString().split('T')[0]}.${format === 'pdf' ? 'pdf' : 'xlsx'}`;
        a.click();
        URL.revokeObjectURL(url);

        addMessage(`✅ Rapport ${format.toUpperCase()} téléchargé avec succès !`, 'bot');

    } catch (e) {
        removeTyping();
        addMessage('Erreur lors de la génération du rapport.', 'bot');
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// HELPERS

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;')
        .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}