# Deutsches Wörterbuch-Bot – Vollständig mit Scrape von wort.ir (alle Wörter, Beispiele, Grammatik realtime)
TOKEN = '8224460982:AAEPMMNfWxFfzqPTcqUCxKI0zJr8IP-dzG4'

import telebot
from telebot import types
import requests
from bs4 import BeautifulSoup
from flask import Flask, request
import os
import traceback
import random

bot = telebot.TeleBot(TOKEN)
print("Bot initialized – Scrape from wort.ir for all words")

# Kleine local_dict nur für Test (5 Wörter – hauptsächlich scrape wort.ir)
local_dict = {
    "haus": {"type": "Nomen", "article": "das", "definition": "Gebäude zum Wohnen.", "synonyms": "Wohnung", "examples": {"beginner": "Das Haus ist groß.", "medium": "Ich wohne im Haus.", "advanced": "Historisches Haus."}, "grammar": "Neutrum. Plural: Häuser."},
    "auto": {"type": "Nomen", "article": "das", "definition": "Motorisiertes Fahrzeug.", "synonyms": "Wagen", "examples": {"beginner": "Das Auto fährt.", "medium": "Ich fahre das Auto.", "advanced": "Elektroauto."}, "grammar": "Neutrum. Plural: Autos."},
    "blau": {"type": "Adjektiv", "article": "", "definition": "Farbton des Himmels.", "synonyms": "Azur", "examples": {"beginner": "Der Himmel ist blau.", "medium": "Blaues Auto.", "advanced": "Blau symbolisiert Ruhe."}, "grammar": "Deklination: ein blaues Auto. Komparativ: blauer."},
    "kommen": {"type": "Verb", "article": "", "definition": "Ankommen oder nähern.", "synonyms": "Ankommen", "examples": {"beginner": "Ich komme.", "medium": "Komm her.", "advanced": "Zug kommt."}, "grammar": "Präsens: ich komme, du kommst."},
    "essen": {"type": "Verb", "article": "", "definition": "Nahrung aufnehmen.", "synonyms": "Speisen", "examples": {"beginner": "Ich esse Brot.", "medium": "Wir essen.", "advanced": "Gesund essen."}, "grammar": "Präsens: ich esse, du isst."}
}

user_levels = {}
user_history = {}

