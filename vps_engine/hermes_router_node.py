#!/usr/bin/env python3
"""
Hermes Agent + 9Router / LiteLLM Gateway + Telegram Bot + Tailscale Node
========================================================================
Runs on Port 4000 (OpenAI-compatible /v1/chat/completions router + Web Config UI)
and runs a background Telegram Bot polling loop + 24/7 Farming Cron Worker.
"""

import hashlib
import http.server
import json
import os
import platform
import shutil
import socketserver
import sqlite3
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parent
DATA_DIR = ENGINE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_PATH = DATA_DIR / "router_telegram_config.json"
DB_PATH = DATA_DIR / "empire_workhorse.db"

START_TIME = time.time()
TELEGRAM_LAST_UPDATE_ID = 0
TELEGRAM_BOT_STATUS = "WAITING_FOR_TOKEN"
FARM_CYCLES_COMPLETED = 0


def load_config() -> dict:
    default_cfg = {
        "telegram_bot_token": os.environ.get("TELEGRAM_BOT_TOKEN", ""),
        "telegram_allowed_chat_id": os.environ.get("TELEGRAM_CHAT_ID", ""),
        "gemini_keys": [k for k in os.environ.get("GEMINI_API_KEY", "").split(",") if k.strip()],
        "groq_keys": [k for k in os.environ.get("GROQ_API_KEY", "").split(",") if k.strip()],
        "openrouter_keys": [k for k in os.environ.get("OPENROUTER_API_KEY", "").split(",") if k.strip()],
        "deepseek_keys": [k for k in os.environ.get("DEEPSEEK_API_KEY", "").split(",") if k.strip()],
        "custom_upstream_url": os.environ.get("CUSTOM_ROUTER_URL", ""),
        "custom_upstream_key": os.environ.get("CUSTOM_ROUTER_KEY", ""),
        "farm_interval_minutes": 60,
        "hermes_system_prompt": (
            "Kamu adalah Hermes Autonomous Agent yang berjalan di VPS Debian InstaBox milik Kak Diko "
            "(4 vCPU, 8 GiB RAM, terhubung via Tailscale & 9Router/LiteLLM). Jawab dengan taktis, "
            "padat, dan eksekusi tugas farming/otomasi secara presisi."
        ),
    }
    if CONFIG_PATH.exists():
        try:
            saved = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            default_cfg.update(saved)
        except Exception:
            pass
    return default_cfg


