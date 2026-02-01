"""
TCMB EVDS API Helper - Yabancı Portföy Akışı Verisi

Bu modül TCMB (Türkiye Cumhuriyet Merkez Bankası) EVDS API'sinden
yabancı yatırımcıların haftalık portföy akışı verilerini çeker.

API Key Almak İçin:
1. https://evds2.tcmb.gov.tr/ adresine gidin
2. "Kayıt Ol" butonuna tıklayın (ücretsiz)
3. Email doğrulama yapın
4. "Profil > API Key" bölümünden key'inizi alın
5. config.py'ye ekleyin: TCMB_API_KEY = "your_key_here"
"""

from evds import evdsAPI
import pandas as pd
import config

class TCMBDataFetcher:
    def __init__(self, api_key=None):
        """
        TCMB EVDS API wrapper
        
        Parameters:
        -----------
        api_key : str
            TCMB API key (config.TCMB_API_KEY'den alınır)
        """
        self.api_key = api_key or getattr(config, 'TCMB_API_KEY', None)
        
        if not self.api_key:
            raise ValueError(
                "TCMB API Key bulunamadı! "
                "Lütfen config.py'ye TCMB_API_KEY = 'your_key' ekleyin. "
                "Key almak için: https://evds2.tcmb.gov.tr/"
            )
        
        self.evds = evdsAPI(self.api_key)
    
    def get_foreign_portfolio_flows(self, start_date, end_date=None):
        """
        Yabancı portföy akışı verilerini çeker (haftalık)
        
        Parameters:
        -----------
        start_date : str
            Başlangıç tarihi (YYYY-MM-DD formatında)
        end_date : str, optional
            Bitiş tarihi (varsayılan: bugün)
            
        Returns:
        --------
        pd.DataFrame
            Columns: Date (index), Foreign_Net_Stock_Flow (Milyon USD)
        """
        # EVDS Serisi: TP.YSSK.A02 - Yabancıların Net Hisse Senedi Alımı
        series_code = "TP.YSSK.A02"
        
        # Format date for EVDS API (requires DD-MM-YYYY)
        start_evds = pd.to_datetime(start_date).strftime('%d-%m-%Y')
        end_evds = pd.to_datetime(end_date).strftime('%d-%m-%Y') if end_date else pd.Timestamp.now().strftime('%d-%m-%Y')
        
        try:
            # Fetch data from EVDS
            data = self.evds.get_data(
                [series_code],
                startdate=start_evds,
                enddate=end_evds
            )
            
            if data is None or data.empty:
                print(f"  Uyarı: TCMB'den {start_date} - {end_date} için veri gelmedi.")
                return pd.DataFrame()
            
            # Clean and format
            data['Tarih'] = pd.to_datetime(data['Tarih'], format='%d-%m-%Y')
            data.set_index('Tarih', inplace=True)
            data.rename(columns={series_code: 'Foreign_Net_Stock_Flow'}, inplace=True)
            
            # Convert to numeric (remove commas, handle Turkish number format)
            data['Foreign_Net_Stock_Flow'] = pd.to_numeric(
                data['Foreign_Net_Stock_Flow'].astype(str).str.replace(',', '.'), 
                errors='coerce'
            )
            
            print(f"  TCMB: {len(data)} adet haftalık yabancı akış verisi çekildi.")
            return data
            
        except Exception as e:
            print(f"  HATA: TCMB API çağrısı başarısız: {e}")
            return pd.DataFrame()
    
    def get_multiple_series(self, series_dict, start_date, end_date=None):
        """
        Birden fazla TCMB serisini çek
        
        Parameters:
        -----------
        series_dict : dict
            {column_name: series_code} formatında sözlük
        """
        start_evds = pd.to_datetime(start_date).strftime('%d-%m-%Y')
        end_evds = pd.to_datetime(end_date).strftime('%d-%m-%Y') if end_date else pd.Timestamp.now().strftime('%d-%m-%Y')
        
        try:
            data = self.evds.get_data(
                list(series_dict.values()),
                startdate=start_evds,
                enddate=end_evds
            )
            
            if data is None or data.empty:
                return pd.DataFrame()
            
            data['Tarih'] = pd.to_datetime(data['Tarih'], format='%d-%m-%Y')
            data.set_index('Tarih', inplace=True)
            data.rename(columns={v: k for k, v in series_dict.items()}, inplace=True)
            
            # Convert all columns to numeric
            for col in data.columns:
                data[col] = pd.to_numeric(
                    data[col].astype(str).str.replace(',', '.'), 
                    errors='coerce'
                )
            
            return data
            
        except Exception as e:
            print(f"  HATA: TCMB multi-series çağrısı başarısız: {e}")
            return pd.DataFrame()


if __name__ == "__main__":
    # Test script
    print("TCMB API Test...")
    
    # Check if API key exists
    if not hasattr(config, 'TCMB_API_KEY'):
        print("\n⚠️  API Key bulunamadı!")
        print("config.py'ye şu satırı ekleyin:")
        print("TCMB_API_KEY = 'your_api_key_here'")
        print("\nAPI Key almak için: https://evds2.tcmb.gov.tr/")
    else:
        fetcher = TCMBDataFetcher()
        
        # Test: Son 1 yıl verisi
        start = "2023-01-01"
        flows = fetcher.get_foreign_portfolio_flows(start)
        
        if not flows.empty:
            print(f"\n✅ Başarılı! {len(flows)} veri noktası çekildi.")
            print("\nİlk 5 satır:")
            print(flows.head())
            print("\nSon 5 satır:")
            print(flows.tail())
        else:
            print("\n❌ Veri çekilemedi. API key veya tarih aralığını kontrol edin.")
