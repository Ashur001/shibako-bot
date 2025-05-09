import discord
from discord.ext import commands
import textwrap

class GeneralCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='tasukete')
    async def help_command(self, ctx):
        """Shows the help message."""

        help_message = textwrap.dedent(f"""{self.bot.config.get('shiba_emoji_string', '...')} こんにちは！ しばこです。 (Hello! I'm Shibako.)

        わたしができること： (Things I can do:)
        `!tasukete` - Shows this help message.
        `!phrases` - Shows all the phrases I might react to.
        `!romaji <japanese text>` - Converts Japanese text to Romaji. (e.g., `!romaji こんにちは`)

        いろいろな　フレーズの　れい： (Examples of various phrases I might react to:)
        `say the line shibako`
        `good bot`
        `hi shibako`
        `pat shibako`
        `shibako fetch`
        `!y` / `!n`

        (ためしてみてね！ - Try them out!)""")

        try:
            await ctx.send(help_message)
        except discord.errors.Forbidden:
            print(f"Error: Cannot send message in channel {ctx.channel.id}. Missing permissions?")
        except Exception as e:
            print(f"Error sending help message: {e}")

    @commands.command(name ='phrases')
    async def phrases_command(self, ctx):
        """Prints all possible phrases to trigger shibako."""

        trigger_map = self.bot.trigger_map
        if not trigger_map:
            error_msg = self.bot.error_messages.get("phrases_list_empty", "...")
            await ctx.send(f"{self.bot.config.get('shiba_emoji_string', '...')} {error_msg}")
            return

        all_triggers = sorted(list(trigger_map.keys())) # Get and sort triggers

        header = f"{self.bot.config.get('shiba_emoji_string', '...')} わたしが　はんのうする　かもしれない　フレーズ： (Phrases I might react to:)\n```\n"
        footer = "\n```"
        body = "\n".join(all_triggers)
        full_message = header + body + footer

        # Check if the message exceeds Discord's approx limit
        if len(full_message) > 1900: # Leave some buffer room
            limit_msg = self.bot.error_messages.get("phrases_list_too_long", "たくさん　ありすぎて　ぜんぶは　みせられない！")
            await ctx.send(f"{self.bot.config.get('shiba_emoji_string', '...')} {limit_msg}")

        else:
            try:
                await ctx.send(full_message)
            except discord.errors.Forbidden:
                 print(f"Error: Cannot send !phrases list in channel {ctx.channel.id}. Missing permissions?")
            except Exception as e:
                print(f"Error sending phrases list message: {e}")

# This setup function is required for the cog to be loaded
async def setup(bot):
    await bot.add_cog(GeneralCog(bot))
        







