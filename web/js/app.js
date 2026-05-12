// ─── Main Application Entry Point ──────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  // Initialize canvas
  Canvas.init('canvas');

  // Load existing workflow from storage
  if (Object.keys(GraphState.nodes).length > 0) {
    Canvas.fitToView();
  }

  // Initial render
  Canvas.render();

  // ── Evolution Panel ──────────────────────────────────────
  _loadEvolutionHistory();
  _loadWorldState();

  const evolveBtn = document.getElementById('evolveBtn');
  const evolveSubmitBtn = document.getElementById('evolveSubmitBtn');

  if (evolveBtn) {
    evolveBtn.addEventListener('click', () => _runEvolve());
  }
  if (evolveSubmitBtn) {
    evolveSubmitBtn.addEventListener('click', () => _runEvolve());
  }

  // Auto-observe workflow runs → send to pyserver
  const runBtn = document.getElementById('runWorkflowBtn');
  if (runBtn) {
    runBtn.addEventListener('click', () => {
      API.observe({ action: 'run_workflow', success: true, cell: 'run_workflow' }).catch(() => {});
    });
  }

  // ── LLM Config Modal ────────────────────────────────────
  _initConfigModal();

  // ── JSON Import ───────────────────────────────────────────
  const jsonImportBtn = document.getElementById('jsonImportBtn');
  if (jsonImportBtn) jsonImportBtn.addEventListener('click', _runJsonImport);

  // ── Magic REPL ────────────────────────────────────────────
  _loadMagicList();
  const magicRunBtn = document.getElementById('magicRunBtn');
  if (magicRunBtn) magicRunBtn.addEventListener('click', _runMagic);

  // click on magic badge → fill name input
  document.getElementById('magicList')?.addEventListener('click', (e) => {
    const badge = e.target.closest('.magic-badge');
    if (badge) document.getElementById('magicName').value = badge.dataset.name;
  });

  // ── Canvas 节点点击 → 将节点标签填入 magic terminal ────────────────
  document.addEventListener('node-selected', (e) => {
    const node = e.detail;
    if (!node) return;
    const nameEl = document.getElementById('magicName');
    const lineEl = document.getElementById('magicLine');
    if (!nameEl) return;
    // 优先匹配同名 magic；如果没有，用 run_workflow 并把节点标签作为参数
    const magicName = nameEl.value;  // 保留已填的
    const label = node.label || node.id || '';
    const nodeType = (node.type || 'cell').toLowerCase();
    // 尝试同名 magic（如 cell 类型 → %cell 等）
    const candidates = ['run_workflow', nodeType, label.toLowerCase().replace(/\s+/g, '_')];
    // 把节点标签填入 line 参数，方便将节点内容传入命令
    if (lineEl) lineEl.value = label;
    // 滚动到 magic panel
    document.getElementById('magicPanel')?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  });

});  // end DOMContentLoaded

// ── Evolution helpers ────────────────────────────────────────────────────────

async function _runEvolve() {
  const requestEl = document.getElementById('evolveRequest');
  const statusEl  = document.getElementById('evolveStatus');
  const submitBtn = document.getElementById('evolveSubmitBtn');
  const evolveBtn = document.getElementById('evolveBtn');

  const request = requestEl ? requestEl.value.trim() : '';

  statusEl.textContent = '🧬 Evolving…';
  statusEl.className = 'evolve-status';
  if (submitBtn) submitBtn.disabled = true;
  if (evolveBtn)  evolveBtn.disabled = true;

  try {
    const result = await API.evolve(request);
    if (result.success) {
      statusEl.textContent = `✓ %${result.name} registered`;
      statusEl.className = 'evolve-status ok';
    } else {
      statusEl.textContent = `✗ ${result.error || 'failed'}`;
      statusEl.className = 'evolve-status err';
    }
    _loadEvolutionHistory();
    _loadWorldState();
    _loadMagicList();   // 进化后刷新命令列表
    _loadMagicList();
  } catch (err) {
    statusEl.textContent = err.message.includes('503')
      ? '⚠ pyserver not running (python web/pyserver.py)'
      : `✗ ${err.message}`;
    statusEl.className = 'evolve-status err';
  } finally {
    if (submitBtn) submitBtn.disabled = false;
    if (evolveBtn)  evolveBtn.disabled = false;
  }
}

