import os
import discord

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)

TARGET_CHANNEL_ID = int(os.getenv("TARGET_CHANNEL_ID", 0))
ALLOWED_ROLE_ID = int(os.getenv("ALLOWED_ROLE_ID", 0))
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
            try:
                await message.guild.kick(message.author, reason="Nag-chat sa restricted channel.")
                print(f"Na-kick si {message.author} dahil nag-chat sa ipinagbabawal na channel.")
            except discord.Forbidden:
                print("Walang sapat na permisos ang bot para mag-kick.")
            except discord.HTTPException:
                print("Nabigo ang pag-kick.")

client.run(TOKEN)

