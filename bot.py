import os
import discord
from discord import app_commands
import subprocess
import tempfile
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

TARGET_CHANNEL_ID = int(os.getenv("TARGET_CHANNEL_ID", 0))
ALLOWED_ROLE_ID = int(os.getenv("ALLOWED_ROLE_ID", 0))
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", 0))
TOKEN = os.getenv("DISCORD_TOKEN")

# 1. IDINAGDAG NATIN ITO: Yung ID ng Owner Role mo
OWNER_ROLE_ID = 1455066902308327526

DEOB_DIR = "/app/deob/Deobfuscator/deobf"

@client.event
async def on_ready():
    await tree.sync()
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    # --- EXISTING ANTI-SPAM LOGIC MO ---
    if message.author == client.user or not message.guild:
        return

    if message.channel.id == TARGET_CHANNEL_ID:
        if message.author.guild_permissions.administrator:
            return
        
        has_allowed_role = any(role.id == ALLOWED_ROLE_ID for role in message.author.roles)
        
        if not has_allowed_role:
            try:
                await message.delete()
            except Exception as e:
                print(f"Hindi mabura ang mensahe: {e}")

            if LOG_CHANNEL_ID:
                try:
                    log_channel = client.get_channel(LOG_CHANNEL_ID)
                    if log_channel:
                        await log_channel.send(f"**{message.author}** has been kicked for sending a message in the anti-spam channel.")
                except Exception as e:
                    print(f"Hindi makapag-send sa log channel: {e}")

            try:
                await message.guild.kick(message.author, reason="Nag-chat sa restricted channel.")
                print(f"Na-kick si {message.author} dahil nag-chat sa ipinagbabawal na channel.")
            except Exception as e:
                print(f"Nabigo ang pag-kick: {e}")


# --- DEOBFUSCATION COMMAND (OWNER ONLY) ---
@tree.command(name="deob", description="I-deobfuscate ang Luraph file (Owner only)")
async def deob(interaction: discord.Interaction, file: discord.Attachment):
    
    # 2. AUTHORIZATION CHECK: Dito natin chinecheck kung may Owner Role o kaya ay Server Owner
    is_owner = any(role.id == OWNER_ROLE_ID for role in interaction.user.roles)
    is_server_owner = interaction.guild and interaction.guild.owner_id == interaction.user.id
    
    if not (is_owner or is_server_owner):
        # Ephemeral = ikaw lang makakakita ng message, hindi yung ibang tao sa channel
        await interaction.response.send_message("❌ Hindi ka authorized na gumamit ng command na ito. Owner Role lang ang pwedeng mag-deobfuscate.", ephemeral=True)
        return

    # Kung authorized, saka pa lang mag-defer
    await interaction.response.defer()

    if not file.filename.endswith(".lua"):
        await interaction.followup.send("Lua file lang ang tinatanggap.")
        return

    if file.size > 5 * 1024 * 1024:
        await interaction.followup.send("Masyadong malaki ang file (max 5MB).")
        return

    with tempfile.TemporaryDirectory() as tmp:
        inp = os.path.join(tmp, "input.lua")
        out = os.path.join(tmp, "output.lua")
        await file.save(inp)

        try:
            # Subukan muna ang v15
            proc = await asyncio.create_subprocess_exec(
                "python", "deob.py", inp, "-o", out,
                "--obfuscator", "luraph_v15",
                cwd=DEOB_DIR,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)

            # Kung fail, subukan ang v14
            if proc.returncode != 0 or not os.path.exists(out):
                proc = await asyncio.create_subprocess_exec(
                    "python", "cli.py", inp, "-o", out,
                    "--engine", "14.9",
                    cwd=DEOB_DIR,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)

            if os.path.exists(out):
                await interaction.followup.send(file=discord.File(out))
            else:
                await interaction.followup.send(f"Failed: {stderr.decode()[:1000]}")

        except asyncio.TimeoutError:
            await interaction.followup.send("Timeout ang deobfuscation. Masyadong malaki o kumplikado ang file.")

client.run(TOKEN)
