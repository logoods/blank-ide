async function fetchJSON(url, options) {
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || 'Request failed');
  }
  return data;
}

// ─── Schema Inspector ────────────────────────────────────────────────────────

function renderSchemaTree(schema) {
  const tree = document.getElementById('schemaTree');
  tree.innerHTML = '';

  Object.entries(schema.entities || {}).forEach(([entityName, fields]) => {
    const li = document.createElement('li');
    li.className = 'schema-entity';

    const header = document.createElement('div');
    header.className = 'schema-entity-header';
    header.setAttribute('role', 'button');
    header.setAttribute('aria-expanded', 'true');
    header.innerHTML = `<span class="toggle-icon">▾</span><span class="entity-name">${entityName}</span><span class="field-count">${fields.length} field${fields.length !== 1 ? 's' : ''}</span>`;

    const fieldList = document.createElement('ul');
    fieldList.className = 'schema-fields';

    fields.forEach((field) => {
      const fieldLi = document.createElement('li');
      fieldLi.className = 'schema-field';
      fieldLi.innerHTML = `<span class="field-name">${field.name}</span><span class="field-type">${field.type}</span>${field.description ? `<span class="field-desc">${field.description}</span>` : ''}`;
      fieldList.appendChild(fieldLi);
    });

    header.addEventListener('click', () => {
      const expanded = header.getAttribute('aria-expanded') === 'true';
      header.setAttribute('aria-expanded', String(!expanded));
      header.querySelector('.toggle-icon').textContent = expanded ? '▸' : '▾';
      fieldList.style.display = expanded ? 'none' : '';
    });

    li.appendChild(header);
    li.appendChild(fieldList);
    tree.appendChild(li);
  });
}

document.getElementById('expandAllBtn').addEventListener('click', () => {
  document.querySelectorAll('.schema-entity-header').forEach((header) => {
    header.setAttribute('aria-expanded', 'true');
    header.querySelector('.toggle-icon').textContent = '▾';
    header.nextElementSibling.style.display = '';
  });
});

document.getElementById('collapseAllBtn').addEventListener('click', () => {
  document.querySelectorAll('.schema-entity-header').forEach((header) => {
    header.setAttribute('aria-expanded', 'false');
    header.querySelector('.toggle-icon').textContent = '▸';
    header.nextElementSibling.style.display = 'none';
  });
});

document.getElementById('refreshSchemaBtn').addEventListener('click', async () => {
  try {
    const schema = await fetchJSON('/api/schema');
    renderSchemaTree(schema);
  } catch (error) {
    console.error(error);
  }
});

// ─── World-State Viewer ───────────────────────────────────────────────────────

let autoRefreshTimer = null;

function renderWorldStateKV(state, container, depth) {
  container.innerHTML = '';
  depth = depth || 0;

  Object.entries(state).forEach(([key, value]) => {
    const row = document.createElement('div');
    row.className = 'kv-row';
    row.style.paddingLeft = `${depth * 16}px`;

    if (value !== null && typeof value === 'object' && !Array.isArray(value)) {
      const groupHeader = document.createElement('div');
      groupHeader.className = 'kv-group-header';
      groupHeader.setAttribute('role', 'button');
      groupHeader.setAttribute('aria-expanded', 'true');
      groupHeader.innerHTML = `<span class="toggle-icon">▾</span><span class="kv-key">${key}</span><span class="kv-type">{object}</span>`;

      const nested = document.createElement('div');
      nested.className = 'kv-nested';
      renderWorldStateKV(value, nested, depth + 1);

      groupHeader.addEventListener('click', () => {
        const expanded = groupHeader.getAttribute('aria-expanded') === 'true';
        groupHeader.setAttribute('aria-expanded', String(!expanded));
        groupHeader.querySelector('.toggle-icon').textContent = expanded ? '▸' : '▾';
        nested.style.display = expanded ? 'none' : '';
      });

      row.appendChild(groupHeader);
      row.appendChild(nested);
    } else if (Array.isArray(value)) {
      const groupHeader = document.createElement('div');
      groupHeader.className = 'kv-group-header';
      groupHeader.setAttribute('role', 'button');
      groupHeader.setAttribute('aria-expanded', 'true');
      groupHeader.innerHTML = `<span class="toggle-icon">▾</span><span class="kv-key">${key}</span><span class="kv-type">[${value.length}]</span>`;

      const nested = document.createElement('div');
      nested.className = 'kv-nested';
      value.forEach((item, idx) => {
        const itemDiv = document.createElement('div');
        itemDiv.className = 'kv-row';
        itemDiv.style.paddingLeft = `${(depth + 1) * 16}px`;
        if (item !== null && typeof item === 'object') {
          itemDiv.innerHTML = `<span class="kv-key">[${idx}]</span><span class="kv-value">${JSON.stringify(item)}</span>`;
        } else {
          itemDiv.innerHTML = `<span class="kv-key">[${idx}]</span><span class="kv-value">${item}</span>`;
        }
        nested.appendChild(itemDiv);
      });

      groupHeader.addEventListener('click', () => {
        const expanded = groupHeader.getAttribute('aria-expanded') === 'true';
        groupHeader.setAttribute('aria-expanded', String(!expanded));
        groupHeader.querySelector('.toggle-icon').textContent = expanded ? '▸' : '▾';
        nested.style.display = expanded ? 'none' : '';
      });

      row.appendChild(groupHeader);
      row.appendChild(nested);
    } else {
      row.innerHTML = `<span class="kv-key">${key}</span><span class="kv-value">${value}</span>`;
    }

    container.appendChild(row);
  });
}

