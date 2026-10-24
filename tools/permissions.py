"""
Módulo de Verificação de Permissões e Níveis de Acesso (Free, Booster, VIP).
Valida diretamente no backend através dos dados confiáveis da guilda Discord.
"""
from typing import Tuple
import discord
from config import VIP_CARGOS


def obter_nivel_acesso(member: discord.Member) -> dict:
    """
    Retorna o perfil completo de acesso do membro:
    - is_free: True (todos os membros)
    - is_booster: True se impulsiona o servidor (ou é admin/dono)
    - is_vip: True se possui qualquer um dos cargos VIP configurados (ou é admin/dono)
    - is_admin: True se possui permissão de Administrador
    - tier_nome: Nome formatado do nível mais alto
    """
    if not isinstance(member, discord.Member):
        return {
            "is_free": True,
            "is_booster": False,
            "is_vip": False,
            "is_admin": False,
            "tier_nome": "Free",
            "cargos_vip": []
        }

    is_admin = member.guild_permissions.administrator or member.id == member.guild.owner_id
    is_booster = (member.premium_since is not None) or is_admin

    nomes_cargos_membro = {cargo.name.lower() for cargo in member.roles}
    cargos_vip_config = [nome.lower() for nome in VIP_CARGOS.values()]

    cargos_vip_encontrados = [
        cargo.name for cargo in member.roles if cargo.name.lower() in cargos_vip_config
    ]
    is_vip = bool(cargos_vip_encontrados) or is_admin

    # Determina o rótulo principal
    if is_admin:
        tier_nome = "Administrador (Acesso Total)"
    elif is_vip and is_booster:
        tier_nome = "VIP Booster"
    elif is_vip:
        tier_nome = f"VIP ({cargos_vip_encontrados[0]})"
    elif is_booster:
        tier_nome = "Server Booster"
    else:
        tier_nome = "Free"

    return {
        "is_free": True,
        "is_booster": is_booster,
        "is_vip": is_vip,
        "is_admin": is_admin,
        "tier_nome": tier_nome,
        "cargos_vip": cargos_vip_encontrados,
        "boost_desde": member.premium_since
    }


def verificar_permissao(member: discord.Member, nivel_requerido: str) -> Tuple[bool, str]:
    """
    Verifica se o membro pode acessar uma função de determinado nível:
    'free', 'booster', ou 'vip'.
    Retorna (autorizado: bool, motivo_ou_erro: str).
    """
    info = obter_nivel_acesso(member)
    nivel = nivel_requerido.lower().strip()

    if nivel == "free":
        return True, "Acesso autorizado."

    if nivel == "booster":
        if info["is_booster"]:
            return True, "Acesso autorizado como Server Booster."
        return False, (
            "🔒 **Acesso Negado: Categoria Booster**\n\n"
            "Esta funcionalidade é exclusiva para membros que estão **impulsionando este servidor**.\n"
            "👉 Dê um Boost no servidor para desbloquear instantaneamente todas as ferramentas Booster!"
        )

    if nivel in ("vip", "premium"):
        if info["is_vip"]:
            return True, "Acesso autorizado como Membro VIP."
        cargos_str = ", ".join([f"`{c}`" for c in VIP_CARGOS.values()])
        return False, (
            "🔒 **Acesso Negado: Categoria Premium / VIP**\n\n"
            "Esta funcionalidade é exclusiva para membros com **plano VIP ativo**.\n"
            f"👉 Cargos aceitos: {cargos_str}.\n"
            "Use o comando `!vip` ou contate a administração para obter seu VIP."
        )

    return False, f"Nível de permissão desconhecido: `{nivel_requerido}`."
