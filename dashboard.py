import streamlit as st
import asyncpg
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()   # ⬅️ CARREGUE O .ENV ANTES DE IMPORTAR SEUS MÓDULOS

from database import get_db  # agora o get_db lê a DATABASE_URL corretamente


DATABASE_URL = os.getenv("DATABASE_URL")

st.set_page_config(
    page_title="👑 Hakuryū Dashboard",
    page_icon="🐉",
    layout="wide"
)

# Função para montar URL do avatar do Discord
def discord_avatar_url(discord_id, avatar_hash, size=128):
    if avatar_hash:
        return f"https://cdn.discordapp.com/avatars/{discord_id}/{avatar_hash}.png?size={size}"
    # Fallback: avatar padrão do Discord (usa o discriminador, mas pode deixar um placeholder)
    return "https://cdn.discordapp.com/embed/avatars/0.png"

async def get_membros():
    conn = await get_db()
    try:
        rows = await conn.fetch("""
        SELECT discord_id, discord_username, nome_roblox, nome_rp, genero, altura_jogo,
           estilo_luta_principal, cargo, divisao, status, avatar_hash
        FROM membros
        ORDER BY data_entrada DESC
        """)
        return rows
    finally:
        await conn.close()

st.title("👑• 𝐇𝐚𝐤𝐮𝐫𝐲𝐮̄ (白竜) •👑")
st.caption("Dashboard de gestão da gang")

membros = asyncio.run(get_membros())

# Filtros
st.sidebar.header("Filtros")
cargos = ["Todos"] + sorted({m["cargo"] for m in membros})
cargo_filter = st.sidebar.selectbox("Cargo", cargos)
status_list = ["Todos"] + sorted({m["status"] for m in membros})
status_filter = st.sidebar.selectbox("Status", status_list)
divisoes = ["Todas"] + sorted({m["divisao"] for m in membros if m["divisao"]})
divisao_filter = st.sidebar.selectbox("Divisão", divisoes)

if cargo_filter != "Todos":
    membros = [m for m in membros if m["cargo"] == cargo_filter]
if status_filter != "Todos":
    membros = [m for m in membros if m["status"] == status_filter]
if divisao_filter != "Todas":
    membros = [m for m in membros if m["divisao"] == divisao_filter]

st.subheader(f"👥 Membros ({len(membros)})")

if not membros:
    st.info("Nenhum membro encontrado.")
else:
    cols = st.columns(3)
    for idx, m in enumerate(membros):
        with cols[idx % 3]:
            avatar_url = discord_avatar_url(m["discord_id"], m["avatar_hash"])
            st.image(avatar_url, width=100)

            discord_nome = m["discord_username"] or f"ID: {m['discord_id']}"
            st.markdown(f"**{discord_nome}**")
            st.caption(f"🎮 Roblox: {m['nome_roblox']}")
            if m["nome_rp"]:
                st.caption(f"📜 RP: {m['nome_rp']}")
            divisao = m["divisao"] or "Sem divisão"
            st.caption(f"🔰 Divisão: **{divisao}**")
            st.caption(f"⚜️ Cargo: {m['cargo']} | Status: {m['status']}")
            if m["altura_jogo"]:
                st.caption(f"📏 Altura: {m['altura_jogo']}m")
            if m["estilo_luta_principal"]:
                st.caption(f"🥋 Estilo: {m['estilo_luta_principal']}")
            st.markdown("---")