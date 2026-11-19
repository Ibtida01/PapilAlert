const $ = (id) => document.getElementById(id);
let selectedFile = null;
let previewUrl = null;

async function refreshStatus(){
  try {
    const r = await fetch('/api/status');
    const s = await r.json();
    $('serviceStatus').textContent = s.model_loaded ? 'Service online · research model loaded' : 'Service online · image checks only';
    $('serviceStatus').previousElementSibling.style.background = s.model_loaded ? '#438a7d' : '#c39a53';
    $('resultMode').textContent = s.model_loaded ? 'MODEL AVAILABLE' : 'QUALITY CHECKS ONLY';
  } catch(e) {
    $('serviceStatus').textContent = 'Service unavailable';
    $('serviceStatus').previousElementSibling.style.background = '#ad6558';
  }
}

function setFile(file){
  if(!file) return;
  if(!file.type || !['image/jpeg','image/png','image/webp','image/bmp'].includes(file.type)){
    alert('Please choose a JPEG, PNG, WEBP or BMP image.');
    return;
  }
  if(file.size > 12 * 1024 * 1024){
    alert('The maximum upload size is 12 MB.');
    return;
  }
  if(previewUrl) URL.revokeObjectURL(previewUrl);
  selectedFile = file;
  previewUrl = URL.createObjectURL(file);
  $('imagePreview').src = previewUrl;
  $('fileMeta').textContent = `${file.name} · ${(file.size/1024/1024).toFixed(2)} MB · ${file.type}`;
  $('imagePreviewWrap').classList.remove('hidden');
  $('emptyState').classList.remove('hidden');
  $('resultState').classList.add('hidden');
  $('loadingState').classList.add('hidden');
  $('analyzeBtn').disabled = false;
  $('resultMode').textContent = 'AWAITING REVIEW';
}

$('fileInput').addEventListener('change', e => setFile(e.target.files[0]));
$('clearBtn').addEventListener('click', () => {
  selectedFile = null;
  $('fileInput').value = '';
  $('imagePreviewWrap').classList.add('hidden');
  $('analyzeBtn').disabled = true;
  $('resultState').classList.add('hidden');
  $('loadingState').classList.add('hidden');
  $('emptyState').classList.remove('hidden');
  $('resultMode').textContent = 'AWAITING IMAGE';
  if(previewUrl){ URL.revokeObjectURL(previewUrl); previewUrl = null; }
});

const drop = $('dropzone');
['dragenter','dragover'].forEach(evt => drop.addEventListener(evt, e => {e.preventDefault(); drop.classList.add('drag');}));
['dragleave','drop'].forEach(evt => drop.addEventListener(evt, e => {e.preventDefault(); drop.classList.remove('drag');}));
drop.addEventListener('drop', e => setFile(e.dataTransfer.files[0]));

$('analyzeBtn').addEventListener('click', async () => {
  if(!selectedFile) return;
  $('emptyState').classList.add('hidden');
  $('resultState').classList.add('hidden');
  $('loadingState').classList.remove('hidden');
  $('analyzeBtn').disabled = true;
  const body = new FormData();
  body.append('file', selectedFile);
  try {
    const response = await fetch('/api/analyze', {method:'POST', body});
    const data = await response.json();
    if(!response.ok) throw new Error(data.detail || 'Request failed');
    renderResult(data);
  } catch(err) {
    $('loadingState').classList.add('hidden');
    $('resultState').classList.remove('hidden');
    $('resultMode').textContent = 'PROCESSING ERROR';
    $('resultStatus').textContent = `Unable to process image: ${err.message}`;
    $('resultStatus').className = 'result-status error-status';
    $('qualityFlags').innerHTML = '';
    $('predictionBlock').classList.add('hidden');
    $('noModelBlock').classList.add('hidden');
  } finally {
    $('analyzeBtn').disabled = false;
  }
});

function renderResult(d){
  $('loadingState').classList.add('hidden');
  $('resultState').classList.remove('hidden');
  $('resultMode').textContent = d.prediction ? 'RESEARCH OUTPUT' : 'IMAGE CHECKS';
  const q = d.quality;
  $('qualityScore').textContent = `${q.quality_score}/100`;
  $('imageSize').textContent = `${q.width} × ${q.height}`;
  $('qualityFlags').innerHTML = q.flags.map(x=>`<li>${escapeHtml(x)}</li>`).join('');
  $('resultStatus').className = 'result-status';
  $('resultStatus').textContent = d.status === 'reacquire'
    ? 'Retake or select another image — technical check failed'
    : (d.prediction ? 'Research model output available · specialist review required' : 'Technical checks complete · no classification performed');

  if(d.prediction){
    $('noModelBlock').classList.add('hidden');
    $('predictionBlock').classList.remove('hidden');
    $('predictionSummary').textContent = d.prediction.abstain
      ? 'Model abstained — output is uncertain'
      : `Top model class: ${displayClass(d.prediction.top_class)}`;
    $('scoreRows').innerHTML = d.prediction.class_scores.map(row=>{
      const pct = Math.max(0,Math.min(100,row.score*100));
      return `<div class="score-row"><span>${escapeHtml(displayClass(row.class))}</span><b>${pct.toFixed(1)}%</b><div class="score-track"><div class="score-fill" style="width:${pct}%"></div></div></div>`;
    }).join('');

    const explanation = d.explanation;
    if(explanation && explanation.overlay_data_url){
      $('evidencePanel').classList.remove('hidden');
      setEvidenceImage(
        'evidenceOriginal',
        explanation.original_data_url || previewUrl || '',
        'originalFrame'
      );
      setEvidenceImage(
        'evidenceOverlay',
        explanation.overlay_data_url,
        'overlayFrame'
      );
      $('evidenceNote').textContent = explanation.note || 'Grad-CAM is a coarse model-attention visualisation, not a lesion boundary.';
    } else {
      $('evidencePanel').classList.add('hidden');
    }
  } else {
    $('predictionBlock').classList.add('hidden');
    // A failed technical gate is not the same as a missing classifier.
    $('noModelBlock').classList.toggle('hidden', d.status === 'reacquire');
  }
}

function setEvidenceImage(imageId, source, frameId){
  const img = $(imageId);
  const frame = $(frameId);
  frame.classList.remove('image-error');
  img.onload = () => frame.classList.remove('image-error');
  img.onerror = () => frame.classList.add('image-error');
  img.removeAttribute('src');
  if(!source){
    frame.classList.add('image-error');
    return;
  }
  img.src = source;
}

function displayClass(name){
  return ({no_ode:'No ODE pattern predicted',optic_disc_edema:'Optic-disc edema pattern predicted'}[name] || name || 'Uncertain');
}

function escapeHtml(s){
  return String(s).replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
refreshStatus();
