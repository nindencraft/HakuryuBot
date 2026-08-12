import discord
from discord import app_commands
from discord.ext import commands
from database import fetch_one, execute
import datetime
from typing import Literal  # adicione no topo do arquivo

class Membros(commands.Cog):
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

    # =============================================
    # COMANDO: /registrar
    # =============================================
    @app_commands.command(name="registrar", description="Registra um novo membro na gang")
    @app_commands.describe(
        membro="Usuário do Discord",
        nome_roblox="Nome no Roblox",
        nome_rp="Nome RP do personagem",
        genero="Gênero",
        altura="Altura no jogo (ex: 1.75)",
        estilo_luta="Estilo de luta principal",
        divisao="Divisão (ex: Vanguard, Scout)"
    )
    async def registrar(
        self,
        interaction: discord.Interaction,
        membro: discord.Member,
        nome_roblox: str,
        nome_rp: str = None,
        genero: Literal['Masculino', 'Feminino'] = 'Masculino',
        altura: float = 1.75,
        estilo_luta: str = None,
        divisao: str = None
    ):
        # Verifica permissão pelos cargos do Discord
        if not await self.tem_alguma_funcao(interaction.user, ["Lider", "Vice-Lider", "Líder de Divisão"]):
            return await interaction.response.send_message("❌ Sem permissão.", ephemeral=True)

        discord_id = str(membro.id)
        discord_username = str(membro)  # Ex: "Nome#1234" ou "nome"

        if altura <= 0 or altura > 3.0:
            return await interaction.response.send_message(
                "❌ Altura inválida. Informe um valor entre 0.50 e 3.00 (ex: 1.75). Use ponto, não vírgula.",
                ephemeral=True
    )

        # Verifica se já está registrado
        existente = await fetch_one("SELECT 1 FROM membros WHERE discord_id = $1", discord_id)
        if existente:
            return await interaction.response.send_message(
                "⚠️ Este membro já está registrado no banco de dados.",
                ephemeral=True
            )

        # Insere no banco
        await execute(
            """
            INSERT INTO membros (discord_id, discord_username, nome_roblox, nome_rp, genero, altura_jogo, estilo_luta_principal, cargo, status, data_entrada)
            VALUES ($1, $2, $3, $4, $5, $6, $7, 'Recruta', 'Ativo', $8)
            """,
            discord_id, discord_username, nome_roblox, nome_rp, genero, altura, estilo_luta, datetime.date.today()
        )

        avatar_hash = membro.avatar.key if membro.avatar else None
        if avatar_hash:
            await execute(
            "UPDATE membros SET avatar_hash = $1 WHERE discord_id = $2",
            avatar_hash, discord_id
        )
        
        # Embed de confirmação
        embed = discord.Embed(
            title="✅ Membro Registrado",
            description=f"{membro.mention} agora é um **Recruta** da 👑• 𝐇𝐚𝐤𝐮𝐫𝐲𝐮̄ (白竜) •👑",
            color=discord.Color.gold()
        )
        embed.add_field(name="Discord", value=discord_username, inline=True)
        embed.add_field(name="Roblox", value=nome_roblox, inline=True)
        embed.add_field(name="Altura", value=f"{altura}m", inline=True)
        if estilo_luta:
            embed.add_field(name="Estilo de Luta", value=estilo_luta, inline=True)
        await interaction.response.send_message(embed=embed)

    # =============================================
    # COMANDO: /excluir-registro
    # =============================================
    @app_commands.command(name="remover-registro", description="Remove um membro do banco de dados da gang")
    @app_commands.describe(membro="Membro a ser removido")
    async def remover_registro(self, interaction: discord.Interaction, membro: discord.Member):
        if not await self.tem_alguma_funcao(interaction.user, ["Lider", "Vice-Lider", "Líder de Divisão"]):
         return await interaction.response.send_message("❌ Sem permissão.", ephemeral=True)

        discord_id = str(membro.id)
        # Verifica se existe
        existe = await fetch_one("SELECT 1 FROM membros WHERE discord_id = $1", discord_id)
        if not existe:
            return await interaction.response.send_message("⚠️ Este membro não está registrado.", ephemeral=True)

        await execute("DELETE FROM membros WHERE discord_id = $1", discord_id)
        await interaction.response.send_message(f"✅ Registro de {membro.mention} removido do banco de dados.", ephemeral=True)
        
    # =============================================
    # COMANDO: /ficha
    # =============================================
    @app_commands.command(name="ficha", description="Exibe a ficha completa de um membro")
    @app_commands.describe(membro="Usuário do Discord")
    async def ficha(self, interaction: discord.Interaction, membro: discord.Member):
        discord_id = str(membro.id)
        dados = await fetch_one(
            """
            SELECT discord_username, nome_roblox, nome_rp, genero, altura_jogo, estilo_luta_principal,
           cargo, divisao, status, data_entrada, observacoes,
           pontos_fortes_gerais, pontos_fracos_gerais,
           avatar_hash
            FROM membros WHERE discord_id = $1
            """,
            discord_id
        )
        if not dados:
            return await interaction.response.send_message(
                "❌ Membro não encontrado no banco. Use `/registrar` primeiro.",
                ephemeral=True
            )

        embed = discord.Embed(
            title=f"📋 Ficha de {membro.display_name}",
            color=discord.Color.blue()
        )
        # Thumbnail a partir da hash
        if dados["avatar_hash"]:
            avatar_url = f"https://cdn.discordapp.com/avatars/{discord_id}/{dados['avatar_hash']}.png?size=128"
            embed.set_thumbnail(url=avatar_url)

        embed.add_field(name="Discord", value=dados["discord_username"] or "—", inline=True)
        embed.add_field(name="Nome RP", value=dados["nome_rp"] or "—", inline=True)
        embed.add_field(name="Roblox", value=dados["nome_roblox"], inline=True)
        embed.add_field(name="Gênero", value=dados["genero"], inline=True)
        embed.add_field(name="Altura", value=f"{dados['altura_jogo']}m" if dados["altura_jogo"] else "—", inline=True)
        embed.add_field(name="Estilo de Luta", value=dados["estilo_luta_principal"] or "—", inline=True)
        embed.add_field(name="Cargo", value=dados["cargo"], inline=True)
        embed.add_field(name="Divisão", value=dados["divisao"] or "Nenhuma", inline=True)
        embed.add_field(name="Status", value=dados["status"], inline=True)
        embed.add_field(name="Entrada", value=str(dados["data_entrada"]), inline=True)

        if dados["pontos_fortes_gerais"]:
            embed.add_field(name="💪 Pontos Fortes", value=dados["pontos_fortes_gerais"], inline=False)
        if dados["pontos_fracos_gerais"]:
            embed.add_field(name="⚠️ Pontos Fracos", value=dados["pontos_fracos_gerais"], inline=False)
        if dados["observacoes"]:
            embed.add_field(name="📝 Observações", value=dados["observacoes"], inline=False)

        await interaction.response.send_message(embed=embed)

    # =============================================
    # COMANDO: /atualizar-avatar
    # =============================================
    @app_commands.command(name="atualizar-avatar", description="Atualiza o avatar de um membro no banco de dados")
    @app_commands.describe(membro="Usuário do Discord (deixe vazio para você mesmo)")
    async def atualizar_avatar(self, interaction: discord.Interaction, membro: discord.Member = None):
        # Se não especificar, atualiza o próprio usuário
        if membro is None:
            membro = interaction.user

        # Apenas liderança ou o próprio membro podem atualizar
        if not await self.tem_alguma_funcao(interaction.user, ["Lider", "Vice-Lider", "Líder de Divisão"]) and interaction.user.id != membro.id:
            return await interaction.response.send_message(
                "❌ Você só pode atualizar seu próprio avatar. Peça a um líder para atualizar o de outros.",
                ephemeral=True
            )

        avatar_hash = membro.avatar.key if membro.avatar else None
        if avatar_hash:
            await execute(
                "UPDATE membros SET avatar_hash = $1 WHERE discord_id = $2",
                avatar_hash, str(membro.id)
            )
            await interaction.response.send_message(f"✅ Hash do avatar de {membro.mention} salva no banco!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Esse usuário não possui avatar no Discord.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Membros(bot))