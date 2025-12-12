# Deutsches Wörterbuch-Bot – Full Steps 1-4: Cache + Dict.cc + UI Inline + Audio Forvo + /lang Toggle
TOKEN = '8224460982:AAEPMMNfWxFfzqPTcqUCxKI0zJr8IP-dzG4'

import telebot
from telebot import types
from telebot.types import CallbackQuery  # Step 4: For inline callbacks
import requests
from bs4 import BeautifulSoup  # From Step 3
from flask import Flask, request
import os
import traceback
import json

bot = telebot.TeleBot(TOKEN)
print("Bot initialized – Steps 1-4: Glosbe + Cache + Dict.cc + UI/Audio/Lang")

# Small local for grammar/notes (fallback)
grammar_fallback = {
    "blau": {"type": "Adjektiv", "article": "", "grammar_notes": "Deklination: ein blaues Auto (Neutr.); der blaue Himmel (Mask.). Komparativ: blauer, Superlativ: am blauensten."},
    "rot": {"type": "Adjektiv", "article": "", "grammar_notes": "Deklination: ein rotes Auto; der rote Apfel. Komparativ: röter."},
    "groß": {"type": "Adjektiv", "article": "", "grammar_notes": "Komparativ: größer, Superlativ: am größten. Deklination: ein großes Haus."},
    "kommen": {"type": "Verb", "article": "", "grammar_notes": "Starkes Verb. Präsens: ich komme, du kommst, er kommt. Präteritum: kam, Partizip II: gekommen."},
    "essen": {"type": "Verb", "article": "", "grammar_notes": "Starkes Verb. Präsens: ich esse, du isst. Präteritum: aß, Partizip II: gegessen."},
    "haus": {"type": "Nomen", "article": "das", "grammar_notes": "Neutrum. Plural: Häuser. Deklination: das Haus (Nom./Akk.), des Hauses (Gen.)."},
}

user_levels = {}
user_history = {}
user_lang = {}  # Step 4: Per user language (default 'de')

# Step 2: Cache for speed
response_cache = {}
max_cache = 100

