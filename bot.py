# Deutsches Wörterbuch-Bot verbessert (genaue Artikel, stärkeres Dict)
TOKEN = '8224460982:AAEPMMNfWxFfzqPTcqUCxKI0zJr8IP-dzG4'

# Bibliotheken
import telebot
from telebot import types
import requests
from bs4 import BeautifulSoup
from flask import Flask, request
import os
import json
from lxml import etree  # Für besseres Parse (Artikel)

bot = telebot.TeleBot(TOKEN)

# Erweitertes lokales Wörterbuch (20 gängige Wörter, aus Duden/Wiktionary, Deutsch zu Deutsch)
local_dict = {
    "haus": {
        "article": "das",
        "definition": "Gebäude zum Wohnen. Ein Haus bietet Schutz und Wohnraum für Menschen.",
        "synonyms": "Wohnhaus, Gebäude, Heim, Behausung",
        "examples": {
            "beginner": "Das Haus ist groß. (Einfaches Beispiel: Das Haus steht dort.)",
            "medium": "Ich wohne in einem alten Haus in der Stadt.",
            "advanced": "Das Architektur-Haus von Frank Lloyd Wright ist ein Meisterwerk."
        },
        "grammar": "Neutrum (das Haus), Plural: Häuser. Deklination: dem Hause (Dativ). Geschlecht: neutral. Häufigkeit: sehr hoch."
    },
    "freund": {
        "article": "der",
        "definition": "Person mit enger, freundschaftlicher Beziehung. Ein Freund teilt Freuden und Sorgen.",
        "synonyms": "Kumpel, Genosse, Gefährte, Buddy",
        "examples": {
            "beginner": "Der Freund spielt Fußball.",
            "medium": "Mein bester Freund hilft mir immer.",
            "advanced": "Freunde sind wie Sterne – man sieht sie nicht immer, aber sie sind da."
        },
        "grammar": "Maskulinum (der Freund), Feminin: Freundin (die). Plural: Freunde. Verb: Freundschaft pflegen."
    },
    "auto": {
        "article": "das",
        "definition": "Kraftfahrzeug mit Rädern und Motor. Das Auto revolutionierte den Transport.",
        "synonyms": "Wagen, Fahrzeug, Karre, Automobil",
        "examples": {
            "beginner": "Das Auto fährt schnell.",
            "medium": "Ich parke das Auto in der Garage.",
            "advanced": "Das Elektroauto reduziert CO2-Emissionen erheblich."
        },
        "grammar": "Neutrum (das Auto), Plural: Autos. Abkürzung: PKW. Deklination: dem Auto (Dativ)."
    },
    "buch": {
        "article": "das",
        "definition": "Druckwerk mit Seiten und Inhalt. Ein Buch ist Wissensquelle und Unterhaltung.",
        "synonyms": "Roman, Band, Schrift, Lektüre",
        "examples": {
            "beginner": "Das Buch liegt auf dem Tisch.",
            "medium": "Ich lese ein spannendes Buch.",
            "advanced": "Das Buch 'Faust' von Goethe ist ein Klassiker der Literatur."
        },
        "grammar": "Neutrum (das Buch), Plural: Bücher. Verb: lesen, schreiben. Umlaut: Buch → Bücher."
    },
    "liebe": {
        "article": "die",
        "definition": "Tiefe Zuneigung zu einer Person oder Sache. Liebe ist ein universelles Gefühl.",
        "synonyms": "Affektion, Zärtlichkeit, Leidenschaft, Hingabe",
        "examples": {
            "beginner": "Die Liebe macht glücklich.",
            "medium": "Ich fühle tiefe Liebe zu meiner Familie.",
            "advanced": "Romantische Liebe wird in der Poesie oft idealisiert."
        },
        "grammar": "Femininum (die Liebe), Plural: Lieben. Verb: lieben (ich liebe). Idiomatisch: Liebe siegt."
    },
    "essen": {
        "article": "das",
        "definition": "Nahrungsaufnahme durch Kauen und Schlucken. Essen ist essenziell fürs Überleben.",
        "synonyms": "Mahlzeit, Speise, Nahrung, Mahl",
        "examples": {
            "beginner": "Ich esse ein Apfel.",
            "medium": "Wir essen zu Abend in der Küche.",
            "advanced": "Ausgewogenes Essen verhindert Krankheiten."
        },
        "grammar": "Verb (essen), unregelmäßig: essen – aß – gegessen. Präsens: ich esse, du isst. Substantiv: das Essen (Mittagessen)."
    },
    "gehen": {
        "article": "",
        "definition": "Fortbewegung mit den Füßen. Gehen ist die einfachste Form der Mobilität.",
        "synonyms": "Laufen, Schreiten, Wandern, Spazieren",
        "examples": {
            "beginner": "Ich gehe in die Schule.",
            "medium": "Geh nicht so schnell, bitte.",
            "advanced": "Er geht täglich eine Stunde spazieren, um fit zu bleiben."
        },
        "grammar": "Verb (gehen), schwach: gehen – ging – gegangen. Präsens: ich gehe, du gehst. Separabel: ausgehen."
    },
    "schule": {
        "article": "die",
        "definition": "Bildungseinrichtung für Kinder und Jugendliche. Die Schule vermittelt Wissen.",
        "synonyms": "Lernanstalt, Unterricht, Bildungszentrum",
        "examples": {
            "beginner": "Die Schule beginnt um acht Uhr.",
            "medium": "Ich lerne viel in der Schule.",
            "advanced": "Die Reform der Schule zielt auf Inklusion ab."
        },
        "grammar": "Femininum (die Schule), Plural: Schulen. Kompositum: Schulleiter, Schulzeit."
    },
    "wasser": {
        "article": "das",
        "definition": "Geruchlose Flüssigkeit. Wasser ist die Basis des Lebens.",
        "synonyms": "H2O, Flüssigkeit, Getränk",
        "examples": {
            "beginner": "Das Wasser ist kalt.",
            "medium": "Trink viel Wasser am Tag.",
            "advanced": "Das Trinkwasser muss gereinigt werden, um gesund zu sein."
        },
        "grammar": "Neutrum (das Wasser), kein Plural. Deklination: dem Wasser (Dativ). Kompositum: Meerwasser."
    },
    "freundin": {
        "article": "die",
        "definition": "Weibliche Freundin. Eine Freundin teilt Interessen und Geheimnisse.",
        "synonyms": "Bekannte, Gefährtin, Komplizin",
        "examples": {
            "beginner": "Die Freundin kommt zu Besuch.",
            "medium": "Meine Freundin und ich gehen einkaufen.",
            "advanced": "Eine gute Freundin ist unbezahlbar in schwierigen Zeiten."
        },
        "grammar": "Femininum (die Freundin), Plural: Freundinnen. Diminutiv: Freundinchen."
    },
    "arbeit": {
        "article": "die",
        "definition": "Tätigkeit zur Erwerbsgewinnung. Arbeit gibt Struktur und Sinn.",
        "synonyms": "Beruf, Job, Beschäftigung",
        "examples": {
            "beginner": "Die Arbeit ist schwer.",
            "medium": "Ich gehe zur Arbeit.",
            "advanced": "Flexible Arbeitformen werden immer populärer."
        },
        "grammar": "Femininum (die Arbeit), Plural: Arbeiten. Verb: arbeiten."
    },
    "zeit": {
        "article": "die",
        "definition": "Fortschreitende Abfolge von Momenten. Zeit ist relativ.",
        "synonyms": "Dauer, Augenblick, Epoche",
        "examples": {
            "beginner": "Die Zeit vergeht schnell.",
            "medium": "Ich habe keine Zeit.",
            "advanced": "Zeitmanagement ist Schlüssel zum Erfolg."
        },
        "grammar": "Femininum (die Zeit), Plural: Zeiten. Kompositum: Zeitreise."
    },
    "mensch": {
        "article": "der",
        "definition": "Individuum der Spezies Homo sapiens. Der Mensch ist sozial.",
        "synonyms": "Person, Individuum, Individ",
        "examples": {
            "beginner": "Der Mensch ist müde.",
            "medium": "Jeder Mensch hat Rechte.",
            "advanced": "Der moderne Mensch lebt in einer globalisierten Welt."
        },
        "grammar": "Maskulinum (der Mensch), Plural: Menschen. Umlaut: Mensch → Menschen."
    },
    "welt": {
        "article": "die",
        "definition": "Der gesamte Raum und die gesamte Zeit. Die Welt ist vielfältig.",
        "synonyms": "Erde, Kosmos, Universum",
        "examples": {
            "beginner": "Die Welt ist schön.",
            "medium": "Ich reise um die Welt.",
            "advanced": "Die Weltwirtschaft leidet unter Inflation."
        },
        "grammar": "Femininum (die Welt), Plural: Welten. Kompositum: Weltanschauung."
    },
    "leben": {
        "article": "das",
        "definition": "Existenz und Funktionsweise eines Organismus. Leben ist kostbar.",
        "synonyms": "Existenz, Dasein, Vita",
        "examples": {
            "beginner": "Das Leben ist kurz.",
            "medium": "Ich genieße das Leben.",
            "advanced": "Das Leben ist eine Reise, nicht das Ziel."
        },
        "grammar": "Neutrum (das Leben), Plural: Leben. Verb: leben (ich lebe)."
    },
    "tag": {
        "article": "der",
        "definition": "Zeiteinheit von 24 Stunden. Der Tag hat Morgen und Abend.",
        "synonyms": "Tageszeit, Datum, Periode",
        "examples": {
            "beginner": "Der Tag ist sonnig.",
            "medium": "Heute ist ein guter Tag.",
            "advanced": "Der Tag der offenen Tür informiert über das Unternehmen."
        },
        "grammar": "Maskulinum (der Tag), Plural: Tage. Kompositum: Tagtraum."
    },
    "nacht": {
        "article": "die",
        "definition": "Dunkle Tageshälfte. Die Nacht bringt Ruhe.",
        "synonyms": "Dunkelheit, Abend, Finsternis",
        "examples": {
            "beginner": "Die Nacht ist dunkel.",
            "medium": "Ich schlafe in der Nacht.",
            "advanced": "Die Polar-Nacht dauert monatelang."
        },
        "grammar": "Femininum (die Nacht), Plural: Nächte. Umlaut: Nacht → Nächte."
    },
    "stunde": {
        "article": "die",
        "definition": "Zeiteinheit von 60 Minuten. Die Stunde vergeht schnell.",
        "synonyms": "Zeitspanne, Moment, Viertelstunde",
        "examples": {
            "beginner": "Die Stunde ist lang.",
            "medium": "In einer Stunde komme ich.",
            "advanced": "Die Geschäftsstunde endet um 18 Uhr."
        },
        "grammar": "Femininum (die Stunde), Plural: Stunden. Kompositum: Stundenzahl."
    },
    "jahr": {
        "article": "das",
        "definition": "Zeitraum von 365 Tagen. Das Jahr hat 12 Monate.",
        "synonyms": "Jahreszeit, Kalenderjahr, Periode",
        "examples": {
            "beginner": "Das Jahr ist neu.",
            "medium": "Im nächsten Jahr reise ich.",
            "advanced": "Das Fiskaljahr endet im Dezember."
        },
        "grammar": "Neutrum (das Jahr), Plural: Jahre. Kompositum: Jahreszeiten."
    },
    "wort": {
        "article": "das",
        "definition": "Sprachzeichen zur Bedeutungsvermittlung. Ein Wort drückt Gedanken aus.",
        "synonyms": "Begriff, Ausdruck, Terminus",
        "examples": {
            "beginner": "Das Wort ist kurz.",
            "medium": "Lies das Wort laut.",
            "advanced": "Das Wort 'Demokratie' stammt aus dem Griechischen."
        },
        "grammar": "Neutrum (das Wort), Plural: Worte. Verb: sagen, schreiben."
    }
}

