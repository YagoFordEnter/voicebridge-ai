"""
web_companion.py — VoiceBridge AI
Real-time Mobile Companion server for iPhone 13 / mobile browsers via local Wi-Fi.

Runs FastAPI + WebSockets on port 8000 in a daemon thread.
Serves a responsive mobile-first dark interface (OLED black, high legibility):
  - Live synchronized Teleprompter text & fuzzy scroll position
  - Live streamed Copilot interview responses (tokens + completed answers)
  - Quick action controls: Font Size (A- / A+), Mode Toggle (SCRIPT / INTERVIEW),
    Clear Text, and Paste Script directly from mobile clipboard.
"""
from __future__ import annotations

import asyncio
import json
import logging
import socket
import threading
from typing import Callable, Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import uvicorn

logger = logging.getLogger("voicebridge.web")

# ---------------------------------------------------------------------------
# Utility: Detect primary Local Wi-Fi IPv4 address
# ---------------------------------------------------------------------------
def get_local_ip() -> str:
    """Returns the local IPv4 address of this machine on the active LAN/Wi-Fi."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Doesn't need to actually reach external host, just queries the OS routing table
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


# ---------------------------------------------------------------------------
# Companion Server State & Event Hub
# ---------------------------------------------------------------------------
class WebCompanionServer:
    def __init__(
        self,
        port: int = 8000,
        on_script_submitted: Callable[[str], None] | None = None,
        on_mode_toggled: Callable[[], None] | None = None,
    ):
        self.port = port
        self.on_script_submitted = on_script_submitted
        self.on_mode_toggled = on_mode_toggled

        self.app = FastAPI(title="VoiceBridge AI Mobile Companion")
        self.active_connections: Set[WebSocket] = set()
        self.loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None

        # Cached state to deliver immediately upon client connection
        self.current_mode = "SCRIPT"
        self.current_text = ""
        self.current_scroll_fraction = 0.0

        self._setup_routes()

    def _setup_routes(self) -> None:
        @self.app.get("/", response_class=HTMLResponse)
        async def index():
            return HTML_PAGE

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.active_connections.add(websocket)
            logger.info("📱 iPhone / Client connected to Web Companion")

            # Send current snapshot on connect
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "sync",
                        "mode": self.current_mode,
                        "text": self.current_text,
                        "fraction": self.current_scroll_fraction,
                    }
                )
            )

            try:
                while True:
                    data = await websocket.receive_text()
                    msg = json.loads(data)
                    msg_type = msg.get("type")

                    if msg_type == "paste_script":
                        script_text = msg.get("text", "").strip()
                        if script_text and self.on_script_submitted:
                            self.current_text = script_text
                            self.on_script_submitted(script_text)
                    elif msg_type == "toggle_mode":
                        if self.on_mode_toggled:
                            self.on_mode_toggled()
            except WebSocketDisconnect:
                self.active_connections.discard(websocket)
                logger.info("📱 Client disconnected from Web Companion")
            except Exception as e:
                logger.error("WebSocket error: %s", e)
                self.active_connections.discard(websocket)

    # -----------------------------------------------------------------------
    # Thread-safe broadcast methods (called from backend / Qt threads)
    # -----------------------------------------------------------------------
    def broadcast(self, payload: dict) -> None:
        """Schedules a JSON broadcast to all connected mobile clients."""
        if not self.loop or self.loop.is_closed():
            return
        asyncio.run_coroutine_threadsafe(self._async_broadcast(payload), self.loop)

    async def _async_broadcast(self, payload: dict) -> None:
        if not self.active_connections:
            return
        data = json.dumps(payload)
        dead = []
        for ws in self.active_connections:
            try:
                await ws.send_text(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.active_connections.discard(ws)

    def update_mode(self, mode: str) -> None:
        self.current_mode = mode
        self.broadcast({"type": "mode", "mode": mode})

    def update_teleprompter_view(self, before: str, highlight: str, after: str, fraction: float) -> None:
        self.current_scroll_fraction = fraction
        self.broadcast(
            {
                "type": "teleprompter",
                "before": before,
                "highlight": highlight,
                "after": after,
                "fraction": fraction,
            }
        )

    def update_copilot_token(self, token: str) -> None:
        self.broadcast({"type": "copilot_token", "token": token})

    def update_copilot_complete(self, full_text: str) -> None:
        self.current_text = full_text
        self.broadcast({"type": "copilot_complete", "text": full_text})

    def update_status(self, status: str) -> None:
        self.broadcast({"type": "status", "status": status})

    # -----------------------------------------------------------------------
    # Server Lifecycle
    # -----------------------------------------------------------------------
    def start(self) -> str:
        """Starts uvicorn in a background daemon thread and returns access URL."""
        local_ip = get_local_ip()
        url = f"http://{local_ip}:{self.port}"

        def run():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            config = uvicorn.Config(
                app=self.app,
                host="0.0.0.0",
                port=self.port,
                log_level="warning",
                loop="asyncio",
            )
            server = uvicorn.Server(config)
            self.loop.run_until_complete(server.serve())

        self._thread = threading.Thread(target=run, daemon=True, name="web-companion")
        self._thread.start()
        logger.info("🌐 Web Companion active on: %s", url)
        return url


# ---------------------------------------------------------------------------
# Responsive Mobile-First HTML Page (OLED Dark UI)
# ---------------------------------------------------------------------------
HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>VoiceBridge AI Companion</title>
  <style>
    * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
    body {
      margin: 0;
      padding: 0;
      background-color: #000000;
      color: #E2E8F0;
      font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, sans-serif;
      height: 100vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    header {
      background: #090D14;
      border-bottom: 1px solid #1E293B;
      padding: 10px 14px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }
    .badge {
      font-size: 11px;
      font-weight: 700;
      padding: 5px 9px;
      border-radius: 6px;
      letter-spacing: 0.5px;
      text-transform: uppercase;
    }
    .mode-script { background: rgba(56, 189, 248, 0.15); color: #38BDF8; border: 1px solid rgba(56, 189, 248, 0.4); }
    .mode-interview { background: rgba(74, 222, 128, 0.15); color: #4ADE80; border: 1px solid rgba(74, 222, 128, 0.4); }
    .status-text { font-size: 11px; color: #64748B; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 110px; }
    .btn-group { display: flex; gap: 6px; }
    button {
      background: #1E293B;
      color: #F8FAFC;
      border: 1px solid #334155;
      border-radius: 8px;
      padding: 6px 11px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
    }
    button:active { background: #38BDF8; color: #000; }
    #container {
      flex: 1;
      padding: 18px 16px;
      overflow-y: auto;
      scroll-behavior: smooth;
    }
    #content {
      font-size: 24px;
      line-height: 1.55;
      word-break: break-word;
      transition: font-size 0.15s ease;
    }
    .before-text { color: #64748B; }
    .highlight-text {
      color: #FFFFFF;
      background: rgba(56, 189, 248, 0.35);
      border-bottom: 2px solid #38BDF8;
      border-radius: 4px;
      padding: 2px 4px;
      font-weight: 700;
    }
    .after-text { color: #CBD5E1; }
    .bullet { display: block; margin-bottom: 12px; color: #F1F5F9; }
    footer {
      background: #090D14;
      border-top: 1px solid #1E293B;
      padding: 10px 12px;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .input-row { display: flex; gap: 8px; }
    textarea {
      flex: 1;
      height: 40px;
      background: #0F172A;
      color: #F8FAFC;
      border: 1px solid #334155;
      border-radius: 8px;
      padding: 8px;
      font-size: 13px;
      resize: none;
    }
    .btn-action { background: #0284C7; border: none; font-size: 13px; padding: 0 14px; font-weight: 700; }
  </style>
</head>
<body>
  <header>
    <div id="modeBadge" class="badge mode-script" onclick="toggleMode()">📜 SCRIPT</div>
    <div class="btn-group">
      <button onclick="changeFontSize(-2)">A−</button>
      <button onclick="changeFontSize(2)">A+</button>
      <button onclick="clearText()">Clear</button>
    </div>
    <div id="status" class="status-text">Connected</div>
  </header>

  <div id="container">
    <div id="content"><span class="after-text">Ready. Load a script or start speaking...</span></div>
  </div>

  <footer>
    <div class="input-row">
      <textarea id="scriptInput" placeholder="Paste script from iPhone here..."></textarea>
      <button class="btn-action" onclick="sendScript()">Send</button>
    </div>
  </footer>

  <script>
    let ws;
    let currentFontSize = 24;
    let copilotBuffer = "";

    function connect() {
      const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
      ws = new WebSocket(`${proto}//${location.host}/ws`);

      ws.onopen = () => {
        document.getElementById('status').innerText = 'Online ✓';
      };

      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        const content = document.getElementById('content');
        const container = document.getElementById('container');

        if (msg.type === 'sync') {
          updateModeBadge(msg.mode);
          if (msg.text) content.innerHTML = msg.text;
        } else if (msg.type === 'mode') {
          updateModeBadge(msg.mode);
          copilotBuffer = "";
          content.innerHTML = `<span style="color:#64748B;">Mode: ${msg.mode}...</span>`;
        } else if (msg.type === 'teleprompter') {
          content.innerHTML = `
            <span class="before-text">${msg.before} </span>
            <span class="highlight-text">${msg.highlight}</span>
            <span class="after-text"> ${msg.after}</span>
          `;
          if (msg.fraction !== undefined) {
            container.scrollTop = msg.fraction * (container.scrollHeight - container.clientHeight);
          }
        } else if (msg.type === 'copilot_token') {
          copilotBuffer += msg.token;
          const formatted = copilotBuffer.replace(/\|/g, '<br><span class="bullet">• ').replace(/\*\*/g, '');
          content.innerHTML = `<span style="color:#F8FAFC;">${formatted}</span>`;
          container.scrollTop = container.scrollHeight;
        } else if (msg.type === 'copilot_complete') {
          copilotBuffer = "";
          const formatted = msg.text.replace(/\|/g, '<br><span class="bullet">• ').replace(/\*\*/g, '');
          content.innerHTML = `<span style="color:#F8FAFC;">${formatted}</span>`;
        } else if (msg.type === 'status') {
          document.getElementById('status').innerText = msg.status;
        }
      };

      ws.onclose = () => {
        document.getElementById('status').innerText = 'Offline ✗ Reconnecting...';
        setTimeout(connect, 2000);
      };
    }

    function updateModeBadge(mode) {
      const badge = document.getElementById('modeBadge');
      if (mode === 'INTERVIEW') {
        badge.className = 'badge mode-interview';
        badge.innerText = '🎙️ INTERVIEW';
      } else {
        badge.className = 'badge mode-script';
        badge.innerText = '📜 SCRIPT';
      }
    }

    function toggleMode() {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'toggle_mode' }));
      }
    }

    function changeFontSize(delta) {
      currentFontSize = Math.min(42, Math.max(16, currentFontSize + delta));
      document.getElementById('content').style.fontSize = currentFontSize + 'px';
    }

    function clearText() {
      copilotBuffer = "";
      document.getElementById('content').innerHTML = '<span style="color:#64748B;">Cleared</span>';
    }

    function sendScript() {
      const input = document.getElementById('scriptInput');
      const text = input.value.trim();
      if (text && ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'paste_script', text: text }));
        input.value = '';
      }
    }

    window.onload = connect;
  </script>
</body>
</html>
"""
