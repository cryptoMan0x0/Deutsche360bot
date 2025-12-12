# بات دیکشنری آلمانی به آلمانی با Wiktionary API (webhook برای Render)
TOKEN = '8224460982:AAEPMMNfWxFfzqPTcqUCxKI0zJr8IP-dzG4'  # Tokenت

# کتابخونه‌ها
import telebot
import requests
from bs4 import BeautifulSoup
from flask import Flask, request
import os

bot = telebot.TeleBot(TOKEN)

# تابع برای گرفتن داده از Wiktionary API (با header)
def get_german_definition(word):
    # URL API Wiktionary
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
    # Header برای حل 403
    headers = {
        'User-Agent': 'GermanDictBot/1.0 (Personal educational bot by @sprachschule67; contact: @sprachschule67)'
    }
    try:
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            pages = data['query'].get('pages', {})
            if pages and not str(list(pages.keys())[0]).startswith('-1'):  # اگر صفحه پیدا شد
                page = list(pages.values())[0]
                extract = page.get('extract', 'تعریف پیدا نشد').strip()
                
                # پارس ساده با BeautifulSoup
                soup = BeautifulSoup(extract, 'html.parser') if extract else None
                text = soup.get_text() if soup else extract
                
                # استخراج آرتیکل (der/die/das)
                article = 'نامشخص'
                lower_text = text.lower()
                if 'der ' in lower_text[:20]:
                    article = 'der'
                elif 'die ' in lower_text[:20]:
                    article = 'die'
                elif 'das ' in lower_text[:20]:
                    article = 'das'
                
                # تعریف اصلی
                definition = text[:250] + '...' if len(text) > 250 else text
                
                # مترادف‌ها (از لینک‌ها)
                synonyms = []
                if 'links' in page:
                    for link in page['links'][:5]:
                        if link['title'] != word and ':' not in link['title'] and len(link['title']) > 2:
                            synonyms.append(link['title'])
                synonyms_str = ', '.join(synonyms[:3]) if synonyms else 'پیدا نشد (در Wiktionary چک کن)'
                
                # مثال‌ها (جملات ساده از متن)
                examples = []
                sentences = [s.strip() + '.' for s in text.split('.') if len(s.strip()) > 15][:4]
                if not sentences:
                    examples = [f"مثال برای {word}: {definition[:80]}..."]
                else:
                    examples = sentences
                
                # نکات گرامری
                grammar_notes = f"آرتیکل: {article}. برای مبتدی: آرتیکل حفظ کن. متوسط: جملات رو بساز. پیشرفته: مترادف‌ها رو استفاده کن. جمع/صرف: در Wiktionary جزئیات."
                
                return {
                    'word': word.capitalize(),
                    'definition': definition,
                    'article': article,
                    'synonyms': synonyms_str,
                    'examples': examples[:3],
                    'grammar_notes': grammar_notes
                }
            else:
                return {'error': f'کلمه "{word}" در Wiktionary آلمانی پیدا نشد!'}
        else:
            return {'error': f'خطا در اتصال به Wiktionary (کد: {response.status_code}). ممکنه موقت باشه – بعداً امتحان کن یا /local بزن.'}
    except Exception as e:
        return {'error': f'خطا: {str(e)} (اینترنت یا VPN چک کن)'}

# /start
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.reply_to(message, "سلام! بات با User-Agent (@sprachschule67) بروز شد. کلمه آلمانی بفرست (مثل 'Haus' یا 'Freund'). اگر 403 موند، بگو /local بزنم! 🌍")

# هر پیام (سرچ کلمه)
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    word = message.text.strip().lower()
    if word == '/start':
        return
    
    if len(word) < 2:
        bot.reply_to(message, "لطفاً کلمه‌ای با حداقل ۲ حرف بفرست!")
        return
    
    bot.reply_to(message, "در حال جستجو در Wiktionary... ⏳ (چند ثانیه)")
    
    data = get_german_definition(word)
    
    if 'error' in data:
        bot.reply_to(message, f"❌ {data['error']}\nکلمه دیگه‌ای امتحان کن، یا /local برای حالت محلی (بدون API).")
    else:
        # پاسخ زیبا
        response = f"📖 **{data['word']}**\n\n"
        response += f"📰 **آرتیکل:** {data['article']} {data['word']}\n\n"
        response += f"📚 **تعریف (به آلمانی):** {data['definition']}\n\n"
        response += f"🔄 **مترادف‌ها:** {data['synonyms']}\n\n"
        response += f"💡 **مثال‌ها (برای سطوح مختلف):**\n"
        levels = ['مبتدی', 'متوسط', 'پیشرفته']
        for i, ex in enumerate(data['examples']):
            level = levels[min(i, 2)]
            response += f"• {level}: {ex}\n"
        response += f"\n📝 **نکات گرامری:** {data['grammar_notes']}\n\n"
        response += "منبع: de.wiktionary.org. عالی برای زبان‌آموزها! (بات توسط @sprachschule67)"
        
        bot.reply_to(message, response, parse_mode='Markdown')

# برای Render: webhook mode (حل ports)
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
    return '<h1>بات دیکشنری آلمانی آنلاین! (@sprachschule67)</h1>'

# شروع webhook
bot.remove_webhook()
webhook_url = f'https://deutsche360-bot.onrender.com/{TOKEN}'
bot.set_webhook(url=webhook_url)

# اجرای سرور (باز کردن پورت)
PORT = int(os.environ.get('PORT', 5000))
app.run(host='0.0.0.0', port=PORT)

print("بات با webhook شروع شد! (برای Render)")
