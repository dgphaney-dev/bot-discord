"""
Registro e Despachante Modular de Ferramentas (Tools).
Centraliza todas as ferramentas do sistema organizadas por categoria e nível de permissão.
"""
from typing import Dict, Any, Callable
from .permissions import obter_nivel_acesso, verificar_permissao
from .free_tools import (
    executar_mensagens_dm,
    executar_call_voz,
    executar_alternar_status,
    executar_remover_oauth2,
    executar_download_dados,
    executar_rich_presence,
    executar_farmar_orbs,
    executar_excluir_amizades,
    executar_sair_grupos,
    executar_sair_servidores,
)
from .booster_tools import (
    executar_boost_prioridade,
    executar_boost_canal_temp,
    executar_boost_estatisticas,
)
from .vip_tools import (
    executar_vip_status,
    executar_vip_call,
)

FERRAMENTAS: Dict[str, Dict[str, Any]] = {
    # Categoria Free
    "free_mensagens": {
        "nome": "Mensagens e DMs",
        "descricao": "Limpar mensagens, abrir e fechar DMs",
        "emoji": "💬",
        "tier": "free",
        "handler": executar_mensagens_dm
    },
    "free_call": {
        "nome": "Call",
        "descricao": "Entrar, permanecer e sair da call",
        "emoji": "🎧",
        "tier": "free",
        "handler": executar_call_voz
    },
    "free_status": {
        "nome": "Alternar Status",
        "descricao": "Intervalo minimo de 60s",
        "emoji": "🔄",
        "tier": "free",
        "handler": executar_alternar_status
    },
    "free_oauth2": {
        "nome": "Remover OAuth2",
        "descricao": "Remova autorizacoes de bots e apps",
        "emoji": "✂️",
        "tier": "free",
        "handler": executar_remover_oauth2
    },
    "free_download": {
        "nome": "Download",
        "descricao": "10 downloads por dia (horario de Brasilia)",
        "emoji": "📥",
        "tier": "free",
        "handler": executar_download_dados
    },
    "free_rich_presence": {
        "nome": "Rich Presence",
        "descricao": "Presets de jogos e RPC customizado",
        "emoji": "🎮",
        "tier": "free",
        "handler": executar_rich_presence
    },
    "free_orbs": {
        "nome": "Farmar Orbs",
        "descricao": "2 quests por dia (horario de Brasilia)",
        "emoji": "🪐",
        "tier": "free",
        "handler": executar_farmar_orbs
    },
    "free_amizades": {
        "nome": "Excluir Amizades",
        "descricao": "Remova e gerencie amigos com segurança",
        "emoji": "👤",
        "tier": "free",
        "handler": executar_excluir_amizades
    },
    "free_grupos": {
        "nome": "Sair de Grupos",
        "descricao": "Saia de todos os grupos de DM",
        "emoji": "👥",
        "tier": "free",
        "handler": executar_sair_grupos
    },
    "free_servidores": {
        "nome": "Sair de Servidores",
        "descricao": "Gerencie a presença em servidores",
        "emoji": "🚪",
        "tier": "free",
        "handler": executar_sair_servidores
    },

    # Categoria Booster
    "booster_canal": {
        "nome": "Canal Temporário Booster",
        "descricao": "Criar canal de voz exclusivo para você",
        "emoji": "🚀",
        "tier": "booster",
        "handler": executar_boost_canal_temp
    },
    "booster_prioridade": {
        "nome": "Suporte Prioritário",
        "descricao": "Prioridade de atendimento e canais especiais",
        "emoji": "✨",
        "tier": "booster",
        "handler": executar_boost_prioridade
    },
    "booster_stats": {
        "nome": "Métricas do Servidor",
        "descricao": "Estatísticas em tempo real sobre impulsos",
        "emoji": "📊",
        "tier": "booster",
        "handler": executar_boost_estatisticas
    },

    # Categoria VIP
    "vip_status": {
        "nome": "Status do Plano VIP",
        "descricao": "Visualizar seus benefícios e validade",
        "emoji": "👑",
        "tier": "vip",
        "handler": executar_vip_status
    },
    "vip_call": {
        "nome": "Call VIP Privada",
        "descricao": "Gerar canal VIP exclusivo com controle de amigos",
        "emoji": "💎",
        "tier": "vip",
        "handler": executar_vip_call
    },
}


def obter_ferramentas_por_tier(tier: str) -> Dict[str, Dict[str, Any]]:
    """Filtra o dicionário de ferramentas pelo nível informado."""
    tier_lower = tier.lower().strip()
    return {k: v for k, v in FERRAMENTAS.items() if v["tier"] == tier_lower}
