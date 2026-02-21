#!/bin/bash

# Renkler
GREEN='\033[0;32m'
NC='\033[0m'

# Sanal ortam kontrolü ve aktivasyon
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Sanal ortam (venv) bulunamadı. Lütfen önce scripts/setup_wsl.sh çalıştırın."
    exit 1
fi

echo -e "${GREEN}Backtest Başlatılıyor...${NC}"
python scripts/run_backtest.py
