const form = document.querySelector('#video-form');
const input = document.querySelector('#url');
const status = document.querySelector('#status');
const result = document.querySelector('#result');
const inspectButton = document.querySelector('#inspect-button');
const downloadButton = document.querySelector('#download-button');
let currentUrl = '';

function setStatus(message, error = false) {
  status.textContent = message;
  status.classList.toggle('error', error);
}

function duration(seconds) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const rest = seconds % 60;
  return hours ? `${hours}:${String(minutes).padStart(2, '0')}:${String(rest).padStart(2, '0')}` : `${minutes}:${String(rest).padStart(2, '0')}`;
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  result.hidden = true;
  currentUrl = '';
  inspectButton.disabled = true;
  setStatus('Buscando informações do vídeo…');
  try {
    const response = await fetch('/api/inspect', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({url: input.value})});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Não foi possível acessar o vídeo.');
    currentUrl = data.url;
    document.querySelector('#title').textContent = data.title;
    document.querySelector('#meta').textContent = `${data.channel} · ${duration(data.duration)}`;
    const thumbnail = document.querySelector('#thumbnail');
    thumbnail.src = data.thumbnail || '';
    thumbnail.hidden = !data.thumbnail;
    result.hidden = false;
    setStatus('Confira o vídeo antes de baixar.');
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    inspectButton.disabled = false;
  }
});

downloadButton.addEventListener('click', async () => {
  if (!currentUrl) return;
  downloadButton.disabled = true;
  setStatus('Preparando o arquivo. Isso pode levar alguns minutos…');
  try {
    const quality = document.querySelector('input[name="quality"]:checked').value;
    const response = await fetch('/api/download', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({url: currentUrl, quality})});
    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.error || 'Falha ao baixar o vídeo.');
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    const header = response.headers.get('Content-Disposition') || '';
    link.download = header.match(/filename="([^"]+)"/)?.[1] || 'video.mp4';
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 60000);
    setStatus('Download iniciado.');
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    downloadButton.disabled = false;
  }
});
