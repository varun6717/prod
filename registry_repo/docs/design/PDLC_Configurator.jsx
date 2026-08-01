import React, { useState, useEffect, useMemo } from "react";

/* ============================================================
   PDLC — Run Configurator (TASK-001 patterns + TASK-002 screens)
   Styled to the telemetry design system: dark default · cyan
   structure · electric-blue typed values · HUD brackets.
   UI collects config ONLY and emits UI_INPUT.yaml (§3.1, FR-XS-02).
   ============================================================ */

const STYLE = `
.pdlc{
  --bg:#0a0b0d; --panel:#0e1012; --panel-2:#121517;
  --line:rgba(232,236,239,.08); --line-strong:rgba(232,236,239,.16);
  --ink:#e2e6e9; --ink-soft:rgba(226,230,233,.76); --ink-mute:rgba(226,230,233,.50); --ink-dim:rgba(226,230,233,.30);
  --accent:#3ee6ff; --accent-contrast:#06141a; --accent-dim:rgba(62,230,255,.12); --accent-faint:rgba(62,230,255,.05);
  --accent-soft:rgba(62,230,255,.55);
  --val:#3ee6ff;                       /* typed-value color (dark) */
  --grid:rgba(232,236,239,.028); --hover:rgba(232,236,239,.05); --focus:rgba(232,236,239,.45); --edge:rgba(232,236,239,.32);
  --rate:#fbbf24;
  --mono:'JetBrains Mono','Consolas',ui-monospace,monospace;
  --sans:'General Sans','Segoe UI',-apple-system,sans-serif;
  background:var(--bg); color:var(--ink); font-family:var(--sans);
  background-image:linear-gradient(var(--grid) 1px,transparent 1px),linear-gradient(90deg,var(--grid) 1px,transparent 1px);
  background-size:48px 48px; min-height:640px; border:1px solid var(--line-strong);
}
.pdlc[data-theme="light"]{
  --bg:#eef1f3; --panel:#fafbfb; --panel-2:#ffffff;
  --line:rgba(15,19,23,.14); --line-strong:rgba(15,19,23,.24);
  --ink:#0d1116; --ink-soft:rgba(13,17,22,.82); --ink-mute:rgba(13,17,22,.60); --ink-dim:rgba(13,17,22,.38);
  --accent:#0e7490; --accent-contrast:#ffffff; --accent-dim:rgba(14,116,144,.10); --accent-faint:rgba(14,116,144,.06);
  --accent-soft:rgba(14,116,144,.5);
  --val:#1d4ed8;                       /* electric blue — pops on light */
  --grid:rgba(15,19,23,.05); --hover:rgba(15,19,23,.05); --focus:rgba(15,19,23,.45); --edge:rgba(15,19,23,.44);
  --rate:#b45309;
}
.pdlc *{box-sizing:border-box;}
.mono{font-family:var(--mono);}
.micro{font-family:var(--mono);font-size:9.5px;font-weight:500;letter-spacing:.2em;text-transform:uppercase;color:var(--ink-mute);}

.pdlc-hd{position:sticky;top:0;z-index:5;display:flex;align-items:center;justify-content:space-between;
  height:52px;padding:0 20px;background:var(--panel);border-bottom:1px solid var(--line-strong);}
.ident{display:flex;align-items:center;gap:10px;}
.ident-box{width:22px;height:22px;border:1px solid var(--accent);box-shadow:0 0 10px var(--accent-dim);
  display:flex;align-items:center;justify-content:center;color:var(--accent);font-family:var(--mono);font-size:8.5px;font-weight:700;}
.ident-title{font-family:var(--mono);font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:var(--ink-soft);}
.hd-right{display:flex;align-items:center;gap:14px;}
.clock{font-family:var(--mono);font-size:10.5px;color:var(--ink-mute);letter-spacing:.1em;}
.themebtn{font-family:var(--mono);font-size:9.5px;letter-spacing:.1em;color:var(--ink-mute);background:transparent;
  border:1px solid var(--line);padding:5px 9px;cursor:pointer;text-transform:uppercase;}
.themebtn:hover{color:var(--ink);border-color:var(--focus);}

.pdlc-body{display:grid;grid-template-columns:248px 1fr;min-height:588px;}
.nav{border-right:1px solid var(--line);background:var(--panel);padding:14px 0;}
.navhint{padding:0 18px 12px;}
.navitem{position:relative;display:flex;align-items:center;gap:11px;padding:11px 18px;cursor:pointer;border:none;
  background:transparent;width:100%;text-align:left;transition:background 120ms linear;}
.navitem:hover{background:var(--hover);}
.navitem.on{background:var(--accent-faint);}
.navitem.on::before{content:"";position:absolute;left:0;top:0;bottom:0;width:2px;background:var(--accent);}
.navnum{font-family:var(--mono);font-size:11px;color:var(--ink-mute);width:14px;flex-shrink:0;}
.navitem.on .navnum{color:var(--accent);}
.navled{width:7px;height:7px;flex-shrink:0;background:var(--ink-dim);}
.navitem.on .navled{background:var(--accent);box-shadow:0 0 6px var(--accent);}
.navlabel{flex:1;font-size:12.5px;color:var(--ink-soft);}
.navitem.on .navlabel{color:var(--ink);font-weight:500;}
.navbadge{font-family:var(--mono);font-size:8px;letter-spacing:.12em;padding:2px 6px;border:1px solid var(--line-strong);
  color:var(--ink-mute);text-transform:uppercase;}
.navbadge.action{color:var(--accent);border-color:var(--accent-soft);}

.main{padding:30px 34px;overflow:auto;}
.crumb{font-family:var(--mono);font-size:9.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--ink-dim);margin-bottom:8px;}
.h{font-size:22px;font-weight:600;letter-spacing:-.01em;margin:0 0 6px;}
.driven{display:inline-flex;align-items:center;gap:7px;font-family:var(--mono);font-size:9px;letter-spacing:.12em;
  text-transform:uppercase;color:var(--ink-mute);border:1px solid var(--line);padding:3px 9px;margin-bottom:18px;}

.rule{display:flex;align-items:center;gap:12px;margin:28px 0 16px;}
.rule::after{content:"";flex:1;height:1px;background:var(--line);}
.rule-i{font-family:var(--mono);font-size:10px;color:var(--accent);letter-spacing:.1em;}
.rule-l{font-family:var(--mono);font-size:10px;font-weight:500;letter-spacing:.22em;text-transform:uppercase;color:var(--ink-mute);white-space:nowrap;}

.field{margin-bottom:18px;max-width:580px;}
.flabel{display:block;font-family:var(--mono);font-size:9.5px;font-weight:500;letter-spacing:.16em;text-transform:uppercase;color:var(--ink-mute);margin-bottom:7px;}
.fhint{font-size:11px;color:var(--ink-dim);margin-top:6px;}
.tinput{display:flex;align-items:center;gap:8px;padding:9px 12px;background:var(--panel-2);border:1px solid var(--line);transition:border-color 140ms linear;}
.tinput:focus-within{border-color:var(--accent);}
.tinput input,.tinput textarea,.tinput select{flex:1;background:transparent;border:none;outline:none;color:var(--val);
  font-family:var(--mono);font-size:12.5px;font-weight:500;letter-spacing:.02em;width:100%;resize:vertical;}
.tinput input::placeholder,.tinput textarea::placeholder{color:var(--ink-dim);-webkit-text-fill-color:var(--ink-dim);font-weight:400;}
.tinput select option{background:var(--panel-2);color:var(--ink);}
.tinput .x{background:transparent;border:none;color:var(--ink-mute);cursor:pointer;font-size:15px;line-height:1;padding:0 2px;}
.tinput .x:hover{color:var(--rate);}

.tseg{display:inline-flex;border:1px solid var(--edge);overflow:hidden;}
.tseg button{padding:8px 18px;font-family:var(--mono);font-size:10.5px;font-weight:500;letter-spacing:.14em;text-transform:uppercase;
  color:var(--ink-mute);cursor:pointer;background:transparent;border:none;border-right:1px solid var(--line);}
.tseg button:last-child{border-right:none;}
.tseg button.active{color:var(--accent-contrast);background:var(--accent);font-weight:600;}

.chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px;}
.chip{display:inline-flex;align-items:center;gap:7px;padding:4px 8px;font-family:var(--mono);font-size:10px;font-weight:600;
  letter-spacing:.08em;color:var(--val);border:1px solid currentColor;}
.chip button{background:transparent;border:none;color:var(--ink-mute);cursor:pointer;font-size:12px;line-height:1;padding:0;}
.chip::before{content:"";width:5px;height:5px;background:currentColor;}

.srow{border:1px solid var(--line);background:var(--panel);margin-bottom:12px;}
.srow-hd{display:flex;align-items:center;justify-content:space-between;padding:11px 14px;border-bottom:1px solid var(--line);}
.srow-type{display:flex;align-items:center;gap:9px;}
.srow-name{font-family:var(--mono);font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--ink-soft);}
.srow-tag{font-family:var(--mono);font-size:8.5px;letter-spacing:.12em;padding:2px 7px;border:1px solid var(--line-strong);color:var(--ink-mute);text-transform:uppercase;}
.srow-tag.live{color:var(--accent);border-color:var(--accent-soft);}
.srow-body{padding:13px 14px;}
.srow-item{display:grid;gap:10px;padding-bottom:12px;margin-bottom:12px;border-bottom:1px dashed var(--line);}
.srow-item:last-of-type{border-bottom:none;margin-bottom:8px;padding-bottom:0;}
.addbtn{font-family:var(--mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--accent);background:transparent;
  border:1px dashed var(--accent-soft);padding:6px 12px;cursor:pointer;}
.addbtn:hover{background:var(--accent-faint);}
.authref{font-family:var(--mono);font-size:10px;color:var(--ink-dim);letter-spacing:.05em;margin-top:12px;}
.authref b{color:var(--ink-mute);font-weight:500;}

.gen-grid{display:grid;grid-template-columns:1fr 1fr;gap:26px;align-items:start;}
.btn-gen{display:inline-flex;align-items:center;gap:9px;padding:11px 20px;font-family:var(--mono);font-size:11px;font-weight:600;
  letter-spacing:.14em;text-transform:uppercase;color:var(--accent-contrast);background:var(--accent);border:1px solid var(--accent);cursor:pointer;}
.btn-gen:hover{opacity:.88;}
.btn-ghost{display:inline-flex;align-items:center;gap:8px;padding:11px 18px;font-family:var(--mono);font-size:11px;font-weight:500;
  letter-spacing:.12em;text-transform:uppercase;color:var(--ink-soft);background:transparent;border:1px solid var(--edge);cursor:pointer;}
.btn-ghost:hover{color:var(--ink);border-color:var(--focus);}
.btn-ghost:disabled{opacity:.55;cursor:not-allowed;}

.yaml{background:#07090b;border:1px solid var(--line);padding:16px;font-family:var(--mono);font-size:11px;line-height:1.7;
  white-space:pre;overflow:auto;max-height:540px;}
.yaml .yk{color:rgba(232,236,239,.58);}
.yaml .yv{color:#3ee6ff;}
.yaml .ys{color:rgba(62,230,255,.55);}
.yaml .yc{color:rgba(232,236,239,.34);font-style:italic;}

.callout{border:1px solid var(--accent-soft);background:var(--accent-faint);padding:13px 15px;margin:0 0 22px;max-width:680px;}
.callout .ct{font-family:var(--mono);font-size:9px;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);margin-bottom:5px;}
.callout p{margin:0;font-size:12.5px;color:var(--ink-soft);line-height:1.55;}
.gesture{border:1px solid var(--line-strong);background:var(--panel-2);padding:14px 16px;margin-top:18px;max-width:560px;}
.gesture code{font-family:var(--mono);font-size:11.5px;color:var(--val);}
.gesture ol.steps{margin:0;padding-left:18px;}
.gesture ol.steps li{font-size:12px;color:var(--ink-soft);line-height:1.65;margin-bottom:9px;}
.gesture ol.steps li:last-child{margin-bottom:0;}
.cmd{display:inline-block;font-family:var(--mono);font-size:11.5px;font-weight:600;color:var(--val);background:var(--accent-faint);border:1px solid var(--accent-soft);padding:1px 7px;letter-spacing:.02em;}
.gesture b{color:var(--ink);font-weight:600;}
.led-blink{animation:pblink 1.1s steps(2,start) infinite;}
@keyframes pblink{to{visibility:hidden;}}
`;

