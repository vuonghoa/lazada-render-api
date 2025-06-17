from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import re

app = Flask(__name__)

@app.route("/")
def home():
    return {"message": "✅ Lazada Playwright API is running on Render."}

@app.route("/lazada")
def get_lazada_info():
    url = request.args.get("url")
    token = request.args.get("token")
    LAZADA_TOKEN = "vntech68_lazada_secret"

    if not url:
        return jsonify({"error": "Thiếu URL", "success": False}), 400
    if token != LAZADA_TOKEN:
        return jsonify({"error": "Unauthorized", "success": False}), 403

    browser = None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            page.goto(url, timeout=30000)
            page.wait_for_timeout(3000)

            # Lấy tiêu đề
            title = page.title().strip()

            # Lấy ảnh đại diện
            image = page.locator('meta[property="og:image"]').get_attribute("content") or ""

            # Tìm các span chứa giá
            spans = page.locator("span:has-text('₫')").all_inner_texts()
            seen = set()
            prices = []
            for s in spans:
                cleaned = re.sub(r"[^\d]", "", s)
                if cleaned and cleaned not in seen:
                    seen.add(cleaned)
                    prices.append(cleaned)

            def parse_price(text):
                return int(re.sub(r"[^\d]", "", text))

            price_val = parse_price(prices[0]) if len(prices) >= 1 else 0
            list_val = parse_price(prices[1]) if len(prices) >= 2 else price_val

            discount = 0
            if list_val > price_val > 0:
                discount = round(100 - (price_val / list_val * 100))

            return jsonify({
                "title": title,
                "image": image,
                "price": f"{price_val:,}₫" if price_val else "N/A",
                "original_price": f"{list_val:,}₫" if list_val else "N/A",
                "discount_percent": discount,
                "success": True
            })
    except Exception as e:
        return jsonify({"error": str(e), "success": False})
    finally:
        if browser:
            browser.close()