# Step 3: Dict.cc fallback (parse HTML)
def get_dictcc_data(word):
    print(f"Debug: Dict.cc fallback for '{word}'")
    url = f"https://www.dict.cc/?s={word}&hl=de"
    headers = {'User-Agent': 'Mozilla/5.0 (Educational bot; @sprachschule67)'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            terms_table = soup.find('table', class_='td7')
            if terms_table:
                terms = [td.get_text().strip() for td in terms_table.find_all('td', class_='td7note')[:5]]
                definition = f'Definition für {word}: {terms[0] if terms else "Allgemeiner Begriff aus Dict.cc."}'
                synonyms = ', '.join(terms[1:]) if len(terms) > 1 else 'Synonyme in Dict.cc gefunden.'
                examples = [f"Beispiel: {word} als {terms[0] if terms else 'Begriff'}.", f"Satz: Der {word}."]
                word_type = 'Nomen'  # Default
                article = ''
                grammar_notes = grammar_fallback.get(word, {}).get('grammar_notes', f'Grammatik: Standard (Dict.cc).')
                full_data = {'word': word.capitalize(), 'definition': definition, 'article': article, 'type': word_type, 'synonyms': synonyms, 'examples': examples, 'grammar_notes': grammar_notes, 'source': 'Dict.cc'}
                
                # Cache
                if len(response_cache) >= max_cache:
                    oldest_key = next(iter(response_cache))
                    del response_cache[oldest_key]
                response_cache[word] = full_data
                print(f"Debug: Dict.cc success for '{word}'")
                return full_data
    except Exception as e:
        print(f"Debug: Dict.cc error: {str(e)}")
    return get_approximate(word)

# Glosbe API (with cache + Dict.cc fallback – Steps 2-3)
def get_glosbe_data(word):
    if word in response_cache:
        print(f"Debug: Cache hit for '{word}'")
        return response_cache[word]
    
    print(f"Debug: Glosbe API for '{word}'")
    url = f"https://glosbe.com/gapi/translate?from=de&dest=de&format=json&phrase={word}&page=1&results=10"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['tuc'] and len(data['tuc']) > 0:
                tuc = data['tuc'][0]
                phrase = tuc.get('phrase', {}).get('text', word.capitalize())
                definition = tuc.get('meanings', [{}])[0].get('text', f'Definition von {word}: Allgemeiner Begriff.')
                word_type = tuc.get('meanings', [{}])[0].get('category', 'Nomen')
                if 'adjektiv' in word_type.lower() or 'adjective' in word_type.lower():
                    word_type = 'Adjektiv'
                elif 'verb' in word_type.lower():
                    word_type = 'Verb'
                elif 'nomen' in word_type.lower() or 'noun' in word_type.lower():
                    word_type = 'Nomen'
                else:
                    word_type = 'Nomen'
                article = 'das' if word_type == 'Adjektiv' else 'der' if 'mask' in str(tuc).lower() else 'die' if 'fem' in str(tuc).lower() else ''
                synonyms = ', '.join([p.get('text', '') for p in data.get('phrase', [])[:5] if p.get('text')]) if data.get('phrase') else 'Synonyme nicht gefunden.'
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
                grammar_notes = grammar_fallback.get(word, {}).get('grammar_notes', f'Grammatik für {word_type}: Standard.')
                full_data = {'word': phrase, 'definition': definition, 'article': article, 'type': word_type, 'synonyms': synonyms, 'examples': examples, 'grammar_notes': grammar_notes, 'source': 'Glosbe API'}
                
                # Cache
                if len(response_cache) >= max_cache:
                    oldest_key = next(iter(response_cache))
                    del response_cache[oldest_key]
                response_cache[word] = full_data
                print(f"Debug: Glosbe success for '{word}'")
                return full_data
            else:
                print(f"Debug: No Glosbe data – fallback Dict.cc")
        else:
            print(f"Debug: Glosbe status {response.status_code} – fallback Dict.cc")
    except Exception as e:
        print(f"Debug: Glosbe error: {str(e)} – fallback Dict.cc")
    return get_dictcc_data(word)

# Approximate fallback (final)
def get_approximate(word):
    print(f"Debug: Approximate for '{word}'")
    word_type = 'Adjektiv' if word in ['blau', 'rot', 'groß'] else 'Verb' if word in ['kommen', 'essen'] else 'Nomen'
    article = 'das' if word_type == 'Adjektiv' else 'der' if word_type == 'Nomen' else ''
    definition = f'Approximate Definition für "{word}": Häufiger Begriff im Deutschen.'
    examples = [f"Beispiel: Der {word} ist gut.", f"Medium: Ich sehe den {word}.", f"Advanced: {word} in Kontext."]
    grammar_notes = grammar_fallback.get(word, {}).get('grammar_notes', f'Standard für {word_type}.')
    full_data = {'word': word.capitalize(), 'definition': definition, 'article': article, 'type': word_type, 'synonyms': 'Ähnliche Wörter', 'examples': examples, 'grammar_notes': grammar_notes, 'source': 'Approximate'}
    
    # Cache
    if len(response_cache) >= max_cache:
        oldest_key = next(iter(response_cache))
        del response_cache[oldest_key]
    response_cache[word] = full_data
    return full_data

# get_local (with cache)
def get_local(word, message):
    word_lower = word.lower()
    if word_lower in grammar_fallback:
        data = {'word': word_lower.capitalize(), 'article': grammar_fallback[word_lower]['article'], 'type': grammar_fallback[word_lower]['type'], 'grammar_notes': grammar_fallback[word_lower]['grammar_notes'], 'definition': f'Definition für {word}: Local.', 'synonyms': 'Nicht spezifiziert', 'examples': [f"Beispiel: Der {word}."], 'source': 'Local'}
        if word_lower not in response_cache:
            if len(response_cache) >= max_cache:
                oldest_key = next(iter(response_cache))
                del response_cache[oldest_key]
            response_cache[word_lower] = data
        return data
    return None

# Step 4: Forvo Audio (pronunciation MP3)
def get_audio_url(word):
    print(f"Debug: Forvo audio for '{word}'")
    url = f"https://apiforvo.com/v1/words/{word}/pronunciations?language=de&format=mp3"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data['items'] and len(data['items']) > 0:
                audio_url = data['items'][0]['path_mp3']  # First pronunciation
                full_url = f"https://audio00.forvo.com/mp3/{audio_url}"
                print(f"Debug: Forvo success: {full_url}")
                return full_url
    except Exception as e:
        print(f"Debug: Forvo error: {str(e)}")
    return None

# Step 4: Translate to Persian (simple dict – expand if needed)
def translate_to_fa(data, word):
    fa_dict = {
        "definition": "تعریف: " + data['definition'][:100] + " (تقریبی فارسی).",
        "synonyms": "مشابه‌ها: " + data['synonyms'],
        "examples": ["مثال: " + ex for ex in data['examples'][:2]],
        "grammar_notes": "دستور زبان: " + data['grammar_notes'][:100],
        "type": {"Adjektiv": "صفت", "Verb": "فعل", "Nomen": "اسم"}.get(data['type'], data['type']),
        "article": "مقاله: " + data['article'] if data['article'] else ""
    }
    return fa_dict

# Handlers
@bot.message_handler(commands=['start'])
def start_message(message):
    print(f"Debug: /start")
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    markup.add(types.KeyboardButton("/lang de"), types.KeyboardButton("/lang fa"))
    markup.add(types.KeyboardButton("/cache_info"), types.KeyboardButton("/audio blau"))  # Example
    bot.reply_to(message, "Hallo! Bot mit Steps 1-4: Cache, Fallback, UI Inline + Audio + /lang!\nBefehle: /level, /local, /history, /lang fa/en, /audio <word>, /cache_info\nTest: 'blau' – klicke Buttons, /lang fa für فارسی, /audio blau für صدا!", reply_markup=markup)

@bot.message_handler(commands=['lang'])
def set_lang(message):
    parts = message.text.split()
    lang = parts[1].lower() if len(parts) > 1 else 'de'
    if lang in ['de', 'fa', 'en']:
        user_lang[message.from_user.id] = lang
        bot.reply_to(message, f"Sprache auf {lang} gesetzt! (de=Deutsch, fa=فارسی, en=English)")
    else:
        bot.reply_to(message, "Verfügbare Sprachen: de, fa, en. /lang de (default)")

@bot.message_handler(commands=['audio'])
def send_audio(message):
    parts = message.text.split()
    word = parts[1].lower() if len(parts) > 1 else 'blau'  # Default test
    audio_url = get_audio_url(word)
    if audio_url:
        bot.send_voice(message.chat.id, audio_url, caption=f"Pronunciation von '{word}' (Forvo API – Step 4)")
    else:
        bot.reply_to(message, f"Audio nicht gefunden für '{word}'. Versuche ein gängiges Wort wie 'haus'.")

@bot.message_handler(commands=['cache_info'])
def cache_info(message):
    cache_size = len(response_cache)
    cached_words = list(response_cache.keys())[:5]
    bot.reply_to(message, f"Cache: {cache_size}/{max_cache} Wörter. Erste: {', '.join(cached_words)} (Steps 1-4)")

@bot.message_handler(commands=['level'])
def set_level(message):
    parts = message.text.split()
    level = parts[1].lower() if len(parts) > 1 else 'medium'
    if level in ['beginner', 'medium', 'advanced']:
        user_levels[message.from_user.id] = level
        bot.reply_to(message, f"Level {level} set!")
    else:
        bot.reply_to(message, "Levels: beginner, medium, advanced")

@bot.message_handler(commands=['local'])
def local_mode(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    for key in grammar_fallback.keys():
        markup.row(types.KeyboardButton(key))
    bot.reply_to(message, "Local Words: Choose! (Steps 1-4 active)")

@bot.message_handler(commands=['history'])
def show_history(message):
    hist = user_history.get(message.from_user.id, [])
    if hist:
        bot.reply_to(message, "Last 5 Words:\n" + "\n".join(hist[-5:]))
    else:
        bot.reply_to(message, "History empty!")

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

        level = user_levels.get(user_id, 'medium')
        examples = data['examples']
        if level == 'beginner' and len(examples) > 1:
            examples = examples[:1]
        elif level == 'advanced':
            if len(examples) < 3:
                examples.append(f"Advanced: {word} in Kontext.")

        # Step 4: Language toggle
        lang = user_lang.get(user_id, 'de')
        if lang == 'fa':
            fa_data = translate_to_fa(data, word)
            response = f"📖 **{data['word']}** ({fa_data['type']}, {data['source']})\n\n"
            if fa_data['article']:
                response += f"📰 {fa_data['article']}\n\n"
            response += f"📚 {fa_data['definition']}\n\n"
            if fa_data['synonyms']:
                response += f"🔄 {fa_data['synonyms']}\n\n"
            response += f"💡 مثال‌ها ({level}):\n"
            for ex in fa_data['examples']:
                response += f"• {ex}\n"
            response += f"\n📝 {fa_data['grammar_notes']}"
        else:  # de or en (same for now)
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

        # Step 4: Inline markup for UI
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("Synonyme anzeigen", callback_data=f"syn_{word}"),
                   types.InlineKeyboardButton("Mehr Beispiele", callback_data=f"ex_{word}"))
        markup.add(types.InlineKeyboardButton("Konjugation", callback_data=f"gram_{word}"),
                   types.InlineKeyboardButton("Hören (Audio)", callback_data=f"audio_{word}"))
        markup.add(types.InlineKeyboardButton("Mehr online", url=f"https://de.glosbe.com/de/de/{word}"))

        bot.reply_to(message, response, parse_mode='Markdown', reply_markup=markup)
        print(f"Debug: UI response sent for '{word}' (lang: {lang})")

    except Exception as e:
        print(f"Debug: Error for '{word}': {str(e)}")
        bot.reply_to(message, f"Fehler: {str(e)}. /start neu.")

# Step 4: Callback handlers for inline UI
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call: CallbackQuery):
    data = call.data
    word = data.split('_')[1]
    user_id = call.from_user.id
    
    if data.startswith('syn_'):
        # Get synonyms
        full_data = response_cache.get(word, get_glosbe_data(word))
        syn_text = full_data['synonyms'] if full_data['synonyms'] else 'Keine Synonyme gefunden.'
        bot.edit_message_text(f"Synonyme für {word}: {syn_text}\n\n(Klicke /start für neu)", call.message.chat.id, call.message.message_id, parse_mode='Markdown')
        print(f"Debug: Syn callback for {word}")
    elif data.startswith('ex_'):
        # More examples
        full_data = response_cache.get(word, get_glosbe_data(word))
        ex_text = '\n'.join(full_data['examples'])
        bot.edit_message_text(f"Mehr Beispiele für {word}:\n{ex_text}\n\n(Klicke /start für neu)", call.message.chat.id, call.message.message_id)
        print(f"Debug: Ex callback for {word}")
    elif data.startswith('gram_'):
        # Grammar
        full_data = response_cache.get(word, get_glosbe_data(word))
        gram_text = full_data['grammar_notes']
        bot.edit_message_text(f"Konjugation/Grammatik für {word}:\n{gram_text}\n\n(Klicke /start für neu)", call.message.chat.id, call.message.message_id)
        print(f"Debug: Gram callback for {word}")
    elif data.startswith('audio_'):
        # Audio
        audio_url = get_audio_url(word)
        if audio_url:
            bot.delete_message(call.message.chat.id, call.message.message_id)  # Delete old
            bot.send_voice(call.message.chat.id, audio_url, caption=f"Pronunciation von '{word}' (Forvo – Step 4)")
        else:
            bot.answer_callback_query(call.id, "Audio nicht verfügbar. Versuche /audio {word}")
        print(f"Debug: Audio callback for {word}")
    else:
        bot.answer_callback_query(call.id, "Button gedrückt – mehr Infos!")

# Webhook
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
    return '<h1>Bot Steps 1-4: UI + Audio + Lang – interactive!</h1>'

bot.remove_webhook()
bot.set_webhook(url=f'https://deutsche360-bot.onrender.com/{TOKEN}')

PORT = int(os.environ.get('PORT', 5000))
app.run(host='0.0.0.0', port=PORT)

print("Bot Steps 1-4 started – UI, Audio, Lang ready!")