async function _loadEvolutionHistory() {
  const histEl = document.getElementById('evolveHistory');
  if (!histEl) return;
  try {
    const data = await API.listEvolutions();
    const exts = (data.extensions || []).slice(-6).reverse();
    if (exts.length === 0) {
      histEl.innerHTML = '<span class="muted">No evolutions yet</span>';
      return;
    }
    histEl.innerHTML = exts
      .map((e) => `
        <div class="evolve-item">
          <span class="cmd">%${e.name}</span>
          <span class="desc">${(e.request || '').slice(0, 60)}</span>
        </div>`)
      .join('');
  } catch {
    // pyserver not running — silent
  }
}

async function _loadWorldState() {
  const el = document.getElementById('worldStateContent');
  if (!el) return;
  try {
    const data = await API.getWorldState();
    const state = data.state || {};
    const keys = Object.keys(state);
    if (keys.length === 0) {
      el.innerHTML = '<span class="muted">(empty)</span>';
      return;
    }
    el.innerHTML = keys
      .map((k) => `<div class="ws-row"><span class="ws-key">${k}</span><span class="ws-val" title="${state[k]}">${state[k]}</span></div>`)
      .join('');
  } catch {
    el.innerHTML = '<span class="muted">pyserver offline</span>';
  }
}

// ── Magic REPL ──────────────────────────────────────────────────────────────

async function _loadMagicList() {
  const el = document.getElementById('magicList');
  if (!el) return;
  try {
    const data = await API.listMagics();
    const magics = data.magics || {};
    const lines = magics.line || [];
    const cells = magics.cell || [];
    if (lines.length + cells.length === 0) {
      el.innerHTML = '<span class="muted">No magics yet — run Evolve first</span>';
      return;
    }
    const mkBadge = (name, kind) =>
      `<span class="magic-badge" data-name="${name}" title="${kind} magic">${kind === 'cell' ? '%%' : '%'}${name}</span>`;
    el.innerHTML = lines.map((n) => mkBadge(n, 'line')).join('') +
                   cells.map((n) => mkBadge(n, 'cell')).join('');
  } catch {
    el.innerHTML = '<span class="muted">pyserver offline</span>';
  }
}

async function _runMagic() {
  const nameEl   = document.getElementById('magicName');
  const lineEl   = document.getElementById('magicLine');
  const cellEl   = document.getElementById('magicCell');
  const outputEl = document.getElementById('magicOutput');
  const btn      = document.getElementById('magicRunBtn');

  const name = nameEl.value.trim().replace(/^%+/, '');
  if (!name) { outputEl.textContent = '⚠ Enter a magic command name'; return; }

  const line = lineEl.value.trim();
  const cell = cellEl.value || null;  // null → line magic; empty string → cell magic

  btn.disabled = true;
  outputEl.textContent = '⏳ Running…';

  try {
    const result = await API.runMagic(name, line, cell);
    outputEl.textContent = result.output || (result.ok ? '(no output)' : result.error);
    outputEl.className = `magic-output${result.ok ? '' : ' err'}`;
    _loadWorldState();   // 运行后刚新世界状态
  } catch (err) {
    outputEl.textContent = err.message.includes('503')
      ? '⚠ pyserver not running'
      : `✗ ${err.message}`;
    outputEl.className = 'magic-output err';
  } finally {
    btn.disabled = false;
    API.observe({ action: `magic:${name}`, cell: `%${name} ${line}`, success: true }).catch(() => {});
  }
}

// ── JSON Import ───────────────────────────────────────────────────────────────

