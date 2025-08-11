const API = {
  health: () => fetch('/healthz').then(r=>r.json()),
  listEvents: () => fetch('/events').then(r=>r.json()),
  historical: () => fetch('/events/historical').then(r=>r.json()),
  createEvent: (payload) => fetch('/events',{method:'POST',headers:{'Content-Type':'application/json', ...(localStorage.getItem('token')?{'Authorization':'Bearer '+localStorage.getItem('token')}: {})},body:JSON.stringify(payload)}).then(r=>r.json()),
  confirm: (id,payload) => fetch(`/events/${id}/confirm`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}).then(r=>r.json()),
  patchEvent: (id,payload) => fetch(`/events/${id}`,{method:'PATCH',headers:{'Content-Type':'application/json', ...(localStorage.getItem('token')?{'Authorization':'Bearer '+localStorage.getItem('token')}: {})},body:JSON.stringify(payload)}).then(r=>r.json()),
  signup: (payload)=> fetch('/auth/signup',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}).then(r=>r.json()),
  login: (payload)=> fetch('/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}).then(r=>r.json()),
      participants: (id)=> fetch(`/events/${id}/participants`).then(r=>r.json()),
};

const routes = {
  '/map': mapView,
  '/events': eventsView,
  '/historical': historicalView,
  '/signup': signupView,
  '/login': loginView,
  '/attendees': attendeesView,
};

function toast(msg){ alert(msg); }

function router(){
  const hash = location.hash.replace('#','') || '/map';
  (routes[hash] || mapView)();
}
window.addEventListener('hashchange', router);
window.addEventListener('load', () => {
  router();
  // WebSocket notifications -> Browser Notification API
  let ws = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + '/ws/events');
  ws.onmessage = (ev) => {
    try {
      const d = JSON.parse(ev.data);
      if (d.type === 'attendance_confirmed') {
        if (Notification && Notification.permission !== 'denied') {
          Notification.requestPermission().then(() => {
            new Notification('אישור הגעה חדש', { body: `${d.display_name} אישר הגעה לאירוע ${d.event_id}` });
          });
        } else {
          console.log('New attendance:', d);
        }
      }
    } catch(e){ console.log(e); }
  };
});

function card(title, bodyEl){
  const wrap = document.createElement('div'); wrap.className = 'card';
  const h = document.createElement('h3'); h.textContent = title; wrap.appendChild(h);
  wrap.appendChild(bodyEl); return wrap;
}

async function mapView(){
  const app = document.getElementById('app'); app.innerHTML = '';
  const mapDiv = document.createElement('div'); mapDiv.id='map';
  app.appendChild(card('מפת אירועים', mapDiv));

  const map = L.map('map').setView([32.0853,34.7818], 11);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom:19}).addTo(map);

  const events = await API.listEvents();
  events.forEach(ev => {
    L.marker([ev.lat, ev.lng]).addTo(map).bindPopup(`<b>${ev.title}</b><br>${ev.address}<br/>משתתפים נדרשים: ${ev.required_attendees}`);
  });

  // Create event form
  const form = document.createElement('div');
  form.innerHTML = `
    <div class="row">
      <div>
        <label>כותרת</label><input id="title"/>
      </div>
      <div>
        <label>כתובת (בישראל)</label><input id="address" placeholder="לדוגמה: דיזנגוף 100 תל אביב"/>
      </div>
    </div>
    <label>תיאור</label><textarea id="desc"></textarea>
    <div class="row">
      <div><label>התחלה</label><input id="start" type="datetime-local"/></div>
      <div><label>סיום</label><input id="end" type="datetime-local"/></div>
    </div>
    <label>כמות משתתפים נדרשת לנעילת אירוע לעריכה</label><input id="req" type="number" min="1" value="1"/>
    <button id="create">צור אירוע</button>
    <div class="muted">יצירת האירוע תבצע גיאוקוד לישראל ותמקם סיכה במפה.</div>
  `;
  app.appendChild(card('יצירת אירוע', form));
  document.getElementById('create').onclick = async () => {
    const payload = {
      title: document.getElementById('title').value,
      description: document.getElementById('desc').value,
      address: document.getElementById('address').value,
      start_time: new Date(document.getElementById('start').value).toISOString(),
      end_time: new Date(document.getElementById('end').value).toISOString(),
      required_attendees: parseInt(document.getElementById('req').value||'1',10)
    };
    const res = await API.createEvent(payload);
    if (res.id){
      L.marker([res.lat, res.lng]).addTo(map).bindPopup(`<b>${res.title}</b><br>${res.address}`);
      toast('האירוע נוצר');
    } else {
      toast('שגיאה ביצירת אירוע');
    }
  };
}

