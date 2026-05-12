async function fetchJSON(url, options) {
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || 'Request failed');
  }
  return data;
}

function renderSchemaTree(schema) {
  const tree = document.getElementById('schemaTree');
  tree.innerHTML = '';

  Object.entries(schema.entities || {}).forEach(([name, fields]) => {
    const item = document.createElement('li');
    const fieldText = fields.map((f) => `${f.name}:${f.type}`).join(', ');
    item.textContent = `${name} → ${fieldText}`;
    tree.appendChild(item);
  });
}

async function loadInitialData() {
  const [schema, world] = await Promise.all([
    fetchJSON('/api/schema'),
    fetchJSON('/api/world-state'),
  ]);

  renderSchemaTree(schema);
  document.getElementById('worldState').textContent = JSON.stringify(world, null, 2);
}

document.getElementById('runWorkflowBtn').addEventListener('click', async () => {
  try {
    const workflow = document.getElementById('workflowName').value.trim() || 'default-workflow';
    const payload = {
      workflow,
      input: {
        cellCode: document.getElementById('cellCode').value,
        triggeredAt: new Date().toISOString(),
      },
    };

    const result = await fetchJSON('/api/workflows/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    document.getElementById('workflowResult').textContent = JSON.stringify(result, null, 2);
    document.getElementById('worldState').textContent = JSON.stringify(result.worldState, null, 2);
  } catch (error) {
    console.error(error);
    document.getElementById('workflowResult').textContent = 'Workflow run failed.';
  }
});

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
    document.getElementById('cellOutput').textContent = 'Cell run failed.';
  }
});

loadInitialData().catch((error) => {
  console.error(error);
  document.getElementById('worldState').textContent = 'Failed to load initial data. Please refresh.';
});