function useUtcClock(){
  const [n,setN]=useState(()=>new Date());
  useEffect(()=>{const t=setInterval(()=>setN(new Date()),1000);return()=>clearInterval(t);},[]);
  const p=(x)=>String(x).padStart(2,"0");
  return `${p(n.getUTCHours())}:${p(n.getUTCMinutes())}:${p(n.getUTCSeconds())} UTC`;
}

const TABS=[
  {n:"0",label:"IDE Repo Initializer",badge:"USER"},
  {n:"1",label:"Domain",badge:"USER"},
  {n:"2",label:"Project & Requirement",badge:"USER"},
  {n:"3",label:"Artifact Inventory",badge:"USER"},
  {n:"4",label:"Generator",badge:"ACTION"},
];
const DOMAINS=[{key:"payment_brand",label:"PBI — Payment Brand Implementations"}];

function Field({label,hint,children}){
  return (<div className="field"><label className="flabel">{label}</label>{children}{hint&&<div className="fhint">{hint}</div>}</div>);
}
function Text({value,onChange,placeholder,area=false}){
  return (<div className="tinput">
    {area?<textarea rows={2} value={value} placeholder={placeholder} onChange={e=>onChange(e.target.value)}/>
         :<input value={value} placeholder={placeholder} onChange={e=>onChange(e.target.value)}/>}
  </div>);
}

