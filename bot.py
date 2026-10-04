import os
import discord
from discord import app_commands
from openai import AsyncOpenAI

from collections import defaultdict
from tavily import TavilyClient

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

conversation_history = defaultdict(list)
MAX_HISTORY = 20

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# ==== ENV VARIABLES ====
TOKEN = os.getenv("DISCORD_TOKEN")
TARGET_CHANNEL_ID = int(os.getenv("TARGET_CHANNEL_ID", 0))
ALLOWED_ROLE_ID = int(os.getenv("ALLOWED_ROLE_ID", 0))
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", 0))

AI_CHANNEL_ID = int(os.getenv("AI_CHANNEL_ID", 0))
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

OWNER_ROLE_ID = 1455066902308327526
AI_PREFIX = ".ai"

# Models
TEXT_MODEL = "openai/gpt-oss-120b"
VISION_MODEL = "qwen/qwen3.8-27b"

client_ai = AsyncOpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

SYSTEM_PROMPT = """You are a helpful AI assistant on Discord with web search access.

When you receive web search results (marked as [Web Search Results]), use them to answer accurately.
- If the search results contain the answer, use them.
- If not, say so honestly and give your best knowledge.
- Cite sources briefly when using search results.
- Be conversational and natural — match the user's tone.
- If the user sends an image, describe it and answer questions about it accurately.
- Never help with piracy or illegal activities.

If you don't know something, say "I don't know" instead of guessing.
"""


def normalize_history_for_text(history):
    """Convert any multimodal (list) content to plain text para sa text-only models."""
    normalized = []
    for msg in history:
        if isinstance(msg.get("content"), list):
            text_parts = []
            has_image = False
            for part in msg["content"]:
                if part.get("type") == "text":
                    text_parts.append(part["text"])
                elif part.get("type") == "image_url":
                    has_image = True
            combined = " ".join(text_parts).strip()
            if has_image:
                combined += " [user sent an image]"
            normalized.append({"role": msg["role"], "content": combined or "[image]"})
        else:
            normalized.append(msg)
    return normalized


@client.event
async def on_ready():
    await tree.sync()
    print(f'Logged in as {client.user}', flush=True)


@client.event
async def on_message(message):
    if message.author == client.user or not message.guild:
        return

    # ==== AI HANDLER ====
    if message.channel.id == AI_CHANNEL_ID:
        prompt = None

        # Check 1: Nag-reply ba sa bot?
        if message.reference and message.reference.message_id:
            try:
                replied = message.reference.resolved
                if not replied:
                    replied = await message.channel.fetch_message(message.reference.message_id)

                if replied and replied.author.id == client.user.id:
                    prompt = message.content.strip()
                    print(f"Reply detected from {message.author}: {prompt}", flush=True)
            except Exception as e:
                print(f"Fetch replied message error: {e}", flush=True)

        # Check 2: May .ai prefix ba?
        if prompt is None and message.content.startswith(AI_PREFIX):
            prompt = message.content[len(AI_PREFIX):].strip()

        # Check 3: May image ba (kahit walang text/prompt)?
        image_urls = []
        if message.attachments:
            for att in message.attachments:
                if att.content_type and att.content_type.startswith("image/"):
                    image_urls.append(att.url)

        # Ignore kung walang prompt AT walang image
        if prompt is None and not image_urls:
            return

        # Kung may image pero walang text prompt, bigyan ng default prompt
        if prompt is None and image_urls:
            prompt = "Ano ang nasa image na ito?"

        if prompt == "":
            prompt = "Ano ang nasa image na ito?"

        # Reset command
        if prompt.lower() in ["reset", "clear"]:
            key = (message.channel.id, message.author.id)
            conversation_history.pop(key, None)
            await message.reply("🧹 Conversation memory cleared.")
            return

        async with message.channel.typing():
            try:
                key = (message.channel.id, message.author.id)

                search_keywords = ["search", "latest", "news", "what is", "who is", "when did", "how to"]
                should_search = any(kw in prompt.lower() for kw in search_keywords) or len(prompt) > 50

                # Skip search kung may image (para hindi magulo ang vision)
                search_context = ""
                if should_search and not image_urls:
                    try:
                        results = tavily.search(query=prompt, max_results=3, search_depth="basic")
                        if results and results.get("results"):
                            search_context = "\n\n[Web Search Results]\n"
                            for r in results["results"]:
                                search_context += f"- {r['title']}: {r['content'][:300]}\n"
                    except Exception as e:
                        print(f"Search error: {e}", flush=True)

                user_content = prompt + search_context

                if image_urls:
                    # Multimodal: text + images
                    content_parts = [{"type": "text", "text": user_content}]
                    for url in image_urls:
                        content_parts.append({
                            "type": "image_url",
                            "image_url": {"url": url}
                        })
                    conversation_history[key].append({"role": "user", "content": content_parts})
                    model_to_use = VISION_MODEL
                else:
                    conversation_history[key].append({"role": "user", "content": user_content})
                    model_to_use = TEXT_MODEL

                if len(conversation_history[key]) > MAX_HISTORY:
                    conversation_history[key] = conversation_history[key][-MAX_HISTORY:]

                if model_to_use == TEXT_MODEL:
                    # Convert any multimodal history to text-only
                    safe_history = normalize_history_for_text(conversation_history[key])
                    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + safe_history
                    response = await client_ai.chat.completions.create(
                        model=model_to_use,
                        messages=messages,
                        temperature=0.4,
                        reasoning_effort="medium",
                    )
                else:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history[key]
    response = await client_ai.chat.completions.create(
        model=model_to_use,
        messages=messages,
        temperature=1.0,
        reasoning_effort="default",
    )
                answer = response.choices[0].message.content
                conversation_history[key].append({"role": "assistant", "content": answer})

            except Exception as e:
                answer = f"⚠️ AI Error: `{e}`"

        for i in range(0, len(answer), 1900):
            chunk = answer[i:i+1900]
            if i == 0:
                await message.reply(chunk)
            else:
                await message.channel.send(chunk)
        return

    # ==== ANTI-SPAM HANDLER ====
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
