import discord
import os
import random
import time
import json
from dotenv import load_dotenv
import pykakasi # For Romaji conversion

# Load environment variables from .env file
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Check if the bot token is loaded
if BOT_TOKEN is None:
    print("Error: BOT_TOKEN not found in .env file. Make sure you have a .env file with BOT_TOKEN set.")
    exit()

# --- Configuration Variables ---
CONFIG_FILE = 'shibako_phrases.json' # Name of your config file
TRIGGER_MAP = {} # Dictionary to map triggers to their config
RUDE_RESPONSE_CONFIG = {} # Store the global rude response settings
SHIBA_EMOJI = "<:shiba:1363005589902589982>" # Default emoji string, can be overridden by config
ERROR_MESSAGES = {} # Dictionary for user-facing error messages loaded from config

# --- Instantiate PyKakasi (Simplified Initialization) ---
# This handles the Japanese to Romaji conversion
try:
    # Initialize without the config dictionary (simplest approach)
    kks = pykakasi.kakasi()
    # Store the convert method
    romaji_converter_func = kks.convert
    print("PyKakasi Romaji converter initialized (Simplified).")
except Exception as e:
    print(f"Error initializing PyKakasi: {e}")
    print("Romaji conversion will not be available.")
    romaji_converter_func = None
# --- ---

# --- Function to Load Configuration from JSON ---
def load_config(filename):
    """Loads configuration from the JSON file."""
    global TRIGGER_MAP, RUDE_RESPONSE_CONFIG, SHIBA_EMOJI, ERROR_MESSAGES # Allow modification of global vars
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        new_trigger_map = {}
        # Populate the trigger map for fast lookups
        for phrase_config in config_data.get('phrases', []):
            # Store the necessary parts of the config for each trigger
            config_details = {
                "name": phrase_config.get("name", "unknown"),
                "response": phrase_config.get("response", "..."), # Default response
                "allow_rude": phrase_config.get("allow_rude_response", False)
            }
            for trigger in phrase_config.get('triggers', []):
                # Ensure triggers are lowercase for case-insensitive matching
                new_trigger_map[trigger.lower()] = config_details

        TRIGGER_MAP = new_trigger_map
        RUDE_RESPONSE_CONFIG = config_data.get('rude_response', {})
        # Load custom emoji string from config, otherwise use default
        SHIBA_EMOJI = config_data.get('shiba_emoji_string', SHIBA_EMOJI)
        ERROR_MESSAGES = config_data.get('error_messages', {}) # Load error messages

        print(f"Loaded configuration from {filename}")
        print(f"Found {len(TRIGGER_MAP)} triggers.")
        if ERROR_MESSAGES:
             print(f"Loaded {len(ERROR_MESSAGES)} error messages.")
        else:
             print("Warning: No error messages found in config.")
        return True # Indicate success

    except FileNotFoundError:
        print(f"Error: {filename} not found. Please ensure it exists.")
        # Set defaults so the bot can potentially still run basic commands
        TRIGGER_MAP = {}
        RUDE_RESPONSE_CONFIG = {}
        ERROR_MESSAGES = {}
        return False # Indicate failure but allow continuation if desired
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {filename}. Check file format.")
        return False # Critical error, likely should exit
    except Exception as e:
        print(f"An unexpected error occurred loading configuration: {e}")
        return False # Critical error
# --- ---

# --- Load the configuration on startup ---
if not load_config(CONFIG_FILE):
    # Decide if bot should exit if config loading fails completely
    print("Warning: Configuration loading failed. Bot functionality may be limited.")
    # exit() # Uncomment this line if you want the bot to stop on config errors
# --- ---

# --- Discord Client Setup ---
# Define the intents your bot needs. Message Content is crucial.
intents = discord.Intents.default()
intents.message_content = True # Make sure this is enabled in the Discord Developer Portal!

# Create a bot instance with the defined intents
client = discord.Client(intents=intents)

# Seed the random number generator (for rude responses)
random.seed()

# --- Event Handlers ---
@client.event
async def on_ready():
    """Event handler for when the bot logs in and is ready."""
    print(f'We have logged in as {client.user}')
    print('Bot is ready!')
    print('-------------------')

