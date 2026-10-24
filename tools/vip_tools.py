"""
Módulo de Funções VIP / Premium.
Ferramentas exclusivas para membros com plano VIP ativo.
"""
import discord
from config import VIP_CARGOS, VIP_LIMITES_AMIGOS


async def executar_vip_status(interaction: discord.Interaction) -> discord.Embed:
    """Ferramenta VIP: Status e resumo do plano VIP."""
    member = interaction.user
    guild = interaction.guild

    cargos_vip = [r.name for r in member.roles if r.name.lower() in [c.lower() for c in VIP_CARGOS.values()]]
    plano_atual = cargos_vip[0] if cargos_vip else "VIP Padrão"

    embed = discord.Embed(
        title="👑 Central do Membro VIP",
        description=f"Bem-vindo à sua área VIP, **{member.display_name}**!",
        color=discord.Color.gold(),
        timestamp=discord.utils.utcnow()
    )
    embed.add_field(name="🏷️ Plano Ativo", value=f"`{plano_atual}`", inline=True)
    embed.add_field(name="✨ Benefícios", value="• Cargo com cor personalizada\n• Canal de voz VIP exclusivo\n• Acesso ao chat de IA sem restrições", inline=False)
    embed.set_footer(text="Acesse o comando !vip para mais opções detalhadas")
    return embed


async def executar_vip_call(interaction: discord.Interaction) -> discord.Embed:
    """Ferramenta VIP: Criar ou gerenciar canal de voz VIP com limite de amigos."""
    guild = interaction.guild
    member = interaction.user

    embed = discord.Embed(
        title="👑 Call VIP Privada",
        color=discord.Color.gold(),
        timestamp=discord.utils.utcnow()
    )

    try:
        nome_canal = f"👑・VIP {member.display_name}"
        categoria = discord.utils.get(guild.categories, name="Calls VIP") or None
        canal = await guild.create_voice_channel(
            name=nome_canal,
            category=categoria,
            reason=f"Call VIP criada por {member.name}"
        )
        embed.description = f"✅ Seu canal de voz VIP exclusivo foi gerado: **{canal.mention}**!"
    except discord.Forbidden:
        embed.color = discord.Color.red()
        embed.description = "❌ O bot não possui a permissão de `Gerenciar Canais` para criar a call VIP."
    except Exception as e:
        embed.color = discord.Color.red()
        embed.description = f"❌ Erro ao gerar canal VIP: `{e}`"

    return embed
