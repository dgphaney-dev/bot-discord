"""
Módulo de Funções Booster.
Ferramentas exclusivas para membros que impulsionam o servidor.
"""
import discord


async def executar_boost_prioridade(interaction: discord.Interaction) -> discord.Embed:
    """Ferramenta Booster: Prioridade em atendimento e filas."""
    embed = discord.Embed(
        title="🚀 Suporte Prioritário Booster",
        description=(
            f"Obrigado por apoiar **{interaction.guild.name}**!\n\n"
            "• Seus tickets de suporte recebem prioridade máxima na fila da Staff.\n"
            "• Acesso prioritário aos canais de áudio de alta fidelidade (384kbps).\n"
            "• Cooldown reduzido em todos os comandos do bot."
        ),
        color=discord.Color.nitro_pink(),
        timestamp=discord.utils.utcnow()
    )
    return embed


async def executar_boost_canal_temp(interaction: discord.Interaction) -> discord.Embed:
    """Ferramenta Booster: Criação de canal de voz temporário exclusivo."""
    guild = interaction.guild
    member = interaction.user

    embed = discord.Embed(
        title="🚀 Canal Temporário de Booster",
        color=discord.Color.nitro_pink(),
        timestamp=discord.utils.utcnow()
    )

    try:
        nome_canal = f"🚀・Call {member.display_name}"
        categoria = discord.utils.get(guild.categories, name="Calls VIP") or None
        canal = await guild.create_voice_channel(
            name=nome_canal,
            category=categoria,
            user_limit=10,
            reason=f"Canal temporário de Booster solicitado por {member.name}"
        )
        embed.description = f"✅ Canal de voz exclusivo criado com sucesso: **{canal.mention}**!\nEle fica disponível para você e seus amigos."
    except discord.Forbidden:
        embed.color = discord.Color.red()
        embed.description = "❌ O bot não possui permissão para gerenciar canais neste servidor."
    except Exception as e:
        embed.color = discord.Color.red()
        embed.description = f"❌ Erro ao criar canal: `{e}`"

    return embed


async def executar_boost_estatisticas(interaction: discord.Interaction) -> discord.Embed:
    """Ferramenta Booster: Métricas e estatísticas do servidor."""
    guild = interaction.guild
    embed = discord.Embed(
        title="🚀 Métricas Avançadas do Servidor",
        color=discord.Color.nitro_pink(),
        timestamp=discord.utils.utcnow()
    )
    embed.add_field(name="✨ Nível de Impulso", value=f"Nível {guild.premium_tier}", inline=True)
    embed.add_field(name="💎 Total de Boosts", value=f"{guild.premium_subscription_count} impulsos", inline=True)
    embed.add_field(name="👥 Total de Membros", value=f"{guild.member_count}", inline=True)
    return embed
