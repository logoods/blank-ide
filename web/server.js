const http = require('http');
const fs = require('fs');
const path = require('path');

const WEB_ROOT = __dirname;
const PORT = Number(process.env.PORT || 3000);

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

function safePath(urlPath) {
  const file = urlPath === '/' ? '/index.html' : urlPath;
  const resolved = path.normalize(path.join(WEB_ROOT, file));
  if (!resolved.startsWith(WEB_ROOT)) {
    return null;
  }
  return resolved;
}

function serveStatic(req, res) {
  const filePath = safePath(req.url.split('?')[0]);
  if (!filePath) {
    sendJSON(res, 400, { error: 'Invalid path' });
    return;
  }

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
    let body = '';
    req.on('data', (chunk) => {
      body += chunk;
      if (body.length > 1024 * 1024) {
        reject(new Error('Payload too large'));
      }
    });
    req.on('end', () => {
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
  return `${prefix}-${Math.random().toString(16).slice(2, 10)}`;
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
      const output = `Cell accepted (${String(code).length} chars)`;
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

    serveStatic(req, res);
  } catch (error) {
    sendJSON(res, 400, { error: error.message });
  }
});

server.listen(PORT, () => {
  console.log(`world-platform web IDE listening on http://localhost:${PORT}`);
});
