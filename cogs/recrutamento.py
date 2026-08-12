import discord
from discord import app_commands
from discord.ext import commands
from database import execute, fetch_all, fetch_one
import datetime

CARGOS_RECRUTADORES = ["Recrutador", "Lider", "Vice-Lider", "Líder de Divisão"]

class Recrutamento(commands.Cog):
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

    @app_commands.command(name="votar-recruta", description="Vota pela aprovação/reprovação de um recruta")
    @app_commands.describe(candidato="Recruta em avaliação", decisao="Sim para aprovar, Não para reprovar", motivo="Justificativa")
    async def votar_recruta(
        self,
        interaction: discord.Interaction,
        candidato: discord.Member,
        decisao: bool,
        motivo: str = None
    ):
        # Apenas membros do conselho de recrutamento (defina o cargo)
        if not await self.tem_alguma_funcao(interaction.user, ["Recrutador", "Lider", "Vice-Lider", "Líder de Divisão"]):
            return await interaction.response.send_message("❌ Sem permissão.", ephemeral=True)

        recrutador_id = str(interaction.user.id)
        candidato_id = str(candidato.id)

        await execute(
            "INSERT INTO votos_recrutamento (candidato_id, recrutador_id, decisao, justificativa) VALUES ($1, $2, $3, $4)",
            candidato_id, recrutador_id, decisao, motivo
        )

        await interaction.response.send_message(f"✅ Voto registrado para {candidato.mention}: {'Aprovar' if decisao else 'Reprovar'}", ephemeral=True)

    @app_commands.command(name="status-recrutamento", description="Mostra a contagem de votos de um recruta")
    @app_commands.describe(candidato="Candidato")
    async def status_recrutamento(self, interaction: discord.Interaction, candidato: discord.Member):
        candidato_id = str(candidato.id)
        votos = await fetch_all(
            "SELECT decisao FROM votos_recrutamento WHERE candidato_id = $1",
            candidato_id
        )
        if not votos:
            return await interaction.response.send_message("❌ Nenhum voto encontrado.", ephemeral=True)

        aprovacoes = sum(1 for v in votos if v["decisao"])
        reprovacoes = len(votos) - aprovacoes

        embed = discord.Embed(title=f"🗳 Votação de {candidato.display_name}", color=discord.Color.blurple())
        embed.add_field(name="✅ Aprovações", value=str(aprovacoes))
        embed.add_field(name="❌ Reprovações", value=str(reprovacoes))
        embed.set_footer(text="Votos individuais são anônimos.")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Recrutamento(bot))