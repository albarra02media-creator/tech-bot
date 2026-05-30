import os, json, time, requests
from openai import OpenAI
import telebot
from keep_alive import keep_alive

# Load API Keys dari Render Environment Variables
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
PEXELS_KEY = os.getenv("PEXELS_KEY")

client = OpenAI(api_key=OPENAI_KEY)
bot = telebot.TeleBot(BOT_TOKEN)

# Jalankan server keep-alive biar bot tidak tidur
keep_alive()

def analyze_products():
    prompt = "Return ONLY a JSON array of 3 trending tech products under $50. Each: {name: str, price: str, category: str, hook: str, selling_points: [str]}"
    res = client.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role":"user","content":prompt}])
    return json.loads(res.choices[0].message.content)

def generate_metadata(p):
    prompt = f"For YouTube Shorts about '{p['name']}' (${p['price']}'), return JSON: {{title: <60 chars, description: 100 chars + affiliate disclaimer, tags: [5], hashtags: [5]}}"
    res = client.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role":"user","content":prompt}])
    return json.loads(res.choices[0].message.content)

def download_footage(query, path):
    headers = {"Authorization": PEXELS_KEY}
    res = requests.get(f"https://api.pexels.com/videos/search?query={query}&per_page=1", headers=headers)
    videos = res.json().get("videos", [])
    if not videos: return False
    url = videos[0]["video_files"][0]["link"]
    r = requests.get(url, stream=True)
    with open(path, "wb") as f:
        for chunk in r.iter_content(1024): f.write(chunk)
    return os.path.getsize(path) > 1000

@bot.message_handler(commands=["start"])
def start(m):
    bot.reply_to(m, "🤖 Tech Affiliate Bot Ready\n\n/send = Generate 3 products + assets\n/status = Check system")

@bot.message_handler(commands=["send"])
def run_bot(m):
    bot.reply_to(m, "⏳ Generating... (tunggu 2-3 menit)")
    try:
        products = analyze_products()
        for i, p in enumerate(products):
            p.update(generate_metadata(p))
            clip = f"/tmp/clip_{i}.mp4"
            if download_footage(p["category"], clip):
                bot.send_document(m.chat.id, open(clip,"rb"), caption=f" {p['title']}\n📲 Import ke CapCut + paste script!")
            txt = f"🎙️ SCRIPT {i+1}:\n{p['hook']}\n• {p['selling_points'][0]}\n• {p['selling_points'][1]}\n\n CTA: Link in bio!\n\n META:\nTitle: {p['title']}\nDesc: {p['description']}\nTags: {', '.join(p['tags'])}\nHashtags: {' '.join(p['hashtags'])}"
            bot.send_message(m.chat.id, txt)
            time.sleep(2)
        bot.reply_to(m, "✅ Done! Siap edit & upload.")
    except Exception as e:
        bot.reply_to(m, f"❌ Error: {e}")

@bot.message_handler(commands=["status"])
def status(m):
    bot.reply_to(m, " Online | 💾 Optimized | 🌐 Connected")

if __name__ == "__main__":
    print("🤖 Bot starting...")
    bot.infinity_polling()