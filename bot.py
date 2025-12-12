# Deutsches Wörterbuch-Bot (Deutsch zu Deutsch, mit Wiktionary API)
TOKEN = '8224460982:AAEPMMNfWxFfzqPTcqUCxKI0zJr8IP-dzG4'

# Bibliotheken
import telebot
from telebot import types
import requests
from bs4 import BeautifulSoup
from flask import Flask, request
import os
import json

bot = telebot.TeleBot(TOKEN)

# Lokales Wörterbuch (10 gängige Wörter, Deutsch zu Deutsch)
local_dict = {
    "haus": {
        "article": "das",
        "definition": "Gebäude, in dem Menschen wohnen. Ein Haus dient als Wohnraum und Schutz.",
        "synonyms": "Wohnung, Gebäude, Heim",
        "examples": {
            "beginner": "Das Haus ist groß.",
            "medium": "Ich wohne in einem alten Haus.",
            "advanced": "Das moderne Haus hat smarte Technologie."
        },
        "grammar": "Neutrum (das Haus), Plural: Häuser. Geschlecht: neutral."
    },
    "freund": {
        "article": "der",
        "definition": "Person, mit der man eine enge Beziehung hat. Ein Freund ist loyal und unterstützend.",
        "synonyms": "Kumpel, Bekannter, Partner",
        "examples": {
            "beginner": "Der Freund ist nett.",
            "medium": "Mein Freund hilft mir.",
            "advanced": "Der beste Freund bleibt immer treu."
        },
        "grammar": "Maskulinum (der Freund), weiblich: Freundin (die). Plural: Freunde."
    },
    "auto": {
        "article": "das",
        "definition": "Fahrzeug mit Motor und Rädern. Das Auto dient dem Transport.",
        "synonyms": "Wagen, Fahrzeug, Karre",
        "examples": {
            "beginner": "Das Auto ist rot.",
            "medium": "Ich fahre mit dem Auto zur Arbeit.",
            "advanced": "Das Elektroauto ist umweltfreundlich."
        },
        "grammar": "Neutrum (das Auto), Plural: Autos. Geschlecht: neutral."
    },
    "buch": {
        "article": "das",
        "definition": "Gedrucktes Werk mit Seiten und Text. Ein Buch vermittelt Wissen.",
        "synonyms": "Roman, Heft, Schrift",
        "examples": {
            "beginner": "Das Buch ist interessant.",
            "medium": "Ich lese ein Buch jeden Abend.",
            "advanced": "Dieses Buch behandelt Philosophie."
        },
        "grammar": "Neutrum (das Buch), Plural: Bücher. Verb: lesen."
    },
    "liebe": {
        "article": "die",
        "definition": "Starkes Gefühl der Zuneigung. Liebe verbindet Menschen.",
        "synonyms": "Affektion, Zuneigung, Leidenschaft",
        "examples": {
            "beginner": "Die Liebe ist schön.",
            "medium": "Ich liebe meine Familie.",
            "advanced": "Liebe erfordert Verständnis."
        },
        "grammar": "Femininum (die Liebe), Verb: lieben."
    },
    "essen": {
        "article": "das",
        "definition": "Aufnahme von Nahrung. Essen nährt den Körper.",
        "synonyms": "Mahlzeit, Speisen",
        "examples": {
            "beginner": "Ich esse Brot.",
            "medium": "Wir essen zusammen.",
            "advanced": "Gesundes Essen ist wichtig."
        },
        "grammar": "Verb (essen), Präsens: ich esse, du isst."
    },
    "gehen": {
        "article": "",
        "definition": "Bewegung zu Fuß. Gehen ist eine grundlegende Handlung.",
        "synonyms": "Laufen, Wandern",
        "examples": {
            "beginner": "Ich gehe nach Hause.",
            "medium": "Geh langsam.",
            "advanced": "Er geht spazieren."
        },
        "grammar": "Verb (gehen), Präsens: ich gehe, du gehst."
    },
    "schule": {
        "article": "die",
        "definition": "Ort zum Lernen. Die Schule bildet Jugendliche aus.",
        "synonyms": "Bildungseinrichtung, Klasse",
        "examples": {
            "beginner": "Die Schule ist groß.",
            "medium": "Ich gehe zur Schule.",
            "advanced": "Die Schule hat gute Lehrer."
        },
        "grammar": "Femininum (die Schule), Plural: Schulen."
    },
    "wasser": {
        "article": "das",
        "definition": "Flüssigkeit zum Trinken. Wasser ist lebensnotwendig.",
        "synonyms": "Getränk, Flüssigkeit",
        "examples": {
            "beginner": "Das Wasser ist kalt.",
            "medium": "Trink Wasser.",
            "advanced": "Sauberes Wasser ist essenziell."
        },
        "grammar": "Neutrum (das Wasser), Plural: Wasser (kein Plural)."
    },
    "freundin": {
        "article": "die",
        "definition": "Weibliche Form von Freund. Eine Freundin ist vertraut.",
        "synonyms": "Freundin, Bekannte",
        "examples": {
            "beginner": "Die Freundin ist nett.",
            "medium": "Meine Freundin ruft an.",
            "advanced": "Sie ist meine beste Freundin."
        },
        "grammar": "Femininum (die Freundin), Plural: Freundinnen."
    }
}

