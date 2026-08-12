import os
import requests
from oauthlib.oauth2 import WebApplicationClient
import streamlit as st

if os.path.exists(".env"):
    from dotenv import load_dotenv
    load_dotenv()

CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", st.secrets.get("DISCORD_CLIENT_ID", ""))
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", st.secrets.get("DISCORD_CLIENT_SECRET", ""))
REDIRECT_URI = "https://hakuryubot-p9s7blcsjpkzdnkjxxqvdq.streamlit.app/"
GUILD_ID = os.getenv("DISCORD_GUILD_ID", st.secrets.get("DISCORD_GUILD_ID", ""))
DONO_ID = os.getenv("DONO_DISCORD_ID", st.secrets.get("DONO_DISCORD_ID", ""))

client = WebApplicationClient(CLIENT_ID)

def get_login_url():
    return client.prepare_request_uri(
        "https://discord.com/api/oauth2/authorize",
        redirect_uri=REDIRECT_URI,
        scope=["identify", "guilds", "guilds.members.read"]
    )

def exchange_code(code):
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "scope": "identify guilds guilds.members.read"
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = requests.post("https://discord.com/api/oauth2/token", data=data, headers=headers)
    r.raise_for_status()
    return r.json()

def get_user_info(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    r = requests.get("https://discord.com/api/users/@me", headers=headers)
    r.raise_for_status()
    return r.json()

def get_guild_member(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        r = requests.get(f"https://discord.com/api/users/@me/guilds/{GUILD_ID}/member", headers=headers)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

def autenticar():
    query_params = st.query_params
    if "code" in query_params:
        code = query_params["code"]
        token_data = exchange_code(code)
        user_info = get_user_info(token_data["access_token"])
        member_info = get_guild_member(token_data["access_token"])
        cargos = []
        if member_info and isinstance(member_info, dict):
            cargos = [role["name"] for role in member_info.get("roles", []) if isinstance(role, dict)]
        st.session_state.user = {
            "id": user_info["id"],
            "nome": user_info["username"],
            "avatar": f"https://cdn.discordapp.com/avatars/{user_info['id']}/{user_info['avatar']}.png?size=128" if user_info["avatar"] else "https://cdn.discordapp.com/embed/avatars/0.png",
            "cargos": cargos
        }
        # Limpa a URL removendo o parâmetro 'code' para evitar loop
        st.markdown(
            """
            <script>
            if (window.location.search.includes('code=')) {
                const url = new URL(window.location);
                url.searchParams.delete('code');
                window.history.replaceState({}, document.title, url.pathname + url.search);
            }
            </script>
            """,
            unsafe_allow_html=True
        )
        st.query_params.clear()

def esta_logado():
    return "user" in st.session_state

def tem_cargo(cargo):
    return esta_logado() and cargo in st.session_state.user.get("cargos", [])

def eh_dono():
    return esta_logado() and st.session_state.user["id"] == DONO_ID