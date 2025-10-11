async function fetchJSON(url, token) {
  const res = await fetch(url, { headers: { 'X-Admin-Token': token || '' } });
  if (!res.ok) throw new Error('HTTP ' + res.status);
  return await res.json();
}

function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text) e.textContent = text;
  return e;
}

async function refresh() {
  const token = document.getElementById('adminToken').value || '';
  try {
    const [agents, tasks, results] = await Promise.all([
      fetchJSON('/agents', token),
      fetchJSON('/tasks', token),
      fetchJSON('/results?limit=50', token),
    ]);

    renderAgents(agents);
    renderTasks(tasks);
    renderResults(results);
  } catch (e) {
    alert('Failed to load data: ' + e.message + '\nDid you set X-Admin-Token?');
  }
}

function renderAgents(list) {
  const root = document.getElementById('agents');
  root.innerHTML = '';
  list.forEach(a => {
    const card = el('div', 'card');
    card.appendChild(el('div', 'title', a.hostname || a.id));
    const kv = el('div', 'kv');
    kv.innerHTML = `
      <div>Agent ID</div><div>${a.id}</div>
      <div>OS</div><div>${a.os || '-'}</div>
      <div>Version</div><div>${a.version || '-'}</div>
      <div>Last Seen</div><div>${new Date(a.last_seen).toLocaleString()}</div>
    `;
    card.appendChild(kv);
    root.appendChild(card);
  });
}

function renderTasks(list) {
  const root = document.getElementById('tasks');
  root.innerHTML = '';
  list.forEach(t => {
    const card = el('div', 'card');
    card.appendChild(el('div', 'title', `${t.type}`));
    const sub = el('div', 'sub', `agent: ${t.target_agent_id} · status: ${t.status}`);
    card.appendChild(sub);
    root.appendChild(card);
  });
}

function renderResults(list) {
  const root = document.getElementById('results');
  root.innerHTML = '';
  list.forEach(r => {
    const row = el('div', 'result');
    const head = el('div');
    head.innerHTML = `<span class="badge">${r.status}</span> task ${r.task_id} · agent ${r.agent_id} · ${new Date(r.created_at).toLocaleString()}`;
    const pre = el('pre', 'code');
    pre.textContent = JSON.stringify(r.output_json, null, 2);
    row.appendChild(head);
    row.appendChild(pre);
    root.appendChild(row);
  });
}

window.addEventListener('DOMContentLoaded', () => {
  document.getElementById('refreshBtn').addEventListener('click', refresh);
});
