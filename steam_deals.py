import os
import time
import requests

WEBHOOK_URL = os.environ.get(
    'WEBHOOK_URL',
    'YOUR_DISCORD_WEBHOOK_URL_HERE'  # Substitua pelo seu webhook do Discord
)

# IDs oficiais de conteúdo adulto da Valve
ADULT_CONTENT_DESCRIPTOR_IDS = {2, 4}  # 2: Nudez/Sexual, 4: Adult Only explícito


def get_steam_deals():
    headers = {
        # Evita herdar permissões de visualização adulta
        "Cookie": "wants_mature_content=0; birthtime=1072915201;"
    }
    response = requests.get(
        "https://store.steampowered.com/api/featured/",
        headers=headers,
        timeout=10,
    )
    return response.json()


def is_mature_or_adult(app_id):
    """Consulta a API de detalhes do app para verificar restrições etárias e descritores."""
    try:
        url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&filters=basic,ratings,content_descriptors"
        res = requests.get(url, timeout=5).json()

        if not res or not res.get(str(app_id), {}).get("success"):
            return False

        data = res[str(app_id)]["data"]

        # 1. Checa idade mínima registrada (ex: 18)
        required_age = data.get("required_age", 0)
        if isinstance(required_age, str) and required_age.isdigit():
            required_age = int(required_age)
        if required_age >= 18:
            return True

        # 2. Checa descritores de conteúdo adulto oficiais da Steam
        descriptors = (
            data.get("content_descriptors", {}).get("ids", [])
        )
        if any(desc_id in ADULT_CONTENT_DESCRIPTOR_IDS for desc_id in descriptors):
            return True

    except Exception as e:
        print(f"Erro ao validar appid {app_id}: {e}")

    return False


def is_adult_content_fallback(deal):
    """Filtro textual leve apenas como redundância secundária."""
    adult_keywords = {
        "hentai",
        "erotic",
        "sexual",
        "xxx",
        "porn",
        "ecchi",
        "fetish",
        "lewd",
    }
    name = deal.get("name", "").lower()
    return any(kw in name for kw in adult_keywords)


def send_to_discord(data):
    all_deals = []
    for key in ("large_capsules", "featured_win", "featured_mac", "featured_linux"):
        if key in data:
            all_deals.extend(data[key])

    seen_ids = set()
    unique_deals = []
    for deal in all_deals:
        appid = deal.get("id")
        if appid and appid not in seen_ids:
            seen_ids.add(appid)
            unique_deals.append(deal)

    safe_deals = []
    for deal in unique_deals:
        appid = deal.get("id")

        # Primeiro teste rápido por texto no título
        if is_adult_content_fallback(deal):
            continue

        # Validação profunda via descritores da Steam (apenas até preencher a lista)
        if is_mature_or_adult(appid):
            continue

        safe_deals.append(deal)
        if len(safe_deals) == 10:  # Discord suporta no máximo 10 embeds
            break

    print(f"Total avaliados: {len(unique_deals)} | Selecionados: {len(safe_deals)}")

    embeds = []
    for i, deal in enumerate(safe_deals, 1):
        name = deal.get("name", "Unknown")
        header_image = deal.get("header_image", "")

        final_price_raw = deal.get("final_price")
        original_price_raw = deal.get("original_price")

        final_price = float(final_price_raw) / 100 if final_price_raw else 0
        original_price = float(original_price_raw) / 100 if original_price_raw else 0

        discount = 0
        if original_price > 0 and final_price < original_price:
            discount = int(((original_price - final_price) / original_price) * 100)

        price_text = (
            f"💰 **R$ {final_price:.2f}** ~~R$ {original_price:.2f}~~\n🏷️ **-{discount}% OFF**"
            if discount > 0
            else f"💰 **R$ {final_price:.2f}**"
        )

        embeds.append(
            {
                "title": f"{i}. 🎮 {name}",
                "url": f"https://store.steampowered.com/app/{deal.get('id')}",
                "description": price_text,
                "color": 0x1B2838,
                "image": {"url": header_image},
                "footer": {
                    "text": f"Promoção {i} de {len(safe_deals)}",
                    "icon_url": "https://github.com/DoctorSolo/web-hook-steam-deals-discord/blob/main/.github/assets/social.png?raw=true",
                },
            }
        )

    if not embeds:
        embeds = [{
            "title": "🎮 Promoções da Steam",
            "description": "Nenhuma promoção encontrada no momento.",
            "color": 0x1B2838,
        }]

    if WEBHOOK_URL:
        requests.post(WEBHOOK_URL, json={"embeds": embeds}, timeout=10)
        print(f"Enviadas {len(embeds)} promoções com imagens!")


if __name__ == "__main__":
    deals_data = get_steam_deals()
    send_to_discord(deals_data)