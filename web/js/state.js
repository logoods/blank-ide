// ─── Global State Management ───────────────────────────────────────────────

const GraphState = {
  nodes: {},
  edges: [],
  selectedNodeId: null,
  viewportX: 0,
  viewportY: 0,
  scale: 1,
  gridSize: 20,
  isDragging: false,
  draggedNodeId: null,
  dragStartX: 0,
  dragStartY: 0,
  isDrawingEdge: false,
  edgeSourceNodeId: null,

  // Counters for auto-naming
  nodeCounters: {
    cell: 0,
    input: 0,
    output: 0,
    decision: 0,
    workflow: 0,
  },

  // Initialization
  init() {
    this.loadFromStorage();
  },

  // Node Management
  addNode(type, x, y) {
    const id = `${type}-${++this.nodeCounters[type]}`;
    this.nodes[id] = {
      id,
      type,
      x,
      y,
      width: 140,
      height: 60,
      label: `${type}-${this.nodeCounters[type]}`,
      params: {},
      inputs: [],
      outputs: [],
    };
    return id;
  },

  getNode(id) {
    return this.nodes[id];
  },

  updateNode(id, updates) {
    if (this.nodes[id]) {
      Object.assign(this.nodes[id], updates);
    }
  },

  deleteNode(id) {
    delete this.nodes[id];
    this.edges = this.edges.filter(e => e.from !== id && e.to !== id);
    if (this.selectedNodeId === id) {
      this.selectedNodeId = null;
    }
  },

  getAllNodes() {
    return Object.values(this.nodes);
  },

  // Edge Management
  addEdge(from, toNodeId, toPort = 0) {
    this.edges.push({ from, toNodeId, toPort });
  },

  deleteEdge(from, toNodeId, toPort) {
    this.edges = this.edges.filter(
      e => !(e.from === from && e.toNodeId === toNodeId && e.toPort === toPort)
    );
  },

  getEdgesFrom(nodeId) {
    return this.edges.filter(e => e.from === nodeId);
  },

  getEdgesTo(nodeId) {
    return this.edges.filter(e => e.toNodeId === nodeId);
  },

  // Selection
  selectNode(id) {
    this.selectedNodeId = id;
  },

  deselectNode() {
    this.selectedNodeId = null;
  },

  // Viewport
  setViewport(x, y, scale) {
    this.viewportX = x;
    this.viewportY = y;
    this.scale = Math.max(0.1, Math.min(scale, 3));
  },

  // Serialization
  toJSON() {
    return {
      nodes: this.nodes,
      edges: this.edges,
    };
  },

  fromJSON(data) {
    this.nodes = data.nodes || {};
    this.edges = data.edges || [];
  },

  saveToStorage() {
    localStorage.setItem('workflow_graph', JSON.stringify(this.toJSON()));
  },

  loadFromStorage() {
    const stored = localStorage.getItem('workflow_graph');
    if (stored) {
      try {
        this.fromJSON(JSON.parse(stored));
      } catch (e) {
        console.warn('Failed to load workflow from storage:', e);
      }
    }
  },

  clear() {
    this.nodes = {};
    this.edges = [];
    this.selectedNodeId = null;
    this.nodeCounters = { cell: 0, input: 0, output: 0, decision: 0, workflow: 0 };
  },
};

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
  GraphState.init();
});
