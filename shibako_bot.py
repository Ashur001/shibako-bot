import discord
from discord.ext import commands
import os 
import json
import asyncio

# Load environment variables from .env file
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
DEEPL_API_KEY = os.getenv("")

# Check if the bot token is loaded
if BOT_TOKEN is None:
    print("Error: BOT_TOKEN not found in .env file. Make sure you have a .env file with BOT_TOKEN set.")
    exit()

# --- Configuration Variables ---
CONFIG_FILE = 'shibako_phrases.json' # Json file containing all shibako trigger phrases
TRIGGER_MAP = {} # Dictionary to map triggers to their config
RUDE_RESPONSE_CONFIG = {} # Store the global rude response settings
SHIBA_EMOJI = "<:shiba:1363005589902589982>" # Default emoji string, can be overridden by config
ERROR_MESSAGES = {} # Dictionary for user-facing error messages loaded from config

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
    print("Warning: Configuration loading failed. Bot functionality may be limited.")
# --- ---

# --- Bot Object Setup ---
intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix = '!', intents=intents)

# Attach configuration data to bot so cogs have access to data:
bot.trigger_map = TRIGGER_MAP
bot.rude_response_config = RUDE_RESPONSE_CONFIG
bot.error_messages = ERROR_MESSAGES
bot.config = {
    "shiba_emoji_string": SHIBA_EMOJI
}

# --- Event Handlers ---
@bot.event
async def on_ready():
    """Event handler for when the bot logs in and is ready."""
    print(f'We have logged in as {bot.user}')
    print('Loading cogs...')

    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and not filename.startswith('_'):
            try: 
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f'Loaded cog: {filename}')
            except Exception as e:
                print(f'Failed to load cog {filename}: {e}')
    
    print('Bot is ready!')
    print('-------------------')

@bot.event
async def on_message(message):
    # Ignore messages sent by the bot itself to prevent loops
    if message.author == bot.user:
        return

    msg_lower = message.content.lower()
    matched_config = bot.trigger_map.get(msg_lower)
    if matched_config and not message.content.startswith(bot.command_prefix): # Avoid triggering on commands
        # ... (your trigger response logic using bot.rude_response_config etc.) ...
        # Example: await message.channel.send(standard_response)
        return 

    # Pass message along to bot to process the command the standard discord.py way:
    await bot.process_commands(message)

# --- Centralized Error Handling ---
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        pass # Ignore command not found errors silently
    elif isinstance(error, commands.MissingRequiredArgument):
         await ctx.send(f"{bot.config['shiba_emoji_string']} You missed an argument! Check `!tasukete {ctx.command.name}`.")
    # Add more specific error handling here
    else:
        print(f'Unhandled command error in {ctx.command}: {error}')
        await ctx.send(f"{bot.config['shiba_emoji_string']} Something went wrong.")

# --- Run the Bot ---
async def main():
    async with bot:
        await bot.start(BOT_TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except discord.LoginFailure:
        print("Login Failed: Improper token.")
    except discord.errors.PrivilegedIntentsRequired:
         print("Privileged Intents Error: Ensure 'Message Content Intent' is enabled.")
    except Exception as e:
        print(f"A critical error occurred: {e}")