import { showView } from './app.js';

let stream = null;

export async function startCapture() {
  showView('capture');
  const video = document.getElementById('camera');

  // stgモード: ?mode=stg なら画像アップロードボタンを表示
  const mode = new URLSearchParams(location.search).get('mode');
  document.getElementById('btn-upload').hidden = mode !== 'stg';

  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'user', width: 640, height: 640 },
      audio: false,
    });
    video.srcObject = stream;
  } catch (e) {
    alert('カメラを許可してください、または ?mode=stg で画像アップロードへ');
    showView('landing');
    return;
  }

  document.getElementById('btn-shutter').onclick = () => captureFrame();
  document.getElementById('btn-upload').onclick = () => {
    document.getElementById('upload-input').click();
  };
  document.getElementById('upload-input').onchange = (e) => {
    const file = e.target.files[0];
    if (file) uploadFile(file);
  };
}

function captureFrame() {
  const video = document.getElementById('camera');
  const canvas = document.getElementById('capture-canvas');
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext('2d').drawImage(video, 0, 0);
  canvas.toBlob((blob) => {
    releaseCamera();
    showConfirm(blob);
  }, 'image/jpeg', 0.92);
}

function uploadFile(file) {
  releaseCamera();
  showConfirm(file);
}

function releaseCamera() {
  if (stream) {
    stream.getTracks().forEach(t => t.stop());
    stream = null;
  }
}

let pendingBlob = null;

function showConfirm(blob) {
  pendingBlob = blob;
  const url = URL.createObjectURL(blob);
  document.getElementById('captured-preview').src = url;
  showView('confirm');
}

document.getElementById('btn-retake').addEventListener('click', () => {
  startCapture();
});

document.getElementById('btn-confirm').addEventListener('click', () => {
  if (pendingBlob) {
    import('./progress.js').then(m => m.submitJob(pendingBlob));
  }
});
