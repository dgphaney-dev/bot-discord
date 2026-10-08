import json
from pathlib import Path
import re
import discord
from config import CARGO_PERM_MUTE, Cores


def converter_tempo(tempo_str: str) -> int | None:
    """
    Converte uma string de tempo (ex: '30s', '15m', '2h', '1d') em segundos.
    Retorna None se o formato for inválido.
    """
    if not isinstance(tempo_str, str):
        return None

    tempo_str = tempo_str.strip().lower()
    match = re.match(r"^(\d+)([smhd])$", tempo_str)
    if not match:
        return None

    quantidade = int(match.group(1))
    unidade = match.group(2)

    fatores = {
        "s": 1,
        "m": 60,
        "h": 3600,
        "d": 86400
    }

    return quantidade * fatores.get(unidade, 0)


def formatar_segundos(segundos: int) -> str:
    """Formata um valor em segundos para texto legível."""
    if segundos >= 86400 and segundos % 86400 == 0:
        dias = segundos // 86400
        return f"{dias} dia(s)"
    if segundos >= 3600 and segundos % 3600 == 0:
        horas = segundos // 3600
        return f"{horas} hora(s)"
    if segundos >= 60 and segundos % 60 == 0:
        minutos = segundos // 60
        return f"{minutos} minuto(s)"
    return f"{segundos} segundo(s)"


# ========================================================
# SISTEMA DE PERMISSÕES CONFIGURÁVEIS POR CARGO
# ========================================================
ARQUIVO_PERMISSOES = Path(__file__).resolve().parent.parent / "data" / "permissoes.json"


def carregar_permissoes() -> dict:
    """Carrega o mapa de permissões salvas por servidor."""
    if not ARQUIVO_PERMISSOES.exists():
        return {}
    try:
        with open(ARQUIVO_PERMISSOES, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def salvar_permissoes(dados: dict):
    """Salva o mapa de permissões no arquivo JSON."""
    ARQUIVO_PERMISSOES.parent.mkdir(parents=True, exist_ok=True)
    with open(ARQUIVO_PERMISSOES, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)


def obter_cargo_permissao(guild_id: int, acao: str) -> int | None:
    """Retorna o ID do cargo configurado para uma determinada ação."""
    dados = carregar_permissoes()
    return dados.get(str(guild_id), {}).get(acao.lower())


def tem_permissao_acao(ctx, acao: str) -> bool:
    """
    Verifica se o autor do comando tem permissão para a ação especificada no Modo 100% Estrito.
    Regra:
    - O autor PRECISA OBRIGATORIAMENTE possuir o cargo configurado para a ação ou o cargo geral de Staff!
    - Nem o Dono do Servidor nem Administradores conseguem usar sem ter o cargo cadastrado.
    """
    if not ctx.guild or not ctx.author:
        return False

    acao_limpa = acao.lower().strip()
    guild_id = ctx.guild.id

    # 1. Verifica se o autor possui o cargo geral de Staff configurado
    cargo_staff_id = obter_cargo_permissao(guild_id, "staff")
    if cargo_staff_id and any(role.id == cargo_staff_id for role in ctx.author.roles):
        return True

    # 2. Verifica se o autor possui o cargo configurado especificamente para essa ação
    cargo_id = obter_cargo_permissao(guild_id, acao_limpa)
    if cargo_id and any(role.id == cargo_id for role in ctx.author.roles):
        return True

    return False


def tem_permissao_mute(ctx) -> bool:
    """Atalho de compatibilidade para verificar permissão de mute."""
    return tem_permissao_acao(ctx, "mute")


def obter_avatar_url(usuario) -> str | None:
    """Retorna de forma segura a URL do avatar de um membro ou usuário."""
    if usuario is None:
        return None

    if hasattr(usuario, "display_avatar") and usuario.display_avatar:
        return usuario.display_avatar.url
    if hasattr(usuario, "avatar") and usuario.avatar:
        return usuario.avatar.url
    if hasattr(usuario, "default_avatar") and usuario.default_avatar:
        if hasattr(usuario.default_avatar, "url"):
            return usuario.default_avatar.url
        return str(usuario.default_avatar)
    return None


async def tentar_deletar_mensagem(ctx):
    """Tenta deletar a mensagem original do comando sem lançar erros se falhar."""
    try:
        if ctx.message:
            await ctx.message.delete()
    except (discord.Forbidden, discord.NotFound, discord.HTTPException, AttributeError):
        pass


def criar_embed_erro(titulo: str, descricao: str) -> discord.Embed:
    """Helper para padronizar embeds de erro."""
    return discord.Embed(
        title=f"❌ {titulo}",
        description=descricao,
        color=Cores.ERRO
    )


def criar_embed_sucesso(titulo: str, descricao: str) -> discord.Embed:
    """Helper para padronizar embeds de sucesso."""
    return discord.Embed(
        title=f"✅ {titulo}",
        description=descricao,
        color=Cores.SUCESSO
    )