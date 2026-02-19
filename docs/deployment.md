# Deployment Guide

## Overview

This guide covers deploying BIST30 AI Trader in various environments.

## Deployment Options

1. **Local Development** - For development and testing
2. **Docker Compose** - For single-server deployment
3. **Production Server** - For production deployment
4. **Cloud Deployment** - For scalable cloud infrastructure (planned)

## Local Development

### Prerequisites

- Python 3.12+
- PostgreSQL 14+ with TimescaleDB
- Git
- (Optional) AMD GPU with ROCm or NVIDIA GPU with CUDA

### Setup

```bash
# Clone repository
git clone https://github.com/yourusername/bist30_ai_trader.git
cd bist30_ai_trader

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Initialize database
python scripts/migration/migrate_to_db.py

# Run tests
pytest
```

### Running Services

```bash
# Start API server
uvicorn api.server:app --reload --port 8000

# Start MLflow
mlflow ui --port 5000

# Run paper trading
python scripts/ops/paper_trading_runner.py
```

## Docker Compose Deployment

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+

### Configuration

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  timescaledb:
    image: timescale/timescaledb:latest-pg14
    environment:
      POSTGRES_DB: bist30_trader
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - timescale_data:/var/lib/postgresql/data

  api:
    build: .
    command: uvicorn api.server:app --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"
    environment:
      - DB_HOST=timescaledb
      - DB_PORT=5432
      - DB_NAME=bist30_trader
      - DB_USER=postgres
      - DB_PASSWORD=${DB_PASSWORD}
    depends_on:
      - timescaledb
    volumes:
      - ./models:/app/models
      - ./reports:/app/reports

  mlflow:
    image: ghcr.io/mlflow/mlflow:latest
    command: mlflow server --host 0.0.0.0 --port 5000
    ports:
      - "5000:5000"
    volumes:
      - mlflow_data:/mlflow

volumes:
  timescale_data:
  mlflow_data:
```

### Deployment

```bash
# Build and start services
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

### Accessing Services

- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- MLflow: http://localhost:5000

## Production Server Deployment

### Server Requirements

**Minimum:**
- 4 CPU cores
- 16 GB RAM
- 100 GB SSD
- Ubuntu 22.04 LTS

**Recommended:**
- 8 CPU cores
- 32 GB RAM
- 500 GB SSD
- GPU for TFT training

### Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.12 python3.12-venv postgresql-14 nginx

# Install TimescaleDB
sudo add-apt-repository ppa:timescale/timescaledb-ppa
sudo apt update
sudo apt install timescaledb-postgresql-14

# Configure TimescaleDB
sudo timescaledb-tune

# Clone repository
git clone https://github.com/yourusername/bist30_ai_trader.git
cd bist30_ai_trader

# Set up application
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with production settings

# Initialize database
python scripts/migration/migrate_to_db.py
```

### Systemd Service

**Create service file:** `/etc/systemd/system/bist30-api.service`

```ini
[Unit]
Description=BIST30 AI Trader API
After=network.target postgresql.service

[Service]
Type=simple
User=bist30
WorkingDirectory=/home/bist30/bist30_ai_trader
Environment="PATH=/home/bist30/bist30_ai_trader/.venv/bin"
ExecStart=/home/bist30/bist30_ai_trader/.venv/bin/uvicorn api.server:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable bist30-api
sudo systemctl start bist30-api
sudo systemctl status bist30-api
```

### Nginx Configuration

**Create config:** `/etc/nginx/sites-available/bist30`

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

**Enable site:**
```bash
sudo ln -s /etc/nginx/sites-available/bist30 /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL/TLS with Let's Encrypt

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is configured automatically
```

## Environment Variables

### Required Variables

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bist30_trader
DB_USER=postgres
DB_PASSWORD=your_secure_password

# MLflow
MLFLOW_TRACKING_URI=http://localhost:5000

# API
API_HOST=0.0.0.0
API_PORT=8000
API_SECRET_KEY=your_secret_key_here

# Trading
INITIAL_CAPITAL=100000
MAX_POSITIONS=5
COMMISSION=0.001
```

### Optional Variables

```bash
# GPU Configuration
HSA_OVERRIDE_GFX_VERSION=10.3.0  # For AMD GPUs
CUDA_VISIBLE_DEVICES=0           # For NVIDIA GPUs

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/bist30/app.log

# Performance
WORKERS=4
MAX_CONNECTIONS=100
```

## Database Management

### Backup

```bash
# Create backup
pg_dump -U postgres bist30_trader > backup_$(date +%Y%m%d).sql

# Automated daily backup
cat > /etc/cron.daily/bist30-backup << 'EOF'
#!/bin/bash
pg_dump -U postgres bist30_trader | gzip > /backups/bist30_$(date +%Y%m%d).sql.gz
find /backups -name "bist30_*.sql.gz" -mtime +30 -delete
EOF
chmod +x /etc/cron.daily/bist30-backup
```

### Restore

```bash
# Restore from backup
psql -U postgres bist30_trader < backup_20260219.sql
```

### Maintenance

```bash
# Vacuum database
psql -U postgres -d bist30_trader -c "VACUUM ANALYZE;"

# Reindex
psql -U postgres -d bist30_trader -c "REINDEX DATABASE bist30_trader;"
```

## Monitoring

### Application Logs

```bash
# View API logs
sudo journalctl -u bist30-api -f

# View application logs
tail -f /var/log/bist30/app.log
```

### System Monitoring

```bash
# CPU and memory
htop

# Disk usage
df -h

# Database connections
psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"
```

### Performance Monitoring

```bash
# API response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/

# Database query performance
psql -U postgres -d bist30_trader -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

## Security Best Practices

### 1. Firewall Configuration

```bash
# Allow SSH, HTTP, HTTPS
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. Database Security

```bash
# Restrict PostgreSQL access
# Edit /etc/postgresql/14/main/pg_hba.conf
# Change: host all all 0.0.0.0/0 md5
# To: host all all 127.0.0.1/32 md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### 3. Application Security

- Use strong passwords
- Enable API authentication
- Implement rate limiting
- Regular security updates
- Monitor access logs

### 4. SSL/TLS

- Use HTTPS only
- Strong cipher suites
- HSTS headers
- Certificate auto-renewal

## Scaling

### Horizontal Scaling

```bash
# Multiple API workers
uvicorn api.server:app --workers 8

# Load balancer (Nginx)
upstream bist30_api {
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}
```

### Database Scaling

- Read replicas for queries
- Connection pooling
- Query optimization
- Partitioning large tables

## Troubleshooting

### API Not Starting

```bash
# Check logs
sudo journalctl -u bist30-api -n 50

# Check port availability
sudo netstat -tulpn | grep 8000

# Test configuration
.venv/bin/uvicorn api.server:app --check
```

### Database Connection Issues

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
psql -U postgres -d bist30_trader -c "SELECT 1;"

# Check connections
psql -U postgres -c "SELECT * FROM pg_stat_activity;"
```

### High Memory Usage

```bash
# Check memory
free -h

# Reduce workers
# Edit systemd service: --workers 2

# Optimize database
psql -U postgres -d bist30_trader -c "VACUUM FULL;"
```

## Maintenance Tasks

### Daily

- Check logs for errors
- Monitor disk space
- Verify backups

### Weekly

- Review performance metrics
- Update dependencies
- Security patches

### Monthly

- Database maintenance
- Log rotation
- Capacity planning

## Related Documentation

- [Main README](../README.md)
- [Architecture](architecture.md)
- [API Documentation](api.md)
