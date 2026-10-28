"""
LX04 AI 命令授权系统 - Web 版 (Sci-Fi HUD)
PC 端运行此脚本，LX04 通过浏览器访问授权界面
"""
import json
import time
import threading
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# ============ 配置 ============
PC_PORT = 9090          # PC 授权服务端口
WEB_PORT = 8080         # Web 界面端口
LX04_IP = None          # 自动检测

# ============ 数据存储 ============
pending_commands = []
authorized_commands = []
denied_commands = []
command_counter = 0
lock = threading.Lock()


def add_command(command, description="", risk_level="medium"):
    """添加待授权命令"""
    global command_counter
    with lock:
        command_counter += 1
        cmd = {
            "id": str(command_counter),
            "command": command,
            "description": description,
            "risk_level": risk_level,
            "timestamp": time.time(),
            "status": "pending",
        }
        pending_commands.append(cmd)
        print(f"  新命令 #{cmd['id']}: {command}")
        return cmd["id"]


def check_authorization(command, description="", risk_level="medium", timeout=120):
    """
    同步等待授权结果
    AI 在执行命令前调用此函数
    """
    cmd_id = add_command(command, description, risk_level)
    print(f"  等待授权 (超时 {timeout}s)...")

    start_time = time.time()
    while time.time() - start_time < timeout:
        time.sleep(0.5)
        with lock:
            for cmd in authorized_commands + denied_commands:
                if cmd["id"] == cmd_id:
                    if cmd["status"] == "authorized":
                        print(f"  已授权: {command}")
                        return True
                    else:
                        print(f"  已拒绝: {command}")
                        return False
    print(f"  超时未响应: {command}")
    return False


# ============ Web 界面 HTML (Sci-Fi HUD) ============
WEB_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI COMMAND AUTH // 授权终端</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Share+Tech+Mono&display=swap');

* { margin: 0; padding: 0; box-sizing: border-box; }

:root {
    --cyan: #00f0ff;
    --green: #05ffa1;
    --red: #ff2a6d;
    --amber: #ffb800;
    --bg: #050810;
    --panel: rgba(8, 16, 30, 0.85);
}

body {
    font-family: 'Share Tech Mono', 'Courier New', monospace;
    background: var(--bg);
    color: #c8e6ff;
    min-height: 100vh;
    padding: 0 16px 16px;
    overflow-x: hidden;
    position: relative;
}

/* ===== 背景动效层 ===== */
body::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image:
        linear-gradient(rgba(0, 240, 255, 0.04) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 240, 255, 0.04) 1px, transparent 1px);
    background-size: 40px 40px;
    animation: gridmove 8s linear infinite;
    pointer-events: none;
    z-index: 0;
}
body::after {
    content: '';
    position: fixed;
    inset: 0;
    background: repeating-linear-gradient(
        0deg, transparent 0px, transparent 2px, rgba(0, 0, 0, 0.15) 3px
    );
    pointer-events: none;
    z-index: 999;
}
@keyframes gridmove { from { background-position: 0 0; } to { background-position: 0 40px; } }

/* ===== 顶部 HUD ===== */
.header {
    position: relative;
    z-index: 1;
    text-align: center;
    padding: 28px 0 18px;
    border-bottom: 1px solid rgba(0, 240, 255, 0.25);
    margin-bottom: 24px;
}
.header h1 {
    font-family: 'Orbitron', monospace;
    font-size: 30px;
    font-weight: 900;
    letter-spacing: 6px;
    color: var(--cyan);
    text-shadow: 0 0 10px rgba(0,240,255,.8), 0 0 30px rgba(0,240,255,.4);
    text-transform: uppercase;
}
.header .sub {
    font-size: 12px;
    letter-spacing: 4px;
    color: rgba(0,240,255,.5);
    margin-top: 6px;
    text-transform: uppercase;
}
.header .status {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    letter-spacing: 2px;
    color: var(--green);
    text-shadow: 0 0 8px rgba(5,255,161,.6);
    margin-top: 12px;
}
.header .status.offline {
    color: var(--red);
    text-shadow: 0 0 8px rgba(255,42,109,.6);
}
.dot {
    width: 10px; height: 10px;
    border-radius: 50%;
    background: currentColor;
    animation: blink 1.2s ease-in-out infinite;
}
@keyframes blink { 0%,100% { opacity: 1; } 50% { opacity: .2; } }

