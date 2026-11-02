"""Read-only LAN quota display.

Two independent, read-only sources, both served from this single 8081 process:
  - Codex:     reads Codex CLI token_count usage windows from session jsonl.
  - WorkBuddy: reads WorkBuddy daily-credits (Buddy加油站) balance from fuel-state.json.

No credentials are transmitted; only derived, non-sensitive aggregates leave this process.
"""
import json, os, pathlib, threading, time
from datetime import datetime, date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SESSION_ROOT = pathlib.Path(os.environ.get('LX04_CODEX_SESSIONS', str(pathlib.Path(os.environ['USERPROFILE']) / '.codex' / 'sessions')))
WORKBUDDY_CREDITS = pathlib.Path(os.environ.get('LX04_WORKBUDDY_CREDITS', str(pathlib.Path(os.environ['USERPROFILE']) / '.workbuddy' / 'wb-daily-credits' / 'state' / 'fuel-state.json')))

_lock = threading.Lock()
_cache = {
    'codex':      {'available': False, 'stale': True, 'windows': [], 'updated_at': None, 'source': 'codex_usage_record'},
    'workbuddy': {'available': False, 'stale': True, 'total': None, 'streak': None, 'claimed_today': False, 'updated_at': None, 'source': 'workbuddy_credits'},
}


# ---------- Codex (token_count windows) ----------
def window(raw, name, now):
    if not isinstance(raw, dict): return None
    used = raw.get('used_percent')
    reset = raw.get('resets_at')
    duration = raw.get('window_minutes')
    if not isinstance(used, (int, float)) or isinstance(used, bool): return None
    if not isinstance(reset, (int, float)) or not isinstance(duration, (int, float)): return None
    return {'name': name, 'remaining_percent': max(0, min(100, 100-used)), 'window_minutes': duration,
            'resets_at': reset, 'expired': reset <= now}


def normalize(raw, timestamp, now=None):
    now = time.time() if now is None else now
    updated = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).timestamp()
    windows = [w for key, title in [('primary', '短期额度'), ('secondary', '长期额度')]
               if (w := window(raw.get(key), title, now)) is not None]
    return {'available': bool(windows), 'stale': now-updated > 300 or any(w['expired'] for w in windows),
            'windows': windows, 'updated_at': updated, 'source': 'codex_usage_record'}


def latest_record():
    # Only recent days, tail bounded per file; conversation content never leaves this process.
    newest = None
    today = datetime.now().date()
    from datetime import timedelta
    candidates=[]
    for delta in range(3):
        day=today-timedelta(days=delta)
        folder=SESSION_ROOT / f'{day.year:04}' / f'{day.month:02}' / f'{day.day:02}'
        candidates.extend(folder.glob('*.jsonl'))
    for path in candidates:
        try:
            with path.open('rb') as f:
                f.seek(max(0, path.stat().st_size-512*1024))
                lines=f.read().splitlines()
            for line in reversed(lines):
                try: item=json.loads(line)
                except (ValueError, UnicodeDecodeError): continue
                payload=item.get('payload', {})
                raw=payload.get('rate_limits') if payload.get('type')=='token_count' else None
                if raw and raw.get('limit_id', 'codex')=='codex':
                    value=normalize(raw,item['timestamp'])
                    if newest is None or value['updated_at'] > newest['updated_at']: newest=value
                    break
        except (OSError, ValueError, KeyError): continue
    return newest


# ---------- WorkBuddy (daily-credits / Buddy加油站) ----------
def latest_workbuddy():
    try:
        raw = json.loads(WORKBUDDY_CREDITS.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    if not isinstance(raw, dict):
        return None
    total = raw.get('total')
    streak = raw.get('streak')
    try: total = int(total)
    except (TypeError, ValueError): total = None
    try: streak = int(streak)
    except (TypeError, ValueError): streak = None

    updated = None
    at = raw.get('at')
    if isinstance(at, str):
        try:
            updated = datetime.strptime(at, '%Y-%m-%dT%H:%M:%S').timestamp()
        except ValueError:
            updated = None

    today = date.today().isoformat()
    claimed_today = (raw.get('date') == today) and str(raw.get('status', '')).lower() in ('ok', 'claimed')
    stale = (raw.get('date') != today) or (updated is not None and time.time() - updated > 86400)

    return {'available': True, 'mode': 'workbuddy', 'total': total, 'streak': streak,
            'claimed_today': claimed_today, 'updated_at': updated, 'stale': stale,
            'source': 'workbuddy_credits'}


def refresh():
    global _cache
    while True:
        cx = latest_record()
        wb = latest_workbuddy()
        with _lock:
            if cx: _cache['codex'] = cx
            if wb: _cache['workbuddy'] = wb
        time.sleep(15)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/codex-usage':
            with _lock: value = json.loads(json.dumps(_cache['codex']))
            if value.get('updated_at'):
                value['stale'] = value['stale'] or time.time() - value['updated_at'] > 300
            self._send(value); return
        if self.path == '/api/workbuddy-usage':
            with _lock: value = json.loads(json.dumps(_cache['workbuddy']))
            self._send(value); return
        self.send_error(404)

    def _send(self, value):
        body = json.dumps(value, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args): pass


def start_background():
    try:
        server = ThreadingHTTPServer(('0.0.0.0', 8081), Handler)
    except OSError:
        return False  # An existing quota service may already own this port.
    threading.Thread(target=refresh, daemon=True).start()
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return True


if __name__ == '__main__':
    server = ThreadingHTTPServer(('0.0.0.0', 8081), Handler)
    threading.Thread(target=refresh, daemon=True).start()
    server.serve_forever()
