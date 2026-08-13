import asyncio
import datetime

import streamlit as st
from dotenv import load_dotenv

from database import get_db
from auth import autenticar, esta_logado, tem_cargo, eh_dono, get_login_url

load_dotenv()

st.set_page_config(
    page_title="Hakuryū Dashboard",
    page_icon="龍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================
# TEMA VISUAL
# =========================
st.markdown("""
<style>
:root {
    --gold: #b89432;
    --gold-light: #d8bd68;
    --gold-dark: #80651d;
    --paper: #fffefa;
    --ivory: #f7f2e7;
    --ink: #292722;
}

.stApp {
    background:
        radial-gradient(circle at 15% 10%, rgba(216,189,104,.12), transparent 25%),
        radial-gradient(circle at 90% 80%, rgba(184,148,50,.10), transparent 30%),
        linear-gradient(135deg, var(--paper) 0%, var(--ivory) 100%);
    color: var(--ink);
}

/* Padrão asanoha japonês sutil, sem imagem externa */
.stApp::before {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    opacity: .035;
    background-image:
        linear-gradient(30deg, #80651d 12%, transparent 12.5%, transparent 87%, #80651d 87.5%, #80651d),
        linear-gradient(150deg, #80651d 12%, transparent 12.5%, transparent 87%, #80651d 87.5%, #80651d),
        linear-gradient(30deg, #80651d 12%, transparent 12.5%, transparent 87%, #80651d 87.5%, #80651d),
        linear-gradient(150deg, #80651d 12%, transparent 12.5%, transparent 87%, #80651d 87.5%, #80651d),
        linear-gradient(60deg, #80651d 25%, transparent 25.5%, transparent 75%, #80651d 75%);
    background-size: 42px 73px;
    background-position: 0 0, 0 0, 21px 37px, 21px 37px, 0 0;
}

.main .block-container { position: relative; z-index: 1; max-width: 1450px; padding-top: 2rem; }

h1 {
    color: var(--gold-dark) !important;
    font-family: Georgia, "Times New Roman", serif;
    font-size: 2.45rem !important;
    letter-spacing: 5px;
    text-align: center;
    text-shadow: 1px 2px 3px rgba(80,55,0,.18);
    border-bottom: 1px solid var(--gold-light);
    padding-bottom: 15px;
}
h1::before { content: "龍  "; color: var(--gold); font-size: .75em; }
h1::after { content: "  龍"; color: var(--gold); font-size: .75em; }
h2, h3 { color: var(--gold-dark) !important; font-family: Georgia, serif; letter-spacing: 1px; }
hr { border: 0; height: 1px; background: linear-gradient(90deg, transparent, var(--gold), var(--gold-light), var(--gold), transparent); margin: 24px 0; }

[data-testid="stSidebar"] {
    background: linear-gradient(rgba(255,255,255,.96), rgba(249,243,228,.97));
    border-right: 2px solid var(--gold);
}
[data-testid="stSidebar"]::before {
    content: "白竜";
    display: block;
    text-align: center;
    color: var(--gold-dark);
    font: 2.2rem Georgia, serif;
    letter-spacing: 8px;
    padding: 12px 0 20px;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(255,255,255,.88);
    border: 1px solid rgba(184,148,50,.55);
    border-radius: 14px;
    box-shadow: 0 5px 18px rgba(91,68,13,.08);
}
[data-testid="stMetric"] {
    background: linear-gradient(145deg, #fff, #faf5e8);
    border: 1px solid var(--gold-light);
    border-radius: 14px;
    padding: 15px;
    box-shadow: 0 3px 12px rgba(90,70,15,.08);
}
[data-testid="stMetricLabel"] { color: var(--gold-dark) !important; }
[data-testid="stMetricValue"] { color: #574513 !important; }

.stButton > button, .stLinkButton > a {
    background: linear-gradient(135deg, #fffefa, #f5ead0);
    color: var(--gold-dark);
    border: 1px solid var(--gold);
    border-radius: 9px;
    font-weight: 600;
    transition: all .2s ease;
}
.stButton > button:hover, .stLinkButton > a:hover {
    background: linear-gradient(135deg, var(--gold), #9d791f);
    color: #fff;
    box-shadow: 0 4px 12px rgba(184,148,50,.3);
}
[data-testid="stExpander"] { border: 1px solid rgba(184,148,50,.6); border-radius: 12px; background: rgba(255,255,255,.72); }
img { border-color: var(--gold) !important; }
.divisao-logo { width: 135px; height: 135px; border-radius: 50%; object-fit: cover; border: 3px solid var(--gold); padding: 4px; background: #fff; box-shadow: 0 5px 16px rgba(184,148,50,.25); }
</style>
""", unsafe_allow_html=True)

# =========================
# AUTENTICAÇÃO
# =========================
if "user" not in st.session_state:
    autenticar()

if not esta_logado():
    st.title("Hakuryū 白竜")
    st.markdown("Faça login com Discord para acessar o painel.")
    st.link_button("Entrar com Discord", get_login_url())
    st.stop()

st.sidebar.image(st.session_state.user["avatar"], width=80)
nome_exibicao = st.session_state.user.get("nome_rp") or st.session_state.user["nome"]
st.sidebar.markdown(f"**{nome_exibicao}**")
st.sidebar.caption(f"Discord: {st.session_state.user['nome']}")

cargos_permitidos = ["Lider", "Vice-Lider", "Líder de Divisão", "Staff", "Recrutador", "Membro", "Em Analise"]
if not eh_dono() and not any(tem_cargo(c) for c in cargos_permitidos):
    st.error("Você não possui um cargo autorizado para acessar este dashboard.")
    st.stop()


def discord_avatar_url(discord_id, avatar_hash, size=128):
    if avatar_hash:
        return f"https://cdn.discordapp.com/avatars/{discord_id}/{avatar_hash}.png?size={size}"
    return "https://cdn.discordapp.com/embed/avatars/0.png"


def executar(coroutine):
    """Executa uma operação async de forma centralizada."""
    return asyncio.run(coroutine)


# =========================
# CONSULTAS EM LOTE E CACHE
# =========================
@st.cache_data(ttl=300, show_spinner=False)
def carregar_dados_completos():
    async def _get():
        conn = await get_db()
        try:
            membros = await conn.fetch("""
                SELECT m.discord_id, m.discord_username, m.nome_roblox, m.nome_rp,
                       m.genero, m.altura_jogo, m.estilo_luta_principal, m.cargo,
                       d.nome_divisao AS divisao, m.status, m.data_entrada, m.avatar_hash
                FROM membros m
                LEFT JOIN divisoes d ON m.divisao_id = d.id
                ORDER BY m.data_entrada DESC
            """)
            warns = await conn.fetch("""
                SELECT membro_id, COUNT(*) AS total_warns
                FROM punicoes WHERE tipo = 'Warn' GROUP BY membro_id
            """)
            stats = await conn.fetch("""
                SELECT p.membro_id,
                       COUNT(*) FILTER (WHERE t.tipo = 'Interno') AS internos,
                       COUNT(*) FILTER (WHERE t.tipo = 'Amistoso') AS amistosos
                FROM presencas_treino p
                JOIN treinos t ON p.treino_id = t.id_treino
                WHERE p.presenca = 'Presente'
                GROUP BY p.membro_id
            """)
            try:
                guerras = await conn.fetch("""
                    SELECT membro_id, COUNT(*) AS total_guerras
                    FROM participacoes_guerra GROUP BY membro_id
                """)
            except Exception:
                guerras = []

            warns_map = {r["membro_id"]: r["total_warns"] for r in warns}
            stats_map = {r["membro_id"]: dict(r) for r in stats}
            guerras_map = {r["membro_id"]: r["total_guerras"] for r in guerras}
            resultado = []
            for row in membros:
                m = dict(row)
                s = stats_map.get(m["discord_id"], {})
                m["warns"] = warns_map.get(m["discord_id"], 0)
                m["stats"] = {
                    "internos": s.get("internos", 0),
                    "amistosos": s.get("amistosos", 0),
                    "guerras": guerras_map.get(m["discord_id"], 0),
                }
                resultado.append(m)
            return resultado
        finally:
            await conn.close()
    return executar(_get())


@st.cache_data(ttl=300, show_spinner=False)
def carregar_treinos():
    async def _get():
        conn = await get_db()
        try:
            rows = await conn.fetch("""
                SELECT t.*,
                       (SELECT COUNT(*) FROM presencas_treino p
                        WHERE p.treino_id = t.id_treino
                        AND p.inscricao = 'Confirmado') AS inscritos
                FROM treinos t ORDER BY t.data_treino DESC
            """)
            return [dict(r) for r in rows]
        finally:
            await conn.close()
    return executar(_get())


@st.cache_data(ttl=300, show_spinner=False)
def carregar_divisoes_completas():
    async def _get():
        conn = await get_db()
        try:
            divisoes = await conn.fetch("""
                SELECT d.*, l.nome_rp AS lider_nome, l.discord_username AS lider_discord,
                       v.nome_rp AS vice_nome, v.discord_username AS vice_discord
                FROM divisoes d
                LEFT JOIN membros l ON d.lider_id = l.discord_id
                LEFT JOIN membros v ON d.vice_lider_id = v.discord_id
                ORDER BY d.nome_divisao
            """)
            membros = await conn.fetch("""
                SELECT discord_id, discord_username, nome_rp, avatar_hash, divisao_id
                FROM membros WHERE divisao_id IS NOT NULL ORDER BY nome_rp
            """)
            por_divisao = {}
            for m in membros:
                por_divisao.setdefault(m["divisao_id"], []).append(dict(m))
            resultado = []
            for d in divisoes:
                item = dict(d)
                item["membros"] = por_divisao.get(d["id"], [])
                resultado.append(item)
            return resultado
        finally:
            await conn.close()
    return executar(_get())


@st.cache_data(ttl=60, show_spinner=False)
def carregar_inscricoes_usuario(membro_id):
    async def _get():
        conn = await get_db()
        try:
            rows = await conn.fetch("""
                SELECT treino_id, inscricao, presenca
                FROM presencas_treino WHERE membro_id = $1
            """, membro_id)
            return {r["treino_id"]: dict(r) for r in rows}
        finally:
            await conn.close()
    return executar(_get())


try:
    membros = carregar_dados_completos()
    treinos = carregar_treinos()
except Exception as exc:
    st.error(f"Sem conexão com o banco de dados: {exc}")
    membros, treinos = [], []

# =========================
# NAVEGAÇÃO
# =========================
st.sidebar.markdown("### Navegação")
aba = None
c1, c2 = st.sidebar.columns(2)
with c1:
    if st.button("Visão Geral", use_container_width=True): aba = "Visão Geral"
    if st.button("Membros", use_container_width=True): aba = "Membros"
    if st.button("Treinos", use_container_width=True): aba = "Treinos"
with c2:
    if st.button("Divisões", use_container_width=True): aba = "Divisões"
    if st.button("Parcerias", use_container_width=True): aba = "Parcerias"

if aba is None:
    aba = st.session_state.get("aba_atual", "Visão Geral")
else:
    st.session_state.aba_atual = aba

membros_filtrados = membros
if aba == "Membros":
    st.sidebar.markdown("---")
    cargos = ["Todos"] + sorted({m["cargo"] for m in membros if m["cargo"]})
    status_list = ["Todos"] + sorted({m["status"] for m in membros if m["status"]})
    divisoes_list = ["Todas"] + sorted({m["divisao"] for m in membros if m["divisao"]})
    cargo_filter = st.sidebar.selectbox("Cargo", cargos)
    status_filter = st.sidebar.selectbox("Status", status_list)
    divisao_filter = st.sidebar.selectbox("Divisão", divisoes_list)
    if cargo_filter != "Todos": membros_filtrados = [m for m in membros_filtrados if m["cargo"] == cargo_filter]
    if status_filter != "Todos": membros_filtrados = [m for m in membros_filtrados if m["status"] == status_filter]
    if divisao_filter != "Todas": membros_filtrados = [m for m in membros_filtrados if m["divisao"] == divisao_filter]

st.sidebar.markdown("---")
if st.sidebar.button("Atualizar dados agora"):
    st.cache_data.clear()
    st.rerun()

st.title("Hakuryū 白竜")
st.caption("Painel de gestão da organização")

# =========================
# VISÃO GERAL
# =========================
if aba == "Visão Geral":
    st.header("Visão Geral")
    ativos = sum(1 for m in membros if m["status"] == "Ativo")
    total_divisoes = len({m["divisao"] for m in membros if m["divisao"]})
    c1, c2, c3 = st.columns(3)
    c1.metric("Membros Ativos", ativos)
    c2.metric("Treinos Cadastrados", len(treinos))
    c3.metric("Divisões", total_divisoes)
    st.divider()
    st.subheader("Próximos Treinos")
    futuros = [t for t in treinos if t["data_treino"] >= datetime.date.today()]
    if futuros:
        for t in futuros[:5]:
            st.markdown(f"**{t['titulo']}** — {t['data_treino']} às {t['horario']} ({t['tipo']})")
    else:
        st.info("Nenhum treino futuro.")

# =========================
# MEMBROS
# =========================
elif aba == "Membros":
    st.header("Membros")
    st.subheader(f"Total exibido: {len(membros_filtrados)}")
    pode_gerenciar = tem_cargo("Lider") or tem_cargo("Vice-Lider") or eh_dono()
    for m in membros_filtrados:
        with st.container(border=True):
            c_avatar, c_info, c_cargo = st.columns([1, 4, 2])
            nome = m["nome_rp"] or m["discord_username"]
            with c_avatar:
                st.image(discord_avatar_url(m["discord_id"], m["avatar_hash"]), width=70)
            with c_info:
                st.markdown(f"### {nome}")
                st.caption(f"Discord: {m['discord_username']}")
                st.caption(f"Roblox: {m['nome_roblox'] or 'Não informado'}")
            with c_cargo:
                st.markdown(f"**Cargo:** {m['cargo']}")
                st.caption(f"Divisão: {m['divisao'] or 'Sem divisão'}")
                st.caption(f"Warns: {m['warns']}")
            with st.expander(f"Detalhes de {nome}"):
                a, b = st.columns(2)
                with a:
                    st.markdown(f"**Discord:** {m['discord_username']}")
                    st.markdown(f"**Roblox:** {m['nome_roblox'] or 'Não informado'}")
                    st.markdown(f"**Nome RP:** {m['nome_rp'] or 'Não informado'}")
                    st.markdown(f"**Gênero:** {m['genero'] or 'Não informado'}")
                    st.markdown(f"**Altura:** {m['altura_jogo'] or 'Não informado'}")
                    st.markdown(f"**Estilo de luta:** {m['estilo_luta_principal'] or 'Não informado'}")
                with b:
                    st.markdown(f"**Cargo:** {m['cargo']}")
                    st.markdown(f"**Divisão:** {m['divisao'] or 'Sem divisão'}")
                    st.markdown(f"**Status:** {m['status']}")
                    st.markdown(f"**Entrada:** {m['data_entrada']}")
                    st.markdown(f"**Warns:** {m['warns']}")
                s = m["stats"]
                st.divider()
                x, y, z = st.columns(3)
                x.metric("Treinos Internos", s["internos"])
                y.metric("Treinos Amistosos", s["amistosos"])
                z.metric("Guerras", s["guerras"])

# =========================
# TREINOS
# =========================
elif aba == "Treinos":
    st.header("Mural de Treinos")
    pode_gerenciar = tem_cargo("Lider") or tem_cargo("Vice-Lider") or tem_cargo("Líder de Divisão") or eh_dono()
    membro_id = st.session_state.user["id"]
    inscricoes = carregar_inscricoes_usuario(membro_id)
    if not treinos:
        st.info("Nenhum treino cadastrado.")
    for t in treinos:
        with st.container(border=True):
            st.subheader(f"{t['titulo']}")
            a, b, c = st.columns(3)
            a.caption(f"Data: {t['data_treino']} às {t['horario']}")
            b.caption(f"Tipo: {t['tipo']}")
            c.caption(f"Inscritos: {t['inscritos']}")
            if t.get("descricao"): st.write(t["descricao"])
            with st.expander("Inscrição de presença"):
                registro = inscricoes.get(t["id_treino"])
                status = registro["inscricao"] if registro else None
                if status is None:
                    if st.button("Inscrever-se", key=f"ins_{t['id_treino']}"):
                        async def inscrever():
                            conn = await get_db()
                            try:
                                await conn.execute("""INSERT INTO presencas_treino (treino_id, membro_id, inscricao)
                                    VALUES ($1, $2, 'Confirmado') ON CONFLICT (treino_id, membro_id)
                                    DO UPDATE SET inscricao = 'Confirmado'""", t["id_treino"], membro_id)
                            finally: await conn.close()
                        executar(inscrever()); st.cache_data.clear(); st.rerun()
                else:
                    st.markdown(f"**Status:** {status}")
                    if st.button("Ausentar-me", key=f"aus_{t['id_treino']}"):
                        async def ausentar():
                            conn = await get_db()
                            try: await conn.execute("DELETE FROM presencas_treino WHERE treino_id=$1 AND membro_id=$2", t["id_treino"], membro_id)
                            finally: await conn.close()
                        executar(ausentar()); st.cache_data.clear(); st.rerun()

# =========================
# DIVISÕES
# =========================
elif aba == "Divisões":
    st.header("Divisões")
    divisoes = carregar_divisoes_completas()
    pode_gerenciar = tem_cargo("Lider") or tem_cargo("Vice-Lider") or eh_dono()
    if not divisoes:
        st.info("Nenhuma divisão criada ainda.")
    for d in divisoes:
        with st.container(border=True):
            a, b = st.columns([1, 4])
            with a:
                if d["logo_url"]:
                    st.markdown(f'<img src="{d["logo_url"]}" class="divisao-logo">', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="divisao-logo" style="display:flex;align-items:center;justify-content:center;font-size:52px">龍</div>', unsafe_allow_html=True)
            with b:
                st.subheader(d["nome_divisao"])
                st.caption(f"Função: {d['funcao_principal'] or 'Não informada'}")
                st.markdown(f"**Líder:** {d['lider_nome'] or 'Não definido'}")
                st.markdown(f"**Vice-Líder:** {d['vice_nome'] or 'Não definido'}")
                membros_divisao = d["membros"]
                st.caption(f"Membros: {len(membros_divisao)}")
                for m in membros_divisao:
                    nome = m["nome_rp"] or m["discord_username"]
                    st.markdown(f"{nome}")

# =========================
# PARCERIAS
# =========================
elif aba == "Parcerias":
    st.header("Parcerias")
    st.info("Em breve: lista de parcerias, status e links.")
