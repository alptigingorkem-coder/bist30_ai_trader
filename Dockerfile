# Base Image: Python 3.12 Slim
FROM python:3.12-slim

# Install system dependencies
# libpq-dev: PostgreSQL driver
# gcc: Compilation for some python packages
# curl: Healthchecks
# git: For installing git dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    g++ \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install build tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install ROCm-compatible PyTorch (Preview/Stable for ROCm 6.2)
# Note: Using python 3.12 might require specific pre-release or stable versions.
# We use the official pytorch rocm index.
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.2

# Copy requirements
COPY requirements.txt .

# Install other Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install pandas-ta from PyPI with --no-deps to bypass broken metadata (numpy requirement typo)
RUN pip install --no-cache-dir --no-deps pandas-ta

# Environment Variable for AMD ROCm Support (RDNA2)
ENV HSA_OVERRIDE_GFX_VERSION=10.3.0
ENV PYTHONUNBUFFERED=1

# Application Code
COPY . .

# Run Command (Default to Paper Trader in EOD mode)
CMD ["python", "scripts/paper_trading_runner.py"]
