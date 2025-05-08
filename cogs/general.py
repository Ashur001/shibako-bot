import discord
from discord.ext import commands

class GeneralCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='tasukete')
    async def help_command(self, ctx):
        """!help message"""

        help_message = f"""{self.bot.config.get('shiba_emoji_string', '<:shiba:1363005589902589982>')} こんにちは！ しばこです。..."""
        await ctx.send(help_message)

    @commands.command(name ='phrases')
    async def phrases_command(self, ctx):
        """Shows all possible trigger phrases."""

        trigger_map = self.bot.trigger_map
        if not trigger_map:
            error_msg = self.bot.error_messages.get("phrases_list_empty", "...")
            await ctx.send(f"{self.bot.config.get('shiba_emoji_string', '...')} {error_msg}")
            return
        
        await ctx.send(full_message)
