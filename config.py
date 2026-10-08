import os
from pathlib import Path
import discord
from dotenv import load_dotenv

# Carrega o arquivo .env localizado na pasta do bot ou na raiz do projeto
diretorio_base = Path(__file__).resolve().parent
caminho_env = diretorio_base / ".env"
load_dotenv(dotenv_path=caminho_env)

# ========================================================
# CONFIGURAÇÕES BÁSICAS DO BOT
# ========================================================
TOKEN = os.getenv("DISCORD_TOKEN", "")

PREFIXO = os.getenv("BOT_PREFIX", "!")

# Intents do Discord
INTENTS = discord.Intents.default()
INTENTS.message_content = True
INTENTS.members = True
INTENTS.guilds = True
INTENTS.presences = True

# ========================================================
# STATUS E PRESENÇA DO BOT
# ========================================================
STATUS_TIPO = os.getenv("BOT_STATUS", "online").lower()
STATUS_MAPA = {
    "online": discord.Status.online,
    "idle": discord.Status.idle,
    "dnd": discord.Status.dnd,
    "invisivel": discord.Status.invisible,
    "invisible": discord.Status.invisible,
}
STATUS_DISCORD = STATUS_MAPA.get(STATUS_TIPO, discord.Status.online)
ATIVIDADE_TEXTO = os.getenv("BOT_ATIVIDADE", f"Meu prefixo é {PREFIXO}")

# ========================================================
# FUNÇÃO AUXILIAR PARA PARSE DE CORES HEXADECIMAIS
# ========================================================
def obter_cor(env_var: str, fallback_hex: str) -> discord.Color:
    """Lê um código hexadecimal do .env ou usa o padrão se inválido."""
    valor = os.getenv(env_var, fallback_hex).strip()
    if not valor.startswith("#"):
        valor = f"#{valor}"
    try:
        return discord.Color.from_str(valor)
    except ValueError:
        return discord.Color.from_str(fallback_hex)


# ========================================================
# PALETA DE CORES PARA EMBEDS (CONFIGURÁVEL NO .ENV)
# ========================================================
class Cores:
    SUCESSO = obter_cor("COR_EMBED_SUCESSO", "#00FF22")
    ERRO = obter_cor("COR_EMBED_ERRO", "#ED4245")
    AVISO = obter_cor("COR_EMBED_AVISO", "#FFCC00")
    INFO = obter_cor("COR_EMBED_INFO", "#00C3FF")
    MODERACAO = obter_cor("COR_EMBED_MODERACAO", "#B700FF")
    PADRAO = obter_cor("COR_EMBED_PADRAO", "#5865F2")

# ========================================================
# CONFIGURAÇÕES DE MODERAÇÃO E SISTEMA
# ========================================================
CARGO_MUTE_NOME = os.getenv("CARGO_MUTE_NOME", "Mutado")
CARGO_PERM_MUTE = os.getenv("CARGO_PERM_MUTE", "mute")
LIMITE_PURGE_MAX = int(os.getenv("LIMITE_PURGE_MAX", "500"))

# ========================================================
# CONFIGURAÇÕES DO SISTEMA VIP
# ========================================================
VIP_CARGOS = {
    "prata": os.getenv("VIP_CARGO_PRATA", "VIP Prata"),
    "gold": os.getenv("VIP_CARGO_GOLD", "VIP Gold"),
    "diamante": os.getenv("VIP_CARGO_DIAMANTE", "VIP Diamante"),
}

VIP_CORES = {
    "prata": obter_cor("COR_VIP_PRATA", "#C0C0C0"),        # Prata
    "gold": obter_cor("COR_VIP_GOLD", "#FFD700"),          # Dourado
    "diamante": obter_cor("COR_VIP_DIAMANTE", "#00E5FF"),  # Ciano / Diamante
}

VIP_LIMITES_AMIGOS = {
    "prata": int(os.getenv("VIP_LIMITE_PRATA", "1")),
    "gold": int(os.getenv("VIP_LIMITE_GOLD", "3")),
    "diamante": int(os.getenv("VIP_LIMITE_DIAMANTE", "5")),
}

VIP_CATEGORIA_CALLS = os.getenv("VIP_CATEGORIA_CALLS", "Calls VIP")

# ========================================================
# TEMPOS DE AUTODEL DA MENSAGEM (SEGUNDOS)
# ========================================================
TEMPO_DELETE_ERRO = int(os.getenv("TEMPO_DELETE_ERRO", "10"))
TEMPO_DELETE_SUCESSO = int(os.getenv("TEMPO_DELETE_SUCESSO", "15"))
TEMPO_DELETE_VIP = int(os.getenv("TEMPO_DELETE_VIP", "120"))
AUTO_DELETE_COMANDOS = os.getenv("AUTO_DELETE_COMANDOS", "true").lower() in ("true", "1", "sim", "yes")

# ========================================================
# CONFIGURAÇÕES DO CHAT COM IA (GOOGLE GEMINI)
# ========================================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODELO = os.getenv("GEMINI_MODELO", "gemini-3.5-flash-lite").strip()
IA_SYSTEM_PROMPT = os.getenv(
    "IA_SYSTEM_PROMPT",
    "Você é o Aspas (Erick Santos), astro do Valorant e uma Inteligência Artificial completa no Discord. "
    "REGRA OBRIGATÓRIA: Dê SEMPRE respostas MUITO CURTAS (no máximo 1 ou 2 frases breves, direto ao ponto). "
    "NUNCA mande textões, parágrafos grandes ou explicações compridas. "
    "Fale sempre com a vibe do Aspas: calmo, humilde e descontraído ('pô mano', 'tô suave', 'se liga:', 'é só clicar na cabeça', 'tá safe', 'nois amassa'). "
    "Você manja de tudo (programação, matemática, biologia, valorant, zoeira), mas sempre responde de forma super curta e rápida."
).strip()
IA_MAX_HISTORICO = int(os.getenv("IA_MAX_HISTORICO", "10"))


