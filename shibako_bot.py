import discord
import os
import random
import time
import json # <--- Import json
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if BOT_TOKEN is None:
    print("Error: BOT_TOKEN not found. Make sure you have a .env file with BOT_TOKEN set.")
    exit()

CONFIG_FILE = 'shibako_phrases.json'
TRIGGER_MAP = {} # Dictionary to map triggers to their config
RUDE_RESPONSE_CONFIG = {} # Store the global rude response settings

# --- Function to Load Configuration ---
def load_config(filename):
    """Loads configuration from a JSON file and builds the trigger map."""
    global TRIGGER_MAP, RUDE_RESPONSE_CONFIG # Allow modification of global vars
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
        RUDE_RESPONSE_CONFIG = config_data.get('rude_response', {}) # Load rude config

        print(f"Loaded configuration from {filename}")
        print(f"Found {len(TRIGGER_MAP)} triggers.")
        return True # Indicate success

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

random.seed() # Seed the random number generator

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

    message_content_lower = message.content.lower()
    message_sender_id = message.author.id

    # --- Check if the message content matches a known trigger ---
    matched_config = TRIGGER_MAP.get(message_content_lower)

    if matched_config:
        # A trigger was matched! Decide response type.
        allow_rude = matched_config.get('allow_rude', False)
        standard_response = matched_config.get('response', '...')

        # Get global rude response settings (with defaults)
        rude_chance = RUDE_RESPONSE_CONFIG.get('chance', 0.0) # Default to 0 chance
        rude_prefix = RUDE_RESPONSE_CONFIG.get('prefix', '')
        rude_template = RUDE_RESPONSE_CONFIG.get('message', '')

        should_be_rude = allow_rude and random.random() < rude_chance

        if should_be_rude and rude_template:
            # Send the rude response
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

    # If no trigger matched, do nothing

# Run the bot
try:
    client.run(BOT_TOKEN)
except discord.LoginFailure:
    print("Login Failed: Improper token has been passed.")
except discord.errors.PrivilegedIntentsRequired:
     print("Privileged Intents Error: Make sure 'Message Content Intent' is enabled on the Discord Developer Portal for your bot.")
except Exception as e:
    print(f"An error occurred while running the bot: {e}")