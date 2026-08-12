import streamlit as st
import datetime
import asyncpg
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from database import get_db
from auth import autenticar, esta_logado, tem_cargo, eh_dono, get_login_url

# Autenticação
autenticar()

if not esta_logado():
    st.title("👑 Hakuryū Dashboard")
    st.markdown("Faça login com Discord para acessar o painel.")
    st.link_button("🔐 Login com Discord", get_login_url())
    st.stop()

# Mostrar usuário logado
st.sidebar.image(st.session_state.user["avatar"], width=80)
st.sidebar.markdown(f"**{st.session_state.user['nome']}**")
st.sidebar.markdown(f"ID: `{st.session_state.user['id']}`")

# Controle de acesso: só membros da gang podem ver o restante
cargos_permitidos = ["Lider", "Vice-Lider", "Líder de Divisão", "Staff", "Recrutador", "Membro", "Em Analise"]
if not eh_dono() and not any(tem_cargo(c) for c in cargos_permitidos):
    st.error("Você não possui um cargo autorizado para acessar este dashboard.")
    st.stop()

st.set_page_config(
    page_title="👑 Hakuryū Dashboard",
    page_icon="🐉",
    layout="wide"
)

def discord_avatar_url(discord_id, avatar_hash, size=128):
    if avatar_hash:
        return f"https://cdn.discordapp.com/avatars/{discord_id}/{avatar_hash}.png?size={size}"
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

async def get_treinos():
    conn = await get_db()
    try:
        rows = await conn.fetch("""
            SELECT t.*, 
                   (SELECT COUNT(*) FROM presencas_treino p WHERE p.treino_id = t.id_treino AND p.inscricao = 'Confirmado') as inscritos
            FROM treinos t
            ORDER BY t.data_treino DESC
        """)
        return rows
    finally:
        await conn.close()

async def get_membros_ativos():
    conn = await get_db()
    try:
        return await conn.fetch("SELECT discord_id, discord_username FROM membros WHERE status = 'Ativo' ORDER BY discord_username")
    finally:
        await conn.close()

# ========== CARREGAR DADOS COM PROTEÇÃO ==========
try:
    membros = asyncio.run(get_membros())
    treinos = asyncio.run(get_treinos())
    membros_ativos = asyncio.run(get_membros_ativos())
except Exception as e:
    st.error(f"⚠️ Sem conexão com o banco de dados: {e}")
    st.info("Usando dados vazios para visualização do layout. Acesse o dashboard online para dados reais.")
    membros = []
    treinos = []
    membros_ativos = []

# ========== SIDEBAR (filtros globais de membros) ==========
st.sidebar.header("Filtros de Membros")
cargos = ["Todos"] + sorted({m["cargo"] for m in membros})
cargo_filter = st.sidebar.selectbox("Cargo", cargos)
status_list = ["Todos"] + sorted({m["status"] for m in membros})
status_filter = st.sidebar.selectbox("Status", status_list)
divisoes = ["Todas"] + sorted({m["divisao"] for m in membros if m["divisao"]})
divisao_filter = st.sidebar.selectbox("Divisão", divisoes)

membros_filtrados = membros
if cargo_filter != "Todos":
    membros_filtrados = [m for m in membros_filtrados if m["cargo"] == cargo_filter]
if status_filter != "Todos":
    membros_filtrados = [m for m in membros_filtrados if m["status"] == status_filter]
if divisao_filter != "Todas":
    membros_filtrados = [m for m in membros_filtrados if m["divisao"] == divisao_filter]

# ========== TÍTULO E ABAS ==========
st.title("👑• 𝐇𝐚𝐤𝐮𝐫𝐲𝐮̄ (白竜) •👑")
st.caption("Dashboard de gestão da gang")
tabs = st.tabs(["Visão Geral", "Membros", "Treinos", "Divisões", "Parcerias"])

# ========== ABA VISÃO GERAL ==========
with tabs[0]:
    st.header("📊 Visão Geral")
    col1, col2, col3 = st.columns(3)
    col1.metric("Membros", len(membros))
    col2.metric("Treinos Cadastrados", len(treinos))
    col3.metric("Divisões", len(divisoes) - 1)  # desconta "Todas"
    st.divider()
    st.subheader("Próximos Treinos")
    futuros = [t for t in treinos if t["data_treino"] >= datetime.date.today()]
    if futuros:
        for t in futuros[:5]:
            st.markdown(f"**{t['titulo']}** — {t['data_treino']} às {t['horario']} ({t['tipo']})")
    else:
        st.info("Nenhum treino futuro.")

# ========== ABA MEMBROS ==========
with tabs[1]:
    st.header("👥 Membros")
    st.subheader(f"Total exibido: {len(membros_filtrados)}")
    if not membros_filtrados:
        st.info("Nenhum membro encontrado com os filtros.")
    else:
        cols = st.columns(3)
        for idx, m in enumerate(membros_filtrados):
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