def save_config(cfg: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def get_tailscale_status() -> dict:
    ip = "Belum Login (Jalankan: sudo tailscale up --ssh)"
    connected = False
    try:
        out = subprocess.check_output(["tailscale", "ip", "-4"], stderr=subprocess.DEVNULL, timeout=3).decode().strip()
        if out:
            ip = out.splitlines()[0].strip()
            connected = True
    except Exception:
        pass
    return {"connected": connected, "tailscale_ip": ip}


_RR_INDEX = 0


def call_9router_litellm(messages: list, model: str = "hermes-auto") -> dict:
    """
    Unified 9Router / LiteLLM OpenAI-compatible multi-provider router with key rotation:
    1. Custom 9Router / LiteLLM upstream (if configured)
    2. Groq Llama-3.3-70B (Ultra-fast LPU)
    3. Google Gemini 2.5 Flash
    4. OpenRouter (Nous Hermes 3 / DeepSeek R1 / Qwen)
    5. DeepSeek API
    6. Built-in Hermes Local Autonomous Engine (0ms fallback)
    """
    global _RR_INDEX
    cfg = load_config()
    _RR_INDEX += 1

    user_prompt = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            user_prompt = m.get("content", "")
            break
    if not user_prompt and messages:
        user_prompt = str(messages[-1].get("content", ""))

    sys_prompt = cfg.get("hermes_system_prompt", "")
    full_messages = [{"role": "system", "content": sys_prompt}] + [
        m for m in messages if m.get("role") != "system"
    ]

    t0 = time.time()

    # 1. Custom 9Router / LiteLLM Upstream
    if cfg.get("custom_upstream_url"):
        try:
            url = cfg["custom_upstream_url"].rstrip("/")
            if not url.endswith("/chat/completions"):
                url += "/v1/chat/completions" if "/v1" not in url else "/chat/completions"
            headers = {"Content-Type": "application/json"}
            if cfg.get("custom_upstream_key"):
                headers["Authorization"] = f"Bearer {cfg['custom_upstream_key']}"
            req = urllib.request.Request(
                url,
                data=json.dumps({"model": model, "messages": full_messages}).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                reply = data["choices"][0]["message"]["content"]
                return {"reply": reply, "provider": f"9router-upstream ({model})", "latency_ms": int((time.time() - t0) * 1000)}
        except Exception:
            pass

    # 2. Groq Key Rotation
    groq_keys = [k.strip() for k in cfg.get("groq_keys", []) if k.strip()]
    if groq_keys:
        key = groq_keys[_RR_INDEX % len(groq_keys)]
        try:
            req = urllib.request.Request(
                "https://api.groq.com/openai/v1/chat/completions",
                data=json.dumps({
                    "model": "llama-3.3-70b-versatile",
                    "messages": full_messages,
                }).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {key}",
                    "User-Agent": "Hermes-9Router/1.0",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                reply = data["choices"][0]["message"]["content"]
                return {"reply": reply, "provider": f"groq/llama-3.3-70b (key #{(_RR_INDEX % len(groq_keys)) + 1})", "latency_ms": int((time.time() - t0) * 1000)}
        except Exception:
            pass

    # 3. OpenRouter (Nous Hermes 3 / Free Models) Key Rotation
    or_keys = [k.strip() for k in cfg.get("openrouter_keys", []) if k.strip()]
    if or_keys:
        key = or_keys[_RR_INDEX % len(or_keys)]
        target_model = "nousresearch/hermes-3-llama-3.1-405b:free" if model == "hermes-auto" else model
        try:
            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=json.dumps({
                    "model": target_model,
                    "messages": full_messages,
                }).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {key}",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                reply = data["choices"][0]["message"]["content"]
                return {"reply": reply, "provider": f"openrouter/{target_model}", "latency_ms": int((time.time() - t0) * 1000)}
        except Exception:
            pass

    # 4. Gemini Key Rotation
    gem_keys = [k.strip() for k in cfg.get("gemini_keys", []) if k.strip()]
    if gem_keys:
        key = gem_keys[_RR_INDEX % len(gem_keys)]
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
            payload = {"contents": [{"parts": [{"text": f"{sys_prompt}\n\nUser: {user_prompt}"}]}]}
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                reply = data["candidates"][0]["content"]["parts"][0]["text"]
                return {"reply": reply, "provider": f"gemini/gemini-2.5-flash (key #{(_RR_INDEX % len(gem_keys)) + 1})", "latency_ms": int((time.time() - t0) * 1000)}
        except Exception:
            pass

    # 5. Built-in Hermes Local Fallback
    ts = get_tailscale_status()
    reply = (
        f"⚡ [Hermes Local Node — {platform.node()}]\n"
        f"• Pesan Diterima: \"{user_prompt}\"\n"
        f"• Tailscale IP: {ts['tailscale_ip']}\n"
        f"• Status Router: Aktif di port 4000 (/v1/chat/completions).\n"
        f"• Tips: Tambahkan API Key (Groq / Gemini / OpenRouter / 9Router) di Web UI Port 4000 "
        f"untuk mengaktifkan rotasi multi-model penuh."
    )
    return {"reply": reply, "provider": "hermes-local-fallback", "latency_ms": 1}


def send_telegram_message(token: str, chat_id: str | int, text: str) -> bool:
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text[:4000]}
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception:
        return False


def telegram_bot_worker() -> None:
    """
    Background daemon that polls Telegram Bot API and executes Hermes commands:
    /start, /status, /farm, /sh <cmd>, or direct AI chat via 9Router/LiteLLM.
    """
    global TELEGRAM_LAST_UPDATE_ID, TELEGRAM_BOT_STATUS
    while True:
        cfg = load_config()
        token = cfg.get("telegram_bot_token", "").strip()
        if not token:
            TELEGRAM_BOT_STATUS = "WAITING_FOR_TOKEN (Set di Web UI :4000)"
            time.sleep(5)
            continue

        try:
            url = f"https://api.telegram.org/bot{token}/getUpdates?offset={TELEGRAM_LAST_UPDATE_ID + 1}&timeout=20"
            with urllib.request.urlopen(url, timeout=25) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("ok"):
                    TELEGRAM_BOT_STATUS = "CONNECTED_AND_POLLING"
                    for upd in data.get("result", []):
                        TELEGRAM_LAST_UPDATE_ID = upd["update_id"]
                        msg = upd.get("message") or {}
                        chat_id = msg.get("chat", {}).get("id")
                        text = (msg.get("text") or "").strip()
                        if not chat_id or not text:
                            continue

                        # Auto-save first chat_id if not set
                        if not cfg.get("telegram_allowed_chat_id"):
                            cfg["telegram_allowed_chat_id"] = str(chat_id)
                            save_config(cfg)

                        if text.startswith("/status") or text.startswith("/start"):
                            ts = get_tailscale_status()
                            total_d, used_d, free_d = shutil.disk_usage("/")
                            status_msg = (
                                f"🤖 HERMES + 9ROUTER/LITELLM VPS NODE\n"
                                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                                f"• Host/Kernel : {platform.node()} ({platform.release()})\n"
                                f"• Tailscale IP: {ts['tailscale_ip']}\n"
                                f"• Disk Free   : {free_d / (1024**3):.2f} GiB\n"
                                f"• Farm Cycles : {FARM_CYCLES_COMPLETED}\n"
                                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                                f"Perintah:\n"
                                f"/status - Info VPS & Tailscale\n"
                                f"/farm - Trigger Farming Artikel & Vektor\n"
                                f"/sh <cmd> - Jalankan perintah Linux di VPS\n"
                                f"Atau ketik pesan apa saja untuk ngobrol dengan Hermes AI!"
                            )
                            send_telegram_message(token, chat_id, status_msg)

                        elif text.startswith("/farm"):
                            topic = text.replace("/farm", "").strip() or "Otomasi AI & Saham Dividen"
                            try:
                                req = urllib.request.Request(
                                    "http://127.0.0.1:8080/api/v1/farm/content",
                                    data=json.dumps({"topic": topic}).encode("utf-8"),
                                    headers={"Content-Type": "application/json"},
                                    method="POST",
                                )
                                with urllib.request.urlopen(req, timeout=15) as r:
                                    res = json.loads(r.read().decode("utf-8"))
                                send_telegram_message(
                                    token,
                                    chat_id,
                                    f"✅ Farming Selesai!\nTopik: {topic}\nArtikel dibuat: {res.get('articles_created', 0)}",
                                )
                            except Exception as e:
                                send_telegram_message(token, chat_id, f"⚠️ Error farming: {e}")

                        elif text.startswith("/sh "):
                            cmd = text[4:].strip()
                            allowed_chat = str(cfg.get("telegram_allowed_chat_id", ""))
                            if allowed_chat and str(chat_id) != allowed_chat:
                                send_telegram_message(token, chat_id, "⛔ Unauthorized chat_id.")
                                continue
                            try:
                                out = subprocess.check_output(
                                    cmd, shell=True, stderr=subprocess.STDOUT, timeout=15
                                ).decode("utf-8", errors="replace")
                                send_telegram_message(token, chat_id, f"💻 Output:\n{out[:3500] or '(OK - No output)'}")
                            except Exception as e:
                                send_telegram_message(token, chat_id, f"❌ Command error:\n{e}")

                        else:
                            res = call_9router_litellm([{"role": "user", "content": text}])
                            send_telegram_message(
                                token,
                                chat_id,
                                f"{res['reply']}\n\n— via {res['provider']} ({res['latency_ms']}ms)",
                            )
        except Exception as e:
            TELEGRAM_BOT_STATUS = f"ERROR: {str(e)[:60]}"
            time.sleep(5)


def autonomous_farming_cron_worker() -> None:
    """
    Runs periodic farming tasks in the background and notifies Telegram if configured.
    """
    global FARM_CYCLES_COMPLETED
    while True:
        cfg = load_config()
        interval_mins = max(10, int(cfg.get("farm_interval_minutes", 60)))
        time.sleep(interval_mins * 60)
        try:
            req = urllib.request.Request(
                "http://127.0.0.1:8080/api/v1/farm/vectors",
                data=json.dumps({"theme": f"Auto-Farm Cycle #{FARM_CYCLES_COMPLETED + 1}"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=10).read()
            FARM_CYCLES_COMPLETED += 1
            if cfg.get("telegram_bot_token") and cfg.get("telegram_allowed_chat_id"):
                send_telegram_message(
                    cfg["telegram_bot_token"],
                    cfg["telegram_allowed_chat_id"],
                    f"🚜 [Auto-Farm Worker] Siklus #{FARM_CYCLES_COMPLETED} selesai! 6 SVG Vector baru telah diproduksi.",
                )
        except Exception:
            pass


def render_hermes_control_html() -> str:
    cfg = load_config()
    ts = get_tailscale_status()
    return f"""<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Hermes + 9Router/LiteLLM + Tailscale + Telegram Control Hub</title>
  <style>
    :root {{
      --bg: #050811;
      --card: #0f172a;
      --border: rgba(148, 163, 184, 0.2);
      --text: #f8fafc;
      --muted: #94a3b8;
      --accent: #38bdf8;
      --green: #10b981;
      --purple: #a855f7;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      padding: 1.5rem;
      line-height: 1.6;
    }}
    .container {{ max-width: 1100px; margin: 0 auto; }}
    .header {{
      background: linear-gradient(90deg, #1e1b4b, #0f172a, #064e3b);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 1.5rem;
      margin-bottom: 1.5rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 1rem;
    }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.25rem; }}
    @media (max-width: 850px) {{ .grid {{ grid-template-columns: 1fr; }} }}
    .card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 1.4rem;
      margin-bottom: 1.25rem;
    }}
    h2 {{ font-size: 1.15rem; margin-bottom: 0.5rem; color: var(--accent); }}
    label {{ display: block; font-size: 0.8rem; color: var(--muted); margin: 0.6rem 0 0.25rem; font-weight: 600; }}
    input, textarea {{
      width: 100%;
      background: #020617;
      border: 1px solid var(--border);
      color: var(--text);
      padding: 0.6rem 0.8rem;
      border-radius: 8px;
      font-size: 0.88rem;
    }}
    button {{
      background: var(--green);
      color: #022c22;
      border: none;
      padding: 0.65rem 1.2rem;
      border-radius: 8px;
      font-weight: 800;
      cursor: pointer;
      margin-top: 1rem;
    }}
    code {{ background: #020617; padding: 0.2rem 0.45rem; border-radius: 5px; color: #34d399; }}
    pre {{ background: #020617; padding: 0.9rem; border-radius: 8px; overflow-x: auto; font-size: 0.82rem; color: #38bdf8; margin-top: 0.75rem; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div>
        <h1>⚡ Hermes Agent + 9Router/LiteLLM + Tailscale Hub</h1>
        <p style="color:var(--muted);font-size:0.88rem;">OpenAI-Compatible Gateway: <code>http://127.0.0.1:4000/v1/chat/completions</code></p>
      </div>
      <div style="text-align:right;font-size:0.85rem;">
        <div>Tailscale IP: <code>{ts['tailscale_ip']}</code></div>
        <div>Telegram Bot: <strong style="color:#34d399;">{TELEGRAM_BOT_STATUS}</strong></div>
      </div>
    </div>

    <div class="grid">
      <div class="card">
        <h2>🔑 1. Konfigurasi Telegram Bot & Multi-Key 9Router/LiteLLM</h2>
        <p style="font-size:0.82rem;color:var(--muted);">Masukkan token dari @BotFather dan API Key AI (pisahkan dengan koma jika punya banyak key untuk rotasi otomatis).</p>
        <label>Telegram Bot Token (@BotFather)</label>
        <input type="password" id="tg_token" value="{cfg.get('telegram_bot_token', '')}" placeholder="123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ" />
        <label>Telegram Chat ID Anda (Kosongkan untuk auto-detect saat Anda chat /start ke bot)</label>
        <input type="text" id="tg_chat" value="{cfg.get('telegram_allowed_chat_id', '')}" placeholder="Otomatis terisi saat Anda kirim /start" />
        <label>Groq API Keys (Pisahkan koma untuk rotasi - Llama 3.3 70B Gratis)</label>
        <input type="text" id="groq_keys" value="{','.join(cfg.get('groq_keys', []))}" placeholder="gsk_xxx1, gsk_xxx2" />
        <label>Gemini API Keys (Pisahkan koma - Gemini 2.5 Flash Gratis)</label>
        <input type="text" id="gemini_keys" value="{','.join(cfg.get('gemini_keys', []))}" placeholder="AIzaSy_xxx1, AIzaSy_xxx2" />
        <label>OpenRouter API Keys (Nous Hermes 3 / Free Models)</label>
        <input type="text" id="or_keys" value="{','.join(cfg.get('openrouter_keys', []))}" placeholder="sk-or-v1-xxx" />
        <label>Custom 9Router / LiteLLM Upstream URL (Opsional)</label>
        <input type="text" id="custom_url" value="{cfg.get('custom_upstream_url', '')}" placeholder="http://127.0.0.1:20128/v1" />
        <button onclick="saveCfg()">💾 Simpan & Aktifkan Bot + Router</button>
        <pre id="save_out">Status: Siap menerima konfigurasi.</pre>
      </div>

      <div>
        <div class="card">
          <h2>🌐 2. Koneksi Tailscale & SSH ke Device Lu</h2>
          <p style="font-size:0.84rem;color:var(--muted);">OS VPS lu adalah <strong>Debian Linux (Kernel 6.18-instabox)</strong>—lebih hemat RAM 400MB dibanding Ubuntu 22.04 dan 100% kompatibel.</p>
          <pre>
# 1. Di Terminal VPS, jalankan perintah ini sekali buat login Tailscale:
sudo tailscale up --ssh

# 2. Setelah klik link login Tailscale yang muncul, cek IP Tailscale VPS:
tailscale ip -4

# 3. Dari Laptop/HP lu (yang sudah install Tailscale), langsung SSH tanpa password:
ssh user@{ts['tailscale_ip']}</pre>
        </div>

        <div class="card">
          <h2>🧪 3. Test Hermes + 9Router/LiteLLM Endpoint (/v1/chat/completions)</h2>
          <input type="text" id="test_msg" value="Berikan 3 ide script farming otomatis di VPS Linux dengan modal API gratis" />
          <button style="background:var(--accent);" onclick="testChat()">🚀 Kirim ke Hermes Router</button>
          <pre id="chat_out">Klik tombol di atas untuk mengetes router...</pre>
        </div>
      </div>
    </div>
  </div>

  <script>
    async function saveCfg() {{
      const payload = {{
        telegram_bot_token: document.getElementById('tg_token').value.trim(),
        telegram_allowed_chat_id: document.getElementById('tg_chat').value.trim(),
        groq_keys: document.getElementById('groq_keys').value.split(',').map(s => s.trim()).filter(Boolean),
        gemini_keys: document.getElementById('gemini_keys').value.split(',').map(s => s.trim()).filter(Boolean),
        openrouter_keys: document.getElementById('or_keys').value.split(',').map(s => s.trim()).filter(Boolean),
        custom_upstream_url: document.getElementById('custom_url').value.trim()
      }};
      const res = await fetch('/api/config', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify(payload)
      }});
      const data = await res.json();
      document.getElementById('save_out').textContent = JSON.stringify(data, null, 2);
      setTimeout(() => location.reload(), 1000);
    }}

    async function testChat() {{
      const msg = document.getElementById('test_msg').value;
      const out = document.getElementById('chat_out');
      out.textContent = 'Memanggil /v1/chat/completions...';
      const res = await fetch('/v1/chat/completions', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{
          model: 'hermes-auto',
          messages: [{{role: 'user', content: msg}}]
        }})
      }});
      const data = await res.json();
      out.textContent = JSON.stringify(data, null, 2);
    }}
  </script>
</body>
</html>
"""


class ThreadedRouterServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class HermesRouterHandler(http.server.BaseHTTPRequestHandler):
    def address_string(self) -> str:
        return str(self.client_address[0])

    def log_message(self, format: str, *args) -> None:
        pass

    def _send_json(self, payload: dict, status: int = 200) -> None:
        raw = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_OPTIONS(self) -> None:
        self._send_json({"status": "ok"})

    def do_GET(self) -> None:
        if self.path in ("/", "/dashboard"):
            raw = render_hermes_control_html().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return

        if self.path in ("/v1/models", "/models"):
            self._send_json({
                "object": "list",
                "data": [
                    {"id": "hermes-auto", "object": "model", "owned_by": "kakdiko-9router"},
                    {"id": "llama-3.3-70b-versatile", "object": "model", "owned_by": "groq"},
                    {"id": "gemini-2.5-flash", "object": "model", "owned_by": "google"},
                    {"id": "nousresearch/hermes-3-llama-3.1-405b:free", "object": "model", "owned_by": "openrouter"},
                ],
            })
            return

        if self.path == "/health":
            self._send_json({"status": "ok", "telegram_bot": TELEGRAM_BOT_STATUS, "tailscale": get_tailscale_status()})
            return

        self._send_json({"error": "Not found"}, status=404)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        body_raw = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        try:
            body = json.loads(body_raw) if body_raw else {}
        except Exception:
            body = {}

        if self.path == "/api/config":
            cfg = load_config()
            for k in ("telegram_bot_token", "telegram_allowed_chat_id", "groq_keys", "gemini_keys", "openrouter_keys", "custom_upstream_url"):
                if k in body:
                    cfg[k] = body[k]
            save_config(cfg)
            self._send_json({"status": "saved", "telegram_token_set": bool(cfg.get("telegram_bot_token"))})
            return

        if self.path in ("/v1/chat/completions", "/chat/completions", "/api/v1/router/chat"):
            messages = body.get("messages") or [{"role": "user", "content": body.get("prompt", "Hello")}]
            model = body.get("model", "hermes-auto")
            res = call_9router_litellm(messages, model)
            # Return full OpenAI-compatible chat.completion response for Hermes CLI / LiteLLM clients
            self._send_json({
                "id": f"chatcmpl-{int(time.time() * 1000)}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": res["provider"],
                "latency_ms": res["latency_ms"],
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": res["reply"]},
                        "finish_reason": "stop",
                    }
                ],
            })
            return

        self._send_json({"error": "Unknown POST path"}, status=404)


if __name__ == "__main__":
    t_bot = threading.Thread(target=telegram_bot_worker, daemon=True)
    t_bot.start()
    t_farm = threading.Thread(target=autonomous_farming_cron_worker, daemon=True)
    t_farm.start()

    port = int(os.environ.get("ROUTER_PORT", "4000"))
    with ThreadedRouterServer(("0.0.0.0", port), HermesRouterHandler) as httpd:
        print(f"[OK] Hermes + 9Router/LiteLLM Gateway + Telegram Bot active on http://0.0.0.0:{port}")
        httpd.serve_forever()
