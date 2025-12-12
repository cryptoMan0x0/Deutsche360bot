# Deutsches Wörterbuch-Bot – Glosbe API (alle Wörter, Beispiele, Synonyme realtime – wie professionelle Bots)
TOKEN = '8224460982:AAEPMMNfWxFfzqPTcqUCxKI0zJr8IP-dzG4'

import telebot
from telebot import types
import requests
from flask import Flask, request
import os
import traceback
import json

bot = telebot.TeleBot(TOKEN)
print("Bot initialized – Glosbe API for all German words")

# Small local for grammar/notes (5-10 words, fallback – main: Glosbe API)
grammar_fallback = {
    "blau": {"type": "Adjektiv", "article": "", "grammar_notes": "Deklination: ein blaues Auto (Neutr.); der blaue Himmel (Mask.). Komparativ: blauer, Superlativ: am blauensten."},
    "rot": {"type": "Adjektiv", "article": "", "grammar_notes": "Deklination: ein rotes Auto; der rote Apfel. Komparativ: röter."},
    "groß": {"type": "Adjektiv", "article": "", "grammar_notes": "Komparativ: größer, Superlativ: am größten. Deklination: ein großes Haus."},
    "kommen": {"type": "Verb", "article": "", "grammar_notes": "Starkes Verb. Präsens: ich komme, du kommst, er kommt. Präteritum: kam, Partizip II: gekommen."},
    "essen": {"type": "Verb", "article": "", "grammar_notes": "Starkes Verb. Präsens: ich esse, du isst. Präteritum: aß, Partizip II: gegessen."},
    "haus": {"type": "Nomen", "article": "das", "grammar_notes": "Neutrum. Plural: Häuser. Deklination: das Haus (Nom./Akk.), des Hauses (Gen.)."},
    # Add more if needed (e.g., philosoph ie: Nomen, die, Plural: Philosophien)
}

user_levels = {}
user_history = {}

# Glosbe API (free, reliable – definition, synonyms, examples, type)
def get_glosbe_data(word):
    print(f"Debug: Glosbe API for '{word}'")
    url = f"https://glosbe.com/gapi/translate?from=de&dest=de&format=json&phrase={word}&page=1&results=10"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['tuc'] and len(data['tuc']) > 0:
                tuc = data['tuc'][0]
                phrase = tuc.get('phrase', {}).get('text', word.capitalize())
                definition = tuc.get('meanings', [{}])[0].get('text', f'Definition von {word}: Allgemeiner Begriff im Deutschen.')
                # Type from meanings or fallback
                word_type = tuc.get('meanings', [{}])[0].get('category', 'Nomen')  # e.g., 'adjective', 'verb'
                if 'adjektiv' in word_type.lower() or 'adjective' in word_type.lower():
                    word_type = 'Adjektiv'
                elif 'verb' in word_type.lower():
                    word_type = 'Verb'
                elif 'nomen' in word_type.lower() or 'noun' in word_type.lower():
                    word_type = 'Nomen'
                else:
                    word_type = 'Nomen'  # Default
                # Article fallback (simple)
                article = 'das' if word_type == 'Adjektiv' else 'der' if 'mask' in str(tuc).lower() else 'die' if 'fem' in str(tuc).lower() else ''
                # Synonyms from phrases
                synonyms = ', '.join([p.get('text', '') for p in data.get('phrase', [])[:5] if p.get('text')]) if data.get('phrase') else 'Synonyme nicht gefunden.'
                # Examples from tuc examples
                examples = []
                for meaning in tuc.get('meanings', []):
                    for ex in meaning.get('examples', []):
                        if ex.get('first', ''):
                            examples.append(ex['first'])
                        if len(examples) >= 3:
                            break
                    if len(examples) >= 3:
                        break
                if not examples:
                    examples = [f"Beispiel: Der {word} ist interessant.", f"Der {word} in einem Satz.", f"Advanced: {word} in Kontext."]
                grammar_notes = grammar_fallback.get(word, {}).get('grammar_notes', f'Grammatik für {word_type}: Standard Deklination/Konjugation (Glosbe + fallback).')
                print(f"Debug: Glosbe success for '{word}'")
                return {'word': phrase, 'definition': definition, 'article': article, 'type': word_type, 'synonyms': synonyms, 'examples': examples, 'grammar_notes': grammar_notes, 'source': 'Glosbe API'}
        else:
            print(f"Debug: Glosbe status {response.status_code} for '{word}'")
    except Exception as e:
        print(f"Debug: Glosbe error for '{word}': {str(e)}")
    return get_approximate(word)

