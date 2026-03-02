
from flask import Flask, request, jsonify
from bot_logic import RentalBot
import os

app = Flask(__name__)

# Initialize the bot (Google Sheet URL and credentials path will be configured by the user)
# IMPORTANT: Replace with your actual Google Sheet URL and credentials path
GOOGLE_SHEET_URL = os.getenv("GOOGLE_SHEET_URL", "YOUR_GOOGLE_SHEET_URL_HERE")
SERVICE_ACCOUNT_PATH = os.getenv("SERVICE_ACCOUNT_PATH", "service_account.json")

bot = RentalBot(google_sheet_url=GOOGLE_SHEET_URL)

# Attempt to connect to Google Sheet on startup
try:
    bot.connect_to_sheet(credentials_path=SERVICE_ACCOUNT_PATH)
except Exception as e:
    print(f"Could not connect to Google Sheet on startup: {e}")

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print(f"Received webhook data: {data}")

    # This part depends heavily on the WhatsApp API provider (e.g., Evolution API, Typebot)
    # You will need to adapt this to the specific payload structure of your chosen API.
    # For demonstration, let's assume a simple structure where 'message' is the text and 'sender' is the phone number.
    
    # Example for Evolution API (simplified)
    # if data and 'messages' in data:
    #     for msg_data in data['messages']:
    #         if msg_data['type'] == 'chat' and 'body' in msg_data:
    #             user_message = msg_data['body']
    #             sender_id = msg_data['from']
    #             # Process message and send response
    #             response_text = process_message(user_message, sender_id)
    #             send_whatsapp_message(sender_id, response_text)

    # For now, let's simulate a simple text message processing
    user_message = data.get("message", "").lower()
    sender_id = data.get("sender", "+5511999999999") # Placeholder sender ID

    response_text = ""

    if "olá" in user_message or "oi" in user_message or "menu" in user_message:
        response_text = "Olá! Bem-vindo(a) à nossa locadora de brinquedos! Como posso ajudar?\n\n"
        response_text += "1. Ver brinquedos disponíveis e preços\n"
        response_text += "2. Calcular valor de aluguel\n"
        response_text += "3. Agendar um brinquedo\n"
        response_text += "4. Falar com um atendente"
    elif "1" in user_message and ("brinquedos" in user_message or "preços" in user_message):
        response_text = bot.get_available_toys()
    elif "2" in user_message and "calcular" in user_message:
        response_text = "Para calcular o valor, me diga quais brinquedos você quer, por quantos dias e o endereço de entrega (ex: 'Quero Pula-Pula Grande e Mesa de Pebolim por 2 dias na Zona Leste')."
    elif "3" in user_message and "agendar" in user_message:
        response_text = "Para agendar, preciso saber: qual brinquedo, data de início e fim, seu nome, telefone e endereço completo. (ex: 'Agendar Pula-Pula Grande de 10/04/2026 a 11/04/2026, meu nome é João, tel (11)9xxxx-xxxx, Endereço: Rua X, 123, Bairro Y')."
    elif "4" in user_message and "atendente" in user_message:
        response_text = "Entendido! Um de nossos atendentes entrará em contato em breve. Por favor, aguarde."
    elif "quero" in user_message and "dias" in user_message and "na" in user_message:
        # Ex: 'Quero Pula-Pula Grande e Mesa de Pebolim por 2 dias na Zona Leste'
        try:
            parts = user_message.split(" por ")
            toys_part = parts[0].replace("quero ", "").strip()
            days_and_location_part = parts[1].strip()

            num_days_str = days_and_location_part.split(" dias ")[0]
            num_days = int(num_days_str)

            location_part = days_and_location_part.split(" na ")[1].strip()
            address = location_part # Simplified for now, can be more complex later

            selected_toys_raw = toys_part.split(" e ")
            selected_toys = [toy.strip().replace("pula-pula", "pula-pula ") for toy in selected_toys_raw]

            price_info = bot.calculate_rental_price(selected_toys, num_days, address)
            if isinstance(price_info, str): # Error message from calculate_rental_price
                response_text = price_info
            else:
                response_text = price_info["details"]
        except Exception as e:
            response_text = f"Não entendi o pedido de cálculo. Por favor, use o formato: 'Quero [Brinquedo 1] e [Brinquedo 2] por [X] dias na [Endereço/Zona]'. Erro: {e}"
    elif "agendar" in user_message and "de " in user_message and "a " in user_message and "meu nome é " in user_message:
        # Ex: 'Agendar Pula-Pula Grande de 10/04/2026 a 11/04/2026, meu nome é João, tel (11)9xxxx-xxxx, Endereço: Rua X, 123, Bairro Y'
        try:
            # Extract toy name
            toy_start_index = user_message.find("agendar ") + len("agendar ")
            toy_end_index = user_message.find(" de ", toy_start_index)
            toy_name = user_message[toy_start_index:toy_end_index].strip()

            # Extract dates
            date_start_index = user_message.find(" de ", toy_end_index) + len(" de ")
            date_end_index = user_message.find(" a ", date_start_index)
            start_date_str = user_message[date_start_index:date_end_index].strip()

            date_end_index_final = user_message.find(", meu nome é ", date_end_index) # Find end of date range
            end_date_str = user_message[date_end_index + len(" a "):date_end_index_final].strip()

            # Extract client name
            name_start_index = user_message.find("meu nome é ", date_end_index_final) + len("meu nome é ")
            name_end_index = user_message.find(", tel ", name_start_index)
            client_name = user_message[name_start_index:name_end_index].strip()

            # Extract phone
            phone_start_index = user_message.find(", tel ", name_end_index) + len(", tel ")
            phone_end_index = user_message.find(", Endereço: ", phone_start_index)
            client_phone = user_message[phone_start_index:phone_end_index].strip()

            # Extract address
            address_start_index = user_message.find(", Endereço: ", phone_end_index) + len(", Endereço: ")
            address = user_message[address_start_index:].strip()

            # Check availability and book
            if bot.sheet:
                availability = bot.check_availability(toy_name, start_date_str, end_date_str)
                if availability is True:
                    booking_result = bot.book_toy(toy_name, start_date_str, end_date_str, client_name, client_phone, address)
                    response_text = booking_result
                elif isinstance(availability, str): # Error message from check_availability
                    response_text = availability
                else:
                    response_text = f"O brinquedo {toy_name} não está disponível entre {start_date_str} e {end_date_str}."
            else:
                response_text = "Não foi possível agendar. O sistema de agenda não está conectado. Por favor, configure a conexão com o Google Sheets."

        except Exception as e:
            response_text = f"Não entendi o pedido de agendamento. Por favor, use o formato: 'Agendar [Brinquedo] de [DD/MM/AAAA] a [DD/MM/AAAA], meu nome é [Seu Nome], tel [Seu Telefone], Endereço: [Seu Endereço Completo]'. Erro: {e}"
    else:
        response_text = "Desculpe, não entendi sua mensagem. Por favor, escolha uma opção do menu ou reformule sua pergunta."

    # In a real scenario, you would send this response_text back to WhatsApp
    # using the specific API provider's method (e.g., Evolution API, Typebot).
    # For this example, we just return it in the webhook response.
    print(f"Sending response: {response_text}")
    return jsonify({"status": "success", "response": response_text})


# Placeholder for sending WhatsApp message (replace with actual API call)
def send_whatsapp_message(recipient_id, message_text):
    print(f"Simulating sending message to {recipient_id}: {message_text}")
    # Example using requests library for a hypothetical API
    # import requests
    # url = "YOUR_WHATSAPP_API_SEND_URL"
    # headers = {"Authorization": "Bearer YOUR_API_TOKEN"}
    # payload = {"to": recipient_id, "text": message_text}
    # response = requests.post(url, headers=headers, json=payload)
    # print(f"WhatsApp API response: {response.status_code} - {response.text}")

if __name__ == "__main__":
    # For local testing, you might want to run this directly
    # In a production environment, this would be run by a WSGI server like Gunicorn
    app.run(host="0.0.0.0", port=5000)

