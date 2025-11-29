# assistant.py
import os
import time
import sqlite3
import threading
from datetime import datetime, timedelta
import requests
import speech_recognition as sr
import pyttsx3
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
load_dotenv()


# ========== Configuration ==========
WAKE_WORDS = ("hey assistant", "ok assistant", "assistant")
OWM_API_KEY = os.environ.get("OWM_API_KEY")  # OpenWeatherMap API key (optional)
NEWSAPI_KEY = os.environ.get("NEWSAPI_KEY")  # NewsAPI key (optional)
DB_PATH = "assistant_reminders.db"

# ========== Text-to-Speech ==========
tts_engine = None
# Try to initialize TTS engine with fallback options
for driver_name in [None, 'dummy']:
    try:
        tts_engine = pyttsx3.init(driverName=driver_name)
        tts_engine.setProperty("rate", 170)
        print("TTS engine initialized successfully")
        break
    except Exception as e:
        if driver_name is None:
            print(f"Warning: Could not initialize default TTS engine: {e}")
            print("TTS will be disabled. Install espeak for Linux: sudo apt-get install espeak")
        continue

def speak(text):
    print("Assistant:", text)
    if tts_engine is not None:
        try:
            tts_engine.say(text)
            tts_engine.runAndWait()
        except Exception as e:
            print(f"TTS error: {e}")
    # If TTS fails, at least print the message

