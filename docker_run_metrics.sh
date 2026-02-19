#!/bin/bash

# BIST30 AI Trader - Docker Konteynerinde Model Eğitim Metriklerini Çalıştırma
# Kullanım: ./docker_run_metrics.sh

echo "=================================================="
echo "🐳 Docker Konteynerinde Metrik Toplama"
echo "=================================================="

# Docker Compose ile konteyner çalıştır
echo ""
echo "📦 Konteyner başlatılıyor..."

docker-compose run --rm app python scripts/analysis/get_training_metrics.py

echo ""
echo "✅ İşlem tamamlandı!"
echo ""
echo "📄 Rapor: reports/training_metrics_summary.json"
echo ""
