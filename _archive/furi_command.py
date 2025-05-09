import discord
import pykakasi # For Romaji conversion

# --- Instantiate PyKakasi (Simplified Initialization) ---
# This handles the Japanese to Romaji conversion
try:
    # Initialize without the config dictionary (simplest approach)
    kks = pykakasi.kakasi()
    # Store the convert method
    # romaji_converter_func = kks.convert #  Not used for Furigana in this version
    print("PyKakasi Romaji converter initialized (Simplified).")
except Exception as e:
    print(f"Error initializing PyKakasi: {e}")
    print("Romaji conversion will not be available.")
    # romaji_converter_func = None # Not used for Furigana
    kks = None
# --- ---

async def handle_furigana(message, msg_lower, ERROR_MESSAGES, SHIBA_EMOJI):
    """Handles the !furigana command."""
    furigana_command = "!furigana" # Changed command name to !furigana
    if msg_lower.startswith("!furigana") or msg_lower.startswith("!furi"): # Changed to also include !furi
        command_length = len("!furigana") if msg_lower.startswith("!furigana") else len("!furi")
        text_to_convert = message.content[command_length:].strip()

        # If no text provided but it's a reply, get the replied message content
        if not text_to_convert and message.reference:
            try:
                replied_message = await message.channel.fetch_message(message.reference.message_id)
                text_to_convert = replied_message.content
            except Exception as e:
                error_msg = ERROR_MESSAGES.get("furigana_fetch_failed", "Failed to fetch replied message for Furigana conversion.") # Changed error message
                await message.channel.send(f"{SHIBA_EMOJI} {error_msg}")
                return

        if not text_to_convert:
            error_msg = ERROR_MESSAGES.get("furigana_no_input", "Please provide Japanese text to convert to Furigana.") # Changed error message
            await message.channel.send(f"{SHIBA_EMOJI} {error_msg}")
            return

        if kks is not None: #check if kks is initialized
            try:
                # Use the stored convert function directly
                result = kks.convert(text_to_convert)
                furigana_parts = []
                for item in result:
                    if item['kunrei'] or item['on']:
                        reading = item['kunrei'] if item['kunrei'] else item['on']
                        furigana_parts.append(f"{item['orig']}「{reading}」")
                    else:
                        furigana_parts.append(item['orig'])
                furigana_text = "".join(furigana_parts)
                response = f"input: {text_to_convert}\nmessage: {furigana_text}"
                await message.channel.send(response)
            except Exception as e:
                print(f"Error during Furigana conversion: {e}")
                error_msg = ERROR_MESSAGES.get("furigana_conversion_failed", "Furigana conversion failed.")  # Changed error message
                await message.channel.send(f"{SHIBA_EMOJI} {error_msg}")
                return
        else:
             error_msg = ERROR_MESSAGES.get("furigana_converter_unavailable", "Furigana conversion is unavailable.")
             await message.channel.send(f"{SHIBA_EMOJI} {error_msg}")
             return

