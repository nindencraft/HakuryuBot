import discord
from discord import app_commands
from discord.ext import commands
from database import execute, fetch_all, fetch_one

CARGOS_PARCEIROS = ["Lider", "Vice-Lider"]

class Parcerias(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ========== NOVAS FUNÇÕES DE PERMISSÃO ==========
    async def tem_permissao(self, member: discord.Member, funcao: str) -> bool:
        row = await fetch_one(
            "SELECT discord_role_id FROM config_cargos WHERE funcao = $1", funcao
        )
        if not row:
            return False
        role_id = int(row["discord_role_id"])
        return any(role.id == role_id for role in member.roles)

    async def tem_alguma_funcao(self, member: discord.Member, funcoes: list) -> bool:
        for funcao in funcoes:
            if await self.tem_permissao(member, funcao):
                return True
        return False
    # ================================================

    @app_commands.command(name="adicionar-parceria", description="Registra uma nova gang parceira")
    @app_commands.describe(
        nome="Nome da gang",
        lider_contato="Discord do líder (tag ou ID)",
        server_id="ID do servidor Discord da gang",
        termos="Termos da parceria"
    )
    async def adicionar_parceria(
        self,
        interaction: discord.Interaction,
        nome: str,
        lider_contato: str = None,
        server_id: str = None,
        termos: str = None
    ):
        if not await self.tem_alguma_funcao(interaction.user, ["Lider", "Vice-Lider"]):
            return await interaction.response.send_message("❌ Sem permissão.", ephemeral=True)

        await execute(
            """
            INSERT INTO parcerias (nome_gang, lider_contato, discord_server_id, termos, representante_nossa_gang)
            VALUES ($1, $2, $3, $4, $5)
            """,
            nome, lider_contato, server_id, termos, str(interaction.user.id)
        )
        await interaction.response.send_message(f"🤝 Parceria com **{nome}** registrada com sucesso!")

    @app_commands.command(name="parcerias", description="Lista todas as parcerias atuais")
    async def listar_parcerias(self, interaction: discord.Interaction):
        rows = await fetch_all("SELECT * FROM parcerias WHERE status = 'Aliado' ORDER BY data_parceria DESC")
        if not rows:
            return await interaction.response.send_message("🤷 Nenhuma parceria ativa.", ephemeral=True)

        embed = discord.Embed(title="🌐 Parcerias da 👑• 𝐇𝐚𝐤𝐮𝐫𝐲𝐮̄ (白竜) •👑", color=discord.Color.purple())
        for r in rows:
            embed.add_field(
                name=r["nome_gang"],
                value=f"**Contato:** {r['lider_contato'] or 'N/A'}\n**Servidor:** {r['discord_server_id'] or 'N/A'}\n**Desde:** {r['data_parceria']}",
                inline=False
            )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Parcerias(bot))