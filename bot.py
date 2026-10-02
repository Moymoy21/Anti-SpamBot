import os
import discord
from discord import app_commands
import subprocess
import tempfile
import asyncio
import shutil

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

TARGET_CHANNEL_ID = int(os.getenv("TARGET_CHANNEL_ID", 0))
ALLOWED_ROLE_ID = int(os.getenv("ALLOWED_ROLE_ID", 0))
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", 0))
TOKEN = os.getenv("DISCORD_TOKEN")

OWNER_ROLE_ID = 1455066902308327526

# --- BINAGO NATIN ITO: Tumutukoy na sa bagong folder na /app/deob2 ---
DEOB_DIR = "/app/deob2" 

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


# --- DROP-DOWN MENU CLASS ---
class DeobSelect(discord.ui.Select):
    def __init__(self, file_path):
        self.file_path = file_path
        
        options = [
            discord.SelectOption(label="Auto-Detect", value="auto", description="Awtomatikong i-detect ang version"),
            discord.SelectOption(label="Luraph v15", value="v15", description="Para sa v15 scripts"),
            discord.SelectOption(label="Luraph v14.9", value="14.9", description="Para sa v14.9 scripts"),
            discord.SelectOption(label="Luraph v14.8", value="14.8", description="Para sa v14.8 scripts"),
            discord.SelectOption(label="Luraph v14.7", value="14.7", description="Para sa v14.7 scripts"),
        ]
        
        super().__init__(placeholder="Choose the Deobfuscator...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.view.original_user.id:
            await interaction.response.send_message("❌ Hindi ikaw ang nag-upload ng file na ito.", ephemeral=True)
            return

        await interaction.response.defer()

        choice = self.values[0]
        out = os.path.join(os.path.dirname(self.file_path), "output.lua")

        try:
            # Dito natin ipapatakbo ang mehCake tool
            # Karaniwan sa mehCake, ang command ay: python main.py input.lua -o output.lua
            # Kung magka-error, maaaring kailangan i-adjust ang arguments na ito.
            proc = await asyncio.create_subprocess_exec(
                "python", "main.py", self.file_path, "-o", out,
                cwd=DEOB_DIR,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)

            if os.path.exists(out):
                await interaction.followup.send(file=discord.File(out))
            else:
                # Fallback kung iba ang syntax ng output ng mehCake
                # Minsan kasi automatic na ginagawa yung output.lua sa tabi ng input
                possible_output = self.file_path.replace(".lua", ".deob.lua")
                if os.path.exists(possible_output):
                    await interaction.followup.send(file=discord.File(possible_output))
                else:
                    await interaction.followup.send(f"❌ Failed: {stderr.decode()[:1000]}")

        except asyncio.TimeoutError:
            await interaction.followup.send("❌ Timeout ang deobfuscation.")
        
        try:
            shutil.rmtree(os.path.dirname(self.file_path))
        except:
            pass


class DeobView(discord.ui.View):
    def __init__(self, file_path, original_user):
        super().__init__(timeout=300)
        self.original_user = original_user
        self.add_item(DeobSelect(file_path))


# --- DEOBFUSCATION COMMAND (OWNER ONLY) ---
@tree.command(name="deob", description="I-deobfuscate ang Luraph file (Owner only)")
async def deob(interaction: discord.Interaction, file: discord.Attachment):
    
    is_owner = any(role.id == OWNER_ROLE_ID for role in interaction.user.roles)
    is_server_owner = interaction.guild and interaction.guild.owner_id == interaction.user.id
    
    if not (is_owner or is_server_owner):
        await interaction.response.send_message("❌ Hindi ka authorized. Owner Role lang ang pwedeng mag-deobfuscate.", ephemeral=True)
        return

    await interaction.response.defer()

    if not file.filename.endswith(".lua"):
        await interaction.followup.send("Lua file lang ang tinatanggap.")
        return

    if file.size > 5 * 1024 * 1024:
        await interaction.followup.send("Masyadong malaki ang file (max 5MB).")
        return

    tmpdir = tempfile.mkdtemp()
    inp = os.path.join(tmpdir, "input.lua")
    await file.save(inp)

    detected_version = "Unknown (Pumili sa drop-down)"
    try:
        with open(inp, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(2000)
            
            if "v15" in content.lower() or "luraph_v15" in content.lower():
                detected_version = "Luraph v15"
            elif "v14.9" in content.lower():
                detected_version = "Luraph v14.9"
            elif "v14.8" in content.lower():
                detected_version = "Luraph v14.8"
            elif "v14.7" in content.lower():
                detected_version = "Luraph v14.7"
    except Exception as e:
        print(f"Detection error: {e}")

    view = DeobView(inp, interaction.user)

    await interaction.followup.send(
        f"🔍 **Detected:** {detected_version}\n\n👇 **Choose the Deobfuscator:**",
        view=view
    )

client.run(TOKEN)
