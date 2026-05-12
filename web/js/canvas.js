// ─── Canvas & Viewport Management ──────────────────────────────────────────

const Canvas = {
  element: null,
  ctx: null,
  width: 0,
  height: 0,

  init(elementId) {
    this.element = document.getElementById(elementId);
    
    // Create canvas overlay for rendering
    const canvas = document.createElement('canvas');
    canvas.id = 'renderCanvas';
    this.element.appendChild(canvas);
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');

    this.resize();
    window.addEventListener('resize', () => this.resize());

    // Mouse/Touch events
    this.canvas.addEventListener('wheel', (e) => this.handleWheel(e));
    this.canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
    this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
    this.canvas.addEventListener('mouseup', (e) => this.handleMouseUp(e));
    this.canvas.addEventListener('mouseout', (e) => this.handleMouseUp(e));

    // Touch events for mobile
    this.canvas.addEventListener('touchstart', (e) => this.handleTouchStart(e));
    this.canvas.addEventListener('touchmove', (e) => this.handleTouchMove(e));
    this.canvas.addEventListener('touchend', (e) => this.handleTouchEnd(e));
  },

  resize() {
    this.width = this.element.clientWidth;
    this.height = this.element.clientHeight;
    this.canvas.width = this.width;
    this.canvas.height = this.height;
    this.render();
  },

  // ─── Viewport Transformation ───────────────────────────────────────────

  worldToScreen(wx, wy) {
    return {
      x: (wx - GraphState.viewportX) * GraphState.scale + this.width / 2,
      y: (wy - GraphState.viewportY) * GraphState.scale + this.height / 2,
    };
  },

  screenToWorld(sx, sy) {
    return {
      x: (sx - this.width / 2) / GraphState.scale + GraphState.viewportX,
      y: (sy - this.height / 2) / GraphState.scale + GraphState.viewportY,
    };
  },

  // ─── Rendering ───────────────────────────────────────────────────────────

  render() {
    const ctx = this.ctx;
    ctx.fillStyle = '#0b0f19';
    ctx.fillRect(0, 0, this.width, this.height);

    ctx.save();
    ctx.translate(this.width / 2, this.height / 2);
    ctx.scale(GraphState.scale, GraphState.scale);
    ctx.translate(-GraphState.viewportX, -GraphState.viewportY);

    // Draw grid
    this.drawGrid();

    // Draw edges
    this.drawEdges();

    // Draw nodes
    this.drawNodes();

    ctx.restore();
  },

  drawGrid() {
    const ctx = this.ctx;
    const gridSize = GraphState.gridSize;
    const offsetX = -GraphState.viewportX;
    const offsetY = -GraphState.viewportY;

    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = 0.5;

    const startX = Math.floor(offsetX / gridSize) * gridSize;
    const startY = Math.floor(offsetY / gridSize) * gridSize;
    const endX = startX + (this.width / GraphState.scale + gridSize);
    const endY = startY + (this.height / GraphState.scale + gridSize);

    for (let x = startX; x < endX; x += gridSize) {
      ctx.beginPath();
      ctx.moveTo(x, startY);
      ctx.lineTo(x, endY);
      ctx.stroke();
    }

    for (let y = startY; y < endY; y += gridSize) {
      ctx.beginPath();
      ctx.moveTo(startX, y);
      ctx.lineTo(endX, y);
      ctx.stroke();
    }
  },

  drawEdges() {
    const ctx = this.ctx;

    GraphState.edges.forEach((edge) => {
      const fromNode = GraphState.getNode(edge.from);
      const toNode = GraphState.getNode(edge.toNodeId);

      if (!fromNode || !toNode) return;

      const x1 = fromNode.x + fromNode.width;
      const y1 = fromNode.y + fromNode.height / 2;
      const x2 = toNode.x;
      const y2 = toNode.y + fromNode.height / 2;

      ctx.strokeStyle = '#2563eb';
      ctx.lineWidth = 2;
      ctx.lineCap = 'round';

      // Bezier curve
      const cp1x = x1 + (x2 - x1) * 0.3;
      const cp1y = y1;
      const cp2x = x2 - (x2 - x1) * 0.3;
      const cp2y = y2;

      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, x2, y2);
      ctx.stroke();

      // Arrow
      this.drawArrow(ctx, cp2x, cp2y, x2, y2);
    });

    // Draw edge being drawn
    if (GraphState.isDrawingEdge && GraphState.edgeSourceNodeId) {
      const sourceNode = GraphState.getNode(GraphState.edgeSourceNodeId);
      if (sourceNode) {
        ctx.strokeStyle = '#f59e0b';
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 5]);
        ctx.beginPath();
        ctx.moveTo(sourceNode.x + sourceNode.width, sourceNode.y + sourceNode.height / 2);
        ctx.lineTo(GraphState.dragStartX, GraphState.dragStartY);
        ctx.stroke();
        ctx.setLineDash([]);
      }
    }
  },

  drawArrow(ctx, fromX, fromY, toX, toY) {
    const headlen = 15;
    const angle = Math.atan2(toY - fromY, toX - fromX);

    ctx.fillStyle = '#2563eb';
    ctx.beginPath();
    ctx.moveTo(toX, toY);
    ctx.lineTo(toX - headlen * Math.cos(angle - Math.PI / 6), toY - headlen * Math.sin(angle - Math.PI / 6));
    ctx.lineTo(toX - headlen * Math.cos(angle + Math.PI / 6), toY - headlen * Math.sin(angle + Math.PI / 6));
    ctx.closePath();
    ctx.fill();
  },

  drawNodes() {
    const ctx = this.ctx;

    GraphState.getAllNodes().forEach((node) => {
      this.drawNode(ctx, node);
    });
  },

  drawNode(ctx, node) {
    const isSelected = GraphState.selectedNodeId === node.id;

    // Node body
    ctx.fillStyle = this.getNodeColor(node.type);
    ctx.strokeStyle = isSelected ? '#60a5fa' : '#475569';
    ctx.lineWidth = isSelected ? 3 : 2;
    ctx.beginPath();
    ctx.roundRect(node.x, node.y, node.width, node.height, 8);
    ctx.fill();
    ctx.stroke();

    // Node label
    ctx.fillStyle = '#f1f5f9';
    ctx.font = 'bold 12px system-ui';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(node.label, node.x + node.width / 2, node.y + node.height / 2);

    // Input/Output ports
    this.drawPorts(ctx, node);
  },

  getNodeColor(type) {
    const colors = {
      cell: '#1f2937',
      input: '#065f46',
      output: '#7c2d12',
      decision: '#4c1d95',
      workflow: '#1e3a8a',
    };
    return colors[type] || '#111827';
  },

  drawPorts(ctx, node) {
    const portRadius = 5;
    const portColor = '#60a5fa';

    // Input port (left)
    ctx.fillStyle = portColor;
    ctx.beginPath();
    ctx.arc(node.x, node.y + node.height / 2, portRadius, 0, Math.PI * 2);
    ctx.fill();

    // Output port (right)
    ctx.fillStyle = portColor;
    ctx.beginPath();
    ctx.arc(node.x + node.width, node.y + node.height / 2, portRadius, 0, Math.PI * 2);
    ctx.fill();
  },

  // ─── Event Handlers ────────────────────────────────────────────────────

  handleWheel(e) {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    const newScale = GraphState.scale * delta;
    GraphState.setViewport(GraphState.viewportX, GraphState.viewportY, newScale);
    this.render();
  },

  handleMouseDown(e) {
    const pos = this.screenToWorld(e.clientX - this.canvas.getBoundingClientRect().left, e.clientY - this.canvas.getBoundingClientRect().top);
    const nodeId = this.getNodeAtPosition(pos.x, pos.y);

    if (e.button === 2) {
      // Right click - pan
      GraphState.isDragging = true;
      GraphState.dragStartX = e.clientX;
      GraphState.dragStartY = e.clientY;
    } else if (nodeId) {
      // Left click on node
      const node = GraphState.getNode(nodeId);
      const isOutputPort = pos.x > node.x + node.width - 10;

      if (isOutputPort) {
        // Start edge drawing
        GraphState.isDrawingEdge = true;
        GraphState.edgeSourceNodeId = nodeId;
      } else {
        // Select and drag node
        GraphState.selectNode(nodeId);
        GraphState.isDragging = true;
        GraphState.draggedNodeId = nodeId;
      }

      GraphState.dragStartX = pos.x;
      GraphState.dragStartY = pos.y;
    } else {
      // Click on empty space
      GraphState.deselectNode();
    }

    UI.updateInspector();
    this.render();
  },

  handleMouseMove(e) {
    const rect = this.canvas.getBoundingClientRect();
    const pos = this.screenToWorld(e.clientX - rect.left, e.clientY - rect.top);

    if (GraphState.isDragging && !GraphState.isDrawingEdge) {
      // Pan or drag node
      if (GraphState.draggedNodeId) {
        const node = GraphState.getNode(GraphState.draggedNodeId);
        if (node) {
          node.x += pos.x - GraphState.dragStartX;
          node.y += pos.y - GraphState.dragStartY;
        }
      } else {
        GraphState.viewportX -= (pos.x - GraphState.dragStartX);
        GraphState.viewportY -= (pos.y - GraphState.dragStartY);
      }

      GraphState.dragStartX = pos.x;
      GraphState.dragStartY = pos.y;
    } else if (GraphState.isDrawingEdge) {
      GraphState.dragStartX = pos.x;
      GraphState.dragStartY = pos.y;
    }

    this.render();
  },

  handleMouseUp(e) {
    const rect = this.canvas.getBoundingClientRect();
    const pos = this.screenToWorld(e.clientX - rect.left, e.clientY - rect.top);

    if (GraphState.isDrawingEdge && GraphState.edgeSourceNodeId) {
      const targetNodeId = this.getNodeAtPosition(pos.x, pos.y);
      if (targetNodeId && targetNodeId !== GraphState.edgeSourceNodeId) {
        GraphState.addEdge(GraphState.edgeSourceNodeId, targetNodeId, 0);
      }
    }

    GraphState.isDragging = false;
    GraphState.draggedNodeId = null;
    GraphState.isDrawingEdge = false;
    GraphState.edgeSourceNodeId = null;

    GraphState.saveToStorage();
    this.render();
  },

  handleTouchStart(e) {
    if (e.touches.length === 1) {
      const touch = e.touches[0];
      this.handleMouseDown({ clientX: touch.clientX, clientY: touch.clientY, button: 0 });
    }
  },

  handleTouchMove(e) {
    if (e.touches.length === 1) {
      const touch = e.touches[0];
      this.handleMouseMove({ clientX: touch.clientX, clientY: touch.clientY });
    }
  },

  handleTouchEnd(e) {
    this.handleMouseUp({ clientX: 0, clientY: 0, button: 0 });
  },

  // ─── Helpers ────────────────────────────────────────────────────────────

  getNodeAtPosition(x, y) {
    const nodes = GraphState.getAllNodes().reverse();
    for (const node of nodes) {
      if (
        x >= node.x &&
        x <= node.x + node.width &&
        y >= node.y &&
        y <= node.y + node.height
      ) {
        return node.id;
      }
    }
    return null;
  },

  fitToView() {
    const nodes = GraphState.getAllNodes();
    if (nodes.length === 0) return;

    let minX = Infinity,
      minY = Infinity,
      maxX = -Infinity,
      maxY = -Infinity;

    nodes.forEach((node) => {
      minX = Math.min(minX, node.x);
      minY = Math.min(minY, node.y);
      maxX = Math.max(maxX, node.x + node.width);
      maxY = Math.max(maxY, node.y + node.height);
    });

    const centerX = (minX + maxX) / 2;
    const centerY = (minY + maxY) / 2;
    const scale = Math.min(
      this.width / (maxX - minX + 100),
      this.height / (maxY - minY + 100)
    );

    GraphState.setViewport(centerX, centerY, scale);
    this.render();
  },
};

// Polyfill for roundRect
if (!CanvasRenderingContext2D.prototype.roundRect) {
  CanvasRenderingContext2D.prototype.roundRect = function (x, y, w, h, r) {
    if (w < 2 * r) r = w / 2;
    if (h < 2 * r) r = h / 2;
    this.beginPath();
    this.moveTo(x + r, y);
    this.arcTo(x + w, y, x + w, y + h, r);
    this.arcTo(x + w, y + h, x, y + h, r);
    this.arcTo(x, y + h, x, y, r);
    this.arcTo(x, y, x + w, y, r);
    this.closePath();
  };
}
