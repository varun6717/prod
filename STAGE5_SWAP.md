# Stage 5 swap · keep "at a glance", retire the 9-step walkthrough

**For:** GitHub Copilot, or whoever applies this on the VDI.
**File to change:** `ai-program-update.html`, the AI Program Update deck. It is a single, self-contained, offline HTML file.
**Goal:** management sees Stage 5 as **two clicks**: *how it decides*, then *what it produced*. The old 9-step Stage 5 must no longer appear in the presentation.

---

## Option A · simplest: replace the file

If your VDI copy of `ai-program-update.html` has **no local edits** (for example, link slots filled with VDI paths in `LINKS`), just replace it with the `ai-program-update.html` that comes with this note. You are done; jump to **Verify**.

If it **does** have local edits, use Option B so you keep them.

---

## Option B · apply the change in place (6 edits)

Make each edit exactly once. Every *find* string below occurs **exactly once** in the old file. If a find matches 0 times or more than once, stop: the file is a different version.

> **Why the old Stage 5 is hidden, not deleted:** the new page's two drill-down buttons, **Compare with the developer** and **How it is scored**, open views (`ILL["s5-compare"]` and `ILL["s5-rubric"]`) that the old Stage 5 code defines. Deleting that section or its JavaScript breaks those buttons. With `data-skip`, the page stays in the file but is left out of Next, the page count, the progress rail and every jump link. As far as the audience can tell, it is removed.

### Edit 1 · add the CSS for the new page

**Find** this line, the header of the Stage 2 styles:

````css
/* ═══════════════════════════════════════════════════════════════════════
   SCENE · PDLC STAGE 2
````

**Insert immediately before it:**

````css
/* ═══════════════════════════════════════════════════════════════════════
   SCENE · PDLC STAGE 5 AT A GLANCE  — two clicks: how it decides → what it produced
   ═══════════════════════════════════════════════════════════════════════ */
