import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
import json
import os
import threading

# --- কনফিগারেশন ---
# আপনার বটফাদারের API KEY এখানে দিন। এটি গোপন রাখবেন।
API_KEY = '8481301472:AAHMjqA8DcldWqzvUrlgtdD-K5ToTKW0hck'

# --- ★★★ আসল সমাধান এখানে ★★★ ---
# ফাইলের জন্য একটি নির্দিষ্ট এবং পূর্ণাঙ্গ পাথ তৈরি করা হলো
# এটি নিশ্চিত করবে যে keywords.json ফাইলটি সব সময় main.py ফাইলের পাশেই থাকবে
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(SCRIPT_DIR, 'keywords.json')
# --- ★★★ পরিবর্তন শেষ ★★★ ---

# --- বট এবং ডেটা শুরু করা ---
bot = telebot.TeleBot(API_KEY)

keywords = {}
data_lock = threading.Lock()
user_states = {}

# --- ডেটা লোড এবং সেভ করার ফাংশন ---

def load_data():
    """ফাইল থেকে কীওয়ার্ড লোড করে মেমোরিতে আনে।"""
    global keywords
    with data_lock:
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    keywords = json.load(f)
                    print(f"ডেটা সফলভাবে লোড হয়েছে {DATA_FILE} থেকে।")
            except json.JSONDecodeError:
                keywords = {}
                print("সতর্কবার্তা: JSON ফাইলটি পড়া যায়নি, খালি ডেটা দিয়ে শুরু হচ্ছে।")
        else:
            keywords = {}
            print("কোনো ডেটা ফাইল পাওয়া যায়নি, খালি ডেটা দিয়ে শুরু হচ্ছে।")

def save_data():
    """বর্তমান কীওয়ার্ডগুলো মেমোরি থেকে ফাইলে সেভ করে।"""
    with data_lock:
        with open(DATA_FILE, 'w') as f:
            json.dump(keywords, f, indent=4)
    print(f"ডেটা সফলভাবে সেভ হয়েছে {DATA_FILE} ফাইলে।")

# --- স্টেট ম্যানেজমেন্ট এবং অন্যান্য হ্যান্ডলার (এগুলো অপরিবর্তিত) ---

def get_user_state(user_id):
    return user_states.get(user_id)

def set_user_state(user_id, state, data=None):
    if state is None:
        if user_id in user_states:
            del user_states[user_id]
    else:
        user_states[user_id] = {'state': state, 'data': data}

@bot.message_handler(commands=['start'])
def handle_start(message):
    set_user_state(message.from_user.id, None)
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Start Adding", callback_data="add_keyword_start"))
    bot.send_message(message.chat.id,
        "Welcome to the *AiTricker Bot!*\n"
        "I can help you auto-reply in your Telegram group using keywords.\n\n"
        "➤ Join our Telegram Group: coming soon"
        "➤ Subscribe to our YouTube Channel: coming soon"
        "*Tap 'Start Adding' below to add a keyword + link.*",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.message_handler(commands=['list'])
def handle_list(message):
    set_user_state(message.from_user.id, None)
    with data_lock:
        if keywords:
            msg_parts = ["*Stored Keywords:*"]
            for key, value in keywords.items():
                value_preview = (value[:30] + '...') if len(value) > 30 else value
                msg_parts.append(f"➤ `{key}` → {value_preview}")
            msg = "\n".join(msg_parts)
            bot.send_message(message.chat.id, msg, parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, "এখনো কোনো কীওয়ার্ড সেভ করা হয়নি।")

@bot.message_handler(commands=['remove'])
def handle_remove(message):
    set_user_state(message.from_user.id, 'awaiting_keyword_to_remove')
    bot.send_message(message.chat.id, "যে কীওয়ার্ডটি ডিলিট করতে চান সেটি টাইপ করুন।\nবাতিল করতে /cancel টাইপ করুন।")

@bot.message_handler(commands=['settings'])
def handle_settings(message):
    set_user_state(message.from_user.id, None)
    bot.send_message(message.chat.id, "সেটিংস ফিচারটি খুব শীঘ্রই আসছে...")

@bot.message_handler(commands=['cancel'])
def handle_cancel(message):
    if get_user_state(message.from_user.id):
        set_user_state(message.from_user.id, None)
        bot.send_message(message.chat.id, "কাজটি বাতিল করা হয়েছে।")
    else:
        bot.send_message(message.chat.id, "আপনি এখন কোনো কাজ করছেন না।")

@bot.callback_query_handler(func=lambda call: call.data == "add_keyword_start")
def callback_add_keyword(call):
    bot.answer_callback_query(call.id)
    set_user_state(call.from_user.id, 'awaiting_keyword')
    bot.send_message(call.message.chat.id, "আপনার নতুন কীওয়ার্ডটি টাইপ করুন।\nবাতিল করতে /cancel টাইপ করুন।")

@bot.message_handler(func=lambda message: get_user_state(message.from_user.id) is not None, content_types=['text'])
def handle_stateful_messages(message):
    user_id = message.from_user.id
    state_info = user_states.get(user_id)
    state = state_info['state']

    if state == 'awaiting_keyword':
        keyword = message.text.strip().lower()
        if not keyword:
            bot.send_message(user_id, "কীওয়ার্ড খালি হতে পারে না। আবার চেষ্টা করুন অথবা /cancel টাইপ করুন।")
            return
        set_user_state(user_id, 'awaiting_response', data={'keyword': keyword})
        bot.send_message(user_id, f"খুব ভালো। এখন `{keyword}` কীওয়ার্ডটির জন্য মেসেজ বা লিঙ্ক পাঠান।\nবাতিল করতে /cancel টাইপ করুন।")

    elif state == 'awaiting_response':
        keyword = state_info['data']['keyword']
        response = message.text.strip()
        with data_lock:
            keywords[keyword] = response
        save_data()
        bot.send_message(user_id, "✅ আপনার কীওয়ার্ড সফলভাবে সেভ হয়েছে।")
        set_user_state(user_id, None)

    elif state == 'awaiting_keyword_to_remove':
        keyword_to_remove = message.text.strip().lower()
        with data_lock:
            if keyword_to_remove in keywords:
                del keywords[keyword_to_remove]
                save_data()
                bot.send_message(user_id, f"✅ কীওয়ার্ড `{keyword_to_remove}` ডিলিট করা হয়েছে।")
            else:
                bot.send_message(user_id, "কীওয়ার্ডটি খুঁজে পাওয়া যায়নি। আবার চেষ্টা করুন অথবা /cancel টাইপ করুন।")
        set_user_state(user_id, None)

@bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup'], content_types=['text'])
def handle_group_messages(message):
    if get_user_state(message.from_user.id):
        return
    key = message.text.strip().lower()
    with data_lock:
        if key in keywords:
            bot.reply_to(message, keywords[key])

# --- বট চালু করা ---
if __name__ == '__main__':
    load_data()
    bot.set_my_commands([
        BotCommand("/start", "বটটি শুরু করুন"),
        BotCommand("/list", "সমস্ত কীওয়ার্ড দেখুন"),
        BotCommand("/remove", "কীওয়ার্ড ডিলিট করুন"),
        BotCommand("/settings", "বটের সেটিংস"),
        BotCommand("/cancel", "চলমান কাজ বাতিল করুন"),
    ])
    print("বট চলছে...")
    bot.infinity_polling(skip_pending=True)
