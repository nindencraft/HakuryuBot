import discord
from discord import app_commands
from discord.ext import commands
from database import fetch_one, execute
import datetime
import traceback
from typing import Literal

print("🔥🔥🔥 MEMBROS.PY NOVO FOI CARREGADO 🔥🔥🔥")

class Membros(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # =============================================
    # GANG DO SERVIDOR (multi-gang)
    # =============================================
    async def gang_da_guild(self, interaction: discord.Interaction):
        """Retorna o id da gang ligada ao servidor onde o comando foi usado."""
        if interaction.guild is None:
            return None
        row = await fetch_one(
            "SELECT id FROM gangs WHERE guild_id = $1 AND ativo = true",
            str(interaction.guild.id),
        )
        return row["id"] if row else None

    async def exigir_gang(self, interaction: discord.Interaction):
        """Garante que o servidor tem gang registrada; senão responde e devolve None."""
        gang_id = await self.gang_da_guild(interaction)
        if gang_id is None:
            await interaction.followup.send(
                "❌ Este servidor ainda não está registrado como gang no painel. "
                "Peça ao Super Owner para registrar o servidor em **Gangs registradas**.",
                ephemeral=True,
            )
            return None
        return gang_id

    # ========== PERMISSÕES (por gang) ==========
    async def tem_permissao(
        self,
        member: discord.Member,
        funcao: str,
        gang_id: int
    ) ->     bool:

        row = await fetch_one(
            """
            SELECT valor
            FROM gang_config
            WHERE gang_id = $1
              AND chave = $2
            """,
            gang_id,
            f"cargo_id:{funcao}",
        )

        if not row or not row["valor"]:
            return False

        try:
            role_id = int(row["valor"])
        except (TypeError, ValueError):
            return False

        return any(role.id == role_id for role in member.roles)

    async def tem_alguma_funcao(self, member: discord.Member, funcoes: list, gang_id: int) -> bool:
        for funcao in funcoes:
            if await self.tem_permissao(member, funcao, gang_id):
                return True
        return False

    async def erro(self, interaction: discord.Interaction, e: Exception):
        """Nunca deixa a interação presa em 'pensando'."""
        traceback.print_exc()
        try:
            await interaction.followup.send(
                f"❌ Erro ao executar o comando: `{e}`", ephemeral=True
            )
        except Exception:
            pass

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
    )
    async def registrar(
        self,
        interaction: discord.Interaction,
        membro: discord.Member,
        nome_roblox: str,
        nome_rp: str = None,
        genero: Literal["Masculino", "Feminino"] = "Masculino",
        altura: float = 1.75,
        estilo_luta: str = None,
    ):
        # Resposta imediata para evitar timeout
        await interaction.response.defer(ephemeral=True)

        try:
            gang_id = await self.exigir_gang(interaction)
            if gang_id is None:
                return

            if not await self.tem_alguma_funcao(
                interaction.user, ["Lider", "Vice-Lider", "Líder de Divisão"], gang_id
            ):
                return await interaction.followup.send("❌ Sem permissão.", ephemeral=True)

            discord_id = str(membro.id)
            discord_username = str(membro)

            if altura <= 0 or altura > 3.0:
                return await interaction.followup.send(
                    "❌ Altura inválida. Informe um valor entre 0.50 e 3.00 (ex: 1.75). "
                    "Use ponto, não vírgula.",
                    ephemeral=True,
                )

            # Já registrado NESTA gang?
            existente = await fetch_one(
                "SELECT 1 FROM membros WHERE discord_id = $1 AND gang_id = $2",
                discord_id,
                gang_id,
            )
            if existente:
                return await interaction.followup.send(
                    "⚠️ Este membro já está registrado no banco de dados desta gang.",
                    ephemeral=True,
                )

            avatar_hash = membro.avatar.key if membro.avatar else None
            
            print(f"🔥 INSERT NOVO | gang_id={gang_id} | membro={discord_id}")
        
            await execute(
                """
                INSERT INTO membros (
                    discord_id, discord_username, nome_roblox, nome_rp, genero,
                    altura_jogo, estilo_luta_principal, cargo, status,
                    data_entrada, avatar_hash, gang_id
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, 'Em Analise', 'Ativo', $8, $9, $10)
                """,
                discord_id,
                discord_username,
                nome_roblox,
                nome_rp,
                genero,
                altura,
                estilo_luta,
                datetime.date.today(),
                avatar_hash,
                gang_id,
            )

            # Buscar o ID do cargo "Em Analise" configurado para a gang
            cargo_row = await fetch_one(
                    """
                    SELECT valor
                    FROM gang_config
                    WHERE gang_id = $1
                      AND chave = 'cargo_id:Em Analise'
                    """,
                    gang_id,
                )

            if cargo_row and cargo_row["valor"]:
                try:
                    cargo_id = int(cargo_row["valor"])
                    cargo = interaction.guild.get_role(cargo_id)

                    if cargo:
                        await interaction.user.add_roles(cargo)
                    else:
                        print(f"⚠️ Cargo Em Analise não encontrado: {cargo_id}")

                except (ValueError, TypeError) as e:
                    print(f"⚠️ ID do cargo Em Analise inválido: {e}")
                except discord.Forbidden:
                    print("❌ O bot não tem permissão para dar o cargo Em Analise.")

            embed = discord.Embed(
                title="✅ Membro Registrado",
                description=f"{membro.mention} entrou como **Em Análise** e aguarda aprovação da liderança.",
                color=discord.Color.gold(),
            )
            embed.add_field(name="Discord", value=discord_username, inline=True)
            embed.add_field(name="Roblox", value=nome_roblox, inline=True)
            embed.add_field(name="Altura", value=f"{altura}m", inline=True)
            if nome_rp:
                embed.add_field(name="Nome RP", value=nome_rp, inline=True)
            if estilo_luta:
                embed.add_field(name="Estilo de Luta", value=estilo_luta, inline=True)

            await interaction.followup.send(embed=embed)
        except Exception as e:
            await self.erro(interaction, e)

    # =============================================
    # COMANDO: /remover-registro
    # =============================================
    @app_commands.command(
        name="remover-registro", description="Remove um membro do banco de dados da gang"
    )
    @app_commands.describe(membro="Membro a ser removido")
    async def remover_registro(self, interaction: discord.Interaction, membro: discord.Member):
        await interaction.response.defer(ephemeral=True)

        try:
            gang_id = await self.exigir_gang(interaction)
            if gang_id is None:
                return

            if not await self.tem_alguma_funcao(
                interaction.user, ["Lider", "Vice-Lider", "Líder de Divisão"], gang_id
            ):
                return await interaction.followup.send("❌ Sem permissão.", ephemeral=True)

            discord_id = str(membro.id)
            existe = await fetch_one(
                "SELECT 1 FROM membros WHERE discord_id = $1 AND gang_id = $2",
                discord_id,
                gang_id,
            )
            if not existe:
                return await interaction.followup.send(
                    "⚠️ Este membro não está registrado nesta gang.", ephemeral=True
                )

            await execute(
                "DELETE FROM membros WHERE discord_id = $1 AND gang_id = $2",
                discord_id,
                gang_id,
            )
            await interaction.followup.send(
                f"✅ Registro de {membro.mention} removido do banco de dados.", ephemeral=True
            )
        except Exception as e:
            await self.erro(interaction, e)

    # =============================================
    # COMANDO: /ficha
    # =============================================
    @app_commands.command(name="ficha", description="Exibe a ficha completa de um membro")
    @app_commands.describe(membro="Usuário do Discord")
    async def ficha(self, interaction: discord.Interaction, membro: discord.Member):
        await interaction.response.defer(ephemeral=True)

        try:
            gang_id = await self.exigir_gang(interaction)
            if gang_id is None:
                return

            discord_id = str(membro.id)
            dados = await fetch_one(
                """
                SELECT m.discord_username, m.nome_roblox, m.nome_rp, m.genero,
                       m.altura_jogo, m.estilo_luta_principal, m.cargo, m.status,
                       m.data_entrada, m.observacoes, m.pontos_fortes_gerais,
                       m.pontos_fracos_gerais, m.avatar_hash,
                       d.nome_divisao AS divisao
                FROM membros m
                LEFT JOIN divisoes d ON d.id = m.divisao_id AND d.gang_id = m.gang_id
                WHERE m.discord_id = $1 AND m.gang_id = $2
                """,
                discord_id,
                gang_id,
            )
            if not dados:
                return await interaction.followup.send(
                    "❌ Membro não encontrado no banco desta gang. Use `/registrar` primeiro.",
                    ephemeral=True,
                )

            embed = discord.Embed(
                title=f"📋 Ficha de {membro.display_name}", color=discord.Color.blue()
            )
            if dados["avatar_hash"]:
                embed.set_thumbnail(
                    url=f"https://cdn.discordapp.com/avatars/{discord_id}/{dados['avatar_hash']}.png?size=128"
                )

            embed.add_field(name="Discord", value=dados["discord_username"] or "—", inline=True)
            embed.add_field(name="Nome RP", value=dados["nome_rp"] or "—", inline=True)
            embed.add_field(name="Roblox", value=dados["nome_roblox"], inline=True)
            embed.add_field(name="Gênero", value=dados["genero"] or "—", inline=True)
            embed.add_field(
                name="Altura",
                value=f"{dados['altura_jogo']}m" if dados["altura_jogo"] else "—",
                inline=True,
            )
            embed.add_field(
                name="Estilo de Luta", value=dados["estilo_luta_principal"] or "—", inline=True
            )
            embed.add_field(name="Cargo", value=dados["cargo"], inline=True)
            embed.add_field(name="Divisão", value=dados["divisao"] or "Nenhuma", inline=True)
            embed.add_field(name="Status", value=dados["status"], inline=True)
            embed.add_field(name="Entrada", value=str(dados["data_entrada"]), inline=True)

            if dados["pontos_fortes_gerais"]:
                embed.add_field(
                    name="💪 Pontos Fortes", value=dados["pontos_fortes_gerais"], inline=False
                )
            if dados["pontos_fracos_gerais"]:
                embed.add_field(
                    name="⚠️ Pontos Fracos", value=dados["pontos_fracos_gerais"], inline=False
                )
            if dados["observacoes"]:
                embed.add_field(name="📝 Observações", value=dados["observacoes"], inline=False)

            await interaction.followup.send(embed=embed)
        except Exception as e:
            await self.erro(interaction, e)

    # =============================================
    # COMANDO: /atualizar-avatar
    # =============================================
    @app_commands.command(
        name="atualizar-avatar", description="Atualiza o avatar de um membro no banco de dados"
    )
    @app_commands.describe(membro="Usuário do Discord (deixe vazio para você mesmo)")
    async def atualizar_avatar(
        self, interaction: discord.Interaction, membro: discord.Member = None
    ):
        await interaction.response.defer(ephemeral=True)

        try:
            gang_id = await self.exigir_gang(interaction)
            if gang_id is None:
                return

            if membro is None:
                membro = interaction.user

            pode_gerir = await self.tem_alguma_funcao(
                interaction.user, ["Lider", "Vice-Lider", "Líder de Divisão"], gang_id
            )
            if not pode_gerir and interaction.user.id != membro.id:
                return await interaction.followup.send(
                    "❌ Você só pode atualizar seu próprio avatar. "
                    "Peça a um líder para atualizar o de outros.",
                    ephemeral=True,
                )

            avatar_hash = membro.avatar.key if membro.avatar else None
            if not avatar_hash:
                return await interaction.followup.send(
                    "❌ Esse usuário não possui avatar no Discord.", ephemeral=True
                )

            await execute(
                "UPDATE membros SET avatar_hash = $1 WHERE discord_id = $2 AND gang_id = $3",
                avatar_hash,
                str(membro.id),
                gang_id,
            )
            await interaction.followup.send(
                f"✅ Hash do avatar de {membro.mention} salva no banco!", ephemeral=True
            )
        except Exception as e:
            await self.erro(interaction, e)


async def setup(bot):
    await bot.add_cog(Membros(bot))
