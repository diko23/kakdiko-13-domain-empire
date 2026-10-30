#!/usr/bin/env bash
# ==============================================================================
# KakDiko VPS Stack: Hermes Agent + 9Router/LiteLLM + Telegram Bot + Tailscale SSH
# Target OS: Debian GNU/Linux (Linux 6.18-instabox, 4 vCPU / 8 GiB RAM / 20 GiB)
# ==============================================================================
set -uo pipefail

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}====================================================================${NC}"
echo -e "${GREEN}  Installing Hermes + 9Router/LiteLLM + Tailscale SSH + Telegram${NC}"
echo -e "${BLUE}====================================================================${NC}"

SUDO=""
if [[ $EUID -ne 0 ]] && command -v sudo &> /dev/null; then
    SUDO="sudo"
fi

# 1. Check OS & Install OpenSSH Server + Essential Packages
echo -e "\n${YELLOW}[1/5] Mengecek OS Debian & menyalakan OpenSSH Server (Port 22)...${NC}"
cat /etc/os-release | grep -E "PRETTY_NAME|VERSION=" || true
export DEBIAN_FRONTEND=noninteractive
$SUDO apt-get update -y >/dev/null 2>&1 || true
$SUDO apt-get install -y openssh-server curl git python3 python3-pip python3-venv jq ca-certificates >/dev/null 2>&1 || true
$SUDO mkdir -p /run/sshd
$SUDO service ssh start 2>/dev/null || $SUDO /usr/sbin/sshd 2>/dev/null || true
echo -e "${GREEN}[OK] OpenSSH Server aktif di Port 22.${NC}"

# 2. Install & Start Tailscale (Userspace-safe for InstaBox 6.18 kernel)
echo -e "\n${YELLOW}[2/5] Menginstal Tailscale & menyambungkan Tailnet + Tailscale SSH...${NC}"
if ! command -v tailscale &> /dev/null; then
    curl -fsSL https://tailscale.com/install.sh | sh
fi

if ! pgrep -x "tailscaled" > /dev/null; then
    if [ -e /dev/net/tun ]; then
        $SUDO nohup tailscaled --state=/var/lib/tailscale/tailscaled.state > /tmp/tailscaled.log 2>&1 &
    else
        $SUDO mkdir -p /var/lib/tailscale
        $SUDO nohup tailscaled --tun=userspace-networking --state=/var/lib/tailscale/tailscaled.state > /tmp/tailscaled.log 2>&1 &
    fi
    sleep 2
fi

# Run tailscale up in background with timeout if not logged in yet, capturing auth URL
TS_IP=$(tailscale ip -4 2>/dev/null || true)
TS_AUTH_URL=""
if [ -z "$TS_IP" ]; then
    $SUDO tailscale up --ssh --accept-routes --hostname="instabox-kakdiko" > /tmp/ts_auth.log 2>&1 &
    sleep 4
    TS_AUTH_URL=$(grep -oE "https://login\\.tailscale\\.com/[a-zA-Z0-9/_-]+" /tmp/ts_auth.log | head -n 1 || true)
fi

# 3. Update Repo & Start Hermes + 9Router/LiteLLM + Telegram Bot Node (Port 4000)
echo -e "\n${YELLOW}[3/5] Menyiapkan Hermes + 9Router/LiteLLM Multi-Provider Gateway (Port 4000)...${NC}"
TARGET_DIR="/opt/domain_empire"
if [ ! -d "$TARGET_DIR/.git" ]; then
    $SUDO mkdir -p "$TARGET_DIR"
    $SUDO chown -R "$(whoami)" "$TARGET_DIR"
    git clone https://github.com/diko23/kakdiko-13-domain-empire.git "$TARGET_DIR"
else
    cd "$TARGET_DIR" && git pull origin main
fi

cd "$TARGET_DIR"
pkill -f "hermes_router_node.py" 2>/dev/null || true
nohup python3 "$TARGET_DIR/vps_engine/hermes_router_node.py" > "$TARGET_DIR/hermes_router.log" 2>&1 &
HERMES_PID=$!
sleep 2

# 4. Install Optional 9Router CLI & NousResearch Hermes CLI Profile
echo -e "\n${YELLOW}[4/5] Menyiapkan alias CLI 'hermes' di terminal VPS...${NC}"
cat << 'EOF' > /tmp/hermes_cli
#!/usr/bin/env bash
PROMPT="$*"
if [ -z "$PROMPT" ]; then
  echo "Usage: hermes <pertanyaan atau instruksi>"
  exit 1
fi
curl -sSL -X POST http://127.0.0.1:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"hermes-auto\",\"messages\":[{\"role\":\"user\",\"content\":\"$PROMPT\"}]}" \
  | jq -r '.choices[0].message.content'
EOF
chmod +x /tmp/hermes_cli
$SUDO mv /tmp/hermes_cli /usr/local/bin/hermes 2>/dev/null || true

# 5. Expose Port 4000 via Cloudflare Quick Tunnel for instant Web Config UI
echo -e "\n${YELLOW}[5/5] Membuka Web Control Hub Hermes + 9Router + Telegram (Port 4000)...${NC}"
CF_BIN="$TARGET_DIR/cloudflared"
[ -f /usr/local/bin/cloudflared ] && CF_BIN="/usr/local/bin/cloudflared"
if [ ! -f "$CF_BIN" ]; then
    curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o "$TARGET_DIR/cloudflared"
    chmod +x "$TARGET_DIR/cloudflared"
    CF_BIN="$TARGET_DIR/cloudflared"
fi

nohup "$CF_BIN" tunnel --no-autoupdate --url http://127.0.0.1:4000 > "$TARGET_DIR/hermes_tunnel.log" 2>&1 &
sleep 5
HERMES_TUNNEL_URL=$(grep -oE "https://[a-zA-Z0-9-]+\\.trycloudflare\\.com" "$TARGET_DIR/hermes_tunnel.log" | head -n 1 || true)

echo -e "\n${GREEN}====================================================================${NC}"
echo -e "${GREEN}[SUCCESS] HERMES + 9ROUTER/LITELLM + TELEGRAM + TAILSCALE SIAP!${NC}"
echo -e "${BLUE}====================================================================${NC}"
echo -e "1. 🧠 PANEL HERMES + 9ROUTER + TELEGRAM BOT (Buka di Chrome Laptop):"
echo -e "   👉 ${GREEN}${HERMES_TUNNEL_URL:-http://localhost:4000}${NC}"
echo -e ""
if [ -n "$TS_IP" ]; then
    echo -e "2. 🌐 TAILSCALE SUDAH TERHUBUNG! IP Tailnet VPS Lu:"
    echo -e "   👉 ${GREEN}${TS_IP}${NC} (Bisa langsung: ${YELLOW}ssh user@${TS_IP}${NC})"
elif [ -n "$TS_AUTH_URL" ]; then
    echo -e "2. 🌐 KLIK LINK INI BUAT SAMBUNGKAN VPS KE TAILSCALE DEVICE LU:"
    echo -e "   👉 ${GREEN}${TS_AUTH_URL}${NC}"
else
    echo -e "2. 🌐 UNTUK LOGIN TAILSCALE, KETIK INI DI TERMINAL:"
    echo -e "   👉 ${YELLOW}sudo tailscale up --ssh${NC}"
fi
echo -e ""
echo -e "3. 💬 TEST HERMES LANGSUNG DARI TERMINAL VPS:"
echo -e "   👉 Ketik: ${YELLOW}hermes \"cek strategi farming hari ini\"${NC}"
echo -e "${BLUE}====================================================================${NC}"