# Benutzerdaten
user_levels = {}
user_history = {}

# Wiktionary-API verbessert (besseres Artikel-Parse)
def get_german_definition(word):
    url = f"https://de.wiktionary.org/w/api.php"
    params = {
        'action': 'parse',
        'format': 'json',
        'page': word,
        'prop': 'text',
        'section': 0  # Erste Sektion (Substantiv)
    }
    headers = {
        'User-Agent': 'GermanDictBot/1.0 (Educational bot; @sprachschule67)'
    }
    try:
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if 'parse' in data:
                text = data['parse']['text']['*']
                soup = BeautifulSoup(text, 'html.parser')
                
                # Artikel extrahieren (aus {{Substantiv|...}} oder Text)
                article = 'unbekannt'
                article_tags = soup.find_all('strong') or soup.find_all(string=lambda text: text and ('der ' in text or 'die ' in text or 'das ' in text))
                if article_tags:
                    art_text = article_tags[0].get_text().lower() if hasattr(article_tags[0], 'get_text') else article_tags[0]
                    if 'der ' in art_text:
                        article = 'der'
                    elif 'die ' in art_text:
                        article = 'die'
                    elif 'das ' in art_text:
                        article = 'das'
                
                # Definition (erster Absatz, gekürzt)
                def_par = soup.find('p')
                definition = def_par.get_text().strip()[:250] + '...' if def_par and len(def_par.get_text()) > 250 else def_par.get_text().strip() if def_par else 'Definition nicht gefunden'
                
                # Synonyme (aus {{Synonyme|...}} oder Links)
                synonyms = []
                syn_section = soup.find(string=lambda text: 'synonyme' in text.lower())
                if syn_section:
                    syn_soup = BeautifulSoup(str(syn_section.parent), 'html.parser')
                    syn_links = syn_soup.find_all('a')
                    for link in syn_links[:4]:
                        syn = link.get_text().strip()
                        if syn and syn.lower() not in [word.lower(), 'wiktionary']:
                            synonyms.append(syn)
                synonyms_str = ', '.join(synonyms) if synonyms else 'Nicht gefunden'
                
                # Beispiele (Sätze aus Text)
                examples = []
                sentences = soup.find_all('li') or [p for p in soup.find_all('p') if len(p.get_text()) > 20]
                for sent in sentences[:3]:
                    ex = sent.get_text().strip()[:100] + '.'
                    if len(ex) > 10:
                        examples.append(ex)
                if not examples:
                    examples = [f"Beispiel: {definition[:50]}."]
                
                grammar_notes = f"Artikel: {article}. Plural/Deklination: Siehe detaillierte Grammatik in Wiktionary. Häufige Fehler: Artikel vergessen."
                
                return {
                    'word': word.capitalize(),
                    'definition': definition,
                    'article': article,
                    'synonyms': synonyms_str,
                    'examples': examples,
                    'grammar_notes': grammar_notes,
                    'source': 'Wiktionary (verbessert)'
                }
            else:
                return {'error': f'Wort "{word}" nicht gefunden. Versuche ähnliche Wörter wie "Haus" oder "Freund".'}
        else:
            return {'error': f'API-Fehler (Code: {response.status_code}). Verwende /local.'}
    except Exception as e:
        return {'error': f'Fehler: {str(e)} – Fallback zu local.'}

