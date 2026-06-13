import os
from fastapi import FastAPI, Request
import ccxt
import uvicorn
import requests

app = FastAPI()

# 1. GİZLİ BİLGİLERİ SİSTEMDEN ÇEK (Kodun içinde şifre kalmadı!)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")

exchange = ccxt.binance({
    'apiKey': BINANCE_API_KEY,
    'secret': BINANCE_SECRET_KEY,
    'enableRateLimit': True,
})
exchange.set_sandbox_mode(True) # Demo mod aktif


def send_telegram_message(message):
    # BURASI DÜZELTİLDİ: api.telegram.org ve /bot eklendi
    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, json=payload)

@app.post("/webhook")
async def receive_webhook(request: Request):
    try:
        # TradingView'dan gelen sinyal verisini oku (JSON formatında)
        data = await request.json()
        print("Gelen Sinyal:", data)
        
        symbol = data.get("symbol", "BTC/USDT") # Örn: BTC/USDT
        action = data.get("action")            # buy veya sell
        amount = data.get("amount", 0.001)       # İşlem miktarı

        if action == "buy":
            # Borsaya Piyasa Fiyatından Alım Emri Gönder
            order = exchange.create_market_buy_order(symbol, amount)
            msg = f"🟢 ALIM YAPILDI!\nSembol: {symbol}\nMiktar: {amount}\nFiyat: {order['price']}"
            send_telegram_message(msg)
            
        elif action == "sell":
            # Borsaya Piyasa Fiyatından Satım Emri Gönder
            order = exchange.create_market_sell_order(symbol, amount)
            msg = f"🔴 SATIM YAPILDI!\nSembol: {symbol}\nMiktar: {amount}\nFiyat: {order['price']}"
            send_telegram_message(msg)

        return {"status": "success", "order_id": order['id']}

    except Exception as e:
        error_msg = f"⚠️ HATA OLUŞTU: {str(e)}"
        send_telegram_message(error_msg)
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
