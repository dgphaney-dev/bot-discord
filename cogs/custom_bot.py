import asyncio
import aiohttp
import discord
from discord.ext import commands
from config import (
    Cores,
    PREFIXO,
    STATUS_DISCORD,
    TEMPO_DELETE_ERRO,
    TEMPO_DELETE_SUCESSO,
    obter_atividade_texto,
    obter_prefixo_salvo,
    salvar_prefixo_arquivo,
)
from utils.helpers import tem_permissao_acao, tentar_deletar_mensagem


async def obter_bytes_imagem(ctx, link: str = None) -> tuple[bytes | None, str | None]:
    """
    Extrai com segurança os bytes de uma imagem tanto de um anexo quanto de um link direto.
    Retorna (bytes, mensagem_de_erro).
    """
    # 1. Se o usuário enviou uma imagem anexada
    if ctx.message.attachments:
        anexo = ctx.message.attachments[0]
        extensao = anexo.filename.lower().split(".")[-1]
        extensoes_validas = ["png", "jpg", "jpeg", "gif", "webp"]

        if extensao not in extensoes_validas:
            return None, (
                "Formato de imagem não suportado. "
                f"Envie um arquivo `.png`, `.jpg`, `.jpeg`, `.gif` ou `.webp` (você enviou `.{extensao}`)."
            )

        # Limite de 10 MB
        if anexo.size > 10 * 1024 * 1024:
            return None, "O arquivo anexado é muito grande. O limite máximo do Discord é de **10 MB**."

        try:
            dados = await anexo.read()
            return dados, None
        except Exception as e:
            return None, f"Falha ao ler o anexo enviado: `{e}`"

    # 2. Se o usuário forneceu uma URL
    if link:
        # Limpa possíveis delimitadores como <link> ou espaços
        url = link.strip("<> \t\n\r")
        if not (url.startswith("http://") or url.startswith("https://")):
            return None, "A URL informada deve começar com `http://` ou `https://`."

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
        }

        try:
            timeout = aiohttp.ClientTimeout(total=20)
            async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
                async with session.get(url) as resposta:
                    if resposta.status != 200:
                        return None, f"O servidor da imagem retornou erro HTTP `{resposta.status}`."

                    tipo_conteudo = resposta.headers.get("Content-Type", "").lower()
                    if tipo_conteudo and not any(ext in tipo_conteudo for ext in ["image", "octet-stream"]):
                        return None, (
                            "O link fornecido não parece ser de uma imagem direta. "
                            f"(Tipo detectado: `{tipo_conteudo}`)."
                        )

                    dados = await resposta.read()
                    if len(dados) > 10 * 1024 * 1024:
                        return None, "A imagem ultrapassa o limite máximo de **10 MB**."

                    return dados, None

        except asyncio.TimeoutError:
            return None, "O download da imagem demorou muito e expirou o tempo limite (Timeout)."
        except Exception as e:
            return None, f"Erro ao baixar a imagem do link fornecido:\n`{e}`"

    return None, "Você precisa **anexar uma imagem** com o comando ou **colar o link direto** dela."


