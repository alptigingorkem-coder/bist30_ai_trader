"""
Merkezi Logging Yapılandırması
------------------------------
Tüm modüller için standart logging altyapısı.

Kullanım:
    from utils.logging_config import get_logger
    logger = get_logger(__name__)
    logger.info("Mesaj")
    logger.warning("Uyarı")
    logger.error("Hata")
"""

import logging
import os
import sys
from datetime import datetime


# Log dizini
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Log dosyası
LOG_FILE = os.path.join(LOG_DIR, "system.log")

# Format
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Root logger'ı bir kez configure et
_configured = False


def _setup_root_logger():
    """Root logger'ı sadece bir kez yapılandır."""
    global _configured
    if _configured:
        return
    
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    
    # Console handler (INFO+)
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    root.addHandler(console)
    
    # File handler (DEBUG+, rotating)
    try:
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
        root.addHandler(file_handler)
    except Exception:
        pass  # Dosya yazılamıyorsa console devam etsin
    
    _configured = True


def get_logger(name: str) -> logging.Logger:
    """
    İsimlendirilmiş logger döndürür.
    
    Args:
        name: Modül adı (genellikle __name__)
    
    Returns:
        logging.Logger instance
    """
    _setup_root_logger()
    return logging.getLogger(name)
