const state = {
  env:null, target:[99,99], start:[0,0], hazards:[], outward:null, returnPath:null,
  roverPath:[], step:0, battery:100, timer:null, mode:"outward", rover:[0,0],
  placingHazard:false, currentOnComplete:null
};
const $ = id => document.getElementById(id);

async function loadEnv(){
  state.env = await fetch("/api/environment").then(r=>r.json());
  $("mapStatus").textContent = `${state.env.rows}×${state.env.cols} navigation grid`;
  const s=state.env.stats;
  $("elevStats").textContent=`Range: ${s.min_elevation.toFixed(0)} to ${s.max_elevation.toFixed(0)} m · mean ${s.mean_elevation.toFixed(1)} m`;
  $("slopeStats").textContent=`Range: ${s.min_slope.toFixed(2)}° to ${s.max_slope.toFixed(2)}° · mean ${s.mean_slope.toFixed(2)}°`;
  $("obStats").textContent=`${s.obstacle_cells} cells currently classified as obstacles (>25° configured threshold).`;
  draw();
}

function draw(){
  if(!state.env)return;
  const c=$("map"), ctx=c.getContext("2d"), rows=state.env.rows, cols=state.env.cols;
  const w=c.width/cols,h=c.height/rows;
  const costs=state.env.cost;
  for(let r=0;r<rows;r++)for(let col=0;col<cols;col++){
    const v=Math.max(0,Math.min(1,(costs[r][col]-1)/9));
    const g=Math.round(45+150*(1-v)), rr=Math.round(25+180*v), b=Math.round(28+30*(1-v));
    ctx.fillStyle=`rgb(${rr},${g},${b})`;ctx.fillRect(col*w,r*h,w+1,h+1);
    if(state.env.obstacles[r][col]){ctx.fillStyle="#050608";ctx.fillRect(col*w,r*h,w+1,h+1)}
  }
  // dynamic hazards
  state.hazards.forEach(([r,col])=>{ctx.fillStyle="#ff4d5d";ctx.fillRect(col*w,r*h,w+1,h+1)});
  // path
  const path = state.mode==="return" && state.returnPath ? state.returnPath : state.outward;
  if(path&&path.path){
    ctx.strokeStyle="#67dcff";ctx.lineWidth=2.5;ctx.beginPath();
    path.path.forEach(([r,col],i)=>{const x=(col+.5)*w,y=(r+.5)*h;i?ctx.lineTo(x,y):ctx.moveTo(x,y)});ctx.stroke();
  }
  marker(ctx,state.start,"#ffffff","B",w,h);
  marker(ctx,state.target,"#e6a23c","T",w,h);
  marker(ctx,state.rover,"#59d4ff","R",w,h);
}
function marker(ctx,[r,col],color,label,w,h){
  ctx.fillStyle=color;ctx.beginPath();ctx.arc((col+.5)*w,(r+.5)*h,7,0,Math.PI*2);ctx.fill();
  ctx.fillStyle="#111";ctx.font="bold 9px Arial";ctx.textAlign="center";ctx.textBaseline="middle";ctx.fillText(label,(col+.5)*w,(r+.5)*h);
}

$("map").addEventListener("click",e=>{
  const rect=e.target.getBoundingClientRect(), x=(e.clientX-rect.left)/rect.width, y=(e.clientY-rect.top)/rect.height;
  const r=Math.max(0,Math.min(99,Math.floor(y*100))), c=Math.max(0,Math.min(99,Math.floor(x*100)));

  if(state.placingHazard){
    if(state.env.obstacles[r][c]){
      $("message").textContent=`(${r}, ${c}) is already impassable terrain — pick a traversable cell for the hazard.`;
      return;
    }
    if(r===state.rover[0]&&c===state.rover[1]){
      $("message").textContent="Can't place a hazard on the rover's current position.";
      return;
    }
    if(!state.hazards.some(p=>p[0]===r&&p[1]===c)){
      state.hazards.push([r,c]);
    }
    state.placingHazard=false;
    $("addHazard").textContent="SIMULATE NEW HAZARD";
    $("addHazard").classList.remove("active");
    $("message").textContent=`Dynamic hazard placed at (${r}, ${c}). Checking active route…`;
    draw();
    attemptReroute([r,c]);
    return;
  }

  $("goalR").value=r;$("goalC").value=c;state.target=[r,c];draw();
});

