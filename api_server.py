import asyncio
import os
import sys
from pathlib import Path
from aiohttp import web

# Garante path
diretorio_base = Path(__file__).resolve().parent
if str(diretorio_base) not in sys.path:
    sys.path.insert(0, str(diretorio_base))

from cogs.api_server import APIServerCog
from utils.console_stream import ConsoleStream

class DummyUser:
    display_avatar = type("Avatar", (), {"url": "https://cdn.discordapp.com/embed/avatars/0.png"})()

class DummyBot:
    def __init__(self):
        self.guilds = []
        self.latency = 0.012
        self.user = DummyUser()

async def main():
    port = int(os.getenv("PORT", 8000))
    dummy_bot = DummyBot()
    cog = APIServerCog(dummy_bot)
    ConsoleStream.log("SYSTEM", "Modo Standalone da API Cypher X iniciado.")
    ConsoleStream.log("INIT", "Carregando configurações de servidores locais...")
    ConsoleStream.log("DONE", "Servidor de desenvolvimento pronto!")
    
    runner = web.AppRunner(cog.app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"🚀 [Cypher X API - Standalone] Rodando em http://127.0.0.1:{port}")
    print("Pressione Ctrl+C para encerrar.")
    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
