import discord
from discord.ext import commands # Import commands module
import pykakasi # For Romaji/Furigana conversion
import os
import requests # For DeepL Translation
import emoji # For language detection

# --- Instantiate PyKakasi (Singleton Initialization for the Cog) ---
# Initialize this resource once when the cog file is first imported.
try:
    kks_instance = pykakasi.kakasi()
    kks_available = True
    print("PyKakasi converter initialized for JpCog.") # Renamed print statement
except Exception as e:
    print(f"Error initializing PyKakasi in JpCog: {e}") # Renamed print statement
    print("Furigana and Romaji conversion will not be available.")
    kks_instance = None
    kks_available = False
# --- ---

class JpCog(commands.Cog):
    def __init__(self, bot, error_messages, shiba_emoji):
        self.bot = bot # Store bot instance
        self.error_messages = error_messages # Store error messages dictionary
        self.shiba_emoji = shiba_emoji # Store SHIBA emoji

        # Store the initialized PyKakasi instance and its availability
        self.kks = kks_instance
        self.kks_available = kks_available

    async def get_text_from_context(self, ctx, text_args):
        """Helper to get text from command args or reply."""
        text = ' '.join(text_args).strip() # Join provided args

        # If no text provided, check for reply
        if not text and ctx.message.reference:
            try:
                # Fetch the replied message
                replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                text = replied_message.content.strip()
            except Exception as e:
                print(f"Error fetching replied message: {e}")
                error_msg = self.error_messages.get("fetch_failed", "Failed to fetch replied message.")
                await ctx.send(f"{self.shiba_emoji} {error_msg}")
                return None # Indicate failure

        return text # Return the gathered text (could still be empty)


    # --- !romaji command ---
    @commands.command(name='romaji')
    async def romaji_command(self, ctx, *text):
        """Converts Japanese text to Romaji."""
        text_to_convert = await self.get_text_from_context(ctx, text)
        if text_to_convert is None: # Error occurred while fetching reply
            return
        if not text_to_convert: # No text provided and no reply or empty reply
            error_msg = self.error_messages.get("romaji_no_input", "テキストをいれてください。")
            await ctx.send(f"{self.shiba_emoji} {error_msg}")
            return

        if self.kks_available and self.kks: # Check if the converter is available
            try:
                result = self.kks.convert(text_to_convert)
                romaji_parts = [item['hepburn'] for item in result] # Extract Hepburn romaji
                romaji_text = ' '.join(romaji_parts) # Join parts with spaces manually
                response = f'{self.shiba_emoji} "{romaji_text}"'
                await ctx.send(response) # Use ctx.send

            except KeyError as e:
                print(f"KeyError during Romaji conversion: 'hepburn' key missing in result for '{text_to_convert}'. Result: {result}")
                error_msg = self.error_messages.get("romaji_conversion_failed", "へんかんできませんでした。")
                await ctx.send(f"{self.shiba_emoji} {error_msg}")
            except Exception as e:
                print(f"Error during Romaji conversion for '{text_to_convert}': {e}")
                error_msg = self.error_messages.get("romaji_conversion_failed", "へんかんできませんでした。")
                await ctx.send(f"{self.shiba_emoji} {error_msg}")
        else:
            error_msg = self.error_messages.get("romaji_converter_unavailable", "ローマジへんかんきはつかえません。")
            await ctx.send(f"{self.shiba_emoji} {error_msg}")


    # --- !furigana command ---
    @commands.command(name='furigana', aliases=['furi'])
    async def furigana_command(self, ctx, *text):
        """Converts Japanese text to Furigana."""
        text_to_convert = await self.get_text_from_context(ctx, text)
        if text_to_convert is None: # Error occurred while fetching reply
            return
        if not text_to_convert: # No text provided and no reply or empty reply
            error_msg = self.error_messages.get("furigana_no_input", "Please provide Japanese text to convert to Furigana.")
            await ctx.send(f"{self.shiba_emoji} {error_msg}")
            return

        if self.kks_available and self.kks: # Check if the converter is available
            try:
                result = self.kks.convert(text_to_convert)
                furigana_parts = []
                for item in result:
                    if item['kunrei'] or item['on']:
                        reading = item['kunrei'] if item['kunrei'] else item['on']
                        furigana_parts.append(f"{item['orig']}「{reading}」")
                    else:
                        furigana_parts.append(item['orig']) # Keep original if no reading found

                furigana_text = "".join(furigana_parts)
                response = f"input: {text_to_convert}\nmessage: {furigana_text}"
                await ctx.send(response) # Use ctx.send

            except Exception as e:
                print(f"Error during Furigana conversion for '{text_to_convert}': {e}")
                error_msg = self.error_messages.get("furigana_conversion_failed", "Furigana conversion failed.")
                await ctx.send(f"{self.shiba_emoji} {error_msg}")
        else:
            error_msg = self.error_messages.get("furigana_converter_unavailable", "Furigana conversion is unavailable.")
            await ctx.send(f"{self.shiba_emoji} {error_msg}")


    # --- !translate command ---
    @commands.command(name='translate', aliases=['tl'])
    async def translate_command(self, ctx, *text):
        """Translates text using DeepL."""
        translateMe = await self.get_text_from_context(ctx, text)
        if translateMe is None: # Error occurred while fetching reply
            return
        if not translateMe: # No text provided and no reply or empty reply
            error_msg = self.error_messages.get("translate_no_input", "翻訳するテキストを入力してください。")
            await ctx.send(f"{self.shiba_emoji} {error_msg}")
            return

        # Detect language (reusing your logic)
        # Assuming emoji.demojize handles emojis appropriately for ASCII check
        if emoji.demojize(translateMe).isascii():
            source_lang = 'EN'
            target_lang = 'JA'
        else:
            source_lang = 'JA'
            target_lang = 'EN'

        # Get DeepL API key from environment (reusing your logic)
        deepl_key = os.getenv('DEEPL_API_KEY')
        if not deepl_key:
            error_msg = self.error_messages.get("translate_no_api_key", "翻訳APIキーが設定されていません。")
            await ctx.send(f"{self.shiba_emoji} {error_msg}")
            return

        url = "https://api-free.deepl.com/v2/translate" # Using the free API endpoint
        params = {
            'auth_key': deepl_key,
            'text': translateMe,
            'source_lang': source_lang,
            'target_lang': target_lang,
            'preserve_formatting': '0' # You might want to adjust this
        }

        try:
            # Use aiohttp or httpx for async requests in a bot,
            # but sticking to requests for consistency with your provided code
            response = requests.post(url, data=params)
            response.raise_for_status()  # Raises an HTTPError for bad responses
            responseJSON = response.json()
            result = responseJSON['translations'][0]['text']
            print("Translated output: ", result)
            await ctx.reply(result) # Use ctx.reply

        except requests.exceptions.RequestException as e:
            print(f"Translation API error: {e}")
            error_msg = self.error_messages.get("translate_api_error", "翻訳APIでエラーが発生しました。")
            await ctx.send(f"{self.shiba_emoji} {error_msg}")
        except (KeyError, IndexError): # Handle missing keys/indices in the response
            print(f"Unexpected API response format: {response.text}")
            error_msg = self.error_messages.get("translate_format_error", "翻訳結果の形式が予期せぬものでした。")
            await ctx.send(f"{self.shiba_emoji} {error_msg}")
        except Exception as e:
            print(f"Unexpected translation error: {e}")
            error_msg = self.error_messages.get("translate_unknown_error", "翻訳中に未知のエラーが発生しました。")
            await ctx.send(f"{self.shiba_emoji} {error_msg}")


    # --- !full command ---
    @commands.command(name='full')
    async def full_command(self, ctx, *text):
        """Performs Furigana, Romaji, and Translation on text."""
        original_text = await self.get_text_from_context(ctx, text)
        if original_text is None: # Error occurred while fetching reply
            return
        if not original_text: # No text provided and no reply or empty reply
            error_msg = self.error_messages.get("full_no_input", "Please provide text or reply to a message for full processing.")
            await ctx.send(f"{self.shiba_emoji} {error_msg}")
            return

        # --- Perform Processing Steps ---
        furigana_text = "Furigana conversion skipped." # Default if kks not available
        romaji_text = "Romaji conversion skipped."   # Default if kks not available
        deepl_translation = "Translation skipped."    # Default if API key missing or API fails

        # 1. Furigana and Romaji (using kks)
        if self.kks_available and self.kks:
            try:
                kks_result = self.kks.convert(original_text)

                # Furigana Formatting
                furigana_parts = []
                romaji_parts = []
                for item in kks_result:
                    # Furigana: orig「reading」
                    if item['kunrei'] or item['on']:
                        reading = item['kunrei'] if item['kunrei'] else item['on']
                        furigana_parts.append(f"{item['orig']}「{reading}」")
                    else:
                        furigana_parts.append(item['orig']) # Keep original if no reading found

                    # Romaji: collect hepburn reading
                    romaji_parts.append(item.get('hepburn', item['orig'])) # Use orig as fallback if hepburn missing

                furigana_text = "".join(furigana_parts)
                romaji_text = " ".join(romaji_parts) # Join romaji with spaces

            except KeyError as e:
                print(f"KeyError during kks conversion for !full: {e} in result: {kks_result}")
                furigana_text = self.error_messages.get("full_conversion_failed", "Furigana/Romaji conversion failed (format error).")
                romaji_text = self.error_messages.get("full_conversion_failed", "Furigana/Romaji conversion failed (format error).")
            except Exception as e:
                print(f"Error during kks conversion for !full: {e}")
                furigana_text = self.error_messages.get("full_conversion_failed", "Furigana/Romaji conversion failed.")
                romaji_text = self.error_messages.get("full_conversion_failed", "Furigana/Romaji conversion failed.")
        else:
            furigana_text = self.error_messages.get("full_converter_unavailable", "Japanese converter unavailable.")
            romaji_text = self.error_messages.get("full_converter_unavailable", "Japanese converter unavailable.")


        # 2. DeepL Translation
        deepl_key = os.getenv('DEEPL_API_KEY')
        if not deepl_key:
            deepl_translation = self.error_messages.get("full_no_api_key", "Translation API key not set.")
            # No return here, we want to send the partial result if available

        else:
            url = "https://api-free.deepl.com/v2/translate"
            # Detect language for translation source/target (reusing your logic)
            if emoji.demojize(original_text).isascii():
                source_lang = 'EN'
                target_lang = 'JA'
            else:
                source_lang = 'JA'
                target_lang = 'EN'

            params = {
                'auth_key': deepl_key,
                'text': original_text,
                'source_lang': source_lang,
                'target_lang': target_lang,
                 'preserve_formatting': '0' # You might want to adjust this
            }

            try:
                # Using requests as in your original code
                response = requests.post(url, data=params)
                response.raise_for_status() # Raises an HTTPError for bad responses
                responseJSON = response.json()
                deepl_translation = responseJSON.get('translations', [{}])[0].get('text', "Translation result not found in API response.")
                print("DeepL Translation output: ", deepl_translation)

            except requests.exceptions.RequestException as e:
                print(f"DeepL API error for !full: {e}")
                deepl_translation = self.error_messages.get("full_api_error", "Translation API error.")
            except (KeyError, IndexError): # Handle missing keys/indices
                print(f"Unexpected API response format for !full: {response.text}")
                deepl_translation = self.error_messages.get("full_api_format_error", "Translation API format error.")
            except Exception as e:
                print(f"Unexpected translation error: {e}")
                deepl_translation = self.error_messages.get("full_translation_unknown_error", "Unknown translation error.")


        # --- Format and Send Final Response ---
        # Using triple backticks for a clean code block format in Discord
        response_message = f"""```
{original_text}
{furigana_text}
{romaji_text}

{deepl_translation}
```""" # Added a newline before translation for clarity

        # Discord has a message length limit (typically 2000 characters)
        if len(response_message) > 1900: # Leave some buffer
            response_message = response_message[:1900] + "\n... (Output truncated due to length)"

        await ctx.send(response_message)


# --- Setup function (Conventional for loading extensions) ---
# This allows you to use bot.load_extension('jp_cog')
# However, passing external resources like ERROR_MESSAGES is easier
# by manually adding the cog instance in main.py's setup_hook.
# We include this setup function definition for completeness, but
# the main.py snippet below shows the manual add_cog approach.
async def setup(bot):
    # Assuming ERROR_MESSAGES and SHIBA_EMOJI are somehow accessible here,
    # e.g., stored on the bot instance: bot.error_messages, bot.shiba_emoji
    # await bot.add_cog(JpCog(bot, bot.error_messages, bot.shiba_emoji))
    print("JpCog setup function called (manual adding in main.py is recommended for passing resources).") # Renamed print statement