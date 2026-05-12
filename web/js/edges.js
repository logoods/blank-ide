// ─── Edge Management ───────────────────────────────────────────────────────

const Edges = {
  // Check if edge already exists
  edgeExists(from, to, port = 0) {
    return GraphState.edges.some(
      (e) => e.from === from && e.toNodeId === to && e.toPort === port
    );
  },

  // Validate edge connection
  canConnect(fromNodeId, toNodeId) {
    const fromNode = GraphState.getNode(fromNodeId);
    const toNode = GraphState.getNode(toNodeId);

    if (!fromNode || !toNode) return false;
    if (fromNode.id === toNode.id) return false; // No self-loops

    // Prevent creating edges between input/output nodes
    if (
      (fromNode.type === 'input' && toNode.type === 'input') ||
      (fromNode.type === 'output' && toNode.type === 'output')
    ) {
      return false;
    }

    // Output can only connect to non-output nodes
    if (fromNode.type === 'output') return false;

    // Input can only receive from non-input nodes
    if (toNode.type === 'input') return false;

    return true;
  },

  // Create edge with validation
  createEdge(fromNodeId, toNodeId, toPort = 0) {
    if (!this.canConnect(fromNodeId, toNodeId)) {
      console.warn('Cannot create edge:', fromNodeId, '→', toNodeId);
      return false;
    }

    if (this.edgeExists(fromNodeId, toNodeId, toPort)) {
      console.warn('Edge already exists');
      return false;
    }

    GraphState.addEdge(fromNodeId, toNodeId, toPort);
    GraphState.saveToStorage();
    return true;
  },

  // Remove edge
  removeEdge(from, to, port = 0) {
    GraphState.deleteEdge(from, to, port);
    GraphState.saveToStorage();
  },

  // Get all edges connected to a node
  getConnectedEdges(nodeId) {
    return {
      outgoing: GraphState.getEdgesFrom(nodeId),
      incoming: GraphState.getEdgesTo(nodeId),
    };
  },

  // Validate graph connectivity (basic)
  validateGraph() {
    const errors = [];
    const nodeIds = new Set(Object.keys(GraphState.nodes));

    GraphState.edges.forEach((edge) => {
      if (!nodeIds.has(edge.from)) {
        errors.push(`Edge references deleted source node: ${edge.from}`);
      }
      if (!nodeIds.has(edge.toNodeId)) {
        errors.push(`Edge references deleted target node: ${edge.toNodeId}`);
      }
    });

    return {
      valid: errors.length === 0,
      errors,
    };
  },

  // Export edges for workflow
  exportEdges() {
    return GraphState.edges.map((edge) => ({
      source: edge.from,
      target: edge.toNodeId,
      port: edge.toPort,
    }));
  },
};
