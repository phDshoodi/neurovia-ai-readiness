// Neurovia demo frontend logic

document.addEventListener('DOMContentLoaded',()=>{
  const KB_FILES = [
    {id:'neurovia', path:'../knowledge-base/neurovia.md', title:'Neurovia'},
    {id:'eeg', path:'../knowledge-base/knowledge-base/eeg.md', title:'EEG Monitoring'},
    {id:'seizure', path:'../knowledge-base/knowledge-base/seizure-safety.md', title:'Seizure Safety'},
    {id:'caregiver', path:'../knowledge-base/knowledge-base/caregiver-guidance.md', title:'Caregiver Guidance'}
  ];

  const docs = {};

  // Load knowledge files
  Promise.all(KB_FILES.map(f=>fetch(f.path).then(r=>r.text()).then(t=>{docs[f.id]=t}))).then(()=>{
    renderKBList(KB_FILES, docs);
    renderCaregiver(docs['caregiver']);
    populateSources(KB_FILES);
  }).catch(err=>{
    console.error('Failed to load knowledge base',err);
    document.getElementById('kb-list').textContent='Failed to load knowledge base files.';
  });

  // Simple markdown to HTML (very small)
  function mdToHtml(md){
    return md.split('\n').map(line=>{
      if(line.startsWith('# ')) return '<h3>'+line.replace('# ','')+'</h3>';
      if(line.startsWith('## ')) return '<h4>'+line.replace('## ','')+'</h4>';
      return '<p>'+line.replace(/\n/g,'')+'</p>';
    }).join('');
  }

  function renderKBList(list, docs){
    const container = document.getElementById('kb-list');
    container.innerHTML='';
    list.forEach(item=>{
      const el = document.createElement('div');
      el.className='kb-item';
      el.innerHTML = '<h4>'+item.title+'</h4><div class="muted">Click to view</div>';
      el.addEventListener('click',()=>{
        const win = window.open(item.path,'_blank');
        if(!win) alert('Unable to open file. Your browser may block popups.');
      });
      container.appendChild(el);
    });
  }

  function populateSources(list){
    const ul = document.getElementById('source-links');
    ul.innerHTML='';
    list.forEach(f=>{
      const li = document.createElement('li');
      const a = document.createElement('a');
      a.href = f.path;
      a.textContent = f.title;
      a.target = '_blank';
      li.appendChild(a);
      ul.appendChild(li);
    });
  }

  function renderCaregiver(md){
    const el = document.getElementById('caregiver-guidance');
    el.innerHTML = mdToHtml(md);
  }

  // Chatbot (very lightweight retrieval)
  const chatForm = document.getElementById('chat-form');
  const messages = document.getElementById('messages');

  chatForm.addEventListener('submit', e=>{
    e.preventDefault();
    const input = document.getElementById('chat-input');
    const q = input.value.trim();
    if(!q) return;
    addMessage(q,'user');
    input.value = '';
    // generate reply
    const reply = answerFromDocs(q, docs);
    setTimeout(()=>addMessage(reply,'bot'), 500 + Math.random()*800);
  });

  function addMessage(text, cls){
    const div = document.createElement('div');
    div.className = 'message '+(cls==='user'?'user':'bot');
    div.innerHTML = '<div>'+text+'</div>';
    messages.appendChild(div);
    messages.parentElement.scrollTop = messages.parentElement.scrollHeight;
  }

  function answerFromDocs(query, docs){
    // naive keyword match across paragraphs
    const qTokens = tokenize(query);
    let best = {score:0, text:'I could not find a clear answer in the prototype knowledge base. Please consult a medical professional for medical questions.' ,source:null};
    Object.keys(docs).forEach(k=>{
      const paragraphs = docs[k].split('\n\n');
      paragraphs.forEach(p=>{
        const tokens = tokenize(p);
        const score = overlapScore(qTokens, tokens);
        if(score>best.score){ best = {score, text:p, source:k}; }
      });
    });

    // Build an educational prototype reply
    const header = '<strong>Neurovia Assistant (educational prototype):</strong>';
    const disclaimer = '<div class="muted" style="font-size:12px;margin-top:6px">This assistant is an educational prototype. It does not replace medical professionals or emergency services.</div>';
    let body = best.text ? ('<div>'+best.text.replace(/\n/g,'<br>')+'</div>') : '<div>Sorry, I don\'t have information for that query.</div>';
    if(best.source){
      body += '<div style="margin-top:8px;font-size:13px">Source: <em>'+best.source+'</em></div>';
    }
    return header + body + disclaimer;
  }

  function tokenize(s){
    return s.toLowerCase().replace(/[.,\/#!$%\^&\*;:{}=\-_`~()\[\]"]/g,'').split(/\s+/).filter(Boolean);
  }
  function overlapScore(a,b){
    const setB = new Set(b);
    let c=0; a.forEach(t=>{ if(setB.has(t)) c++; });
    return c;
  }

  // --- Simulated EEG visualization + risk ---
  const canvas = document.getElementById('eeg-canvas');
  const ctx = canvas.getContext('2d');
  const W = canvas.width; const H = canvas.height;
  let offset = 0;
  const buffer = new Float32Array(W);
  for(let i=0;i<W;i++) buffer[i]=0;

  function generateSample(i,t){
    // baseline alpha rhythm-ish + noise
    const alpha = Math.sin((i+t*0.02)*0.12)*20;
    const beta = Math.sin((i+t*0.02)*0.8)*6;
    const noise = (Math.random()-0.5)*6;
    // occasional spike events
    const spike = (Math.random()<0.002) ? (Math.random()*120 + 80) : 0;
    return alpha + beta + noise + spike;
  }

  let lastAlertTime = 0;

  function draw(t){
    // shift buffer
    for(let i=0;i<W-1;i++) buffer[i]=buffer[i+1];
    buffer[W-1] = generateSample(offset,t);
    offset++;

    // clear
    ctx.fillStyle = 'rgba(10,14,20,1)';
    ctx.fillRect(0,0,W,H);

    // draw axis
    ctx.strokeStyle = 'rgba(255,255,255,0.03)';
    ctx.beginPath();
    ctx.moveTo(0,H/2);
    ctx.lineTo(W,H/2);
    ctx.stroke();

    // draw waveform
    ctx.lineWidth = 1.5;
    ctx.strokeStyle = 'rgba(110,231,183,0.95)';
    ctx.beginPath();
    for(let x=0;x<W;x++){
      const v = buffer[x];
      const y = H/2 + v*0.6;
      if(x===0) ctx.moveTo(x,y); else ctx.lineTo(x,y);
    }
    ctx.stroke();

    // compute a simple risk score based on recent spikes
    const recentMax = Math.max(...buffer.slice(W-200));
    const risk = Math.max(0, Math.min(100, Math.round((Math.abs(recentMax)-30))));
    updateRisk(risk);

    requestAnimationFrame(draw);
  }

  function updateRisk(score){
    const scoreEl = document.getElementById('risk-score');
    const indEl = document.getElementById('risk-indicator');
    const alertsEl = document.getElementById('alerts');
    const lastUpdated = document.getElementById('last-updated');

    scoreEl.textContent = score + '%';
    lastUpdated.textContent = new Date().toLocaleTimeString();

    alertsEl.querySelectorAll('li').forEach(n=>n.remove());

    if(score<30){
      indEl.textContent='LOW'; indEl.className='risk-indicator low';
      const li = document.createElement('li'); li.className='muted'; li.textContent='No current concerns (demo).'; alertsEl.appendChild(li);
    } else if(score<65){
      indEl.textContent='MED'; indEl.className='risk-indicator medium';
      const li = document.createElement('li'); li.textContent='Elevated activity detected — follow caregiver guidance.'; alertsEl.appendChild(li);
    } else {
      indEl.textContent='HIGH'; indEl.className='risk-indicator high';
      const li = document.createElement('li'); li.textContent='High-amplitude events detected. Alert caregivers immediately (demo).'; alertsEl.appendChild(li);
      // add repeated alert entries if threshold exceeded
      const now = Date.now();
      if(now - lastAlertTime > 5000){
        lastAlertTime = now;
        const a = document.createElement('li'); a.style.fontWeight='700'; a.textContent = 'AUTOMATED ALERT: Notify caregiver'; alertsEl.appendChild(a);
      }
    }
  }

  requestAnimationFrame(draw);

});