export default function PDLCConfigurator(){
  const [theme,setTheme]=useState("dark");
  const [tab,setTab]=useState(0);
  const clock=useUtcClock();
  const [generated,setGenerated]=useState(false);
  const [launched,setLaunched]=useState(false);

  const [f,setF]=useState({
    working_path:"", domain:"payment_brand", runtime_tool:"copilot",
    project_name:"", application_name:"", lob:"", requestor:"", requestor_sid:"",
    intent:"", scope_hints:["routing"], stakeholders:[], compliance_deadline:"",
    pdf:[{url:""}], code:[{seal:"",url:""}], confluence:[{url:""}], lucid:[{url:""}],
    score_threshold:"85",
  });
  const set=(k,v)=>setF(p=>({...p,[k]:v}));
  const addChip=(k,v)=>{v=v.trim();if(v&&!f[k].includes(v))set(k,[...f[k],v]);};
  const rmChip=(k,v)=>set(k,f[k].filter(x=>x!==v));
  const setItem=(sk,i,key,val)=>setF(p=>{const a=[...p[sk]];a[i]={...a[i],[key]:val};return{...p,[sk]:a};});
  const addItem=(sk,blank)=>setF(p=>({...p,[sk]:[...p[sk],blank]}));
  const rmItem=(sk,i)=>setF(p=>({...p,[sk]:p[sk].filter((_,j)=>j!==i)}));
  const [chipDraft,setChipDraft]=useState("");
  const [stkDraft,setStkDraft]=useState("");

  const domainLabel=(DOMAINS.find(d=>d.key===f.domain)||DOMAINS[0]).label;
  const yaml=useMemo(()=>buildYaml(f,generated),[f,generated]);

  return (
    <div className="pdlc" data-theme={theme}>
      <style>{STYLE}</style>

      <div className="pdlc-hd">
        <div className="ident">
          <div className="ident-box">PDLC</div>
          <span className="ident-title">Run Configurator</span>
        </div>
        <div className="hd-right">
          <span className="clock">{clock}</span>
          <button className="themebtn" onClick={()=>setTheme(t=>t==="dark"?"light":"dark")}>
            {theme==="dark"?"◐ Light":"◑ Dark"}
          </button>
        </div>
      </div>

      <div className="pdlc-body">
        <nav className="nav">
          <div className="navhint micro">Run Setup · collects config only</div>
          {TABS.map((t,i)=>(
            <button key={t.n} className={"navitem"+(tab===i?" on":"")} onClick={()=>setTab(i)}>
              <span className="navnum">{t.n}</span>
              <span className="navled"/>
              <span className="navlabel">{t.label}</span>
              <span className={"navbadge"+(t.badge==="ACTION"?" action":"")}>{t.badge}</span>
            </button>
          ))}
        </nav>

        <main className="main">
          {tab===0 && <>
            <div className="crumb">PDLC · Run Setup · Stage 0</div>
            <h1 className="h">IDE Repo Initializer</h1>
            <span className="driven">▣ User-driven</span>
            <div className="callout"><div className="ct">Objective</div>
              <p>Set the working directory the run is built in. Generate lays the hydrated core, the chosen overlay,
                and <span className="mono" style={{color:"var(--val)"}}>UI_INPUT.yaml</span> here, ready to open in your IDE.</p></div>
            <Field label="Folder Location Path" hint="→ working_path · e.g. /work/pbi/SEAL-12345-routing">
              <Text value={f.working_path} onChange={v=>set("working_path",v)} placeholder="/work/pbi/SEAL-12345-routing"/>
            </Field>
          </>}

          {tab===1 && <>
            <div className="crumb">PDLC · Run Setup · Stage 1</div>
            <h1 className="h">Domain</h1>
            <span className="driven">▣ User-driven</span>
            <div className="callout"><div className="ct">Objective</div>
              <p>Pick the intake domain. The selection chooses the profiles, templates, adapter, and vocabulary
                hydrated for the run, and is emitted as the <span className="mono" style={{color:"var(--val)"}}>domain</span> key.</p></div>
            <Field label="Intake Domain Type" hint={`emits domain: ${f.domain}`}>
              <div className="tinput">
                <select value={f.domain} onChange={e=>set("domain",e.target.value)}>
                  {DOMAINS.map(d=><option key={d.key} value={d.key}>{d.label}</option>)}
                </select>
              </div>
            </Field>
            <div className="fhint" style={{maxWidth:560}}>Selected: <span style={{color:"var(--val)"}}>{domainLabel}</span> → key <span style={{color:"var(--val)"}} className="mono">{f.domain}</span></div>
          </>}

          {tab===2 && <>
            <div className="crumb">PDLC · Run Setup · Stage 2</div>
            <h1 className="h">Project &amp; Requirement</h1>
            <span className="driven">▣ User-driven</span>
            <div className="callout"><div className="ct">Objective</div>
              <p>Capture project identity and a short requirement seed. Business case, functional requirements, and risks
                are BRD sections the author produces from this seed — not entered here.</p></div>

            <div className="rule"><span className="rule-i">A</span><span className="rule-l">Project Metadata</span></div>
            <Field label="Project Name" hint="→ project_metadata.project_name (also seeds frame.title)"><Text value={f.project_name} onChange={v=>set("project_name",v)} placeholder="Discover Brand Routing"/></Field>
            <Field label="Application Name" hint="→ project_metadata.application_name"><Text value={f.application_name} onChange={v=>set("application_name",v)} placeholder="MerchantRoutingSvc"/></Field>
            <Field label="Line of Business" hint="→ project_metadata.line_of_business"><Text value={f.lob} onChange={v=>set("lob",v)} placeholder="Merchant Services"/></Field>
            <Field label="Requestor" hint="→ project_metadata.requestor"><Text value={f.requestor} onChange={v=>set("requestor",v)} placeholder="Varun Munjal"/></Field>
            <Field label="Requestor SID" hint="→ project_metadata.requestor_sid (user / LDAP id)"><Text value={f.requestor_sid} onChange={v=>set("requestor_sid",v)} placeholder="vmunjal"/></Field>

            <div className="rule"><span className="rule-i">B</span><span className="rule-l">Requirement Frame · BRD seed</span></div>
            <Field label="Intent" hint="→ frame.intent — one line: what we're implementing"><Text area value={f.intent} onChange={v=>set("intent",v)} placeholder="Implement Discover as a routable card brand end-to-end"/></Field>
            <Field label="Compliance Deadline" hint="→ frame.key_dates.compliance_deadline"><Text value={f.compliance_deadline} onChange={v=>set("compliance_deadline",v)} placeholder="2026-09-30"/></Field>
            <Field label="Scope Hints" hint="→ frame.scope_hints[] · Enter to add">
              <div className="tinput"><input value={chipDraft} placeholder="add a scope hint…"
                onChange={e=>setChipDraft(e.target.value)}
                onKeyDown={e=>{if(e.key==="Enter"){addChip("scope_hints",chipDraft);setChipDraft("");}}}/></div>
              <div className="chips">{f.scope_hints.map(c=><span key={c} className="chip">{c}<button onClick={()=>rmChip("scope_hints",c)}>×</button></span>)}</div>
            </Field>
            <Field label="Stakeholders" hint="→ frame.stakeholders[] · optional · Enter to add">
              <div className="tinput"><input value={stkDraft} placeholder="add a stakeholder…"
                onChange={e=>setStkDraft(e.target.value)}
                onKeyDown={e=>{if(e.key==="Enter"){addChip("stakeholders",stkDraft);setStkDraft("");}}}/></div>
              <div className="chips">{f.stakeholders.map(c=><span key={c} className="chip">{c}<button onClick={()=>rmChip("stakeholders",c)}>×</button></span>)}</div>
            </Field>
          </>}

          {tab===3 && <>
            <div className="crumb">PDLC · Run Setup · Stage 3</div>
            <h1 className="h">Artifact Inventory</h1>
            <span className="driven">▣ User-driven</span>
            <div className="callout"><div className="ct">Objective</div>
              <p>List the content the run reads from — documents and code — emitted as <span className="mono" style={{color:"var(--val)"}}>sources[]</span>.
                Add more than one of any type (e.g. two code repos).</p></div>

            <SourceRow type="sharepoint" name="SharePoint — PDF" ph="https://sharepoint.jpmc.net/sites/PBI/Specs"
              items={f.pdf} onItem={(i,k,v)=>setItem("pdf",i,k,v)} onAdd={()=>addItem("pdf",{url:""})} onRemove={i=>rmItem("pdf",i)}/>
            <SourceRow type="bitbucket" name="Bitbucket — Code Repo (Stratus)" bitbucket ph="https://bitbucket.jpmc.net/scm/pbi/merchant-routing-svc.git"
              items={f.code} onItem={(i,k,v)=>setItem("code",i,k,v)} onAdd={()=>addItem("code",{seal:"",url:""})} onRemove={i=>rmItem("code",i)}/>
            <SourceRow type="confluence" name="Confluence" ph="https://confluence.jpmc.net/display/PBI/Discover"
              items={f.confluence} onItem={(i,k,v)=>setItem("confluence",i,k,v)} onAdd={()=>addItem("confluence",{url:""})} onRemove={i=>rmItem("confluence",i)}/>
            <SourceRow type="lucid" name="Lucid" ph="https://lucid.app/lucidchart/…"
              items={f.lucid} onItem={(i,k,v)=>setItem("lucid",i,k,v)} onAdd={()=>addItem("lucid",{url:""})} onRemove={i=>rmItem("lucid",i)}/>
          </>}

          {tab===4 && <>
            <div className="crumb">PDLC · Run Setup · Stage 4</div>
            <h1 className="h">Generator</h1>
            <span className="driven" style={{color:"var(--accent)",borderColor:"var(--accent-soft)"}}>⚡ Action</span>
            <div className="callout"><div className="ct">Objective</div>
              <p>Pick the runtime tool, review the emitted config, and Generate. Generate writes UI_INPUT.yaml and pulls
                the registry; then you launch the run.</p></div>

            <div className="gen-grid">
              <div>
                <Field label="Runtime Tool" hint="→ runtime_tool">
                  <div className="tseg">
                    {["claude","copilot"].map(rt=>(
                      <button key={rt} className={f.runtime_tool===rt?"active":""} onClick={()=>set("runtime_tool",rt)}>
                        {rt==="claude"?"Claude Code":"Copilot"}
                      </button>
                    ))}
                  </div>
                </Field>
                <Field label="Registry (Agentic Repo)" hint="fixed location · commit resolved & pinned at Generate">
                  <div className="authref" style={{padding:"4px 0",marginTop:0}}>
                    {generated
                      ? <b>registry @ 7d2e9a1 · pinned</b>
                      : <><b>registry @ latest</b> <span style={{color:"var(--ink-dim)"}}>· resolves &amp; pins when you Generate</span></>}
                  </div>
                </Field>
                <div style={{display:"flex",gap:12,marginTop:22}}>
                  <button className="btn-gen" onClick={()=>setGenerated(true)}>◆ Generate</button>
                  <button className="btn-ghost" disabled={!generated} onClick={()=>setLaunched(true)}>▸ Launch</button>
                </div>
                {generated && !launched && <div className="fhint" style={{marginTop:10,color:"var(--accent)"}}>✓ Scaffold ready — inspect UI_INPUT.yaml on the right, then Launch for the start steps.</div>}
                <div className="fhint" style={{marginTop:10}}>Two steps: Generate scaffolds &amp; hydrates (deterministic backend, no agent). Launch shows the <b style={{fontWeight:600,color:"var(--ink-soft)"}}>manual</b> start — in MVP you open the agent yourself; the UI can't start it (auto-launch is deferred). Config is immutable after Generate.</div>

                {launched && <div className="gesture">
                  <div className="micro" style={{marginBottom:10,color:"var(--accent)"}}>
                    <span className="navled led-blink" style={{display:"inline-block",background:"var(--accent)",marginRight:7}}/>
                    Manual start · {f.runtime_tool==="claude"?"Claude Code":"Copilot"}
                  </div>
                  {f.runtime_tool==="claude"
                    ? <ol className="steps">
                        <li>Run <span className="cmd">claude</span> in the working path — <span className="mono" style={{color:"var(--ink-mute)"}}>CLAUDE.md</span> loads automatically.</li>
                        <li>Execute <span className="cmd">/start-brd</span>.</li>
                      </ol>
                    : <ol className="steps">
                        <li>Open <b>agent mode</b> — <span className="mono" style={{color:"var(--ink-mute)"}}>copilot-instructions.md</span> loads automatically.</li>
                        <li>Execute <span className="cmd">/start-brd</span>.</li>
                      </ol>}
                </div>}
              </div>

              <div>
                <div className="rule" style={{marginTop:0}}><span className="rule-i">▣</span><span className="rule-l">UI_INPUT.yaml — emitted</span></div>
                <div className="yaml" dangerouslySetInnerHTML={{__html:yaml}}/>
              </div>
            </div>
          </>}
        </main>
      </div>
    </div>
  );
}

