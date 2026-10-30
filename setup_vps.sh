#!/usr/bin/env bash
# ==============================================================================
# KakDiko 13-Domain Empire: Instabox VPS Production Bootstrap
# Optimized for: Ubuntu 22.04 / 24.04 LTS (4 vCPU / 8 GiB RAM / 20 GiB NVMe)
# ==============================================================================
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}====================================================================${NC}"
echo -e "${GREEN}  KakDiko 13-Domain Empire - VPS Automation Workhorse Setup${NC}"
echo -e "${BLUE}====================================================================${NC}"

if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}[!] Skrip ini wajib dijalankan sebagai root (atau sudo).${NC}"
   exit 1
fi

# 1. Update OS Packages
echo -e "\n${YELLOW}[1/6] Memperbarui sistem OS...${NC}"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get upgrade -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold"
apt-get install -y ca-certificates curl gnupg lsb-release git python3 python3-pip python3-venv jq ufw fail2ban

# 2. Setup 2GB Swap (Hemat storage 20GB, hemat RAM)
echo -e "\n${YELLOW}[2/6] Mengonfigurasi 2GB Swap untuk proteksi OOM (Storage-optimized)...${NC}"
if [ ! -f /swapfile ]; then
    fallocate -l 2G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=2048
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    sysctl vm.swappiness=10
    echo 'vm.swappiness=10' >> /etc/sysctl.conf
    echo -e "${GREEN}[OK] 2GB Swap aktif & swappiness diset ke 10.${NC}"
else
    echo -e "${GREEN}[OK] Swapfile sudah ada.${NC}"
fi

# 3. UFW Firewall & Fail2ban Hardening
echo -e "\n${YELLOW}[3/6] Mengaktifkan Firewall (UFW) & Fail2ban...${NC}"
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP Web'
ufw allow 443/tcp comment 'HTTPS SSL'
ufw --force enable
systemctl enable --now fail2ban
echo -e "${GREEN}[OK] Port 22, 80, 443 dibuka aman.${NC}"

# 4. Install Official Docker & Docker Compose
echo -e "\n${YELLOW}[4/6] Menginstal Docker Engine & Compose plugin...${NC}"
if ! command -v docker &> /dev/null; then
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg --yes
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    systemctl enable --now docker
    echo -e "${GREEN}[OK] Docker berhasil dipasang.${NC}"
else
    echo -e "${GREEN}[OK] Docker sudah terpasang.${NC}"
fi

# 5. Clone Monorepo & Setup Automation Workspace
echo -e "\n${YELLOW}[5/6] Menyiapkan repositori KakDiko Domain Empire...${NC}"
TARGET_DIR="/opt/domain_empire"
mkdir -p "$TARGET_DIR"
if [ ! -d "$TARGET_DIR/.git" ]; then
    git clone https://github.com/diko23/kakdiko-13-domain-empire.git "$TARGET_DIR"
else
    cd "$TARGET_DIR" && git pull origin main
fi

cd "$TARGET_DIR"
python3 -m venv "$TARGET_DIR/venv"
"$TARGET_DIR/venv/bin/pip" install --upgrade pip

# 6. Menyiapkan Docker Compose untuk Automasi N8N (Optional Worker)
echo -e "\n${YELLOW}[6/6] Menyiapkan stack automasi N8N & Webhook...${NC}"
cat << 'EOF' > "$TARGET_DIR/docker-compose.yml"
services:
  n8n:
    image: docker.n8n.io/n8nio/n8n:latest
    container_name: empire-n8n
    restart: unless-stopped
    ports:
      - "127.0.0.1:5678:5678"
    environment:
      - N8N_HOST=localhost
      - N8N_PORT=5678
      - N8N_PROTOCOL=http
      - NODE_ENV=production
      - WEBHOOK_URL=http://localhost:5678/
      - GENERIC_TIMEZONE=Asia/Jakarta
    volumes:
      - /opt/n8n_data:/home/node/.n8n
    deploy:
      resources:
        limits:
          cpus: '1.5'
          memory: 1536M
EOF

mkdir -p /opt/n8n_data
chown -R 1000:1000 /opt/n8n_data

echo -e "\n${GREEN}====================================================================${NC}"
echo -e "${GREEN}[SUCCESS] VPS INSTABOX SELESAI DIKONFIGURASI SECARA TOTAL!${NC}"
echo -e "${BLUE}====================================================================${NC}"
echo -e "Resource Status:"
free -h
echo -e "Disk Space Status:"
df -h /
echo -e "${BLUE}====================================================================${NC}"
echo -e "Langkah lanjutan di VPS:"
echo -e "1. Jalankan N8N: ${YELLOW}cd /opt/domain_empire && docker compose up -d${NC}"
echo -e "2. Jalankan Content Generator: ${YELLOW}/opt/domain_empire/venv/bin/python /opt/domain_empire/ai_content_agent.py --list${NC}"
echo -e "${BLUE}====================================================================${NC}"