@client.event
async def on_message(message):
    """Event handler for when a message is received."""
    # Ignore messages sent by the bot itself to prevent loops
    if message.author == client.user:
        return

    # Get message content in lowercase once for efficiency
    msg_lower = message.content.lower()

    # --- Handle Specific Commands First ---

    # !help Command
    if msg_lower == '!help':
        help_message = f"""{SHIBA_EMOJI} こんにちは！ しばこです。 (Hello! I'm Shibako.)

わたしができること： (Things I can do:)
`!help` - Shows this help message.
`!phrases` - Shows all the phrases I might react to.
`!romaji <japanese text>` - Converts Japanese text to Romaji. (e.g., `!romaji こんにちは`)

いろいろな　フレーズの　れい： (Examples of various phrases I might react to:)
`say the line shibako`
`good bot`
`hi shibako`
`pat shibako`
`shibako fetch`
`!y` / `!n`

(ためしてみてね！ - Try them out!)"""
        try:
            await message.channel.send(help_message)
        except discord.errors.Forbidden:
            print(f"Error: Cannot send message in channel {message.channel.id}. Missing permissions?")
        except Exception as e:
            print(f"Error sending help message: {e}")
        return # Stop processing after handling the command

    # !phrases Command
    elif msg_lower == '!phrases':
        if not TRIGGER_MAP:
            error_msg = ERROR_MESSAGES.get("phrases_list_empty", "なにも　フレーズが　みつかりません。")
            await message.channel.send(f"{SHIBA_EMOJI} {error_msg}")
            return

        all_triggers = sorted(list(TRIGGER_MAP.keys())) # Get and sort triggers

        header = f"{SHIBA_EMOJI} わたしが　はんのうする　かもしれない　フレーズ： (Phrases I might react to:)\n```\n"
        footer = "\n```"
        body = "\n".join(all_triggers)
        full_message = header + body + footer

        # Check if the message exceeds Discord's approx limit
        if len(full_message) > 1900: # Leave some buffer room
             limit_msg = ERROR_MESSAGES.get("phrases_list_too_long", "たくさん　ありすぎて　ぜんぶは　みせられない！")
             await message.channel.send(f"{SHIBA_EMOJI} {limit_msg}")
        else:
            try:
                await message.channel.send(full_message)
            except discord.errors.Forbidden:
                 print(f"Error: Cannot send !phrases list in channel {message.channel.id}. Missing permissions?")
            except Exception as e:
                print(f"Error sending phrases list message: {e}")
        return # Stop processing after handling the command

    # !romaji Command
    romaji_command = "!romaji "
    if msg_lower.startswith(romaji_command):
        if romaji_converter_func: # Check if the converter function is available
            text_to_convert = message.content[len(romaji_command):].strip()
            if not text_to_convert:
                error_msg = ERROR_MESSAGES.get("romaji_no_input", "テキストをいれてください。")
                await message.channel.send(f"{SHIBA_EMOJI} {error_msg}")
                return

            try:
                # Use the stored convert function directly
                result = romaji_converter_func(text_to_convert)
                romaji_parts = [item['hepburn'] for item in result] # Extract Hepburn romaji
                romaji_text = ' '.join(romaji_parts) # Join parts with spaces manually
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
             # Converter was not initialized properly
             error_msg = ERROR_MESSAGES.get("romaji_converter_unavailable", "ローマジへんかんきはつかえません。")
             await message.channel.send(f"{SHIBA_EMOJI} {error_msg}")
        return # Stop processing after handling the command

    # --- Handle Configured Triggers (if no command matched) ---
    message_sender_id = message.author.id
    matched_config = TRIGGER_MAP.get(msg_lower) # Check against loaded triggers

    if matched_config:
        allow_rude = matched_config.get('allow_rude', False)
        standard_response = matched_config.get('response', '...')

        rude_chance = RUDE_RESPONSE_CONFIG.get('chance', 0.0)
        rude_prefix = RUDE_RESPONSE_CONFIG.get('prefix', '')
        rude_template = RUDE_RESPONSE_CONFIG.get('message', '')

        should_be_rude = allow_rude and random.random() < rude_chance

        try:
            # Check if rude response should be sent and if template is valid
            if should_be_rude and rude_template and '{message_sender}' in rude_template:
                if rude_prefix:
                    time.sleep(1) # Keep the pause effect
                    await message.channel.send(rude_prefix)

                # Format the rude message (replace placeholder)
                formatted_rude_message = rude_template.format(message_sender=message_sender_id)
                time.sleep(1)
                await message.channel.send(formatted_rude_message)
            else:
                # Send the standard response
                time.sleep(1) # Keep the pause effect
                await message.channel.send(standard_response)
        except discord.errors.Forbidden:
             print(f"Error: Cannot send triggered response in channel {message.channel.id}. Missing permissions?")
        except Exception as e:
             print(f"Error sending triggered response: {e}")


# --- Run the Bot ---
try:
    client.run(BOT_TOKEN)
except discord.LoginFailure:
    print("Login Failed: Improper token has been passed. Check your .env file.")
except discord.errors.PrivilegedIntentsRequired:
     print("Privileged Intents Error: Make sure 'Message Content Intent' is enabled under the 'Privileged Gateway Intents' section on the Discord Developer Portal for your bot application.")
except Exception as e:
    print(f"An critical error occurred while running the bot: {e}")