# Lokale Definition (stark erweitert)
def get_local_definition(word, message):
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
            'source': 'Local (erweitert)'
        }
    else:
        return {'error': f'Wort "{word}" nicht im lokalen Wörterbuch. Füge es hinzu oder verwende /local.'}

# /start (verbessert)
@bot.message_handler(commands=['start'])
def start_message(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Hilfe", callback_data="help"))
    markup.add(types.InlineKeyboardButton("Lokales Dict", callback_data="local_list"))
    bot.reply_to(message, "Hallo! Deutsches Wörterbuch verbessert.\n\nBefehle:\n/level beginner\n/local\n/history\n\nSchicke ein Wort!", reply_markup=markup)

# /level
@bot.message_handler(commands=['level'])
def set_level(message):
    level = message.text.split()[1].lower() if len(message.text.split()) > 1 else 'medium'
    if level in ['beginner', 'medium', 'advanced']:
        user_levels[message.from_user.id] = level
        bot.reply_to(message, f"Niveau {level} gesetzt! Beispiele angepasst.")
    else:
        bot.reply_to(message, "Niveaus: beginner, medium, advanced")

# /local
@bot.message_handler(commands=['local'])
def local_mode(message):
    markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    for word in list(local_dict.keys())[:6]:  # Mehr Wörter
        markup.add(types.KeyboardButton(word))
    bot.reply_to(message, "Lokales Wörterbuch (20 Wörter): Wähle ein Wort!", reply_markup=markup)

# /history
@bot.message_handler(commands=['history'])
def show_history(message):
    hist = user_history.get(message.from_user.id, [])
    if hist:
        response = "Letzte 5 Wörter:\n" + "\n".join([w.capitalize() for w in hist[-5:]])
        bot.reply_to(message, response)
    else:
        bot.reply_to(message, "Verlauf leer!")

# Wortsuche (verbessert)
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    word = message.text.strip().lower()
    user_id = message.from_user.id
    if word in ['/start', '/level', '/local', '/history']:
        return
    
    if len(word) < 2:
        bot.reply_to(message, "Wort mit mind. 2 Buchstaben!")
        return

    # History
    if user_id not in user_history:
        user_history[user_id] = []
    if word not in user_history[user_id]:
        user_history[user_id].append(word)
        if len(user_history[user_id]) > 10:
            user_history[user_id] = user_history[user_id][-10:]

    data = get_german_definition(word)
    if 'error' in data:
        data = get_local_definition(word, message)
        if 'error' in data:
            bot.reply_to(message, data['error'])
            return

    # Beispiele filtern
    level = user_levels.get(user_id, 'medium')
    examples = data['examples'][:1] if level == 'beginner' else data['examples'][:2] if level == 'medium' else data['examples'][:3]

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
    markup.add(types.InlineKeyboardButton("Synonyme erweitert", callback_data=f"syn_{word}"))
    bot.reply_to(message, response, parse_mode='Markdown', reply_markup=markup)

# Buttons
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "help":
        bot.answer_callback_query(call.id, "Hilfe: /level, /local, /history")
    elif call.data == "local_list":
        bot.answer_callback_query(call.id, "Verwende /local für Liste")
    elif call.data.startswith("more_ex_"):
        word = call.data.split("_")[2]
        data = get_german_definition(word) if word not in local_dict else get_local_definition(word, None)
        extra = "\n".join(data['examples'][1:4] if 'examples' in data else ["Keine weiteren Beispiele"])
        bot.answer_callback_query(call.id, f"Mehr Beispiele: {extra}")
    elif call.data.startswith("syn_"):
        word = call.data.split("_")[1]
        data = get_german_definition(word) if word not in local_dict else get_local_definition(word, None)
        bot.answer_callback_query(call.id, f"Synonyme: {data['synonyms']}")

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
    return '<h1>Deutsches Wörterbuch verbessert! (@sprachschule67)</h1>'

bot.remove_webhook()
webhook_url = f'https://deutsche360-bot.onrender.com/{TOKEN}'
bot.set_webhook(url=webhook_url)

PORT = int(os.environ.get('PORT', 5000))
app.run(host='0.0.0.0', port=PORT)

print("Verbesserter Bot gestartet! (Genauer Artikel)")