.p5g{padding-top:84px}
.p5g .hd h2{max-width:1500px;font-size:40px}
.p5g .tally .chip{transition:opacity .4s,border-color .4s} .p5g .tally .chip.off{opacity:.45}
.p5g .tally .chip.on{border-color:rgba(var(--cyan-rgb),.6);color:var(--ink)}
.p5g .cols{position:absolute;left:120px;right:120px;top:262px;height:510px;display:grid;grid-template-columns:250px 350px 560px 1fr;gap:34px}
.p5g .col{position:relative;border-radius:20px;border:1px solid var(--edge-lit);background:#0E1319;padding:20px 22px;display:flex;flex-direction:column;transition:opacity .6s var(--out)}
.p5g .col.dim{opacity:.42}
.p5g .col+.col::before{content:"";position:absolute;left:-30px;top:50%;width:24px;height:2px;background:linear-gradient(90deg,transparent,var(--cyan));animation:p5flow 1.6s linear infinite}
.p5g .col+.col::after{content:"";position:absolute;left:-12px;top:calc(50% - 5px);border:6px solid transparent;border-left:8px solid var(--cyan);border-right:0}
@keyframes p5flow{0%{opacity:.25}50%{opacity:1}100%{opacity:.25}}
.p5g .ch{display:flex;align-items:baseline;gap:12px;margin-bottom:16px}
.p5g .ch i{font-style:normal;font-family:var(--mono);font-size:13px;color:var(--bg-0,#0B0D12);background:var(--cyan);border-radius:50%;width:24px;height:24px;display:inline-grid;place-items:center;flex:none;transform:translateY(-2px)}
.p5g .ch b{font-family:var(--display);font-weight:700;font-size:21px;letter-spacing:-.02em;color:var(--ink)}
.p5g .cf{margin-top:auto;padding-top:12px;font-family:var(--mono);font-size:11.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--dim)}
/* 1 · inputs */
.p5g .in{display:flex;gap:12px;align-items:flex-start;padding:12px 0;border-top:1px solid rgba(255,255,255,.07)} .p5g .in:first-of-type{border-top:0}
.p5g .in s{width:10px;height:10px;border-radius:50%;background:var(--c);box-shadow:0 0 10px var(--c);margin-top:7px;flex:none}
.p5g .in b{display:block;font-size:17px;font-weight:600;color:var(--ink)} .p5g .in span{display:block;font-family:var(--mono);font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin-top:4px}
/* 2 · candidate groups */
.p5g .dg{border:1px solid var(--edge);border-radius:14px;padding:12px 14px;margin-bottom:14px;background:rgba(255,255,255,.02)}
.p5g .dg .k{font-family:var(--mono);font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--violet)} .p5g .dg > b{display:block;font-size:16.5px;font-weight:600;color:var(--ink);margin:4px 0 10px}
.p5g .cd{display:flex;gap:10px;align-items:baseline;padding:7px 10px;border-radius:9px;background:rgba(var(--cyan-rgb),.05);margin-top:6px;font-size:15px;color:var(--muted);line-height:1.35}
.p5g .cd i{font-style:normal;font-family:var(--mono);font-size:12px;color:var(--cyan);flex:none}
/* 3 · ranking matrix */
.p5g .mx{display:grid;grid-template-columns:150px repeat(4,1fr) 104px;align-items:center;row-gap:4px}
.p5g .mx .h{font-family:var(--mono);font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--dim);text-align:center;line-height:1.3;padding-bottom:8px;border-bottom:1px solid var(--edge-lit);align-self:stretch;display:flex;align-items:flex-end;justify-content:center}
.p5g .mx .h:first-child{justify-content:flex-start;text-align:left}
.p5g .mx .grp{grid-column:1/-1;font-family:var(--mono);font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--violet);padding:14px 0 4px}
.p5g .mx .rl{font-size:15px;color:var(--ink);padding:10px 8px;border-radius:10px 0 0 10px} .p5g .mx .rl em{font-style:normal;font-family:var(--mono);color:var(--cyan);margin-right:8px}
.p5g .mx .sc{display:flex;justify-content:center;gap:5px;padding:14px 0}
.p5g .mx .sc u{width:14px;height:14px;border-radius:4px;background:rgba(255,255,255,.08)} .p5g .mx .sc u.f{background:var(--cyan);box-shadow:0 0 8px rgba(var(--cyan-rgb),.5)}
.p5g .mx .rk{font-family:var(--mono);font-size:12.5px;letter-spacing:.06em;text-transform:uppercase;text-align:center;padding:8px 0;border-radius:0 10px 10px 0}
.p5g .mx .rk.w{color:var(--ok)} .p5g .mx .rk.l{color:var(--bad)}
.p5g .mx .row{display:contents}
.p5g .mx .row.w > *{background:rgba(var(--ok-rgb,65,227,155),.0);animation:p5win .8s var(--out) forwards;animation-delay:var(--wd)}
@keyframes p5win{to{background:rgba(var(--ok-rgb,65,227,155),.12)}}
.p5g .mx .row.l > *{opacity:.62}
.p5g .why{margin-top:14px;font-size:15px;line-height:1.45;color:var(--muted)} .p5g .why b{color:var(--ink)}
.p5g .tagx{display:inline-block;margin-top:10px;font-family:var(--mono);font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--warn);border:1px dashed rgba(var(--warn-rgb,255,181,71),.55);border-radius:6px;padding:3px 8px}
/* 4 · the code */
.p5g .wait{flex:1;display:grid;place-items:center;text-align:center;border:1.5px dashed var(--edge-lit);border-radius:14px;font-family:var(--mono);font-size:13px;letter-spacing:.14em;text-transform:uppercase;color:var(--dim);line-height:1.8}
.p5g .fr{display:grid;grid-template-columns:1fr 46px;gap:4px 12px;align-items:center;padding:9px 0;border-top:1px solid rgba(255,255,255,.07)} .p5g .fr:first-of-type{border-top:0}
.p5g .fr b{font-family:var(--mono);font-size:14.5px;font-weight:500;color:var(--ink)} .p5g .fr em{font-style:normal;font-family:var(--mono);font-size:15px;text-align:right;grid-row:1/3;grid-column:2}
.p5g .fr .bar{height:7px;border-radius:4px;background:rgba(255,255,255,.07);overflow:hidden} .p5g .fr .bar i{display:block;height:100%;width:0;border-radius:4px;animation:p5bar .9s var(--out) forwards;animation-delay:var(--d)}
@keyframes p5bar{to{width:var(--w)}}
.p5g .fr.ok em{color:var(--ok)} .p5g .fr.ok .bar i{background:var(--ok)} .p5g .fr.mid em{color:var(--warn)} .p5g .fr.mid .bar i{background:var(--warn)}
.p5g .ov{display:flex;align-items:center;gap:16px;margin-top:14px;padding:14px 16px;border-radius:14px;border:1px solid rgba(var(--ok-rgb,65,227,155),.4);background:rgba(var(--ok-rgb,65,227,155),.07)}
.p5g .ov big{font-family:var(--display);font-size:48px;font-weight:700;line-height:1;color:var(--ok)} .p5g .ov b{display:block;font-size:17px;color:var(--ink)} .p5g .ov span{display:block;font-size:13.5px;color:var(--muted);margin-top:2px}
.p5g .acts{display:flex;flex-wrap:wrap;gap:10px;margin-top:14px}
.p5g .acts a{font-family:var(--mono);font-size:12.5px;letter-spacing:.06em;padding:8px 12px;border-radius:10px;border:1px solid rgba(var(--cyan-rgb),.5);background:rgba(var(--cyan-rgb),.08);color:var(--cyan);cursor:pointer;white-space:nowrap} .p5g .acts a:hover{background:rgba(var(--cyan-rgb),.16)}
.p5g .acts a.alt{border-color:var(--edge-lit);background:none;color:var(--muted)}
.p5g .say{position:absolute;left:120px;right:120px;top:812px;font-family:var(--display);font-weight:600;font-size:22px;letter-spacing:-.015em;color:var(--ink)} .p5g .say span{color:var(--muted);font-weight:500}