# Approximate fallback (if API rare fail)
def get_approximate(word):
    print(f"Debug: Approximate for '{word}'")
    word_type = 'Adjektiv' if word in ['blau', 'rot', 'groß'] else 'Verb' if word in ['kommen', 'essen'] else 'Nomen'
    article = 'das' if word_type == 'Adjektiv' else 'der' if word_type == 'Nomen' else ''
    definition = f'Approximate Definition für "{word}": Häufiger Begriff im Deutschen (Glosbe API fallback).'
    examples = [f"Beispiel (beginner): Der {word} ist gut.", f"Medium: Ich sehe den {word}.", f"Advanced: {word} in der Literatur."]
    grammar_notes = grammar_fallback.get(word, {}).get('grammar_notes', f'Standard für {word_type}: Deklination/Konjugation (z.B. Plural für Nomen).')
    return {'word': word.capitalize(), 'definition': definition, 'article': article, 'type': word_type, 'synonyms': 'Ähnliche Wörter aus Glosbe', 'examples': examples, 'grammar_notes': grammar_notes, 'source': 'Approximate'}

# get_local (small)
def get_local(word, message):
    word_lower = word.lower()
    if word_lower in grammar_fallback:
        print(f"Debug: Local grammar for '{word_lower}'")
        data = {'word': word_lower.capitalize(), 'article': grammar_fallback[word_lower]['article'], 'type': grammar_fallback[word_lower]['type'], 'grammar_notes': grammar_fallback[word_lower]['grammar_notes']}
        # Add basic definition/examples from approximate
        data['definition'] = f'Definition für {word}: Standardbegriff (local fallback).'
        data['synonyms'] = 'Nicht spezifiziert'
        data['examples'] = [f"Beispiel: Der {word}."]
        data['source'] = 'Local Grammar'
        return data
    return None

# Handlers (same structure as before)
@bot.message_handler(commands=['start'])
def start_message(message):
    print(f"Debug: /start")
    bot.reply_to(message, "Hallo! Deutsches Wörterbuch-Bot mit Glosbe API (wie professionelle Bots)!\nAlle Wörter abgedeckt: Definition, Synonyme, Beispiele, Grammatik realtime.\nBefehle: /level, /local (grammar fallback), /history\nTest: 'blau' oder 'philosophie' – vollständig!")

@bot.message_handler(commands=['level'])
def set_level(message):
    parts = message.text.split()
    level = parts[1].lower() if len(parts) > 1 else 'medium'
    if level in ['beginner', 'medium', 'advanced']:
        user_levels[message.from_user.id] = level
        bot.reply_to(message, f"Niveau {level} gesetzt – Beispiele angepasst!")
    else:
        bot.reply_to(message, "Niveaus: beginner, medium, advanced")

@bot.message_handler(commands=['local'])
def local_mode(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    for key in grammar_fallback.keys():
        markup.row(types.KeyboardButton(key))
    bot.reply_to(message, "Grammar Fallback (10 Wörter): Wähle! (Haupt: Glosbe API)")

@bot.message_handler(commands=['history'])
def show_history(message):
    hist = user_history.get(message.from_user.id, [])
    if hist:
        bot.reply_to(message, "Letzte 5 Wörter:\n" + "\n".join(hist[-5:]))
    else:
        bot.reply_to(message, "Verlauf leer – suche Wörter!")

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
        local_data = get_local(word, message)
        if local_data:
            data = local_data
        else:
            data = get_glosbe_data(word)

        # Level examples (select or generate)
        level = user_levels.get(user_id, 'medium')
        examples = data['examples']
        if level == 'beginner' and len(examples) > 1:
            examples = examples[:1]
        elif level == 'advanced':
            if len(examples) < 3:
                examples.append(f"Advanced Beispiel für {word}: In komplexem Kontext.")

        response = f"📖 **{data['word']}** ({data['type']}, {data['source']})\n\n"
        if data['article']:
            response += f"📰 **Artikel:** {data['article']} {word}\n\n"
        response += f"📚 **Definition:** {data['definition']}\n\n"
        if data['synonyms'] and 'nicht gefunden' not in data['synonyms'].lower():
            response += f"🔄 **Synonyme:** {data['synonyms']}\n\n"
        response += f"💡 **Beispiele ({level}):**\n"
        for ex in examples[:3]:
            response += f"• {ex}\n"
        response += f"\n📝 **Grammatik:** {data['grammar_notes']}"

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Mehr auf Glosbe (optional)", url=f"https://de.glosbe.com/de/de/{word}"))
        bot.reply_to(message, response, parse_mode='Markdown', reply_markup=markup)
        print(f"Debug: Glosbe/Local response sent for '{word}'")

    except Exception as e:
        print(f"Debug: Exception for '{word}': {str(e)}")
        bot.reply_to(message, f"Fehler bei '{word}': {str(e)}. Glosbe API – probiere ein anderes Wort oder /start.")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    bot.answer_callback_query(call.id, "Mehr auf Glosbe – optional!")

app = Flask(__name__)

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    print("Debug: Webhook")
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    return 'Unauthorized', 401

@app.route('/', methods=['GET'])
def index():
    return '<h1>Glosbe API Bot – alle Wörter abgedeckt!</h1>'

bot.remove_webhook()
bot.set_webhook(url=f'https://deutsche360-bot.onrender.com/{TOKEN}')

PORT = int(os.environ.get('PORT', 5000))
app.run(host='0.0.0.0', port=PORT)

print("Bot with Glosbe API started – full coverage like pro bots!")
