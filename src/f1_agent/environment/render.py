"""T4A: lightweight top-down replay; rendering stays out of the training loop."""
import json
import math
from pathlib import Path
from typing import Any
from f1_agent.track.geometry import Point2D, Route
from f1_agent.training.interfaces import Action


def replay_episode(episode_path: Path, output_path: Path) -> None:
    """Render saved route, car states and actions; refuse to overwrite output.

    T4A selects a simple portable format (e.g. HTML canvas replay).
    Playback must not step physics again or import a learning framework.
    """
    records = _load_episode(Path(episode_path))
    metadata, steps, outcome = records
    data = {
        "route": metadata["route"],
        "steps": steps,
        "outcome": outcome,
    }
    embedded = json.dumps(data, separators=(",", ":"), allow_nan=False)
    embedded = embedded.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    page = _html_page(embedded)
    destination = Path(output_path)
    with destination.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(page)


def _load_episode(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    try:
        raw_lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ValueError(f"could not read replay episode: {exc}") from exc
    if len(raw_lines) < 4:
        raise ValueError("replay episode is empty or truncated")
    parsed = []
    for line_number, line in enumerate(raw_lines, 1):
        try:
            record = json.loads(line, parse_constant=_reject_constant)
        except (json.JSONDecodeError, ValueError) as exc:
            raise ValueError(f"invalid replay JSON on line {line_number}: {exc}") from exc
        if not isinstance(record, dict):
            raise ValueError(f"replay record on line {line_number} must be an object")
        parsed.append(record)
    metadata = parsed[0]
    if metadata.get("type") != "metadata" or type(metadata.get("schema_version")) is not int or metadata["schema_version"] != 1:
        raise ValueError("unsupported or missing replay metadata schema_version; expected 1")
    if set(metadata) != {"type", "schema_version", "route", "time_step_s", "vehicle", "observation", "effective_config", "route_seed", "episode_seed"}:
        raise ValueError("replay metadata has missing or unknown fields")
    route_data = metadata["route"]
    if not isinstance(route_data, dict) or set(route_data) != {"frame", "points", "closed", "width", "width_source", "source"}:
        raise ValueError("replay route metadata is malformed")
    if route_data["closed"] is not True or not isinstance(route_data["points"], list):
        raise ValueError("replay route must contain closed point geometry")
    points = []
    for pair in route_data["points"]:
        if not isinstance(pair, list) or len(pair) != 2 or not all(_finite(number) for number in pair):
            raise ValueError("replay route coordinates must be finite [x, y] pairs")
        points.append(Point2D(float(pair[0]), float(pair[1])))
    replay_route = Route(tuple(points), route_data["frame"], route_data["source"], route_data["width"], route_data["width_source"])
    if replay_route.frame != "map_metres" or replay_route.width is None:
        raise ValueError("replay requires a map_metres route with explicit road width")
    dt = metadata["time_step_s"]
    if not _finite(dt) or dt <= 0:
        raise ValueError("replay time_step_s must be finite and positive")
    if not isinstance(metadata["vehicle"], dict) or not isinstance(metadata["observation"], dict) or not isinstance(metadata["effective_config"], dict):
        raise ValueError("replay vehicle, observation and effective config metadata must be objects")
    if any(type(metadata[key]) is not int or metadata[key] < 0 for key in ("route_seed", "episode_seed")):
        raise ValueError("replay seeds must be nonnegative integers")
    if parsed[-1].get("type") != "outcome":
        raise ValueError("replay episode is truncated; final outcome record is missing")
    outcome = parsed[-1]
    if type(outcome.get("lap_complete")) is not bool or type(outcome.get("terminated")) is not bool or type(outcome.get("truncated")) is not bool:
        raise ValueError("replay outcome flags must be booleans")
    steps = parsed[1:-1]
    if len(steps) < 2:
        raise ValueError("replay episode needs a spawn frame and at least one recorded step")
    if steps[0].get("step") != 0 or steps[0].get("action") is not None:
        raise ValueError("first replay step must be the action-free spawn frame at step 0")
    for index, item in enumerate(steps):
        if item.get("type") != "step" or item.get("step") != index:
            raise ValueError("replay steps must be sequential and start at zero")
        numeric = ("time_s", "x_m", "y_m", "heading_rad", "speed_mps", "reward")
        if any(not _finite(item.get(key)) for key in numeric) or item["speed_mps"] < 0:
            raise ValueError(f"replay step {index} has invalid numeric state")
        if abs(item["time_s"] - index * dt) > 1e-7:
            raise ValueError(f"replay step {index} has inconsistent time")
        if type(item.get("terminated")) is not bool or type(item.get("truncated")) is not bool:
            raise ValueError(f"replay step {index} termination flags must be booleans")
        action = item.get("action")
        if index == 0:
            continue
        if not isinstance(action, dict) or set(action) != {"steer", "throttle", "brake"}:
            raise ValueError(f"replay step {index} has a malformed action")
        try:
            Action(action["steer"], action["throttle"], action["brake"])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"replay step {index} has an invalid action: {exc}") from exc
    if outcome.get("steps") != len(steps) - 1:
        raise ValueError("replay outcome step count does not match recorded steps")
    if steps[-1]["terminated"] != outcome["terminated"] or steps[-1]["truncated"] != outcome["truncated"]:
        raise ValueError("replay final step flags disagree with outcome")
    return metadata, steps, outcome


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant {value} is not allowed")


