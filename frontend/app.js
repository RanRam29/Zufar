const el = (t, attrs={}, ...children) => {
  const x = document.createElement(t);
  Object.entries(attrs).forEach(([k,v]) => {
    if (k === 'class') x.className = v;
    else if (k.startsWith('on')) x.addEventListener(k.slice(2), v);
    else x.setAttribute(k,v);
  });
  children.flat().forEach(c => x.append(c?.nodeType ? c : document.createTextNode(c)));
  return x;
};

const routes = { '/dashboard': dashboardView, '/api': apiView, '/about': aboutView };

async function dashboardView() {
  const app = document.getElementById('app');
  app.innerHTML = '';
  const card1 = el('div', {class:'card'}, el('h3', {}, 'Service Health'), el('div', {class:'muted'}, 'Live from /healthz'), el('div', {id:'health-kpi', class:'kpi'}, '—'));
  const card2 = el('div', {class:'card'}, el('h3', {}, 'Version'), el('div', {class:'muted'}, 'From /api/version'), el('div', {id:'ver-kpi', class:'kpi'}, '—'));
  const actions = el('div', {class:'card'}, el('h3', {}, 'Actions'), el('div', {class:'muted'}, 'Quick operations'), el('div', {}, el('button', {id:'btn-refresh'}, 'Refresh KPIs'), ' ', el('a', {href:'#/api', class:'btn secondary'}, 'Open API Explorer')));
  const grid = el('div', {class:'grid'}, card1, card2, actions);
  app.append(grid);

  const refresh = async () => {
    try {
      const h = await fetch('/healthz').then(r => r.json());
      const v = await fetch('/api/version').then(r => r.json());
      const kpi = document.getElementById('health-kpi');
      kpi.textContent = (h.status || 'N/A').toUpperCase();
      kpi.className = 'kpi status ' + (h.status === 'up' ? 'up' : 'down');
      document.getElementById('ver-kpi').textContent = v.version || 'N/A';
    } catch (e) {
      document.getElementById('health-kpi').textContent = 'ERROR';
      document.getElementById('ver-kpi').textContent = 'ERROR';
    }
  };
  document.getElementById('btn-refresh').addEventListener('click', refresh);
  refresh();
}

async function apiView() {
  const app = document.getElementById('app');
  app.innerHTML = '';

  const form = el('div', {class:'card'},
    el('h3', {}, 'GET /healthz'),
    el('div', {class:'muted'}, 'Check service & DB connectivity'),
    el('div', {}, el('button', {id:'hbtn'}, 'Execute')),
    el('pre', {id:'hresp'}, '...'),
    el('hr'),
    el('h3', {}, 'GET /api/version'),
    el('div', {class:'muted'}, 'Show version & environment'),
    el('div', {}, el('button', {id:'vbtn'}, 'Execute')),
    el('pre', {id:'vresp'}, '...'),
    el('hr'),
    el('h3', {}, 'GET /events (demo list)'),
    el('div', {}, el('button', {id:'ebtn'}, 'Execute')),
    el('pre', {id:'eresp'}, '...'),
    el('hr'),
    el('h3', {}, 'GET /events/geocode?address='),
    el('input', {id:'addr', placeholder:'Type address...', style:'width:60%'}),
    el('button', {id:'gbtn'}, 'Execute'),
    el('pre', {id:'gresp'}, '...'),
  );

  app.append(form);

  document.getElementById('hbtn').addEventListener('click', async () => {
    document.getElementById('hresp').textContent = 'Loading...';
    try { document.getElementById('hresp').textContent = JSON.stringify(await fetch('/healthz').then(r=>r.json()), null, 2); } catch(e){ document.getElementById('hresp').textContent = e.toString(); }
  });

  document.getElementById('vbtn').addEventListener('click', async () => {
    document.getElementById('vresp').textContent = 'Loading...';
    try { document.getElementById('vresp').textContent = JSON.stringify(await fetch('/api/version').then(r=>r.json()), null, 2); } catch(e){ document.getElementById('vresp').textContent = e.toString(); }
  });

  document.getElementById('ebtn').addEventListener('click', async () => {
    document.getElementById('eresp').textContent = 'Loading...';
    try { document.getElementById('eresp').textContent = JSON.stringify(await fetch('/events').then(r=>r.json()), null, 2); } catch(e){ document.getElementById('eresp').textContent = e.toString(); }
  });

  document.getElementById('gbtn').addEventListener('click', async () => {
    const addr = document.getElementById('addr').value || 'Tel Aviv';
    document.getElementById('gresp').textContent = 'Loading...';
    try { document.getElementById('gresp').textContent = JSON.stringify(await fetch('/events/geocode?address=' + encodeURIComponent(addr)).then(r=>r.json()), null, 2); } catch(e){ document.getElementById('gresp').textContent = e.toString(); }
  });
}

function aboutView() {
  const app = document.getElementById('app');
  app.innerHTML = '';
  const card = el('div', {class:'card'},
    el('h3', {}, 'About this UI'),
    el('p', {class:'muted'}, 'Zero-dependency SPA served directly by FastAPI StaticFiles.')
  );
  app.append(card);
}

function router() {
  const hash = location.hash.replace('#','') || '/dashboard';
  (routes[hash] || dashboardView)();
}
window.addEventListener('hashchange', router);
window.addEventListener('load', router);
