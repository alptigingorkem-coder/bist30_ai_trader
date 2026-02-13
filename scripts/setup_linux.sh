#!/bin/bash

# Renkler
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}BIST30 AI Trader - Linux Ortam Kurulumu Başlıyor...${NC}"

# Python kontrolü
if ! command -v python3 &> /dev/null; then
    echo "Python3 bulunamadı. Lütfen önce python3 kurun."
    exit 1
fi

# Sanal ortam oluşturma
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Sanal ortam (venv) oluşturuluyor...${NC}"
    python3 -m venv venv
else
    echo -e "${GREEN}Sanal ortam zaten var.${NC}"
fi

# Aktivasyon
source venv/bin/activate

# Pip güncelleme
echo -e "${YELLOW}Pip güncelleniyor...${NC}"
pip install --upgrade pip

# Gereksinimleri yükleme
echo -e "${YELLOW}Gereksinimler yükleniyor...${NC}"
pip install -r requirements.txt

echo -e "${GREEN}Kurulum tamamlandı!${NC}"
echo -e "Çalıştırmak için: source venv/bin/activate"
