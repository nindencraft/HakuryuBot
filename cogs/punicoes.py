import discord
from discord import app_commands
from discord.ext import commands
from database import execute, fetch_all, fetch_one
import datetime

CARGOS_STAFF = ["Lider", "Vice-Lider", "Staff"]

class Punicoes(commands.Cog):
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

    @app_commands.command(name="warn", description="Aplica um warn a um membro")
    @app_commands.describe(membro="Membro a ser punido", motivo="Motivo do warn")
    async def warn(self, interaction: discord.Interaction, membro: discord.Member, motivo: str):
        # Verificar permissão (moderador+)
        if not interaction.user.guild_permissions.moderate_members:
            return await interaction.response.send_message("❌ Sem permissão.", ephemeral=True)

        discord_id = str(membro.id)
        staff_id = str(interaction.user.id)
        await execute(
            "INSERT INTO punicoes (membro_id, tipo, motivo, staff_id) VALUES ($1, 'Warn', $2, $3)",
            discord_id, motivo, staff_id
        )

        embed = discord.Embed(
            title="⚠️ Warn Aplicado",
            description=f"{membro.mention} recebeu um warn.",
            color=discord.Color.orange()
        )
        embed.add_field(name="Motivo", value=motivo, inline=False)
        embed.add_field(name="Staff", value=interaction.user.mention, inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="historico", description="Exibe o histórico de punições de um membro")
    @app_commands.describe(membro="Usuário")
    async def historico(self, interaction: discord.Interaction, membro: discord.Member):
        discord_id = str(membro.id)
        rows = await fetch_all(
            "SELECT tipo, motivo, data_aplicacao, staff_id FROM punicoes WHERE membro_id = $1 ORDER BY data_aplicacao DESC LIMIT 10",
            discord_id
        )
        if not rows:
            return await interaction.response.send_message("✅ Nenhuma punição registrada.", ephemeral=True)

        embed = discord.Embed(title=f"📜 Histórico de {membro.display_name}", color=discord.Color.dark_gray())
        for r in rows:
            staff = interaction.guild.get_member(int(r["staff_id"])) if r["staff_id"] else None
            staff_mention = staff.mention if staff else "Desconhecido"
            embed.add_field(
                name=f"{r['tipo']} em {r['data_aplicacao'].strftime('%d/%m/%Y')}",
                value=f"**Motivo:** {r['motivo']}\n**Por:** {staff_mention}",
                inline=False
            )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Punicoes(bot))