# Benutzerlevels und History
user_levels = {}
user_history = {}

# Wiktionary-API (Deutsch zu Deutsch, pur)
def get_german_definition(word):
    url = f"https://de.wiktionary.org/w/api.php"
    params = {
        'action': 'query',
        'format': 'json',
        'prop': 'extracts|links',
        'exintro': True,
        'explaintext': True,
        'redirects': 1,
        'titles': word,
        'exlimit': 'max',
        'pllimit': 'max'
    }
    headers = {
        'User-Agent': 'GermanDictBot/1.0 (Personal educational bot by @sprachschule67; contact: @sprachschule67)'
    }
    try:
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            pages = data['query'].get('pages', {})
            if pages and not str(list(pages.keys())[0]).startswith('-1'):
                page = list(pages.values())[0]
                extract = page.get('extract', 'Definition nicht gefunden').strip()
                soup = BeautifulSoup(extract, 'html.parser') if extract else None
                text = soup.get_text() if soup else extract
                article = 'unbekannt'
                lower_text = text.lower()
                if 'der ' in lower_text[:20]:
                    article = 'der'
                elif 'die ' in lower_text[:20]:
                    article = 'die'
                elif 'das ' in lower_text[:20]:
                    article = 'das'
                definition = text[:250] + '...' if len(text) > 250 else text
                synonyms = []
                if 'links' in page:
                    for link in page['links'][:5]:
                        if link['title'] != word and ':' not in link['title'] and len(link['title']) > 2:
                            synonyms.append(link['title'])
                synonyms_str = ', '.join(synonyms[:3]) if synonyms else 'Nicht gefunden'
                examples = [s.strip() + '.' for s in text.split('.') if len(s.strip()) > 15][:3]
                if not examples:
                    examples = [f"Beispiel für {word}: {definition[:80]}..."]
                grammar_notes = f"Artikel: {article}. Für Anfänger: Artikel merken. Mittelstufe: Sätze bilden. Fortgeschritten: Synonyme verwenden. Plural/Declination: Siehe Wiktionary."
                return {
                    'word': word.capitalize(),
                    'definition': definition,
                    'article': article,
                    'synonyms': synonyms_str,
                    'examples': examples,
                    'grammar_notes': grammar_notes,
                    'source': 'Wiktionary'
                }
            else:
                return {'error': f'Wort "{word}" in Wiktionary nicht gefunden!'}
        else:
            return {'error': f'API-Fehler (Code: {response.status_code}) – Verwende /local.'}
    except Exception as e:
        return {'error': f'Fehler: {str(e)}'}

# Lokale Definition (Deutsch zu Deutsch)
def get_local_definition(word):
    if word in local_dict:
        data = local_dict[word]
        level = user_levels.get(message.from_user.id, 'medium')
        examples = [data['examples'].get(level, data['examples']['medium'])]
        return {
            'word': word.capitalize(),
            'definition': data['definition'],
            'article': data['article'],
            'synonyms': data['synonyms'],
            'examples': examples,
            'grammar_notes': data['grammar'],
            'source': 'Local'
        }
    else:
        return {'error': f'Wort "{word}" im lokalen Wörterbuch nicht gefunden! /local für mehr.'}