async function eventsView(){
  const app = document.getElementById('app'); app.innerHTML = '';
  const listDiv = document.createElement('div');
  const tbl = document.createElement('table');
  tbl.innerHTML = '<thead><tr><th>כותרת</th><th>כתובת</th><th>תחילה</th><th>סיום</th><th>נעול לעריכה</th><th>פעולות</th></tr></thead>';
  const tb = document.createElement('tbody'); tbl.appendChild(tb);
  const events = await API.listEvents();
  events.forEach(ev => {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${ev.title}</td><td>${ev.address}</td><td>${new Date(ev.start_time).toLocaleString()}</td><td>${new Date(ev.end_time).toLocaleString()}</td><td>${ev.is_locked_for_edit ? 'כן' : 'לא'}</td><td><button data-id="${ev.id}" class="confirm-btn">אשר הגעה</button> <button data-id="${ev.id}" class="edit-btn">ערוך</button> <a href="#/attendees?event=${ev.id}">מפת משתתפים</a></td>`;
    tb.appendChild(tr);
  });
  listDiv.appendChild(tbl);
  const form = document.createElement('div');
  form.innerHTML = `
    <label>שם מציג לאישור הגעה</label><input id="displayName" placeholder="שם שיוצג"/>
    <label>מיקום נוכחי (לא חובה)</label>
    <div class="row"><div><input id="lat" placeholder="lat"/></div><div><input id="lng" placeholder="lng"/></div></div>
  `;
  const container = document.createElement('div'); container.append(listDiv, form);
  document.getElementById('app').appendChild(card('רשימת אירועים', container));

  tb.addEventListener('click', async (e) => {
    const t = e.target;
    if (t.classList.contains('confirm-btn')){
      const id = t.getAttribute('data-id');
      const payload = { display_name: document.getElementById('displayName').value, lat: parseFloat(document.getElementById('lat').value || 'NaN'), lng: parseFloat(document.getElementById('lng').value || 'NaN') };
      if (isNaN(payload.lat)) delete payload.lat;
      if (isNaN(payload.lng)) delete payload.lng;
      const res = await API.confirm(id, payload);
      toast(res.ok ? 'אושר' : 'נכשל');
      location.reload();
    } else if (t.classList.contains('edit-btn')){
      const id = t.getAttribute('data-id');
      const title = prompt('כותרת חדשה (השאר ריק ללא שינוי)');
      const desc = prompt('תיאור חדש (ריק ללא שינוי)');
      const payload = {};
      if (title) payload.title = title;
      if (desc) payload.description = desc;
      const res = await API.patchEvent(id, payload);
      if (res.id) toast('עודכן'); else toast(res.detail || 'נכשל');
      location.reload();
    }
  });
}

async function attendeesView(){
  const app = document.getElementById('app'); app.innerHTML = '';
  const url = new URL(location.href);
  const eventId = url.searchParams.get('event');
  if (!eventId){ app.textContent = 'חסר מזהה אירוע'; return; }
  const mapDiv = document.createElement('div'); mapDiv.id='attendeesMap';
  app.appendChild(card('מפת משתתפים', mapDiv));
  const map = L.map('attendeesMap').setView([32.0853,34.7818], 11);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom:19}).addTo(map);

  // Fetch event and all participants via events list (simplified client-side)
  const events = await API.listEvents();
  const ev = events.find(x => String(x.id) === String(eventId));
  if (ev){
    L.marker([ev.lat, ev.lng]).addTo(map).bindPopup(`<b>${ev.title}</b><br>${ev.address}`);
  }
  // There is no dedicated endpoint to list participants; for demo, rely on notifications + confirm flow.
  // In production, add /events/{id}/participants
  toast('לצורך בדיקה, אשר הגעה עם lat/lng ותראה פינים על המפה (דמו).');
}

async function historicalView(){
  const app = document.getElementById('app'); app.innerHTML = '';
  const listDiv = document.createElement('div');
  const events = await API.historical();
  const ul = document.createElement('ul');
  events.forEach(ev => {
    const li = document.createElement('li');
    li.textContent = `${ev.title} — ${new Date(ev.start_time).toLocaleString()} עד ${new Date(ev.end_time).toLocaleString()} (${ev.address})`;
    ul.appendChild(li);
  });
  listDiv.appendChild(ul);
  app.appendChild(card('אירועים היסטוריים', listDiv));
}

async function signupView(){
  const app = document.getElementById('app'); app.innerHTML = '';
  const form = document.createElement('div');
  form.innerHTML = `
    <label>אימייל</label><input id="email"/>
    <label>שם מלא</label><input id="full_name"/>
    <label>סיסמה</label><input id="password" type="password"/>
    <button id="do">הרשמה</button>
  `;
  app.appendChild(card('הרשמה', form));
  document.getElementById('do').onclick = async () => {
    const payload = { email: email.value, full_name: full_name.value, password: password.value };
    const res = await API.signup(payload);
    if (res.access_token){ localStorage.setItem('token', res.access_token); toast('נרשמת בהצלחה'); location.hash = '/map'; }
    else toast(res.detail || 'נכשל');
  };
}

async function loginView(){
  const app = document.getElementById('app'); app.innerHTML = '';
  const form = document.createElement('div');
  form.innerHTML = `
    <label>אימייל</label><input id="email"/>
    <label>סיסמה</label><input id="password" type="password"/>
    <button id="do">התחברות</button>
  `;
  app.appendChild(card('התחברות', form));
  document.getElementById('do').onclick = async () => {
    const payload = { email: email.value, password: password.value };
    const res = await API.login(payload);
    if (res.access_token){ localStorage.setItem('token', res.access_token); toast('התחברת'); location.hash = '/map'; }
    else toast(res.detail || 'נכשל');
  };
}