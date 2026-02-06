
import pandas as pd
import yfinance as yf
from evds import evdsAPI
import os

class TurkeyMacroData:
    def __init__(self, evds_key=None):
        # API Key önceliği: Parametre > Çevre Değişkeni > Hardcoded (Placeholder)
        self.api_key = evds_key or os.getenv('EVDS_API_KEY')
        if not self.api_key:
            print("UYARI: EVDS API Key bulunamadı. Lütfen çevre değişkeni olarak atayın veya __init__'e geçin.")
            print("Örn: os.environ['EVDS_API_KEY'] = 'YOUR_KEY'")
            self.evds = None
        else:
            self.evds = evdsAPI(self.api_key)

    def fetch_all(self, start_date='2018-01-01'):
        """Tüm makro verileri çeker ve günlük frekansta birleştirir."""
        print("Makro veriler çekiliyor (TCMB + Yahoo Finance)...")
        
        data_frames = []
        
        # 1. TCMB Verileri (EVDS)
        if self.evds:
            try:
                # Tarih formatı: DD-MM-YYYY
                start_date_evds = pd.to_datetime(start_date).strftime('%d-%m-%Y')
                end_date_evds = pd.Timestamp.now().strftime('%d-%m-%Y')
                
                # TCMB Politika Faizi (TP.FG2 - 1 Hafta Repo) & USD (TP.DK.USD.A - Alış)
                # Not: EVDS kütüphanesi get_data dönüşünde bazen tarih sütunu 'Tarih' olarak gelir.
                evds_data = self.evds.get_data(['TP.FG2', 'TP.DK.USD.A'], startdate=start_date_evds, enddate=end_date_evds)
                
                if evds_data and not evds_data.empty:
                    # Sütun isimlerini düzelt
                    evds_data.rename(columns={
                        'TP_FG2': 'tcmb_rate',
                        'TP_DK_USD_A': 'usdtry_offical'
                    }, inplace=True)
                    
                    # Tarih sütunu
                    if 'Tarih' in evds_data.columns:
                        evds_data['Date'] = pd.to_datetime(evds_data['Tarih'], format='%d-%m-%Y', errors='coerce')
                        evds_data.set_index('Date', inplace=True)
                        evds_data.drop(columns=['Tarih'], inplace=True, errors='ignore')
                    
                    # Sayısal olmayanları temizle ve doldur
                    for col in ['tcmb_rate', 'usdtry_offical']:
                        if col in evds_data.columns:
                            evds_data[col] = pd.to_numeric(evds_data[col], errors='coerce')
                    
                    # Günlük frekansa genişlet (Forward Fill)
                    evds_data = evds_data.resample('D').ffill()
                    data_frames.append(evds_data)
                    print(f"  [EVDS] TCMB verisi çekildi: {len(evds_data)} gün")
                    
            except Exception as e:
                print(f"  [HATA] EVDS verisi çekilemedi: {e}")

        # 2. Yahoo Finance Verileri
        yf_tickers = {
            'gold': 'GC=F',       # Altın Futures
            'bist100': 'XU100.IS',# BIST 100
            'sp500': '^GSPC',     # S&P 500
            'vix': '^VIX',        # Volatilite Endeksi
            'usdtry': 'TRY=X'     # USD/TRY (Yedek/Realtime)
        }
        
        try:
            yf_data = yf.download(list(yf_tickers.values()), start=start_date, progress=False)['Close']
            
            # Sütun isimlerini eşle
            inv_map = {v: k for k, v in yf_tickers.items()}
            yf_data.rename(columns=inv_map, inplace=True)
            
            # Eksik verileri doldur (Forward Fill)
            yf_data.fillna(method='ffill', inplace=True)
            
            data_frames.append(yf_data)
            print(f"  [YF] Global piyasa verileri çekildi: {len(yf_data)} gün")
            
        except Exception as e:
            print(f"  [HATA] Yahoo Finance verisi çekilemedi: {e}")
            
        # 3. Birleştirme
        if not data_frames:
            return pd.DataFrame()
            
        combined_df = pd.concat(data_frames, axis=1)
        
        # Son temizlik (Forward Fill sonra DropNA)
        combined_df.fillna(method='ffill', inplace=True)
        # combined_df.dropna(inplace=True) # Çok agresif olmasın, baştaki NaN'lar kalsın
        
        # Hafta sonlarını doldur (Opsiyonel, borsa günleri yeterli olabilir ama TFT için sürekli zaman serisi iyidir)
        combined_df = combined_df.resample('D').ffill()
        
        return combined_df

if __name__ == "__main__":
    # Test
    # API Key yoksa sadece YF çalışır, EVDS hata verir veya boş döner.
    loader = TurkeyMacroData() 
    df = loader.fetch_all()
    print(df.tail())
    print(df.info())