document.querySelectorAll(".nav").forEach(b=>b.addEventListener("click",()=>{
  document.querySelectorAll(".nav").forEach(x=>x.classList.remove("active"));b.classList.add("active");
  document.querySelectorAll(".page").forEach(x=>x.classList.remove("active"));$(b.dataset.page).classList.add("active");
}));

$("plan").addEventListener("click",async()=>{
  clearInterval(state.timer);state.step=0;state.mode="outward";state.rover=[...state.start];
  state.target=[Number($("goalR").value),Number($("goalC").value)];state.battery=Number($("battery").value);
  $("batteryOut").textContent=state.battery.toFixed(0)+"%";$("status").textContent="Planning…";
  const res=await fetch("/api/plan",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({
    start:state.start,goal:state.target,battery:state.battery,algorithm:$("algorithm").value,dynamic_obstacles:state.hazards
  })}).then(r=>r.json());
  if(res.error){$("message").textContent=res.error;return}
  if(!res.reachable||!res.mission_possible){$("run").disabled=true;$("status").textContent="Mission blocked";$("message").textContent=res.message;return}
  state.outward=res.outward;state.returnPath=res.return;
  $("costOut").textContent=res.outward.cost.toFixed(2);$("cellsOut").textContent=res.outward.cells;
  $("message").textContent=`Mission feasible. Round-trip terrain cost ${res.round_trip_cost.toFixed(2)}; estimated battery needed ${res.estimated_battery_needed.toFixed(1)}%.`;
  $("status").textContent="Mission planned";$("run").disabled=false;draw();
});

// Drives the rover along whichever path is currently active in state
// (state.outward or state.returnPath, per state.mode), re-reading it on
// every tick. This lets a mid-mission reroute swap the path array under it
// without needing to tear down and rebuild the interval.
function driveAlong(onComplete){
  state.currentOnComplete=onComplete;
  clearInterval(state.timer);
  state.timer=setInterval(()=>{
    const p = state.mode==="outward" ? state.outward.path : state.returnPath.path;
    if(state.step>=p.length-1){
      clearInterval(state.timer);
      onComplete();
      return;
    }
    state.step++;state.rover=[...p[state.step]];
    consumeBattery();updateLive();draw();
  },80);
}

$("run").addEventListener("click",()=>{
  if(!state.outward)return;
  $("run").disabled=true;state.mode="outward";state.step=0;state.rover=[...state.start];
  $("status").textContent="Travelling to target…";
  driveAlong(()=>{
    state.mode="return";state.step=0;state.rover=[...state.target];
    $("status").textContent="Target reached — returning to base…";
    driveAlong(()=>{
      state.rover=[...state.start];$("status").textContent="Mission complete ✓";$("message").textContent="Rover returned safely to base.";updateLive();draw();
    });
  });
});

function consumeBattery(){
  const slope=state.env.slope[state.rover[0]][state.rover[1]];
  state.battery=Math.max(0,state.battery-(0.012+0.003*Math.min(slope,25)));
  if(state.battery<=0){clearInterval(state.timer);$("status").textContent="Battery depleted";$("run").disabled=false}
}
function updateLive(){
  const [r,c]=state.rover;$("batteryOut").textContent=state.battery.toFixed(1)+"%";$("position").textContent=`(${r}, ${c})`;
  $("terrainOut").textContent=state.env.slope[r][c].toFixed(1)+"° slope";
}

