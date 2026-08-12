import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

class HakuryuBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents, help_command=None)

    async def setup_hook(self):
        # Carrega todas as cogs
        cogs = [
            "cogs.membros",
            "cogs.punicoes",
            "cogs.avaliacoes",
            "cogs.recrutamento",
            "cogs.parcerias",
            "cogs.divisoes"
        ]
        for cog in cogs:
            await self.load_extension(cog)
        await self.tree.sync()
        print("Slash commands sincronizados!")

    async def on_ready(self):
        print(f"Bot {self.user} está online!")
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="👑• 𝐇𝐚𝐤𝐮𝐫𝐲𝐮̄ (白竜) •👑"
            )
        )

bot = HakuryuBot()
bot.run(TOKEN)