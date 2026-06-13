import os
from fastapi import FastAPI, Request
import ccxt
import uvicorn
import requests

app = FastAPI()

# 1. GİZLİ BİLGİLERİ SİSTEMDEN ÇEK (Render Environment Variables'dan okunur)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")

# 2. BORSA BAĞLANTISI VE DEMO AYARLARI
exchange = ccxt.binance({
    'apiKey': BINANCE_API_KEY,
    'secret': BINANCE_SECRET_KEY,
    'enableRateLimit': True,
})

# BURASI TAMAMEN DEMO: İstekler kesinlikle gerçek borsaya DEĞİL, Binance Demo sunucusuna gider!
exchange.urls['api'] = {
    'public': 'https://binance.com',
    'private': 'https://binance.com',
}

def send_telegram_message(message):
    """İşlem sonuçlarını anlık olarak Telegram'a gönderen fonksiyon"""
    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram mesajı gönderilemedi: {e}")

@app.get("/")
async def home():
    """Sunucunun çalışıp çalışmadığını test etmek için ana sayfa"""
    return {"status": "Bot Sunucusu Aktif ve Canlı!"}

@app.post("/webhook")
async def receive_webhook(request: Request):
    """TradingView'dan gelecek alım-satım sinyallerini karşılayan ana merkez"""
    try:
        # TradingView'dan gelen sinyal verisini oku (JSON formatında)
        data = await request.json()
        print("Gelen Sinyal Verisi:", data)
        
        # TradingView'dan gelecek parametreler
        symbol = data.get("symbol", "BTC/USDT") # Örn: BTC/USDT veya ETH/USDT
        action = data.get("action")            # buy veya sell
        amount = data.get("amount", 0.001)       # İşlem yapılacak miktar

        # CCXT kütüphanesi için sembol formatını düzeltme (BTCUSDT -> BTC/USDT)
        if "/" not in symbol:
            if symbol.endswith("USDT"):
                symbol = symbol[:-4] + "/USDT"

        if action == "buy":
            # Demo Borsaya Piyasa Fiyatından (Market) ALIM Emri Gönder
            order = exchange.create_market_buy_order(symbol, amount)
            executed_price = order.get('price') or order.get('average') or data.get('price', 'Bilinmiyor')
            msg = f"🟢 DEMO ALIM YAPILDI!\nSembol: {symbol}\nMiktar: {amount}\nFiyat: {executed_price}"
            send_telegram_message(msg)
            return {"status": "success", "order_id": order.get('id')}
            
        elif action == "sell":
            # Demo Borsaya Piyasa Fiyatından (Market) SATIM Emri Gönder
            order = exchange.create_market_sell_order(symbol, amount)
            executed_price = order.get('price') or order.get('average') or data.get('price', 'Bilinmiyor')
            msg = f"🔴 DEMO SATIM YAPILDI!\nSembol: {symbol}\nMiktar: {amount}\nFiyat: {executed_price}"
            send_telegram_message(msg)
            return {"status": "success", "order_id": order.get('id')}

        else:
            return {"status": "error", "message": "Geçersiz aksiyon. Sadece 'buy' veya 'sell' olmalı."}

    except Exception as e:
        error_msg = f"⚠️ BOT HATA ALDI: {str(e)}"
        print(error_msg)
        send_telegram_message(error_msg)
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