````

### Edit 2 · add the new page, and retire the old Stage 5 page

**Find** this exact line, the opening tag of the old Stage 5 section:

````html
  <section class="scene ps2 ps4 ps5" data-label="PDLC · Stage 5 · Draft code changes" data-section="pdlc-stage-5" data-ambient="0.1" data-calm data-steps="9">
````

**Replace it with** the new page's markup followed by the old section's re-labelled, hidden opening tag:

````html
  <section class="scene p5g" data-label="PDLC · Stage 5 · Draft code changes" data-section="pdlc-stage-5-glance" data-ambient="0.1" data-calm data-steps="2">
    <div class="hd"><div><div class="kick a fade" style="--d:0"></div><h2 class="a focus" style="--d:150"></h2></div><div class="tally"></div></div>
    <div class="cols"></div>
    <div class="say"></div>
  </section>
  <section class="scene ps2 ps4 ps5" data-label="PDLC · Stage 5 · Full walkthrough" data-section="pdlc-stage-5" data-ambient="0.1" data-calm data-steps="9" data-skip>
````

Leave the rest of the old section (its inner `div`s and `</section>`) as it is.

### Edit 3 · add the new page's JavaScript

**Find** this line:

````js
      /* ── Stage 5 · Draft code changes ── */
````

**Insert immediately before it:**

