import urllib.request
import re
import json
import time

BASE_URL = "https://www.loja3d.com.br"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9",
}

def fetch_page(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="ignore")

def extract_products(html):
    products = []
    # Split HTML by product block boundaries
    parts = re.split(r'(?=<div class="product-block[^"]*"[^>]*data-product-box=")', html)
    for block in parts[1:]:  # skip first (pre-products content)
        id_match = re.search(r'data-product-box="(\d+)"', block)
        if not id_match:
            continue
        product_id = id_match.group(1)
        # Trim block to a reasonable size to avoid bleeding into next product
        block = block[:5000]
        # Product URL
        url_match = re.search(r'href="(/produto/[^"]+)"', block)
        product_url = BASE_URL + url_match.group(1) if url_match else None

        # Product name
        name_match = re.search(r'<h3 class="name">.*?<a[^>]+>([^<]+)</a>', block, re.DOTALL)
        name = name_match.group(1).strip() if name_match else None

        # Image URL - try srcset (above fold) then data-srcset (lazy-loaded)
        img_match = re.search(r'<img[^>]+(?:data-srcset|srcset)="([^"]+)"', block)
        image_url = None
        if img_match:
            srcset = img_match.group(1)
            # Extract original (no resize prefix) or largest available
            orig = re.search(r'(//cdn\.vnda\.com\.br/loja3d/[^\s]+)\s+2000w', srcset)
            if orig:
                image_url = "https:" + orig.group(1)
            else:
                # fallback: first URL in srcset
                first = re.search(r'(https://[^\s]+)', srcset)
                if first:
                    image_url = first.group(1)

        # Price: try to find actual price, may be pre-sale
        price_match = re.search(r'<strong[^>]*class="[^"]*price[^"]*"[^>]*>([^<]+)</strong>', block)
        price = price_match.group(1).strip() if price_match else None

        # Pre-sale flag
        is_presale = bool(re.search(r'data-pre-sale="' + product_id + '"', block))

        products.append({
            "id": product_id,
            "name": name,
            "price": price,
            "is_presale": is_presale,
            "product_url": product_url,
            "image_url": image_url,
        })
    return products

def scrape_all():
    all_products = []

    print("Buscando página 1...")
    html = fetch_page(f"{BASE_URL}/filamentos")

    # Get total pages
    total_match = re.search(r'totalPages:\s*(\d+)', html)
    total_pages = int(total_match.group(1)) if total_match else 1
    print(f"Total de páginas: {total_pages}")

    products = extract_products(html)
    print(f"  -> {len(products)} produtos encontrados")
    all_products.extend(products)

    for page in range(2, total_pages + 1):
        print(f"Buscando página {page}/{total_pages}...")
        time.sleep(0.5)  # polite delay
        html = fetch_page(f"{BASE_URL}/filamentos?page={page}")
        products = extract_products(html)
        print(f"  -> {len(products)} produtos encontrados")
        all_products.extend(products)

    return all_products

if __name__ == "__main__":
    produtos = scrape_all()

    output = {
        "total": len(produtos),
        "source": "https://www.loja3d.com.br/filamentos",
        "scraped_at": "2026-05-22",
        "products": produtos
    }

    with open("/root/filamentos/filamentos.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nTotal de produtos salvos: {len(produtos)}")
    print("Arquivo salvo em: /root/filamentos/filamentos.json")
