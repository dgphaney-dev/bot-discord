"""
Servidor Web Integrado para o Painel do Bot Discord.
Permite visualizar e gerenciar o dashboard via navegador na porta configurada (padrão: 8080).
"""
import os
import asyncio
from pathlib import Path
from aiohttp import web

PASTA_WEB = Path(__file__).resolve().parent
ARQUIVO_HTML = PASTA_WEB / "dashboard.html"


async def handle_index(request):
    """Serve a página principal do dashboard moderno."""
    if not ARQUIVO_HTML.exists():
        return web.Response(text="Página do painel não encontrada.", status=404)
    with open(ARQUIVO_HTML, "r", encoding="utf-8") as f:
        html = f.read()
    return web.Response(text=html, content_type="text/html")


async def handle_api_status(request):
    """Endpoint de status do sistema e bot."""
    bot = request.app.get("bot")
    latencia = round(bot.latency * 1000) if bot else 0
    guilds_count = len(bot.guilds) if bot else 0

    dados = {
        "online": True if bot and bot.is_ready() else False,
        "latencia_ms": latencia,
        "servidores": guilds_count,
        "versao": "2.0.0"
    }
    return web.json_response(dados)


def criar_app_web(bot=None):
    """Cria a aplicação web aiohttp."""
    app = web.Application()
    app["bot"] = bot
    app.router.add_get("/", handle_index)
    app.router.add_get("/dashboard", handle_index)
    app.router.add_get("/api/status", handle_api_status)
    return app


async def iniciar_servidor_web(bot=None, porta=None):
    """Inicia o servidor de forma assíncrona em segundo plano."""
    porta = porta or int(os.getenv("PORT", "8080"))
    app = criar_app_web(bot)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", porta)
    try:
        await site.start()
        print(f"🌐 [Dashboard Web] Servidor online em http://localhost:{porta}")
    except Exception as e:
        print(f"⚠️ Não foi possível iniciar o dashboard web na porta {porta}: {e}")


if __name__ == "__main__":
    web.run_app(criar_app_web(), port=8080)
