
import gspread
from datetime import datetime, timedelta

class RentalBot:
    def __init__(self, google_sheet_url=None):
        self.toys = {
            "pula-pula pequeno": {"price_day": 120.00, "price_2_days": 200.00, "sizes": ["2.5m"]},
            "pula-pula medio": {"price_day": 120.00, "price_2_days": 200.00, "sizes": ["3m"]},
            "pula-pula grande": {"price_day": 120.00, "price_2_days": 200.00, "sizes": ["4m"]},
            "piscina de bolinhas": {"price_day": 120.00, "price_2_days": None, "sizes": ["1.50m x 1.50m"]},
            "kit infantil": {"price_day": 70.00, "price_2_days": None, "sizes": ["2 cavalinhos + 1 escorregador P"]},
            "mesa de pebolim": {"price_day": 150.00, "price_2_days": None, "sizes": []},
            "mesa de hoquei": {"price_day": 200.00, "price_2_days": None, "sizes": []},
            "kit karaokê": {"price_day": 170.00, "price_2_days": None, "sizes": ["JBL Partybox + 2 Microfones"]}
        }
        self.google_sheet_url = google_sheet_url
        self.sheet = None
        self.freight_rules = {
            "default": 50.00, # Example default freight cost
            "zona_leste": 30.00,
            "zona_oeste": 60.00,
            "zona_norte": 40.00,
            "zona_sul": 70.00
        } # Placeholder for freight rules

    def connect_to_sheet(self, credentials_path='service_account.json'):
        try:
            gc = gspread.service_account(filename=credentials_path)
            self.sheet = gc.open_by_url(self.google_sheet_url).sheet1 # Assuming data is in the first sheet
            print("Conectado ao Google Sheet com sucesso!")
        except Exception as e:
            print(f"Erro ao conectar ao Google Sheet: {e}")
            self.sheet = None

    def get_available_toys(self):
        message = "Brinquedos disponíveis:\n\n"
        for toy_name, details in self.toys.items():
            message += f"• {toy_name.replace('_', ' ').title()} "
            if details['sizes']:
                message += f"({", ".join(details['sizes'])}) "
            message += f"📌 R$ {details['price_day']:.2f} - diária.\n"
            if details['price_2_days']:
                message += f"📌 R$ {details['price_2_days']:.2f} - 2 dias\n"
        message += "\n💰Pagamento 50% no agendamento 50% no dia do evento\n"
        message += "📅 Desconto especial para mais de 1 diária"
        return message

    def calculate_freight(self, address):
        # This is a placeholder. You'll need to implement actual logic
        # based on your delivery areas/zones.
        address_lower = address.lower()
        if "zona leste" in address_lower:
            return self.freight_rules["zona_leste"]
        elif "zona oeste" in address_lower:
            return self.freight_rules["zona_oeste"]
        elif "zona norte" in address_lower:
            return self.freight_rules["zona_norte"]
        elif "zona sul" in address_lower:
            return self.freight_rules["zona_sul"]
        else:
            return self.freight_rules["default"]

    def calculate_rental_price(self, selected_toys, num_days, address=""): # Added address parameter
        total_price = 0.0
        for toy_name in selected_toys:
            toy_name_lower = toy_name.lower()
            if toy_name_lower in self.toys:
                if num_days == 1:
                    total_price += self.toys[toy_name_lower]["price_day"]
                elif num_days == 2 and self.toys[toy_name_lower]["price_2_days"] is not None:
                    total_price += self.toys[toy_name_lower]["price_2_days"]
                elif num_days > 2:
                    # For more than 2 days, apply daily rate for each day, with a special discount logic
                    # For now, let's assume daily rate for each day for simplicity, user can define discount later
                    total_price += self.toys[toy_name_lower]["price_day"] * num_days
                else:
                    # Fallback for invalid num_days or if 2-day price not available
                    total_price += self.toys[toy_name_lower]["price_day"] * num_days
            else:
                return f"Brinquedo '{toy_name}' não encontrado."
        
        freight_cost = self.calculate_freight(address) # Calculate freight based on address

        final_price = total_price + freight_cost
        signal_payment = final_price * 0.5

        return {
            "total_price": final_price,
            "signal_payment": signal_payment,
            "details": f"Total para {num_days} dia(s) (incluindo frete de R$ {freight_cost:.2f}): R$ {final_price:.2f}. Sinal de 50%: R$ {signal_payment:.2f}."
        }

    def check_availability(self, toy_name, start_date_str, end_date_str):
        if not self.sheet:
            return "Erro: Planilha não conectada. Por favor, configure a conexão primeiro."

        try:
            start_date = datetime.strptime(start_date_str, '%d/%m/%Y')
            end_date = datetime.strptime(end_date_str, '%d/%m/%Y')
        except ValueError:
            return "Formato de data inválido. Use DD/MM/AAAA."

        records = self.sheet.get_all_records()
        for record in records:
            booked_toy = record.get('Brinquedo')
            booked_start_str = record.get('Data Início')
            booked_end_str = record.get('Data Fim')

            if booked_toy and booked_start_str and booked_end_str:
                try:
                    booked_start = datetime.strptime(booked_start_str, '%d/%m/%Y')
                    booked_end = datetime.strptime(booked_end_str, '%d/%m/%Y')

                    if booked_toy.lower() == toy_name.lower():
                        # Check for overlap
                        if not (end_date < booked_start or start_date > booked_end):
                            return False # Not available
                except ValueError:
                    continue # Skip invalid date formats in sheet
        return True # Available

    def book_toy(self, toy_name, start_date_str, end_date_str, client_name, client_phone, address):
        if not self.sheet:
            return "Erro: Planilha não conectada. Por favor, configure a conexão primeiro."

        if not self.check_availability(toy_name, start_date_str, end_date_str):
            return f"O brinquedo {toy_name} não está disponível entre {start_date_str} e {end_date_str}."

        # Generate a simple booking ID
        last_row = len(self.sheet.get_all_values()) + 1
        booking_id = f"BKG-{last_row:04d}"

        new_booking = [
            booking_id,
            start_date_str,
            end_date_str,
            toy_name,
            client_name,
            client_phone,
            address,
            "Pendente" # Initial status
        ]
        self.sheet.append_row(new_booking)
        return f"Agendamento para {toy_name} de {start_date_str} a {end_date_str} registrado com sucesso! ID: {booking_id}. Status: Pendente."

