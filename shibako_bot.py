# ... (keep imports and previous code above on_message) ...

@client.event
async def on_message(message):
    # Ignore messages sent by the bot itself
    if message.author == client.user:
        return

    # Process commands first
    msg_lower = message.content.lower()

    # --- Handle Help Command ---
    if msg_lower == '!help':
        # Added !phrases command to the description
        help_message = f"""{SHIBA_EMOJI} こんにちは！ しばこです。 (Hello! I'm Shibako.)

わたしができること： (Things I can do:)
`!help` - Shows this help message.
`!phrases` - Shows all the phrases I might react to.
`!romaji <japanese text>` - Converts Japanese text to Romaji. (e.g., `!romaji こんにちは`)

いろいろな　フレーズの　れい： (Examples of various phrases I might react to:)
`say the line shibako`
`good bot`
`hi shibako`
`pat shibako`
`shibako fetch`
`!y` / `!n`

(ためしてみてね！ - Try them out!)"""
        await message.channel.send(help_message)
        return # Stop processing after handling the command

    # --- Handle List Phrases Command ---
    elif msg_lower == '!phrases':
        if not TRIGGER_MAP:
            # Use an error message potentially from config or a default
            error_msg = ERROR_MESSAGES.get("phrases_list_empty", "なにも　フレーズが　みつかりません。")
            await message.channel.send(f"{SHIBA_EMOJI} {error_msg}")
            return

        all_triggers = sorted(list(TRIGGER_MAP.keys())) # Get and sort triggers

        # Format the message using a code block
        header = f"{SHIBA_EMOJI} わたしが　はんのうする　かもしれない　フレーズ： (Phrases I might react to:)\n```\n"
        footer = "\n```"
        # Join phrases with newline characters
        body = "\n".join(all_triggers)

        full_message = header + body + footer

        # Check if the message exceeds Discord's approx limit
        if len(full_message) > 1900: # Leave some buffer room
             limit_msg = ERROR_MESSAGES.get("phrases_list_too_long", "たくさん　ありすぎて　ぜんぶは　みせられない！")
             await message.channel.send(f"{SHIBA_EMOJI} {limit_msg}")
        else:
            await message.channel.send(full_message)
        return # Stop processing after handling the command

    # --- Handle Romaji Command ---
    romaji_command = "!romaji "
    if msg_lower.startswith(romaji_command):
        # Check if the converter function is available
        if romaji_converter_func:
            text_to_convert = message.content[len(romaji_command):].strip()
            if not text_to_convert:
                error_msg = ERROR_MESSAGES.get("romaji_no_input", "テキストをいれてください。")
                await message.channel.send(f"{SHIBA_EMOJI} {error_msg}")
                return

            try:
                result = romaji_converter_func(text_to_convert)
                romaji_parts = [item['hepburn'] for item in result]
                romaji_text = ' '.join(romaji_parts)
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
             error_msg = ERROR_MESSAGES.get("romaji_converter_unavailable", "ローマジへんかんきはつかえません。")
             await message.channel.send(f"{SHIBA_EMOJI} {error_msg}")
        return # Stop processing after handling the command

    # --- Handle Configured Triggers ---
    # (Only check these if it wasn't a specific command above)
    message_sender_id = message.author.id
    # Use msg_lower which is already calculated
    matched_config = TRIGGER_MAP.get(msg_lower)

    if matched_config:
        allow_rude = matched_config.get('allow_rude', False)
        standard_response = matched_config.get('response', '...')

        rude_chance = RUDE_RESPONSE_CONFIG.get('chance', 0.0)
        rude_prefix = RUDE_RESPONSE_CONFIG.get('prefix', '')
        rude_template = RUDE_RESPONSE_CONFIG.get('message', '')

        should_be_rude = allow_rude and random.random() < rude_chance

        if should_be_rude and rude_template and '{message_sender}' in rude_template:
            if rude_prefix:
                time.sleep(1)
                await message.channel.send(rude_prefix)

            formatted_rude_message = rude_template.format(message_sender=message_sender_id)
            time.sleep(1)
            await message.channel.send(formatted_rude_message)
        else:
            time.sleep(1)
            await message.channel.send(standard_response)

# ... (rest of the code, including client.run()) ...