const $=s=>document.querySelector(s);
const sel=(n,o,l)=>["sel",n,o,l],txt=(n,v,l)=>["txt",n,v,l],num=(n,v,l)=>["num",n,v,l];
const MODS={
dashboard:{n:"Dashboard"},
food:{n:"Smart Food",t:"Smart Food Recommendation",f:[sel("diet",["Vegetarian","Non-Vegetarian"],"Diet"),sel("spice",["Low","Medium","High"],"Maximum spice"),txt("avoid","Peanut","Ingredient to avoid")],b:"Recommend food"},
delivery:{n:"Smart Delivery",t:"Autonomous Delivery Planning",f:[txt("start","Warehouse","Start"),txt("goal","Building C","Goal"),txt("waypoints","W1,W2,W3","Waypoints (comma separated)")],b:"Plan route"},
astar:{n:"Smart Navigation",t:"Robot Navigation (A*)"},
breakplanner:{n:"Break Planner",t:"Break-Time Planner",f:[num("break_min",30,"Break length (minutes)"),num("eat_min",10,"Time you need to eat (minutes)"),num("walk_main",3,"Walk to Main Cafeteria (minutes, one way)")],b:"Plan my break"},
queue:{n:"Go or Wait",t:"Go or Wait Advisor",f:[num("queue",25,"People in the queue (0-60)"),num("counters",2,"Counters open (0-6)"),num("minutes",20,"Minutes until your next class (0-60)")],b:"Should I go?"},
foodprep:{n:"Food Preparation",t:"Food Preparation FIS",f:[num("demand",160,"Expected demand (0-200 meals)"),num("remaining",20,"Remaining food (0-100 %)"),num("hour",12,"Hour of day (0-23)")],b:"Calculate preparation"},
neurofuzzy:{n:"Neuro-Fuzzy",t:"Neuro-Fuzzy Cafeteria Management",f:[sel("day",["Mon","Tue","Wed","Thu","Fri","Sat","Sun"],"Day to plan"),num("prev_demand",150,"Previous day demand (meals)"),num("remaining",40,"Remaining food (0-100 %)"),num("hour",12,"Hour of day (0-23)")],b:"Predict and decide"},
mealplanner:{n:"Best Time to Eat",t:"Best Time to Eat",f:[sel("meal",["Breakfast","Lunch","Snacks","Dinner"],"Meal"),sel("priority",["Avoid the crowd","Make sure food is available"],"What matters most to you")],b:"Find best time"},
slm:{n:"Language Model",t:"Micro and Small Language Models",f:[sel("model",["Micro (bigram)","Small (trigram)"],"Model"),txt("text","the cafeteria prepares","Start of sentence"),num("words",6,"Words to generate")],b:"Predict and generate"},
history:{n:"AI History"}};
const post=(m,d)=>fetch("/api/"+m,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(d)}).then(r=>r.json());
const nice=k=>k.replace(/_/g," ").replace(/^./,c=>c.toUpperCase());
const val=v=>Array.isArray(v)?(v.length&&typeof v[0]=="object"?tbl(v):`<div class=chips>${v.map(x=>`<span class=chip>${x}</span>`).join("")}</div>`):(v&&typeof v=="object"?kv(v):`<span>${v}</span>`);
const kv=o=>`<table class=kv>${Object.entries(o).map(([k,v])=>`<tr><th>${nice(k)}<td>${val(v)}</tr>`).join("")}</table>`;
const tbl=a=>`<table><tr>${Object.keys(a[0]).map(h=>`<th>${nice(h)}`).join("")}</tr>${a.map(r=>`<tr>${Object.values(r).map(v=>`<td>${v}`).join("")}</tr>`).join("")}</table>`;
const TECH=["rule","model"];
const fmt=o=>{const e=Object.entries(o),m=e.filter(([k])=>!TECH.includes(k)),t=e.filter(([k])=>TECH.includes(k));
 return `<div class=rows>${m.map(([k,v],i)=>`<div class="row${i?"":" lead"}"><div class=lbl>${nice(k)}</div><div class=v>${val(v)}</div></div>`).join("")}</div>`+(t.length?`<details><summary>How this was decided</summary>${kv(Object.fromEntries(t))}</details>`:"")};
