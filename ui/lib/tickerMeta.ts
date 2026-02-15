// BIST 30 Ticker Metadata

interface TickerMeta {
    name: string;
    sector: string;
    description?: string;
}

const TICKER_META: Record<string, TickerMeta> = {
    AKBNK: { name: "Akbank", sector: "Bankacılık" },
    ALARK: { name: "Alarko Holding", sector: "Holding" },
    ASELS: { name: "Aselsan", sector: "Savunma" },
    ASTOR: { name: "Astor Enerji", sector: "Enerji" },
    BIMAS: { name: "BİM", sector: "Perakende" },
    EKGYO: { name: "Emlak Konut", sector: "GYO" },
    ENKAI: { name: "Enka İnşaat", sector: "İnşaat" },
    EREGL: { name: "Ereğli Demir Çelik", sector: "Metal" },
    FROTO: { name: "Ford Otosan", sector: "Otomotiv" },
    GARAN: { name: "Garanti BBVA", sector: "Bankacılık" },
    GUBRF: { name: "Gübre Fabrikaları", sector: "Kimya" },
    HEKTS: { name: "Hektaş", sector: "Kimya" },
    ISCTR: { name: "İş Bankası", sector: "Bankacılık" },
    KCHOL: { name: "Koç Holding", sector: "Holding" },
    KONTR: { name: "Kontrolmatik", sector: "Enerji" },
    KRDMD: { name: "Kardemir", sector: "Metal" },
    ODAS: { name: "Odaş Enerji", sector: "Enerji" },
    OYAKC: { name: "Oyak Çimento", sector: "Çimento" },
    PETKM: { name: "Petkim", sector: "Petrokimya" },
    PGSUS: { name: "Pegasus", sector: "Havayolu" },
    SAHOL: { name: "Sabancı Holding", sector: "Holding" },
    SASA: { name: "SASA Polyester", sector: "Kimya" },
    SISE: { name: "Şişecam", sector: "Cam" },
    TAVHL: { name: "TAV Havalimanları", sector: "Havacılık" },
    TCELL: { name: "Turkcell", sector: "Telekom" },
    THYAO: { name: "Türk Hava Yolları", sector: "Havayolu" },
    TOASO: { name: "Tofaş", sector: "Otomotiv" },
    TSKB: { name: "TSKB", sector: "Bankacılık" },
    TTKOM: { name: "Türk Telekom", sector: "Telekom" },
    TUPRS: { name: "Tüpraş", sector: "Enerji" },
    YKBNK: { name: "Yapı Kredi", sector: "Bankacılık" },
    XU100: { name: "BIST 100 Endeksi", sector: "Endeks" },
};

const DEFAULT_META: TickerMeta = { name: "Bilinmeyen", sector: "Diğer" };

export function getTickerMeta(symbol: string): TickerMeta {
    return TICKER_META[symbol] || DEFAULT_META;
}

export function getVolatilityLevel(changePercent: number): string {
    const abs = Math.abs(changePercent);
    if (abs < 1) return "DÜŞÜK";
    if (abs < 3) return "NORMAL";
    if (abs < 5) return "YÜKSEK";
    return "ÇOK YÜKSEK";
}
