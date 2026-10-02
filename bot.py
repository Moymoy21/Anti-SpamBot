import os
import discord
from discord import app_commands
from openai import AsyncOpenAI

# ... (same setup as before)

# Groq gamit ang OpenAI-compatible client
client_ai = AsyncOpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

SYSTEM_PROMPT = """You are a technical assistant on Discord..."""

@client.event
async def on_message(message):
    if message.author == client.user or not message.guild:
        return

    # ==== AI HANDLER ====
    if message.channel.id == AI_CHANNEL_ID:
        if not message.content.startswith(AI_PREFIX):
            return

        prompt = message.content[len(AI_PREFIX):].strip()
        if not prompt:
            await message.reply("⚠️ Usage: `.ai <your question>`")
            return

        async with message.channel.typing():
            try:
                response = await client_ai.chat.completions.create(
                    model="llama-3.3-70b-versatile",  # o "llama-3.1-8b-instant" para sa mas mataas na limit
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.4,
                )
                answer = response.choices[0].message.content
            except Exception as e:
                answer = f"⚠️ AI Error: `{e}`"

        for i in range(0, len(answer), 1900):
            chunk = answer[i:i+1900]
            if i == 0:
                await message.reply(chunk)
            else:
                await message.channel.send(chunk)
        return

    # ... (anti-spam logic)  # Don't run anti-spam below

    # ============ ANTI-SPAM HANDLER ============
    if message.channel.id == TARGET_CHANNEL_ID:
        if message.author.guild_permissions.administrator:
            return

        has_allowed_role = any(role.id == ALLOWED_ROLE_ID for role in message.author.roles)

        if not has_allowed_role:
            try:
                await message.delete()
            except Exception as e:
                print(f"Hindi mabura ang mensahe: {e}", flush=True)

            if LOG_CHANNEL_ID:
                try:
                    log_channel = client.get_channel(LOG_CHANNEL_ID)
                    if log_channel:
                        await log_channel.send(
                            f"**{message.author}** has been kicked for sending a message in the anti-spam channel."
                        )
                except Exception as e:
                    print(f"Hindi makapag-send sa log channel: {e}", flush=True)

            try:
                await message.guild.kick(message.author, reason="Nag-chat sa restricted channel.")
                print(f"Na-kick si {message.author} dahil nag-chat sa ipinagbabawal na channel.", flush=True)
            except Exception as e:
                print(f"Nabigo ang pag-kick: {e}", flush=True)


client.run(TOKEN)
