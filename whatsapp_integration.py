import os
import requests
from flask import Flask, request, jsonify
from bot_logic import RentalBot

app = Flask(__name__)

# Configurações
GOOGLE_SHEET_URL = os.getenv("GOOGLE_SHEET_URL")
SERVICE_ACCOUNT_PATH = os.getenv("SERVICE_ACCOUNT_PATH", "service_account.json")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

bot = RentalBot(google_sheet_url=GOOGLE_SHEET_URL)

try:
    bot.connect_to_sheet(credentials_path=SERVICE_ACCOUNT_PATH)
except Exception as e:
    print(f"Erro ao conectar ao Google Sheet: {e}")

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        # Validação do Facebook
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        return "Token inválido", 403

    # Recebimento de mensagens
    data = request.json
    # ... (resto do código de processamento de mensagens)
    return jsonify({"status": "success"}), 200

@app.route("/", methods=["GET"])
def home():
    return "Robô de Locação Online!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