/**
 * 支持两种格式:
 * 1. 节点数组: [{type, label, params, x, y}, ...]
 * 2. workflow 导出寻: {nodes:[...], edges:[...]}
 */
function _runJsonImport() {
  const input  = document.getElementById('jsonImportInput');
  const status = document.getElementById('jsonImportStatus');
  const raw = input.value.trim();
  if (!raw) { _setImportStatus('Please paste JSON first', 'err'); return; }

  let data;
  try {
    data = JSON.parse(raw);
  } catch (e) {
    _setImportStatus(`✗ Invalid JSON: ${e.message}`, 'err');
    return;
  }

  // Normalise to node array — handle all common shapes
  let nodeList = null;

  if (Array.isArray(data)) {
    // [{type,...}, ...]
    nodeList = data;
  } else if (data && Array.isArray(data.nodes)) {
    // {nodes:[...], edges:[...]}  — workflow export
    nodeList = data.nodes;
  } else if (data && data.type) {
    // single node object
    nodeList = [data];
  } else if (data && typeof data === 'object') {
    // maybe top-level keys are node objects: {id: {type,...}}
    const vals = Object.values(data);
    if (vals.length > 0 && vals[0] && vals[0].type) {
      nodeList = vals;
    }
  }

  if (!nodeList || nodeList.length === 0) {
    const preview = JSON.stringify(data).slice(0, 120);
    _setImportStatus(`\u2717 Cannot find nodes. Got: ${preview}\u2026`, 'err');
    return;
  }

  const VALID_TYPES = Object.keys(Nodes.types);
  const CANVAS_CX  = 300;
  const CANVAS_CY  = 200;
  const GAP_X      = 180;
  const GAP_Y      = 100;
  const PER_ROW    = 4;

  let created = 0;
  let errors  = [];

  nodeList.forEach((n, i) => {
    const type = (n.type || 'cell').toLowerCase();
    if (!VALID_TYPES.includes(type)) {
      errors.push(`#${i}: unknown type “${type}”`);
      return;
    }

    // Position: use provided coords or auto-grid
    const pos = n.position || {};
    const x = pos.x ?? n.x ?? CANVAS_CX + (i % PER_ROW) * GAP_X;
    const y = pos.y ?? n.y ?? CANVAS_CY + Math.floor(i / PER_ROW) * GAP_Y;

    const nodeId = Nodes.createNode(type, x, y);
    const node   = GraphState.getNode(nodeId);
    if (!node) return;

    if (n.label)  node.label  = n.label;
    if (n.params) Object.assign(node.params, n.params);

    created++;
  });

  // Import edges if provided
  if (!Array.isArray(data) && Array.isArray(data.edges)) {
    data.edges.forEach((e) => {
      if (e.from && e.to) GraphState.addEdge(e.from, e.to, e.port || 'input');
    });
  }

  GraphState.saveToStorage();
  Canvas.render();
  Canvas.fitToView();

  const msg = errors.length
    ? `✓ ${created} nodes • ${errors.length} skipped: ${errors.join('; ')}`
    : `✓ ${created} node${created !== 1 ? 's' : ''} imported`;
  _setImportStatus(msg, errors.length ? '' : 'ok');
  if (!errors.length) input.value = '';

  // Observe this action
  API.observe({ action: 'json_import', cell: `imported ${created} nodes`, success: true }).catch(() => {});
}

function _setImportStatus(msg, cls) {
  const el = document.getElementById('jsonImportStatus');
  if (!el) return;
  el.textContent = msg;
  el.className = `evolve-status${cls ? ' ' + cls : ''}`;
}

// ── LLM Config Modal ───────────────────────────────────────────────────────

