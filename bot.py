import os
import discord

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)

TARGET_CHANNEL_ID = int(os.getenv("TARGET_CHANNEL_ID", 0))
ALLOWED_ROLE_ID = int(os.getenv("ALLOWED_ROLE_ID", 0))
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", 0))
TOKEN = os.getenv("DISCORD_TOKEN")

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user or not message.guild:
        return

    if message.channel.id == TARGET_CHANNEL_ID:
        if message.author.guild_permissions.administrator:
            return
        
        has_allowed_role = any(role.id == ALLOWED_ROLE_ID for role in message.author.roles)
        
        if not has_allowed_role:
            # 1. Burahin muna ang mensahe
            try:
                await message.delete()
            except Exception as e:
                print(f"Hindi mabura ang mensahe: {e}")

            # 2. I-send muna ang announcement sa log channel bago i-kick (o kahit sabay)
            if LOG_CHANNEL_ID:
                try:
                    log_channel = client.get_channel(LOG_CHANNEL_ID)
                    if log_channel:
                        await log_channel.send(f"**{message.author}** has been kicked for sending a message in the anti-spam channel.")
                except Exception as e:
                    print(f"Hindi makapag-send sa log channel: {e}")

            # 3. I-kick ang user
            try:
                await message.guild.kick(message.author, reason="Nag-chat sa restricted channel.")
                print(f"Na-kick si {message.author} dahil nag-chat sa ipinagbabawal na channel.")
            except Exception as e:
                print(f"Nabigo ang pag-kick: {e}")

client.run(TOKEN)
