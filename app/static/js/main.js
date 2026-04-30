// ===== THEME TOGGLE =====
const html = document.documentElement;
const themeBtn = document.querySelector('.theme-toggle');

const savedTheme = localStorage.getItem('theme') || 'dark';
html.setAttribute('data-theme', savedTheme);

themeBtn?.addEventListener('click', () => {
    const next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
});

// ===== NOTIFICATION BADGE =====
const notifBadge = document.querySelector('.notif-badge');

async function fetchNotifCount() {
    try {
        const res = await fetch('/api/notifications/count');
        if (!res.ok) return;
        const { count } = await res.json();
        if (notifBadge) {
            if (count > 0) {
                notifBadge.textContent = count > 99 ? '99+' : count;
                notifBadge.hidden = false;
            } else {
                notifBadge.hidden = true;
            }
        }
    } catch { /* not logged in */ }
}

fetchNotifCount();

// ===== CHAT: scroll to bottom =====
const chatMessages = document.getElementById('chat-messages');
if (chatMessages) {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// ===== ADMIN TABS =====
document.querySelectorAll('.admin-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.admin-tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.admin-tab-content').forEach(c => c.hidden = true);
        tab.classList.add('active');
        document.getElementById('tab-' + tab.dataset.tab).hidden = false;
    });
});

// ===== REPORT FORM TOGGLE =====
document.querySelectorAll('.btn-report-toggle').forEach(btn => {
    btn.addEventListener('click', () => {
        const target = document.getElementById(btn.dataset.target);
        if (target) target.hidden = !target.hidden;
    });
});

// ===== REPORT CHAR COUNTER =====
document.querySelectorAll('.report-textarea').forEach(ta => {
    const counter = ta.closest('form').querySelector('.report-chars');
    if (!counter) return;
    ta.addEventListener('input', () => {
        counter.textContent = ta.value.length;
    });
});