def _finite(value: object) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except (OverflowError, TypeError):
        return False


def _html_page(data: str) -> str:
    # All rendering uses the saved route/state payload; this page never imports
    # or executes the simulator and can be opened without network access.
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>F1 driving episode replay</title><style>
body{{margin:0;background:#10161c;color:#e8eef2;font:15px system-ui,sans-serif;display:grid;grid-template-rows:auto 1fr auto;height:100vh}}
header,footer{{padding:10px 16px;background:#18232c;display:flex;gap:16px;align-items:center;flex-wrap:wrap}}
header strong{{font-size:17px}} #status{{color:#b5c5d0}} canvas{{width:100%;height:100%;min-height:300px;display:block}} footer input{{flex:1;min-width:180px}}
button{{background:#2b4655;color:white;border:1px solid #527181;border-radius:5px;padding:6px 12px;cursor:pointer}}
</style></head><body><header><strong>Recorded drive replay</strong><span id="status"></span><span id="outcome"></span></header>
<canvas id="view"></canvas><footer><button id="toggle">Pause</button><input id="frame" type="range" min="0" value="0"><span id="counter"></span></footer>
<script>const data={data};const frames=data.steps;const route=data.route;const result=data.outcome;
const canvas=document.getElementById('view'),ctx=canvas.getContext('2d'),slider=document.getElementById('frame');
slider.max=String(frames.length-1);document.getElementById('outcome').textContent=result.lap_complete?'Lap complete':(result.failure_reason|| (result.truncated?'Time limit':'Episode ended'));
document.getElementById('status').textContent=`${{result.steps}} steps · ${{Number(result.elapsed_s).toFixed(1)}} s · ${{Number(result.progress_m).toFixed(1)}} m progress`;
let current=0,playing=true,last=0;document.getElementById('toggle').onclick=()=>{{playing=!playing;document.getElementById('toggle').textContent=playing?'Pause':'Play'}};
slider.oninput=()=>{{current=Number(slider.value);draw()}};
function draw(){{const dpr=window.devicePixelRatio||1,w=canvas.clientWidth,h=canvas.clientHeight;canvas.width=w*dpr;canvas.height=h*dpr;ctx.setTransform(dpr,0,0,dpr,0,0);ctx.fillStyle='#10161c';ctx.fillRect(0,0,w,h);
const all=route.points.concat(frames.map(f=>[f.x_m,f.y_m]));let minX=Math.min(...all.map(p=>p[0])),maxX=Math.max(...all.map(p=>p[0])),minY=Math.min(...all.map(p=>p[1])),maxY=Math.max(...all.map(p=>p[1]));
const pad=48,scale=Math.min((w-2*pad)/Math.max(1,maxX-minX),(h-2*pad)/Math.max(1,maxY-minY));const ox=(w-(maxX-minX)*scale)/2-minX*scale,oy=(h+(maxY-minY)*scale)/2+minY*scale;
ctx.setTransform(dpr*scale,0,0,-dpr*scale,dpr*ox,dpr*oy);ctx.lineCap='round';ctx.lineJoin='round';
ctx.beginPath();route.points.forEach((p,i)=>i?ctx.lineTo(p[0],p[1]):ctx.moveTo(p[0],p[1]));ctx.closePath();ctx.strokeStyle='#42525d';ctx.lineWidth=route.width;ctx.stroke();ctx.strokeStyle='#b6c4cc';ctx.lineWidth=Math.max(.15,route.width*.025);ctx.stroke();
ctx.beginPath();frames.slice(0,current+1).forEach((f,i)=>i?ctx.lineTo(f.x_m,f.y_m):ctx.moveTo(f.x_m,f.y_m));ctx.strokeStyle='#43e08b';ctx.lineWidth=Math.max(.2,route.width*.045);ctx.stroke();
const car=frames[current];ctx.save();ctx.translate(car.x_m,car.y_m);ctx.rotate(car.heading_rad);ctx.fillStyle='#ffcf4a';ctx.strokeStyle='#10161c';ctx.lineWidth=.12;ctx.beginPath();ctx.moveTo(2.3,0);ctx.lineTo(1.4,.85);ctx.lineTo(-1.8,.85);ctx.lineTo(-2.2,.45);ctx.lineTo(-2.2,-.45);ctx.lineTo(-1.8,-.85);ctx.lineTo(1.4,-.85);ctx.closePath();ctx.fill();ctx.stroke();ctx.restore();
document.getElementById('counter').textContent=`${{current+1}} / ${{frames.length}} · ${{Number(car.time_s).toFixed(2)}} s`;}}
function animate(t){{if(playing&&t-last>100){{last=t;current=Math.min(frames.length-1,current+1);slider.value=String(current);draw();if(current===frames.length-1)playing=false}}requestAnimationFrame(animate)}}
window.addEventListener('resize',draw);draw();requestAnimationFrame(animate);
</script></body></html>'''
