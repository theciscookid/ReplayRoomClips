from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import glob
from agent_engine import process_agent_directive
from viral_master import process_youtube_clip

app = FastAPI(title="ReplayRoomClips Command Center")
os.makedirs("output_shorts", exist_ok=True)
app.mount("/shorts", StaticFiles(directory="output_shorts"), name="shorts")

class AgentRequest(BaseModel):
    directive: str
    target_file: str = "viral_master.py"

class ClipRequest(BaseModel):
    url: str
    start_time: int = 0
    duration: int = 30

@app.get("/", response_class=HTMLResponse)
def get_console():
    return """
    <!DOCTYPE html>
    <html>
    <head><title>ReplayRoomClips Studio</title></head>
    <body style="font-family:monospace; background:#1e1e1e; color:#d4d4d4; padding:20px;">
        <h2>ReplayRoomClips Automation Console</h2>
        
        <div style="background:#252526; padding:15px; border-radius:5px; margin-bottom:15px;">
            <h3>🎬 Shorts Bot (Clip Generator)</h3>
            <input type="text" id="yt_url" placeholder="Paste YouTube URL here..." style="width:60%; padding:8px;"><br><br>
            Start Time (sec): <input type="number" id="start_time" value="0" style="width:80px; padding:6px;"> 
            Duration (sec): <input type="number" id="duration" value="30" style="width:80px; padding:6px;"><br><br>
            <button onclick="generateClip()" style="padding:10px 20px; background:#28a745; color:white; border:none; font-weight:bold;">Generate Vertical Short</button>
            <pre id="clip_log" style="background:#111; padding:10px; color:#4ec9b0; margin-top:10px;">Ready for clipping task...</pre>
        </div>

        <div style="background:#252526; padding:15px; border-radius:5px; margin-bottom:15px;">
            <h3>🤖 Self-Evolving Code Agent</h3>
            Target File: <select id="target_file"><option value="viral_master.py">viral_master.py</option><option value="main.py">main.py</option></select><br><br>
            <input type="text" id="directive" placeholder="Enter upgrade directive..." style="width:70%; padding:8px;">
            <button onclick="runAgent()" style="padding:8px 15px; background:#0e639c; color:white; border:none;">Execute Agent</button>
            <pre id="agent_log" style="background:#111; padding:10px; color:#7aa2f7; margin-top:10px;">Agent standing by...</pre>
        </div>

        <div style="background:#252526; padding:15px; border-radius:5px;">
            <h3>📁 Output Gallery</h3>
            <ul id="gallery">Loading clips...</ul>
        </div>

        <script>
            async function loadGallery() {
                const res = await fetch('/clips/list');
                const data = await res.json();
                const list = document.getElementById('gallery');
                if (data.clips.length === 0) {
                    list.innerHTML = "No rendered clips yet.";
                } else {
                    list.innerHTML = data.clips.map(c => `<li><a href="/shorts/${c}" target="_blank">${c}</a></li>`).join('');
                }
            }
            
            async function generateClip() {
                const url = document.getElementById('yt_url').value;
                const start_time = parseInt(document.getElementById('start_time').value);
                const duration = parseInt(document.getElementById('duration').value);
                document.getElementById('clip_log').innerText = "Processing & rendering clip...";
                const res = await fetch('/clip/generate', {
                    method: 'POST', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ url: url, start_time: start_time, duration: duration })
                });
                const data = await res.json();
                document.getElementById('clip_log').innerText = data.result;
                loadGallery();
            }

            async function runAgent() {
                const directive = document.getElementById('directive').value;
                const target_file = document.getElementById('target_file').value;
                document.getElementById('agent_log').innerText = "Working...";
                const res = await fetch('/agent/evolve', {
                    method: 'POST', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ directive: directive, target_file: target_file })
                });
                const data = await res.json();
                document.getElementById('agent_log').innerText = data.result;
            }

            loadGallery();
        </script>
    </body>
    </html>
    """

@app.get("/clips/list")
def list_clips():
    videos = glob.glob("output_shorts/*.mp4")
    filenames = [os.path.basename(v) for v in videos]
    return {"clips": filenames}

@app.post("/clip/generate")
def generate(req: ClipRequest):
    res = process_youtube_clip(req.url, req.start_time, req.duration)
    return {"result": res}

@app.post("/agent/evolve")
def evolve(req: AgentRequest):
    res = process_agent_directive(req.directive, req.target_file)
    return {"result": res}