const out=h=>$("#res").innerHTML=`<div class="box res">${h}</div>`;
$("#nav").insertAdjacentHTML("beforeend",Object.entries(MODS).map(([k,m])=>`<a tabindex=0 data-k=${k}>${m.n}</a>`).join(""));
$("#nav").onclick=e=>e.target.dataset.k&&show(e.target.dataset.k);
$("#nav").onkeydown=e=>e.key=="Enter"&&e.target.dataset.k&&show(e.target.dataset.k);
const head=m=>`<h2>${m.t}</h2>`;
async function show(k){
 document.querySelectorAll("nav a").forEach(a=>a.classList.toggle("on",a.dataset.k==k));
 const m=MODS[k],M=$("#main");
 if(k=="dashboard"){const s=await fetch("/api/stats").then(r=>r.json());
  M.innerHTML=`<h2>Smart Campus Intelligence Hub</h2><p class=stat style="margin:-12px 0 18px">One Flask backend, one SQLite database, nine AI modules.</p><div class=cards>
  <div class=box><div class=big>${s._total}</div><div class=stat>AI decisions saved</div></div><div class=box><div class=big>${s._foods}</div><div class=stat>Foods in database</div></div><div class=box><div class=big>${s._days}</div><div class=stat>Days of cafeteria history</div></div></div>
  <h3>Modules</h3><div class=cards>${Object.entries(MODS).slice(1,-1).map(([q,x])=>`<div class="box tile" onclick="show('${q}')"><b>${x.n}</b><br><small>Used ${s[q]||0} times</small></div>`).join("")}</div>`;return}
 if(k=="history"){const h=await fetch("/api/history").then(r=>r.json());
  M.innerHTML=`<h2>AI Decision History</h2><p class=stat style="margin:-12px 0 18px">Tick entries, then delete them.</p><div class=box><button id=del>Delete selected</button><table><tr><th><input type=checkbox id=all aria-label="Select all"><th>Time<th>Module<th>Input<th>Output</tr>${h.map(r=>`<tr><td><input type=checkbox class=ck value=${r.id} aria-label="Select entry ${r.id}"><td>${r.ts}<td>${(MODS[r.module]||{}).n||r.module}<td>${r.input_data}<td>${r.output}</tr>`).join("")||"<tr><td colspan=5>No decisions yet. Use any module first."}</table></div>`;
  $("#all").onchange=e=>document.querySelectorAll(".ck").forEach(c=>c.checked=e.target.checked);
  $("#del").onclick=async()=>{const ids=[...document.querySelectorAll(".ck:checked")].map(c=>+c.value);
   if(!ids.length)return alert("Select at least one entry first.");if(!confirm(`Delete ${ids.length} selected entries?`))return;
   await fetch("/api/history/delete",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({ids})});show("history")};return}
 if(k=="astar")return astarPage(M,m);
  M.innerHTML=head(m)+`<form id=f>${m.f.map(([t,n,v,l])=>`<label for=${n}>${l}</label>`+(t=="sel"?`<select id=${n}>${v.map(o=>`<option>${o}`).join("")}</select>`:`<input id=${n} type=${t=="num"?"number":"text"} value="${v}" step=any>`)).join("")}<button>${m.b}</button></form><div id=res></div>`;
 $("#f").onsubmit=async e=>{e.preventDefault();const d={};m.f.forEach(([t,n])=>d[n]=t=="num"?+$("#"+n).value:$("#"+n).value);
  const r=await post(k,d);out(r.error||fmt(r))}}
let G=["S..X...",".X.X.X.","....X..","X.X...G"];
function astarPage(M,m){M.innerHTML=head(m)+`<div class=box><div id=g class=grid></div><div class=legend>S = start, G = goal, X = obstacle. Click a cell to add or remove an obstacle.</div><button id=go>Find path</button></div><div id=res></div>`;draw([]);
 $("#go").onclick=async()=>{const r=await post("astar",{grid:G});draw(r.path||[]);out(r.error||r.message||fmt({shortest_path:"Found",path_length:r.path_length_cells+" cells",total_cost:r.cost}))}}
function draw(p){const g=$("#g");g.style.gridTemplateColumns=`repeat(${G[0].length},42px)`;
 g.innerHTML=G.map((row,r)=>[...row].map((ch,c)=>{const on=p.some(q=>q[0]==r&&q[1]==c)&&ch=="."; return `<div class="cell ${on?"P":ch}" data-r=${r} data-c=${c}>${ch=="."?"":ch}</div>`}).join("")).join("");
 g.onclick=e=>{const d=e.target.dataset;if(d.r==null)return;const ch=G[d.r][d.c];if("SG".includes(ch))return;
  G[d.r]=G[d.r].slice(0,d.c)+(ch=="X"?".":"X")+G[d.r].slice(+d.c+1);draw([])}}
show("dashboard");