// Called whenever a new hazard is placed. If it lands on a stretch of the
// rover's active route that hasn't been driven yet, pause, ask the backend
// for a fresh path from the rover's current position to its current
// destination (avoiding all placed hazards), then resume.
async function attemptReroute(hazard){
  if(!state.outward) return;
  const activePath = state.mode==="outward" ? state.outward : state.returnPath;
  if(!activePath || !activePath.path) return;

  const remaining = activePath.path.slice(state.step);
  const onRoute = remaining.some(([r,c])=>r===hazard[0]&&c===hazard[1]);
  if(!onRoute){
    $("message").textContent=`Hazard placed at (${hazard[0]}, ${hazard[1]}) — it's clear of the active route.`;
    return;
  }

  const wasRunning = !!state.timer;
  clearInterval(state.timer);
  $("status").textContent="Hazard on route — recalculating…";
  const destination = state.mode==="outward" ? state.target : state.start;

  const res = await fetch("/api/reroute",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({
    start: state.rover, goal: destination, algorithm: $("algorithm").value, dynamic_obstacles: state.hazards
  })}).then(r=>r.json());

  if(res.error || !res.reachable){
    $("status").textContent="Rover stranded";
    $("message").textContent="The hazard blocks every route to the destination — no alternate path found.";
    $("run").disabled=false;
    return;
  }

  if(state.mode==="outward"){ state.outward = res; $("costOut").textContent=res.cost.toFixed(2); $("cellsOut").textContent=res.cells; }
  else { state.returnPath = res; }
  state.step = 0;
  $("message").textContent=`Route recalculated around the hazard (${res.cells} cells, cost ${res.cost.toFixed(2)}).`;
  $("status").textContent = state.mode==="outward" ? "Travelling to target…" : "Returning to base…";
  draw();

  if(wasRunning && state.currentOnComplete){
    driveAlong(state.currentOnComplete);
  }
}

$("addHazard").addEventListener("click",()=>{
  if(!state.env)return;
  state.placingHazard=!state.placingHazard;
  if(state.placingHazard){
    $("addHazard").textContent="CLICK MAP TO PLACE…";
    $("addHazard").classList.add("active");
    $("message").textContent="Click anywhere on the map to place the new hazard.";
  }else{
    $("addHazard").textContent="SIMULATE NEW HAZARD";
    $("addHazard").classList.remove("active");
    $("message").textContent="Hazard placement cancelled.";
  }
});
$("clearHazards").addEventListener("click",()=>{state.hazards=[];draw();$("message").textContent="Simulated dynamic hazards cleared."});

$("compare").addEventListener("click",async()=>{
  const res=await fetch("/api/compare",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({start:state.start,goal:state.target,dynamic_obstacles:state.hazards})}).then(r=>r.json());
  const card=(x)=>`<div class="metric-line"><span>Reachable</span><b>${x.reachable?"Yes":"No"}</b></div>
  <div class="metric-line"><span>Path cost</span><b>${x.reachable?x.cost.toFixed(2):"—"}</b></div>
  <div class="metric-line"><span>Path cells</span><b>${x.cells}</b></div>
  <div class="metric-line"><span>Nodes explored</span><b>${x.explored}</b></div>
  <div class="metric-line"><span>Execution time</span><b>${x.time_ms.toFixed(3)} ms</b></div>`;
  $("aMetrics").innerHTML=card(res.astar);$("dMetrics").innerHTML=card(res.dijkstra);
  if(res.astar.reachable&&res.dijkstra.reachable){
    const faster=res.astar.time_ms<res.dijkstra.time_ms?"A*":"Dijkstra";
    $("comparisonResult").innerHTML=`For this measured test, <b>${faster}</b> completed the search faster. The page reports the observed result rather than assuming one algorithm is always better. Compare path cost, path length, nodes explored and execution time together.`;
  }else $("comparisonResult").textContent="At least one algorithm could not find a path for this scenario.";
});

loadEnv().catch(err=>{$("mapStatus").textContent="Could not load environment data.";console.error(err)});