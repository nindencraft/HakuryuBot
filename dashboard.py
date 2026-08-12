import streamlit as st
import datetime
import asyncpg
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from database import get_db
from auth import autenticar, esta_logado, tem_cargo, eh_dono, get_login_url

st.set_page_config(
    page_title="👑 Hakuryū Dashboard",
    page_icon="🐉",
    layout="wide"
)

st.markdown("""
<style>
    /* Fundo geral branco suave */
    .stApp {
        background-color: #fdfdf7;
        color: #2a2a2a;
    }

    /* Título principal com dourado e serifa japonesa */
    h1 {
        color: #b8860b !important;
        font-family: 'Georgia', 'Noto Serif JP', serif;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        letter-spacing: 2px;
    }

    /* Subtítulos */
    h2, h3 {
        color: #8b6508 !important;
        font-family: 'Georgia', serif;
    }

    /* Sidebar branca com borda dourada */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 2px solid #d4af37;
    }

    /* Cartões e containers com borda dourada suave */
    .stContainer, .stExpander {
        background-color: #ffffff;
        border: 1px solid #d4af37;
        border-radius: 12px;
        padding: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }

    /* Botões */
    .stButton>button {
        background-color: #ffffff;
        color: #8b6508;
        border: 1px solid #d4af37;
        border-radius: 8px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #d4af37;
        color: #ffffff;
    }

    /* Métricas */
    .stMetric {
        background-color: #ffffff;
        border: 1px solid #d4af37;
        border-radius: 8px;
        padding: 8px;
    }

    /* Avatares redondos */
    img {
        border-radius: 50%;
    }

    /* Fundo com padrão sutil de nuvens (opcional) */
    .stApp::before {
        content: "";
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background-image: url('https://www.transparenttextures.com/patterns/japanese-architectural.png');
        opacity: 0.05;
        pointer-events: none;
    }

    /* Pequeno dragão decorativo no título */
    h1::before {
        content: "🐉 ";
        font-size: 1.2em;
    }
</style>
""", unsafe_allow_html=True)

# ========== AUTENTICAÇÃO PERSISTENTE ==========
if "user" not in st.session_state:
    autenticar()

if not esta_logado():
    st.title("👑 Hakuryū Dashboard")
    st.markdown("Faça login com Discord para acessar o painel.")
    st.link_button("🔐 Login com Discord", get_login_url())
    st.stop()

# Mostrar usuário logado
st.sidebar.image(st.session_state.user["avatar"], width=80)
nome_exibicao = st.session_state.user.get("nome_rp") or st.session_state.user["nome"]
st.sidebar.markdown(f"**{nome_exibicao}**")
st.sidebar.caption(f"Discord: {st.session_state.user['nome']}")

# Controle de acesso
cargos_permitidos = ["Lider", "Vice-Lider", "Líder de Divisão", "Staff", "Recrutador", "Membro", "Em Analise"]
if not eh_dono() and not any(tem_cargo(c) for c in cargos_permitidos):
    st.error("Você não possui um cargo autorizado para acessar este dashboard.")
    st.stop()

def discord_avatar_url(discord_id, avatar_hash, size=128):
    if avatar_hash:
        return f"https://cdn.discordapp.com/avatars/{discord_id}/{avatar_hash}.png?size={size}"
    return "https://cdn.discordapp.com/embed/avatars/0.png"

# ========== FUNÇÃO PARA ESTATÍSTICAS ==========
async def get_estatisticas_membro(discord_id):
    conn = await get_db()
    try:
        internos = await conn.fetchval("""
            SELECT COUNT(*)
            FROM presencas_treino p
            JOIN treinos t ON p.treino_id = t.id_treino
            WHERE p.membro_id = $1 AND p.presenca = 'Presente' AND t.tipo = 'Interno'
        """, discord_id)

        amistosos = await conn.fetchval("""
            SELECT COUNT(*)
            FROM presencas_treino p
            JOIN treinos t ON p.treino_id = t.id_treino
            WHERE p.membro_id = $1 AND p.presenca = 'Presente' AND t.tipo = 'Amistoso'
        """, discord_id)

        try:
            guerras = await conn.fetchval("""
                SELECT COUNT(*)
                FROM participacoes_guerra
                WHERE membro_id = $1
            """, discord_id)
        except:
            guerras = 0

        return {"internos": internos, "amistosos": amistosos, "guerras": guerras}
    finally:
        await conn.close()

# ========== FUNÇÕES COM CACHE ==========
@st.cache_data(ttl=60)
def carregar_membros():
    async def _get():
        conn = await get_db()
        try:
            rows = await conn.fetch("""
                SELECT discord_id, discord_username, nome_roblox, nome_rp, genero, altura_jogo,
                       estilo_luta_principal, cargo, divisao, status, data_entrada, avatar_hash
                FROM membros
                ORDER BY data_entrada DESC
            """)
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    return asyncio.run(_get())

