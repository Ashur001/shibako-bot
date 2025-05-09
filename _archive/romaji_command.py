import discord
import pykakasi # For Romaji conversion

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

async def handle_romaji(message, msg_lower, ERROR_MESSAGES, SHIBA_EMOJI):
    """Handles the !romaji command."""
    romaji_command = "!romaji "
    if msg_lower.startswith(romaji_command):
        text_to_convert = message.content[len(romaji_command):].strip()

        # If no text provided but it's a reply, get the replied message content
        if not text_to_convert and message.reference:
            try:
                replied_message = await message.channel.fetch_message(message.reference.message_id)
                text_to_convert = replied_message.content
            except Exception as e:
                error_msg = ERROR_MESSAGES.get("romaji_fetch_failed", "返信されたメッセージを取得できませんでした。")
                await message.channel.send(f"{SHIBA_EMOJI} {error_msg}")
                return

        if not text_to_convert:
            error_msg = ERROR_MESSAGES.get("romaji_no_input", "テキストをいれてください。")
            await message.channel.send(f"{SHIBA_EMOJI} {error_msg}")
            return

        if romaji_converter_func: # Check if the converter function is available
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