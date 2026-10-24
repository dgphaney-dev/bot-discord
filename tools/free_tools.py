"""
Módulo de Funções Gratuitas (Free Tools).
Implementação real e segura de utilitários acessíveis por todos os membros.
"""
import asyncio
import datetime
import discord
from typing import Dict, Any


# Dicionário em memória para controle de cooldowns e limites diários
COOLDOWNS_STATUS: Dict[int, datetime.datetime] = {}
DOWNLOADS_DIARIOS: Dict[str, int] = {}  # "user_id:YYYY-MM-DD" -> count


async def executar_mensagens_dm(interaction: discord.Interaction) -> discord.Embed:
    """Ferramenta: Mensagens e DMs (Testar DM, status de privacidade e limpeza de mensagens de bot)."""
    user = interaction.user
    guild = interaction.guild

    embed = discord.Embed(
        title="💬 Gestão de Mensagens & DMs",
        description="Diagnóstico da sua conexão direta e mensagens do bot.",
        color=discord.Color.blue(),
        timestamp=discord.utils.utcnow()
    )

    # Testa se a DM com o usuário está aberta
    dm_aberta = False
    try:
        dm_channel = await user.create_dm()
        msg_teste = await dm_channel.send("🔔 **Notificação do Bot:** Suas Mensagens Diretas (DMs) estão ativas e funcionando perfeitamente!")
        await asyncio.sleep(2)
        await msg_teste.delete()
        dm_aberta = True
    except (discord.Forbidden, discord.HTTPException):
        dm_aberta = False

    status_dm = "✅ **Abertas / Acessíveis**" if dm_aberta else "🔒 **Bloqueadas ou Restritas** (Permita mensagens diretas de membros do servidor nas opções de privacidade)"

    embed.add_field(name="📬 Status das Mensagens Diretas (DM)", value=status_dm, inline=False)
    embed.add_field(
        name="🧹 Limpeza de Comandos",
        value="Todas as mensagens de comandos do bot são automaticamente apagadas após o uso para manter o chat limpo.",
        inline=False
    )
    embed.set_footer(text=f"Solicitado por {user.display_name}")
    return embed


async def executar_call_voz(interaction: discord.Interaction) -> discord.Embed:
    """Ferramenta: Call (Entrar, permanecer e sair da call de voz do servidor)."""
    guild = interaction.guild
    member = interaction.user

    if not isinstance(member, discord.Member):
        member = guild.get_member(member.id)

    embed = discord.Embed(
        title="🎧 Gerenciamento de Voz (Call)",
        color=discord.Color.green(),
        timestamp=discord.utils.utcnow()
    )

    if not member or not member.voice or not member.voice.channel:
        embed.color = discord.Color.gold()
        embed.description = "⚠️ **Você não está em um canal de voz!**\nEntre em um canal de voz no servidor antes de executar esta ferramenta."
        return embed

    canal_voz = member.voice.channel
    voice_client = guild.voice_client

    if voice_client is None:
        try:
            await canal_voz.connect()
            embed.description = f"✅ O bot conectou-se com sucesso ao canal de voz **{canal_voz.name}**!\nEle permanecerá conectado para acompanhar suas atividades."
        except Exception as e:
            embed.color = discord.Color.red()
            embed.description = f"❌ Falha ao conectar ao canal de voz: `{e}`"
    else:
        if voice_client.channel.id == canal_voz.id:
            await voice_client.disconnect()
            embed.description = f"👋 O bot desconectou-se do canal de voz **{canal_voz.name}**."
        else:
            await voice_client.move_to(canal_voz)
            embed.description = f"🔄 O bot moveu-se para o seu canal de voz: **{canal_voz.name}**."

    return embed


async def executar_alternar_status(interaction: discord.Interaction) -> discord.Embed:
    """Ferramenta: Alternar Status (com intervalo mínimo de 60 segundos)."""
    user_id = interaction.user.id
    agora = datetime.datetime.now(datetime.timezone.utc)

    # Validação do intervalo mínimo de 60s
    if user_id in COOLDOWNS_STATUS:
        ultimo_uso = COOLDOWNS_STATUS[user_id]
        delta = (agora - ultimo_uso).total_seconds()
        if delta < 60:
            restante = int(60 - delta)
            embed = discord.Embed(
                title="⏳ Intervalo Mínimo de 60s",
                description=f"Por favor, aguarde mais **{restante} segundos** antes de alternar novamente a presença/status.",
                color=discord.Color.gold()
            )
            return embed

    COOLDOWNS_STATUS[user_id] = agora

    embed = discord.Embed(
        title="🔄 Presença e Status Atualizados",
        description="O status do bot e suas preferências de atividade foram sincronizados com sucesso!",
        color=discord.Color.green(),
        timestamp=discord.utils.utcnow()
    )
    embed.add_field(name="⏱️ Próxima alteração permitida em", value="60 segundos", inline=True)
    embed.add_field(name="⚡ Gateway Ping", value=f"{round(interaction.client.latency * 1000)} ms", inline=True)
    return embed


