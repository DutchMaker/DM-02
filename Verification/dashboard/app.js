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
  let ioPanel=$('io-contract');
  if(!ioPanel) {
    ioPanel=document.createElement('section');ioPanel.id='io-contract';ioPanel.className='panel';
    $('milestones').before(ioPanel);
  }
  const io=report.io_contract;
  let mechanicalPanel=$('mechanical-contract');
  if(!mechanicalPanel) {
    mechanicalPanel=document.createElement('section');mechanicalPanel.id='mechanical-contract';mechanicalPanel.className='panel';
    $('milestones').before(mechanicalPanel);
  }
  const mechanical=report.mechanical_contract;
  mechanicalPanel.hidden=!mechanical;
  if(mechanical) mechanicalPanel.innerHTML=`<div class="eyebrow">${esc(mechanical.revision)} / OWNER-SELECTED GEOMETRY</div><h2>Four 250 × 200 mm CPU cards · eight positions</h2><p>270 × 270 mm active backplane · 30 mm pitch · four layers. Draft connector plan checks 1,242 contacts against native R2 boundaries.</p><p><strong>Connector fit and physical qualification pending.</strong> The memory card uses 109 of 112 signal positions, including the new live-address/read interface.</p><div class="links"><a href="/Mechanical-contract.md">Selected mechanical contract ↗</a><a href="/Connector-plan.md">Connector semantics and candidates ↗</a><a href="/build/cp1-connectors/">Contact tables and checks ↗</a></div>`;
  ioPanel.hidden=!io;
  if(io) ioPanel.innerHTML=`<div class="eyebrow">${esc(io.scope.revision)} / FIRST MACHINE · ${esc(io.revision)} / LOGICAL IO</div><h2>Text-first computer with peripheral expansion</h2><p>Autonomous ROM boot · stack/backplane · local reset/run/halt/step · separate ESP32/LCD debugger. Computer and peripheral cards remain DIP/through-hole.</p><p><strong>Physical interface implementation pending.</strong> The current output connector carries a registered write address. Expansion reads need a separate live address, qualified selection and buffered return path.</p><div class="links"><a href="/IO-interface.md">Scope, address map and handshake ↗</a><a href="/build/cp1/io-contract-check.json">Logical checks and native connector audit ↗</a></div>`;
  $('milestones').innerHTML=(report.milestones||[]).map(m=>`<article class="milestone">${badge(m.status)}<span class="number">0${m.number}</span><h3>${esc(m.title)}</h3><p>${esc(m.summary)}</p><details><summary>Acceptance gates</summary><ul>${(m.gates||[]).map(g=>`<li>${badge(g.status)} <a href="#check-${esc(g.gate)}">${esc(g.id)}</a>: ${esc(g.text)}</li>`).join('')}</ul></details></article>`).join('');
  let bridgePanel=$('io-bridge');
  if(!bridgePanel) {
    bridgePanel=document.createElement('section');bridgePanel.id='io-bridge';bridgePanel.className='panel';
    $('milestones').before(bridgePanel);
  }
  const bridge=report.io_bridge;
  bridgePanel.hidden=!bridge;
  if(bridge) bridgePanel.innerHTML=`<div class="eyebrow">${esc(bridge.revision)} / SEPARATE CIRCUIT CANDIDATE</div><h2>Four private I/O returns · ${esc(bridge.dip_count)} added DIP packages</h2><p>Four delay profiles: 70,020 read cases and 256 writes each. Four injected faults detected. Native bindings cover 17 memory-card extensions and 384 peripheral contacts.</p><p><strong>CPU integration and physical qualification pending.</strong> Internal load screening passes. The conditional 379 ns return-path sum excludes the endpoint and full CPU path; minimum delays and actual loading/edges remain unqualified.</p><div class="links"><a href="/IO-bridge.md">Circuit and evidence limits ↗</a><a href="/build/cp1-bridge/">Bridge candidate evidence ↗</a><a href="/build/cp1-bridge/boundary-audit.json">Native boundary bindings ↗</a></div>`;
  let cpuIOPanel=$('io-cpu');
  if(!cpuIOPanel) {
    cpuIOPanel=document.createElement('section');cpuIOPanel.id='io-cpu';cpuIOPanel.className='panel';
    $('milestones').before(cpuIOPanel);
  }
  cpuIOPanel.hidden=!report.io_cpu;
  if(report.io_cpu) cpuIOPanel.innerHTML=`<div class="eyebrow">CP1-BI1 / CPU–BRIDGE DIAGNOSTIC</div><h2>29 passing profiles · endpoint latency boundary found</h2><p>The fetched diagnostic checks 14 echoed bytes through the complete CPU/bridge path. Three connection faults were detected. At 500 kHz, a 160 ns endpoint fixture passed; 200 ns failed setup reserve and 400 ns returned incorrect data. The 400 ns fixture passed at diagnostic 250 kHz.</p><p><strong>Conditional simulation with preloaded memory and behavioral endpoints.</strong> Real text circuitry, autonomous boot with BR1 and full physical timing remain open.</p><div class="links"><a href="/IO-CPU-integration.md">Diagnostic method and limits ↗</a><a href="/build/cp1-io-cpu/">Passing and failed runs ↗</a></div>`;
  let textPanel=$('text-card');
  if(!textPanel) {
    textPanel=document.createElement('section');textPanel.id='text-card';textPanel.className='panel';
    $('milestones').before(textPanel);
  }
  textPanel.hidden=!report.text_card;
  if(report.text_card) textPanel.innerHTML=`<div class="eyebrow">CP1-TX1 / SERIAL TEXT CANDIDATE</div><h2>37 DIP ICs · all 256 bytes decoded</h2><p>Six standalone profiles passed mailbox, framing, overrun and reset checks; four injected faults were detected. Six CPU/bridge profiles passed, including absent-device handling. The five-byte TX1 transcript finished after CPU HALT.</p><p>Local 4 MHz oscillator, 9600-baud terminal setting, 5 V TTL TX/GND header. <strong>Physical terminal output and clock-domain crossing qualification remain open.</strong> The CPU diagnostic uses preloaded memory; R2 remains the accepted circuit.</p><div class="links"><a href="/Text-card.md">Circuit, timing and qualification scope ↗</a><a href="/build/cp1-text/">Native schematic and evidence ↗</a></div>`;
  let bootPanel=$('text-boot');
  if(!bootPanel) {
    bootPanel=document.createElement('section');bootPanel.id='text-boot';bootPanel.className='panel';
    $('milestones').before(bootPanel);
  }
  bootPanel.hidden=!report.text_boot;
  if(report.text_boot) bootPanel.innerHTML=`<div class="eyebrow">CP1-TB1 / ROM-ONLY SERIAL STARTUP</div><h2>Six startup profiles · three loader faults detected</h2><p>From reset PC zero, an 806-byte ROM loader deposits the 160-byte text diagnostic into poisoned SRAM at $4000. All six runs emit TX1 CR LF; the serializer finishes after CPU HALT. The architectural oracle checks all 160 writes and 322 loader instructions.</p><p>Four SRAM poison seeds, maximum/zero/mixed delay profiles and a 25 ms reset guard. Lowest sampled CPU setup: 81.5 ns. <strong>Physical startup and terminal/CDC qualification remain open.</strong> R2 remains the accepted circuit.</p><div class="links"><a href="/Text-boot.md">ROM image, method and scope ↗</a><a href="/build/cp1-text-boot/">Startup and mutation evidence ↗</a></div>`;
  let assemblyPanel=$('native-assembly');
  if(!assemblyPanel) {
    assemblyPanel=document.createElement('section');assemblyPanel.id='native-assembly';assemblyPanel.className='panel';
    $('milestones').before(assemblyPanel);
  }
  assemblyPanel.hidden=!report.native_assembly;
  if(report.native_assembly) assemblyPanel.innerHTML=`<div class="eyebrow">CP1-NA1 / NATIVE ASSEMBLY CANDIDATE</div><h2>270 DIP ICs · 6,491 physical pins checked</h2><p>A checked-in KiCad hierarchy joins R2, MQ1/BR1 and TX1. The independent export matches 1,762 net groups and checks component values, pin metadata and fitted flags. Three wiring mutations are detected. The first iteration's library-ID collision is preserved and rejected.</p><p>134 explicit TB1 boundary bindings checked; 58 logical boundary markers are excluded from BOM and board transfer. <strong>Production-source and physical qualification remain open.</strong> R2 remains accepted; the existing TB1 simulation is reused by static pin/port equivalence.</p><div class="links"><a href="/Native-assembly.md">Native source, verification and scope ↗</a><a href="/build/cp1-native-assembly/">Hierarchy views and evidence ↗</a></div>`;
  let connectorPanel=$('connector-assembly');
  if(!connectorPanel) {
    connectorPanel=document.createElement('section');connectorPanel.id='connector-assembly';connectorPanel.className='panel';
    $('milestones').before(connectorPanel);
  }
  connectorPanel.hidden=!report.connector_assembly;
  if(report.connector_assembly) connectorPanel.innerHTML=`<div class="eyebrow">CP1-CA1 / CPU CONNECTOR ASSEMBLY</div><h2>768 mating contacts · four separate CPU net domains</h2><p>Sixteen DIN96 candidates replace 58 logical boundary markers. The native export checks 7,324 pins and all 17 memory extensions. Applying the declared mating pairs preserves NA1's functional graph exactly.</p><p>Four wiring mutations detected. A shared-global-label bypass passes the mated graph but fails the separate-card check. <strong>Physical connector and production qualification remain open.</strong> R2 remains accepted; this is static connectivity evidence.</p><div class="links"><a href="/Connector-assembly.md">Contact mapping, isolation and scope ↗</a><a href="/build/cp1-connector-assembly/">Native hierarchy and mutation evidence ↗</a></div>`;
  let loadsPanel=$('link-loads');
  if(!loadsPanel) {
    loadsPanel=document.createElement('section');loadsPanel.id='link-loads';loadsPanel.className='panel';
    $('milestones').before(loadsPanel);
  }
  loadsPanel.hidden=!report.link_loads;
  if(report.link_loads) loadsPanel.innerHTML=`<div class="eyebrow">CP1-LL1 / WHOLE-LINK LOAD INVENTORY</div><h2>7,324 pins · 1,708 driver scenarios</h2><p>All fitted contacts and pull resistors counted. MAR bits 14–15 reach 48 pF before wiring, or 53 pF with the old 5 pF allowance. Eight DATA lines exceed the HCT245 disable fixture; eight SRAM lines exceed its output-release fixture.</p><p>Both oscillators have 5 pF remaining after the input-capacitance subtotal. <strong>Complete physical loads remain unknown.</strong> Manufacturer conditions, allocation-only terms and socket/connector/routing/cable/probe gaps are recorded per path.</p><div class="links"><a href="/Link-loads.md">Method and electrical findings ↗</a><a href="/build/cp1-link-loads/">Pin matrix and manufacturer evidence ↗</a></div>`;
  let marPanel=$('mar-distribution');
  if(!marPanel) {
    marPanel=document.createElement('section');marPanel.id='mar-distribution';marPanel.className='panel';
    $('milestones').before(marPanel);
  }
  marPanel.hidden=!report.mar_distribution;
  if(report.mar_distribution) marPanel.innerHTML=`<div class="eyebrow">CP1-MD1 / BUFFERED MEMORY ADDRESS CANDIDATE</div><h2>MAR loading reduced to 30 pF per bit</h2><p>Two added DIP buffers isolate the memory-side address loads. Their outputs drive 24–28 pF. Explicit socket/routing/probe allocations leave at least 5 pF planning margin on raw MAR paths and 7 pF on buffered paths.</p><p>Four ROM/text startup profiles and the full memory exercise pass. All 65,536 address words checked; swapped-address and disabled-buffer faults detected. <strong>Physical loads and timing remain unqualified.</strong> MD1 is a separate 272-DIP candidate; R2 remains accepted.</p><div class="links"><a href="/MAR-distribution.md">Topology, budgets and affected checks ↗</a><a href="/build/cp1-mar-distribution/">Native source and simulation evidence ↗</a></div>`;
  let releasePanel=$('release-requirements');
  if(!releasePanel) {
    releasePanel=document.createElement('section');releasePanel.id='release-requirements';releasePanel.className='panel';
    $('milestones').before(releasePanel);
  }
  releasePanel.hidden=!report.release_requirements;
  if(report.release_requirements) releasePanel.innerHTML=`<div class="eyebrow">CP1-RR1 / DATA AND SRAM RELEASE</div><h2>Driver ownership and release requirements traced</h2><p>DATA has one driver; the private SRAM bus has two. Native OE/WE paths, 8,192 control states and four instrumented ROM/text boots checked. Same-data contention, early capture and late-release faults detected.</p><p>Smallest sampled SRAM control gaps: 4,981 ns read-to-write and 4,947.5 ns write-to-read. <strong>Physical release and hold remain unqualified.</strong> A 48-driver measurement specification covers actual loads and the OC1 voltage/temperature grid.</p><div class="links"><a href="/Release-requirements.md">Paths, assumptions and measurement procedure ↗</a><a href="/build/cp1-release/">Experiments and event logs ↗</a></div>`;
  const counts={}; report.checks.forEach(c=>counts[c.status] = (counts[c.status]||0)+1);
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
