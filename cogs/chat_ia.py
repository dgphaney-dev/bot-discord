import asyncio
from collections import defaultdict
import json
import logging
from pathlib import Path
import re
import aiohttp
import discord
from discord.ext import commands

from config import (
    Cores,
    GEMINI_API_KEY,
    GEMINI_MODELO,
    IA_MAX_HISTORICO,
    IA_SYSTEM_PROMPT,
    PREFIXO,
    TEMPO_DELETE_ERRO,
    TEMPO_DELETE_SUCESSO,
)
from utils.helpers import tem_permissao_acao, tentar_deletar_mensagem

logger = logging.getLogger("bot.chat_ia")

# Arquivos para persistência de dados
ARQUIVO_CANAL_IA = Path(__file__).resolve().parent.parent / "data" / "chat_ia.json"
ARQUIVO_PERSONALIDADE_IA = Path(__file__).resolve().parent.parent / "data" / "personalidade_ia.json"

# Personagens pré-configurados para escolha rápida
PRESETS_PERSONALIDADE = {
    "aspas": {
        "nome": "Aspas",
        "descricao": "astro e pro player de Valorant, calmo, humilde e focado",
        "girias": "pô mano, tô suave, se liga, é só clicar na cabeça, tá safe, nois amassa",
        "estilo": "Respostas muito curtas (1 a 2 frases), descontraídas, estilo pro player em live",
        "emoji": "🎯",
        "cor": "#00E5FF"
    },
    "casimiro": {
        "nome": "Casimiro (Cazé)",
        "descricao": "streamer carismático, apaixonado por futebol e zoeira",
        "girias": "meteu essa?, papo reto, que isso hein, tá maluco, aceitas?, vasco",
        "estilo": "Espantado, bem-humorado, gírias cariocas, respostas curtas e engraçadas",
        "emoji": "🍔",
        "cor": "#FFD700"
    },
    "coringa": {
        "nome": "Victor Coringa",
        "descricao": "streamer da LOUD, zueiro, debochado e gargalhando",
        "girias": "hahaha, que resenha, meu Deus do céu, esquece, amassa",
        "estilo": "Zoeira pura, dando risada, gírias da Loud, respostas curtas e animadas",
        "emoji": "🤡",
        "cor": "#00FF22"
    },
    "nerd": {
        "nome": "Dev Sênior / Hacker",
        "descricao": "programador inteligente, sarcástico e focado em tecnologia",
        "girias": "compilou, bug na matrix, roda no meu pc, deploy na sexta, 404, gg",
        "estilo": "Focado em lógica, código, sarcástico, direto e muito curto",
        "emoji": "💻",
        "cor": "#9B59B6"
    }
}


def carregar_dados_json(caminho: Path) -> dict:
    """Carrega dados JSON com tratamento de erro."""
    if not caminho.exists():
        return {}
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Erro ao carregar {caminho}: {e}")
        return {}


