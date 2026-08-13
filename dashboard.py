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
    /* ========== FUNDO GERAL ========== */
    .stApp {
        background: linear-gradient(180deg, #fdfdf7 0%, #f5f0e8 100%);
        color: #2a2a2a;
    }

    /* ========== TÍTULO PRINCIPAL ========== */
    h1 {
        color: #b8860b !important;
        font-family: 'Georgia', 'Noto Serif JP', serif;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.15);
        letter-spacing: 3px;
        font-size: 2.5em !important;
        text-align: center;
        padding: 10px 0;
    }

    h1::before {
        content: "🐉 ";
        font-size: 1.3em;
    }

    h1::after {
        content: " 🐉";
        font-size: 1.3em;
    }

    /* ========== SUBTÍTULOS ========== */
    h2, h3 {
        color: #8b6508 !important;
        font-family: 'Georgia', serif;
        letter-spacing: 1px;
    }

    /* ========== LINHA DIVISÓRIA DOURADA ========== */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #d4af37, transparent);
        margin: 20px 0;
    }

    /* ========== SIDEBAR ========== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ffffff 0%, #faf5e8 100%);
        border-right: 3px solid #d4af37;
    }

    [data-testid="stSidebar"] img {
        border: 2px solid #d4af37;
        box-shadow: 0 2px 8px rgba(212, 175, 55, 0.3);
    }

    /* ========== BOTÕES DA SIDEBAR ========== */
    [data-testid="stSidebar"] .stButton>button {
        background-color: #fdfdf7;
        color: #8b6508;
        border: 1px solid #d4af37;
        border-radius: 10px;
        padding: 10px;
        font-weight: bold;
        transition: all 0.3s;
        margin-bottom: 6px;
        width: 100%;
    }

    [data-testid="stSidebar"] .stButton>button:hover {
        background-color: #d4af37;
        color: #ffffff;
        border-color: #8b6508;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(212, 175, 55, 0.4);
    }

    /* ========== CARTÕES E CONTAINERS ========== */
    .stContainer, .stExpander {
        background-color: #ffffff;
        border: 2px solid #d4af37;
        border-radius: 15px;
        padding: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-bottom: 10px;
        transition: box-shadow 0.3s;
    }

    .stContainer:hover {
        box-shadow: 0 6px 16px rgba(212, 175, 55, 0.2);
    }

    /* ========== EXPANDERS ========== */
    .stExpander {
        border: 1px solid #d4af37;
    }

    /* ========== BOTÕES GERAIS ========== */
    .stButton>button {
        background-color: #ffffff;
        color: #8b6508;
        border: 1px solid #d4af37;
        border-radius: 10px;
        font-weight: bold;
        padding: 8px 12px;
        transition: all 0.3s;
    }

    .stButton>button:hover {
        background-color: #d4af37;
        color: #ffffff;
        box-shadow: 0 2px 8px rgba(212, 175, 55, 0.4);
    }

    /* ========== MÉTRICAS ========== */
    .stMetric {
        background-color: #ffffff;
        border: 2px solid #d4af37;
        border-radius: 12px;
        padding: 12px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }

    /* ========== AVATARES REDONDOS ========== */
    img {
        border-radius: 50%;
        border: 2px solid #d4af37;
    }

    /* ========== LOGO DA DIVISÃO ========== */
    .divisao-logo {
        width: 150px;
        height: 150px;
        border-radius: 50%;
        border: 3px solid #d4af37;
        object-fit: cover;
        box-shadow: 0 4px 12px rgba(212, 175, 55, 0.3);
    }

    /* ========== FUNDO COM PADRÃO SUTIL ========== */
    .stApp::before {
        content: "";
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background-image: url('https://www.transparenttextures.com/patterns/japanese-architectural.png');
        opacity: 0.04;
        pointer-events: none;
    }

    /* ========== CAPTIONS ========== */
    .stCaption {
        color: #6b5b3e;
        font-size: 0.9em;
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

# ========== FUNÇÃO OTIMIZADA: CARREGA TUDO EM LOTE ==========
@st.cache_data(ttl=300)
def carregar_dados_completos():
    async def _get():
        conn = await get_db()
        try:
            membros = await conn.fetch("""
                SELECT m.discord_id, m.discord_username, m.nome_roblox, m.nome_rp, m.genero, m.altura_jogo,
                       m.estilo_luta_principal, m.cargo, d.nome_divisao as divisao, m.status, m.data_entrada, m.avatar_hash
                FROM membros m
                LEFT JOIN divisoes d ON m.divisao_id = d.id
                ORDER BY m.data_entrada DESC
            """)

            warns = await conn.fetch("""
                SELECT membro_id, COUNT(*) as total_warns
                FROM punicoes
                WHERE tipo = 'Warn'
                GROUP BY membro_id
            """)
            warns_dict = {w["membro_id"]: w["total_warns"] for w in warns}

            stats = await conn.fetch("""
                SELECT 
                    p.membro_id,
                    COUNT(*) FILTER (WHERE t.tipo = 'Interno' AND p.presenca = 'Presente') as internos,
                    COUNT(*) FILTER (WHERE t.tipo = 'Amistoso' AND p.presenca = 'Presente') as amistosos
                FROM presencas_treino p
                JOIN treinos t ON p.treino_id = t.id_treino
                WHERE p.presenca = 'Presente'
                GROUP BY p.membro_id
            """)
            stats_dict = {s["membro_id"]: {"internos": s["internos"], "amistosos": s["amistosos"]} for s in stats}

            try:
                guerras = await conn.fetch("""
                    SELECT membro_id, COUNT(*) as total_guerras
                    FROM participacoes_guerra
                    GROUP BY membro_id
                """)
                guerras_dict = {g["membro_id"]: g["total_guerras"] for g in guerras}
            except:
                guerras_dict = {}

            resultado = []
            for m in membros:
                m_dict = dict(m)
                m_dict["warns"] = warns_dict.get(m["discord_id"], 0)
                m_dict["stats"] = {
                    "internos": stats_dict.get(m["discord_id"], {}).get("internos", 0),
                    "amistosos": stats_dict.get(m["discord_id"], {}).get("amistosos", 0),
                    "guerras": guerras_dict.get(m["discord_id"], 0)
                }
                resultado.append(m_dict)

            return resultado
        finally:
            await conn.close()
    return asyncio.run(_get())

@st.cache_data(ttl=300)
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

@st.cache_data(ttl=300)
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
    membros = carregar_dados_completos()
    treinos = carregar_treinos()
    membros_ativos = carregar_membros_ativos()
except Exception as e:
    st.error(f"⚠️ Sem conexão com o banco de dados: {e}")
    membros = []
    treinos = []
    membros_ativos = []

# ========== NAVEGAÇÃO POR BOTÕES ==========
st.sidebar.markdown("### 📑 Navegação")

aba = None
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("📊 Visão Geral", use_container_width=True, key="nav_geral"):
        aba = "Visão Geral"
    if st.button("👥 Membros", use_container_width=True, key="nav_membros"):
        aba = "Membros"
    if st.button("🗓️ Treinos", use_container_width=True, key="nav_treinos"):
        aba = "Treinos"
with col2:
    if st.button("🔰 Divisões", use_container_width=True, key="nav_divisoes"):
        aba = "Divisões"
    if st.button("🌐 Parcerias", use_container_width=True, key="nav_parcerias"):
        aba = "Parcerias"

# Manter a aba selecionada
if aba is None:
    aba = st.session_state.get("aba_atual", "Visão Geral")
else:
    st.session_state.aba_atual = aba

# Filtros de membros
if aba == "Membros":
    st.sidebar.markdown("---")
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
else:
    membros_filtrados = membros

# Botão de atualização
st.sidebar.markdown("---")
if st.sidebar.button("🔄 Atualizar dados agora"):
    st.cache_data.clear()
    st.rerun()

# ========== TÍTULO ==========
st.title("👑• 𝐇𝐚𝐤𝐮𝐫𝐲𝐮̄ (白竜) •👑")
st.caption("Dashboard de gestão da gang")

# ========== ABA VISÃO GERAL ==========
if aba == "Visão Geral":
    st.header("📊 Visão Geral")
    col1, col2, col3 = st.columns(3)
    membros_ativos_count = len([m for m in membros if m["status"] == "Ativo"])
    col1.metric("Membros Ativos", membros_ativos_count)
    col2.metric("Treinos Cadastrados", len(treinos))
    col3.metric("Divisões", len({m["divisao"] for m in membros if m["divisao"]}))
    st.divider()
    st.subheader("Próximos Treinos")
    futuros = [t for t in treinos if t["data_treino"] >= datetime.date.today()]
    if futuros:
        for t in futuros[:5]:
            st.markdown(f"**{t['titulo']}** — {t['data_treino']} às {t['horario']} ({t['tipo']})")
    else:
        st.info("Nenhum treino futuro.")

# ========== ABA MEMBROS ==========
elif aba == "Membros":
    st.header("👥 Membros")
    st.subheader(f"Total exibido: {len(membros_filtrados)}")

    pode_gerenciar_membros = tem_cargo("Lider") or tem_cargo("Vice-Lider") or eh_dono()

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

                    warns = m["warns"]
                    if warns > 0:
                        st.markdown(f"⚠️ **Warns:** {warns}")
                    else:
                        st.caption("⚠️ Warns: 0")

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
                        st.markdown(f"**Warns:** {m['warns']}")

                    stats = m["stats"]
                    st.divider()
                    st.markdown("### 📈 Estatísticas")
                    col_st1, col_st2, col_st3 = st.columns(3)
                    col_st1.metric("Treinos Internos", stats["internos"])
                    col_st2.metric("Treinos Amistosos", stats["amistosos"])
                    col_st3.metric("Guerras", stats["guerras"])

                    if pode_gerenciar_membros:
                        st.divider()
                        st.markdown("### 🔧 Ações")
                        col_acao1, col_acao2, col_acao3, col_acao4 = st.columns(4)

                        with col_acao1:
                            if st.button("⚠️ Advertir", key=f"advertir_{m['discord_id']}"):
                                st.session_state.advertir_membro = m["discord_id"]
                                st.rerun()

                        with col_acao2:
                            if st.button("⚜️ Trocar cargo", key=f"trocar_cargo_btn_{m['discord_id']}"):
                                st.session_state.trocar_cargo_membro = m["discord_id"]
                                st.rerun()

                        with col_acao3:
                            if st.button("📜 Histórico", key=f"hist_warns_{m['discord_id']}"):
                                st.session_state.historico_membro = m["discord_id"]
                                st.rerun()

                        with col_acao4:
                            if st.button("🗑️ Remover", key=f"remover_btn_{m['discord_id']}"):
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
elif aba == "Treinos":
    st.header("🗓️ Mural de Treinos")

    pode_gerenciar_presenca = tem_cargo("Lider") or tem_cargo("Vice-Lider") or tem_cargo("Líder de Divisão") or eh_dono()

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
                col_titulo, col_delete = st.columns([8, 1])
                with col_titulo:
                    st.subheader(f"📅 {t['titulo']}")
                with col_delete:
                    if pode_gerenciar_presenca:
                        if st.button("❌", key=f"del_{t['id_treino']}", help="Deletar treino"):
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

                col1, col2, col3 = st.columns(3)
                col1.caption(f"Data: {t['data_treino']} às {t['horario']}")
                col2.caption(f"Tipo: {t['tipo']}")
                col3.caption(f"Status: {t['status']}")
                st.caption(f"Inscritos: {t['inscritos']}")

                with st.expander("📝 Inscrição de presença", expanded=False):
                    membro_id = st.session_state.user["id"]

                    async def verificar_inscricao(treino_id, membro_id):
                        conn = await get_db()
                        try:
                            row = await conn.fetchrow(
                                "SELECT inscricao FROM presencas_treino WHERE treino_id = $1 AND membro_id = $2",
                                treino_id, membro_id
                            )
                            return row["inscricao"] if row else None
                        finally:
                            await conn.close()

                    status_inscricao = asyncio.run(verificar_inscricao(t['id_treino'], membro_id))

                    if status_inscricao is None:
                        if st.button("✅ Inscrever-se", key=f"inscrever_{t['id_treino']}"):
                            async def inserir_inscricao():
                                conn = await get_db()
                                try:
                                    await conn.execute(
                                        """
                                        INSERT INTO presencas_treino (treino_id, membro_id, inscricao)
                                        VALUES ($1, $2, 'Confirmado')
                                        ON CONFLICT (treino_id, membro_id)
                                        DO UPDATE SET inscricao = 'Confirmado'
                                        """,
                                        t['id_treino'], membro_id
                                    )
                                finally:
                                    await conn.close()
                            asyncio.run(inserir_inscricao())
                            st.success("Inscrição confirmada!")
                            st.cache_data.clear()
                            st.rerun()
                    else:
                        st.markdown(f"**Status:** {status_inscricao}")
                        if st.button("❌ Ausentar-me", key=f"ausentar_{t['id_treino']}"):
                            async def ausentar():
                                conn = await get_db()
                                try:
                                    await conn.execute(
                                        "DELETE FROM presencas_treino WHERE treino_id = $1 AND membro_id = $2",
                                        t['id_treino'], membro_id
                                    )
                                finally:
                                    await conn.close()
                            asyncio.run(ausentar())
                            st.success("Você foi retirado da lista de inscritos.")
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

# ========== ABA DIVISÕES ==========
elif aba == "Divisões":
    st.header("🔰 Divisões")

    pode_gerenciar_divisoes = tem_cargo("Lider") or tem_cargo("Vice-Lider") or eh_dono()

    # ========== CRIAR NOVA DIVISÃO ==========
    if pode_gerenciar_divisoes:
        with st.expander("➕ Criar Nova Divisão", expanded=False):
            with st.form("nova_divisao", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    nome_divisao = st.text_input("Nome da Divisão")
                    discord_role_id = st.text_input("ID do Cargo no Discord")
                with col2:
                    logo_url = st.text_input("URL da Logo (opcional)")
                    funcao = st.text_input("Função principal (opcional)")

                submitted = st.form_submit_button("Criar Divisão")
                if submitted and nome_divisao:
                    async def criar_divisao():
                        conn = await get_db()
                        try:
                            await conn.execute(
                                """
                                INSERT INTO divisoes (nome_divisao, logo_url, discord_role_id, funcao_principal)
                                VALUES ($1, $2, $3, $4)
                                """,
                                nome_divisao, logo_url or None, discord_role_id or None, funcao or None
                            )
                        finally:
                            await conn.close()
                    asyncio.run(criar_divisao())
                    st.success(f"✅ Divisão **{nome_divisao}** criada!")
                    st.cache_data.clear()
                    st.rerun()

    # ========== LISTAR DIVISÕES ==========
    async def carregar_divisoes():
        conn = await get_db()
        try:
            rows = await conn.fetch("""
                SELECT d.*, 
                       l.nome_rp as lider_nome, l.discord_username as lider_discord,
                       v.nome_rp as vice_nome, v.discord_username as vice_discord
                FROM divisoes d
                LEFT JOIN membros l ON d.lider_id = l.discord_id
                LEFT JOIN membros v ON d.vice_lider_id = v.discord_id
                ORDER BY d.nome_divisao
            """)
            return [dict(row) for row in rows]
        finally:
            await conn.close()

    divisoes = asyncio.run(carregar_divisoes())

    if not divisoes:
        st.info("Nenhuma divisão criada ainda.")
    else:
        for d in divisoes:
            with st.container():
                # Cabeçalho da divisão
                col_logo, col_info, col_acoes = st.columns([1, 3, 1])
                with col_logo:
                    if d["logo_url"]:
                        st.markdown(f'<img src="{d["logo_url"]}" class="divisao-logo">', unsafe_allow_html=True)
                    else:
                        st.markdown('<div style="width:150px;height:150px;border:3px solid #d4af37;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:60px;">🔰</div>', unsafe_allow_html=True)
                with col_info:
                    st.subheader(d["nome_divisao"])
                    st.caption(f"ID do Cargo: {d['discord_role_id'] or 'N/A'}")
                    if d["funcao_principal"]:
                        st.caption(f"Função: {d['funcao_principal']}")
                with col_acoes:
                    if pode_gerenciar_divisoes:
                        if st.button("🗑️", key=f"del_div_{d['id']}", help="Deletar divisão"):
                            async def deletar_divisao():
                                conn = await get_db()
                                try:
                                    await conn.execute("DELETE FROM divisoes WHERE id = $1", d['id'])
                                finally:
                                    await conn.close()
                            asyncio.run(deletar_divisao())
                            st.success("Divisão deletada!")
                            st.cache_data.clear()
                            st.rerun()

                # Líder e Vice-Líder
                col_lider, col_vice = st.columns(2)
                with col_lider:
                    st.markdown(f"**👑 Líder:** {d['lider_nome'] or 'Não definido'}")
                    if d["lider_discord"]:
                        st.caption(f"Discord: {d['lider_discord']}")
                with col_vice:
                    st.markdown(f"**⚜️ Vice-Líder:** {d['vice_nome'] or 'Não definido'}")
                    if d["vice_discord"]:
                        st.caption(f"Discord: {d['vice_discord']}")

                # Membros da divisão
                async def carregar_membros_divisao(divisao_id):
                    conn = await get_db()
                    try:
                        rows = await conn.fetch("""
                            SELECT discord_id, discord_username, nome_rp, avatar_hash
                            FROM membros
                            WHERE divisao_id = $1
                            ORDER BY nome_rp
                        """, divisao_id)
                        return [dict(row) for row in rows]
                    finally:
                        await conn.close()

                membros_divisao = asyncio.run(carregar_membros_divisao(d["id"]))
                st.caption(f"**Membros:** {len(membros_divisao)}")

                if membros_divisao:
                    for m in membros_divisao:
                        col_avatar, col_nome = st.columns([1, 5])
                        with col_avatar:
                            avatar_url = discord_avatar_url(m["discord_id"], m["avatar_hash"])
                            st.image(avatar_url, width=30)
                        with col_nome:
                            nome = m["nome_rp"] or m["discord_username"]
                            st.markdown(f"{nome}")

                # Gerenciar divisão (apenas liderança)
                if pode_gerenciar_divisoes:
                    with st.expander(f"⚙️ Gerenciar {d['nome_divisao']}", expanded=False):
                        nomes_membros = {m["nome_rp"] or m["discord_username"]: m["discord_id"] for m in membros}
                        
                        col_lider_sel, col_vice_sel = st.columns(2)
                        with col_lider_sel:
                            novo_lider = st.selectbox(
                                "Líder",
                                ["Nenhum"] + list(nomes_membros.keys()),
                                key=f"lider_{d['id']}"
                            )
                        with col_vice_sel:
                            novo_vice = st.selectbox(
                                "Vice-Líder",
                                ["Nenhum"] + list(nomes_membros.keys()),
                                key=f"vice_{d['id']}"
                            )

                        novos_membros = st.multiselect(
                            "Adicionar membros",
                            list(nomes_membros.keys()),
                            key=f"add_membros_{d['id']}"
                        )

                        if st.button("💾 Salvar alterações", key=f"salvar_div_{d['id']}"):
                            async def atualizar_divisao():
                                conn = await get_db()
                                try:
                                    if novo_lider != "Nenhum":
                                        await conn.execute(
                                            "UPDATE divisoes SET lider_id = $1 WHERE id = $2",
                                            nomes_membros[novo_lider], d['id']
                                        )
                                    else:
                                        await conn.execute(
                                            "UPDATE divisoes SET lider_id = NULL WHERE id = $1",
                                            d['id']
                                        )
                                    
                                    if novo_vice != "Nenhum":
                                        await conn.execute(
                                            "UPDATE divisoes SET vice_lider_id = $1 WHERE id = $2",
                                            nomes_membros[novo_vice], d['id']
                                        )
                                    else:
                                        await conn.execute(
                                            "UPDATE divisoes SET vice_lider_id = NULL WHERE id = $1",
                                            d['id']
                                        )
                                    
                                    for nome in novos_membros:
                                        await conn.execute(
                                            "UPDATE membros SET divisao_id = $1 WHERE discord_id = $2",
                                            d['id'], nomes_membros[nome]
                                        )
                                finally:
                                    await conn.close()
                            asyncio.run(atualizar_divisao())
                            st.success("Divisão atualizada!")
                            st.cache_data.clear()
                            st.rerun()

                st.divider()

# ========== ABA PARCERIAS ==========
elif aba == "Parcerias":
    st.header("🌐 Parcerias")
    st.info("Em breve: lista de parcerias, status e links.")