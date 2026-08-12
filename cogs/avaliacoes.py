import discord
from discord import app_commands
from discord.ext import commands
from database import execute, fetch_one
import datetime

class Avaliacoes(commands.Cog):
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

    @app_commands.command(name="avaliar", description="Avalia um membro após um treino")
    @app_commands.describe(
        membro="Membro avaliado",
        tipo="Tipo de treino (Interno/Amistoso/Guerra)",
        nota="Nota de 1 a 5",
        pontos_fortes="O que fez bem",
        pontos_fracos="O que precisa melhorar",
        comentarios="Observações adicionais"
    )
    async def avaliar(
    self,
    interaction: discord.Interaction,
    membro: discord.Member,
    tipo: str,
    nota: int,
    pontos_fortes: str = None,
    pontos_fracos: str = None,
    comentarios: str = None
):
    # Verificação pelos cargos definidos no banco (IDs)
        if not await self.tem_alguma_funcao(interaction.user, ["Lider", "Vice-Lider", "Staff"]):
            return await interaction.response.send_message("❌ Sem permissão.", ephemeral=True)
        avaliador_id = str(interaction.user.id)
        avaliado_id = str(membro.id)

        # Verifica se o avaliado existe
        membro_existe = await fetch_one("SELECT 1 FROM membros WHERE discord_id = $1", avaliado_id)
        if not membro_existe:
            return await interaction.response.send_message("❌ Membro não registrado no banco.", ephemeral=True)

        await execute(
            """
            INSERT INTO avaliacoes_treino
            (avaliador_id, membro_avaliado_id, data_treino, tipo_treino, pontos_fortes_observados, pontos_fracos_observados, nota_geral, comentarios)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            avaliador_id, avaliado_id, datetime.date.today(), tipo,
            pontos_fortes, pontos_fracos, nota, comentarios
        )

        embed = discord.Embed(title="📝 Avaliação Registrada", color=discord.Color.green())
        embed.add_field(name="Avaliado", value=membro.mention, inline=True)
        embed.add_field(name="Nota", value=f"{nota}/5", inline=True)
        embed.add_field(name="Tipo", value=tipo, inline=True)
        if pontos_fortes:
            embed.add_field(name="Pontos Fortes", value=pontos_fortes, inline=False)
        if pontos_fracos:
            embed.add_field(name="Pontos Fracos", value=pontos_fracos, inline=False)
        if comentarios:
            embed.add_field(name="Comentários", value=comentarios, inline=False)

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Avaliacoes(bot))