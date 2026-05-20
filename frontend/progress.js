let currentJobId = null;
let resultUrl = null;
let downloadUrl = null;

export async function submitJob(faceBlob) {
  const { startGame, setServerProgress, setServerDone } = await import('./minigame.js');

  const fd = new FormData();
  fd.append('face', faceBlob, 'face.jpg');
  const res = await fetch('/api/swap', { method: 'POST', body: fd });
  const { job_id, sse_url } = await res.json();
  currentJobId = job_id;
  resultUrl = `/api/result/${job_id}.mp4`;
  downloadUrl = `${location.origin}/api/download/${job_id}.mp4`;

  startGame();

  const es = new EventSource(sse_url);
  es.addEventListener('progress', (e) => {
    const d = JSON.parse(e.data);
    setServerProgress(d.progress, d.message);
  });
  es.addEventListener('done', () => {
    setServerDone();
    es.close();
  });
  es.addEventListener('failed', (e) => {
    const d = JSON.parse(e.data);
    alert(`処理失敗: ${d.message}`);
    es.close();
    location.reload();
  });
}

export function getResultUrls() {
  return { play: resultUrl, download: downloadUrl };
}