````js
      /* ── Stage 5 at a glance · two clicks for management: how it decides → what it produced.
            Groups, candidates, decisions and file scores are real (code_changes.json); the matrix dots are illustrative. ── */
      var s5g=$('.scene[data-section="pdlc-stage-5-glance"]');
      if(s5g){
        var G5={
          kicker:"04 · Showcase · Stage 5 of 5 · Draft code changes",
          headline:"It weighs several ways to build the change, keeps the best, then writes the code for a person to review.",
          chips:["Click 1 · how it decides","Click 2 · what it produced"],
          inputs:[ ["Approved requirements","Solution Intent v2 · G2","var(--cyan)"], ["Delivery plan","Jira · 6 stories · G3","var(--violet)"], ["Live code","Stratus · code map","var(--ok)"], ["Past changes","History KB · Neuro","var(--warn)"] ],
          groups:[ { g:"DG-1", t:"Declare the new DCAP levels", c:[ ["CD-1","Add rows to the existing tables"] ] },
                   { g:"DG-2", t:"Route DCAP transactions", c:[ ["CD-2","Add the check inside each of 3 branches"], ["CD-3","Add one step after today's logic"] ] } ],
          crit:["Fits the code","Keeps today's logic","One place to change","Easy to prove"],
          mx:[ ["DG-1 · levels",[ ["CD-1","Existing tables",[3,3,3,3],"Best",1] ]],
               ["DG-2 · routing",[ ["CD-3","One step after",[3,3,3,3],"Best",1], ["CD-2","Inside 3 branches",[2,2,1,1],"Rejected",0] ]] ],
          why:"<b>Best in each group wins.</b> CD-2 was rejected: the same check copied three times means three places to break.",
          files:[ ["inter_level_defines.h","24 new levels",85], ["Visa_FPI_table.h","24 FPI rows",100], ["inter_lev_Vi_CA.c","the DCAP step",100], ["mdVisa.c","settlement routing",100] ],
          say:["It reads the approved inputs, sketches the ways to build it, scores them, and keeps the best.","Then it writes the code as reviewable copies, scored per file. <span>A person approves at G4.</span>"]
        };
        $(".kick",s5g).textContent=G5.kicker; $("h2",s5g).textContent=G5.headline;
        function A(cls,d,on){return on?' class="a '+cls+'" style="--d:'+d+'"':''}
        function renderG(step){
          var p=step===0, q=step===1;   /* p: play the decision columns · q: play the code column */
          $(".tally",s5g).innerHTML=G5.chips.map(function(c,i){return '<span class="chip '+(i===step?'on':'off')+'" style="--c:var(--'+(i?'ok':'cyan')+')"><i></i>'+esc(c)+'</span>'}).join("");
          var h='';
          h+='<div class="col'+(q?' dim':'')+'"><div class="ch"><i>1</i><b>Inputs</b></div>'+
             G5.inputs.map(function(x,i){return '<div class="in"><s style="--c:'+x[2]+'"></s><div'+A("rise",400+i*180,p)+'><b>'+esc(x[0])+'</b><span>'+esc(x[1])+'</span></div></div>'}).join("")+
             '<div class="cf"'+A("fade",1300,p)+'>9 approved inputs · nothing invented</div></div>';
          h+='<div class="col'+(q?' dim':'')+'"><div class="ch"><i>2</i><b>Ways to build it</b></div>'+
             G5.groups.map(function(g,gi){return '<div class="dg"'+A("rise",1500+gi*500,p)+'><div class="k">'+g.g+' · design group</div><b>'+esc(g.t)+'</b>'+
               g.c.map(function(c,ci){return '<div class="cd"'+A("pop",1800+gi*500+ci*250,p)+'><i>'+c[0]+'</i>'+esc(c[1])+'</div>'}).join("")+'</div>'}).join("")+
             '<div class="cf"'+A("fade",2700,p)+'>2 groups · 3 candidates</div></div>';
          var r=0, M='<div class="mx"><div class="h">Candidate</div>'+G5.crit.map(function(c){return '<div class="h">'+esc(c)+'</div>'}).join("")+'<div class="h">Rank</div>';
          G5.mx.forEach(function(gr){M+='<div class="grp">'+esc(gr[0])+'</div>';
            gr[1].forEach(function(row){var d0=3000+r*550; r++;
              M+='<div class="row '+(row[4]?'w':'l')+'" style="--wd:'+(p?d0+1300:0)+'ms"><div class="rl"'+A("fade",d0,p)+'><em>'+row[0]+'</em>'+esc(row[1])+'</div>'+
                row[2].map(function(v,ci){return '<div class="sc"'+A("pop",d0+120+ci*110,p)+'>'+[1,2,3].map(function(k){return '<u'+(k<=v?' class="f"':'')+'></u>'}).join("")+'</div>'}).join("")+
                '<div class="rk '+(row[4]?'w':'l')+'"'+A("pop",d0+700,p)+'>'+(row[4]?'✓ ':'✕ ')+esc(row[3])+'</div></div>'});
          });
          M+='</div>';
          h+='<div class="col"><div class="ch"><i>3</i><b>Score them, keep the best</b></div>'+M+
             '<div class="why"'+A("fade",5000,p)+'>'+G5.why+'</div><div'+A("fade",5300,p)+'><span class="tagx">Illustrative scores · groups, choices and reasons are real</span></div></div>';
          if(step===0){
            h+='<div class="col"><div class="ch"><i>4</i><b>Write the code</b></div><div class="wait"'+A("fade",5600,true)+'>Next click<br>the code it writes</div></div>';
          } else {
            h+='<div class="col"><div class="ch"><i>4</i><b>Write the code</b></div>'+
               G5.files.map(function(f,i){var d=500+i*350;return '<div class="fr '+(f[2]>=90?'ok':'mid')+'"'+A("rise",d,true)+'><b>'+esc(f[0])+'</b><em>'+f[2]+'</em><div class="bar"><i style="--w:'+f[2]+'%;--d:'+(d+300)+'ms"></i></div></div>'}).join("")+
               '<div class="ov"'+A("pop",2200,true)+'><big>85</big><div><b>Overall · High</b><span>The lowest file sets it. Evidence score, not a test result.</span></div></div>'+
               '<div class="acts"'+A("fade",2700,true)+'><a data-ill="s5-compare">Compare with the developer →</a><a data-ill="s5-rubric" class="alt">How it is scored →</a></div></div>';
          }
          $(".cols",s5g).innerHTML=h;
          $(".say",s5g).innerHTML='<div class="a fade" style="--d:'+(p?5800:3000)+'">'+G5.say[step]+'</div>';
        }
        HOOKS["pdlc-stage-5-glance"]=function(s,g,step){renderG(step)};
      }

