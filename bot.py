# ... (همه کد گام ۵ قبلی – فقط این بخش audio رو بروز کن برای gtts 2.5.4)

# Step 4: gTTS Audio (updated for v2.5.4)
def get_audio_file(word):
    print(f"Debug: gTTS audio for '{word}' (v2.5.4)")
    try:
        tts = gTTS(text=f"{word.capitalize()}, Deutsche Aussprache", lang='de', slow=False)
        mp3_buffer = BytesIO()
        tts.write_to_fp(mp3_buffer)
        mp3_buffer.seek(0)
        print(f"Debug: gTTS v2.5.4 success for '{word}'")
        return mp3_buffer
    except Exception as e:
        print(f"Debug: gTTS error v2.5.4: {str(e)}")
        return None

# در callback_query, audio_ بخش:
elif data.startswith('audio_'):
    bot.answer_callback_query(call.id, "Audio generiert... (gTTS 2.5.4)")
    audio_buffer = get_audio_file(word)
    if audio_buffer:
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_voice(call.message.chat.id, audio_buffer, caption=f"Aussprache '{word}' (Step 4 fixed)")
    else:
        bot.answer_callback_query(call.id, "Audio fehlgeschlagen. /audio {word} probieren.")

# /audio command:
@bot.message_handler(commands=['audio'])
def send_audio(message):
    parts = message.text.split()
    word = parts[1].lower() if len(parts) > 1 else 'blau'
    audio_buffer = get_audio_file(word)
    if audio_buffer:
        bot.send_voice(message.chat.id, audio_buffer, caption=f"Aussprache '{word}' (gTTS 2.5.4)")
    else:
        bot.reply_to(message, f"Audio fehlgeschlagen für '{word}'. Häufiges Wort versuchen.")

# ... (بقیه کد گام ۵ – local_dict 20 words, /daily, /stats, etc.)
