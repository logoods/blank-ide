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
});

// Handle context menu (right-click)
document.addEventListener('contextmenu', (e) => {
  if (e.target.id === 'renderCanvas') {
    e.preventDefault();
  }
});
