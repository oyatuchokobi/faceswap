const views = ['landing', 'capture', 'confirm', 'game', 'result'];

export function showView(name) {
  for (const v of views) {
    document.getElementById(`view-${v}`).classList.toggle('active', v === name);
  }
}

// State machine entry
document.getElementById('btn-start').addEventListener('click', () => {
  import('/static/camera.js').then(m => m.startCapture());
});

document.getElementById('btn-again').addEventListener('click', () => {
  location.reload();
});

// Initial view
showView('landing');
