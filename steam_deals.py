import requests
import os
from datetime import datetime

WEBHOOK_URL = os.environ.get('WEBHOOK_URL', 'your url here')

def get_steam_deals():
    response = requests.get(
        "https://store.steampowered.com/api/featured/"
    )
    return response.json()

def is_adult_content(deal):
    """Verifica se o jogo tem conteúdo adulto"""
    # Verifica tags e descrições comuns de conteúdo +18
    adult_keywords = [
        'adult', 'nsfw', 'hentai', 'erotic', 'sexual', 
        'nudity', 'mature', 'xxx', 'porn', 'ecchi',
        'sex', 'femboy', 'futa', 'yaoi', 'yuri',
        'fetish', 'bdsm', 'incest',
    ]
    
    name = deal.get('name', '').lower()
    description = deal.get('description', '').lower() if deal.get('description') else ''
    
    # Verifica keywords no nome e descrição
    for keyword in adult_keywords:
        if keyword in name or keyword in description:
            return True
    
    return False

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
    
    # Filtra jogos +18
    safe_deals = [deal for deal in unique_deals if not is_adult_content(deal)]
    
    print(f"Total: {len(unique_deals)} | Após filtro +18: {len(safe_deals)}")
    
    # Constrói a descrição com todas as promoções
    description = ""
    
    for i, deal in enumerate(safe_deals[:10], 1):
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
            "text": f"Atualizado em {datetime.now().strftime('%d/%m/%Y às %H:%M')} | Filtro +18 ativo ✅",
            "icon_url": "https://store.steampowered.com/favicon.ico"
        }
    }
    
    payload = {"embeds": [embed]}
    
    requests.post(WEBHOOK_URL, json=payload)
    print(f"Enviadas {len(safe_deals[:10])} promoções (sem +18)!")

if __name__ == "__main__":
    data = get_steam_deals()
    send_to_discord(data)