# ========== Database for reminders ==========
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS reminders (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               message TEXT NOT NULL,
               remind_at TEXT NOT NULL,
               triggered INTEGER DEFAULT 0
           )"""
    )
    conn.commit()
    conn.close()

def add_reminder_to_db(message, remind_at_iso):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO reminders (message, remind_at) VALUES (?, ?)", (message, remind_at_iso))
    conn.commit()
    conn.close()

def get_pending_reminders():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, message, remind_at FROM reminders WHERE triggered=0")
    rows = c.fetchall()
    conn.close()
    return rows

def mark_reminder_triggered(reminder_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE reminders SET triggered=1 WHERE id=?", (reminder_id,))
    conn.commit()
    conn.close()

# ========== Scheduler ==========
scheduler = BackgroundScheduler()
scheduler.start()

def schedule_reminder(reminder_id, message, remind_at_dt):
    def job():
        speak(f"Reminder: {message}")
        mark_reminder_triggered(reminder_id)
    scheduler.add_job(job, 'date', run_date=remind_at_dt, id=f"rem_{reminder_id}")

def schedule_existing_reminders():
    for row in get_pending_reminders():
        rid, message, remind_at = row
        remind_at_dt = datetime.fromisoformat(remind_at)
        if remind_at_dt > datetime.now():
            # If job exists (e.g., after restart), skip scheduling duplicates
            try:
                scheduler.get_job(f"rem_{rid}")
            except Exception:
                schedule_reminder(rid, message, remind_at_dt)
        else:
            # time passed; mark triggered so it doesn't repeat (or trigger immediately if you prefer)
            mark_reminder_triggered(rid)

# ========== Speech recognition ==========
recognizer = sr.Recognizer()
mic = sr.Microphone()

def listen_for_phrase(timeout=None, phrase_time_limit=8):
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.7)
        audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
    try:
        text = recognizer.recognize_google(audio)
        return text.lower()
    except sr.WaitTimeoutError:
        return ""
    except sr.UnknownValueError:
        return ""
    except sr.RequestError:
        # network error or API down
        return ""

# ========== Utilities: parse time phrases ==========
def parse_time_phrase(phrase):
    # Very simple parser: supports:
    # - "in X minutes"
    # - "in X hours"
    # - "at HH:MM" or "at H PM" (very basic)
    phrase = phrase.lower()
    now = datetime.now()
    if "in " in phrase and "minute" in phrase:
        try:
            num = int([w for w in phrase.split() if w.isdigit()][0])
            return now + timedelta(minutes=num)
        except Exception:
            pass
    if "in " in phrase and "hour" in phrase:
        try:
            num = int([w for w in phrase.split() if w.isdigit()][0])
            return now + timedelta(hours=num)
        except Exception:
            pass
    if "at " in phrase:
        # naive parse: find HH or HH:MM and optional am/pm
        import re
        m = re.search(r'at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', phrase)
        if m:
            h = int(m.group(1))
            mm = int(m.group(2)) if m.group(2) else 0
            ampm = m.group(3)
            if ampm:
                if ampm == "pm" and h != 12:
                    h += 12
                if ampm == "am" and h == 12:
                    h = 0
            candidate = now.replace(hour=h, minute=mm, second=0, microsecond=0)
            if candidate < now:
                candidate += timedelta(days=1)
            return candidate
    return None

# ========== Command handlers ==========
def handle_set_reminder(command_text):
    # Expected patterns: "set a reminder to <message> in 10 minutes"
    # naive split
    if "reminder to" in command_text:
        parts = command_text.split("reminder to", 1)[1].strip()
    elif "remind me to" in command_text:
        parts = command_text.split("remind me to", 1)[1].strip()
    else:
        speak("I didn't understand the reminder format. Try: remind me to take medicine in 10 minutes.")
        return
    # attempt to find time phrase
    # heuristics: look for " in X minutes/hours" or " at HH:MM"
    time_part = None
    for token in (" in ", " at "):
        if token in parts:
            idx = parts.find(token)
            message = parts[:idx].strip()
            time_part = parts[idx:].strip()
            break
    if not time_part:
        # fallback: ask for time
        speak("When should I remind you?")
        resp = listen_for_phrase(timeout=8)
        time_part = " " + resp
        message = parts
    remind_at = parse_time_phrase(time_part)
    if not remind_at:
        speak("I couldn't parse the time. Please say something like 'in 10 minutes' or 'at 7 PM'.")
        return
    add_reminder_to_db(message, remind_at.isoformat())
    # get last inserted id
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT last_insert_rowid()")
    rid = c.fetchone()[0]
    conn.close()
    schedule_reminder(rid, message, remind_at)
    speak(f"Okay, I'll remind you to {message} at {remind_at.strftime('%I:%M %p on %b %d')}.")

def handle_check_weather(command_text):
    # extract location if provided: "weather in London" or default to local
    loc = None
    if " in " in command_text:
        loc = command_text.split(" in ", 1)[1].strip()
    if not OWM_API_KEY:
        speak("Weather API key not set. Please set OWM_API_KEY environment variable.")
        return
    if not loc:
        # use a default — ask user
        speak("For which city?")
        loc = listen_for_phrase(timeout=6)
        if not loc:
            speak("I couldn't get the city name.")
            return
    # call OpenWeatherMap current weather
    try:
        params = {"q": loc, "appid": OWM_API_KEY, "units": "metric"}
        r = requests.get("https://api.openweathermap.org/data/2.5/weather", params=params, timeout=8)
        data = r.json()
        if r.status_code != 200:
            speak(f"Couldn't get weather for {loc}. {data.get('message','')}")
            return
        desc = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        speak(f"The weather in {loc} is {desc} with a temperature of {temp} degrees Celsius.")
    except Exception as e:
        speak("Sorry, I couldn't fetch the weather right now.")
        print("weather error:", e)

def handle_read_news(command_text):
    # Read top headlines
    if NEWSAPI_KEY:
        try:
            params = {"apiKey": NEWSAPI_KEY, "country": "us", "pageSize": 5}
            r = requests.get("https://newsapi.org/v2/top-headlines", params=params, timeout=8)
            data = r.json()
            if data.get("status") == "ok":
                articles = data.get("articles", [])[:5]
                if not articles:
                    speak("No articles found.")
                    return
                speak("Here are the top headlines.")
                for a in articles:
                    speak(a.get("title", ""))
                    time.sleep(0.3)
                return
        except Exception as e:
            print("newsapi error:", e)
    # Fallback: simple RSS (BBC top stories)
    try:
        r = requests.get("http://feeds.bbci.co.uk/news/rss.xml", timeout=8)
        # minimal parsing to find <title> tags
        titles = []
        import re
        for m in re.finditer(r"<title>(.*?)</title>", r.text, re.I|re.S):
            titles.append(re.sub("<.*?>", "", m.group(1)).strip())
            if len(titles) >= 6:
                break
        if titles:
            speak("Here are some headlines from BBC.")
            # skip first title (it's feed title)
            for t in titles[1:6]:
                speak(t)
                time.sleep(0.3)
            return
    except Exception as e:
        print("rss error:", e)
    speak("Sorry, I couldn't fetch the news right now.")

def handle_help():
    speak("You can say: set a reminder to take medicine in 10 minutes. Or say: what's the weather in London. Or: read the news.")

# ========== Main command processor ==========
def process_command(command_text):
    print("Heard command:", command_text)
    if any(kw in command_text for kw in ("remind", "reminder", "remind me")):
        handle_set_reminder(command_text)
    elif "weather" in command_text:
        handle_check_weather(command_text)
    elif "news" in command_text or "headlines" in command_text:
        handle_read_news(command_text)
    elif "help" in command_text:
        handle_help()
    elif "exit" in command_text or "quit" in command_text or "stop" in command_text:
        speak("Goodbye!")
        os._exit(0)
    else:
        speak("Sorry, I didn't understand that. Say 'help' to hear what I can do.")

# ========== Boot & background restore ==========
def boot():
    init_db()
    schedule_existing_reminders()
    speak("Assistant started. Say 'Hey Assistant' to give a command.")

# ========== Listener loop (wake-word + command) ==========
def listener_loop():
    boot()
    while True:
        try:
            text = listen_for_phrase(timeout=None, phrase_time_limit=6)
            if not text:
                continue
            print("Heard:", text)
            if any(w in text for w in WAKE_WORDS):
                speak("Yes?")
                # listen for command
                cmd = listen_for_phrase(timeout=6, phrase_time_limit=10)
                if not cmd:
                    speak("I didn't hear anything.")
                else:
                    process_command(cmd)
            # else: ignore background speech
        except KeyboardInterrupt:
            speak("Shutting down.")
            break
        except Exception as e:
            print("Listener error:", e)
            time.sleep(1)

if __name__ == "__main__":
    listener_loop()
