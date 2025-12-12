# Deutsches Wörterbuch-Bot – Einfach & Test (nur /start + 5 local words, Debug full)
TOKEN = '8224460982:AAEPMMNfWxFfzqPTcqUCxKI0zJr8IP-dzG4'  # Ersetze mit neuem Token wenn nötig!

import telebot
from telebot import types
import requests
from bs4 import BeautifulSoup
from flask import Flask, request
import os
import traceback

bot = telebot.TeleBot(TOKEN)
print("Bot initialized – Token OK?")

# Einfaches local_dict (nur 5 Testwörter – erweitern später)
local_dict = {
    "haus": {"type": "Nomen", "article": "das", "definition": "Gebäude zum Wohnen.", "synonyms": "Wohnung, Gebäude", "examples": {"beginner": "Das Haus ist groß.", "medium": "Ich wohne im Haus.", "advanced": "Historisches Haus."}, "grammar": "Neutrum. Plural: Häuser."},
    "essen": {"type": "Verb", "article": "", "definition": "Nahrung aufnehmen.", "synonyms": "Speisen, verspeisen", "examples": {"beginner": "Ich esse.", "medium": "Wir essen zusammen.", "advanced": "Ich esse gesund."}, "grammar": "Starkes Verb. Präsens: ich esse, du isst."},
    "groß": {"type": "Adjektiv", "article": "", "definition": "Hohe Größe oder Bedeutung.", "synonyms": "Riesig, enorm", "examples": {"beginner": "Großes Haus.", "medium": "Großer Erfolg.", "advanced": "Große Ideen."}, "grammar": "Adjektiv. Komparativ: größer."},
    "kommen": {"type": "Verb", "article": "", "definition": "Sich nähern oder ankommen.", "synonyms": "Ankommen, eintreffen", "examples": {"beginner": "Ich komme.", "medium": "Komm her.", "advanced": "Der Zug kommt."}, "grammar": "Starkes Verb. Präsens: ich komme, du kommst."},
    "gut": {"type": "Adjektiv", "article": "", "definition": "Hohe Qualität oder positiv.", "synonyms": "Ausgezeichnet, positiv", "examples": {"beginner": "Gut gemacht!", "medium": "Guter Rat.", "advanced": "Gute Absichten."}, "grammar": "Adjektiv. Komparativ: besser."}
}

user_levels = {}
user_history = {}

