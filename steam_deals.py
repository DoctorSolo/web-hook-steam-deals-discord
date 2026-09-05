import requests
import os
from datetime import datetime

WEBHOOK_URL = os.environ.get('WEBHOOK_URL', '')

def get_steam_deals():
    response = requests.get(
        "https://store.steampowered.com/api/featured/"
    )
    return response.json()

def send_to_discord(data):
    # Combina todas as seções de promoções
    all_deals = []
    
    if 'large_capsules' in data:
        all_deals.extend(data['large_capsules'])
    
    if 'featured_win' in data:
        all_deals.extend(data['featured_win'])
    
    if 'featured_mac' in data:
        all_deals.extend(data['featured_mac'])
    
    if 'featured_linux' in data:
        all_deals.extend(data['featured_linux'])
    
    # Remove duplicatas por appid
    seen_ids = set()
    unique_deals = []
    for deal in all_deals:
        appid = deal.get('id')
        if appid and appid not in seen_ids:
            seen_ids.add(appid)
            unique_deals.append(deal)
    
    # Constrói a descrição com todas as promoções (mais espaçado)
    description = ""
    
    for i, deal in enumerate(unique_deals[:10], 1):  # Limita a 10 para caber melhor
        name = deal.get('name', 'Unknown')
        header_image = deal.get('header_image', '')
        
        # Tratamento seguro para preços
        final_price_raw = deal.get('final_price')
        original_price_raw = deal.get('original_price')
        
        final_price = float(final_price_raw) / 100 if final_price_raw else 0
        original_price = float(original_price_raw) / 100 if original_price_raw else 0
        
        # Calcula desconto
        discount = 0
        if original_price > 0 and final_price < original_price:
            discount = int(((original_price - final_price) / original_price) * 100)
        
        # Formata o item com mais espaçamento
        description += f"━━━━━━━━━━━━━━━━━━━━\n\n"
        description += f"**{i}. 🎮 {name}**\n\n"
        
        if header_image:
            description += f"[📷 Ver Imagem]({header_image})\n\n"
        
        if discount > 0:
            description += f"💰 **R$ {final_price:.2f}** ~~R$ {original_price:.2f}~~\n"
            description += f"🏷️ **-{discount}% OFF**\n\n"
        else:
            description += f"💰 **R$ {final_price:.2f}**\n\n"
        
        description += f"[🔗 Acessar na Steam](https://store.steampowered.com/app/{deal.get('id')})\n\n"
    
    # Se não houver promoções
    if not description:
        description = "Nenhuma promoção encontrada no momento. 😔"
    
    # Cria um único embed
    embed = {
        "title": "🎮 Promoções da Steam",
        "description": description,
        "color": 0x1b2838,
        "thumbnail": {
            "url": "https://store.steampowered.com/public/shared/images/responsive/logo_steam.svg"
        },
        "footer": {
            "text": f"Atualizado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
            "icon_url": "https://store.steampowered.com/favicon.ico"
        }
    }
    
    payload = {"embeds": [embed]}
    
    requests.post(WEBHOOK_URL, json=payload)
    print(f"Enviadas {len(unique_deals[:10])} promoções!")

if __name__ == "__main__":
    data = get_steam_deals()
    send_to_discord(data)