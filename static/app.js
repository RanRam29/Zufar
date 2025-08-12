(() => {
  const yearEl = document.getElementById('year');
  yearEl.textContent = new Date().getFullYear();

  const healthEl = document.getElementById('health');
  const setHealth = (ok, msg) => {
    healthEl.classList.remove('ok','err');
    healthEl.classList.add(ok ? 'ok' : 'err');
    healthEl.textContent = 'בריאות: ' + (ok ? 'תקין' : ('שגוי – ' + (msg||'')));
  };

  fetch('/healthz').then(r => {
    if (r.ok) setHealth(true);
    else setHealth(false, r.status);
  }).catch(e => setHealth(false, e?.message));

  const form = document.getElementById('register-form');
  const out = document.getElementById('register-result');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    out.textContent = 'שולח...';
    const fd = new FormData(form);
    const body = {
      email: fd.get('email'),
      full_name: fd.get('full_name') || null,
      password: fd.get('password')
    };
    form.querySelector('button').disabled = true;
    try {
      const res = await fetch('/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      const data = await res.json().catch(() => ({}));
      out.textContent = JSON.stringify(data, null, 2);
      if (!res.ok) out.style.borderColor = '#e85d75'; else out.style.borderColor = '#2a3a4a';
    } catch (err) {
      out.textContent = String(err);
      out.style.borderColor = '#e85d75';
    } finally {
      form.querySelector('button').disabled = false;
    }
  });
})();
