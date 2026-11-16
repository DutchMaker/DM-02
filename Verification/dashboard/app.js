'use strict';
const $ = id => document.getElementById(id);
const esc = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const badge = status => `<span class="badge ${esc(status)}">${esc(status)}</span>`;
const link = path => '/build/' + path.split('/').map(encodeURIComponent).join('/');
let report, renderedRun;
function controlProfiles(check) {
  if(!check.profiles) return '';
  return `<div class="control-profiles"><table><caption>Counter phase / flag capture assumptions</caption><thead><tr><th>Profile</th><th>Cases disagreeing</th><th>PC mismatches</th><th>Nested calls passing</th></tr></thead><tbody>${check.profiles.map(p=>`<tr><td>${esc(p.phase)} / ${esc(p.flag_capture)}</td><td>${esc(p.failed)} / ${esc(p.cases)}</td><td>${esc(p.pc_mismatches)}</td><td>${esc(p.roundtrips_passed)} / ${esc(p.roundtrips)}</td></tr>`).join('')}</tbody></table></div>`;
}
function renderChecks() {
  const term=$('search').value.toLowerCase(), status=$('status').value;
  const checks=report.checks.filter(c=>(status==='all'||c.status===status)&&`${c.title} ${c.summary} ${c.id}`.toLowerCase().includes(term));
  $('checks').innerHTML=checks.map(c=>`<article class="check" id="check-${esc(c.id)}">${badge(c.status)}<div class="eyebrow">${esc(c.id)}</div><h3>${esc(c.title)}</h3><p>${esc(c.summary)}</p>${c.contract_validation?`<p class="contract-acceptance"><strong>MOD-03 functional contract: ${esc(c.requirement_status)}.</strong> ${esc(c.contract_validation.boundary)}</p>`:''}${c.limitation?`<p><strong>Scope:</strong> ${esc(c.limitation)}</p>`:''}${controlProfiles(c)}<div class="links">${(c.artifacts||[]).map(p=>`<a href="${link(p)}">${esc(p.split('/').pop())} ↗</a>`).join('')}</div><details><summary>Inspect structured evidence</summary><pre>${esc(JSON.stringify(c,null,2))}</pre></details></article>`).join('') || '<p class="empty">No checks match this filter.</p>';
}
function render() {
  $('run').textContent=`${(report.revision||report.target||'reference').toUpperCase()} · ${report.mode||'full execution'} · ${report.state.toUpperCase()} · ${new Date(report.finished_at||report.started_at).toLocaleString()} · ${Object.keys(report.source_hashes).length} source files fingerprinted`;
  let contractPanel=$('operating-contract');
  if(!contractPanel) {
    contractPanel=document.createElement('section');contractPanel.id='operating-contract';contractPanel.className='panel';
    $('milestones').before(contractPanel);
  }
  const contract=report.operating_contract;
  contractPanel.hidden=!contract;
  if(contract) {
    const clock=contract.clock;
    contractPanel.innerHTML=`<div class="eyebrow">${esc(contract.revision)} / SELECTED OPERATING CONTRACT</div><h2>${esc(clock.microcycle_nominal_hz/1000)} kHz microcycles · ${esc(clock.oscillator_nominal_hz/1000000)} MHz oscillator</h2><p>${esc(contract.supply.min_v)}–${esc(contract.supply.max_v)} V at IC pins · ${esc(contract.ambient.min_c)}–${esc(contract.ambient.max_c)} °C ambient. The preferred ${esc(clock.preferred_microcycle_hz/1000000)} MHz microcycle rate is optional.</p><p><strong>Physical qualification pending.</strong> Startup, reset, loaded edges and complete min/max timing still require acceptance. The historical requirements and R2 simulation inputs remain preserved.</p><div class="links"><a href="/Operating-contract.md">Operating contract and acceptance rules ↗</a><a href="/build/cp1/qualification-matrix.json">Specified qualification matrix ↗</a><a href="/build/cp1-readiness/">Clock-selection evidence ↗</a></div>`;
  }
  $('milestones').innerHTML=(report.milestones||[]).map(m=>`<article class="milestone">${badge(m.status)}<span class="number">0${m.number}</span><h3>${esc(m.title)}</h3><p>${esc(m.summary)}</p><details><summary>Acceptance gates</summary><ul>${(m.gates||[]).map(g=>`<li>${badge(g.status)} <a href="#check-${esc(g.gate)}">${esc(g.id)}</a>: ${esc(g.text)}</li>`).join('')}</ul></details></article>`).join('');
  const counts={}; report.checks.forEach(c=>counts[c.status]=(counts[c.status]||0)+1);
  $('counts').innerHTML=Object.entries(counts).map(([s,n])=>`<span>${n} ${badge(s)}</span>`).join('');
  renderChecks();
  const budget=report.checks.find(c=>c.id==='timing')?.budget;
  if(budget) {
    const p=budget.terms;
    const segments=[['Source',p.source_tco_ns,'#63dfdc'],['ROM',p.rom_access_ns,'#8ab8ec'],['Buffer',p.buffer_delay_ns,'#b5a4e5'],['Setup',p.setup_ns,'#ffd082'],['Jitter',p.clock_uncertainty_ns,'#ff9096']];
    $('timing').innerHTML=`<div class="budgetbar">${segments.map(([n,v,c])=>`<span title="${n}: ${v} ns" style="flex:${v};background:${c}">${v}</span>`).join('')}</div><div class="budgetlegend">${segments.map(([n,v])=>`${n} ${v}`).join(' + ')} = <strong>${budget.required_ns} ns</strong></div><div class="margin bad"><span>Documented · ${p.documented_phase_ns} ns</span><strong>${budget.documented_margin_ns} ns</strong></div><div class="margin good"><span>Candidate · ${p.candidate_phase_ns} ns</span><strong>+${budget.candidate_margin_ns} ns</strong></div>`;
    const counted=report.checks.find(c=>c.id==='clock-candidate')?.budget;
    if(counted) $('timing').innerHTML+=`<div class="margin ${counted.passing?'good':'bad'}"><span>C1 conditional lower bound · ${counted.phase_min_ns.toFixed(2)} ns</span><strong>${counted.pilot_margin_ns.toFixed(2)} ns</strong></div><p><a href="#check-clock-candidate">Counted-clock circuit, bounds and corner tests ↗</a></p>`;
  } else $('timing').textContent=report.checks.find(c=>c.id==='timing')?.summary||'Timing results unavailable.';
  const cases=report.checks.find(c=>c.id==='pilot')?.cases||[];
  $('mutations').innerHTML=cases.map(c=>`<tr><td>${esc(c.name)}</td><td>${esc(c.observed.join(', ')||'No violations')}</td><td>${badge(c.status)}</td></tr>`).join('');
  $('wavecase').innerHTML=cases.map(c=>`<option value="${esc(c.waveform)}">${esc(c.name)}</option>`).join('');
  drawWave();
  $('alu').innerHTML=(report.checks.find(c=>c.id==='alu')?.rows||[]).map(r=>`<details><summary><span class="${r.data_errors||r.flag_errors?'errors':'ok'}">${r.op.toString(16).padStart(2,'0').toUpperCase()} / ${esc(r.name)}</span><small>${r.data_errors.toLocaleString()} data · ${r.flag_errors.toLocaleString()} flags</small></summary><pre>${esc(JSON.stringify({data:r.data_examples,words:r.examples},null,2))}</pre></details>`).join('') || '<p>ALU results unavailable.</p>';
  $('risklist').innerHTML=report.risks.map(r=>`<article class="risk"><div class="id">${esc(r.id)}</div><div><h3>${esc(r.title)} ${badge(r.severity)}</h3><p>${esc(r.action)} <a href="#check-${esc(r.evidence)}" data-check="${esc(r.evidence)}">Evidence ↗</a></p></div></article>`).join('');
  $('trace').innerHTML=report.traceability.map(r=>`<tr><td>${esc(r.id)}</td><td>${esc(r.text)}</td><td>${badge(r.status)}</td></tr>`).join('');
  $('provenance').textContent=JSON.stringify({target:report.target,mode:report.mode,provenance:report.provenance,equivalence:report.equivalence,tools:report.tools,models:report.models,requirements:report.requirements,source_hashes:report.source_hashes},null,2);
}
async function drawWave() {
  const path=$('wavecase').value;
  if(!path) { $('waveform').textContent='Waveform unavailable.'; return; }
  $('vcd').href=link(path);
  try {
    const response=await fetch(link(path)); if(!response.ok) throw Error('Waveform file missing');
    const text=await response.text();
    if(path!==$('wavecase').value) return;
    const unit=text.match(/\$timescale\s+(\d+)\s*(s|ms|us|ns|ps|fs)\s+\$end/);
    if(!unit) throw Error('Unsupported VCD timescale');
    const scale=Number(unit[1])*({s:1e9,ms:1e6,us:1e3,ns:1,ps:1e-3,fs:1e-6}[unit[2]]);
    const names=['src_clk','source_q','rom_q','data_bus','dst_clk','destination'];
    const defs=[...text.matchAll(/\$var\s+\S+\s+(\d+)\s+(\S+)\s+(\S+).*?\$end/g)].map(m=>({width:+m[1],id:m[2],name:m[3],events:[]})).filter(d=>names.includes(d.name));
    let t=0;
    for(const line of text.split('\n')) {
      if(line.startsWith('#')) t=Number(line.slice(1))*scale;
      if(t>1000) break;
      const m=line.match(/^b([01xz]+)\s+(\S+)$/i)||line.match(/^([01xz])(\S+)$/i);
      if(m) for(const d of defs) if(d.id===m[2]) d.events.push([t,m[1]]);
    }
    defs.sort((a,b)=>names.indexOf(a.name)-names.indexOf(b.name));
    const x=t=>130+t*.78, width=940, height=defs.length*36+42;
    let svg=`<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(path)} first transfer waveform">`;
    for(let t=0;t<=1000;t+=100) svg+=`<line x1="${x(t)}" x2="${x(t)}" y1="20" y2="${height-20}" stroke="#293645"/><text x="${x(t)}" y="12" fill="#a5b5c5" font-size="9">${t} ns</text>`;
    defs.forEach((d,i)=>{
      const y=40+i*36; svg+=`<text x="0" y="${y+5}" fill="#a5b5c5" font-size="11" font-family="monospace">${esc(d.name)}</text>`;
      d.events.forEach(([t,v],j)=>{
        const end=d.events[j+1]?.[0]??1000, a=x(t), b=x(end), unknown=/[xz]/i.test(v), color=unknown?'#ffd082':'#63dfdc';
        if(d.width===1) {
          const level=v==='1'?y-10:y+10;
          const previous=(d.events[j-1]?.[1]??v)==='1'?y-10:y+10;
          svg+=`<path d="M${a},${previous} V${level} H${b}" stroke="${color}" fill="none"/>`;
        } else {
          svg+=`<path d="M${a},${y} l3,-10 H${Math.max(a+3,b-3)} L${b},${y} l-3,10 H${a+3} Z" stroke="${color}" fill="none"/>`;
          if(b-a>25) svg+=`<text x="${a+7}" y="${y+4}" fill="${color}" font-size="10" font-family="monospace">${unknown?esc(v):parseInt(v,2).toString(16).padStart(2,'0').toUpperCase()}</text>`;
        }
      });
    });
    $('waveform').innerHTML=svg+'</svg>';
  } catch(e) { $('waveform').textContent=e.message; }
}
async function refresh() {
  $('refresh').disabled=true;
  try {
    const response=await fetch('/api/state'); const data=await response.json();
    if(!response.ok) throw Error(data.error||'Cannot load report');
    report=data.report;
    const f=data.freshness;
    $('freshness').textContent=f.fresh?'● SOURCE & EVIDENCE CURRENT':`● ${f.state==='running'?'RUN IN PROGRESS':'STALE / INCOMPLETE EVIDENCE'}`;
    $('freshness').style.color=f.fresh?'var(--green)':'var(--amber)';
    $('notice').hidden=f.fresh;
    $('notice').textContent=f.fresh?'':`Results need a fresh run. ${f.changed.length} changed source files; ${(f.altered_evidence||[]).length} missing or altered evidence files. ${f.changed.slice(0,5).join(', ')}`;
    const key=JSON.stringify([report.started_at,report.finished_at,report.checks]);
    if(renderedRun!==key) { render(); renderedRun=key; }
  } catch(e) {
    $('freshness').textContent='● REPORT UNAVAILABLE'; $('notice').hidden=false; $('notice').textContent=e.message;
  } finally { $('refresh').disabled=false; }
}
$('refresh').addEventListener('click',refresh);
$('search').addEventListener('input',()=>report&&renderChecks());
$('status').addEventListener('change',()=>report&&renderChecks());
$('wavecase').addEventListener('change',drawWave);
$('risklist').addEventListener('click',event=>{if(event.target.dataset.check){$('search').value='';$('status').value='all';renderChecks();}});
refresh(); setInterval(refresh,20000);
