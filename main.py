import os, json, time, requests
import google.generativeai as genai
import telebot
from keep_alive import keep_alive

# Load API Keys
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # Ganti dari OPENAI_API_KEY
PEXELS_KEY = os.getenv("PEXELS_KEY")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

bot = telebot.TeleBot(BOT_TOKEN)
keep_alive()

def analyze_products():
    prompt = """Return ONLY a JSON array of 3 trending tech products under $50. 
    Each product must have this exact format:
    {
        "name": "product name",
        "price": "$XX",
        "category": "tech category",
        "hook": "catchy hook",
        "selling_points": ["point 1", "point 2"]
    }
    
    Do not include any explanation, just the JSON array."""
    
    response = model.generate_content(prompt)
    # Extract JSON from response
    text = response.text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    
    return json.loads(text)

def generate_metadata(p):
    prompt = f"""For YouTube Shorts about '{p['name']}' (priced at {p['price']}'), 
    return ONLY a JSON object with this exact format:
    {{
        "title": "catchy title under 60 characters",
        "description": "100 characters description with affiliate disclaimer",
        "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
        "hashtags": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5"]
    }}
    
    Do not include any explanation, just the JSON."""
    
    response = model.generate_content(prompt)
    text = response.text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    
    return json.loads(text)

def download_footage(query, path):
    headers = {"Authorization": PEXELS_KEY}
    res = requests.get(f"https://api.pexels.com/videos/search?query={query}&per_page=1", headers=headers)
    videos = res.json().get("videos", [])
    if not videos: 
        return False
    url = videos[0]["video_files"][0]["link"]
    r = requests.get(url, stream=True)
    with open(path, "wb") as f:
        for chunk in r.iter_content(1024): 
            f.write(chunk)
    return os.path.getsize(path) > 1000

@bot.message_handler(commands=["start"])
def start(m):
    bot.reply_to(m, "🤖 Tech Affiliate Bot Ready (Powered by Gemini AI)\n\n/send = Generate 3 products + assets\n/status = Check system")

@bot.message_handler(commands=["send"])
def run_bot(m):
    bot.reply_to(m, "⏳ Generating with Gemini AI... (tunggu 2-3 menit)")
    try:
        products = analyze_products()
        for i, p in enumerate(products):
            p.update(generate_metadata(p))
            clip = f"/tmp/clip_{i}.mp4"
            if download_footage(p["category"], clip):
                bot.send_document(m.chat.id, open(clip,"rb"), caption=f"🎬 {p['title']}\n📲 Import ke CapCut + paste script!")
            
            txt = f"""🎙️ SCRIPT {i+1}:
{p['hook']}
• {p['selling_points'][0]}
• {p['selling_points'][1]}

🔗 CTA: Link in bio!

📋 META:
Title: {p['title']}
Desc: {p['description']}
Tags: {', '.join(p['tags'])}
Hashtags: {' '.join(p['hashtags'])}"""
            
            bot.send_message(m.chat.id, txt)
            time.sleep(2)
        
        bot.reply_to(m, "✅ Done! Siap edit & upload.")
    
    except Exception as e:
        bot.reply_to(m, f"❌ Error: {str(e)}")

@bot.message_handler(commands=["status"])
def status(m):
    bot.reply_to(m, "🟢 Online | 💾 Gemini AI | 🌐 Connected")

if __name__ == "__main__":
    print("🤖 Bot starting with Gemini AI...")
    bot.infinity_polling()