@st.cache_data(ttl=60)
def carregar_treinos():
    async def _get():
        conn = await get_db()
        try:
            rows = await conn.fetch("""
                SELECT t.*, 
                       (SELECT COUNT(*) FROM presencas_treino p WHERE p.treino_id = t.id_treino AND p.inscricao = 'Confirmado') as inscritos
                FROM treinos t
                ORDER BY t.data_treino DESC
            """)
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    return asyncio.run(_get())

@st.cache_data(ttl=60)
def carregar_membros_ativos():
    async def _get():
        conn = await get_db()
        try:
            rows = await conn.fetch("SELECT discord_id, discord_username, nome_rp FROM membros WHERE status = 'Ativo' ORDER BY nome_rp")
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    return asyncio.run(_get())

# ========== CARREGAR DADOS ==========
try:
    membros = carregar_membros()
    treinos = carregar_treinos()
    membros_ativos = carregar_membros_ativos()
except Exception as e:
    st.error(f"⚠️ Sem conexão com o banco de dados: {e}")
    st.info("Usando dados vazios para visualização do layout.")
    membros = []
    treinos = []
    membros_ativos = []

# ========== SIDEBAR ==========
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

# Botão de atualização
st.sidebar.markdown("---")
if st.sidebar.button("🔄 Atualizar dados agora"):
    st.cache_data.clear()
    st.rerun()

# ========== TÍTULO E ABAS ==========
st.title("👑• 𝐇𝐚𝐤𝐮𝐫𝐲𝐮̄ (白竜) •👑")
st.caption("Dashboard de gestão da gang")
tabs = st.tabs(["Visão Geral", "Membros", "Treinos", "Divisões", "Parcerias"])

# ========== ABA VISÃO GERAL ==========
with tabs[0]:
    st.header("📊 Visão Geral")
    col1, col2, col3 = st.columns(3)
    membros_ativos_count = len([m for m in membros if m["status"] == "Ativo"])
    col1.metric("Membros Ativos", membros_ativos_count)
    col2.metric("Treinos Cadastrados", len(treinos))
    col3.metric("Divisões", len(divisoes) - 1)
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

    pode_gerenciar_membros = tem_cargo("Lider") or tem_cargo("Vice-Lider")

    if not membros_filtrados:
        st.info("Nenhum membro encontrado com os filtros.")
    else:
        for m in membros_filtrados:
            with st.container():
                col_avatar, col_info, col_cargo = st.columns([1, 4, 2])

                with col_avatar:
                    avatar_url = discord_avatar_url(m["discord_id"], m["avatar_hash"])
                    st.image(avatar_url, width=70)

                with col_info:
                    nome_principal = m["nome_rp"] or m["discord_username"]
                    st.markdown(f"### {nome_principal}")
                    st.caption(f"Discord: {m['discord_username']}")
                    st.caption(f"Roblox: {m['nome_roblox']}")

                with col_cargo:
                    st.markdown(f"**⚜️ Cargo:**")
                    st.markdown(f"**{m['cargo']}**")
                    st.caption(f"Divisão: {m['divisao'] or 'Sem divisão'}")

                with st.expander(f"📋 Detalhes de {nome_principal}", expanded=False):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Discord:** {m['discord_username']}")
                        st.markdown(f"**Roblox:** {m['nome_roblox']}")
                        if m["nome_rp"]:
                            st.markdown(f"**Nome RP:** {m['nome_rp']}")
                        st.markdown(f"**Gênero:** {m['genero']}")
                        if m["altura_jogo"]:
                            st.markdown(f"**Altura:** {m['altura_jogo']}m")
                        if m["estilo_luta_principal"]:
                            st.markdown(f"**Estilo de luta:** {m['estilo_luta_principal']}")
                    with col2:
                        st.markdown(f"**Cargo:** {m['cargo']}")
                        st.markdown(f"**Divisão:** {m['divisao'] or 'Sem divisão'}")
                        st.markdown(f"**Status:** {m['status']}")
                        st.markdown(f"**Entrada:** {m['data_entrada']}")

                    # Estatísticas de participação
                    stats = asyncio.run(get_estatisticas_membro(m["discord_id"]))
                    st.divider()
                    st.markdown("### 📈 Estatísticas")
                    col_st1, col_st2, col_st3 = st.columns(3)
                    col_st1.metric("Treinos Internos", stats["internos"])
                    col_st2.metric("Treinos Amistosos", stats["amistosos"])
                    col_st3.metric("Guerras", stats["guerras"])

                    if pode_gerenciar_membros:
                        st.divider()
                        st.markdown("### 🔧 Gerenciar")
                        col_cargo_sel, col_salvar, col_remover = st.columns([3, 2, 2])
                        with col_cargo_sel:
                            novo_cargo = st.selectbox(
                                "Alterar cargo",
                                ["Recruta", "Membro", "Líder de Divisão", "Staff", "Recrutador", "Vice-Lider", "Lider"],
                                index=["Recruta", "Membro", "Líder de Divisão", "Staff", "Recrutador", "Vice-Lider", "Lider"].index(m["cargo"]) if m["cargo"] in ["Recruta", "Membro", "Líder de Divisão", "Staff", "Recrutador", "Vice-Lider", "Lider"] else 0,
                                key=f"cargo_exp_{m['discord_id']}"
                            )
                        with col_salvar:
                            if st.button("💾 Salvar cargo", key=f"salvar_cargo_exp_{m['discord_id']}"):
                                async def atualizar_cargo():
                                    conn = await get_db()
                                    try:
                                        await conn.execute(
                                            "UPDATE membros SET cargo = $1 WHERE discord_id = $2",
                                            novo_cargo, m["discord_id"]
                                        )
                                    finally:
                                        await conn.close()
                                asyncio.run(atualizar_cargo())
                                st.success(f"Cargo de {nome_principal} atualizado para {novo_cargo}!")
                                st.cache_data.clear()
                                st.rerun()
                        with col_remover:
                            if st.button("🗑️ Remover", key=f"remover_exp_{m['discord_id']}"):
                                async def remover_membro():
                                    conn = await get_db()
                                    try:
                                        await conn.execute("DELETE FROM membros WHERE discord_id = $1", m["discord_id"])
                                    finally:
                                        await conn.close()
                                asyncio.run(remover_membro())
                                st.success(f"{nome_principal} removido do registro.")
                                st.cache_data.clear()
                                st.rerun()

                st.divider()

