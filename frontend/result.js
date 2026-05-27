import { showView } from './app.js';
import { getResultUrls } from './progress.js';

export function showResult() {
  showView('result');
  const { play, download } = getResultUrls();
  const video = document.getElementById('result-video');
  const overlay = document.getElementById('result-overlay');

  const qr = qrcode(0, 'M');
  qr.addData(download);
  qr.make();
  document.getElementById('qr-container').innerHTML = qr.createImgTag(6);

  video.src = play;
  video.play().catch(() => {});

  video.addEventListener('ended', () => {
    overlay.classList.add('visible');
  }, { once: true });
}