async function refreshWorldState() {
  try {
    const world = await fetchJSON('/api/world-state');
    renderWorldStateKV(world, document.getElementById('worldStateKV'));
  } catch (error) {
    console.error(error);
    document.getElementById('worldStateKV').textContent = 'Failed to load world state.';
  }
}

document.getElementById('refreshWorldBtn').addEventListener('click', refreshWorldState);

document.getElementById('autoRefreshToggle').addEventListener('change', (e) => {
  if (e.target.checked) {
    autoRefreshTimer = setInterval(refreshWorldState, 3000);
  } else {
    clearInterval(autoRefreshTimer);
    autoRefreshTimer = null;
  }
});

document.getElementById('exportWorldBtn').addEventListener('click', async () => {
  try {
    const world = await fetchJSON('/api/world-state');
    const blob = new Blob([JSON.stringify(world, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `world-state-${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
    a.click();
    URL.revokeObjectURL(url);
  } catch (error) {
    console.error(error);
  }
});

document.getElementById('importWorldInput').addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (!file) {
    return;
  }
  const reader = new FileReader();
  reader.onload = (ev) => {
    try {
      const state = JSON.parse(ev.target.result);
      renderWorldStateKV(state, document.getElementById('worldStateKV'));
    } catch {
      alert('Invalid JSON file.');
    }
  };
  reader.readAsText(file);
  e.target.value = '';
});

// ─── Workflow Runner ──────────────────────────────────────────────────────────

const workflowHistory = [];

function renderWorkflowHistory() {
  const container = document.getElementById('workflowHistory');
  if (workflowHistory.length === 0) {
    container.innerHTML = '<p class="empty-history">No workflows run yet.</p>';
    return;
  }

  container.innerHTML = '';
  workflowHistory.slice().reverse().forEach((entry) => {
    const item = document.createElement('div');
    item.className = `history-item status-${entry.status}`;
    item.innerHTML = `
      <div class="history-header">
        <span class="history-workflow">${entry.workflow}</span>
        <span class="history-status badge-${entry.status}">${entry.status}</span>
        <span class="history-time">${new Date(entry.startedAt).toLocaleTimeString()}</span>
      </div>
      <div class="history-id">${entry.id}</div>
    `;
    container.appendChild(item);
  });
}

document.getElementById('runWorkflowBtn').addEventListener('click', async () => {
  const workflow = document.getElementById('workflowName').value.trim() || 'default-workflow';
  const pending = {
    id: 'pending…',
    workflow,
    status: 'running',
    startedAt: new Date().toISOString(),
  };
  workflowHistory.push(pending);
  renderWorkflowHistory();

  try {
    const payload = {
      workflow,
      input: {
        cellCode: document.getElementById('cellCode').value,
        triggeredAt: pending.startedAt,
      },
    };

    const result = await fetchJSON('/api/workflows/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const idx = workflowHistory.indexOf(pending);
    workflowHistory[idx] = result.run;
    renderWorkflowHistory();

    document.getElementById('workflowResult').textContent = JSON.stringify(result, null, 2);
    document.getElementById('workflowLatest').open = true;

    renderWorldStateKV(result.worldState, document.getElementById('worldStateKV'));
  } catch (error) {
    console.error(error);
    const idx = workflowHistory.indexOf(pending);
    workflowHistory[idx] = { ...pending, id: 'error', status: 'failed' };
    renderWorkflowHistory();
    document.getElementById('workflowResult').textContent = `Workflow run failed: ${error.message}`;
    document.getElementById('workflowLatest').open = true;
  }
});

// ─── Cell Runner ─────────────────────────────────────────────────────────────

document.getElementById('runCellBtn').addEventListener('click', async () => {
  try {
    const code = document.getElementById('cellCode').value;
    const result = await fetchJSON('/api/cells/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code }),
    });

    document.getElementById('cellOutput').textContent = JSON.stringify(result, null, 2);
  } catch (error) {
    console.error(error);
    document.getElementById('cellOutput').textContent = `Cell run failed: ${error.message}`;
  }
});

// ─── Initialise ───────────────────────────────────────────────────────────────

async function loadInitialData() {
  const [schema, world] = await Promise.all([
    fetchJSON('/api/schema'),
    fetchJSON('/api/world-state'),
  ]);

  renderSchemaTree(schema);
  renderWorldStateKV(world, document.getElementById('worldStateKV'));
  renderWorkflowHistory();
}

loadInitialData().catch((error) => {
  console.error(error);
  document.getElementById('worldStateKV').textContent = 'Failed to load initial data. Please refresh.';
});
