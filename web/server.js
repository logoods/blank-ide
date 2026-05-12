const http = require('http');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const PY_PORT = Number(process.env.PY_PORT || 3001);

const WEB_ROOT = __dirname;
const PORT = Number(process.env.PORT || 3000);
const MAX_BODY_BYTES = 1024 * 1024;
const STATIC_FILES = {
  '/': 'index.html',
  '/index.html': 'index.html',
  '/styles.css': 'styles.css',
  '/js/state.js': 'js/state.js',
  '/js/canvas.js': 'js/canvas.js',
  '/js/nodes.js': 'js/nodes.js',
  '/js/edges.js': 'js/edges.js',
  '/js/ui.js': 'js/ui.js',
  '/js/api.js': 'js/api.js',
  '/js/app.js': 'js/app.js',
};

const schema = {
  entities: {
    WorkflowRun: [
      { name: 'id', type: 'string' },
      { name: 'workflow', type: 'string' },
      { name: 'status', type: 'string' },
      { name: 'startedAt', type: 'datetime' },
    ],
    WorldState: [
      { name: 'activeWorkflow', type: 'string' },
      { name: 'lastCellOutput', type: 'string' },
      { name: 'updatedAt', type: 'datetime' },
    ],
  },
};

const worldState = {
  activeWorkflow: 'idle',
  lastCellOutput: 'none',
  updatedAt: new Date().toISOString(),
};

function sendJSON(res, status, body) {
  res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8' });
  res.end(JSON.stringify(body));
}

function serveStatic(req, res) {
  const requestPath = new URL(req.url, 'http://localhost').pathname;
  const fileName = STATIC_FILES[requestPath];
  if (!fileName) {
    sendJSON(res, 400, { error: 'Invalid path' });
    return;
  }
  const filePath = path.join(WEB_ROOT, fileName);

  fs.readFile(filePath, (err, data) => {
    if (err) {
      sendJSON(res, 404, { error: 'Not found' });
      return;
    }

    const ext = path.extname(filePath);
    const typeMap = {
      '.html': 'text/html; charset=utf-8',
      '.js': 'application/javascript; charset=utf-8',
      '.css': 'text/css; charset=utf-8',
    };
    res.writeHead(200, { 'Content-Type': typeMap[ext] || 'application/octet-stream' });
    res.end(data);
  });
}

function parseBody(req) {
  return new Promise((resolve, reject) => {
    const rawContentLength = req.headers['content-length'];
    const contentLength = Number(rawContentLength);
    if (rawContentLength === undefined || !Number.isFinite(contentLength) || contentLength < 0) {
      reject(new Error('Missing or invalid Content-Length'));
      return;
    }
    if (contentLength > MAX_BODY_BYTES) {
      reject(new Error('Payload too large'));
      return;
    }

    let body = '';
    let aborted = false;
    let receivedBytes = 0;
    req.on('data', (chunk) => {
      if (aborted) {
        return;
      }

      receivedBytes += chunk.length;
      if (receivedBytes > MAX_BODY_BYTES || receivedBytes > contentLength) {
        aborted = true;
        req.destroy();
        reject(new Error('Payload too large'));
        return;
      }
      body += chunk;
    });
    req.on('end', () => {
      if (aborted) {
        return;
      }
      if (!body) {
        resolve({});
        return;
      }
      try {
        resolve(JSON.parse(body));
      } catch {
        reject(new Error('Invalid JSON body'));
      }
    });
    req.on('error', reject);
  });
}

function randomId(prefix) {
  return `${prefix}-${crypto.randomUUID()}`;
}

const server = http.createServer(async (req, res) => {
  try {
    if (req.method === 'GET' && req.url === '/api/schema') {
      sendJSON(res, 200, schema);
      return;
    }

    if (req.method === 'GET' && req.url === '/api/world-state') {
      sendJSON(res, 200, worldState);
      return;
    }

    if (req.method === 'POST' && req.url === '/api/cells/run') {
      const { code = '' } = await parseBody(req);
      const output = `Cell accepted (${`${code}`.length} chars)`;
      worldState.lastCellOutput = output;
      worldState.updatedAt = new Date().toISOString();
      sendJSON(res, 200, { output, status: 'ok', ranAt: worldState.updatedAt });
      return;
    }

    if (req.method === 'POST' && req.url === '/api/workflows/run') {
      const { workflow = 'default-workflow', input = {} } = await parseBody(req);
      const run = {
        id: randomId('run'),
        workflow: String(workflow),
        status: 'completed',
        startedAt: new Date().toISOString(),
        input,
      };

      worldState.activeWorkflow = run.workflow;
      worldState.updatedAt = run.startedAt;

      sendJSON(res, 200, { run, worldState });
      return;
    }

    if (req.method === 'OPTIONS') {
      res.writeHead(204);
      res.end();
      return;
    }

    // ── Evolution / World / Config API: proxy to Python server ──────
    const pyRoutes = ['/api/evolve', '/api/observe', '/api/world', '/api/config', '/api/magic'];
    const reqPath = new URL(req.url, 'http://localhost').pathname;
    if (pyRoutes.some((r) => reqPath === r || reqPath.startsWith(r + '/'))) {
      proxyToPython(req, res);
      return;
    }

    serveStatic(req, res);
  } catch (error) {
    sendJSON(res, 400, { error: error.message });
  }
});

server.listen(PORT, () => {
  console.log(`world-platform web IDE listening on http://localhost:${PORT}`);
  console.log(`Evolution API proxied to http://127.0.0.1:${PY_PORT} (start: python web/pyserver.py)`);
});

// ── Proxy to Python evolution server ────────────────────────────────────────
function proxyToPython(req, res) {
  const options = {
    hostname: '127.0.0.1',
    port: PY_PORT,
    path: req.url,
    method: req.method,
    headers: { ...req.headers, host: `127.0.0.1:${PY_PORT}` },
  };
  const proxy = http.request(options, (pyRes) => {
    res.writeHead(pyRes.statusCode, pyRes.headers);
    pyRes.pipe(res);
  });
  proxy.on('error', () => {
    sendJSON(res, 503, { error: 'Evolution server not running. Start: python web/pyserver.py' });
  });
  req.pipe(proxy);
}
