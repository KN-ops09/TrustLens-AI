const messageInput = document.getElementById('messageInput');
const analyzeBtn = document.getElementById('analyzeBtn');
const charHint = document.getElementById('charHint');
const tracePanel = document.getElementById('tracePanel');
const traceBody = document.getElementById('traceBody');
const resultPanel = document.getElementById('resultPanel');

const gaugeFill = document.getElementById('gaugeFill');
const gaugeNumber = document.getElementById('gaugeNumber');
const verdictCategory = document.getElementById('verdictCategory');
const verdictExplanation = document.getElementById('verdictExplanation');
const flagsList = document.getElementById('flagsList');
const recommendedAction = document.getElementById('recommendedAction');

const GAUGE_CIRCUMFERENCE = 251;

messageInput.addEventListener('input', () => {
  charHint.textContent = `${messageInput.value.length} characters`;
});

analyzeBtn.addEventListener('click', analyze);

async function analyze() {
  const message = messageInput.value.trim();
  if (!message) {
    messageInput.focus();
    return;
  }

  analyzeBtn.disabled = true;
  analyzeBtn.querySelector('.btn-label').textContent = 'Scanning…';
  tracePanel.hidden = false;
  resultPanel.hidden = true;
  traceBody.textContent = '';

  let fullText = '';

  try {
    const res = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    });

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split('\n\n');
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const payload = JSON.parse(line.slice(6));
        if (payload.type === 'token') {
          fullText += payload.text;
          renderTrace(fullText);
        }
      }
    }

    renderResult(fullText);
  } catch (err) {
    traceBody.textContent += `\n[error] ${err.message}`;
  } finally {
    analyzeBtn.disabled = false;
    analyzeBtn.querySelector('.btn-label').textContent = 'Scan message';
  }
}

function renderTrace(fullText) {
  // Show only the reasoning trace portion (everything before the json fence)
  const jsonStart = fullText.indexOf('```json');
  const visible = jsonStart === -1 ? fullText : fullText.slice(0, jsonStart);
  traceBody.textContent = visible.trim();
}

function renderResult(fullText) {
  const match = fullText.match(/```json\s*([\s\S]*?)\s*```/);
  if (!match) return;

  let data;
  try {
    data = JSON.parse(match[1]);
  } catch {
    return;
  }

  resultPanel.hidden = false;

  const pct = Math.max(0, Math.min(100, Number(data.scam_probability) || 0));
  const offset = GAUGE_CIRCUMFERENCE - (GAUGE_CIRCUMFERENCE * pct) / 100;

  requestAnimationFrame(() => {
    gaugeFill.style.strokeDashoffset = offset;
    gaugeFill.style.stroke = pct >= 65 ? 'var(--danger)' : pct >= 35 ? 'var(--warn)' : 'var(--accent)';
  });

  animateNumber(gaugeNumber, pct);

  verdictCategory.textContent = data.category || 'Unclassified';
  verdictExplanation.textContent = data.explanation || '';
  recommendedAction.textContent = data.recommended_action || '';

  flagsList.innerHTML = '';
  (data.red_flags || []).forEach((flag) => {
    const chip = document.createElement('span');
    chip.className = 'flag-chip';
    chip.textContent = flag;
    flagsList.appendChild(chip);
  });

  resultPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function animateNumber(el, target) {
  const start = 0;
  const duration = 900;
  const startTime = performance.now();
  function tick(now) {
    const progress = Math.min(1, (now - startTime) / duration);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(start + (target - start) * eased);
    if (progress < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}
