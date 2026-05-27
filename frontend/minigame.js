const POSE_CDN = 'https://cdn.jsdelivr.net/npm/@mediapipe/pose@0.5/pose.js';
const MIN_DURATION_MS = 30_000;

let startTime = 0;
let gameProgress = 0;
let serverProgress = 0;
let serverDone = false;
let dribbleCount = 0;
let shootCount = 0;

let camStream = null;
let pose = null;
let lastWristY = null;
let bothHandsUpFrames = 0;

export async function startGame() {
  const { showView } = await import('./app.js');
  showView('game');
  startTime = Date.now();

  const camera = document.getElementById('game-camera');
  camStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
  camera.srcObject = camStream;
  camera.hidden = false;

  try {
    await loadScript(POSE_CDN);
    setupPose(camera);
  } catch (e) {
    console.error('MediaPipe load failed, falling back to timer-only', e);
  }

  requestAnimationFrame(updateUI);
}

function loadScript(src) {
  return new Promise((res, rej) => {
    const s = document.createElement('script');
    s.src = src; s.onload = res; s.onerror = rej;
    document.head.appendChild(s);
  });
}

function setupPose(videoEl) {
  pose = new Pose({ locateFile: f => `https://cdn.jsdelivr.net/npm/@mediapipe/pose@0.5/${f}` });
  pose.setOptions({ modelComplexity: 0, smoothLandmarks: true, enableSegmentation: false });
  pose.onResults(onPoseResults);

  const tick = async () => {
    if (videoEl.readyState >= 2) {
      await pose.send({ image: videoEl });
    }
    if (!serverDone || gameProgress < 100) requestAnimationFrame(tick);
  };
  tick();
}

function onPoseResults(results) {
  if (!results.poseLandmarks) return;
  const lm = results.poseLandmarks;
  const lw = lm[15], rw = lm[16];
  const ls = lm[11], rs = lm[12];

  if (lastWristY !== null) {
    const dy = rw.y - lastWristY;
    if (dy < -0.05) { dribbleCount++; }
  }
  lastWristY = rw.y;

  if (lw.y < ls.y && rw.y < rs.y) {
    bothHandsUpFrames++;
    if (bothHandsUpFrames === 10) shootCount++;
  } else {
    bothHandsUpFrames = 0;
  }
}

function updateUI() {
  const elapsed = Date.now() - startTime;

  document.getElementById('combined-progress').value = serverProgress;
  document.getElementById('server-pct').textContent = `${serverProgress}%`;
  document.getElementById('game-score').textContent =
    `🏃 ${dribbleCount}  |  🎯 ${shootCount}`;

  if (elapsed >= MIN_DURATION_MS && serverDone) {
    cleanup();
    import('./result.js').then(m => m.showResult());
    return;
  }
  requestAnimationFrame(updateUI);
}

function cleanup() {
  if (camStream) {
    camStream.getTracks().forEach(t => t.stop());
    camStream = null;
  }
}

export function setServerProgress(pct, msg) {
  serverProgress = pct;
}

export function setServerDone() {
  serverDone = true;
  serverProgress = 100;
}
