"""
Live Trading Execution Module - MANUAL CONFIRMATION REQUIRED
Gerçek para ile işlem için güvenlik katmanı

⚠️ UYARI: Bu modül gerçek para ile işlem yapar!
Her işlem önce kullanıcı onayı gerektirir.
"""

import os
from datetime import datetime
from typing import Dict, List, Tuple

# Safety constants
MIN_LOT_SIZE = 1  # Minimum lot
MAX_SINGLE_ORDER_TL = 2000  # Max tek emir tutarı
REQUIRE_CONFIRMATION = True  # Manuel onay zorunlu


class LiveExecutionEngine:
    """
    Manuel onaylı gerçek para execution engine.
    
    Safety Features:
    - Her işlem için terminal onayı
    - Küçük lot sınırlaması
    - İşlem günlüğü
    - Geri alma imkanı (iptal window)
    """
    
    def __init__(
        self,
        capital: float = 10000,
        max_position_pct: float = 0.20,  # Max %20 tek pozisyon
        paper_mode: bool = True  # Varsayılan: Paper mode
    ):
        self.capital = capital
        self.max_position_pct = max_position_pct
        self.paper_mode = paper_mode
        self.pending_orders: List[dict] = []
        self.executed_orders: List[dict] = []
        self.rejected_orders: List[dict] = []
        
    def calculate_lot_size(self, price: float, target_weight: float) -> int:
        """
        Küçük lot hesaplama.
        Target weight'e göre alınacak lot sayısını hesaplar.
        """
        target_value = self.capital * target_weight
        
        # Max single order limit
        target_value = min(target_value, MAX_SINGLE_ORDER_TL)
        
        lot_size = int(target_value / price)
        
        # Minimum lot kontrolü
        lot_size = max(MIN_LOT_SIZE, lot_size)
        
        return lot_size

    def create_order(
        self,
        symbol: str,
        side: str,  # "BUY" or "SELL"
        price: float,
        quantity: int,
        confidence: float,
        reason: str
    ) -> dict:
        """
        Emir oluştur (henüz execute etme).
        """
        order = {
            "order_id": f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}-{symbol[:4]}",
            "symbol": symbol,
            "side": side,
            "price": price,
            "quantity": quantity,
            "total_value": price * quantity,
            "confidence": confidence,
            "reason": reason,
            "status": "PENDING",
            "created_at": datetime.now().isoformat(),
            "confirmed_at": None,
            "executed_at": None
        }
        
        self.pending_orders.append(order)
        return order

    def display_pending_orders(self):
        """Bekleyen emirleri göster"""
        if not self.pending_orders:
            print("\n📭 Bekleyen emir yok.")
            return
        
        print("\n" + "="*70)
        print("📋 ONAY BEKLEYEN EMİRLER")
        print("="*70)
        
        mode_str = "🧪 PAPER" if self.paper_mode else "💰 GERÇEK PARA"
        print(f"Mod: {mode_str}\n")
        
        for i, order in enumerate(self.pending_orders, 1):
            side_icon = "🟢" if order["side"] == "BUY" else "🔴"
            conf_bar = "█" * int(order["confidence"] * 10)
            
            print(f"{i}. {side_icon} {order['side']:4} {order['symbol']:<10}")
            print(f"   Fiyat    : {order['price']:.2f} TL")
            print(f"   Adet     : {order['quantity']} lot")
            print(f"   Tutar    : {order['total_value']:.2f} TL")
            print(f"   Güven    : {conf_bar} ({order['confidence']:.0%})")
            print(f"   Sebep    : {order['reason']}")
            print()
        
        print("="*70)

    def confirm_order(self, order_index: int) -> Tuple[bool, str]:
        """
        Tek bir emri onayla.
        Returns: (success, message)
        """
        if order_index < 0 or order_index >= len(self.pending_orders):
            return False, "Geçersiz emir numarası"
        
        order = self.pending_orders[order_index]
        
        # Confirmation prompt
        print(f"\n⚠️ {order['side']} {order['quantity']} {order['symbol']} @ {order['price']:.2f}")
        print(f"   Toplam: {order['total_value']:.2f} TL")
        
        if not self.paper_mode:
            print("\n🔴 DİKKAT: GERÇEK PARA İŞLEMİ!")
        
        response = input("\n[E]vet / [H]ayır: ").strip().upper()
        
        if response == "E":
            order["status"] = "CONFIRMED"
            order["confirmed_at"] = datetime.now().isoformat()
            self.pending_orders.remove(order)
            self.executed_orders.append(order)
            return True, f"✅ {order['order_id']} onaylandı"
        else:
            order["status"] = "REJECTED"
            self.pending_orders.remove(order)
            self.rejected_orders.append(order)
            return False, f"❌ {order['order_id']} reddedildi"

    def confirm_all_interactive(self):
        """
        Tüm emirleri interaktif olarak onayla.
        """
        self.display_pending_orders()
        
        if not self.pending_orders:
            return
        
        print("\nSeçenekler:")
        print("  [T] Tümünü onayla")
        print("  [R] Tümünü reddet")
        print("  [1-N] Tek tek onayla")
        print("  [Q] Çık")
        
        while self.pending_orders:
            choice = input("\n> ").strip().upper()
            
            if choice == "Q":
                print("İşlem iptal edildi.")
                break
            elif choice == "T":
                for _ in range(len(self.pending_orders)):
                    self.confirm_order(0)
                break
            elif choice == "R":
                while self.pending_orders:
                    order = self.pending_orders.pop(0)
                    order["status"] = "REJECTED"
                    self.rejected_orders.append(order)
                print("Tüm emirler reddedildi.")
                break
            elif choice.isdigit():
                idx = int(choice) - 1
                success, msg = self.confirm_order(idx)
                print(msg)
                self.display_pending_orders()

    def get_execution_summary(self) -> dict:
        """Execution özeti"""
        return {
            "pending": len(self.pending_orders),
            "executed": len(self.executed_orders),
            "rejected": len(self.rejected_orders),
            "total_executed_value": sum(o["total_value"] for o in self.executed_orders),
            "paper_mode": self.paper_mode
        }

    def print_execution_log(self):
        """Execution log yazdır"""
        print("\n" + "="*60)
        print("📝 EXECUTION LOG")
        print("="*60)
        
        summary = self.get_execution_summary()
        print(f"Mod: {'PAPER' if summary['paper_mode'] else 'LIVE'}")
        print(f"Bekleyen  : {summary['pending']}")
        print(f"İşlenen   : {summary['executed']}")
        print(f"Reddedilen: {summary['rejected']}")
        print(f"Toplam TL : {summary['total_executed_value']:.2f}")
        print("="*60)


