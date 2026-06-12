/* ===== Theme Toggle ===== */
(function() {
  const toggle = document.getElementById('themeToggle');
  if (toggle) {
    const saved = localStorage.getItem('physics-story-theme');
    if (saved === 'night') document.body.classList.add('night-mode');
    toggle.addEventListener('click', function() {
      document.body.classList.toggle('night-mode');
      localStorage.setItem('physics-story-theme',
        document.body.classList.contains('night-mode') ? 'night' : 'day');
    });
  }
})();

/* ===== Knowledge Cards ===== */
document.addEventListener('click', function(e) {
  const card = e.target.closest('.knowledge-card');
  if (card) card.classList.toggle('open');
});

/* ===== Challenge Quiz ===== */
document.addEventListener('change', function(e) {
  const input = e.target;
  if (input.type === 'radio' && input.name && input.name.startsWith('quiz-')) {
    const box = input.closest('.challenge-box');
    const feedback = box.querySelector('.feedback');
    const correct = box.querySelector('input[data-correct="true"]');
    if (feedback) {
      feedback.className = 'feedback ' + (input === correct ? 'correct' : 'wrong');
      feedback.textContent = input === correct ? '✅ 正确！太棒了！' : '❌ 再想想看，注意物理原理哦～';
    }
  }
});

/* ===== Progress Tracking ===== */
function markComplete(chapterId) {
  const completed = JSON.parse(localStorage.getItem('physics-story-progress') || '{}');
  completed[chapterId] = true;
  localStorage.setItem('physics-story-progress', JSON.stringify(completed));
  updateProgressUI();
}
function isComplete(chapterId) {
  const completed = JSON.parse(localStorage.getItem('physics-story-progress') || '{}');
  return !!completed[chapterId];
}
function updateProgressUI() {
  document.querySelectorAll('[data-chapter]').forEach(el => {
    if (isComplete(el.dataset.chapter)) el.classList.add('completed');
  });
}
document.addEventListener('DOMContentLoaded', updateProgressUI);

/* ===== Canvas Responsive ===== */
function setupCanvas(canvas, width, height) {
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  const w = rect.width || width;
  canvas.width = w * dpr;
  canvas.height = height * dpr;
  canvas.style.height = height + 'px';
  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);
  return { ctx, width: w, height: height };
}
