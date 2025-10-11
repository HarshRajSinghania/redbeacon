async function fetchJSON(url, token) {
  const res = await fetch(url, { headers: { 'X-Admin-Token': token || '' } });
  if (!res.ok) throw new Error('HTTP ' + res.status);
  return await res.json();
}

async function postJSON(url, token, body) {
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Admin-Token': token || ''
    },
    body: JSON.stringify(body || {})
  });
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
    populateAgentSelect(agents);
  } catch (e) {
    alert('Failed to load data: ' + e.message + '\nDid you set X-Admin-Token?');
  }
}

function populateAgentSelect(agents) {
  const sel = document.getElementById('agentSelect');
  sel.innerHTML = '';
  agents.forEach(a => {
    const opt = document.createElement('option');
    opt.value = a.id;
    opt.textContent = `${a.hostname || a.id}`;
    sel.appendChild(opt);
  });
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

function insertPreset() {
  const type = document.getElementById('typeSelect').value;
  let preset = {};
  switch (type) {
    case 'inventory': preset = {}; break;
    case 'metrics': preset = { interval: 0.5 }; break;
    case 'logs': preset = { path: 'C:/Windows/system32/drivers/etc/hosts', max_lines: 50 }; break;
    case 'exec':
      // Windows example; change to { cmd: 'echo', args: ['hello'] } for Linux/macOS
      preset = { cmd: 'cmd', args: ['/c','echo','hello'] };
      break;
    case 'processes_list': preset = { name_filter: '', limit: 100 }; break;
    case 'network_info': preset = {}; break;
    case 'open_ports': preset = { protocols: ['tcp'], listening_only: true, limit: 100 }; break;
    case 'uptime': preset = {}; break;
    case 'user_sessions': preset = {}; break;
    case 'disk_usage_detail': preset = {}; break;
    case 'file_stat': preset = { path: 'C:/Windows/system32/notepad.exe' }; break;
    case 'file_checksum': preset = { path: 'C:/Windows/system32/notepad.exe', algo: 'sha256', max_mb: 5 }; break;
    case 'file_fetch': preset = { path: 'C:/Windows/system32/drivers/etc/hosts', max_kb: 32 }; break;
    case 'path_exists_glob': preset = { glob: 'C:/Windows/Temp/*', limit: 50 }; break;
    case 'env_vars': preset = { keys: ['PATH','TEMP'] }; break;
    default: preset = {};
  }
  const ta = document.getElementById('payloadInput');
  ta.value = JSON.stringify(preset, null, 2);
}

async function createTask() {
  const token = document.getElementById('adminToken').value || '';
  const agentId = document.getElementById('agentSelect').value;
  const type = document.getElementById('typeSelect').value;
  const payloadText = document.getElementById('payloadInput').value || '{}';
  let payload;
  try {
    payload = JSON.parse(payloadText);
  } catch (e) {
    alert('Invalid JSON in payload');
    return;
  }
  try {
    await postJSON('/tasks', token, {
      target_agent_id: agentId,
      type: type,
      payload: payload
    });
    await refresh();
    alert('Task created');
  } catch (e) {
    alert('Failed to create task: ' + e.message + '\nCheck your admin token.');
  }
}

window.addEventListener('DOMContentLoaded', () => {
  document.getElementById('refreshBtn').addEventListener('click', refresh);
  document.getElementById('presetBtn').addEventListener('click', insertPreset);
  document.getElementById('createTaskBtn').addEventListener('click', createTask);
  // Initial load
  refresh();
});
