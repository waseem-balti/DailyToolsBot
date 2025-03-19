from telethon import TelegramClient, events
from telethon.tl.custom import Button
from telethon.tl.types import InputMediaPhoto
import asyncio
import aiohttp
import logging
import os
import random
import re
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Credentials
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
W_API = os.getenv('W_API')
NEWS_API = os.getenv('NEWS_API')

# Initialize the Telegram client
client = TelegramClient('s1', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Dictionary to track user messages for rate-limiting
user_last_message = {}

# Dictionary to track user preferences
user_preferences = {}

# Dictionary for reminders
user_reminders = {}

# Simple state management for conversation flows
user_states = {}

# Dictionary for user game scores
user_scores = {}

# Dictionary for trivia answers
trivia_answers = {}

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Main menu buttons
async def get_main_menu_buttons():
    return [
        [Button.inline("🌤️ Weather", b"weather_menu"), Button.inline("😂 Jokes", b"joke")],
        [Button.inline("📰 News", b"news_menu"), Button.inline("🎮 Games", b"games_menu")],
        [Button.inline("⏰ Reminders", b"reminder_menu"), Button.inline("📝 Notes", b"notes_menu")],
        [Button.inline("⚙️ Settings", b"settings"), Button.inline("ℹ️ About", b"about")],
        [Button.inline("❓ Help", b"help")]
    ]

# Start command
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    user = await event.get_sender()
    user_id = event.sender_id
    username = user.username or user.first_name
    
    # Initialize user preferences if not exists
    if user_id not in user_preferences:
        user_preferences[user_id] = {
            "temperature_unit": "celsius",
            "language": "english",
            "notifications": True,
            "theme": "light",
            "notes": []
        }
    
    welcome_text = f"👋 Hello, {username}!\n\nI'm your personal assistant bot. How can I help you today?"
    
    buttons = await get_main_menu_buttons()
    await event.respond(welcome_text, buttons=buttons)
    logger.info(f"User {event.sender_id} started the bot")

# Help menu
@client.on(events.NewMessage(pattern='/help'))
async def help_command(event):
    buttons = [
        [Button.inline("🤖 Bot Commands", b"help_commands")],
        [Button.inline("🌐 Weather", b"help_weather"), Button.inline("📰 News", b"help_news")],
        [Button.inline("😂 Jokes", b"help_jokes"), Button.inline("🎮 Games", b"help_games")],
        [Button.inline("⏰ Reminders", b"help_reminders"), Button.inline("📝 Notes", b"help_notes")],
        [Button.inline("⚙️ Settings", b"help_settings")],
        [Button.inline("🔙 Back to Main Menu", b"main_menu")]
    ]
    await event.respond("Choose a help topic:", buttons=buttons)

# About command
@client.on(events.NewMessage(pattern='/about'))
async def about_command(event):
    about_text = (
        "📱 **Telegram Assistant Bot**\n\n"
        "I'm a versatile bot designed to make your Telegram experience better.\n"
        "I can provide weather updates, tell jokes, deliver news, set reminders, and more!\n\n"
        "Version: 2.1.0\n"
        "Created with ❤️ using Telethon\n\n"
        "Type /help to see all available commands."
    )
    buttons = [[Button.inline("🔙 Back to Main Menu", b"main_menu")]]
    await event.respond(about_text, buttons=buttons)

# Weather command with city input
@client.on(events.NewMessage(pattern='/weather'))
async def weather_command(event):
    # Check if command includes a city
    command_parts = event.message.text.split(' ', 1)
    if len(command_parts) > 1:
        city = command_parts[1].strip()
        weather_info, success = await get_weather_data(city)
        
        buttons = [[Button.inline("🔙 Back to Weather Menu", b"weather_menu")]]
        await event.respond(weather_info, buttons=buttons)
    else:
        buttons = [
            [Button.inline("🔍 Search City", b"weather_search")],
            [Button.location("📍 Share Location")],
            [Button.inline("🔙 Back to Main Menu", b"main_menu")]
        ]
        await event.respond("How would you like to get the weather?", buttons=buttons)

# Location handler
@client.on(events.NewMessage)
async def handle_location(event):
    if event.geo:
        lat = event.geo.lat
        lon = event.geo.long
        # Get weather based on coordinates
        weather_info, success = await get_weather_data(f"{lat},{lon}")
        
        buttons = [[Button.inline("🔙 Back to Weather Menu", b"weather_menu")]]
        await event.respond(weather_info, buttons=buttons)
        return True
    return False

# City input handler
async def get_weather_data(city):
    try:
        api_key = W_API
        url = f'http://api.weatherapi.com/v1/forecast.json?q={city}&key={api_key}&days=3&aqi=yes&alerts=yes'

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Format the weather info with emojis
                    location = data['location']
                    current = data['current']
                    forecast = data['forecast']['forecastday']
                    
                    condition = current['condition']['text']
                    temp_c = current['temp_c']
                    temp_f = current['temp_f']
                    humidity = current['humidity']
                    wind_kph = current['wind_kph']
                    
                    # Add emojis based on condition
                    condition_emoji = "☀️"
                    if "rain" in condition.lower():
                        condition_emoji = "🌧️"
                    elif "cloud" in condition.lower():
                        condition_emoji = "☁️"
                    elif "snow" in condition.lower():
                        condition_emoji = "❄️"
                    elif "storm" in condition.lower() or "thunder" in condition.lower():
                        condition_emoji = "⛈️"
                    elif "fog" in condition.lower() or "mist" in condition.lower():
                        condition_emoji = "🌫️"
                    
                    # Current weather
                    weather_info = (
                        f"🌡️ **Weather in {location['name']}, {location['country']}**\n\n"
                        f"🌡️ Temperature: **{temp_c}°C** / **{temp_f}°F**\n"
                        f"{condition_emoji} Condition: **{condition}**\n"
                        f"💧 Humidity: **{humidity}%**\n"
                        f"💨 Wind: **{wind_kph} km/h**\n"
                    )
                    
                    # Air quality if available
                    if 'air_quality' in current and 'us-epa-index' in current['air_quality']:
                        aqi = current['air_quality']['us-epa-index']
                        aqi_status = "Good 👍" if aqi <= 2 else "Moderate 👌" if aqi <= 4 else "Poor 👎"
                        weather_info += f"🌬️ Air Quality: **{aqi_status}**\n"
                    
                    # Add forecast for next 3 days
                    weather_info += "\n**3-Day Forecast:**\n"
                    for day in forecast:
                        date = datetime.strptime(day['date'], '%Y-%m-%d').strftime('%a, %b %d')
                        day_condition = day['day']['condition']['text']
                        day_emoji = "☀️"
                        if "rain" in day_condition.lower():
                            day_emoji = "🌧️"
                        elif "cloud" in day_condition.lower():
                            day_emoji = "☁️"
                        elif "snow" in day_condition.lower():
                            day_emoji = "❄️"
                        
                        weather_info += (
                            f"• **{date}**: {day_emoji} {day_condition}, "
                            f"Max: {day['day']['maxtemp_c']}°C, Min: {day['day']['mintemp_c']}°C\n"
                        )
                    
                    weather_info += f"\n📅 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    return weather_info, True
                else:
                    return f"Sorry, I couldn't fetch the weather for '{city}'. Please check the spelling or try another location.", False
    except Exception as e:
        logger.error(f"Weather error: {str(e)}")
        return "An error occurred while fetching the weather. Please try again.", False

# Weather city search conversation handler
@client.on(events.CallbackQuery(data=b"weather_search"))
async def weather_search(event):
    await event.edit("Please type the city name (e.g., 'London', 'New York'):")
    
    # Set a flag to indicate we're waiting for a city
    user_id = event.sender_id
    user_states[user_id] = "waiting_for_city"

# Weather button callback
@client.on(events.CallbackQuery(data=b"weather_menu"))
async def weather_menu_callback(event):
    buttons = [
        [Button.inline("🔍 Search City", b"weather_search")],
        [Button.inline("🌡️ Weather Forecast", b"weather_forecast")],
        [Button.inline("🔙 Back to Main Menu", b"main_menu")]
    ]
    await event.edit("Weather Menu:", buttons=buttons)

# Weather forecast callback
@client.on(events.CallbackQuery(data=b"weather_forecast"))
async def weather_forecast_callback(event):
    await event.edit("Please type the city name for a forecast:")
    
    # Set a flag to indicate we're waiting for a city for forecast
    user_id = event.sender_id
    user_states[user_id] = "waiting_for_forecast_city"

# Handle text messages for various inputs
@client.on(events.NewMessage(func=lambda e: e.text and not e.text.startswith('/')))
async def handle_text_input(event):
    user_id = event.sender_id
    
    if user_id not in user_states:
        return False
        
    state = user_states[user_id]
    
    # Skip if no active state
    if state is None:
        return False
        
    # If state is a string (for simple states)
    if isinstance(state, str):
        if state == "waiting_for_city":
            city = event.text.strip()
            weather_info, success = await get_weather_data(city)
            
            buttons = [[Button.inline("🔙 Back to Weather Menu", b"weather_menu")]]
            await event.respond(weather_info, buttons=buttons)
            
            # Reset the state
            user_states[user_id] = None
            return True
            
        elif state == "waiting_for_forecast_city":
            city = event.text.strip()
            weather_info, success = await get_weather_data(city)
            
            buttons = [[Button.inline("🔙 Back to Weather Menu", b"weather_menu")]]
            await event.respond(weather_info, buttons=buttons)
            
            # Reset the state
            user_states[user_id] = None
            return True
            
        elif state == "waiting_for_note_title":
            note_title = event.text.strip()
            user_states[user_id] = {"state": "waiting_for_note_content", "title": note_title}
            await event.respond(f"📝 Title: **{note_title}**\n\nNow please type the content of your note:")
            return True
            
        elif state == "waiting_for_reminder_text":
            reminder_text = event.text.strip()
            user_states[user_id] = {"state": "waiting_for_reminder_time", "text": reminder_text}
            await event.respond(
                f"📝 Reminder text: **{reminder_text}**\n\n"
                "Now please specify when to remind you.\n"
                "Examples: 10m (10 minutes), 2h (2 hours), 1d (1 day), or enter a specific time like '14:30'"
            )
            return True
            
    # If state is a dictionary (for complex states)
    elif isinstance(state, dict):
        if state.get("state") == "waiting_for_note_content":
            note_content = event.text.strip()
            note_title = state.get("title", "Untitled")
            
            # Ensure user has preferences initialized
            if user_id not in user_preferences:
                user_preferences[user_id] = {"notes": []}
            elif "notes" not in user_preferences[user_id]:
                user_preferences[user_id]["notes"] = []
            
            # Generate note ID
            note_id = 1
            if user_preferences[user_id]["notes"]:
                note_id = max(note["id"] for note in user_preferences[user_id]["notes"]) + 1
                
            # Save the note
            user_preferences[user_id]["notes"].append({
                "id": note_id,
                "title": note_title,
                "content": note_content,
                "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            
            buttons = [[Button.inline("📝 View Notes", b"view_notes"), Button.inline("🔙 Main Menu", b"main_menu")]]
            await event.respond(f"✅ Note saved successfully!\n\nTitle: **{note_title}**\nID: {note_id}", buttons=buttons)
            
            # Reset the state
            user_states[user_id] = None
            return True
        
        elif state.get("state") == "waiting_for_reminder_time":
            time_input = event.text.strip().lower()
            reminder_text = state.get("text", "Reminder")
            
            # Parse the time input
            delay_seconds = 0
            reminder_time = None
            
            # Try to match patterns like "5m", "2h", "1d"
            time_match = re.match(r"(\d+)([mhd])", time_input)
            if time_match:
                value = int(time_match.group(1))
                unit = time_match.group(2)
                
                if unit == 'm':
                    delay_seconds = value * 60
                elif unit == 'h':
                    delay_seconds = value * 60 * 60
                elif unit == 'd':
                    delay_seconds = value * 24 * 60 * 60
                    
                reminder_time = datetime.now() + timedelta(seconds=delay_seconds)
            else:
                # Try to match specific time like "14:30"
                time_match = re.match(r"(\d{1,2}):(\d{2})", time_input)
                if time_match:
                    hours = int(time_match.group(1))
                    minutes = int(time_match.group(2))
                    
                    now = datetime.now()
                    reminder_time = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)
                    
                    # If the time is already passed today, set it for tomorrow
                    if reminder_time < now:
                        reminder_time += timedelta(days=1)
                        
                    delay_seconds = (reminder_time - now).total_seconds()
                else:
                    # Invalid time format
                    await event.respond(
                        "⚠️ Invalid time format. Please use formats like:\n"
                        "10m (10 minutes)\n"
                        "2h (2 hours)\n"
                        "1d (1 day)\n"
                        "14:30 (specific time)"
                    )
                    return True
            
            # Initialize reminders for this user if not exists
            if user_id not in user_reminders:
                user_reminders[user_id] = []
                
            # Generate reminder ID
            reminder_id = 1
            if user_reminders[user_id]:
                reminder_id = max(reminder["id"] for reminder in user_reminders[user_id]) + 1
                
            # Add the reminder
            reminder = {
                "id": reminder_id,
                "text": reminder_text,
                "time": reminder_time.timestamp() if reminder_time else (time.time() + delay_seconds),
                "created_at": time.time()
            }
            user_reminders[user_id].append(reminder)
            
            # Schedule the reminder
            asyncio.create_task(send_reminder(user_id, reminder_id, reminder_text, delay_seconds))
            
            formatted_time = reminder_time.strftime('%Y-%m-%d %H:%M:%S') if reminder_time else f"in {time_input}"
            
            buttons = [[Button.inline("⏰ View Reminders", b"view_reminders"), Button.inline("🔙 Main Menu", b"main_menu")]]
            await event.respond(
                f"✅ Reminder set successfully!\n\n"
                f"📝 {reminder_text}\n"
                f"⏰ {formatted_time}\n"
                f"🆔 Reminder ID: {reminder_id}",
                buttons=buttons
            )
            
            # Reset the state
            user_states[user_id] = None
            return True
            
        elif state.get("state") == "playing_number_guess":
            try:
                guess = int(event.text.strip())
                target = state.get("number")
                attempts = state.get("attempts", 0) + 1
                
                if guess < 1 or guess > 100:
                    await event.respond("Please enter a valid number between 1 and 100!")
                    return True
                
                if guess == target:
                    buttons = [
                        [Button.inline("🎮 Play Again", b"game_number")],
                        [Button.inline("🔙 Games Menu", b"games_menu")]
                    ]
                    await event.respond(
                        f"🎉 Congratulations! You got it in {attempts} attempts!\n"
                        f"The number was {target}",
                        buttons=buttons
                    )
                    user_states[user_id] = None
                else:
                    hint = "higher" if guess < target else "lower"
                    user_states[user_id]["attempts"] = attempts
                    await event.respond(f"Try {hint}! (Attempt {attempts})")
            except ValueError:
                await event.respond("Please enter a valid number between 1 and 100!")
            return True
    
    return False

# Function to send reminder when time is up
async def send_reminder(user_id, reminder_id, text, delay_seconds):
    await asyncio.sleep(delay_seconds)
    
    # Check if reminder still exists
    if user_id in user_reminders:
        reminder_exists = False
        for reminder in user_reminders[user_id]:
            if reminder["id"] == reminder_id:
                reminder_exists = True
                break
        
        if reminder_exists:
            # Remove the reminder
            user_reminders[user_id] = [r for r in user_reminders[user_id] if r["id"] != reminder_id]
            
            # Send the reminder
            buttons = [[Button.inline("⏰ Set New Reminder", b"set_reminder"), Button.inline("🔙 Main Menu", b"main_menu")]]
            try:
                await client.send_message(
                    user_id,
                    f"⏰ **REMINDER**\n\n📝 {text}\n\n⌚ Time's up!",
                    buttons=buttons
                )
                logger.info(f"Reminder sent to user {user_id}: {text}")
            except Exception as e:
                logger.error(f"Failed to send reminder to {user_id}: {e}")

# Joke command
@client.on(events.NewMessage(pattern='/joke'))
async def joke_command(event):
    joke_text = await get_joke()
    
    buttons = [
        [Button.inline("😂 Another Joke", b"joke")],
        [Button.inline("🔙 Back to Main Menu", b"main_menu")]
    ]
    await event.respond(joke_text, buttons=buttons)

# Function to get a joke
async def get_joke():
    joke_apis = [
        'https://official-joke-api.appspot.com/random_joke',
        'https://v2.jokeapi.dev/joke/Any?blacklistFlags=nsfw,religious,political,racist,sexist&type=twopart'
    ]
    
    api_url = random.choice(joke_apis)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if api_url.startswith('https://official-joke-api'):
                        joke_text = f"😂 **Joke Time!**\n\n{data['setup']}\n\n🤣 {data['punchline']}"
                    else:
                        joke_text = f"😂 **Joke Time!**\n\n{data['setup']}\n\n🤣 {data['delivery']}"
                    
                    return joke_text
                else:
                    return "Sorry, I couldn't fetch a joke right now. Please try again later."
    except Exception as e:
        logger.error(f"Joke error: {str(e)}")
        return "Sorry, I couldn't fetch a joke right now. Please try again later."

# News command
@client.on(events.NewMessage(pattern='/news'))
async def news_command(event):
    buttons = [
        [Button.inline("🌍 World", b"news_world"), Button.inline("💼 Business", b"news_business")],
        [Button.inline("🏥 Health", b"news_health"), Button.inline("🔬 Science", b"news_science")],
        [Button.inline("⚽ Sports", b"news_sports"), Button.inline("💻 Technology", b"news_technology")],
        [Button.inline("🔙 Back to Main Menu", b"main_menu")]
    ]
    await event.respond("📰 Select a news category:", buttons=buttons)

# Function to get news
async def get_news(category='general'):
    try:
        api_key = NEWS_API
        if not api_key:
            return "News API key is missing. Please set the NEWS_API environment variable."
            
        url = f'https://newsapi.org/v2/top-headlines?category={category}&pageSize=5&apiKey={api_key}'
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data['status'] == 'ok' and data['totalResults'] > 0:
                        news_text = f"📰 **Top {category.capitalize()} News:**\n\n"
                        
                        for i, article in enumerate(data['articles'][:5], 1):
                            title = article['title']
                            source = article['source']['name']
                            description = article.get('description', 'No description available')
                            
                            news_text += f"**{i}. {title}**\n"
                            news_text += f"Source: {source}\n"
                            news_text += f"{description}\n\n"
                        
                        news_text += f"📅 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        return news_text
                    else:
                        return f"No news available for the {category} category at the moment."
                else:
                    return f"Error: API returned status code {response.status}. Please check your News API key."
    except Exception as e:
        logger.error(f"News error: {str(e)}")
        return "Sorry, I couldn't fetch the news right now. Please try again later."

# Notes command
@client.on(events.NewMessage(pattern='/notes'))
async def notes_command(event):
    await notes_menu(event)

async def notes_menu(event):
    buttons = [
        [Button.inline("📝 Create Note", b"create_note"), Button.inline("📋 View Notes", b"view_notes")],
        [Button.inline("🔍 Find Note", b"find_note"), Button.inline("🗑️ Delete Note", b"delete_note")],
        [Button.inline("🔙 Back to Main Menu", b"main_menu")]
    ]
    await event.respond("📝 Notes Menu:", buttons=buttons)

# Reminders command
@client.on(events.NewMessage(pattern='/reminders'))
async def reminders_command(event):
    await reminder_menu(event)

async def reminder_menu(event):
    buttons = [
        [Button.inline("⏰ Set Reminder", b"set_reminder"), Button.inline("📋 View Reminders", b"view_reminders")],
        [Button.inline("🗑️ Delete Reminder", b"delete_reminder")],
        [Button.inline("🔙 Back to Main Menu", b"main_menu")]
    ]
    await event.respond("⏰ Reminders Menu:", buttons=buttons)

# Games command
@client.on(events.NewMessage(pattern='/games'))
async def games_command(event):
    await games_menu(event)

async def games_menu(event):
    buttons = [
        [Button.inline("🎲 Dice Game", b"game_dice"), Button.inline("🔢 Number Guess", b"game_number")],
        [Button.inline("✂️ Rock Paper Scissors", b"game_rps"), Button.inline("🎯 Trivia", b"game_trivia")],
        [Button.inline("🔙 Back to Main Menu", b"main_menu")]
    ]
    await event.respond("🎮 Games Menu:", buttons=buttons)

# Settings command
@client.on(events.NewMessage(pattern='/settings'))
async def settings_command(event):
    user_id = event.sender_id
    
    # Initialize user preferences if not exists
    if user_id not in user_preferences:
        user_preferences[user_id] = {
            "temperature_unit": "celsius",
            "language": "english",
            "notifications": True,
            "theme": "light",
            "notes": []
        }
    
    buttons = [
        [Button.inline("🌡️ Temperature Unit", b"settings_temp"), Button.inline("🔔 Notifications", b"settings_notif")],
        [Button.inline("🎨 Theme", b"settings_theme")],
        [Button.inline("🔙 Back to Main Menu", b"main_menu")]
    ]
    await event.respond("⚙️ Settings Menu:", buttons=buttons)

# Features command
@client.on(events.NewMessage(pattern='/features'))
async def features_command(event):
    features_text = (
        "🔍 **Available Features:**\n\n"
        "• 🌤️ **Weather**: Get current weather and forecasts\n"
        "• 😂 **Jokes**: Enjoy random jokes\n"
        "• 📰 **News**: Read the latest news by category\n"
        "• 📝 **Notes**: Create and manage notes\n"
        "• ⏰ **Reminders**: Set and manage reminders\n"
        "• 🎮 **Games**: Play fun mini-games\n"
        "• ⚙️ **Settings**: Customize your experience\n"
        "• ❓ **Help**: Get assistance with bot commands\n"
        "• ℹ️ **About**: Learn more about this bot\n\n"
        "What would you like to try?"
    )
    buttons = await get_main_menu_buttons()
    await event.respond(features_text, buttons=buttons)

# Joke callback
@client.on(events.CallbackQuery(data=b"joke"))
async def joke_callback(event):
    joke_text = await get_joke()
    buttons = [
        [Button.inline("😂 Another Joke", b"joke")],
        [Button.inline("🔙 Back to Main Menu", b"main_menu")]
    ]
    await event.edit(joke_text, buttons=buttons)

# Callback query handlers
@client.on(events.CallbackQuery)
async def handle_callback(event):
    data = event.data.decode('utf-8')
    user_id = event.sender_id
    
    # Main menu handlers
    if data == "main_menu":
        buttons = await get_main_menu_buttons()
        await event.edit("Main Menu:", buttons=buttons)
    
    elif data == "about":
        about_text = (
            "📱 **Telegram Assistant Bot**\n\n"
            "I'm a versatile bot designed to make your Telegram experience better.\n"
            "I can provide weather updates, tell jokes, deliver news, set reminders, and more!\n\n"
            "Version: 2.1.0\n"
            "Created with ❤️ using Telethon\n\n"
            "Type /help to see all available commands."
        )
        buttons = [[Button.inline("🔙 Back to Main Menu", b"main_menu")]]
        await event.edit(about_text, buttons=buttons)
    
    elif data == "help":
        buttons = [
            [Button.inline("🤖 Bot Commands", b"help_commands")],
            [Button.inline("🌐 Weather", b"help_weather"), Button.inline("📰 News", b"help_news")],
            [Button.inline("😂 Jokes", b"help_jokes"), Button.inline("🎮 Games", b"help_games")],
            [Button.inline("⏰ Reminders", b"help_reminders"), Button.inline("📝 Notes", b"help_notes")],
            [Button.inline("⚙️ Settings", b"help_settings")],
            [Button.inline("🔙 Back to Main Menu", b"main_menu")]
        ]
        await event.edit("Choose a help topic:", buttons=buttons)
    
    # Help submenu handlers
    elif data == "help_commands":
        commands_text = (
            "🤖 **Bot Commands:**\n\n"
            "/start - Start the bot and show main menu\n"
            "/help - Show help menu\n"
            "/about - Information about the bot\n"
            "/weather - Get weather updates\n"
            "/joke - Get a random joke\n"
            "/news - Browse news categories\n"
            "/notes - Manage your notes\n"
            "/reminders - Set and manage reminders\n"
            "/games - Play mini-games\n"
            "/settings - Customize your preferences\n"
            "/features - See all available features"
        )
        buttons = [[Button.inline("🔙 Back to Help", b"help")]]
        await event.edit(commands_text, buttons=buttons)
    
    elif data == "help_weather":
        help_text = (
            "🌤️ **Weather Feature:**\n\n"
            "Get current weather conditions and forecasts for any location.\n\n"
            "**Usage:**\n"
            "• /weather - Opens the weather menu\n"
            "• /weather [city] - Gets weather for specific city\n"
            "• Share your location - Gets weather for your current location\n\n"
            "The weather data includes temperature, condition, humidity, wind speed, and a 3-day forecast."
        )
        buttons = [[Button.inline("🔙 Back to Help", b"help")]]
        await event.edit(help_text, buttons=buttons)
    
    elif data == "help_news":
        help_text = (
            "📰 **News Feature:**\n\n"
            "Get the latest news from various categories.\n\n"
            "**Usage:**\n"
            "• /news - Opens the news category menu\n\n"
            "**Available Categories:**\n"
            "• World\n• Business\n• Health\n• Science\n• Sports\n• Technology"
        )
        buttons = [[Button.inline("🔙 Back to Help", b"help")]]
        await event.edit(help_text, buttons=buttons)
    
    elif data == "help_jokes":
        help_text = (
            "😂 **Jokes Feature:**\n\n"
            "Enjoy random jokes for entertainment.\n\n"
            "**Usage:**\n"
            "• /joke - Get a random joke\n"
            "• 'Another Joke' button - Get another random joke"
        )
        buttons = [[Button.inline("🔙 Back to Help", b"help")]]
        await event.edit(help_text, buttons=buttons)
    
    elif data == "help_games":
        help_text = (
            "🎮 **Games Feature:**\n\n"
            "Play fun mini-games right in your chat.\n\n"
            "**Available Games:**\n"
            "• 🎲 Dice Game - Roll dice and try your luck\n"
            "• 🔢 Number Guess - Guess a number between 1-100\n"
            "• ✂️ Rock Paper Scissors - Play against the bot\n"
            "• 🎯 Trivia - Test your knowledge\n\n"
            "Use /games to access the games menu."
        )
        buttons = [[Button.inline("🔙 Back to Help", b"help")]]
        await event.edit(help_text, buttons=buttons)
    
    elif data == "help_reminders":
        help_text = (
            "⏰ **Reminders Feature:**\n\n"
            "Set and manage reminders for important tasks.\n\n"
            "**Usage:**\n"
            "• /reminders - Opens the reminders menu\n"
            "• 'Set Reminder' - Create a new reminder\n"
            "• 'View Reminders' - See all your active reminders\n"
            "• 'Delete Reminder' - Remove a specific reminder\n\n"
            "You can set reminders using formats like:\n"
            "• 10m (10 minutes)\n• 2h (2 hours)\n• 1d (1 day)\n• 14:30 (specific time)"
        )
        buttons = [[Button.inline("🔙 Back to Help", b"help")]]
        await event.edit(help_text, buttons=buttons)
    
    elif data == "help_notes":
        help_text = (
            "📝 **Notes Feature:**\n\n"
            "Create and manage personal notes.\n\n"
            "**Usage:**\n"
            "• /notes - Opens the notes menu\n"
            "• 'Create Note' - Add a new note\n"
            "• 'View Notes' - See all your saved notes\n"
            "• 'Find Note' - Search for specific notes\n"
            "• 'Delete Note' - Remove a specific note"
        )
        buttons = [[Button.inline("🔙 Back to Help", b"help")]]
        await event.edit(help_text, buttons=buttons)
    
    elif data == "help_settings":
        help_text = (
            "⚙️ **Settings Feature:**\n\n"
            "Customize your bot experience.\n\n"
            "**Available Settings:**\n"
            "• 🌡️ Temperature Unit - Choose between Celsius/Fahrenheit\n"
            "• 🔔 Notifications - Enable/disable notifications\n"
            "• 🎨 Theme - Choose between light/dark theme\n\n"
            "Your settings are saved for future sessions."
        )
        buttons = [[Button.inline("🔙 Back to Help", b"help")]]
        await event.edit(help_text, buttons=buttons)
    
    # News category handlers
    elif data.startswith("news_"):
        category = data.split("_")[1]
        news_text = await get_news(category)
        
        buttons = [
            [Button.inline("🔙 News Categories", b"news_menu")],
            [Button.inline("🔄 Refresh", f"news_{category}")],
            [Button.inline("🔙 Main Menu", b"main_menu")]
        ]
        await event.edit(news_text, buttons=buttons)
    
    elif data == "news_menu":
        buttons = [
            [Button.inline("🌍 World", b"news_world"), Button.inline("💼 Business", b"news_business")],
            [Button.inline("🏥 Health", b"news_health"), Button.inline("🔬 Science", b"news_science")],
            [Button.inline("⚽ Sports", b"news_sports"), Button.inline("💻 Technology", b"news_technology")],
            [Button.inline("🔙 Back to Main Menu", b"main_menu")]
        ]
        await event.edit("📰 Select a news category:", buttons=buttons)
    
    # Notes menu handlers
    elif data == "notes_menu":
        await notes_menu(event)
    
    elif data == "create_note":
        await event.edit("Please enter a title for your note:")
        user_states[user_id] = "waiting_for_note_title"
    
    elif data == "view_notes":
        if user_id not in user_preferences or "notes" not in user_preferences[user_id] or not user_preferences[user_id]["notes"]:
            buttons = [
                [Button.inline("📝 Create Note", b"create_note")],
                [Button.inline("🔙 Notes Menu", b"notes_menu")]
            ]
            await event.edit("You don't have any notes yet. Create one?", buttons=buttons)
        else:
            notes = user_preferences[user_id]["notes"]
            notes_text = "📝 **Your Notes:**\n\n"
            
            for note in notes:
                created_at = note.get("created_at", "Unknown date")
                notes_text += f"**{note['title']}** (ID: {note['id']})\n"
                notes_text += f"Created: {created_at}\n\n"
            
            buttons = [
                [Button.inline("📝 Create Note", b"create_note"), Button.inline("📖 View Note", b"view_note_by_id")],
                [Button.inline("🗑️ Delete Note", b"delete_note"), Button.inline("🔙 Notes Menu", b"notes_menu")]
            ]
            await event.edit(notes_text, buttons=buttons)
    
    elif data == "view_note_by_id":
        if user_id not in user_preferences or "notes" not in user_preferences[user_id] or not user_preferences[user_id]["notes"]:
            buttons = [[Button.inline("🔙 Notes Menu", b"notes_menu")]]
            await event.edit("You don't have any notes yet.", buttons=buttons)
        else:
            await event.edit("Please enter the ID of the note you want to view:")
            user_states[user_id] = "waiting_for_note_id"
    
    elif data == "delete_note":
        if user_id not in user_preferences or "notes" not in user_preferences[user_id] or not user_preferences[user_id]["notes"]:
            buttons = [[Button.inline("🔙 Notes Menu", b"notes_menu")]]
            await event.edit("You don't have any notes to delete.", buttons=buttons)
        else:
            await event.edit("Please enter the ID of the note you want to delete:")
            user_states[user_id] = "waiting_for_note_delete_id"
    
    elif data == "find_note":
        await event.edit("Please enter a keyword to search in your notes:")
        user_states[user_id] = "waiting_for_note_search"
    
    # Reminder menu handlers
    elif data == "reminder_menu":
        await reminder_menu(event)
    
    elif data == "set_reminder":
        await event.edit("Please enter the text for your reminder (what you want to be reminded about):")
        user_states[user_id] = "waiting_for_reminder_text"
    
    elif data == "view_reminders":
        if user_id not in user_reminders or not user_reminders[user_id]:
            buttons = [
                [Button.inline("⏰ Set Reminder", b"set_reminder")],
                [Button.inline("🔙 Reminders Menu", b"reminder_menu")]
            ]
            await event.edit("You don't have any active reminders. Set one?", buttons=buttons)
        else:
            reminders = user_reminders[user_id]
            reminders_text = "⏰ **Your Active Reminders:**\n\n"
            
            for reminder in reminders:
                reminder_time = datetime.fromtimestamp(reminder["time"])
                time_str = reminder_time.strftime('%Y-%m-%d %H:%M:%S')
                
                reminders_text += f"**{reminder['text']}** (ID: {reminder['id']})\n"
                reminders_text += f"Time: {time_str}\n\n"
            
            buttons = [
                [Button.inline("⏰ Set Reminder", b"set_reminder"), Button.inline("🗑️ Delete Reminder", b"delete_reminder")],
                [Button.inline("🔙 Reminders Menu", b"reminder_menu")]
            ]
            await event.edit(reminders_text, buttons=buttons)
    
    elif data == "delete_reminder":
        if user_id not in user_reminders or not user_reminders[user_id]:
            buttons = [[Button.inline("🔙 Reminders Menu", b"reminder_menu")]]
            await event.edit("You don't have any active reminders to delete.", buttons=buttons)
        else:
            await event.edit("Please enter the ID of the reminder you want to delete:")
            user_states[user_id] = "waiting_for_reminder_delete_id"
    
    # Games menu handlers
    elif data == "games_menu":
        await games_menu(event)
    
    elif data == "game_dice":
        # Roll a dice
        dice_result = random.randint(1, 6)
        
        buttons = [
            [Button.inline("🎲 Roll Again", b"game_dice")],
            [Button.inline("🔙 Games Menu", b"games_menu")]
        ]
        await event.edit(f"🎲 You rolled a **{dice_result}**!", buttons=buttons)
    
    elif data == "game_number":
        # Start a number guessing game
        number = random.randint(1, 100)
        user_states[user_id] = {"state": "playing_number_guess", "number": number, "attempts": 0}
        
        await event.edit(
            "🔢 **Number Guessing Game**\n\n"
            "I'm thinking of a number between 1 and 100.\n"
            "Try to guess it in as few attempts as possible!\n\n"
            "Enter your guess:"
        )
    
    elif data == "game_rps":
        # Rock Paper Scissors game
        buttons = [
            [Button.inline("✊ Rock", b"rps_rock"), Button.inline("✋ Paper", b"rps_paper"), Button.inline("✂️ Scissors", b"rps_scissors")],
            [Button.inline("🔙 Games Menu", b"games_menu")]
        ]
        await event.edit("✂️ **Rock Paper Scissors**\n\nMake your choice:", buttons=buttons)
    
    elif data.startswith("rps_"):
        player_choice = data.split("_")[1]
        choices = ["rock", "paper", "scissors"]
        bot_choice = random.choice(choices)
        
        # Determine winner
        if player_choice == bot_choice:
            result = "It's a tie! 🤝"
        elif (player_choice == "rock" and bot_choice == "scissors") or \
             (player_choice == "paper" and bot_choice == "rock") or \
             (player_choice == "scissors" and bot_choice == "paper"):
            result = "You win! 🎉"
        else:
            result = "I win! 😎"
        
        # Emojis for choices
        choice_emojis = {"rock": "✊", "paper": "✋", "scissors": "✂️"}
        
        buttons = [
            [Button.inline("🎮 Play Again", b"game_rps")],
            [Button.inline("🔙 Games Menu", b"games_menu")]
        ]
        await event.edit(
            f"✂️ **Rock Paper Scissors**\n\n"
            f"Your choice: {choice_emojis[player_choice]} {player_choice.capitalize()}\n"
            f"My choice: {choice_emojis[bot_choice]} {bot_choice.capitalize()}\n\n"
            f"**{result}**",
            buttons=buttons
        )
    
    elif data == "game_trivia":
        # Trivia game
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://opentdb.com/api.php?amount=1&type=multiple') as response:
                    if response.status == 200:
                        data = await response.json()
                        if data['response_code'] == 0 and data['results']:
                            question_data = data['results'][0]
                            question = question_data['question']
                            correct_answer = question_data['correct_answer']
                            answers = question_data['incorrect_answers'] + [correct_answer]
                            random.shuffle(answers)
                            
                            trivia_answers[user_id] = correct_answer
                            
                            buttons = []
                            for i, answer in enumerate(answers):
                                buttons.append([Button.inline(answer, f"trivia_{i}")])
                            
                            buttons.append([Button.inline("🔙 Games Menu", b"games_menu")])
                            
                            await event.edit(
                                f"🎯 **Trivia Question**\n\n"
                                f"Category: {question_data['category']}\n"
                                f"Difficulty: {question_data['difficulty'].capitalize()}\n\n"
                                f"Question: {question}\n\n"
                                f"Select your answer:",
                                buttons=buttons
                            )
                        else:
                            await event.edit("Failed to fetch a trivia question. Please try again.")
                    else:
                        await event.edit("Failed to fetch a trivia question. Please try again.")
        except Exception as e:
            logger.error(f"Trivia error: {str(e)}")
            await event.edit("An error occurred while fetching the trivia question. Please try again.")
    
    elif data.startswith("trivia_"):
        if user_id in trivia_answers:
            correct_answer = trivia_answers[user_id]
            user_answer = event.data_match.group().decode('utf-8').split('_')[1]
            answer_index = int(user_answer)
            
            # Get the actual answer text from the button
            answer_text = None
            for row in event.message.buttons:
                for button in row:
                    if button.data == event.data:
                        answer_text = button.text
                        break
                if answer_text:
                    break
            
            if answer_text == correct_answer:
                result = "✅ Correct! Great job!"
                # Update user's score
                if user_id not in user_scores:
                    user_scores[user_id] = {"trivia": 1}
                elif "trivia" not in user_scores[user_id]:
                    user_scores[user_id]["trivia"] = 1
                else:
                    user_scores[user_id]["trivia"] += 1
            else:
                result = f"❌ Wrong! The correct answer was: {correct_answer}"
            
            buttons = [
                [Button.inline("🎯 Another Question", b"game_trivia")],
                [Button.inline("🔙 Games Menu", b"games_menu")]
            ]
            
            await event.edit(
                f"🎯 **Trivia Result**\n\n"
                f"{result}\n\n"
                f"Your score: {user_scores.get(user_id, {}).get('trivia', 0)}",
                buttons=buttons
            )
            
            # Clear the stored answer
            if user_id in trivia_answers:
                del trivia_answers[user_id]
    
    # Settings handlers
    elif data == "settings":
        user_prefs = user_preferences.get(user_id, {
            "temperature_unit": "celsius",
            "language": "english",
            "notifications": True,
            "theme": "light",
            "notes": []
        })
        
        buttons = [
            [Button.inline("🌡️ Temperature Unit", b"settings_temp"), Button.inline("🔔 Notifications", b"settings_notif")],
            [Button.inline("🎨 Theme", b"settings_theme")],
            [Button.inline("🔙 Back to Main Menu", b"main_menu")]
        ]
        
        await event.edit(
            f"⚙️ **Your Settings:**\n\n"
            f"🌡️ Temperature Unit: {user_prefs.get('temperature_unit', 'celsius').capitalize()}\n"
            f"🔔 Notifications: {'Enabled' if user_prefs.get('notifications', True) else 'Disabled'}\n"
            f"🎨 Theme: {user_prefs.get('theme', 'light').capitalize()}\n",
            buttons=buttons
        )
    
    elif data == "settings_temp":
        current_unit = user_preferences.get(user_id, {}).get('temperature_unit', 'celsius')
        buttons = [
            [Button.inline("°C Celsius", b"set_temp_celsius"), Button.inline("°F Fahrenheit", b"set_temp_fahrenheit")],
            [Button.inline("🔙 Back to Settings", b"settings")]
        ]
        await event.edit(
            f"🌡️ **Temperature Unit**\n\n"
            f"Current setting: {current_unit.capitalize()}\n\n"
            f"Select your preferred unit:",
            buttons=buttons
        )
    
    elif data == "set_temp_celsius":
        if user_id not in user_preferences:
            user_preferences[user_id] = {}
        user_preferences[user_id]['temperature_unit'] = 'celsius'
        await event.edit("✅ Temperature unit set to Celsius", buttons=[[Button.inline("🔙 Back to Settings", b"settings")]])
    
    elif data == "set_temp_fahrenheit":
        if user_id not in user_preferences:
            user_preferences[user_id] = {}
        user_preferences[user_id]['temperature_unit'] = 'fahrenheit'
        await event.edit("✅ Temperature unit set to Fahrenheit", buttons=[[Button.inline("🔙 Back to Settings", b"settings")]])
    
    elif data == "settings_notif":
        current_status = user_preferences.get(user_id, {}).get('notifications', True)
        buttons = [
            [Button.inline("🔔 Enable", b"set_notif_on"), Button.inline("🔕 Disable", b"set_notif_off")],
            [Button.inline("🔙 Back to Settings", b"settings")]
        ]
        await event.edit(
            f"🔔 **Notifications**\n\n"
            f"Current setting: {'Enabled' if current_status else 'Disabled'}\n\n"
            f"Select your preference:",
            buttons=buttons
        )
    
    elif data == "set_notif_on":
        if user_id not in user_preferences:
            user_preferences[user_id] = {}
        user_preferences[user_id]['notifications'] = True
        await event.edit("✅ Notifications enabled", buttons=[[Button.inline("🔙 Back to Settings", b"settings")]])
    
    elif data == "set_notif_off":
        if user_id not in user_preferences:
            user_preferences[user_id] = {}
        user_preferences[user_id]['notifications'] = False
        await event.edit("✅ Notifications disabled", buttons=[[Button.inline("🔙 Back to Settings", b"settings")]])
    
    elif data == "settings_theme":
        current_theme = user_preferences.get(user_id, {}).get('theme', 'light')
        buttons = [
            [Button.inline("☀️ Light", b"set_theme_light"), Button.inline("🌙 Dark", b"set_theme_dark")],
            [Button.inline("🔙 Back to Settings", b"settings")]
        ]
        await event.edit(
            f"🎨 **Theme**\n\n"
            f"Current setting: {current_theme.capitalize()}\n\n"
            f"Select your preference:",
            buttons=buttons
        )
    
    elif data == "set_theme_light":
        if user_id not in user_preferences:
            user_preferences[user_id] = {}
        user_preferences[user_id]['theme'] = 'light'
        await event.edit("✅ Theme set to Light", buttons=[[Button.inline("🔙 Back to Settings", b"settings")]])
    
    elif data == "set_theme_dark":
        if user_id not in user_preferences:
            user_preferences[user_id] = {}
        user_preferences[user_id]['theme'] = 'dark'
        await event.edit("✅ Theme set to Dark", buttons=[[Button.inline("🔙 Back to Settings", b"settings")]])

# Run the client
async def main():
    await client.run_until_disconnected()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("Bot stopped by user!")
    finally:
        loop.close()