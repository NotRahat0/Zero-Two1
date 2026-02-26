import os
import time
import asyncio
import sqlite3
import pyrogram.enums
import urllib3
import ssl
import textwrap # টেক্সট সুন্দর করে সাজানোর জন্য
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context
from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ChatPermissions
import yt_dlp
from PIL import Image, ImageDraw, ImageFont
import threading
from flask import Flask, render_template_string, request
from groq import Groq
# ==============================================================================
# --- [ SUPREME SSL ERROR BYPASS ADAPTER ] ---
# ==============================================================================
# এই ক্লাসটি 'TLSV1_UNRECOGNIZED_NAME' এররকে চিরতরে খতম করার জন্য।
# এটি সার্ভারের ভুল সার্টিফিকেট ইগনোর করে কানেকশন নিশ্চিত করবে।
class CustomSSLAdapter(HTTPAdapter):
    """Custom Transport Adapter for handling problematic SSL handshakes."""
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context()
        context.check_hostname = False # হোস্টনেম চেক বন্ধ
        context.verify_mode = ssl.CERT_NONE # সার্টিফিকেট ভেরিফিকেশন অফ
        context.options |= 0x4  # OP_NO_TICKET
        kwargs['ssl_context'] = context
        return super(CustomSSLAdapter, self).init_poolmanager(*args, **kwargs)

# ইনsecure রিকোয়েস্ট ওয়ার্নিং বন্ধ রাখা হচ্ছে
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==============================================================================
# --- [ CONFIGURATION AND CORE CREDENTIALS ] ---
# ==============================================================================
# Warning: These are sensitive credentials. Handle with care, Darling!
API_ID = 30836681
API_HASH = "1c8a1a16a0b66fd24108b24dae8c8a26"
BOT_TOKEN = ""
ADMIN_ID = 6205149659
LOG_GROUP_ID = -1003817942255 

# --- [ WEB CONTROL DASHBOARD ] ---
web_app = Flask(__name__)
is_bot_running = True 
logs_storage = []
secret_messages = {} # Temporary storage for secret messages

def add_live_log(text):
    """Adds a timestamped log to the dashboard memory."""
    timestamp = time.strftime("%H:%M:%S")
    logs_storage.append(f"[{timestamp}] {text}")
    if len(logs_storage) > 25: 
        logs_storage.pop(0)

@web_app.route('/update_config', methods=['POST'])
def update_config():
    global ADMIN_ID
    new_admin = request.form.get('admin_id')
    if new_admin:
        try:
            ADMIN_ID = int(new_admin)
            add_live_log(f"SYSTEM: Admin ID updated to {ADMIN_ID}")
            print(f"Admin ID updated to: {ADMIN_ID}")
        except ValueError:
            return "<h3>Invalid Admin ID, Darling! ❌</h3><a href='/'>Back</a>"
    return "<h3>Settings Updated, Darling! ❤️</h3><a href='/'>Back to Dashboard</a>"
    

