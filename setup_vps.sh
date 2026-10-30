#!/usr/bin/env bash
# ==============================================================================
# KakDiko 13-Domain Empire: Universal AI Workhorse & Profit Engine Bootstrap
# Compatible with: InstaBox (4 vCPU / 8 GiB / 20 GiB), Ubuntu/Debian VM & Containers
# ==============================================================================
set -uo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}====================================================================${NC}"
echo -e "${GREEN}  KakDiko 13-Domain Empire - Universal AI Workhorse Bootstrap${NC}"
echo -e "${BLUE}====================================================================${NC}"

SUDO=""
if [[ $EUID -ne 0 ]] && command -v sudo &> /dev/null; then
    SUDO="sudo"
fi

# 1. Update OS & Install Essential Tools
echo -e "\n${YELLOW}[1/6] Memastikan paket inti (Git, Python3, Curl, SQLite) tersedia...${NC}"
export DEBIAN_FRONTEND=noninteractive
if command -v apt-get &> /dev/null; then
    $SUDO apt-get update -y || true
    $SUDO apt-get install -y ca-certificates curl git python3 python3-pip python3-venv jq || true
fi

# 2. Setup 2GB Swap (Graceful fallback on microVM / container kernels)
echo -e "\n${YELLOW}[2/6] Mengoptimalkan memori & swap (20 GiB Storage Safe)...${NC}"
if [ ! -f /swapfile ]; then
    ($SUDO fallocate -l 2G /swapfile || $SUDO dd if=/dev/zero of=/swapfile bs=1M count=2048) 2>/dev/null || true
    $SUDO chmod 600 /swapfile 2>/dev/null || true
    $SUDO mkswap /swapfile 2>/dev/null || true
    if $SUDO swapon /swapfile 2>/dev/null; then
        echo -e "${GREEN}[OK] 2GB Swap aktif.${NC}"
    else
        $SUDO rm -f /swapfile 2>/dev/null || true
        echo -e "${GREEN}[OK] Kernel container InstaBox menggunakan manajemen memori host (8 GiB RAM siap).${NC}"
    fi
fi

# 3. Clone / Update Monorepo
echo -e "\n${YELLOW}[3/6] Mengunduh & menyiapkan repositori KakDiko 13-Domain Empire...${NC}"
TARGET_DIR="/opt/domain_empire"
if ! $SUDO mkdir -p "$TARGET_DIR" 2>/dev/null; then
    TARGET_DIR="$HOME/domain_empire"
    mkdir -p "$TARGET_DIR"
fi
$SUDO chown -R "$(whoami)" "$TARGET_DIR" 2>/dev/null || true

if [ ! -d "$TARGET_DIR/.git" ]; then
    git clone https://github.com/diko23/kakdiko-13-domain-empire.git "$TARGET_DIR"
else
    cd "$TARGET_DIR" && git pull origin main
fi

cd "$TARGET_DIR"

# 4. Build 13 Domains & Initialize AI Workhorse Database
echo -e "\n${YELLOW}[4/6] Membangun 13 Domain Statis & Menginisialisasi AI Workhorse...${NC}"
python3 build_monorepo.py
python3 test_monorepo.py
python3 vps_engine/empire_workhorse.py --init-only

# 5. Start Universal AI Workhorse & Multi-LLM Router Daemon (Port 8080)
echo -e "\n${YELLOW}[5/6] Menjalankan Daemon AI Workhorse & Multi-LLM Router di Port 8080...${NC}"
pkill -f "empire_workhorse.py" 2>/dev/null || true
nohup python3 "$TARGET_DIR/vps_engine/empire_workhorse.py" --host 0.0.0.0 --port 8080 > "$TARGET_DIR/workhorse.log" 2>&1 &
WORKHORSE_PID=$!
sleep 2

# 6. Start Background Self-Keepalive Loop (Resets internal activity every 10 mins)
echo -e "\n${YELLOW}[6/6] Mengaktifkan Background Keep-Alive & Auto-Farm Daemon...${NC}"
cat << 'EOF' > "$TARGET_DIR/keepalive_loop.sh"
#!/usr/bin/env bash
while true; do
  curl -fsSL http://127.0.0.1:8080/keepalive > /dev/null 2>&1 || true
  sleep 600
done
EOF
chmod +x "$TARGET_DIR/keepalive_loop.sh"
pkill -f "keepalive_loop.sh" 2>/dev/null || true
nohup "$TARGET_DIR/keepalive_loop.sh" > /dev/null 2>&1 &

# Free up CPU/RAM by closing heavy VNC desktop browsers inside the VPS
pkill -f "chromium" 2>/dev/null || true
pkill -f "chrome" 2>/dev/null || true

# Launch Cloudflare Quick Tunnel so user can open Dashboard natively on their own laptop (Zero VNC Lag!)
echo -e "\n${YELLOW}[+] Membuka Jalur Akses Cepat (Cloudflare Tunnel) agar bisa dibuka langsung di Chrome Laptop Anda...${NC}"
if [ ! -f /usr/local/bin/cloudflared ] && [ ! -f "$TARGET_DIR/cloudflared" ]; then
    curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o "$TARGET_DIR/cloudflared"
    chmod +x "$TARGET_DIR/cloudflared"
fi
CF_BIN="$TARGET_DIR/cloudflared"
[ -f /usr/local/bin/cloudflared ] && CF_BIN="/usr/local/bin/cloudflared"

pkill -f "cloudflared tunnel" 2>/dev/null || true
nohup "$CF_BIN" tunnel --no-autoupdate --url http://127.0.0.1:8080 > "$TARGET_DIR/tunnel.log" 2>&1 &
sleep 5
PUBLIC_TUNNEL_URL=$(grep -oE "https://[a-zA-Z0-9-]+\\.trycloudflare\\.com" "$TARGET_DIR/tunnel.log" | head -n 1 || true)

echo -e "\n${GREEN}====================================================================${NC}"
echo -e "${GREEN}[SUCCESS] INSTABOX AI WORKHORSE & 13-DOMAIN ENGINE AKTIF!${NC}"
echo -e "${BLUE}====================================================================${NC}"
echo -e "PID Daemon      : ${GREEN}${WORKHORSE_PID}${NC}"
echo -e "Lokasi Kerja    : ${YELLOW}${TARGET_DIR}${NC}"
if [ -n "$PUBLIC_TUNNEL_URL" ]; then
    echo -e "🚀 BUKA DI CHROME LAPTOP LU (ANTI-LEMOT): ${GREEN}${PUBLIC_TUNNEL_URL}${NC}"
    echo -e "🔗 KEEP-ALIVE URL (UptimeRobot/GitHub)  : ${GREEN}${PUBLIC_TUNNEL_URL}/keepalive${NC}"
    echo -e "🧠 ENDPOINT AI ROUTER PUBLIK            : ${GREEN}${PUBLIC_TUNNEL_URL}/api/v1/router/chat${NC}"
else
    echo -e "Dashboard UI    : ${GREEN}http://localhost:8080/${NC} (Cek log tunnel di $TARGET_DIR/tunnel.log)"
fi
echo -e "${BLUE}====================================================================${NC}"
curl -sSL http://127.0.0.1:8080/api/status | head -n 35
echo -e "\n${BLUE}====================================================================${NC}"
