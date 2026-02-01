class SectorAllocator:
    def __init__(self, max_concentration=0.40):
        self.max_concentration = max_concentration
        self.current_allocation = {}  # {sector: total_size}
        
    def can_add_position(self, sector, proposed_size):
        """
        FIX 17: Sektör konsantrasyon kontrolü
        """
        current_sector_size = self.current_allocation.get(sector, 0.0)
        new_sector_size = current_sector_size + proposed_size
        
        if new_sector_size > self.max_concentration:
            allowed_size = self.max_concentration - current_sector_size
            return max(0.0, allowed_size)  # Kalan alanı ver
            
        return proposed_size

    def update_allocation(self, sector, size):
        """Pozisyon eklendikten sonra durumu günceller."""
        if size > 0:
            self.current_allocation[sector] = self.current_allocation.get(sector, 0.0) + size