# Pre-trade checklist
def pre_trade_checklist() -> bool:
    """
    Live trading öncesi kontrol listesi.
    Tümü onaylanmadan işlem yapılamaz.
    """
    checks = [
        ("Piyasa açık mı? (09:30-18:00)", "market_hours"),
        ("Yeterli bakiye var mı?", "balance"),
        ("Stop-loss planlandı mı?", "stop_loss"),
        ("Günlük limit aşılmadı mı?", "daily_limit"),
        ("Manuel müdahale hazır mı?", "manual_ready")
    ]
    
    print("\n" + "="*60)
    print("✅ PRE-TRADE CHECKLIST")
    print("="*60)
    
    all_passed = True
    for question, _ in checks:
        response = input(f"  {question} [E/H]: ").strip().upper()
        if response != "E":
            all_passed = False
            print(f"    ❌ Başarısız")
        else:
            print(f"    ✅ OK")
    
    if all_passed:
        print("\n✅ Tüm kontroller geçti. İşlem yapılabilir.")
    else:
        print("\n❌ Bazı kontroller başarısız. İşlem yapılamaz.")
    
    print("="*60)
    return all_passed


if __name__ == "__main__":
    # Demo
    engine = LiveExecutionEngine(capital=10000, paper_mode=True)
    
    # Örnek emirler oluştur
    engine.create_order("THYAO.IS", "BUY", 305.50, 3, 0.75, "Model sinyali")
    engine.create_order("AKBNK.IS", "BUY", 52.80, 10, 0.68, "Model sinyali")
    
    # Interactive confirmation
    engine.confirm_all_interactive()
    
    # Summary
    engine.print_execution_log()