# ========== ABA TREINOS ==========
with tabs[2]:
    st.header("🗓️ Mural de Treinos")

    with st.expander("➕ Criar Novo Treino", expanded=False):
        with st.form("novo_treino", clear_on_submit=True):
            titulo = st.text_input("Título do treino")
            descricao = st.text_area("Descrição")
            data_treino = st.date_input("Data")
            horario = st.time_input("Horário")
            tipo = st.selectbox("Tipo", ["Interno", "Amistoso", "Obrigatório", "Extra"])
            local = st.text_input("Local (ex: Arena 1, Roblox)")
            divisao = st.text_input("Divisão responsável (opcional)")
        
            submitted = st.form_submit_button("Criar Treino")
            if submitted:
                async def inserir_treino():
                    conn = await get_db()
                    try:
                        await conn.execute(
                            """
                            INSERT INTO treinos (titulo, descricao, data_treino, horario, tipo, local, divisao_responsavel, criado_por)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        """,
                        titulo, descricao, data_treino, horario, tipo, local, divisao, st.session_state.user["id"]
                        )
                    finally:
                        await conn.close()
                asyncio.run(inserir_treino())
                st.success(f"✅ Treino **{titulo}** criado com sucesso!")
                st.rerun()

    if not treinos:
        st.info("Nenhum treino cadastrado.")
    else:
        for t in treinos:
            with st.container():
                st.subheader(f"📅 {t['titulo']}")
                col1, col2, col3 = st.columns(3)
                col1.caption(f"Data: {t['data_treino']} às {t['horario']}")
                col2.caption(f"Tipo: {t['tipo']}")
                col3.caption(f"Status: {t['status']}")
                st.caption(f"Inscritos: {t['inscritos']}")

                with st.expander("📝 Inscrição de presença", expanded=False):
                    nomes_membros = {m["discord_username"]: m["discord_id"] for m in membros_ativos}
                    membro_selecionado = st.selectbox("Selecione o membro", list(nomes_membros.keys()), key=f"membro_{t['id_treino']}")
                    inscricao = st.radio("Confirmação", ["Confirmado", "Recusado", "Pendente"], key=f"inscricao_{t['id_treino']}")
                    if st.button("Registrar inscrição", key=f"btn_inscricao_{t['id_treino']}"):
                        async def inserir_inscricao():
                            conn = await get_db()
                            try:
                                await conn.execute(
                                    """
                                    INSERT INTO presencas_treino (treino_id, membro_id, inscricao)
                                    VALUES ($1, $2, $3)
                                    ON CONFLICT (treino_id, membro_id)
                                    DO UPDATE SET inscricao = EXCLUDED.inscricao
                                    """,
                                    t['id_treino'], nomes_membros[membro_selecionado], inscricao
                                )
                            finally:
                                await conn.close()
                        asyncio.run(inserir_inscricao())
                        st.success("Inscrição registrada!")
                        st.rerun()

                with st.expander("✅ Marcar presença", expanded=False):
                    async def get_inscritos(treino_id):
                        conn = await get_db()
                        try:
                            return await conn.fetch("""
                                SELECT p.membro_id, m.discord_username, p.inscricao, p.presenca
                                FROM presencas_treino p
                                JOIN membros m ON p.membro_id = m.discord_id
                                WHERE p.treino_id = $1
                            """, treino_id)
                        finally:
                            await conn.close()
                    presencas = asyncio.run(get_inscritos(t['id_treino']))
                    if not presencas:
                        st.caption("Nenhum inscrito ainda.")
                    else:
                        for p in presencas:
                            col1, col2, col3, col4 = st.columns([3,2,2,2])
                            col1.write(p["discord_username"])
                            col2.write(f"Inscrição: {p['inscricao']}")
                            nova_presenca = col3.selectbox(
                                "Presença",
                                ["Pendente", "Presente", "Ausente", "Justificado"],
                                index=["Pendente", "Presente", "Ausente", "Justificado"].index(p["presenca"]),
                                key=f"presenca_{t['id_treino']}_{p['membro_id']}"
                            )
                            if col4.button("Salvar", key=f"salvar_presenca_{t['id_treino']}_{p['membro_id']}"):
                                async def atualizar_presenca():
                                    conn = await get_db()
                                    try:
                                        await conn.execute(
                                            "UPDATE presencas_treino SET presenca = $1 WHERE treino_id = $2 AND membro_id = $3",
                                            nova_presenca, t['id_treino'], p['membro_id']
                                        )
                                    finally:
                                        await conn.close()
                                asyncio.run(atualizar_presenca())
                                st.success("Presença atualizada!")
                                st.rerun()
                st.divider()

# ========== ABA DIVISÕES (placeholder) ==========
with tabs[3]:
    st.header("🔰 Divisões")
    st.info("Em breve: gerenciamento de divisões, líderes e membros.")

# ========== ABA PARCERIAS (placeholder) ==========
with tabs[4]:
    st.header("🌐 Parcerias")
    st.info("Em breve: lista de parcerias, status e links.")