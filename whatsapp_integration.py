import os
import requests
from flask import Flask, request, jsonify
from bot_logic import RentalBot

app = Flask(__name__)

# Configurações do Bot e Google Sheets
GOOGLE_SHEET_URL = os.getenv("GOOGLE_SHEET_URL")
SERVICE_ACCOUNT_PATH = os.getenv("SERVICE_ACCOUNT_PATH", "service_account.json")

# Configurações da API de QR Code (Ex: Evolution API)
API_URL = os.getenv("API_URL") # O link que a empresa de API vai te dar
API_KEY = os.getenv("API_KEY") # A senha que a empresa de API vai te dar

bot = RentalBot(google_sheet_url=GOOGLE_SHEET_URL)

try:
    bot.connect_to_sheet(credentials_path=SERVICE_ACCOUNT_PATH)
    print("Bot conectado à planilha com sucesso!")
except Exception as e:
    print(f"Erro ao conectar à planilha: {e}")

def send_message(to, text):
    """Envia mensagem via API de QR Code"""
    url = f"{API_URL}/message/sendText/sua_instancia"
    headers = {"apikey": API_KEY, "Content-Type": "application/json"}
    payload = {"number": to, "options": {"delay": 1200}, "textMessage": {"text": text}}
    requests.post(url, headers=headers, json=payload)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    # Lógica para ler a mensagem vinda da Evolution API
    try:
        message_data = data.get("data", {})
        sender = message_data.get("key", {}).get("remoteJid", "").split("@")[0]
        text = message_data.get("message", {}).get("conversation", "").lower()
        
        if text:
            # Aqui entra a lógica do seu bot (Menu, Preços, etc)
            response = "Olá! Recebi sua mensagem: " + text
            send_message(sender, response)
            
    except Exception as e:
        print(f"Erro: {e}")
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
