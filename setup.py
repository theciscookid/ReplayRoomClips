import os

api_key_input = "YOUR_ACTUAL_API_KEY"

agent_code = f'''import os
import subprocess
import glob
from google import genai
from google.genai import errors

WORK_DIR = os.path.dirname(os.path.abspath(__file__))
GEMINI_API_KEY = "{api_key_input}"

def list_workspace_files():
    files = glob.glob(os.path.join(WORK_DIR, "*.py")) + glob.glob(os.path.join(WORK_DIR, "*.html"))
    return [os.path.basename(f) for f in files]

def read_local_file(filename: str) -> str:
    safe_path = os.path.join(WORK_DIR, os.path.basename(filename))
    if not os.path.exists(safe_path):
        return f"Error: File {{filename}} not found."
    with open(safe_path, "r", encoding="utf-8") as f:
        return f.read()

def write_local_file(filename: str, content: str) -> str:
    safe_path = os.path.join(WORK_DIR, os.path.basename(filename))
    with open(safe_path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Success: Updated {{filename}}"

def run_syntax_check(filename: str) -> dict:
    safe_path = os.path.join(WORK_DIR, os.path.basename(filename))
    if not filename.endswith(".py"):
        return {{"valid": True, "output": "Not a python file, skipped syntax check."}}
    result = subprocess.run(["python3", "-m", "py_compile", safe_path], capture_output=True, text=True)
    if result.returncode == 0:
        return {{"valid": True, "output": f"Syntax check passed for {{filename}}."}}
    else:
        return {{"valid": False, "output": result.stderr}}

def process_agent_directive(directive: str, target_file: str = "viral_master.py") -> str:
    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_ACTUAL_API_KEY":
        return "Error: Please update your Gemini API key in agent_engine.py."
    
    file_content = read_local_file(target_file)
    if file_content.startswith("Error:"):
        return file_content

    client = genai.Client(api_key=GEMINI_API_KEY)
    prompt = f"You are an expert autonomous software engineering agent upgrading a local developer environment. Modify the file `{{target_file}}` based on this directive: \\"{{directive}}\\". Here is the current content:\\n\\n{{file_content}}\\n\\nReturn ONLY the complete updated Python code block wrapped in ```python ... ```."

    try:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        raw_text = response.text.strip()
        
        if "```" in raw_text:
            parts = raw_text.split("```")
            for p in parts:
                if "def " in p or "import " in p:
                    new_code = p.replace("python\\n", "", 1).strip()
                    break
            else:
                new_code = raw_text
        else:
            new_code = raw_text

        write_local_file(target_file, new_code)
        syntax_res = run_syntax_check(target_file)
        
        if syntax_res["valid"]:
            return f"Successfully evolved {{target_file}} via Gemini AI!\\n{{syntax_res['output']}}"
        else:
            return f"Warning: Agent applied changes, but syntax check failed:\\n{{syntax_res['output']}}"
    except Exception as e:
        return f"Error during agent execution: {{e}}"
'''