function SourceRow({type,name,bitbucket,ph,items,onItem,onAdd,onRemove}){
  return (
    <div className="srow">
      <div className="srow-hd">
        <div className="srow-type">
          <span className="navled" style={{background:"var(--ink-mute)"}}/>
          <span className="srow-name">{name}</span>
        </div>
      </div>
      <div className="srow-body">
        {items.map((it,i)=>(
          <div key={i} className="srow-item">
            {bitbucket && <div>
              <label className="flabel">SEAL ID{items.length>1?` · ${i+1}`:""}</label>
              <div className="tinput"><input value={it.seal} placeholder="SEAL-12345" onChange={e=>onItem(i,"seal",e.target.value)}/></div>
            </div>}
            <div>
              <label className="flabel">{bitbucket?"Repo URL":"URL / Path"}{!bitbucket&&items.length>1?` · ${i+1}`:""}</label>
              <div className="tinput">
                <input value={it.url} placeholder={ph} onChange={e=>onItem(i,"url",e.target.value)}/>
                {items.length>1 && <button className="x" title="remove" onClick={()=>onRemove(i)}>×</button>}
              </div>
            </div>
          </div>
        ))}
        <button className="addbtn" onClick={onAdd}>+ Add {bitbucket?"another repo":"another URL"}</button>
        <div className="authref"><b>auth_ref:</b> jpmc_adapters:{type}</div>
      </div>
    </div>
  );
}

