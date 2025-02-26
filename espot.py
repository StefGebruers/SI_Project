import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta

# Hulpfunctie om het uur te vergelijken en te bepalen of het vandaag of morgen is
def is_today_or_tomorrow(time_str):
    # Huidige datum en morgen berekenen
    today = datetime.today()
    tomorrow = today + timedelta(days=1)
    
    # Tijd omzetten naar een datetime-object
    time = datetime.strptime(time_str, "%d/%m/%Y %H:%M:%S")
    
    # Controleren of het vandaag of morgen is
    if time.date() == today.date():
        return 'today'
    elif time.date() == tomorrow.date():
        return 'tomorrow'
    else:
        return None

# URL van de pagina die je wilt scrapen
url = "https://my.elexys.be/MarketInformation/SpotBelpex.aspx"

# Verzoek om de inhoud van de pagina op te halen
response = requests.get(url)
response.raise_for_status()  # Zorg ervoor dat de aanvraag succesvol is

# BeautifulSoup gebruiken om de HTML te parsen
soup = BeautifulSoup(response.text, 'html.parser')

# Zoek de tabel die de prijzen bevat
rows = soup.find_all('tr', class_='dxgvDataRow_Office2010Blue')

# Lijsten voor prijzen van vandaag en morgen
prices_today = []
prices_tomorrow = []

# Itereer door de rijen in de tabel
for row in rows:
    # Haal de datum en prijs op
    cols = row.find_all('td')
    if len(cols) >= 2:
        time = cols[0].get_text(strip=True)
        price = cols[1].get_text(strip=True).replace('€', '').strip()
        
        # Bepaal of de tijd vandaag of morgen is
        period = is_today_or_tomorrow(time)
        
        if period == 'today':
            prices_today.append({
                'time': time,
                'price': price
            })
        elif period == 'tomorrow':
            prices_tomorrow.append({
                'time': time,
                'price': price
            })

# Variabelen voor prijzen van vandaag en morgen
today_prices = prices_today
tomorrow_prices = prices_tomorrow

# Print de prijzen van vandaag en morgen
print("Prijzen vandaag:", today_prices)
print("Prijzen morgen:", tomorrow_prices)

# Sla de gegevens op in een JSON-bestand
with open('prices_per_hour.json', 'w') as json_file:
    json.dump({
        'today': today_prices,
        'tomorrow': tomorrow_prices
    }, json_file, indent=4)

print("Gegevens zijn opgeslagen in 'prices_per_hour.json'")