const _PROVIDER_DEFAULTS = {
  deepseek: { model: 'deepseek-chat',         baseUrl: 'https://api.deepseek.com/v1' },
  openai:   { model: 'gpt-4o',                baseUrl: 'https://api.openai.com/v1' },
  claude:   { model: 'claude-3-5-sonnet-20241022', baseUrl: 'https://api.anthropic.com' },
  qwen:     { model: 'qwen-max',              baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1' },
  ollama:   { model: 'llama3',                baseUrl: 'http://localhost:11434' },
  custom:   { model: '',                      baseUrl: '' },
};

function _initConfigModal() {
  const modal     = document.getElementById('configModal');
  const openBtn   = document.getElementById('configBtn');
  const closeBtn  = document.getElementById('configCloseBtn');
  const saveBtn   = document.getElementById('cfgSaveBtn');
  const provSel   = document.getElementById('cfgProvider');

  if (!modal) return;

  // Fill from localStorage on open
  openBtn.addEventListener('click', () => {
    _fillConfigForm();
    modal.hidden = false;
  });

  closeBtn.addEventListener('click', () => { modal.hidden = true; });
  modal.addEventListener('click', (e) => { if (e.target === modal) modal.hidden = true; });

  // Auto-fill model/baseUrl when provider changes (only if fields untouched)
  provSel.addEventListener('change', () => {
    const def = _PROVIDER_DEFAULTS[provSel.value] || _PROVIDER_DEFAULTS.custom;
    const modelEl   = document.getElementById('cfgModel');
    const baseUrlEl = document.getElementById('cfgBaseUrl');
    if (!modelEl.dataset.userEdited)   modelEl.value   = def.model;
    if (!baseUrlEl.dataset.userEdited) baseUrlEl.value = def.baseUrl;
  });

  ['cfgModel', 'cfgBaseUrl'].forEach((id) => {
    document.getElementById(id).addEventListener('input', (e) => {
      e.target.dataset.userEdited = '1';
    });
  });

  saveBtn.addEventListener('click', _saveConfig);
}

function _fillConfigForm() {
  const saved = JSON.parse(localStorage.getItem('llm_config') || '{}');
  const provider = saved.provider || 'deepseek';
  const def      = _PROVIDER_DEFAULTS[provider] || _PROVIDER_DEFAULTS.custom;

  document.getElementById('cfgProvider').value = provider;
  document.getElementById('cfgModel').value    = saved.model   || def.model;
  document.getElementById('cfgApiKey').value   = saved.apiKey  || '';
  document.getElementById('cfgBaseUrl').value  = saved.baseUrl || def.baseUrl;

  // Reset user-edited flags
  ['cfgModel', 'cfgBaseUrl'].forEach((id) => {
    delete document.getElementById(id).dataset.userEdited;
  });
  document.getElementById('cfgStatus').textContent = '';
  document.getElementById('cfgStatus').className   = 'cfg-status';
}

async function _saveConfig() {
  const cfg = {
    provider: document.getElementById('cfgProvider').value,
    model:    document.getElementById('cfgModel').value.trim(),
    apiKey:   document.getElementById('cfgApiKey').value.trim(),
    baseUrl:  document.getElementById('cfgBaseUrl').value.trim(),
  };

  // Persist locally (never log apiKey to console)
  localStorage.setItem('llm_config', JSON.stringify(cfg));

  const statusEl = document.getElementById('cfgStatus');
  const saveBtn  = document.getElementById('cfgSaveBtn');
  saveBtn.disabled = true;
  statusEl.textContent = 'Applying…';
  statusEl.className   = 'cfg-status';

  try {
    await API.setConfig(cfg);
    statusEl.textContent = '✓ Applied';
    statusEl.className   = 'cfg-status ok';
    setTimeout(() => { document.getElementById('configModal').hidden = true; }, 800);
  } catch (err) {
    statusEl.textContent = err.message.includes('503')
      ? '⚠ pyserver not running — saved locally only'
      : `✗ ${err.message}`;
    statusEl.className = 'cfg-status err';
  } finally {
    saveBtn.disabled = false;
  }
}

// Handle context menu (right-click)
document.addEventListener('contextmenu', (e) => {
  if (e.target.id === 'renderCanvas') {
    e.preventDefault();
  }
});
