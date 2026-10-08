import asyncio
import os
import sys
from pathlib import Path
import discord
from discord.ext import commands

# Força a codificação UTF-8 no console do Windows para evitar erros com emojis
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Garante que o diretório base do bot esteja no sys.path
diretorio_base = Path(__file__).resolve().parent
if str(diretorio_base) not in sys.path:
    sys.path.insert(0, str(diretorio_base))

from config import (
    ATIVIDADE_TEXTO,
    AUTO_DELETE_COMANDOS,
    INTENTS,
    PREFIXO,
    STATUS_DISCORD,
    TOKEN,
    obter_atividade_texto,
    obter_prefixo_salvo,
)

def get_prefix(bot_instance, message):
    """Resolve o prefixo dinamicamente para cada mensagem em tempo real."""
    prefix = getattr(bot_instance, "custom_prefix", None) or obter_prefixo_salvo()
    return commands.when_mentioned_or(prefix)(bot_instance, message)

# Inicialização do Bot
bot = commands.Bot(
    command_prefix=get_prefix,
    intents=INTENTS,
    case_insensitive=True,  # Permite comandos tanto em minúsculas quanto maiúsculas (ex: !vip ou !VIP)
    help_command=None       # Desabilita o help padrão para usar o cog de painel interativo (!painel / !ajuda)
)
bot.custom_prefix = obter_prefixo_salvo()


async def setup_hook():
    """Executado antes do login para sincronizar comandos Slash globalmente."""
    try:
        print("🔄 Sincronizando comandos Slash (/) globalmente com o Discord...")
        sincronizados = await bot.tree.sync()
        print(f"✨ {len(sincronizados)} comandos Slash sincronizados globalmente!")
    except Exception as e:
        print(f"⚠️ Erro ao sincronizar globalmente: {e}")

bot.setup_hook = setup_hook


@bot.event
async def on_ready():
    """Disparado quando o bot se conecta com sucesso ao Discord."""
    print("=" * 50)
    print(f"🤖 Bot Conectado: {bot.user.name} (ID: {bot.user.id})")
    print(f"📡 Discord.py Versão: {discord.__version__}")
    print(f"🌐 Servidores Conectados: {len(bot.guilds)}")
    for g in bot.guilds:
        print(f"   🏠 {g.name} (ID: {g.id})")
        # Sincroniza na guilda para os comandos aparecerem instantaneamente no chat
        try:
            bot.tree.copy_global_to(guild=g)
            cmds = await bot.tree.sync(guild=g)
            print(f"      ⚡ {len(cmds)} comandos Slash sincronizados instantaneamente em: {g.name}")
        except Exception as e:
            print(f"      ⚠️ Falha ao sincronizar em {g.name}: {e}")
    prefixo_atual = getattr(bot, "custom_prefix", obter_prefixo_salvo())
    print(f"⚡ Prefixo Atual: {prefixo_atual}")
    print("=" * 50)

    # Configuração de status e atividade customizados
    texto_atividade = obter_atividade_texto(prefixo_atual)
    atividade = discord.Game(name=texto_atividade)
    await bot.change_presence(
        status=STATUS_DISCORD,
        activity=atividade
    )


@bot.event
async def on_message(message):
    """Monitora mensagens e encaminha para o processador de comandos."""
    if message.author.bot:
        return

    # Se a mensagem for um comando, apaga imediatamente do chat
    if message.content.startswith(PREFIXO):
        print(f"⚡ [Comando Recebido] {message.author.name} em #{message.channel.name}: '{message.content}'")
        if AUTO_DELETE_COMANDOS:
            try:
                await message.delete()
            except (discord.Forbidden, discord.NotFound, discord.HTTPException, AttributeError):
                pass

    await bot.process_commands(message)


@bot.before_invoke
async def auto_deletar_comando(ctx):
    """Garante que a mensagem do comando digitada pelo usuário seja sempre apagada do chat."""
    if AUTO_DELETE_COMANDOS:
        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.NotFound, discord.HTTPException, AttributeError):
            pass


@bot.event
async def on_command_completion(ctx):
    """Log de confirmação de comando executado com sucesso."""
    print(f"✅ [Comando Executado] '{ctx.command.name}' por {ctx.author.name} em #{ctx.channel.name}")


@bot.event
async def on_command_error(ctx, error):
    """Tratamento global de exceções para comandos."""
    # Se o comando tiver um tratamento de erro local específico, deixa ele lidar
    if hasattr(ctx.command, "on_error"):
        return

    cog = ctx.cog
    if cog and cog._get_overridden_method(cog.cog_command_error) is not None:
        return

    # Erros comuns que podem ser ignorados silenciosamente ou logados
    if isinstance(error, commands.CommandNotFound):
        print(f"❓ [Comando Não Encontrado] Mensagem de {ctx.author.name}: '{ctx.message.content}'")
        return

    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Você não tem permissão para executar este comando.", delete_after=8)
        return

    if isinstance(error, commands.BotMissingPermissions):
        await ctx.send("❌ O bot não possui as permissões necessárias para executar esta ação.", delete_after=8)
        return

    print(f"⚠️ Erro no comando '{ctx.command}': {error}")


async def carregar_modulos():
    """Carrega dinamicamente todos os Cogs presentes na pasta 'cogs'."""
    pasta_cogs = diretorio_base / "cogs"

    if not pasta_cogs.exists():
        print(f"❌ Pasta de cogs não encontrada: {pasta_cogs}")
        return

    print("📦 Carregando módulos (Cogs)...")
    for arquivo in pasta_cogs.glob("*.py"):
        nome_extensao = f"cogs.{arquivo.stem}"
        try:
            await bot.load_extension(nome_extensao)
            print(f"  ✅ Módulo [{arquivo.name}] carregado com sucesso.")
        except Exception as e:
            print(f"  ❌ Falha ao carregar o módulo [{arquivo.name}]: {e}")


async def main():
    """Ponto de entrada assíncrono para inicialização."""
    if not TOKEN or TOKEN == "seu_token_aqui":
        print("❌ ERRO: O Token do bot não foi configurado!")
        print("👉 Preencha o arquivo .env com seu DISCORD_TOKEN.")
        return

    async with bot:
        await carregar_modulos()
        await bot.start(TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot desligado com sucesso.")
