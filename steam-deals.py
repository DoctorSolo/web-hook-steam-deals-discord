import requests
import os
from datetime import datetime

WEBHOOK_URL = os.environ['WEBHOOK_URL']

def get_steam_deals():
    response = requests.get(
        "https://store.steampowered.com/api/featured/"
    )
    return response.json()

def send_to_discord(deals):
    embed = {
        "embeds": [{
            "title": "🎮 Novas Promoções na Steam",
            "description": "Confira as ofertas!",
            "color": 0x1b2838,
            "timestamp": datetime.utcnow().isoformat()
        }]
    }
    
    requests.post(WEBHOOK_URL, json=embed)

if __name__ == "__main__":
    deals = get_steam_deals()
    send_to_discord(deals)
    print("Notificação enviada!")