# /start
@bot.message_handler(commands=['start'])
def start_message(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Hilfe", callback_data="help"))
    bot.reply_to(message, "Hallo! Ich bin dein deutsches Wörterbuch-Bot.\n\nBefehle:\n/level beginner – Anfängerniveau\n/local – Lokales Wörterbuch\n/history – Verlauf\n\nSchicke ein Wort (z.B. 'Haus')!", reply_markup=markup)

# /level
@bot.message_handler(commands=['level'])
def set_level(message):
    level = message.text.split()[1].lower() if len(message.text.split()) > 1 else 'medium'
    if level in ['beginner', 'medium', 'advanced']:
        user_levels[message.from_user.id] = level
        bot.reply_to(message, f"Niveau {level} eingestellt! Beispiele werden angepasst.")
    else:
        bot.reply_to(message, "Niveaus: beginner, medium, advanced")

# /local
@bot.message_handler(commands=['local'])
def local_mode(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    for word in list(local_dict.keys())[:5]:
        markup.add(types.KeyboardButton(word))
    bot.reply_to(message, "Lokaler Modus aktiviert! Wähle ein Wort:", reply_markup=markup)

# /history
@bot.message_handler(commands=['history'])
def show_history(message):
    hist = user_history.get(message.from_user.id, [])
    if hist:
        response = "Letzte 5 Wörter:\n" + "\n".join(hist[-5:])
        bot.reply_to(message, response)
    else:
        bot.reply_to(message, "Verlauf leer! Suche ein Wort.")

# Wortsuche
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    word = message.text.strip().lower()
    user_id = message.from_user.id
    if word in ['/start', '/level', '/local', '/history']:
        return
    
    if len(word) < 2:
        bot.reply_to(message, "Wort mit mind. 2 Buchstaben eingeben!")
        return

    # History speichern
    if user_id not in user_history:
        user_history[user_id] = []
    if word not in user_history[user_id]:
        user_history[user_id].append(word)
        if len(user_history[user_id]) > 10:
            user_history[user_id] = user_history[user_id][-10:]

    # API versuchen, sonst local
    data = get_german_definition(word)
    if 'error' in data:
        data = get_local_definition(word)
        if 'error' in data:
            bot.reply_to(message, data['error'])
            return

    # Antwort mit Niveau
    level = user_levels.get(user_id, 'medium')
    examples = data['examples'][:1] if level == 'beginner' else data['examples'][:2] if level == 'medium' else data['examples']

    response = f"📖 **{data['word']}** ({data['source']})\n\n"
    response += f"📰 **Artikel:** {data['article']} {data['word']}\n\n"
    response += f"📚 **Definition:** {data['definition']}\n\n"
    response += f"🔄 **Synonyme:** {data['synonyms']}\n\n"
    response += f"💡 **Beispiele ({level}):**\n"
    for ex in examples:
        response += f"• {ex}\n"
    response += f"\n📝 **Grammatik:** {data['grammar_notes']}"

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Mehr Beispiele", callback_data=f"more_ex_{word}"))
    markup.add(types.InlineKeyboardButton("Synonyme", callback_data=f"syn_{word}"))
    markup.add(types.InlineKeyboardButton("Niveau ändern", callback_data="level"))
    bot.reply_to(message, response, parse_mode='Markdown', reply_markup=markup)

# Inline-Buttons
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "help":
        bot.answer_callback_query(call.id, "Hilfe: /level, /local, /history")
    elif call.data == "level":
        bot.answer_callback_query(call.id, "Niveau mit /level ändern")
    elif call.data.startswith("more_ex_"):
        word = call.data.split("_")[2]
        data = get_german_definition(word) if word not in local_dict else get_local_definition(word)
        if 'examples' in data:
            extra = "\n".join(data['examples'][1:3])
            bot.answer_callback_query(call.id, f"Mehr Beispiele für {word}:\n{extra}")
    elif call.data.startswith("syn_"):
        word = call.data.split("_")[1]
        data = get_german_definition(word) if word not in local_dict else get_local_definition(word)
        bot.answer_callback_query(call.id, f"Synonyme für {word}: {data['synonyms']}")

# Render Webhook
app = Flask(__name__)

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        return 'Unauthorized'

@app.route('/', methods=['GET', 'HEAD'])
def index():
    return '<h1>Deutsches Wörterbuch-Bot online! (@sprachschule67)</h1>'

bot.remove_webhook()
webhook_url = f'https://deutsche360-bot.onrender.com/{TOKEN}'
bot.set_webhook(url=webhook_url)

PORT = int(os.environ.get('PORT', 5000))
app.run(host='0.0.0.0', port=PORT)

print("Deutscher Bot gestartet! (Deutsch zu Deutsch)")
