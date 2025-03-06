import os
from entsoe import EntsoePandasClient
import pandas as pd
import matplotlib

matplotlib.use('Agg')  # Zorgt ervoor dat het werkt in een headless omgeving
import matplotlib.pyplot as plt
from jinja2 import Environment, FileSystemLoader

#API-sleutel
client = EntsoePandasClient(api_key="d23a1866-678d-4c7c-a38e-ccf32827ca32")

# Huidige datum en tijdzone
start = pd.Timestamp.now(tz='Europe/Brussels').normalize()
end = start + pd.Timedelta(days=2)

country_code = 'BE'  # België

# Functie om bestanden te verwijderen
def verwijder_bestand(bestandsnaam):
    if os.path.exists(bestandsnaam):
        os.remove(bestandsnaam)

# Oude bestanden verwijderen
verwijder_bestand("energieprijzen_vandaag.png")
verwijder_bestand("energieprijzen_morgen.png")

try:
    # Day-ahead prijzen ophalen
    day_ahead_prices = client.query_day_ahead_prices(country_code, start=start, end=end)
    print("Opgehaalde prijzen vandaag:")
    print(day_ahead_prices)

    # Vandaag en morgen bepalen
    vandaag = start
    morgen = start + pd.Timedelta(days=1)

    # Prijzen filteren per dag
    prijzen_vandaag = day_ahead_prices[vandaag:vandaag + pd.Timedelta(days=1)]
    prijzen_morgen = day_ahead_prices[morgen:morgen + pd.Timedelta(days=1)]

    # Controleren of er data is voor vandaag
    if prijzen_vandaag.empty:
        raise ValueError("Geen data beschikbaar voor vandaag.")

    # Functie om de beste en slechtste momenten te bepalen
    def analyseer_prijzen(prijzen):
        gesorteerde_prijzen = prijzen.sort_values()
        beste_uren = gesorteerde_prijzen.index[:3]  # Goedkoopste 3 uren
        duurste_uren = gesorteerde_prijzen.index[-3:]  # Duurste 3 uren
        return beste_uren, duurste_uren

    # Analyseer prijzen voor vandaag
    beste_uren_vandaag, duurste_uren_vandaag = analyseer_prijzen(prijzen_vandaag)

    # Analyseer prijzen voor morgen (indien beschikbaar)
    if prijzen_morgen.empty:
        beste_uren_morgen, duurste_uren_morgen = [], []
    else:
        beste_uren_morgen, duurste_uren_morgen = analyseer_prijzen(prijzen_morgen)

    # Converteer de tijden naar strings
    beste_uren_vandaag_str = ", ".join(f"{t.hour}u (€{prijzen_vandaag[t]:.2f})" for t in beste_uren_vandaag)
    duurste_uren_vandaag_str = ", ".join(f"{t.hour}u (€{prijzen_vandaag[t]:.2f})" for t in duurste_uren_vandaag)

    if prijzen_morgen.empty:
        beste_uren_morgen_str = "Nog niet beschikbaar"
        duurste_uren_morgen_str = "Nog niet beschikbaar"
    else:
        beste_uren_morgen_str = ", ".join(f"{t.hour}u (€{prijzen_morgen[t]:.2f})" for t in beste_uren_morgen)
        duurste_uren_morgen_str = ", ".join(f"{t.hour}u (€{prijzen_morgen[t]:.2f})" for t in duurste_uren_morgen)

    # Grafieken maken
    def plot_prijzen(prijzen, titel, bestandsnaam):
        plt.figure(figsize=(12, 6))
        plt.plot(prijzen.index, prijzen.values, marker='o', linestyle='-', color='blue')
        plt.xticks(prijzen.index, [t.strftime('%H:%M') for t in prijzen.index], rotation=45)
        plt.xlabel('Tijd')
        plt.ylabel('Energieprijs (€ per MWh)')
        plt.title(titel)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.savefig(bestandsnaam)

    # Grafiek voor vandaag
    plot_prijzen(prijzen_vandaag, "Energieprijzen Vandaag", "energieprijzen_vandaag.png")
    print("Grafiek voor vandaag opgeslagen als 'energieprijzen_vandaag.png'")

    # Grafiek voor morgen (indien beschikbaar)
    if not prijzen_morgen.empty:
        plot_prijzen(prijzen_morgen, "Energieprijzen Morgen", "energieprijzen_morgen.png")
        print("Grafiek voor morgen opgeslagen als 'energieprijzen_morgen.png'")

    # HTML genereren met Jinja2
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template("template.html")

    html_output = template.render(
        beste_uren_vandaag=beste_uren_vandaag_str,
        duurste_uren_vandaag=duurste_uren_vandaag_str,
        beste_uren_morgen=beste_uren_morgen_str,
        duurste_uren_morgen=duurste_uren_morgen_str
    )

    # HTML-bestand opslaan
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_output)

    print("✅ HTML-pagina gegenereerd als 'index.html'.")

except Exception as e:
    print(f"⚠️ Er is een fout opgetreden: {e}")