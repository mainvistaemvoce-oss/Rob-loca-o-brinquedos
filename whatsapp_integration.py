import os
import requests
from flask import Flask, request, jsonify
from bot_logic import RentalBot

app = Flask(__name__)

# Configurações do Bot e Google Sheets
GOOGLE_SHEET_URL = os.getenv("GOOGLE_SHEET_URL")
SERVICE_ACCOUNT_PATH = os.getenv("SERVICE_ACCOUNT_PATH", "service_account.json")

# Configurações da API de QR Code (Evolution API)
API_URL = os.getenv("API_URL") # Ex: https://sua-api.com
API_KEY = os.getenv("API_KEY" ) # Sua chave de API
INSTANCE_NAME = os.getenv("INSTANCE_NAME", "brinkspark") # Nome da sua instância

bot = RentalBot(google_sheet_url=GOOGLE_SHEET_URL)

try:
    bot.connect_to_sheet(credentials_path=SERVICE_ACCOUNT_PATH)
    print("Bot conectado à planilha com sucesso!")
except Exception as e:
    print(f"Erro ao conectar à planilha: {e}")

def send_message(to, text):
    """Envia mensagem via Evolution API"""
    url = f"{API_URL}/message/sendText/{INSTANCE_NAME}"
    headers = {"apikey": API_KEY, "Content-Type": "application/json"}
    # O número precisa estar no formato 5511999999999
    payload = {"number": to, "options": {"delay": 1200}, "textMessage": {"text": text}}
    try:
        requests.post(url, headers=headers, json=payload)
    except Exception as e:
        print(f"Erro ao enviar mensagem: {e}")

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    try:
        # Lógica para ler a mensagem vinda da Evolution API
        message_data = data.get("data", {})
        sender = message_data.get("key", {}).get("remoteJid", "").split("@")[0]
        
        # Pega o texto da mensagem (pode estar em diferentes campos dependendo da API)
        message = message_data.get("message", {})
        text = message.get("conversation") or message.get("extendedTextMessage", {}).get("text") or ""
        text = text.lower().strip()
        
        if text:
            print(f"Mensagem recebida de {sender}: {text}")
            # CHAMA A LÓGICA DO SEU BOT DE BRINQUEDOS
            response = bot.process_message(text) 
            send_message(sender, response)
            
    except Exception as e:
        print(f"Erro no processamento: {e}")
    return "OK", 200

@app.route("/", methods=["GET"])
def home():
    return "Robô de Locação Online!", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