main_code = '''from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import subprocess
import os
import json
import datetime
from agent_engine import process_agent_directive, list_workspace_files, read_local_file

app = FastAPI(title="Self-Evolving Local Console")

os.makedirs("output_shorts", exist_ok=True)
app.mount("/shorts", StaticFiles(directory="output_shorts"), name="shorts")

CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"discord_webhook": ""}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

class TaskRequest(BaseModel):
    script_name: str
    arg: str = ""

class WebhookRequest(BaseModel):
    webhook_url: str

class AgentRequest(BaseModel):
    directive: str
    target_file: str = "viral_master.py"

console_state = {
    "status": "Idle",
    "running_script": "None",
    "last_output": "No output yet.",
    "last_trade_signal": "Waiting for webhook alerts...",
    "agent_log": "Agent standing by for directives..."
}

def run_local_script(script_path: str, arg: str):
    global console_state
    console_state["status"] = "Running"
    console_state["running_script"] = script_path
    
    env = os.environ.copy()
    config = load_config()
    if config.get("discord_webhook"):
        env["DISCORD_WEBHOOK_URL"] = config["discord_webhook"]

    try:
        cmd = ["python3", script_path]
        if arg:
            cmd.append(arg)
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, env=env)
        console_state["last_output"] = result.stdout or "Script executed successfully with no stdout."
        console_state["status"] = "Completed"
    except subprocess.CalledProcessError as e:
        console_state["last_output"] = f"SUBPROCESS ERROR:\\n{e.stderr or e.stdout}"
        console_state["status"] = "Failed"
    except Exception as e:
        console_state["last_output"] = f"GENERAL ERROR:\\n{str(e)}"
        console_state["status"] = "Failed"

@app.get("/", response_class=HTMLResponse)
def get_console():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Self-Evolving Local Console</title>
        <style>
            body { font-family: monospace; background: #1e1e1e; color: #d4d4d4; margin: 0; padding: 20px; }
            h1 { color: #4ec9b0; margin-top: 0; }
            .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
            .card { background: #252526; border: 1px solid #333; padding: 15px; border-radius: 4px; }
            .full-width { grid-column: span 2; }
            input[type="text"] { background: #3c3c3c; border: 1px solid #555; color: white; padding: 8px; width: calc(100% - 110px); font-family: monospace; margin-right: 5px; border-radius: 3px; }
            select { background: #3c3c3c; color: white; border: 1px solid #555; padding: 8px; font-family: monospace; border-radius: 3px; margin-right: 5px; }
            button { background: #0e639c; color: white; border: none; padding: 8px 15px; cursor: pointer; font-family: monospace; border-radius: 3px; margin-top: 5px; }
            button:hover { background: #1177bb; }
            pre { background: #111; padding: 12px; overflow-x: auto; color: #ce9178; max-height: 200px; border-radius: 4px; }
            .status-idle { color: #dcdcaa; }
            .status-running { color: #4ec9b0; }
            .status-completed { color: #4fc1ff; }
            .status-failed { color: #f44747; }
            .agent-box { background: #1b2838; border: 1px solid #2d4f6c; padding: 10px; border-radius: 4px; color: #7aa2f7; white-space: pre-wrap; max-height: 150px; overflow-y: auto; }
            .gallery-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 15px; margin-top: 10px; }
            .short-card { background: #1e1e1e; border: 1px solid #444; padding: 10px; border-radius: 4px; text-align: center; }
            video { width: 100%; max-height: 320px; border-radius: 4px; background: black; }
        </style>
    </head>
    <body>
        <h1>Autonomous Self-Evolving Console</h1>
        
        <div class="grid">
            <div class="card">
                <h3>System Status</h3>
                <p>State: <span id="status" class="status-idle">Idle</span></p>
                <p>Active Task: <span id="running-script">None</span></p>
            </div>

            <div class="card">
                <h3>Discord Webhook Config</h3>
                <div style="margin-bottom: 5px;">
                    <input type="text" id="webhookInput" placeholder="Paste Discord webhook URL...">
                    <button onclick="saveWebhook()">Save</button>
                </div>
                <p style="font-size: 11px; color: #888; margin: 0;" id="webhookStatus">Status: Not Configured</p>
            </div>

            <div class="card full-width" style="border: 1px solid #7aa2f7;">
                <h3 style="color: #7aa2f7;">Autonomous Code Agent & Self-Evolution</h3>
                <p style="font-size: 12px; color: #aaa;">Instruct the local agent to modify, upgrade, or debug your workspace files.</p>
                <div style="margin-bottom: 10px; display: flex; gap: 5px;">
                    <select id="agentTarget">
                        <option value="viral_master.py">viral_master.py</option>
                        <option value="main.py">main.py</option>
                        <option value="agent_engine.py">agent_engine.py</option>
                    </select>
                    <input type="text" id="agentDirective" placeholder="Enter evolution directive...">
                    <button onclick="triggerAgent()" style="background: #2d4f6c;">Execute Agent</button>
                </div>
                <div class="agent-box" id="agent-log">Agent standing by...</div>
            </div>

            <div class="card">
                <h3>Shorts Bot (`viral_master.py`)</h3>
                <div style="margin-bottom: 10px;">
                    <input type="text" id="botArg" placeholder="Enter YouTube URL...">
                    <button onclick="triggerTaskWithArg('viral_master.py')">Generate Clips</button>
                </div>
            </div>

            <div class="card">
                <h3>TradingView Signal Feed</h3>
                <div style="background: #1a3322; border: 1px solid #285430; padding: 10px; border-radius: 4px; color: #a3be8c; max-height: 80px; overflow-y: auto;" id="trade-signal">Waiting for alerts...</div>
            </div>

            <div class="card full-width">
                <h3>ReplayRoomClips Output Gallery</h3>
                <div class="gallery-grid" id="shorts-gallery">
                    <p style="color: #777;">No rendered shorts found yet.</p>
                </div>
            </div>

            <div class="card full-width">
                <h3>Execution Output / Logs</h3>
                <pre id="output">No output yet.</pre>
            </div>
        </div>

        <script>
            async function fetchStatus() {
                const res = await fetch('/status');
                const data = await res.json();
                const statusEl = document.getElementById('status');
                statusEl.innerText = data.status;
                statusEl.className = 'status-' + data.status.toLowerCase();
                document.getElementById('running-script').innerText = data.running_script || 'None';
                document.getElementById('trade-signal').innerText = data.last_trade_signal;
                document.getElementById('agent-log').innerText = data.agent_log;
                if (data.last_output) {
                    document.getElementById('output').innerText = data.last_output;
                }
            }

            async function triggerAgent() {
                const directive = document.getElementById('agentDirective').value;
                const targetFile = document.getElementById('agentTarget').value;
                if(!directive) { alert('Please enter a directive.'); return; }
                
                document.getElementById('agent-log').innerText = "Agent is working on code evolution...";
                const res = await fetch('/agent/evolve', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ directive: directive, target_file: targetFile })
                });
                const data = await res.json();
                document.getElementById('agent-log').innerText = data.result;
                fetchStatus();
            }

            async function fetchGallery() {
                const res = await fetch('/gallery');
                const files = await res.json();
                const galleryEl = document.getElementById('shorts-gallery');
                if (files.length === 0) {
                    galleryEl.innerHTML = '<p style="color: #777;">No rendered shorts found yet.</p>';
                    return;
                }
                let html = '';
                files.forEach(file => {
                    html += `
                        <div class="short-card">
                            <video controls src="/shorts/${file}"></video>
                            <p style="font-size: 11px; word-break: break-all; margin: 5px 0;">${file}</p>
                            <a href="/shorts/${file}" download style="color: #4fc1ff; font-size: 11px; text-decoration: none;">Download MP4</a>
                        </div>
                    `;
                });
                galleryEl.innerHTML = html;
            }

            async function saveWebhook() {
                const url = document.getElementById('webhookInput').value;
                await fetch('/config/webhook', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ webhook_url: url })
                });
                loadConfig();
                alert('Discord Webhook saved!');
            }

            async function loadConfig() {
                const res = await fetch('/config');
                const data = await res.json();
                if (data.discord_webhook) {
                    document.getElementById('webhookInput').value = data.discord_webhook;
                    document.getElementById('webhookStatus').innerText = 'Status: Active & Linked';
                    document.getElementById('webhookStatus').style.color = '#4ec9b0';
                }
            }

            async function triggerTask(scriptName, arg) {
                await fetch('/run', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ script_name: scriptName, arg: arg })
                });
                fetchStatus();
            }

            async function triggerTaskWithArg(scriptName) {
                const arg = document.getElementById('botArg').value;
                if(!arg) { alert('Please enter a YouTube URL'); return; }
                await triggerTask(scriptName, arg);
                setTimeout(fetchGallery, 5000);
            }

            setInterval(() => {
                fetchStatus();
                fetchGallery();
            }, 3000);

            loadConfig();
            fetchGallery();
        </script>
    </body>
    </html>
    """

@app.get("/status")
def get_status():
    return console_state

@app.post("/agent/evolve")
def evolve_code(req: AgentRequest):
    global console_state
    result = process_agent_directive(req.directive, req.target_file)
    console_state["agent_log"] = f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Directive: {req.directive}\\n{{result}}"
    return {"result": result}

@app.get("/gallery")
def get_gallery():
    if not os.path.exists("output_shorts"):
        return []
    files = [f for f in os.listdir("output_shorts") if f.endswith(".mp4")]
    files.sort(key=lambda x: os.path.getmtime(os.path.join("output_shorts", x)), reverse=True)
    return files

@app.get("/config")
def get_config():
    return load_config()

@app.post("/config/webhook")
def update_webhook(req: WebhookRequest):
    config = load_config()
    config["discord_webhook"] = req.webhook_url
    save_config(config)
    return {"status": "success"}

@app.post("/run")
def trigger_run(req: TaskRequest, background_tasks: BackgroundTasks):
    if os.path.exists(req.script_name):
        background_tasks.add_task(run_local_script, req.script_name, req.arg)
        return {"message": f"Started {{req.script_name}}"}
    return {"error": f"Script {{req.script_name}} not found."}

@app.post("/webhook/tradingview")
async def tradingview_webhook(request: Request):
    global console_state
    try:
        body = await request.body()
        payload = body.decode("utf-8")
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        console_state["last_trade_signal"] = f"[{{timestamp}}] {{payload}}"
        return {"status": "success", "received": payload}
    except Exception as e:
        return {"status": "error", "message": str(e)}
'''