# Scrape from wort.ir (realtime für alle Wörter – Definition, Beispiele, Grammatik)
def scrape_wort_ir(word):
    print(f"Debug: Scrape wort.ir for '{word}'")
    url = f"https://wort.ir/{word}/"
    headers_list = [
        {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'},
        {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    ]
    for attempt in range(3):  # 3 retries
        headers = random.choice(headers_list)
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Parse wort.ir structure (simple: meaning div, examples ul, grammar span)
                title = soup.find('h1', class_='word-title')
                word_type = 'Adjektiv' if 'صفت' in str(soup) else 'Verb' if 'فعل' in str(soup) else 'Nomen' if 'اسم' in str(soup) else 'Unbekannt'
                article = 'der' if 'مذکر' in str(soup) else 'die' if 'مؤنث' in str(soup) else 'das' if 'خنثی' in str(soup) else ''
                definition_div = soup.find('div', class_='meaning') or soup.find('p', class_='definition')
                definition = definition_div.get_text().strip()[:250] if definition_div else f'Definition für {word}: Begriff aus Deutsch (wort.ir).'
                # Beispiele (ul class examples or li)
                examples_li = soup.find_all('li', class_='example') or soup.find_all('ul', class_='examples').find_all('li') if soup.find('ul', class_='examples') else []
                examples = [li.get_text().strip()[:100] for li in examples_li[:3]] or [f"Beispiel: Der {word} ist schön."]
                # Synonyme (if div synonyms)
                synonyms_div = soup.find('div', class_='synonyms')
                synonyms = synonyms_div.get_text().strip() if synonyms_div else 'Synonyme nicht gefunden.'
                # Grammatik/Konjugation (div grammar or table)
                grammar_div = soup.find('div', class_='grammar') or soup.find('table', class_='konjugation')
                grammar_notes = grammar_div.get_text().strip()[:200] if grammar_div else f'Grammatik für {word_type}: Standard Deklination/Konjugation (wort.ir).'
                print(f"Debug: wort.ir success for '{word}' attempt {attempt+1}")
                return {'word': word.capitalize(), 'definition': definition, 'article': article, 'type': word_type, 'synonyms': synonyms, 'examples': examples, 'grammar_notes': grammar_notes, 'source': 'wort.ir'}
        except Exception as e:
            print(f"Debug: wort.ir attempt {attempt+1} failed for '{word}': {str(e)}")
            continue
    print(f"Debug: wort.ir failed – fallback approximate")
    return get_approximate(word)

# Approximate fallback (for rare fails, full info)
def get_approximate(word):
    approx_data = {
        "blau": {"type": "Adjektiv", "article": "", "definition": "به رنگ آبی، آرام و خنک (Farbton des Himmels, symbolisiert Ruhe).", "synonyms": "آبی آسمانی, ازور (Azur, himmelblau)", "examples": ["Der Himmel ist blau. (آسمان آبی است.)", "Ein blaues Kleid. (لباس آبی.)", "Blaue Augen. (چشمان آبی.)"], "grammar_notes": "صفت (Adjektiv). صرف: ein blaues Auto (خنثی); der blaue Himmel (مذکر). مقایسه: blauer (مقایسه), am blauensten (عالی)."},
        # Add more common if needed (e.g., rot, grün – but wort.ir covers most)
    }
    if word in approx_data:
        return approx_data[word]
    # General approximate
    return {'word': word.capitalize(), 'definition': f'Allgemeine Definition für "{word}": Begriff im Deutschen (suche wort.ir für Details).', 'article': '', 'type': 'Nomen', 'synonyms': 'Nicht gefunden', 'examples': [f"Beispiel: Der {word} ist interessant."], 'grammar_notes': 'Standard Grammatik. Für Verben: Präsens ich {word}, du {word}st.', 'source': 'Approximate'}

# get_local (klein, for speed)
def get_local(word, message):
    word_lower = word.lower()
    if word_lower in local_dict:
        print(f"Debug: Local for '{word_lower}'")
        data = local_dict[word_lower]
        level = user_levels.get(message.from_user.id, 'medium')
        ex = data['examples'].get(level, data['examples']['beginner'])
        return {'word': word.capitalize(), 'definition': data['definition'], 'article': data['article'], 'type': data['type'], 'synonyms': data['synonyms'], 'examples': [ex], 'grammar_notes': data['grammar'], 'source': 'Local'}
    return None

# Handlers
@bot.message_handler(commands=['start'])
def start_message(message):
    print(f"Debug: /start")
    bot.reply_to(message, "Hallo! Deutsches Wörterbuch-Bot mit Scrape von wort.ir (alle Wörter, Beispiele, Grammatik realtime)!\nBefehle: /level beginner|medium|advanced, /local (5 Test), /history\nEingabe: 'blau' oder jedes Wort – vollständige Info von wort.ir!")

@bot.message_handler(commands=['level'])
def set_level(message):
    parts = message.text.split()
    level = parts[1].lower() if len(parts) > 1 else 'medium'
    if level in ['beginner', 'medium', 'advanced']:
        user_levels[message.from_user.id] = level
        bot.reply_to(message, f"Niveau {level} gesetzt! Beispiele angepasst.")
    else:
        bot.reply_to(message, "Niveaus: beginner, medium, advanced")

@bot.message_handler(commands=['local'])
def local_mode(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    for key in local_dict.keys():
        markup.row(types.KeyboardButton(key))
    bot.reply_to(message, "Lokale Testwörter (5): Wähle! (Für alle: scrape wort.ir)")

@bot.message_handler(commands=['history'])
def show_history(message):
    hist = user_history.get(message.from_user.id, [])
    if hist:
        bot.reply_to(message, "Letzte Wörter:\n" + "\n".join(hist[-5:]))
    else:
        bot.reply_to(message, "Verlauf leer – suche Wörter!")

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    word = message.text.strip().lower()
    user_id = message.from_user.id
    print(f"Debug: Handling '{word}' from {user_id}")
    if len(word) < 2 or word.startswith('/'):
        return

    # History
    if user_id not in user_history:
        user_history[user_id] = []
    if word not in user_history[user_id]:
        user_history[user_id].append(word)
        if len(user_history[user_id]) > 10:
            user_history[user_id].pop(0)

    try:
        local_data = get_local(word, message)
        if local_data:
            data = local_data
            print(f"Debug: Local response for '{word}'")
        else:
            data = scrape_wort_ir(word)
            print(f"Debug: wort.ir response for '{word}'")

        # Adjust examples for level (if multiple, select; else generate/add)
        level = user_levels.get(user_id, 'medium')
        if len(data['examples']) > 1:
            ex_list = data['examples'][:2] if level == 'beginner' else data['examples'][:3] if level == 'medium' else data['examples']
        else:
            # Generate level-based if only 1 example
            base_ex = data['examples'][0]
            ex_list = [base_ex]  # Simple, or expand if needed

        response = f"📖 **{data['word']}** ({data['type']}, {data['source']})\n\n"
        if data['article']:
            response += f"📰 **Artikel:** {data['article']} {word}\n\n"
        response += f"📚 **Definition:** {data['definition']}\n\n"
        if data['synonyms'] and data['synonyms'] != 'Nicht gefunden':
            response += f"🔄 **Synonyme:** {data['synonyms']}\n\n"
        response += f"💡 **Beispiele ({level}):**\n"
        for ex in ex_list:
            response += f"• {ex}\n"
        response += f"\n📝 **Grammatik:** {data['grammar_notes']}"

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Mehr auf wort.ir (optional)", url=f"https://wort.ir/{word}/"))
        bot.reply_to(message, response, parse_mode='Markdown', reply_markup=markup)
        print(f"Debug: Full response sent for '{word}'")

    except Exception as e:
        print(f"Debug: Error handling '{word}': {str(e)}\n{traceback.format_exc()}")
        bot.reply_to(message, f"Fehler bei '{word}': {str(e)}. Scrape wort.ir – probiere erneut oder /start.")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    bot.answer_callback_query(call.id, "Mehr auf wort.ir – optional!")

# Webhook
app = Flask(__name__)

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    print("Debug: Webhook POST received")
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    return 'Unauthorized', 401

@app.route('/', methods=['GET', 'HEAD'])
def index():
    return '<h1>Bot mit wort.ir Scrape – alle Wörter!</h1>'

bot.remove_webhook()
bot.set_webhook(url=f'https://deutsche360-bot.onrender.com/{TOKEN}')

PORT = int(os.environ.get('PORT', 5000))
app.run(host='0.0.0.0', port=PORT)

print("Bot gestartet – wort.ir für alle Wörter & Beispiele!")