function buildYaml(f,generated){
  const v=(x)=>x?`<span class="yv">${esc(x)}</span>`:`<span class="yc">—</span>`;
  const s=(x)=>`<span class="ys">${esc(x)}</span>`;
  const k=(x)=>`<span class="yk">${x}</span>`;
  const atGen=`<span class="yc"># set at Generate</span>`;
  const hints=f.scope_hints.length?`[${f.scope_hints.map(h=>`<span class="yv">${esc(h)}</span>`).join(", ")}]`:`<span class="yc">[]</span>`;
  const stk=f.stakeholders.length?`[${f.stakeholders.map(h=>`<span class="yv">${esc(h)}</span>`).join(", ")}]`:`<span class="yc">[]</span>`;
  const L=[];
  L.push(`${k("run_id:")} ${generated?s("r-2026-06-17-001"):atGen}`);
  L.push(`${k("schema_version:")} ${s("1")}`);
  L.push(`${k("working_path:")} ${v(f.working_path)}`);
  L.push(`${k("domain:")} ${v(f.domain)}`);
  L.push(`${k("runtime_tool:")} ${v(f.runtime_tool)}`);
  L.push(`${k("registry_sha:")} ${generated?s("7d2e9a1"):atGen}`);
  L.push("");
  L.push(`${k("project_metadata:")}`);
  L.push(`  ${k("project_name:")} ${v(f.project_name)}`);
  L.push(`  ${k("application_name:")} ${v(f.application_name)}`);
  L.push(`  ${k("line_of_business:")} ${v(f.lob)}`);
  L.push(`  ${k("requestor:")} ${v(f.requestor)}`);
  L.push(`  ${k("requestor_sid:")} ${v(f.requestor_sid)}`);
  L.push("");
  L.push(`${k("frame:")}  <span class="yc"># BRD seed</span>`);
  L.push(`  ${k("title:")} ${v(f.project_name)}`);
  L.push(`  ${k("intent:")} ${v(f.intent)}`);
  L.push(`  ${k("scope_hints:")} ${hints}`);
  L.push(`  ${k("stakeholders:")} ${stk}`);
  L.push(`  ${k("key_dates:")} { ${k("compliance_deadline:")} ${v(f.compliance_deadline)} }`);
  L.push("");
  L.push(`${k("sources:")}`);
  let any=false;
  f.pdf.forEach(it=>{if(it.url){any=true;L.push(`  - ${k("type:")} ${v("sharepoint")}`);L.push(`    ${k("url:")} ${v(it.url)}`);L.push(`    ${k("auth_ref:")} ${s("jpmc_adapters:sharepoint")}`);}});
  f.code.forEach(it=>{if(it.url||it.seal){any=true;L.push(`  - ${k("type:")} ${v("bitbucket")}`);L.push(`    ${k("seal_id:")} ${v(it.seal)}`);L.push(`    ${k("repo_url:")} ${v(it.url)}`);L.push(`    ${k("auth_ref:")} ${s("jpmc_adapters:bitbucket")}`);}});
  f.confluence.forEach(it=>{if(it.url){any=true;L.push(`  - ${k("type:")} ${v("confluence")}`);L.push(`    ${k("url:")} ${v(it.url)}`);L.push(`    ${k("auth_ref:")} ${s("jpmc_adapters:confluence")}`);}});
  f.lucid.forEach(it=>{if(it.url){any=true;L.push(`  - ${k("type:")} ${v("lucid")}`);L.push(`    ${k("url:")} ${v(it.url)}`);L.push(`    ${k("auth_ref:")} ${s("jpmc_adapters:lucid")}`);}});
  if(!any)L.push(`  <span class="yc"># add sources in Stage 3</span>`);
  L.push("");
  L.push(`${k("gates:")} { ${k("score_threshold:")} ${v(f.score_threshold)} }`);
  L.push(`<span class="yc"># jira: deferred this slice (no push)</span>`);
  return L.join("\n");
}
function esc(s){return String(s).replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));}