/* ===== 扫描线扫过 ===== */
.sweepline {
    position: fixed;
    left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, rgba(0,240,255,.6), transparent);
    animation: sweep 4s linear infinite;
    pointer-events: none;
    z-index: 998;
}
@keyframes sweep { from { top: -2px; } to { top: 100vh; } }

/* ===== Tab 切换 ===== */
.tabs {
    position: relative;
    z-index: 1;
    display: flex;
    max-width: 720px;
    margin: 0 auto 20px;
    border: 1px solid rgba(0,240,255,.3);
    background: var(--panel);
    clip-path: polygon(12px 0, 100% 0, 100% calc(100% - 12px), calc(100% - 12px) 100%, 0 100%, 0 12px);
}
.tab {
    flex: 1;
    padding: 14px;
    text-align: center;
    cursor: pointer;
    font-size: 14px;
    letter-spacing: 3px;
    color: #5a7a99;
    text-transform: uppercase;
    transition: all .25s;
    position: relative;
}
.tab.active {
    color: var(--cyan);
    text-shadow: 0 0 8px rgba(0,240,255,.7);
    background: rgba(0,240,255,.08);
}
.tab.active::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 2px;
    background: var(--cyan);
    box-shadow: 0 0 10px var(--cyan);
}
.tab .count {
    background: var(--red);
    color: #fff;
    border-radius: 2px;
    padding: 1px 7px;
    font-size: 11px;
    margin-left: 6px;
    box-shadow: 0 0 8px rgba(255,42,109,.7);
}

/* ===== 命令卡片 ===== */
#tab-pending, #tab-history { position: relative; z-index: 1; max-width: 720px; margin: 0 auto; }

.command-card {
    background: var(--panel);
    border: 1px solid rgba(0,240,255,.35);
    padding: 20px;
    margin-bottom: 16px;
    position: relative;
    clip-path: polygon(16px 0, 100% 0, 100% calc(100% - 16px), calc(100% - 16px) 100%, 0 100%, 0 16px);
    animation: cardin .4s ease-out;
}
@keyframes cardin { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: none; } }
.command-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: var(--amber);
    box-shadow: 0 0 12px var(--amber);
}
.command-card.risk-high::before { background: var(--red); box-shadow: 0 0 12px var(--red); }
.command-card.risk-low::before  { background: var(--green); box-shadow: 0 0 12px var(--green); }

/* 四角标记 */
.corner { position: absolute; width: 14px; height: 14px; border-color: var(--cyan); border-style: solid; }
.corner.tl { top: 6px; left: 6px; border-width: 2px 0 0 2px; }
.corner.tr { top: 6px; right: 6px; border-width: 2px 2px 0 0; }
.corner.bl { bottom: 6px; left: 6px; border-width: 0 0 2px 2px; }
.corner.br { bottom: 6px; right: 6px; border-width: 0 2px 2px 0; }

.risk-badge {
    display: inline-block;
    padding: 3px 12px;
    font-size: 12px;
    font-weight: bold;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-bottom: 12px;
    border: 1px solid currentColor;
    text-shadow: 0 0 6px currentColor;
}
.risk-high .risk-badge { color: var(--red); background: rgba(255,42,109,.1); }
.risk-medium .risk-badge { color: var(--amber); background: rgba(255,184,0,.1); }
.risk-low .risk-badge { color: var(--green); background: rgba(5,255,161,.1); }

.command-text {
    font-family: 'Share Tech Mono', monospace;
    font-size: 17px;
    letter-spacing: 1px;
    color: var(--cyan);
    text-shadow: 0 0 6px rgba(0,240,255,.5);
    background: rgba(0, 20, 35, .9);
    border-left: 3px solid var(--cyan);
    padding: 14px 16px;
    margin: 10px 0;
    word-break: break-all;
}
.command-text::before { content: '> '; color: rgba(0,240,255,.4); }

.description {
    font-size: 13px;
    letter-spacing: 1px;
    color: #6a8aaa;
    margin: 10px 0 20px;
}
.description::before { content: '// '; color: rgba(106,138,170,.5); }

