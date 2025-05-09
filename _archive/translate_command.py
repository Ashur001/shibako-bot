import discord
import os
import requests
import emoji
from dotenv import load_dotenv

async def handle_translate(message, msg_lower, ERROR_MESSAGES, SHIBA_EMOJI):
    """Handles the !translate and !tl commands."""
    translate_command = "!translate "
    if msg_lower.startswith(translate_command) or msg_lower.startswith("!tl"):
        # Get the text to translate
        translateMe = message.content[len("!translate "):].strip() if msg_lower.startswith(translate_command) else message.content[len("!tl "):].strip()

        # If no text provided but it's a reply, get the replied message content
        if not translateMe and message.reference:
            try:
                replied_message = await message.channel.fetch_message(message.reference.message_id)
                translateMe = replied_message.content
            except Exception as e:
                error_msg = ERROR_MESSAGES.get("translate_fetch_failed", "返信されたメッセージを取得できませんでした。")
                await message.channel.send(f"{SHIBA_EMOJI} {error_msg}")
                return
        elif not translateMe:
            error_msg = ERROR_MESSAGES.get("translate_no_input", "翻訳するテキストを入力してください。")
            await message.channel.send(f"{SHIBA_EMOJI} {error_msg}")
            return

        # Detect language
        if emoji.demojize(translateMe).isascii():  # Text is EN if all chars (excl emoji) are ascii
            source_lang = 'EN'
            target_lang = 'JA'
        else:  # Else, text is JA
            source_lang = 'JA'
            target_lang = 'EN'

        # Get DeepL API key from environment
        deepl_key = os.getenv('DEEPL_API_KEY')
        if not deepl_key:
            error_msg = ERROR_MESSAGES.get("translate_no_api_key", "翻訳APIキーが設定されていません。")
            await message.channel.send(f"{SHIBA_EMOJI} {error_msg}")
            return

        url = "https://api-free.deepl.com/v2/translate"
        params = {
            'auth_key': deepl_key,
            'text': translateMe,
            'source_lang': source_lang,
            'target_lang': target_lang
        }

        try:
            response = requests.post(url, data=params)
            response.raise_for_status()  # Raises an HTTPError for bad responses
            responseJSON = response.json()
            result = responseJSON['translations'][0]['text']
            print("Translated output: ", result)
            await message.reply(result)
        except requests.exceptions.RequestException as e:
            print(f"Translation API error: {e}")
            error_msg = ERROR_MESSAGES.get("translate_api_error", "翻訳APIでエラーが発生しました。")
            await message.channel.send(f"{SHIBA_EMOJI} {error_msg}")
        except KeyError:
            print(f"Unexpected API response format: {response.text}")
            error_msg = ERROR_MESSAGES.get("translate_format_error", "翻訳結果の形式が予期せぬものでした。")
            await message.channel.send(f"{SHIBA_EMOJI} {error_msg}")
        except Exception as e:
            print(f"Unexpected translation error: {e}")
            error_msg = ERROR_MESSAGES.get("translate_unknown_error", "翻訳中に未知のエラーが発生しました。")
            await message.channel.send(f"{SHIBA_EMOJI} {error_msg}")
