// ─── Backend API Integration ───────────────────────────────────────────────

const API = {
  baseURL: '',

  async fetchJSON(url, options = {}) {
    const response = await fetch(url, options);
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || 'Request failed');
    }
    return data;
  },

  // Execute workflow graph through backend
  async runWorkflow(graphJSON) {
    try {
      const result = await this.fetchJSON('/api/workflows/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(graphJSON),
      });
      return result;
    } catch (error) {
      console.error('Workflow execution failed:', error);
      throw error;
    }
  },

  // Get workflow status
  async getWorkflowStatus(runId) {
    try {
      const result = await this.fetchJSON(`/api/workflows/${runId}`);
      return result;
    } catch (error) {
      console.error('Failed to get workflow status:', error);
      throw error;
    }
  },

  // Load workflow from backend
  async loadWorkflow(workflowName) {
    try {
      const result = await this.fetchJSON(`/api/workflows/${workflowName}`);
      return result;
    } catch (error) {
      console.error('Failed to load workflow:', error);
      throw error;
    }
  },

  // Save workflow to backend
  async saveWorkflow(graphJSON, name) {
    try {
      const result = await this.fetchJSON('/api/workflows', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          graph: graphJSON,
        }),
      });
      return result;
    } catch (error) {
      console.error('Failed to save workflow:', error);
      throw error;
    }
  },
};

// Wire up workflow run button to execute graph
document.addEventListener('DOMContentLoaded', () => {
  const runBtn = document.getElementById('runWorkflowBtn');
  if (runBtn) {
    runBtn.addEventListener('click', async () => {
      try {
        const workflow = Nodes.exportAsWorkflow();
        const result = await API.runWorkflow(workflow);
        console.log('Workflow result:', result);
        alert('Workflow executed successfully!');
      } catch (error) {
        console.error('Error:', error);
        alert('Workflow execution failed: ' + error.message);
      }
    });
  }
});