.btn-row { display: flex; gap: 14px; }
.btn {
    flex: 1;
    padding: 15px;
    border: 1px solid currentColor;
    background: transparent;
    font-family: 'Orbitron', monospace;
    font-size: 16px;
    font-weight: 700;
    letter-spacing: 4px;
    cursor: pointer;
    transition: all .2s;
    text-transform: uppercase;
    clip-path: polygon(10px 0, 100% 0, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0 100%, 0 10px);
}
.btn-deny { color: var(--red); background: rgba(255,42,109,.08); }
.btn-deny:hover { background: var(--red); color: #050810; box-shadow: 0 0 20px rgba(255,42,109,.8); }
.btn-allow { color: var(--green); background: rgba(5,255,161,.08); }
.btn-allow:hover { background: var(--green); color: #050810; box-shadow: 0 0 20px rgba(5,255,161,.8); }
.btn:active { transform: scale(.97); }

/* ===== 历史 ===== */
.history-item {
    background: var(--panel);
    border: 1px solid rgba(0,240,255,.15);
    padding: 12px 16px;
    margin-bottom: 8px;
    font-size: 13px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
}
.history-item .cmd { color: var(--cyan); font-family: monospace; flex: 1; word-break: break-all; }
.history-item .result { padding: 3px 10px; font-size: 11px; letter-spacing: 2px; border: 1px solid currentColor; white-space: nowrap; }
.result-ok { color: var(--green); text-shadow: 0 0 6px rgba(5,255,161,.5); }
.result-no { color: var(--red); text-shadow: 0 0 6px rgba(255,42,109,.5); }

/* ===== 空状态 ===== */
.empty-state {
    text-align: center;
    padding: 70px 20px;
    color: rgba(90,122,153,.7);
}
.empty-state .icon {
    font-family: 'Orbitron', monospace;
    font-size: 54px;
    color: rgba(0,240,255,.35);
    text-shadow: 0 0 20px rgba(0,240,255,.4);
    margin-bottom: 18px;
    animation: blink 2s ease-in-out infinite;
}
.empty-state p { font-size: 14px; letter-spacing: 3px; text-transform: uppercase; }
</style>
</head>
<body>

<div class="sweepline"></div>

<div class="header">
    <h1>AI Command Auth</h1>
    <div class="sub">// LX04 授权终端 v2.0 //</div>
    <div class="status" id="status"><span class="dot"></span>CONNECTING...</div>
</div>

<div class="tabs">
    <div class="tab active" onclick="showTab('pending', this)">
        Pending 待授权 <span class="count" id="pending-count">0</span>
    </div>
    <div class="tab" onclick="showTab('history', this)">
        History 记录
    </div>
</div>

<div id="tab-pending">
    <div id="commands-list"></div>
    <div class="empty-state" id="empty-state">
        <div class="icon">[ ... ]</div>
        <p>Awaiting Authorization Request</p>
        <p style="margin-top:8px; font-size:11px;">等待 AI 命令授权请求</p>
    </div>
</div>

<div id="tab-history" style="display:none">
    <div id="history-list"></div>
</div>

<script>
let currentTab = 'pending';

function showTab(tab, el) {
    currentTab = tab;
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    el.classList.add('active');
    document.getElementById('tab-pending').style.display = tab === 'pending' ? 'block' : 'none';
    document.getElementById('tab-history').style.display = tab === 'history' ? 'block' : 'none';
    if (tab === 'history') loadHistory();
}

function refresh() {
    fetch('/api/pending')
        .then(r => r.json())
        .then(data => {
            const st = document.getElementById('status');
            st.innerHTML = '<span class="dot"></span>ONLINE - MONITORING';
            st.className = 'status';
            document.getElementById('pending-count').textContent = data.length;

            const list = document.getElementById('commands-list');
            const empty = document.getElementById('empty-state');

            if (data.length === 0) {
                list.innerHTML = '';
                empty.style.display = 'block';
            } else {
                empty.style.display = 'none';
                list.innerHTML = data.map(cmd => {
                    const riskClass = 'risk-' + cmd.risk_level;
                    const riskLabel = {high:'High Risk',medium:'Med Risk',low:'Low Risk'}[cmd.risk_level] || 'Med Risk';
                    return `
                    <div class="command-card ${riskClass}">
                        <span class="corner tl"></span><span class="corner tr"></span>
                        <span class="corner bl"></span><span class="corner br"></span>
                        <span class="risk-badge">${riskLabel}</span>
                        <div class="command-text">${escapeHtml(cmd.command)}</div>
                        <div class="description">${escapeHtml(cmd.description || 'no description')}</div>
                        <div class="btn-row">
                            <button class="btn btn-deny" onclick="auth('${cmd.id}', false)">&#10007; Deny</button>
                            <button class="btn btn-allow" onclick="auth('${cmd.id}', true)">&#10003; Allow</button>
                        </div>
                    </div>`;
                }).join('');
            }
        })
        .catch(() => {
            const st = document.getElementById('status');
            st.innerHTML = '<span class="dot"></span>LINK LOST - RETRYING';
            st.className = 'status offline';
        });
}

function auth(id, allowed) {
    fetch('/api/auth', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({id: id, authorized: allowed})
    }).then(() => refresh());
}

function loadHistory() {
    fetch('/api/history')
        .then(r => r.json())
        .then(data => {
            const list = document.getElementById('history-list');
            if (data.length === 0) {
                list.innerHTML = '<div class="empty-state"><p>No Records / 暂无历史记录</p></div>';
                return;
            }
            list.innerHTML = data.map(cmd => {
                const cls = cmd.status === 'authorized' ? 'result-ok' : 'result-no';
                const label = cmd.status === 'authorized' ? 'ALLOWED' : 'DENIED';
                return `<div class="history-item">
                    <span class="cmd">${escapeHtml(cmd.command)}</span>
                    <span class="result ${cls}">${label}</span>
                </div>`;
            }).join('');
        });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

refresh();
setInterval(refresh, 2000);
</script>
</body>
</html>"""


# ============ HTTP 服务器 ============
class WebHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(WEB_HTML.encode("utf-8"))

        elif self.path.startswith("/api/check/"):
            # 查询单条命令状态: GET /api/check/<id>
            cmd_id = self.path.rsplit("/", 1)[-1]
            with lock:
                status = None
                for cmd in pending_commands + authorized_commands + denied_commands:
                    if cmd["id"] == cmd_id:
                        status = cmd["status"]
                        break
            self.send_json({"id": cmd_id, "status": status})

        elif self.path == "/api/pending":
            with lock:
                data = [c for c in pending_commands if c["status"] == "pending"]
            self.send_json(data)

        elif self.path == "/api/history":
            with lock:
                data = authorized_commands[-50:] + denied_commands[-50:]
                data.sort(key=lambda x: x["timestamp"], reverse=True)
                data = data[:50]
            self.send_json(data)

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/auth":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            cmd_id = body.get("id")
            authorized = body.get("authorized", False)

            with lock:
                for cmd in pending_commands:
                    if cmd["id"] == cmd_id:
                        cmd["status"] = "authorized" if authorized else "denied"
                        if authorized:
                            authorized_commands.append(cmd)
                        else:
                            denied_commands.append(cmd)
                        pending_commands.remove(cmd)
                        break

            self.send_json({"status": "ok"})

        elif self.path == "/api/add":
            # 外部 AI 提交待授权命令: POST /api/add
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            cmd_id = add_command(
                body.get("command", ""),
                body.get("description", ""),
                body.get("risk_level", "medium"),
            )
            self.send_json({"status": "ok", "id": cmd_id})
        else:
            self.send_response(404)
            self.end_headers()

    def send_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def log_message(self, format, *args):
        pass  # 静默日志


def get_local_ip():
    """获取本机局域网 IP"""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def run_server():
    from codex_quota_server import start_background
    start_background()
    local_ip = get_local_ip()
    print("=" * 50)
    print("  LX04 AI 命令授权系统 - Web 版 (Sci-Fi HUD)")
    print("=" * 50)
    print()
    print(f"  本机 IP: {local_ip}")
    print(f"  授权服务: http://{local_ip}:{PC_PORT}")
    print(f"  Web 界面: http://{local_ip}:{WEB_PORT}")
    print()
    print(f"  在 LX04 浏览器中打开:")
    print(f"  http://{local_ip}:{WEB_PORT}")
    print()
    print("  按 Ctrl+C 停止服务")
    print("=" * 50)
    print()

    # 启动 Web 界面服务器
    web_server = HTTPServer(("0.0.0.0", WEB_PORT), WebHandler)
    web_thread = threading.Thread(target=web_server.serve_forever, daemon=True)
    web_thread.start()

    print("Web 界面服务器已启动")

    # 尝试在本地浏览器打开
    try:
        webbrowser.open(f"http://localhost:{WEB_PORT}")
    except Exception:
        pass

    # 保持运行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n服务已停止")
        web_server.shutdown()


if __name__ == "__main__":
    run_server()