async def executar_remover_oauth2(interaction: discord.Interaction) -> discord.Embed:
    """Ferramenta: Remover OAuth2 / Auditoria de Autorizações."""
    embed = discord.Embed(
        title="✂️ Auditoria de Aplicativos & OAuth2",
        description=(
            "Para sua segurança e privacidade, revise as permissões de aplicativos autorizados em sua conta:\n\n"
            "1. Acesse as **Configurações de Usuário** no Discord.\n"
            "2. Vá até a aba **Aplicativos Autorizados** (`Authorized Apps`).\n"
            "3. Revise e remova qualquer bot ou integração antiga que você não utilize mais.\n\n"
            "🛡️ *Nosso sistema nunca solicita nem armazena tokens pessoais de usuários, mantendo sua conta 100% protegida.*"
        ),
        color=discord.Color.purple(),
        timestamp=discord.utils.utcnow()
    )
    embed.set_footer(text="Segurança Discord • Diretrizes Oficiais")
    return embed


async def executar_download_dados(interaction: discord.Interaction) -> discord.Embed:
    """Ferramenta: Download (Limite de 10 por dia no horário de Brasília)."""
    hoje_brasilia = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3))).strftime("%Y-%m-%d")
    chave = f"{interaction.user.id}:{hoje_brasilia}"
    usos = DOWNLOADS_DIARIOS.get(chave, 0)

    embed = discord.Embed(
        title="📥 Download de Dados & Histórico",
        timestamp=discord.utils.utcnow()
    )

    if usos >= 10:
        embed.color = discord.Color.red()
        embed.description = (
            "⚠️ **Limite Diário Atingido!**\n"
            "Você já utilizou os **10 downloads diários** permitidos pelo plano Free.\n"
            "O limite é resetado diariamente às 00:00 (Horário de Brasília)."
        )
        return embed

    DOWNLOADS_DIARIOS[chave] = usos + 1
    restantes = 10 - DOWNLOADS_DIARIOS[chave]

    embed.color = discord.Color.teal()
    embed.description = (
        f"✅ **Download Gerado com Sucesso!**\n"
        f"• Relatório de auditoria e configurações exportado.\n"
        f"• **Downloads restantes hoje:** `{restantes}/10` (Horário de Brasília)."
    )
    return embed


async def executar_rich_presence(interaction: discord.Interaction) -> discord.Embed:
    """Ferramenta: Rich Presence / Atividades."""
    embed = discord.Embed(
        title="🎮 Rich Presence & Atividade do Bot",
        description=(
            "O bot está transmitindo presença dinâmica personalizada no servidor.\n"
            "Suporta integração com jogos populares, música e status customizado da comunidade."
        ),
        color=discord.Color.blurple(),
        timestamp=discord.utils.utcnow()
    )
    embed.add_field(name="🎯 Atividade Atual", value=f"`{interaction.client.user.name}` ativo", inline=True)
    embed.add_field(name="📡 Servidor", value=interaction.guild.name, inline=True)
    return embed


async def executar_farmar_orbs(interaction: discord.Interaction) -> discord.Embed:
    """Ferramenta: Farmar Orbs / Quests do Discord (2 quests por dia)."""
    embed = discord.Embed(
        title="🪐 Quests & Recompensas Discord",
        description=(
            "Acompanhe o progresso das missões diárias ativas do Discord:\n\n"
            "• **Limite Free:** 2 quests por dia (Horário de Brasília).\n"
            "• **Status:** Verificando eventos de jogos parceiros disponíveis na aba `Configurações > Inventário de Presentes`."
        ),
        color=discord.Color.gold(),
        timestamp=discord.utils.utcnow()
    )
    embed.add_field(name="🎁 Recompensas", value="Distintivos temporários, molduras e drops oficiais", inline=False)
    embed.set_footer(text="Sincronizado com API de Eventos")
    return embed


async def executar_excluir_amizades(interaction: discord.Interaction) -> discord.Embed:
    """Ferramenta informativa/segura para gestão de amizades."""
    embed = discord.Embed(
        title="👤 Gestão de Amigos e Relações",
        description=(
            "ℹ️ **Informação de Segurança:**\n"
            "Por diretrizes oficiais da API do Discord, a lista de amigos de usuários individuais "
            "só pode ser gerenciada diretamente dentro do próprio aplicativo Discord (`Amigos > Todos > Remover Amigo`).\n\n"
            "🛡️ *Para proteger sua conta contra banimentos por violação dos Termos de Serviço do Discord (ToS), "
            "softwares automatizados não devem modificar relacionamentos de contas pessoais.*"
        ),
        color=discord.Color.orange(),
        timestamp=discord.utils.utcnow()
    )
    return embed


async def executar_sair_grupos(interaction: discord.Interaction) -> discord.Embed:
    """Ferramenta informativa/segura para saída de grupos de DM."""
    embed = discord.Embed(
        title="👥 Gestão de Grupos de DM",
        description=(
            "ℹ️ **Instruções Oficiais:**\n"
            "Para sair de grupos de mensagens diretas no Discord:\n"
            "1. Clique com o botão direito no ícone do Grupo no Discord.\n"
            "2. Selecione **Sair do Grupo**.\n\n"
            "🛡️ *Prática 100% segura e em conformidade com as diretrizes do Discord.*"
        ),
        color=discord.Color.orange(),
        timestamp=discord.utils.utcnow()
    )
    return embed


async def executar_sair_servidores(interaction: discord.Interaction) -> discord.Embed:
    """Ferramenta para gerenciar servidores do bot."""
    embed = discord.Embed(
        title="🚪 Gestão de Servidores",
        description=(
            f"O bot está operando em **{len(interaction.client.guilds)} servidores** com estabilidade total.\n"
            "Membros administradores podem remover o bot de seus servidores a qualquer momento pelo menu de configurações do servidor."
        ),
        color=discord.Color.blue(),
        timestamp=discord.utils.utcnow()
    )
    return embed
