// ─── Node Management ───────────────────────────────────────────────────────

const Nodes = {
  // Node type definitions
  types: {
    cell: {
      label: 'Cell',
      icon: '📦',
      color: '#1f2937',
      params: ['code', 'description'],
    },
    input: {
      label: 'Input',
      icon: '📥',
      color: '#065f46',
      params: ['name', 'type'],
    },
    output: {
      label: 'Output',
      icon: '📤',
      color: '#7c2d12',
      params: ['name', 'type'],
    },
    decision: {
      label: 'Decision',
      icon: '⚙️',
      color: '#4c1d95',
      params: ['condition', 'trueBranch', 'falseBranch'],
    },
    workflow: {
      label: 'Workflow',
      icon: '🔄',
      color: '#1e3a8a',
      params: ['workflowName', 'input', 'output'],
    },
  },

  // Create a new node at given position
  createNode(type, x, y) {
    if (!this.types[type]) {
      console.error(`Unknown node type: ${type}`);
      return;
    }

    const nodeId = GraphState.addNode(type, x, y);
    const node = GraphState.getNode(nodeId);

    // Initialize default parameters
    const typeDef = this.types[type];
    node.params = {};
    typeDef.params.forEach((param) => {
      node.params[param] = '';
    });

    GraphState.saveToStorage();
    return nodeId;
  },

  // Update node parameter
  updateParam(nodeId, paramKey, value) {
    const node = GraphState.getNode(nodeId);
    if (node) {
      node.params[paramKey] = value;
      GraphState.saveToStorage();
    }
  },

  // Get node display info
  getNodeInfo(nodeId) {
    const node = GraphState.getNode(nodeId);
    if (!node) return null;

    const typeDef = this.types[node.type];
    return {
      ...node,
      typeDef,
      icon: typeDef.icon,
    };
  },

  // Export nodes as workflow JSON
  exportAsWorkflow() {
    const nodes = [];
    const edges = [];

    GraphState.getAllNodes().forEach((node) => {
      nodes.push({
        id: node.id,
        type: node.type,
        label: node.label,
        params: node.params,
        position: { x: node.x, y: node.y },
      });
    });

    GraphState.edges.forEach((edge) => {
      edges.push({
        from: edge.from,
        to: edge.toNodeId,
        port: edge.toPort,
      });
    });

    return {
      version: '1.0',
      name: 'workflow',
      nodes,
      edges,
      timestamp: new Date().toISOString(),
    };
  },
};
