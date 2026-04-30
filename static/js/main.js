// NexaCV — Main JS

// Sidebar toggle
function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
}

// Close sidebar on outside click (mobile)
document.addEventListener('click', (e) => {
  const sidebar = document.getElementById('sidebar');
  const menuBtn = document.querySelector('.topbar__menu');
  if (sidebar && !sidebar.contains(e.target) && menuBtn && !menuBtn.contains(e.target)) {
    sidebar.classList.remove('open');
  }
});

// Toggle password visibility
function togglePassword(btn) {
  const input = btn.closest('.input-wrap').querySelector('input');
  const icon  = btn.querySelector('i');
  if (input.type === 'password') {
    input.type = 'text';
    icon.setAttribute('data-lucide', 'eye-off');
  } else {
    input.type = 'password';
    icon.setAttribute('data-lucide', 'eye');
  }
  lucide.createIcons();
}

// Animate sub-score bars on results page
document.addEventListener('DOMContentLoaded', () => {
  const fills = document.querySelectorAll('.sub-score__fill');
  setTimeout(() => {
    fills.forEach(f => {
      const w = f.style.width;
      f.style.width = '0%';
      setTimeout(() => { f.style.width = w; }, 100);
    });
  }, 200);

  // Auto-dismiss flash messages after 5s
  setTimeout(() => {
    document.querySelectorAll('.flash').forEach(f => {
      f.style.animation = 'slideIn .3s ease reverse';
      setTimeout(() => f.remove(), 300);
    });
  }, 5000);
});
