import discord
from discord import app_commands
from discord.ext import commands
from database import execute, fetch_one

CARGOS_GESTAO = ["Lider", "Vice-Lider", "Líder de Divisão"]

class Divisoes(commands.Cog):
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

    def tem_permissao(self, member: discord.Member) -> bool:
        cargos_nomes = [role.name for role in member.roles]
        return any(c in cargos_nomes for c in CARGOS_GESTAO)

    @app_commands.command(name="setar-divisao", description="Atribui um membro a uma divisão")
    @app_commands.describe(membro="Membro", divisao="Nome da divisão (ex: Vanguard)")
    async def setar_divisao(self, interaction: discord.Interaction, membro: discord.Member, divisao: str):
        if not await self.tem_alguma_funcao(interaction.user, ["Lider", "Vice-Lider", "Líder de Divisão"]):
            return await interaction.response.send_message("❌ Sem permissão.", ephemeral=True)

        discord_id = str(membro.id)
        # Verifica se o membro existe no banco
        existe = await fetch_one("SELECT 1 FROM membros WHERE discord_id = $1", discord_id)
        if not existe:
            return await interaction.response.send_message("❌ Membro não registrado.", ephemeral=True)

        await execute("UPDATE membros SET divisao = $1 WHERE discord_id = $2", divisao, discord_id)

        # Opcional: também atualizar o cargo do Discord (se houver um cargo com o nome da divisão)
        # Exemplo: atribuir role do Discord com mesmo nome da divisão
        role = discord.utils.get(interaction.guild.roles, name=divisao)
        if role:
            await membro.add_roles(role, reason=f"Atribuído à divisão {divisao}")

        await interaction.response.send_message(f"✅ {membro.mention} agora faz parte da divisão **{divisao}**.")

async def setup(bot):
    await bot.add_cog(Divisoes(bot))