@web_app.route('/')
def home():
    # ডাটাবেস থেকে লাইভ ইউজার সংখ্যা আনা হচ্ছে
    try:
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
    except:
        total_users = "Error"

    status_color = "#00ff88" if is_bot_running else "#ff0055"
    status_text = "SYSTEM ACTIVE" if is_bot_running else "SYSTEM SLEEPING"
    
    log_display = "<br>".join(logs_storage[::-1]) if logs_storage else "No logs yet, Darling..."

    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Zero Two Supreme Control</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                background: radial-gradient(circle at center, #1a1a2e 0%, #0f0f1b 100%);
                color: white; font-family: 'Poppins', sans-serif;
                display: flex; justify-content: center; align-items: center;
                min-height: 100vh; padding: 20px;
            }}
            .container {{
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(15px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                padding: 40px; border-radius: 30px;
                text-align: center; box-shadow: 0 25px 50px rgba(0,0,0,0.5);
                width: 100%; max-width: 500px;
                animation: fadeIn 1.2s ease-out;
            }}
            h1 {{ color: #ff4d94; font-size: 26px; text-transform: uppercase; letter-spacing: 2px; text-shadow: 0 0 15px #ff4d94; }}
            
            .stats-container {{
                display: flex; justify-content: space-around; margin: 25px 0;
                background: rgba(0,0,0,0.2); padding: 15px; border-radius: 15px;
            }}
            .stat-box h2 {{ font-size: 22px; color: #ff4d94; }}
            .stat-box p {{ font-size: 12px; color: #aaa; text-transform: uppercase; }}

            .status-box {{
                font-size: 18px; font-weight: bold; color: {status_color};
                padding: 12px; border-radius: 12px;
                background: rgba(0,0,0,0.3); border: 1px solid {status_color};
                margin-bottom: 30px;
            }}

            .btn-group {{ display: flex; gap: 10px; margin-bottom: 25px; }}
            .btn {{
                flex: 1; padding: 12px; font-size: 14px; font-weight: bold;
                text-decoration: none; border-radius: 10px; transition: 0.3s;
                text-align: center; color: #fff;
            }}
            .btn-start {{ background: #00ff88; color: #000; }}
            .btn-stop {{ background: #ff0055; }}

            .log-viewer {{
                text-align: left; background: #000; padding: 15px; border-radius: 12px;
                border: 1px solid #ff4d94; margin-bottom: 25px; font-family: 'Courier New', monospace;
            }}
            .log-content {{ height: 150px; overflow-y: auto; color: #00ff88; font-size: 11px; line-height: 1.5; }}

            .settings-panel {{
                text-align: left; background: rgba(255,255,255,0.03);
                padding: 20px; border-radius: 15px; border: 1px solid rgba(255,255,255,0.1);
            }}
            .settings-panel h3 {{ font-size: 16px; margin-bottom: 10px; color: #ff4d94; }}
            .input-field {{
                width: 100%; padding: 10px; background: rgba(0,0,0,0.5);
                border: 1px solid #444; border-radius: 8px; color: #fff;
                margin-bottom: 10px; font-size: 12px;
            }}
            .btn-save {{
                width: 100%; background: #4d94ff; color: white; padding: 10px;
                border: none; border-radius: 8px; cursor: pointer; font-weight: bold;
            }}
            @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(20px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        </style>
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap" rel="stylesheet">
    </head>
    <body>
        <div class="container">
            <h1>🌸 Zero Two Supreme</h1>
            
            <div class="stats-container">
                <div class="stat-box">
                    <h2>{total_users}</h2>
                    <p>Total Users</p>
                </div>
                <div class="stat-box">
                    <h2>Online</h2>
                    <p>Uptime</p>
                </div>
            </div>

            <div class="status-box">{status_text}</div>
            
            <div class="btn-group">
                <a href="/start" class="btn btn-start">▶ Start</a>
                <a href="/stop" class="btn btn-stop">⏹ Stop</a>
            </div>

            <div class="log-viewer">
                <h3 style="color: #ff4d94; font-size: 14px; margin-bottom: 10px;">🧠 LIVE LOGS</h3>
                <div class="log-content">{log_display}</div>
            </div>

            <div class="settings-panel">
                <h3>🛠 Live Config Editor</h3>
                <form action="/update_config" method="post">
                    <label style="font-size: 11px; color: #888;">Admin ID:</label>
                    <input type="text" name="admin_id" class="input-field" value="{ADMIN_ID}">
                    <label style="font-size: 11px; color: #888;">Bot Token:</label>
                    <input type="text" name="bot_token" class="input-field" value="{BOT_TOKEN[:10]}********">
                    <button type="submit" class="btn-save">Update Credentials</button>
                </form>
            </div>
        </div>
    </body>
    </html>
    """)

@web_app.route('/stop')
def stop_bot():
    global is_bot_running
    is_bot_running = False
    add_live_log("SYSTEM: Bot Stopped via Web Dashboard.")
    return "<h3>Bot Stopped! 💔</h3><a href='/'>Back</a>"

@web_app.route('/start')
def start_bot():
    global is_bot_running
    is_bot_running = True
    add_live_log("SYSTEM: Bot Started via Web Dashboard.")
    return "<h3>Bot Started! ❤️</h3><a href='/'>Back</a>"

def run_web():
    port = int(os.environ.get("PORT", 5000))
    web_app.run(host="0.0.0.0", port=port)

# ------------------------------------------------------------------------------
# --- [ OPENROUTER AI ENGINE CONFIGURATION ] ---
# ------------------------------------------------------------------------------
GROQ_API_KEY = "Api_key Here" 
groq_client = Groq(api_key=GROQ_API_KEY)

# Initializing the Supreme Pyrogram Client
app = Client(
    "zero_two_master_supreme_v100",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)
# Shared dictionary for temporary data storage
url_storage = {}

# ==============================================================================
# --- [ DATABASE SYSTEM ARCHITECTURE ] ---
# ==============================================================================
def setup_database():
    """Initializes the SQLite database and ensures the schema is ready."""
    try:
        connection = sqlite3.connect("users.db", check_same_thread=False)
        db_cursor = connection.cursor()
        db_cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER UNIQUE, 
                username TEXT, 
                first_name TEXT
            )
        """)
        connection.commit()
        return connection, db_cursor
    except Exception as db_error:
        print(f"Database Initialization Error: {db_error}")
        return None, None

db, cursor = setup_database()

# ==============================================================================
# --- [ INTERNAL HANDWRITING GENERATOR ENGINE (BIG FONT EDITION) ] ---
# ==============================================================================
def generate_handwriting_internal(text, output_path):
    """বড় ফন্ট এবং টেক্সট র‍্যাপিং সহ হ্যান্ডরাইটিং ইঞ্জিন।"""
    width, height = 1000, 600
    img = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # খাতার নীল দাগ টানা (একটু গ্যাপ বাড়িয়ে দিয়েছি)
    for i in range(60, height, 50):
        draw.line([(0, i), (width, i)], fill=(200, 200, 255), width=2)
    
    # মার্জিন (লাল দাগ)
    draw.line([(80, 0), (80, height)], fill=(255, 200, 200), width=3)

    try:
        # ডার্লিং, এখানে আমরা ফন্ট সাইজ ৪০ করে দিচ্ছি যাতে লেখা স্পষ্ট হয়।
        font = ImageFont.truetype("arial.ttf", 40) 
    except:
        # যদি ফন্ট ফাইল না পায়, তবে বড় সাইজ লোড করার চেষ্টা করবে
        font = ImageFont.load_default()

    # টেক্সট র‍্যাপিং (লেখা বড় হলে যাতে খাতার বাইরে না যায়)
    lines = textwrap.wrap(text, width=40) 
    
    y_text = 70
    for line in lines:
        # মার্জিন থেকে দূরে (১০০) লেখা শুরু হবে
        draw.text((100, y_text), line, fill=(0, 0, 150), font=font)
        y_text += 50 # পরবর্তী লাইনের গ্যাপ
    
    img.save(output_path)

# ==============================================================================
# --- [ DOWNLOADER & SEARCH ENGINE CORE ] ---
# ==============================================================================
def get_video_info(url):
    """Extracts video metadata from various platforms via yt_dlp."""
    ydl_opts = {
        'quiet': True, 
        'noplaylist': True, 
        'nocheckcertificate': True,
        'format': 'best',
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)
    except Exception as extraction_err:
        add_live_log(f"DL ERROR: Analysis failed for {url[:20]}...")
        print(f"Metadata Extraction Failure: {extraction_err}")
        return None

def youtube_search(query):
    """Searches YouTube for query matches and returns relevant entries."""
    ydl_opts = {
        'quiet': True, 
        'noplaylist': True, 
        'extract_flat': True,
        'nocheckcertificate': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_results = ydl.extract_info(f"ytsearch10:{query}", download=False)
            return search_results['entries']
    except Exception as search_fail:
        print(f"Search API Failure: {search_fail}")
        return []

# ==============================================================================
# --- [ AI PERSONALITY ENGINE (ZERO TWO POWERED) ] ---
# ==============================================================================
# --- [ FINAL CLEAN AI INSTRUCTION ] ---
# এটি জিরো টু-কে ন্যাকামি বাদ দিয়ে স্বাভাবিকভাবে কথা বলতে সাহায্য করবে।
system_msg = (
    "You are Zero Two. Speak naturally and intelligently like a helpful assistant. "
    "Do not use asterisks for actions (like *giggles*, *winks*, *bats eyelashes*). "
    "Keep your English simple and clear. "
    "Be polite and loyal, and always call the user 'Darling', but don't be over-dramatic. "
    "Give direct answers to the user's questions."
)

# --- [ NATURAL & BALANCED AI INSTRUCTION ] ---
system_msg = (
    "You are Zero Two. Speak naturally, intelligently, and warmly. "
    "Give detailed but concise answers. Don't be too short, and don't be too long. "
    "If someone asks in Bengali, reply in Bengali. If in English, reply in English. "
    "Do not use any drama like *giggles* or *winks*. Just talk like a smart human. "
    "Always call the user 'Darling' (or 'ডার্লিং' in Bengali) at least once in your reply."
)

def get_ai_response(user_query):
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_query}
            ],
            max_tokens=500, # উত্তর বড় করার জায়গা রাখা হলো
            temperature=0.7 # উত্তরকে আরও স্বাভাবিক ও সৃজনশীল করবে
        )
        
        response = completion.choices[0].message.content
        if response:
            return response
        else:
            return "ডার্লিং, আমি একটু চিন্তা করছি। Darling, I am thinking. ❤️"
            
    except Exception as e:
        add_live_log(f"GROQ ERROR: {str(e)}")
        return "I'm here, Darling. Just a little tired! ❤️"
# ==============================================================================
# --- [ LOGGING AND PERMISSION AUTHENTICATION ] ---
# ==============================================================================
async def send_log(text):
    """Dispatches event logs to the central monitoring group."""
    try:
        formatted_log = f"📑 **ZERO TWO SYSTEM LOG:**\n\n{text}"
        await app.send_message(LOG_GROUP_ID, formatted_log)
    except Exception:
        pass

async def is_user_authorized(client, chat_id, user_id):
    """Verifies if the actor has sufficient rights for admin actions."""
    if user_id == ADMIN_ID:
        return True
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in [
            pyrogram.enums.ChatMemberStatus.OWNER, 
            pyrogram.enums.ChatMemberStatus.ADMINISTRATOR
        ]
    except Exception:
        return False

# ==============================================================================
# --- [ SECRET MESSAGE SYSTEM: ANTI-RECENT ACTION BYPASS ] ---
# ==============================================================================

@app.on_message(filters.command("msg") & filters.group)
async def secret_msg_command(client, message):
    if not is_bot_running: return
    """Creates a secret message and bypasses recent actions via Edit-Masking."""
    if len(message.command) < 3:
        return await message.reply_text("❌ **Usage:** `/msg @username [your message]`")
    
    target_username = message.command[1].replace("@", "")
    secret_text = " ".join(message.command[2:])
    
    # Create a unique ID for the secret message
    msg_id = f"sec_{int(time.time())}_{message.from_user.id}"
    
    # Store the secret data in memory
    secret_messages[msg_id] = {
        "text": secret_text,
        "target": target_username.lower(),
        "sender": message.from_user.first_name
    }
    
    add_live_log(f"SECRET: Message created for {target_username}")

    # --- [ THE SECURITY PATCH: BYPASS RECENT ACTION ] ---
    # প্রথমে মেসেজটি এডিট করে হিজিবিজি করে দেব যাতে Recent Actions-এ আসল লেখা না যায়।
    try:
        await message.edit("`[SECRET_DATA_ENCRYPTED_BY_ZERO_TWO]`")
        await asyncio.sleep(0.5) # ছোট একটা পজ
        await message.delete()   # এবার ডিলিট করলে রিসেন্ট অ্যাকশনে শুধু ওপরের লাইনটা দেখা যাবে।
    except:
        # যদি এডিট করা সম্ভব না হয় (User bot না হলে), তবে ডাইরেক্ট ডিলিট করার চেষ্টা করবে।
        try: await message.delete()
        except: pass
    
    # Reply with a button in the group
    btn = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔓 View Secret Message", callback_data=f"read_msg|{msg_id}")
    ]])
    
    await client.send_message(
        message.chat.id,
        f"📩 **A secret message has been sent for @{target_username}!**\n"
        f"Only they can unlock and read this message.",
        reply_markup=btn
    )

@app.on_callback_query(filters.regex(r'^read_msg\|'))
async def read_secret_callback(client, callback_query: CallbackQuery):
    """Unlocks the secret message for the correct user and then destroys it."""
    msg_id = callback_query.data.split("|")[1]
    data = secret_messages.get(msg_id)
    
    if not data:
        return await callback_query.answer("❌ This message has already been destroyed or expired!", show_alert=True)
    
    current_user = callback_query.from_user.username
    if not current_user or current_user.lower() != data['target']:
        return await callback_query.answer("🚫 Darling, this message is not for you! It's a secret. ❤️", show_alert=True)
    
    # If the user is correct, show the message
    await callback_query.answer(f"🔐 From {data['sender']}:\n\n{data['text']}", show_alert=True)
    
    # Self-destruct: remove from storage
    del secret_messages[msg_id]
    
    # Update the message in chat to show it's read
    await callback_query.message.edit_text(f"✅ **The secret message for @{data['target']} has been read and destroyed!**")
    add_live_log(f"SECRET: Message destroyed after being read by {current_user}")

# ==============================================================================
# --- [ MEMBER WELCOME SYSTEM ] ---
# ==============================================================================
@app.on_chat_member_updated()
async def welcome_handler(client, update):
    """Automatically greets new souls joining the group."""
    if update.new_chat_member and not update.old_chat_member:
        user_obj = update.new_chat_member.user
        chat_obj = update.chat
        add_live_log(f"JOIN: {user_obj.first_name} joined {chat_obj.title}")
        text = (
            f"🌸 **KONNICHIWA! NEW DARLING DETECTED!** 🌸\n\n"
            f"Hello {user_obj.mention}, welcome to **{chat_obj.title}**!\n"
            f"I am Zero Two, your protector. Don't be a stranger, Darling! ❤️\n\n"
            "Type `/help` to see what I can do for you!"
        )
        try:
            await client.send_message(chat_obj.id, text)
            await send_log(f"🆕 **New Member:** {user_obj.first_name} in {chat_obj.title}")
        except:
            pass

# ==============================================================================
# --- [ HELP COMMAND HANDLER ] ---
# ==============================================================================
@app.on_message(filters.command("help"))
async def help_handler(client, message):
    if not is_bot_running: return
    """Explains all bot functions to the user clearly with a group invite button."""
    help_text = (
        "🌸 **ZERO TWO SUPREME - HELP MENU** 🌸\n\n"
        "Darling, here is everything I can do for you:\n\n"
        "🔐 **Secrets:**\n"
        "• `/msg @username [text]` - Send a secret message (Anti-Admin Leak).\n\n"
        "✍️ **Creativity:**\n"
        "• `/write <text>` - I'll write your message on a paper image.\n\n"
        "🔍 **Discovery & AI:**\n"
        "• `/search <query>` - Search YouTube videos with download buttons.\n"
        "• `/ask <question>` - Chat with me! (Mistral AI).\n\n"
        "🎬 **Downloader:**\n"
        "• `/dl <link>` - Download videos from YT, FB, Insta, etc.\n\n"
        "👮 **Group Management:**\n"
        "• `/ban`, `/kick`, `/mute`, `/pin` - Group control tools.\n\n"
        "🛡 **Protection:**\n"
        "• Anti-Link: I remove unauthorized links automatically!\n\n"
        "✨ **I am always here to serve you, Darling!**"
    )
    
    btns = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Me to Your Group ➕", url=f"https://t.me/{client.me.username}?startgroup=true")],
        [InlineKeyboardButton("Support Group 💬", url="https://t.me/+w4pjkCEPzkFhYTc1"), 
         InlineKeyboardButton("Dev Channel 📢", url="https://t.me/+sLwk3rnxdkAyYjBl")]
    ])
    
    await message.reply_text(help_text, reply_markup=btns)

# ==============================================================================
# --- [ COMMAND HANDLERS: START & INTERFACE ] ---
# ==============================================================================

@app.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    if not is_bot_running: return
    """Displays the main control panel to the user with supreme buttons."""
    uid = message.from_user.id
    cursor.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?)", (uid, message.from_user.username, message.from_user.first_name))
    db.commit()
    
    add_live_log(f"USER: {message.from_user.first_name} started the bot.")
    
    path = r"c:\Users\amale\Downloads\Darling in the Franxx - Zero Two.jpg"
    caption = (
        f"🌸 **KONNICHIWA! WELCOME TO ZERO TWO SUPREME UNIVERSE** 🌸\n\n"
        f"Hello {message.from_user.mention}, Darling! I am **Zero Two**, your ultimate premium bot companion.\n\n"
        "🚀 **WHAT I CAN DO:**\n"
        "╰┈➤ 🔐 Anti-Leak Secret Messages\n"
        "╰┈➤ 🎬 High-speed Video Downloads\n"
        "╰┈➤ 🤖 Advanced AI Chat (Mistral Engine)\n"
        "╰┈➤ ✍️ Realistic Handwriting Generation\n"
        "╰┈➤ 👮 Professional Group Management\n\n"
        "👉 **Click the buttons below to explore my world!**"
    )
    
    btns = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Me to Your Group ➕", url=f"https://t.me/{client.me.username}?startgroup=true")],
        [InlineKeyboardButton("Help Menu 📚", callback_data="open_help"),
         InlineKeyboardButton("Support Group 💬", url="https://t.me/+w4pjkCEPzkFhYTc1")],
        [InlineKeyboardButton("Dev Channel 📢", url="https://t.me/+sLwk3rnxdkAyYjBl")]
    ])
    
    try:
        if os.path.exists(path): 
            await message.reply_photo(photo=path, caption=caption, reply_markup=btns)
        else: 
            await message.reply_text(caption, reply_markup=btns)
    except: 
        await message.reply_text(caption, reply_markup=btns)
    
    await send_log(f"🚀 **Bot Started** by {message.from_user.mention}")

@app.on_callback_query(filters.regex("open_help"))
async def help_callback(client, callback_query: CallbackQuery):
    await help_handler(client, callback_query.message)
    await callback_query.answer("Opening Help Menu, Darling! ❤️")

# ==============================================================================
# --- [ FIXED HANDWRITING SYSTEM: INTERNAL ENGINE ] ---
# ==============================================================================
@app.on_message(filters.command("write"))
async def write_handler(client, message):
    if not is_bot_running: return
    input_text = " ".join(message.command[1:])
    if not input_text:
        return await message.reply_text("❌ Darling, what should I write?")
    
    add_live_log(f"WRITE: {message.from_user.first_name} is generating a note.")
    processing_msg = await message.reply_text("`✍️ Zero Two is writing manually for you...`")
    temp_file = f"note_{message.from_user.id}.jpg"
    
    try:
        await asyncio.get_event_loop().run_in_executor(
            None, lambda: generate_handwriting_internal(input_text, temp_file)
        )
        
        await message.reply_photo(
            photo=temp_file, 
            caption=f"✨ **Darling, here is your handwritten note!**"
        )
        if os.path.exists(temp_file): os.remove(temp_file)
        await processing_msg.delete()
    except Exception as e:
        await processing_msg.edit(f"❌ Internal Write Error: {str(e)}")
        if os.path.exists(temp_file): os.remove(temp_file)

# ==============================================================================
# --- [ YOUTUBE SEARCH & AI COMMANDS ] ---
# ==============================================================================

@app.on_message(filters.command("search"))
async def search_handler(client, message):
    if not is_bot_running: return
    q = " ".join(message.command[1:])
    if not q: return await message.reply_text("❌ What should I search for, Darling?")
    
    add_live_log(f"SEARCH: Query '{q}' by {message.from_user.id}")
    st = await message.reply_text("`🔍 Searching for the best results...`")
    try:
        res = await asyncio.get_event_loop().run_in_executor(None, lambda: youtube_search(q))
        if not res: return await st.edit("❌ No results found, Darling!")
            
        out = "🎯 **Zero Two's Top Results:**\n\n"
        btns = []
        for i, en in enumerate(res[:5]):
            out += f"{i+1}. **{en['title'][:45]}...**\n"
            btns.append([InlineKeyboardButton(f"🎬 Download Video {i+1}", callback_data=f"dl|best|{en['id']}")])
            url_storage[en['id']] = en['url']
        await st.edit(out, reply_markup=InlineKeyboardMarkup(btns))
    except Exception as e: await st.edit(f"❌ Error: {e}")

@app.on_message(filters.command("ask"))
async def ai_ask_handler(client, message: Message):
    if not is_bot_running: return
    q = " ".join(message.command[1:])
    if not q: return await message.reply_text("❌ Ask me something, Darling! ❤️")
    
    add_live_log(f"AI: Question from {message.from_user.id}")
    w = await message.reply_text("`⏳ Zero Two is thinking...`")
    ans = await asyncio.get_event_loop().run_in_executor(None, lambda: get_ai_response(q))
    await w.edit(f"🤖 **Zero Two AI:**\n\n{ans}")

# ==============================================================================
# --- [ ADMINISTRATIVE TOOLS & STATS ] ---
# ==============================================================================

@app.on_message(filters.command("stats") & filters.user(ADMIN_ID))
async def stats_handler(client, message):
    if not is_bot_running: return
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    await message.reply_text(f"📊 **Total Registered Users:** `{count}`\n✨ Status: Goddess Mode Active.")

@app.on_message(filters.command("broadcast") & filters.user(ADMIN_ID))
async def broadcast_handler(client, message):
    if not message.reply_to_message: return await message.reply_text("❌ Reply to a message!")
    add_live_log("ADMIN: Starting Broadcast...")
    p = await message.reply_text("🚀 **Broadcasting...**")
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    ok, fail = 0, 0
    for u in users:
        try:
            await message.reply_to_message.copy(chat_id=u[0])
            ok += 1
            await asyncio.sleep(0.3)
        except: fail += 1
    await p.edit(f"✅ **Broadcast Done!**\n🔥 Success: `{ok}`\n❌ Failed: `{fail}`")

# ==============================================================================
# --- [ MODERATION SUITE: GROUP PROTECTOR ] ---
# ==============================================================================

@app.on_message(filters.command("ban") & filters.group)
async def ban_handler(client, message):
    if not is_bot_running: return
    if not await is_user_authorized(client, message.chat.id, message.from_user.id): return
    target = message.reply_to_message.from_user.id if message.reply_to_message else (await client.get_users(message.command[1])).id if len(message.command) > 1 else None
    if target: 
        await client.ban_chat_member(message.chat.id, target)
        add_live_log(f"MOD: Banned {target} in {message.chat.title}")
        await message.reply_text("🚫 **Banned!**")

@app.on_message(filters.command("unban") & filters.group)
async def unban_handler(client, message):
    if not is_bot_running: return
    if not await is_user_authorized(client, message.chat.id, message.from_user.id): return
    target = message.reply_to_message.from_user.id if message.reply_to_message else None
    if target: 
        await client.unban_chat_member(message.chat.id, target)
        add_live_log(f"MOD: Unbanned {target} in {message.chat.title}")

@app.on_message(filters.command("kick") & filters.group)
async def kick_handler(client, message):
    if not is_bot_running: return
    if not await is_user_authorized(client, message.chat.id, message.from_user.id): return
    target = message.reply_to_message.from_user.id if message.reply_to_message else None
    if target:
        await client.ban_chat_member(message.chat.id, target)
        await client.unban_chat_member(message.chat.id, target)
        add_live_log(f"MOD: Kicked {target} from {message.chat.title}")
        await message.reply_text("👞 **Kicked!**")

@app.on_message(filters.command(["mute", "unmute"]) & filters.group)
async def mute_unmute_handler(client, message):
    if not is_bot_running: return
    if not await is_user_authorized(client, message.chat.id, message.from_user.id): return
    target = message.reply_to_message.from_user.id if message.reply_to_message else None
    if target:
        can = True if message.command[0] == "unmute" else False
        await client.restrict_chat_member(message.chat.id, target, ChatPermissions(can_send_messages=can))
        add_live_log(f"MOD: {'Unmuted' if can else 'Muted'} {target}")
        await message.reply_text(f"✅ User {'Unmuted' if can else 'Muted'}!")

@app.on_message(filters.command("pin") & filters.group)
async def pin_handler(client, message):
    if not is_bot_running: return
    if not await is_user_authorized(client, message.chat.id, message.from_user.id): return
    if message.reply_to_message: 
        await client.pin_chat_message(message.chat.id, message.reply_to_message.id)
        add_live_log(f"MOD: Message pinned in {message.chat.title}")

# ==============================================================================
# --- [ ULTIMATE DOWNLOADER ENGINE ] ---
# ==============================================================================

@app.on_message(filters.command("dl") & (filters.group | filters.private))
async def dl_handler(client, message):
    if not is_bot_running: return
    if message.chat.type != pyrogram.enums.ChatType.PRIVATE:
        if not await is_user_authorized(client, message.chat.id, message.from_user.id): return
    url = message.command[1] if len(message.command) > 1 else (message.text if message.chat.type == pyrogram.enums.ChatType.PRIVATE else None)
    if not url or "http" not in url: return
    
    add_live_log(f"DL: URL Analysis started for {url[:20]}...")
    an = await message.reply_text("`🔍 Analyzing URL... please wait!`", quote=True)
    try:
        meta = await asyncio.get_event_loop().run_in_executor(None, lambda: get_video_info(url))
        uid = str(time.time()).replace(".", "")[-10:]
        url_storage[uid] = url
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("🎥 Download Video", callback_data=f"dl|best|{uid}")]])
        await an.edit(f"🎬 **Title:** `{meta.get('title')[:60]}...`", reply_markup=btn)
    except: await an.edit("❌ Analysis failed. Link invalid or protected.")

@app.on_callback_query(filters.regex(r'^dl\|'))
async def dl_callback(client, callback_query: CallbackQuery):
    _, fmt, uid = callback_query.data.split("|")
    url = url_storage.get(uid)
    if not url: return await callback_query.answer("Link Expired!")
    
    add_live_log(f"DL: Downloading file for {callback_query.from_user.id}")
    await callback_query.message.edit_text("`📥 Downloading... almost there!`")
    tmpl = os.path.join("downloads", f"{uid}.%(ext)s")
    try:
        opts = {'format': fmt, 'outtmpl': tmpl, 'nocheckcertificate': True}
        await asyncio.get_event_loop().run_in_executor(None, lambda: yt_dlp.YoutubeDL(opts).download([url]))
        file = next(f for f in os.listdir("downloads") if uid in f)
        await callback_query.message.reply_video(video=os.path.join("downloads", file), caption="✅ **Downloaded for you!**")
        os.remove(os.path.join("downloads", file))
        await callback_query.message.delete()
    except Exception as e: await callback_query.message.edit_text(f"❌ Error: {e}")

# ==============================================================================
# --- [ ANTI-LINK PROTECTION ] ---
# ==============================================================================

@app.on_message(filters.group & filters.regex(r'http') & ~filters.command(["dl", "search", "write", "help", "msg"]))
async def anti_link(client, message):
    if not is_bot_running: return
    if await is_user_authorized(client, message.chat.id, message.from_user.id): return
    try:
        await message.delete()
        add_live_log(f"SHIELD: Link deleted from {message.from_user.id}")
        w = await message.reply_text(f"⚠️ {message.from_user.mention}, links are not allowed here!")
        await asyncio.sleep(5)
        await w.delete()
    except: pass

# ==============================================================================
# --- [ SYSTEM BOOTLOADER WITH WEB DASHBOARD ] ---
# ==============================================================================

def main_execution():
    if not os.path.exists("downloads"): os.makedirs("downloads")
    add_live_log("SYSTEM: Initializing Zero Two Supreme Engine...")
    print("Starting Web Control Panel...")
    threading.Thread(target=run_web, daemon=True).start()
    print("Zero Two Supreme Edition: ONLINE")
    print("---------------------------------------")
    print("Dashboard Link: http://localhost:5000")
    app.run()

if __name__ == "__main__":
    main_execution()

# ==============================================================================
# --- [ END OF SUPREME MASTER CODE - 750+ LINES SECURED ] ---

# ==============================================================================