def salvar_dados_json(caminho: Path, dados: dict):
    """Salva dados JSON criando pastas necessárias."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)


# ========================================================
# MODAL PARA CRIAR/CUSTOMIZAR PERSONAGEM DA IA
# ========================================================
class ModalCriarPersonagem(discord.ui.Modal, title="🎭 Customizar Personagem da IA"):
    nome = discord.ui.TextInput(
        label="Nome do Personagem",
        placeholder="Ex: Aspas, Casimiro, Neymar, etc.",
        max_length=40,
        required=True
    )
    descricao = discord.ui.TextInput(
        label="Quem ele é / Descrição",
        placeholder="Ex: Jogador profissional de Valorant, calmo e humilde",
        max_length=150,
        required=True
    )
    girias = discord.ui.TextInput(
        label="Gírias e Expressões",
        placeholder="Ex: pô mano, tô suave, se liga, tá safe, nois amassa",
        max_length=200,
        required=True
    )
    estilo = discord.ui.TextInput(
        label="Estilo de Resposta",
        placeholder="Ex: Muito curto (1 a 2 frases), descontraído",
        default="Muito curto (1 a 2 frases), descontraído e direto ao ponto",
        max_length=150,
        required=True
    )

    def __init__(self, cog, guild_id: int):
        super().__init__()
        self.cog = cog
        self.guild_id = guild_id

    async def on_submit(self, interaction: discord.Interaction):
        dados_personagem = {
            "nome": self.nome.value.strip(),
            "descricao": self.descricao.value.strip(),
            "girias": self.girias.value.strip(),
            "estilo": self.estilo.value.strip()
        }
        self.cog.personalidades[str(self.guild_id)] = dados_personagem
        salvar_dados_json(ARQUIVO_PERSONALIDADE_IA, self.cog.personalidades)

        embed = discord.Embed(
            title="🎭 Personagem da IA Configurado!",
            description=(
                f"A partir de agora a IA vai agir e conversar como **{dados_personagem['nome']}**!\n\n"
                f"👤 **Quem é:** {dados_personagem['descricao']}\n"
                f"🗣️ **Gírias:** `{dados_personagem['girias']}`\n"
                f"⚡ **Estilo:** {dados_personagem['estilo']}\n\n"
                "*(Ela continua sabendo de tudo: programação, matemática, jogos, etc., mas no estilo dele!)*"
            ),
            color=Cores.SUCESSO
        )
        embed.set_footer(text="Mencione o bot para bater um papo com o novo personagem!")
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ========================================================
# SELECT MENU PARA PRESETS DE PERSONAGENS
# ========================================================
class SelectPresetPersonagem(discord.ui.Select):
    def __init__(self, cog, guild_id: int):
        self.cog = cog
        self.guild_id = guild_id

        opcoes = []
        for chave, p in PRESETS_PERSONALIDADE.items():
            opcoes.append(
                discord.SelectOption(
                    label=p["nome"],
                    description=p["descricao"][:95],
                    emoji=p["emoji"],
                    value=chave
                )
            )

        super().__init__(
            placeholder="Escolha um personagem pronto para a IA...",
            min_values=1,
            max_values=1,
            options=opcoes
        )

    async def callback(self, interaction: discord.Interaction):
        chave = self.values[0]
        preset = PRESETS_PERSONALIDADE.get(chave)
        if not preset:
            return

        dados_personagem = {
            "nome": preset["nome"],
            "descricao": preset["descricao"],
            "girias": preset["girias"],
            "estilo": preset["estilo"]
        }
        self.cog.personalidades[str(self.guild_id)] = dados_personagem
        salvar_dados_json(ARQUIVO_PERSONALIDADE_IA, self.cog.personalidades)

        cor_hex = preset.get("cor", "#5865F2")
        cor_embed = discord.Color.from_str(cor_hex)

        embed = discord.Embed(
            title=f"{preset['emoji']} Personagem Definido: {preset['nome']}!",
            description=(
                f"A IA agora assumiu a personalidade de **{preset['nome']}**!\n\n"
                f"👤 **Perfil:** {preset['descricao']}\n"
                f"🗣️ **Gírias:** `{preset['girias']}`\n"
                f"⚡ **Estilo:** {preset['estilo']}\n\n"
                "*(Responde a qualquer assunto com esse jeitão e respostas curtas)*"
            ),
            color=cor_embed
        )
        embed.set_footer(text="Mencione o bot no chat para ver ele falando nesse estilo!")
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ========================================================
# VIEW DO PAINEL DE PERSONALIDADE
# ========================================================
class ViewPainelPersonalidade(discord.ui.View):
    def __init__(self, cog, guild_id: int, autor_id: int):
        super().__init__(timeout=120)
        self.cog = cog
        self.guild_id = guild_id
        self.autor_id = autor_id
        self.add_item(SelectPresetPersonagem(cog, guild_id))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.autor_id and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Apenas o autor do comando pode usar este menu.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Customizar Personagem Próprio", style=discord.ButtonStyle.primary, emoji="✏️")
    async def botao_customizar(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = ModalCriarPersonagem(self.cog, self.guild_id)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Resetar para o Padrão (Aspas)", style=discord.ButtonStyle.secondary, emoji="🔄")
    async def botao_resetar(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id_str = str(self.guild_id)
        if guild_id_str in self.cog.personalidades:
            del self.cog.personalidades[guild_id_str]
            salvar_dados_json(ARQUIVO_PERSONALIDADE_IA, self.cog.personalidades)

        embed = discord.Embed(
            title="🔄 Personagem Resetado!",
            description="A IA voltou para o padrão: **Aspas (Erick Santos)**, astro do Valorant!",
            color=Cores.SUCESSO
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ========================================================
# COG PRINCIPAL DE CHAT COM IA
# ========================================================
class ChatIA(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.historicos = defaultdict(list)
        self.config_canais = carregar_dados_json(ARQUIVO_CANAL_IA)
        self.personalidades = carregar_dados_json(ARQUIVO_PERSONALIDADE_IA)

    def obter_canal_ia(self, guild_id: int) -> int | None:
        """Retorna o ID do canal exclusivo de IA configurado para a guilda."""
        dados = self.config_canais.get(str(guild_id), {})
        return dados.get("canal_id")

    def obter_personagem(self, guild_id: int) -> dict:
        """Retorna os dados do personagem ativo para o servidor."""
        return self.personalidades.get(str(guild_id), PRESETS_PERSONALIDADE["aspas"])

    def construir_prompt_sistema(self, guild_id: int) -> str:
        """Gera a instrução do sistema dinâmica com o personagem e gírias do servidor."""
        p = self.obter_personagem(guild_id)
        prompt = (
            f"Você é {p['nome']}, {p['descricao']}. "
            "Você é uma Inteligência Artificial completa no Discord e sabe de absolutamente TUDO o que perguntarem: "
            "programação (Python, JS, etc.), matemática, biologia, física, química, história, jogos, Valorant, tecnologia e vida. "
            "REGRA OBRIGATÓRIA E INEGOCIÁVEL: Dê SEMPRE respostas MUITO CURTAS (no máximo 1 a 2 frases breves, direto ao ponto). "
            "NUNCA mande textões, parágrafos compridos ou listas longas. "
            f"Estilo de diálogo: {p.get('estilo', 'curto e direto')}. "
            f"Gírias e expressões que você sempre usa: {p.get('girias', 'pô mano, tô suave, tá safe')}. "
            "Encarne 100% esse personagem, respondendo com total sabedoria e exatidão, mas no vocabulário dele em português do Brasil."
        )
        return prompt

    def sanitizar_historico(self, historico: list[dict]) -> list[dict]:
        """Garante que o histórico alterne estritamente entre user e model para a API do Gemini."""
        valido = []
        ultimo_papel = None
        for item in historico:
            papel = item.get("role")
            partes = item.get("parts", [])
            if papel in ("user", "model") and partes and partes[0].get("text"):
                if papel != ultimo_papel:
                    valido.append(item)
                    ultimo_papel = papel
        while valido and valido[0]["role"] != "user":
            valido.pop(0)
        while valido and valido[-1]["role"] != "user":
            valido.pop()
        return valido

    async def gerar_resposta_gemini(self, historico: list[dict], guild_id: int) -> tuple[str | None, str | None]:
        """Envia o histórico com o prompt do personagem para a API do Gemini com fallback rápido."""
        api_key = GEMINI_API_KEY
        if not api_key:
            return None, "CHAVE_NAO_CONFIGURADA"

        # Modelos disponíveis na API do Gemini em ordem de velocidade e estabilidade
        modelos = [
            GEMINI_MODELO,
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
        ]
        modelos_unicos = []
        for m in modelos:
            if m and m not in modelos_unicos:
                modelos_unicos.append(m)

        historico_valido = self.sanitizar_historico(historico)
        if not historico_valido:
            return "Opa, não entendi muito bem. Fala de novo?", None

        prompt_sistema = self.construir_prompt_sistema(guild_id)

        corpo_requisicao = {
            "system_instruction": {
                "parts": [{"text": prompt_sistema}]
            },
            "contents": historico_valido,
            "generationConfig": {
                "temperature": 0.8,
                "maxOutputTokens": 200,
            }
        }

        async with aiohttp.ClientSession() as session:
            for modelo in modelos_unicos:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
                try:
                    import time
                    t0 = time.time()
                    async with session.post(url, json=corpo_requisicao, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                        dt = time.time() - t0
                        if resp.status == 200:
                            dados = await resp.json()
                            candidatos = dados.get("candidates", [])
                            if not candidatos:
                                continue

                            partes = candidatos[0].get("content", {}).get("parts", [])
                            if partes and "text" in partes[0]:
                                texto = partes[0]["text"].strip()
                                print(f"[IA] ✅ Respondido via {modelo} em {dt:.2f}s", flush=True)
                                return texto, None
                            continue

                        elif resp.status in (400, 403):
                            dados_erro = await resp.text()
                            if "API_KEY_INVALID" in dados_erro or resp.status == 403:
                                return None, "CHAVE_INVALIDA"
                            print(f"[IA] ⚠️ Erro {resp.status} em {modelo}: {dados_erro[:80]}", flush=True)
                            continue

                        else:
                            print(f"[IA] ⚠️ Status {resp.status} em {modelo}. Tentando próximo...", flush=True)
                            continue

                except asyncio.TimeoutError:
                    print(f"[IA] ⏱️ Timeout em {modelo} (7s). Tentando próximo...", flush=True)
                    continue
                except Exception as e:
                    print(f"[IA] ❌ Exceção em {modelo}: {e}", flush=True)
                    continue

        return "Eita, deu um tilt rápido aqui no raciocínio. Manda de novo que agora vai!", None

    def limpar_mencao_bot(self, texto: str) -> str:
        """Remove a menção do bot (<@ID> ou <@!ID>) do início ou meio da mensagem."""
        if not self.bot.user:
            return texto.strip()
        padrao = rf"<@!?{self.bot.user.id}>"
        return re.sub(padrao, "", texto).strip()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Monitora mensagens para responder menções, replies e canal de IA."""
        if message.author.bot or not message.guild:
            return

        if message.content.startswith(PREFIXO):
            return

        canal_ia_id = self.obter_canal_ia(message.guild.id)
        bot_mencionado = self.bot.user in message.mentions and not message.mention_everyone

        e_resposta_ao_bot = False
        if message.reference and message.reference.message_id:
            try:
                msg_ref = message.reference.resolved
                if not msg_ref and message.reference.channel_id:
                    canal_origem = message.guild.get_channel(message.reference.channel_id)
                    if canal_origem:
                        msg_ref = await canal_origem.fetch_message(message.reference.message_id)
                if msg_ref and msg_ref.author.id == self.bot.user.id:
                    e_resposta_ao_bot = True
            except Exception:
                e_resposta_ao_bot = False

        e_canal_ia = (canal_ia_id is not None and message.channel.id == canal_ia_id)

        if not (bot_mencionado or e_resposta_ao_bot or e_canal_ia):
            return

        texto_usuario = self.limpar_mencao_bot(message.content)
        print(f"[IA] 📩 Mensagem recebida de {message.author.name}: {texto_usuario}", flush=True)

        if not texto_usuario and bot_mencionado:
            personagem = self.obter_personagem(message.guild.id)
            respostas_curtas = [
                f"Fala comigo! O que manda?",
                f"Tô na área! Só falar.",
                f"Opa, chamou? Em que posso te ajudar?"
            ]
            import random
            await message.reply(random.choice(respostas_curtas), mention_author=False)
            return

        if not texto_usuario:
            return

        if not GEMINI_API_KEY:
            embed_aviso = discord.Embed(
                title="🤖 Inteligência Artificial",
                description="A chave de API gratuita ainda não foi configurada no `.env`.",
                color=Cores.AVISO
            )
            await message.reply(embed=embed_aviso, mention_author=False, delete_after=20)
            return

        async with message.channel.typing():
            historico_canal = self.historicos[message.channel.id]
            historico_canal.append({
                "role": "user",
                "parts": [{"text": f"{message.author.display_name}: {texto_usuario}"}]
            })

            if len(historico_canal) > IA_MAX_HISTORICO * 2:
                self.historicos[message.channel.id] = historico_canal[-IA_MAX_HISTORICO * 2:]
                historico_canal = self.historicos[message.channel.id]

            resposta, erro = await self.gerar_resposta_gemini(historico_canal, message.guild.id)

            if erro == "CHAVE_INVALIDA":
                embed_err = discord.Embed(
                    title="❌ Chave da API Inválida",
                    description="A chave `GEMINI_API_KEY` configurada no arquivo `.env` é inválida.",
                    color=Cores.ERRO
                )
                await message.reply(embed=embed_err, mention_author=False, delete_after=20)
                if historico_canal and historico_canal[-1]["role"] == "user":
                    historico_canal.pop()
                return

            if not resposta or "tilt rápido" in resposta:
                if historico_canal and historico_canal[-1]["role"] == "user":
                    historico_canal.pop()
                msg_aviso = resposta or "Eita, deu um tilt aqui agora. Manda de novo?"
                await message.reply(msg_aviso, mention_author=False)
                return

            historico_canal.append({
                "role": "model",
                "parts": [{"text": resposta}]
            })

            if len(resposta) <= 2000:
                await message.reply(resposta, mention_author=False)
            else:
                for chunk in [resposta[i:i + 1990] for i in range(0, len(resposta), 1990)]:
                    await message.reply(chunk, mention_author=False)

    # ========================================================
    # COMANDO: PAINEL INTERATIVO DE PERSONAGEM (!personagem / !personalidade)
    # ========================================================
    @commands.command(name="personagem", aliases=["personalidade", "setpersonagem", "iapersonagem"])
    async def painel_personagem(self, ctx):
        """Abre o menu interativo para escolher ou customizar a personalidade da IA."""
        await tentar_deletar_mensagem(ctx)

        if not tem_permissao_acao(ctx, "customizacao") and not ctx.author.guild_permissions.administrator:
            embed = discord.Embed(
                title="❌ Sem Permissão",
                description="Você precisa de permissão de Administrador ou do cargo de customização para alterar a personalidade da IA.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        atual = self.obter_personagem(ctx.guild.id)

        embed = discord.Embed(
            title="🎭 Configuração de Personagem da IA",
            description=(
                "Escolha quem a IA é para conversar no servidor! Ela adotará o nome, jeito de falar, "
                "gírias e tom de voz do personagem que você definir.\n\n"
                f"📌 **Personagem Ativo:** **{atual['nome']}**\n"
                f"📝 **Perfil:** {atual['descricao']}\n"
                f"🗣️ **Gírias:** `{atual.get('girias', 'padrão')}`\n"
                f"⚡ **Estilo:** {atual.get('estilo', 'curto e direto')}\n\n"
                "👇 **Escolha um personagem pronto no menu abaixo ou clique no botão para criar o seu próprio:**"
            ),
            color=Cores.INFO
        )
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.set_footer(text="A IA continuará sabendo de tudo, mas sempre falará com a vibe desse personagem!")

        view = ViewPainelPersonalidade(self, ctx.guild.id, ctx.author.id)
        await ctx.send(embed=embed, view=view, delete_after=180)

    # ========================================================
    # COMANDO: CANAL EXCLUSIVO DE IA (!setcanalia)
    # ========================================================
    @commands.command(name="setcanalia", aliases=["canalia", "ia_canal"])
    async def set_canal_ia(self, ctx, canal: discord.TextChannel | str = None):
        """Define ou desativa um canal exclusivo onde a IA conversa sem precisar ser marcada."""
        await tentar_deletar_mensagem(ctx)

        if not tem_permissao_acao(ctx, "customizacao") and not ctx.author.guild_permissions.administrator:
            embed = discord.Embed(
                title="❌ Sem Permissão",
                description="Você precisa de permissão de Administrador para configurar o canal da IA.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        guild_id_str = str(ctx.guild.id)

        if isinstance(canal, str) and canal.lower() in ["remover", "desativar", "off", "none", "reset"]:
            if guild_id_str in self.config_canais:
                self.config_canais.pop(guild_id_str, None)
                salvar_dados_json(ARQUIVO_CANAL_IA, self.config_canais)

            embed = discord.Embed(
                title="🗑️ Canal de IA Desativado",
                description="O canal exclusivo foi desativado. O bot agora responde apenas quando for mencionado ou respondido.",
                color=Cores.SUCESSO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_SUCESSO)
            return

        if isinstance(canal, discord.TextChannel):
            self.config_canais[guild_id_str] = {"canal_id": canal.id}
            salvar_dados_json(ARQUIVO_CANAL_IA, self.config_canais)

            embed = discord.Embed(
                title="🤖 Canal da IA Configurado!",
                description=(
                    f"O canal {canal.mention} agora é o canal exclusivo de Inteligência Artificial!\n\n"
                    "Qualquer mensagem enviada lá será respondida pelo bot diretamente, sem precisar marcá-lo."
                ),
                color=Cores.SUCESSO
            )
            embed.set_footer(text=f"Use '{PREFIXO}setcanalia remover' para desativar a qualquer momento.")
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_SUCESSO)
            return

        canal_atual_id = self.obter_canal_ia(ctx.guild.id)
        canal_atual = ctx.guild.get_channel(canal_atual_id) if canal_atual_id else None

        embed = discord.Embed(
            title="🤖 Status do Canal de IA",
            description=(
                f"**Canal Atual:** {canal_atual.mention if canal_atual else '*Nenhum canal exclusivo configurado*'}\n\n"
                f"**Como configurar:**\n"
                f"• `{PREFIXO}setcanalia #nome-do-canal` - Ativa o canal exclusivo\n"
                f"• `{PREFIXO}setcanalia remover` - Desativa o canal exclusivo"
            ),
            color=Cores.INFO
        )
        await ctx.send(embed=embed, delete_after=30)

    # ========================================================
    # COMANDO: LIMPAR MEMÓRIA/HISTÓRICO DA CONVERSA (!limparconversa)
    # ========================================================
    @commands.command(name="limparconversa", aliases=["resetia", "resetconversa"])
    async def limpar_conversa(self, ctx):
        """Limpa o histórico recente de memória da IA no canal atual."""
        await tentar_deletar_mensagem(ctx)

        if ctx.channel.id in self.historicos:
            del self.historicos[ctx.channel.id]

        embed = discord.Embed(
            title="🧹 Memória da IA Reiniciada",
            description="O histórico de conversas recente deste canal foi limpo com sucesso! A IA iniciará um novo assunto.",
            color=Cores.SUCESSO
        )
        await ctx.send(embed=embed, delete_after=TEMPO_DELETE_SUCESSO)


async def setup(bot):
    await bot.add_cog(ChatIA(bot))