# Einfacher Scrape-Fallback (nur PONS, no multi for test)
def get_definition(word):
    print(f"Debug: Scrape for '{word}'")
    try:
        url = f"https://de.pons.com/uebersetzung/deutsch/{word}"
        headers = {'User-Agent': 'Mozilla/5.0 (Test bot)'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            def_text = soup.find('p').get_text().strip()[:200] if soup.find('p') else 'Definition from PONS.'
            print(f"Debug: PONS success for '{word}'")
            return {'definition': def_text, 'source': 'PONS'}
        else:
            print(f"Debug: PONS status {response.status_code} for '{word}'")
            return {'definition': f'Keine Definition. Link: {url}', 'source': 'Fallback'}
    except Exception as e:
        print(f"Debug: Scrape error for '{word}': {str(e)}")
        return {'definition': f'Fehler: {str(e)}. Suche online.', 'source': 'Error'}

def get_local(word):
    if word in local_dict:
        print(f"Debug: Local found for '{word}'")
        return local_dict[word]
    print(f"Debug: No local for '{word}'")
    return None

# /start – Einfach & mit try/except
@bot.message_handler(commands=['start'])
def start_message(message):
    print(f"Debug: /start called by user {message.from_user.id} – Name: {message.from_user.first_name}")
    try:
        bot.reply_to(message, "Hallo! Deutsches Wörterbuch-Bot gestartet! 🚀\n\nBefehle:\n/level beginner|medium|advanced – Niveau setzen\n/local – Lokale Wörter (5 Test)\n/history – Verlauf\n\nWort eingeben, z.B. 'haus' oder 'kommen'.\nQuelle: Local + PONS.de\n\n/grammatik für Infos.")
        print("Debug: /start reply sent successfully!")
    except Exception as e:
        print(f"Debug: /start exception: {str(e)}\n{traceback.format_exc()}")
        # Fallback reply
        bot.reply_to(message, f"Hallo! Bot läuft, aber Fehler: {str(e)}. /start erneut.")

# /level
@bot.message_handler(commands=['level'])
def set_level(message):
    print("Debug: /level called")
    parts = message.text.split()
    level = parts[1].lower() if len(parts) > 1 else 'medium'
    if level in ['beginner', 'medium', 'advanced']:
        user_levels[message.from_user.id] = level
        bot.reply_to(message, f"Niveau {level} gesetzt!")
        print(f"Debug: Level set to {level}")
    else:
        bot.reply_to(message, "Verfügbare Niveaus: beginner, medium, advanced")

# /local
@bot.message_handler(commands=['local'])
def local_mode(message):
    print("Debug: /local called")
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    for key in local_dict:
        markup.row(types.KeyboardButton(key))
    bot.reply_to(message, "Lokale Wörter (5 Test): Tippe ein Wort!", reply_markup=markup)

# /history
@bot.message_handler(commands=['history'])
def show_history(message):
    print("Debug: /history called")
    hist = user_history.get(message.from_user.id, [])
    if hist:
        bot.reply_to(message, "Letzte Wörter:\n" + "\n".join(hist[-5:]))
    else:
        bot.reply_to(message, "Noch keine Wörter gesucht!")

# Haupt-Handler
@bot.message_handler(func=lambda m: True)
def handle_message(message):
    word = message.text.strip().lower()
    user_id = message.from_user.id
    print(f"Debug: Message '{word}' from {user_id}")
    if len(word) < 2 or word.startswith('/'):
        return

    # History
    if user_id not in user_history:
        user_history[user_id] = []
    user_history[user_id].append(word)
    if len(user_history[user_id]) > 10:
        user_history[user_id] = user_history[user_id][-10:]

    try:
        level_data = get_local(word)
        if level_data:
            data = level_data
            level = user_levels.get(user_id, 'medium')
            example = data['examples'].get(level, data['examples']['medium'])
            response = f"📖 **{word.capitalize()}** ({data['type']}, Local)\n\n📰 Artikel: {data['article']} {word}\n\n📚 Definition: {data['definition']}\n\n🔄 Synonyme: {data['synonyms']}\n\n💡 Beispiel ({level}): {example}\n\n📝 Grammatik: {data['grammar']}"
        else:
            scrape_data = get_definition(word)
            response = f"📖 **{word.capitalize()}** (PONS)\n\n📚 Definition: {scrape_data['definition']}\n\nLink: https://de.pons.com/uebersetzung/deutsch/{word}"

        bot.reply_to(message, response, parse_mode='Markdown')
        print(f"Debug: Response for '{word}' sent!")

    except Exception as e:
        print(f"Debug: Handle exception for '{word}': {str(e)}\n{traceback.format_exc()}")
        bot.reply_to(message, f"Fehler bei '{word}': {str(e)}. Probiere /start.")

# Callback simple
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    print("Debug: Callback")
    bot.answer_callback_query(call.id, "OK!")

# Flask Webhook
app = Flask(__name__)

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    print("Debug: Webhook POST")
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    return 'Unauthorized', 401

@app.route('/', methods=['GET'])
def index():
    print("Debug: GET /")
    return '<h1>Bot läuft! Test /start</h1>'

bot.remove_webhook()
bot.set_webhook(url=f'https://deutsche360-bot.onrender.com/{TOKEN}')

PORT = int(os.environ.get('PORT', 5000))
print(f"Starting bot on port {PORT}")
app.run(host='0.0.0.0', port=PORT)