class Customizacao(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ========================================================
    # COMANDO: AVATAR DO BOT
    # ========================================================
    @commands.command(name="avatar_bot", aliases=["foto_bot", "setavatar"])
    async def avatar_bot(self, ctx, link: str = None):
        """
        Altera a foto de perfil (avatar) do bot.
        Pode receber um anexo, um link direto ou a palavra 'remover' para redefinir.
        """
        await tentar_deletar_mensagem(ctx)

        if not tem_permissao_acao(ctx, "customizacao"):
            embed = discord.Embed(
                title="❌ Sem Permissão",
                description="Você precisa de permissão de Administrador ou do cargo configurado para alterar o avatar do bot.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        # Opção para remover/redefinir o avatar
        if link and link.lower() in ["remover", "reset", "deletar", "padrao"]:
            try:
                await self.bot.user.edit(avatar=None)
                embed_reset = discord.Embed(
                    title="🖼️ Avatar Redefinido!",
                    description=f"O avatar do bot foi redefinido para o padrão por {ctx.author.mention}.",
                    color=Cores.SUCESSO
                )
                await ctx.send(embed=embed_reset, delete_after=TEMPO_DELETE_SUCESSO)
                return
            except Exception as e:
                embed_erro = discord.Embed(
                    title="❌ Falha ao Redefinir Avatar",
                    description=f"Ocorreu um erro:\n`{e}`",
                    color=Cores.ERRO
                )
                await ctx.send(embed=embed_erro, delete_after=TEMPO_DELETE_ERRO)
                return

        # Baixa os bytes da imagem
        imagem_bytes, erro = await obter_bytes_imagem(ctx, link)
        if erro:
            embed_erro = discord.Embed(
                title="❌ Entrada Inválida",
                description=erro,
                color=Cores.ERRO
            )
            await ctx.send(embed=embed_erro, delete_after=TEMPO_DELETE_ERRO)
            return

        msg_processando = await ctx.send(
            embed=discord.Embed(
                title="⚙️ Processando Alteração",
                description="Atualizando o avatar do bot no Discord...",
                color=Cores.INFO
            )
        )

        try:
            await self.bot.user.edit(avatar=imagem_bytes)
            await msg_processando.delete()

            embed_sucesso = discord.Embed(
                title="🖼️ Avatar Atualizado com Sucesso!",
                description=f"A foto de perfil do bot foi alterada por {ctx.author.mention}.",
                color=Cores.SUCESSO
            )
            embed_sucesso.set_image(url=self.bot.user.display_avatar.url)
            embed_sucesso.set_footer(text="A propagação global no Discord pode demorar alguns segundos.")
            await ctx.send(embed=embed_sucesso, delete_after=TEMPO_DELETE_SUCESSO)

        except discord.HTTPException as e:
            await msg_processando.delete()
            if getattr(e, "code", None) == 50035 or "Invalid Form Body" in str(e):
                embed_aviso = discord.Embed(
                    title="❌ Imagem Rejeitada pelo Discord",
                    description="O formato ou as dimensões da imagem foram rejeitados. Tente enviar uma imagem PNG ou JPEG padrão.",
                    color=Cores.ERRO
                )
                await ctx.send(embed=embed_aviso, delete_after=TEMPO_DELETE_ERRO)
            elif e.status == 429 or "rate limited" in str(e).lower():
                embed_limite = discord.Embed(
                    title="⚠️ Limite de Alterações Excedido",
                    description="O Discord limita a frequência de troca de avatares. Aguarde alguns minutos antes de tentar novamente.",
                    color=Cores.AVISO
                )
                await ctx.send(embed=embed_limite, delete_after=TEMPO_DELETE_ERRO)
            else:
                embed_api = discord.Embed(
                    title="❌ Erro na API do Discord",
                    description=f"Falha ao salvar o novo avatar:\n`{e}`",
                    color=Cores.ERRO
                )
                await ctx.send(embed=embed_api, delete_after=TEMPO_DELETE_ERRO)

        except ValueError as e:
            await msg_processando.delete()
            embed_val = discord.Embed(
                title="❌ Formato Inválido",
                description=f"O Discord não aceitou este formato de imagem: `{e}`",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed_val, delete_after=TEMPO_DELETE_ERRO)

        except Exception as e:
            await msg_processando.delete()
            embed_geral = discord.Embed(
                title="❌ Erro Inesperado",
                description=f"Ocorreu um erro inesperado ao alterar o avatar:\n`{e}`",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed_geral, delete_after=TEMPO_DELETE_ERRO)

    @avatar_bot.error
    async def avatar_bot_error(self, ctx, error):
        await tentar_deletar_mensagem(ctx)
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Permissão Negada",
                description="Apenas **Administradores** podem alterar o avatar do bot.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)

    # ========================================================
    # COMANDO: BANNER DO BOT
    # ========================================================
    @commands.command(name="banner_bot", aliases=["banner", "setbanner"])
    async def banner_bot(self, ctx, link: str = None):
        """
        Altera o banner de perfil do bot.
        Pode receber um anexo, um link direto ou 'remover' para retirar o banner.
        """
        await tentar_deletar_mensagem(ctx)

        if not tem_permissao_acao(ctx, "customizacao"):
            embed = discord.Embed(
                title="❌ Sem Permissão",
                description="Você precisa de permissão de Administrador ou do cargo configurado para alterar o banner do bot.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        # Opção para remover/redefinir o banner
        if link and link.lower() in ["remover", "reset", "deletar", "limpar"]:
            try:
                await self.bot.user.edit(banner=None)
                embed_reset = discord.Embed(
                    title="🎨 Banner Removido!",
                    description=f"O banner do bot foi removido por {ctx.author.mention}.",
                    color=Cores.SUCESSO
                )
                await ctx.send(embed=embed_reset, delete_after=TEMPO_DELETE_SUCESSO)
                return
            except Exception as e:
                embed_erro = discord.Embed(
                    title="❌ Falha ao Remover Banner",
                    description=f"Ocorreu um erro ao retirar o banner:\n`{e}`",
                    color=Cores.ERRO
                )
                await ctx.send(embed=embed_erro, delete_after=TEMPO_DELETE_ERRO)
                return

        # Baixa os bytes da imagem
        imagem_bytes, erro = await obter_bytes_imagem(ctx, link)
        if erro:
            embed_erro = discord.Embed(
                title="❌ Entrada Inválida",
                description=erro,
                color=Cores.ERRO
            )
            await ctx.send(embed=embed_erro, delete_after=TEMPO_DELETE_ERRO)
            return

        msg_processando = await ctx.send(
            embed=discord.Embed(
                title="⚙️ Processando Alteração",
                description="Atualizando o banner do bot no Discord...",
                color=Cores.INFO
            )
        )

        try:
            await self.bot.user.edit(banner=imagem_bytes)
            await msg_processando.delete()

            embed_sucesso = discord.Embed(
                title="🎨 Banner Atualizado com Sucesso!",
                description=f"O banner do bot foi alterado por {ctx.author.mention}.",
                color=Cores.SUCESSO
            )
            # Se o bot tiver banner público acessível, exibe no embed
            usuario_atualizado = await self.bot.fetch_user(self.bot.user.id)
            if usuario_atualizado.banner:
                embed_sucesso.set_image(url=usuario_atualizado.banner.url)

            embed_sucesso.set_footer(text="A alteração pode demorar alguns instantes para sincronizar no perfil.")
            await ctx.send(embed=embed_sucesso, delete_after=TEMPO_DELETE_SUCESSO)

        except discord.HTTPException as e:
            await msg_processando.delete()
            if getattr(e, "code", None) == 50035 or "Invalid Form Body" in str(e):
                embed_aviso = discord.Embed(
                    title="❌ Banner Rejeitado",
                    description="O Discord rejeitou a imagem do banner. Recomenda-se resolução retangular (ex: 600x240) em PNG ou JPEG.",
                    color=Cores.ERRO
                )
                await ctx.send(embed=embed_aviso, delete_after=TEMPO_DELETE_ERRO)
            elif e.status == 429 or "rate limited" in str(e).lower():
                embed_limite = discord.Embed(
                    title="⚠️ Limite de Alterações Excedido",
                    description="Muitas alterações em pouco tempo. Aguarde alguns minutos antes de trocar o banner novamente.",
                    color=Cores.AVISO
                )
                await ctx.send(embed=embed_limite, delete_after=TEMPO_DELETE_ERRO)
            else:
                embed_api = discord.Embed(
                    title="❌ Erro na API do Discord",
                    description=f"Falha ao salvar o novo banner:\n`{e}`",
                    color=Cores.ERRO
                )
                await ctx.send(embed=embed_api, delete_after=TEMPO_DELETE_ERRO)

        except ValueError as e:
            await msg_processando.delete()
            embed_val = discord.Embed(
                title="❌ Formato Inválido",
                description=f"Formato inválido para banner: `{e}`",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed_val, delete_after=TEMPO_DELETE_ERRO)

        except Exception as e:
            await msg_processando.delete()
            embed_geral = discord.Embed(
                title="❌ Erro Inesperado",
                description=f"Ocorreu um erro ao trocar o banner:\n`{e}`",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed_geral, delete_after=TEMPO_DELETE_ERRO)

    @banner_bot.error
    async def banner_bot_error(self, ctx, error):
        await tentar_deletar_mensagem(ctx)
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Permissão Negada",
                description="Apenas **Administradores** podem alterar o banner do bot.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)

    # ========================================================
    # COMANDO: NOME DO BOT
    # ========================================================
    @commands.command(name="nome_bot", aliases=["setname", "nomebot"])
    async def nome_bot(self, ctx, *, novo_nome: str = None):
        """Altera o nome de usuário (username) do bot."""
        await tentar_deletar_mensagem(ctx)

        if not tem_permissao_acao(ctx, "customizacao"):
            embed = discord.Embed(
                title="❌ Sem Permissão",
                description="Você precisa de permissão de Administrador ou do cargo configurado para alterar o nome do bot.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        if not novo_nome or not novo_nome.strip():
            embed_erro = discord.Embed(
                title="❌ Nome Não Informado",
                description="Você precisa informar o novo nome que deseja aplicar!\n\n**Exemplo:** `!nome_bot Meu Super Bot`",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed_erro, delete_after=TEMPO_DELETE_ERRO)
            return

        novo_nome = novo_nome.strip()

        if len(novo_nome) < 2:
            embed_erro = discord.Embed(
                title="❌ Nome Muito Curto",
                description="O nome do bot precisa ter pelo menos **2** caracteres.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed_erro, delete_after=TEMPO_DELETE_ERRO)
            return

        if len(novo_nome) > 32:
            embed_erro = discord.Embed(
                title="❌ Nome Muito Longo",
                description="O nome do bot não pode ter mais de **32** caracteres.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed_erro, delete_after=TEMPO_DELETE_ERRO)
            return

        if novo_nome == self.bot.user.name:
            embed_aviso = discord.Embed(
                title="⚠️ Nome Idêntico",
                description="O nome informado já é o nome atual do bot.",
                color=Cores.AVISO
            )
            await ctx.send(embed=embed_aviso, delete_after=TEMPO_DELETE_ERRO)
            return

        # Caracteres proibidos pelas regras do Discord para usernames
        caracteres_proibidos = ["@", "#", ":", "```"]
        if any(char in novo_nome for char in caracteres_proibidos):
            embed_erro = discord.Embed(
                title="❌ Caracteres Inválidos",
                description="O nome do bot não pode conter os seguintes caracteres: `@`, `#`, `:`, ````",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed_erro, delete_after=TEMPO_DELETE_ERRO)
            return

        nome_antigo = self.bot.user.name

        msg_processando = await ctx.send(
            embed=discord.Embed(
                title="⚙️ Processando Alteração",
                description="Atualizando o nome do bot no Discord...",
                color=Cores.INFO
            )
        )

        try:
            await self.bot.user.edit(username=novo_nome)
            await msg_processando.delete()

            embed_sucesso = discord.Embed(
                title="📛 Nome Alterado com Sucesso!",
                description=f"O nome do bot foi alterado por {ctx.author.mention}.",
                color=Cores.SUCESSO
            )
            embed_sucesso.add_field(name="Nome Anterior", value=f"`{nome_antigo}`", inline=True)
            embed_sucesso.add_field(name="Nome Atual", value=f"`{novo_nome}`", inline=True)
            embed_sucesso.set_thumbnail(url=self.bot.user.display_avatar.url)
            await ctx.send(embed=embed_sucesso, delete_after=TEMPO_DELETE_SUCESSO)

        except discord.HTTPException as e:
            await msg_processando.delete()
            if getattr(e, "code", None) == 50035 or "username" in str(e).lower():
                embed_limite = discord.Embed(
                    title="⚠️ Limite do Discord Atingido",
                    description=(
                        "O Discord impõe uma limitação rígida de segurança:\n"
                        "O nome de usuário de um bot só pode ser alterado **2 vezes por hora**.\n\n"
                        "Por favor, aguarde alguns minutos antes de tentar novamente."
                    ),
                    color=Cores.AVISO
                )
                await ctx.send(embed=embed_limite, delete_after=TEMPO_DELETE_ERRO)
            else:
                embed_api = discord.Embed(
                    title="❌ Erro na API do Discord",
                    description=f"Não foi possível alterar o nome:\n`{e}`",
                    color=Cores.ERRO
                )
                await ctx.send(embed=embed_api, delete_after=TEMPO_DELETE_ERRO)

        except Exception as e:
            await msg_processando.delete()
            embed_geral = discord.Embed(
                title="❌ Erro Inesperado",
                description=f"Ocorreu um erro inesperado ao alterar o nome:\n`{e}`",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed_geral, delete_after=TEMPO_DELETE_ERRO)

    @nome_bot.error
    async def nome_bot_error(self, ctx, error):
        await tentar_deletar_mensagem(ctx)
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Permissão Negada",
                description="Apenas **Administradores** podem alterar o nome do bot.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)

    # ========================================================
    # COMANDO: PREFIXO DO BOT (DINÂMICO E PRESENÇA NO DISCORD)
    # ========================================================
    @commands.command(name="setprefix", aliases=["prefixo", "prefix", "set_prefix"])
    async def setprefix(self, ctx, novo_prefixo: str = None):
        """
        Altera o prefixo de comandos do bot e atualiza o status de presença (Jogando Meu prefixo é ...).
        Exemplo: !setprefix .
        """
        await tentar_deletar_mensagem(ctx)

        if not tem_permissao_acao(ctx, "customizacao"):
            embed = discord.Embed(
                title="❌ Sem Permissão",
                description="Você precisa de autorização da Staff ou do cargo configurado para alterar o prefixo do bot.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        prefixo_atual = getattr(self.bot, "custom_prefix", None) or obter_prefixo_salvo()

        if not novo_prefixo or not novo_prefixo.strip():
            embed_info = discord.Embed(
                title="⚙️ Prefixo do Bot",
                description=(
                    f"O prefixo atual do bot é: `{prefixo_atual}`\n\n"
                    f"**Como alterar:**\n"
                    f"`{prefixo_atual}setprefix <novo_prefixo>`\n\n"
                    f"**Exemplos:**\n"
                    f"• `{prefixo_atual}setprefix .`\n"
                    f"• `{prefixo_atual}setprefix !`\n"
                    f"• `{prefixo_atual}setprefix $`\n\n"
                    f"*(Ao alterar, o status no Discord muda automaticamente para `Jogando Meu prefixo é <novo_prefixo>`)*"
                ),
                color=Cores.INFO
            )
            await ctx.send(embed=embed_info, delete_after=TEMPO_DELETE_SUCESSO)
            return

        novo_prefixo = novo_prefixo.strip()

        if len(novo_prefixo) > 5:
            embed_erro = discord.Embed(
                title="❌ Prefixo Muito Longo",
                description="O prefixo pode ter no máximo **5 caracteres**.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed_erro, delete_after=TEMPO_DELETE_ERRO)
            return

        if any(char.isspace() for char in novo_prefixo):
            embed_erro = discord.Embed(
                title="❌ Prefixo Inválido",
                description="O prefixo não pode conter espaços vazios.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed_erro, delete_after=TEMPO_DELETE_ERRO)
            return

        if novo_prefixo == prefixo_atual:
            embed_aviso = discord.Embed(
                title="⚠️ Prefixo Idêntico",
                description=f"O prefixo informado já é o prefixo atual do bot (`{prefixo_atual}`).",
                color=Cores.AVISO
            )
            await ctx.send(embed=embed_aviso, delete_after=TEMPO_DELETE_ERRO)
            return

        # 1. Salva a persistência no arquivo JSON
        salvar_prefixo_arquivo(novo_prefixo)

        # 2. Atualiza a memória dinâmica do bot
        self.bot.custom_prefix = novo_prefixo

        # 3. Atualiza o status/atividade do bot no Discord
        novo_status_texto = obter_atividade_texto(novo_prefixo)
        try:
            await self.bot.change_presence(
                status=STATUS_DISCORD,
                activity=discord.Game(name=novo_status_texto)
            )
        except Exception as e:
            print(f"⚠️ Falha ao atualizar presença do bot no Discord: {e}")

        # 4. Envia embed de confirmação
        embed_sucesso = discord.Embed(
            title="⚡  Prefixo Atualizado com Sucesso!",
            description=(
                f"> O prefixo de comandos foi alterado por {ctx.author.mention}.\n\n"
                f"• **Prefixo Anterior:** `{prefixo_atual}`\n"
                f"• **Novo Prefixo:** `{novo_prefixo}`\n"
                f"• **Status no Discord:** `Jogando {novo_status_texto}`\n\n"
                f"💡 *Tente executar:* `{novo_prefixo}painel` *ou* `{novo_prefixo}vip`"
            ),
            color=Cores.SUCESSO
        )
        embed_sucesso.set_author(name="Configuração de Sistema", icon_url=self.bot.user.display_avatar.url)
        if ctx.guild.icon:
            embed_sucesso.set_thumbnail(url=ctx.guild.icon.url)
        embed_sucesso.set_footer(text=f"{ctx.guild.name} • Alterado por {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
        embed_sucesso.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed_sucesso, delete_after=TEMPO_DELETE_SUCESSO)


async def setup(bot):
    await bot.add_cog(Customizacao(bot))