viral_code = '''import os
import sys
import yt_dlp
from faster_whisper import WhisperModel
from moviepy.editor import VideoFileClip

def download_video(url: str, output_dir: str = "downloads") -> str:
    os.makedirs(output_dir, exist_ok=True)
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': os.path.join(output_dir, '%(id)s.%(ext)s'),
    }
    print(f"[-] Downloading video from URL: {url}")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
    print(f"[+] Downloaded successfully: {filename}")
    return filename

def transcribe_and_detect_clips(video_path: str):
    print("[-] Loading Whisper model...")
    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, info = model.transcribe(video_path, word_timestamps=True)
    
    all_words = []
    for segment in segments:
        if segment.words:
            for word in segment.words:
                all_words.append({"word": word.word.strip(), "start": word.start, "end": word.end})
                
    if not all_words:
        print("[!] No words transcribed.")
        return []

    clips = []
    total_duration = all_words[-1]["end"]
    current_start = 0.0
    while current_start < total_duration:
        current_end = min(current_start + 40, total_duration)
        window_words = [w for w in all_words if current_start <= w["start"] < current_end]
        if len(window_words) > 10:
            clips.append({
                "start": window_words[0]["start"],
                "end": window_words[-1]["end"],
                "score": 85
            })
        current_start += 30
    return clips[:3]

def render_short(video_path: str, clip_info: dict, output_path: str):
    start_time = max(0, clip_info["start"] - 0.2)
    end_time = clip_info["end"] + 0.2
    print(f"[-] Rendering vertical clip -> {output_path}")
    
    with VideoFileClip(video_path) as video:
        subclip = video.subclip(start_time, end_time)
        w, h = subclip.size
        target_w = int(h * (9 / 16))
        x_center = w / 2
        x1 = max(0, x_center - (target_w / 2))
        x2 = min(w, x_center + (target_w / 2))
        
        cropped = subclip.crop(x1=x1, y1=0, x2=x2, y2=h).resize(height=1920)
        cropped.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=30, preset="ultrafast", logger=None)
    print(f"[+] Successfully generated: {output_path}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 viral_master.py <YouTube_URL>")
        sys.exit(1)
    url = sys.argv[1]
    video_file = download_video(url)
    clips = transcribe_and_detect_clips(video_file)
    os.makedirs("output_shorts", exist_ok=True)
    for idx, clip in enumerate(clips):
        render_short(video_file, clip, f"output_shorts/ReplayRoom_Short_{idx+1}.mp4")
    print("[+] All clips generated!")

if __name__ == "__main__":
    main()
'''

with open("agent_engine.py", "w") as f:
    f.write(agent_code)

with open("main.py", "w") as f:
    f.write(main_code)

with open("viral_master.py", "w") as f:
    f.write(viral_code)

print("Setup completed successfully! agent_engine.py, main.py, and viral_master.py have been created.")
