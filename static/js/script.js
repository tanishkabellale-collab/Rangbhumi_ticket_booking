// Shared script for countdowns and seat rendering / selection

// Countdown on index page
function startCountdowns(){
  document.querySelectorAll('.countdown').forEach(el=>{
    const seconds = parseInt(el.dataset.seconds)
    let s = seconds
    function tick(){
      if(s<=0){ el.textContent='Starts soon'; return }
      const d = Math.floor(s/86400)
      const h = Math.floor((s%86400)/3600)
      const m = Math.floor((s%3600)/60)
      const sec = s%60
      el.textContent = `${d}d ${h}h ${m}m ${sec}s`;
      s--
      setTimeout(tick,1000)
    }
    tick()
  })
}

// Seat page logic
function renderSeats(){
  const grid = document.getElementById('seat-grid');
  if(!grid) return;
  const rows = parseInt(grid.dataset.rows);
  const cols = parseInt(grid.dataset.cols);
  const rowLetters = ['A','B','C','D','E'];
  grid.innerHTML=''

  for(let r=0;r<rows;r++){
    for(let c=1;c<=cols;c++){
      const code = `${rowLetters[r]}${c}`;
      const div = document.createElement('div');
      div.classList.add('seat');
      div.dataset.code = code;
      div.textContent = code;
      const status = SEATS[code];
      if(status === 'booked') div.classList.add('booked');
      if(r+1 === VIP_ROWS[0]) div.classList.add('vip');
      grid.appendChild(div);
    }
  }

  // selection logic (click or drag)
  let selecting = false;
  let selected = new Set();

  function updateSidebar(){
    const listEl = document.getElementById('selected-list');
    if(selected.size===0) listEl.textContent='None';
    else listEl.textContent = Array.from(selected).join(', ');
    let total = 0;
    selected.forEach(code=>{ total += code.startsWith('A') ? VIP_PRICE : NORMAL_PRICE });
    document.getElementById('price').textContent = `Total: Rs ${total}`;
    document.getElementById('seats-input').value = Array.from(selected).join(',');
  }

  grid.addEventListener('mousedown', e=>{ selecting=true; if(e.target.classList.contains('seat') && !e.target.classList.contains('booked')) toggleSeat(e.target); })
  grid.addEventListener('mouseup', e=>{ selecting=false })
  grid.addEventListener('mouseleave', e=>{ selecting=false })
  grid.addEventListener('mouseover', e=>{ if(selecting && e.target.classList.contains('seat') && !e.target.classList.contains('booked')) toggleSeat(e.target) })

  function toggleSeat(el){
    const code = el.dataset.code;
    if(el.classList.contains('selected')){ el.classList.remove('selected'); selected.delete(code); playClick() }
    else { el.classList.add('selected'); selected.add(code); playClick() }
    updateSidebar()
  }

  // best-seat suggestion: choose first available center seat(s)
  document.getElementById('best-seat').addEventListener('click', ()=>{
    const candidates = Array.from(document.querySelectorAll('.seat')).filter(s=>!s.classList.contains('booked'));
    if(candidates.length===0) return;
    const colsNum = cols;
    const centerIndex = Math.floor(colsNum/2);
    candidates.sort((a,b)=>{
      const aParts = parseSeat(a.dataset.code);
      const bParts = parseSeat(b.dataset.code);
      const da = Math.abs(aParts.col - centerIndex) + Math.abs(aParts.row - 2);
      const db = Math.abs(bParts.col - centerIndex) + Math.abs(bParts.row - 2);
      return da-db;
    })
    document.querySelectorAll('.seat.selected').forEach(s=>s.classList.remove('selected'))
    selected.clear()
    const pick = candidates[0]; pick.classList.add('selected'); selected.add(pick.dataset.code); updateSidebar()
  })

  function parseSeat(code){
    const rowMap = {A:0,B:1,C:2,D:3,E:4};
    return {row: rowMap[code[0]], col: parseInt(code.slice(1))-1}
  }

  // small click sound
  function playClick(){
    try{
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const o = ctx.createOscillator();
      const g = ctx.createGain();
      o.type='sine'; o.frequency.value=800; g.gain.value=0.02
      o.connect(g); g.connect(ctx.destination); o.start(0); o.stop(ctx.currentTime+0.03)
    }catch(e){ }
  }

  updateSidebar()
}

// run on load
window.addEventListener('DOMContentLoaded', ()=>{
  startCountdowns();
  renderSeats();
})
