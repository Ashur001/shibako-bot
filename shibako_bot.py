import discord
import os
import random
import time
import json
from dotenv import load_dotenv
import pykakasi

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if BOT_TOKEN is None:
    print("Error: BOT_TOKEN not found. Make sure you have a .env file with BOT_TOKEN set.")
    exit()

# Use the correct filename
CONFIG_FILE = 'shibako_phrases.json'
TRIGGER_MAP = {}
RUDE_RESPONSE_CONFIG = {}
SHIBA_EMOJI = "<:shiba:1363005589902589982>" # Default emoji
ERROR_MESSAGES = {}

# --- Instantiate PyKakasi (Simplified Initialization) ---
try:
    kks = pykakasi.kakasi()
    romaji_converter_func = kks.convert
    print("PyKakasi Romaji converter initialized (Simplified).")
except Exception as e:
    print(f"Error initializing PyKakasi: {e}")
    print("Romaji conversion will not be available.")
    romaji_converter_func = None
# --- ---

# --- Function to Load Configuration ---
def load_config(filename):
    """Loads configuration from a JSON file and builds the trigger map."""
    global TRIGGER_MAP, RUDE_RESPONSE_CONFIG, SHIBA_EMOJI, ERROR_MESSAGES
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        new_trigger_map = {}
        for phrase_config in config_data.get('phrases', []):
            config_details = {
                "name": phrase_config.get("name", "unknown"),
                "response": phrase_config.get("response", "..."),
                "allow_rude": phrase_config.get("allow_rude_response", False)
            }
            for trigger in phrase_config.get('triggers', []):
                new_trigger_map[trigger.lower()] = config_details

        TRIGGER_MAP = new_trigger_map
        RUDE_RESPONSE_CONFIG = config_data.get('rude_response', {})
        # Load emoji string, keeping default if not found
        SHIBA_EMOJI = config_data.get('shiba_emoji_string', SHIBA_EMOJI)
        ERROR_MESSAGES = config_data.get('error_messages', {})

        print(f"Loaded configuration from {filename}")
        print(f"Found {len(TRIGGER_MAP)} triggers.")
        if ERROR_MESSAGES:
             print(f"Loaded {len(ERROR_MESSAGES)} error messages.")
        else:
             print("Warning: No error messages found in config.")
        return True

    except FileNotFoundError:
        print(f"Error: {filename} not found. Bot cannot process triggers.")
        return False
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {filename}. Check file format.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred loading configuration: {e}")
        return False
# --- ---

# --- Load the configuration on startup ---
if not load_config(CONFIG_FILE):
    print("Exiting due to configuration loading errors.")
    exit()
# --- ---

# Define the intents
intents = discord.Intents.default()
intents.message_content = True

# Create a bot instance
client = discord.Client(intents=intents)

random.seed()

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    print('Bot is ready!')
    print('-------------------')

@client.event
async def on_message(message):
    # Ignore messages sent by the bot itself
    if message.author == client.user:
        return

    # Process commands first
    msg_lower = message.content.lower()

    # --- Handle Help Command ---
    if msg_lower == '!help':
        help_message = f"""{SHIBA_EMOJI} こんにちは！ しばこです。 (Hello! I'm Shibako.)

わたしができること： (Things I can do:)
`!help` - Shows this help message.
`!romaji <japanese text>` - Converts Japanese text to Romaji. (e.g., `!romaji こんにちは`)

あとは、いろいろな　フレーズに　はんのうするかも…？ (Also, I might react to various phrases...?)"""
        await message.channel.send(help_message)
        return # Stop processing after handling the command

    # --- Handle Romaji Command ---
    romaji_command = "!romaji "
    if msg_lower.startswith(romaji_command):
        # Check if the converter function is available
        if romaji_converter_func:
            text_to_convert = message.content[len(romaji_command):].strip()
            if not text_to_convert:
                error_msg = ERROR_MESSAGES.get("romaji_no_input", "テキストをいれてください。")
                await message.channel.send(f"{SHIBA_EMOJI} {error_msg}")
                return

            try:
                result = romaji_converter_func(text_to_convert)
                romaji_parts = [item['hepburn'] for item in result]
                romaji_text = ' '.join(romaji_parts)
                response = f'{SHIBA_EMOJI} "{romaji_text}"'
                await message.channel.send(response)
            except KeyError:
                print(f"Error during Romaji conversion: 'hepburn' key missing in result for '{text_to_convert}'. Result: {result}")
                error_msg = ERROR_MESSAGES.get("romaji_conversion_failed", "へんかんできませんでした。")
                await message.channel.send(f"{SHIBA_EMOJI} {error_msg}")
            except Exception as e:
                print(f"Error during Romaji conversion for '{text_to_convert}': {e}")
                error_msg = ERROR_MESSAGES.get("romaji_conversion_failed", "へんかんできませんでした。")
                await message.channel.send(f"{SHIBA_EMOJI} {error_msg}")
        else:
             error_msg = ERROR_MESSAGES.get("romaji_converter_unavailable", "ローマジへんかんきはつかえません。")
             await message.channel.send(f"{SHIBA_EMOJI} {error_msg}")
        return # Stop processing after handling the command

    # --- Handle Configured Triggers ---
    # (Only check these if it wasn't a specific command above)
    message_sender_id = message.author.id
    # Use msg_lower which is already calculated
    matched_config = TRIGGER_MAP.get(msg_lower)

    if matched_config:
        allow_rude = matched_config.get('allow_rude', False)
        standard_response = matched_config.get('response', '...')

        rude_chance = RUDE_RESPONSE_CONFIG.get('chance', 0.0)
        rude_prefix = RUDE_RESPONSE_CONFIG.get('prefix', '')
        rude_template = RUDE_RESPONSE_CONFIG.get('message', '')

        should_be_rude = allow_rude and random.random() < rude_chance

        if should_be_rude and rude_template and '{message_sender}' in rude_template:
            if rude_prefix:
                time.sleep(1)
                await message.channel.send(rude_prefix)

            formatted_rude_message = rude_template.format(message_sender=message_sender_id)
            time.sleep(1)
            await message.channel.send(formatted_rude_message)
        else:
            time.sleep(1)
            await message.channel.send(standard_response)

# Run the bot
# (Try/except block remains the same)
try:
    client.run(BOT_TOKEN)
except discord.LoginFailure:
    print("Login Failed: Improper token has been passed.")
except discord.errors.PrivilegedIntentsRequired:
     print("Privileged Intents Error: Make sure 'Message Content Intent' is enabled on the Discord Developer Portal for your bot.")
except Exception as e:
    print(f"An error occurred while running the bot: {e}")