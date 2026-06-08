document.addEventListener('DOMContentLoaded', () => {
    const params = new URLSearchParams(window.location.search);

    const subject = params.get('subject') || '(Sans objet)';
    const sender  = params.get('sender')  || '—';
    const date    = params.get('date')    || '—';
    const body    = params.get('body')    || '(Corps vide)';

    document.getElementById('email_subject').innerText = subject;
    document.getElementById('email_sender').innerText  = sender;
    document.getElementById('email_date').innerText    = date;
    document.getElementById('email_body').innerHTML    = body;

    document.title = `${subject} — ALT Fleet`;
});