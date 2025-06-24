import discord
from discord.ext import commands
import aiohttp
import asyncio
import os

TOKEN = os.getenv("DISCORD_TOKEN")
print(TOKEN)
WEBHOOK_URL = 'https://webhook.ninjadasautomacoes.com/webhook/discord/cadastrar'
ROLE_NAME = "ninjas"

INTENTS = discord.Intents.default()
INTENTS.members = True
INTENTS.messages = True
INTENTS.message_content = True

bot = commands.Bot(command_prefix="!", intents=INTENTS)

@bot.event
async def on_ready():
    print(f'Bot online como {bot.user}!')

class RetryView(discord.ui.View):
    def __init__(self, member):
        super().__init__(timeout=300)
        self.member = member

    @discord.ui.button(label="🔁 Tentar novamente", style=discord.ButtonStyle.primary)
    async def retry_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.member:
            await interaction.response.send_message("⛔ Você não pode usar esse botão.", ephemeral=True)
            return
        await interaction.response.send_message("🔄 Vamos tentar de novo!", ephemeral=True)
        await start_email_check(self.member)  # reinicia fluxo

async def start_email_check(member):
    try:
        dm = await member.create_dm()
        await dm.send("👋 Olá! Para completar seu acesso, por favor, informe seu e-mail:")

        def check(msg):
            return msg.author == member and isinstance(msg.channel, discord.DMChannel)

        for attempt in range(3):
            try:
                msg = await bot.wait_for("message", check=check, timeout=120)
                email = msg.content.strip()

                async with aiohttp.ClientSession() as session:
                    payload = {"email": email, "username": member.name, "user_id": str(member.id)}
                    async with session.post(WEBHOOK_URL, json=payload) as resp:
                        data = await resp.json()

                if data.get("active"):
                    role = discord.utils.get(member.guild.roles, name=ROLE_NAME)
                    if role:
                        await member.add_roles(role)
                        await dm.send(f"✅ Seu e-mail foi validado. Cargo '{ROLE_NAME}' atribuído!")
                    else:
                        await dm.send(f"⚠️ E-mail válido, mas o cargo '{ROLE_NAME}' não foi encontrado.")
                    return
                else:
                    await dm.send(f"❌ E-mail não encontrado. Tente novamente. ({attempt+1}/3)")
            except asyncio.TimeoutError:
                break
            except Exception as e:
                print(f"[ERRO] {e}")
                await dm.send("⚠️ Ocorreu um erro. Tente novamente.")

        # Envia botão de retry
        view = RetryView(member)
        await dm.send("❌ Tentativas esgotadas ou tempo excedido. Deseja tentar novamente?", view=view)

    except Exception as e:
        print(f"[ERRO FINAL] {e}")

@bot.event
async def on_member_join(member):
    await asyncio.sleep(2)
    await start_email_check(member)

bot.run(TOKEN)