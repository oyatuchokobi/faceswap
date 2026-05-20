import { showView } from './app.js';
import { getResultUrls } from './progress.js';

export function showResult() {
  showView('result');
  const { play, download } = getResultUrls();
  const video = document.getElementById('result-video');
  video.src = play;
  video.play().catch(() => { /* autoplay rejected, user has controls */ });

  const qr = qrcode(0, 'M');
  qr.addData(download);
  qr.make();
  document.getElementById('qr-container').innerHTML = qr.createImgTag(6);
}