# Example Usage (for testing purposes)
if __name__ == "__main__":
    # IMPORTANT: Replace with your actual Google Sheet URL and credentials path
    # bot = RentalBot(google_sheet_url="YOUR_GOOGLE_SHEET_URL")
    # bot.connect_to_sheet(credentials_path='path/to/your/service_account.json')

    bot = RentalBot()
    print(bot.get_available_toys())

    # Example calculation
    selected = ["Pula-Pula Pequeno", "Mesa de Pebolim"]
    days = 1
    price_info = bot.calculate_rental_price(selected, days, "Rua das Flores, Zona Leste")
    print(price_info)

    selected_2_days = ["Pula-Pula Pequeno"]
    days_2 = 2
    price_info_2 = bot.calculate_rental_price(selected_2_days, days_2, "Av. Principal, Zona Oeste")
    print(price_info_2)

    selected_3_days = ["Piscina de Bolinhas"]
    days_3 = 3
    price_info_3 = bot.calculate_rental_price(selected_3_days, days_3, "Centro, Zona Norte")
    print(price_info_3)

    # Example availability check and booking (requires sheet connection)
    # if bot.sheet:
    #     print(bot.check_availability("Pula-Pula Grande", "15/03/2026", "16/03/2026"))
    #     print(bot.book_toy("Pula-Pula Grande", "25/03/2026", "25/03/2026", "Carlos Souza", "(11) 99887-7665", "Rua Nova, 50, Zona Sul"))
