import discord
import os # For loading the token from an environment variable (recommended)
import random
import time
from dotenv import load_dotenv

BOT_TOKEN = os.getenv("BOT_TOKEN")

if BOT_TOKEN is None:
    print("Error: BOT_TOKEN not found. Make sure you have a .env file with BOT_TOKEN set.")
    exit() 

# Define the intents your bot needs.
# For reading messages, message content intent is crucial.
intents = discord.Intents.default()
intents.message_content = True # Make sure this is enabled in the Discord Developer Portal too!

# Create a bot instance with a command prefix and the defined intents
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
    
    shibako_phrase = "say the line shibako"

    response_float = random.random()
    message_sender = message.author.id
    message_content_lower = message.content.lower()

    if message.content.startswith('!y') or message_content_lower == shibako_phrase:
      if response_float < .20:
        time.sleep(1)
        await message.channel.send(" ... ")
        time.sleep(1)
        await message.channel.send(f"🖕<:shiba:1363005589902589982> <@{message_sender}>")

      else:
        time.sleep(1)
        await message.channel.send("<:shiba:1363005589902589982> はい")

    elif message.content.startswith('!n'):
      if response_float < .20:
        time.sleep(1)
        await message.channel.send(" ... ")
        time.sleep(1)
        await message.channel.send(f"🖕<:shiba:1363005589902589982> <@{message_sender}>")
        
      else:
        time.sleep(1)
        await message.channel.send("<:shiba:1363005589902589982> いいえ")

# Run the bot
try:
    client.run(BOT_TOKEN)
except discord.LoginFailure:
    print("Login Failed: Improper token has been passed.")
except Exception as e:
    print(f"An error occurred: {e}")