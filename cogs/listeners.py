import discord
from discord.ext import commands
import random
import time # For the sleep effect

class ListenerCog(commands.Cog, name="Message Listeners"):
    """
    Handles non-command message triggers and other events.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        Listens for messages and responds to configured trigger phrases.
        This runs for *every* message, so command processing still needs to happen.
        """
        # Ignore messages sent by the bot itself to prevent loops
        if message.author == self.bot.user:
            return

        # Ignore messages that are likely commands to avoid conflict
        # (assuming your command prefix is attached to the bot object)
        if message.content.startswith(self.bot.command_prefix):
            return

        msg_lower = message.content.lower()
        message_sender_id = message.author.id

        # Access trigger map and rude response config from the bot instance
        # These should be attached to self.bot in your main shibako_bot.py
        trigger_map = getattr(self.bot, 'trigger_map', {})
        rude_response_config = getattr(self.bot, 'rude_response_config', {})
        shiba_emoji = getattr(self.bot.config, 'shiba_emoji_string', '<:shiba:1363005589902589982>') # Default if not found

        matched_config = trigger_map.get(msg_lower)

        if matched_config:
            allow_rude = matched_config.get('allow_rude', False)
            standard_response = matched_config.get('response', f"{shiba_emoji} ...") # Default response

            rude_chance = rude_response_config.get('chance', 0.0)
            rude_prefix = rude_response_config.get('prefix', '')
            rude_template = rude_response_config.get('message', '')

            should_be_rude = allow_rude and random.random() < rude_chance

            try:
                if should_be_rude and rude_template and '{message_sender}' in rude_template:
                    if rude_prefix:
                        time.sleep(1) # Keep the pause effect
                        await message.channel.send(rude_prefix)
                    
                    formatted_rude_message = rude_template.format(message_sender=f"<@{message_sender_id}>") # Mention user
                    time.sleep(1)
                    await message.channel.send(formatted_rude_message)
                else:
                    time.sleep(1) # Keep the pause effect
                    await message.channel.send(standard_response)
            except discord.errors.Forbidden:
                 print(f"Error (ListenerCog): Cannot send triggered response in channel {message.channel.id}. Missing permissions?")
            except Exception as e:
                 print(f"Error (ListenerCog) sending triggered response: {e}")
            
            # Important: Do NOT call bot.process_commands(message) here.
            # That should be handled in your main bot file's on_message,
            # or this listener will prevent commands from being processed if it matches a trigger.
            return # Stop further processing in this specific on_message listener if a trigger matched.

# This setup function is required for the cog to be loaded
async def setup(bot: commands.Bot):
    await bot.add_cog(ListenerCog(bot))
    print("ListenerCog loaded.")