# ========== ABA TREINOS ==========
with tabs[2]:
    st.header("🗓️ Mural de Treinos")

    pode_gerenciar_presenca = tem_cargo("Lider") or tem_cargo("Vice-Lider") or tem_cargo("Líder de Divisão")

    if pode_gerenciar_presenca:
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
                    st.cache_data.clear()
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

                # Botão de deletar em formulário separado
                if pode_gerenciar_presenca:
                    with st.form(f"form_deletar_{t['id_treino']}"):
                        delete_submitted = st.form_submit_button("🗑️ Deletar treino")
                        if delete_submitted:
                            async def deletar_treino():
                                conn = await get_db()
                                try:
                                    await conn.execute("DELETE FROM treinos WHERE id_treino = $1", t['id_treino'])
                                finally:
                                    await conn.close()
                            asyncio.run(deletar_treino())
                            st.success("Treino deletado!")
                            st.cache_data.clear()
                            st.rerun()

                with st.expander("📝 Inscrição de presença", expanded=False):
                    nomes_membros = {}
                    for m in membros_ativos:
                        nome_principal = m["nome_rp"] or m["discord_username"]
                        nomes_membros[nome_principal] = m["discord_id"]

                    if not pode_gerenciar_presenca:
                        nome_usuario = st.session_state.user.get("nome_rp") or st.session_state.user["nome"]
                        if nome_usuario in nomes_membros:
                            membro_selecionado = nome_usuario
                        else:
                            membro_selecionado = st.selectbox("Selecione o membro", list(nomes_membros.keys()), key=f"membro_{t['id_treino']}")
                    else:
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
                        st.cache_data.clear()
                        st.rerun()

                if pode_gerenciar_presenca:
                    with st.expander("✅ Marcar presença", expanded=False):
                        async def get_inscritos(treino_id):
                            conn = await get_db()
                            try:
                                rows = await conn.fetch("""
                                    SELECT p.membro_id, m.discord_username, m.nome_rp, m.avatar_hash, p.inscricao, p.presenca
                                    FROM presencas_treino p
                                    JOIN membros m ON p.membro_id = m.discord_id
                                    WHERE p.treino_id = $1
                                """, treino_id)
                                return [dict(row) for row in rows]
                            finally:
                                await conn.close()
                        presencas = asyncio.run(get_inscritos(t['id_treino']))
                        if not presencas:
                            st.caption("Nenhum inscrito ainda.")
                        else:
                            for p in presencas:
                                col1, col2, col3, col4 = st.columns([3,2,2,2])
                                avatar_url = discord_avatar_url(p["membro_id"], p["avatar_hash"])
                                col1.image(avatar_url, width=40)
                                nome_rp = p["nome_rp"] or p["discord_username"]
                                col1.markdown(f"**{nome_rp}**")
                                col1.caption(f"Discord: {p['discord_username']}")

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
                                    st.cache_data.clear()
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