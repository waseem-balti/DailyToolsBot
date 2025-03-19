from telethon import TelegramClient, events
from telethon.tl.custom import Button
import time, os, dotenv, logging, aiohttp

#credentials
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
W_API =  os.getenv('W_API')

# Initialize the Telegram client
client = TelegramClient('s1', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Dictionary to track user messages for rate-limiting
user_last_message = {}

# Rate-limiting handler
@client.on(events.NewMessage)
async def rate_limited_handler(event):
    # Ignore commands (messages starting with '/')
    if event.message.text.startswith('/'):
        return

    user_id = event.sender_id
    current_time = time.time()

    # Check if the user is sending messages too quickly
    if user_id in user_last_message and current_time - user_last_message[user_id] < 5:
        await event.respond("Please wait a few seconds before sending another message.")
        return

    # Update the last message time for the user
    user_last_message[user_id] = current_time
    await event.respond("/help for help")

# Logging setup
logging.basicConfig(level=logging.INFO)

# Echo handler for non-command messages
@client.on(events.NewMessage)
async def echo(event):
    # Log the message
    logging.info(f"User {event.sender_id} sent: {event.message.text}")
    # Echo the message back to the user
    await event.respond(event.message.text)


# Start command
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond('Hello! I am your bot. How can I assist you today?')

# Dictionary to map numbers to help topics
help_topics = {
    "1": "Start the bot: Use the /start command to initiate the bot and get a welcome message.",
    "2": "Help: Use the /help command to see this menu.",
    "3": "About: Use the /about command to learn more about the bot.",
    "4": "Weather: Use the /weather(City) command to get weather information for a specific city.",
    "5": "Joke: Use the /joke command to get a random joke.",
    "6": "Menu: Use the /menu command to see an interactive menu with options.",
    "7": "Features: Use the /features command to list all available features."
}

# Help command
@client.on(events.NewMessage(pattern='/help'))
async def help(event):
    help_text = (
        "Reply with a number to get detailed help about a specific feature:\n"
        "1. Start\n"
        "2. Help\n"
        "3. About\n"
        "4. Weather\n"
        "5. Joke\n"
        "6. Menu\n"
        "7. Features"
    )
    await event.respond(help_text)

# Handler for numbered replies to the help menu
@client.on(events.NewMessage)
async def help_reply(event):
    user_reply = event.message.text.strip()
    if user_reply in help_topics:
        await event.respond(help_topics[user_reply])

# About command
@client.on(events.NewMessage(pattern='/about'))
async def about(event):
    about_text = (
        "I am a simple Telegram bot built using the Telethon library.\n"
        "You can customize me to add more features!"
    )
    await event.respond(about_text)

# Weather command
@client.on(events.NewMessage(pattern='/weather(.+)'))
async def weather(event):
    try:
        city = event.pattern_match.group(1)
        api_key = W_API
        url = f'http://api.weatherapi.com/v1/current.json?q={city}&key={api_key}&aqi=no'

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    weather_info = (
                        f"Weather in {city}:\n"
                        f"Temperature: {data['current']['temp_c']}°C\n"
                        f"Condition: {data['current']['condition']['text']}\n"
                        f"Humidity: {data['current']['humidity']}%\n"
                        f"Wind Speed: {data['current']['wind_kph']} km/h"
                    )
                    await event.respond(weather_info)
                else:
                    await event.respond("Sorry, I couldn't fetch the weather for that location.")
    except Exception as e:
        await event.respond("An error occurred while fetching the weather. Please try again.")

# Joke command
@client.on(events.NewMessage(pattern='/joke'))
async def joke(event):
    url = 'https://official-joke-api.appspot.com/random_joke'

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                joke_text = f"{data['setup']} - {data['punchline']}"
                await event.respond(joke_text)
            else:
                await event.respond("Sorry, I couldn't fetch a joke right now.")

# Menu command with interactive buttons
@client.on(events.NewMessage(pattern='/menu'))
async def menu(event):
    buttons = [
        [Button.text("Option 1"), Button.text("Option 2")],
        [Button.text("Option 3"), Button.text("Option 4")]
    ]
    await event.respond("Choose an option:", buttons=buttons)

# Start the bot
client.run_until_disconnected()