````

### Edit 4 · make navigation skip hidden pages

**Find:**

````js
  var scenes=$$(".scene"),cur=-1,step=0,busy=false,gen=0;
````

**Replace with:**

````js
  var scenes=$$(".scene:not([data-skip])"),cur=-1,step=0,busy=false,gen=0;   /* data-skip: kept in the file, left out of the flow */
````

### Edit 5 · make the section jump links skip hidden pages (3 places)

**Replace every occurrence** (there are exactly **3**) of:

````js
$$(".scene").findIndex
````

**with:**

````js
$$(".scene:not([data-skip])").findIndex
````

### Edit 6 · do NOT delete

- Do **not** delete the old Stage 5 `<section ... data-section="pdlc-stage-5" ... data-skip>`.
- Do **not** delete the `stage5:` content object or the `/* ── Stage 5 · Draft code changes ── */` JavaScript block.

They power the two drill-downs on the new page.

---

## Verify

Open the deck in a browser and check:

1. The page counter reads **xx / 15**, and the last page is **"PDLC · Stage 5 · Draft code changes"** with **1/2** and **2/2** steps.
2. **Click 1** builds four panels: Inputs → Ways to build it → Score them, keep the best → Write the code (placeholder).
3. **Click 2** dims the first two panels and fills **Write the code**: 4 files scored 85 / 100 / 100 / 100 and **Overall 85 · High**.
4. **Compare with the developer →** and **How it is scored →** each open a full-screen view. Click outside the view to close it.
5. Next on the last step reads **Start over** and returns to the cover. The old 9-step Stage 5 never appears.
6. The browser console shows no errors.

Deep link to the new page: `ai-program-update.html?s=14&b=0` (click 1) or `&b=1` (click 2).

## Undo

To bring the 9-step walkthrough back into the flow, remove ` data-skip` from the old Stage 5 opening tag. To remove the new page, delete the `<section class="scene p5g" …>` block. Its CSS and JavaScript are harmless if left in.

## What is real

- **Real**, from `code_changes.json`: the design groups, the candidates, which were picked or rejected and why, and the file scores.
- **Illustrative**, and labelled so on the page: the matrix dots.
