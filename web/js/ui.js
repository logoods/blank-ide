// ─── UI Management ─────────────────────────────────────────────────────────

const UI = {
  // Update inspector panel based on selected node
  updateInspector() {
    const container = document.getElementById('inspectorContent');
    const selectedId = GraphState.selectedNodeId;

    if (!selectedId) {
      container.innerHTML = '<p class="empty-message">Select a node to edit</p>';
      return;
    }

    const nodeInfo = Nodes.getNodeInfo(selectedId);
    if (!nodeInfo) return;

    let html = `
      <div class="inspector-header">
        <h3>${nodeInfo.icon} ${nodeInfo.label}</h3>
        <button class="btn-delete" onclick="UI.deleteSelectedNode()" title="Delete node">🗑️</button>
      </div>

      <div class="inspector-section">
        <label>Node ID:</label>
        <input type="text" value="${nodeInfo.id}" readonly class="inspector-readonly">
      </div>

      <div class="inspector-section">
        <label>Label:</label>
        <input 
          type="text" 
          value="${nodeInfo.label}" 
          placeholder="Node label"
          onchange="UI.updateNodeLabel('${nodeInfo.id}', this.value)"
        >
      </div>
    `;

    // Render parameters
    const typeDef = Nodes.types[nodeInfo.type];
    if (typeDef && typeDef.params.length > 0) {
      html += '<div class="inspector-section"><label>Parameters:</label>';
      typeDef.params.forEach((param) => {
        const value = nodeInfo.params[param] || '';
        html += `
          <div class="param-input">
            <label>${param}:</label>
            <textarea 
              placeholder="Enter ${param}"
              onchange="Nodes.updateParam('${nodeInfo.id}', '${param}', this.value)"
            >${value}</textarea>
          </div>
        `;
      });
      html += '</div>';
    }

    // Show connections
    const edges = Edges.getConnectedEdges(selectedId);
    if (edges.outgoing.length > 0 || edges.incoming.length > 0) {
      html += '<div class="inspector-section"><label>Connections:</label>';
      if (edges.incoming.length > 0) {
        html += '<div class="connections-group"><strong>Input from:</strong>';
        edges.incoming.forEach((edge) => {
          const fromNode = GraphState.getNode(edge.from);
          html += `
            <div class="connection-item">
              ${fromNode.label}
              <button class="btn-sm" onclick="Edges.removeEdge('${edge.from}', '${selectedId}', ${edge.toPort}); Canvas.render(); UI.updateInspector();">✕</button>
            </div>
          `;
        });
        html += '</div>';
      }
      if (edges.outgoing.length > 0) {
        html += '<div class="connections-group"><strong>Output to:</strong>';
        edges.outgoing.forEach((edge) => {
          const toNode = GraphState.getNode(edge.toNodeId);
          html += `
            <div class="connection-item">
              ${toNode.label}
              <button class="btn-sm" onclick="Edges.removeEdge('${selectedId}', '${edge.toNodeId}', ${edge.toPort}); Canvas.render(); UI.updateInspector();">✕</button>
            </div>
          `;
        });
        html += '</div>';
      }
      html += '</div>';
    }

    container.innerHTML = html;
  },

  updateNodeLabel(nodeId, newLabel) {
    GraphState.updateNode(nodeId, { label: newLabel });
    GraphState.saveToStorage();
    Canvas.render();
    this.updateInspector();
  },

  deleteSelectedNode() {
    if (!GraphState.selectedNodeId) return;
    if (confirm('Delete this node? All connected edges will also be removed.')) {
      GraphState.deleteNode(GraphState.selectedNodeId);
      GraphState.saveToStorage();
      Canvas.render();
      this.updateInspector();
    }
  },

  // Initialize palette buttons
  initPalette() {
    document.querySelectorAll('.palette-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        const type = btn.dataset.nodeType;
        // Add node in center of viewport
        const x = GraphState.viewportX - 70;
        const y = GraphState.viewportY - 30;
        Nodes.createNode(type, x, y);
        Canvas.render();
      });
    });
  },

  // Initialize canvas controls
  initControls() {
    document.getElementById('clearCanvasBtn').addEventListener('click', () => {
      if (confirm('Clear all nodes and edges?')) {
        GraphState.clear();
        GraphState.saveToStorage();
        Canvas.render();
        this.updateInspector();
      }
    });

    document.getElementById('fitViewBtn').addEventListener('click', () => {
      Canvas.fitToView();
    });

    document.getElementById('saveWorkflowBtn').addEventListener('click', () => {
      this.saveWorkflow();
    });
  },

  // Save workflow as JSON file
  saveWorkflow() {
    const workflow = Nodes.exportAsWorkflow();
    const blob = new Blob([JSON.stringify(workflow, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `workflow-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  },
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  UI.initPalette();
  UI.initControls();
  UI.updateInspector();
});
