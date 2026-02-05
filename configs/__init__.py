# Sektör Konfigürasyonları Modülü
from .banking import *
from .holding import *
from .industrial import *
from .growth import *
from .aviation import *
from .automotive import *
from .energy import *
from .steel import *
from .retail import *
from .telecom import *
from .real_estate import *

# Kolay erişim için sözlük
SECTOR_CONFIGS = {
    'BANKING': banking,
    'HOLDING': holding,
    'INDUSTRIAL': industrial,
    'GROWTH': growth,
    'AVIATION': aviation,
    'AUTOMOTIVE': automotive,
    'ENERGY': energy,
    'STEEL': steel,
    'RETAIL': retail,
    'TELECOM': telecom,
    'REAL_ESTATE': real_estate
}

def get_config_for_sector(sector_name):
    """Sektör adına göre ilgili konfigürasyon modülünü döndürür."""
    # Normalize (uppercase, replace spaces)
    key = sector_name.upper().replace(' ', '_')
    return SECTOR_CONFIGS.get(key, None)
