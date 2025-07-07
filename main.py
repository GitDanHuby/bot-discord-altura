# =================================================================================
# ARQUIVO main.py DEFINITIVO FINAL - COM TUDO (INCLUINDO LOGS DE TICKET)
# =================================================================================

# --- Seção de Imports ---
import discord
from discord import app_commands
from discord.ui import View, Select, Button, button
import os
from dotenv import load_dotenv
from samp_client.client import SampClient
from web_server import start_web_server
from database_setup import setup_database, SessionLocal, User, Setting
import random
import time
from datetime import datetime
from yt_dlp import YoutubeDL

# --- Configuração Inicial ---
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.guilds = True
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

xp_cooldowns = {}
music_queues = {}
voice_join_times = {} # <--- ADICIONE ESTA LINHA

# --- FUNÇÃO AUXILIAR PARA PEGAR CONFIGURAÇÕES DO DB ---
def get_setting(key):
    db = SessionLocal()
    try:
        setting = db.query(Setting).filter(Setting.key == key).first()
        # Retorna o valor se a configuração existir, senão retorna None
        return setting.value if setting and setting.value else None
    finally:
        db.close()

# --- LÓGICA E CLASSES PARA O SISTEMA DE TICKETS ---

ID_CANAL_LOGS_TICKETS = 1386744831266521231 # <<< COLOQUE AQUI O ID DO SEU CANAL #logs-ticket

class ConfirmCloseView(View):
    def __init__(self, closed_by: discord.Member):
        super().__init__(timeout=60)
        self.value = None
        self.closed_by = closed_by

    @button(label="Confirmar Fechamento", style=discord.ButtonStyle.danger, custom_id="confirm_close_final_v4")
    async def confirm(self, interaction: discord.Interaction, button: Button):
        try:
            # Log de fechamento
            log_channel = interaction.guild.get_channel(ID_CANAL_LOGS_TICKETS)
            if log_channel:
                embed_log = discord.Embed(
                    title="🔒 Ticket Fechado",
                    description=f"O ticket `{interaction.channel.name}` foi fechado.",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
                embed_log.add_field(name="Fechado por", value=self.closed_by.mention, inline=True)
                await log_channel.send(embed=embed_log)

            await interaction.response.send_message("✅ Ticket fechado. O canal será deletado em 5 segundos.", ephemeral=True)
            time.sleep(5)
            await interaction.channel.delete()
        except Exception as e:
            print(f"Erro ao deletar/logar canal: {e}")
        self.value = True
        self.stop()

    @button(label="Cancelar", style=discord.ButtonStyle.secondary, custom_id="cancel_close_final_v4")
    async def cancel(self, interaction: discord.Interaction, button: Button):
        await interaction.message.delete()
        await interaction.response.send_message("❌ Ação cancelada.", ephemeral=True)
        self.value = False
        self.stop()

class CloseTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @button(label="🔒 Fechar Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket_button_final_v4")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ Você não tem permissão para fechar este ticket.", ephemeral=True)
            return

        view = ConfirmCloseView(closed_by=interaction.user)
        await interaction.response.send_message("Tem certeza que deseja fechar este ticket? Esta ação não pode ser desfeita.", view=view, ephemeral=True)
        await view.wait()

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        custom_id="ticket_menu_v4",
        placeholder="Selecione o tipo de ticket que deseja abrir...",
        min_values=1, max_values=1,
        options=[
            discord.SelectOption(label="Compra", emoji="🛒", description="Para dúvidas ou problemas com compras.", value="compra"),
            discord.SelectOption(label="Suporte", emoji="⛑️", description="Preciso de ajuda com algo no servidor.", value="suporte"),
            discord.SelectOption(label="Reportar Bug", emoji="👾", description="Encontrei um bug e quero reportá-lo.", value="reportar_bug"),
            discord.SelectOption(label="Denúncia", emoji="🚨", description="Para denúncias de jogadores.", value="denuncia")
        ]
    )
    async def ticket_menu_callback(self, interaction: discord.Interaction, select: Select):
        ID_CARGO_STAFF = 1380957727748263966
        mapa_categorias = {
            "compra": 1386744264037503159,
            "suporte": 1386749804394184815,
            "reportar_bug": 1386749987920285806,
            "denuncia": 1386749871142473820
        }

        option_value = select.values[0]
        option_label = [opt.label for opt in select.options if opt.value == option_value][0]
        
        user = interaction.user
        guild = interaction.guild

        id_categoria_correta = mapa_categorias.get(option_value)
        categoria = guild.get_channel(id_categoria_correta)
        cargo_staff = guild.get_role(ID_CARGO_STAFF)

        if not categoria or not cargo_staff:
            await interaction.response.send_message("Erro de configuração do bot (IDs). Contate um administrador.", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True, view_channel=True),
            cargo_staff: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True, view_channel=True),
            client.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, embed_links=True)
        }

        nome_canal = f"ticket-{option_label.lower().replace(' ', '-')}-{user.name}"
        
        try:
            ticket_channel = await guild.create_text_channel(name=nome_canal, category=categoria, overwrites=overwrites)
            
            # Log de abertura
            log_channel = guild.get_channel(ID_CANAL_LOGS_TICKETS)
            if log_channel:
                embed_log = discord.Embed(
                    title="✅ Ticket Aberto",
                    description=f"Um novo ticket foi aberto no canal {ticket_channel.mention}.",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                embed_log.add_field(name="Criado por", value=user.mention, inline=True)
                embed_log.add_field(name="Tipo", value=option_label, inline=True)
                await log_channel.send(embed=embed_log)

        except Exception as e:
            print(f"Erro ao criar/logar canal: {e}")
            await interaction.response.send_message("Ocorreu um erro ao criar o ticket.", ephemeral=True)
            return

        embed_ticket = discord.Embed(title=f"Ticket de {option_label} Aberto!", description=f"Olá {user.mention}, obrigado por nos contatar. \n\nPor favor, descreva seu problema ou dúvida em detalhes. Um membro da equipe <@&{ID_CARGO_STAFF}> virá te ajudar em breve.", color=discord.Color.green())
        
        await ticket_channel.send(embed=embed_ticket, view=CloseTicketView())
        
        await interaction.response.send_message(f"✅ Seu ticket foi criado com sucesso! Acesse: {ticket_channel.mention}", ephemeral=True)

class DashboardView(discord.ui.View):
    def __init__(self, url: str):
        super().__init__()
        # Adiciona o botão que é um link
        self.add_item(discord.ui.Button(label="Acessar o Painel de Controle", style=discord.ButtonStyle.link, url=url, emoji="🚀"))
# =================================================================================
# --- SEÇÃO DE COMANDOS DE BARRA (/) ---
# =================================================================================
async def play_next(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    if guild_id in music_queues and music_queues[guild_id]:
        voice_client = interaction.guild.voice_client
        if not voice_client:
            return

        # Pega a próxima música da fila
        song_info = music_queues[guild_id].pop(0)
        
        YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist':'True', 'quiet': True}
        FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

        with YoutubeDL(YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info(f"ytsearch:{song_info['query']}" if not song_info['query'].startswith("http") else song_info['query'], download=False)
                if 'entries' in info:
                    info = info['entries'][0]
            except Exception as e:
                await song_info['channel'].send(f"❌ Erro ao processar: `{song_info['title']}`. Pulando para a próxima.")
                # Tenta tocar a próxima da fila recursivamente
                await play_next(interaction)
                return
        
        audio_url = info['url']
        source = discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS)
        
        # O 'after' é a mágica: quando a música acabar, chama a função play_next de novo
        voice_client.play(source, after=lambda _: client.loop.create_task(play_next(interaction)))

        await song_info['channel'].send(f"▶️ Tocando agora: **{info['title']}**")
    else:
        # Fila vazia, pode adicionar uma mensagem ou simplesmente parar
        # await interaction.channel.send("Fila de músicas terminada.")
        pass

@tree.command(name="configurar_tickets", description="Posta o painel de abertura de tickets neste canal.")
@app_commands.checks.has_permissions(manage_guild=True)
async def configurar_tickets(interaction: discord.Interaction):
    embed = discord.Embed(title="🎫 Central de Atendimento - Altura RP City", description="**ESCOLHA O TIPO DE TICKET QUE DESEJA ABRIR NO MENU ABAIXO**\n\nÉ importante lembrar-se de abrir tickets apenas quando necessário. Nossa equipe está aqui para ajudar e fornecer suporte sempre que você precisar.", color=discord.Color.blue())
    embed.set_thumbnail(url=client.user.display_avatar.url)
    embed.set_footer(text="© Altura RolePlay / SEASON 1 ✓")
    await interaction.channel.send(embed=embed, view=TicketView())
    await interaction.response.send_message("Painel de tickets configurado!", ephemeral=True)

@tree.command(name="dashboard", description="Envia o link para o painel de controle web do bot.")
async def dashboard(interaction: discord.Interaction):
    # Pega a URL pública do seu serviço na Railway automaticamente
    dashboard_url = f"https://{os.getenv('RAILWAY_PUBLIC_DOMAIN')}"
    
    # Verifica se a URL foi encontrada
    if not os.getenv('RAILWAY_PUBLIC_DOMAIN'):
        await interaction.response.send_message("❌ A URL do dashboard não está configurada no ambiente.", ephemeral=True)
        return

    embed = discord.Embed(
        title="🚀 Painel de Controle do Altura RP City",
        description="Clique no botão abaixo para acessar o dashboard web e configurar as funcionalidades do bot, como a mensagem de boas-vindas!",
        color=discord.Color.blurple() # Cor padrão do Discord
    )
    
    # Cria a view com o botão e envia
    view = DashboardView(url=dashboard_url)
    await interaction.response.send_message(embed=embed, view=view)

@tree.command(name="ping", description="Testa se o bot está respondendo.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong! 🏓")

@tree.command(name="ip", description="Mostra o endereço de IP para se conectar ao servidor SAMP.")
async def ip(interaction: discord.Interaction):
    embed_ip = discord.Embed(title="🚀 Conecte-se ao Altura RolePlay City!", description="Use o IP abaixo para entrar na melhor cidade do SAMP!", color=discord.Color.blue())
    embed_ip.add_field(name="Endereço do Servidor:", value="`179.127.16.157:29015`", inline=False)
    embed_ip.set_footer(text="Clique no IP para copiar. Te vemos lá!")
    await interaction.response.send_message(embed=embed_ip)

@tree.command(name="regras", description="Mostra as regras principais do servidor.")
async def regras(interaction: discord.Interaction):
    regras_texto = """
    **1. Siga as diretrizes do Discord:** Termos | Regras.
    **2. Nicks e perfis devem ser legíveis e adequados.** Nada de "Staff", fontes estranhas ou conteúdo adulto.
    **3. Não use imagens de outros sem permissão.**
    **4. Contas fakes ou secundárias são proibidas.**
    **5. Respeite todos os membros, dentro e fora do servidor.**
    **6. Sem trolls em call:** nada de voz modificada, música ou micro estourando.
    **7. Sem trolls no chat:** ghost-ping, flood, gore, spam, etc.
    **8. Não abuse dos canais de suporte.**
    **9. Proibido divulgar outros servidores (SA-MP ou Discord).**
    **10. Links ou arquivos maliciosos serão punidos severamente.**
    **11. Nada de conteúdo que prejudique o servidor (ex: hackers, DM, etc).**
    **12. Raids = punição severa.**
    **13. Evite tentar burlar punições — isso agrava a situação.**
    **14. Sem divulgação de organizações ou comércio externo.**
    **15. Recrutamento só nos canais apropriados.**
    **16. Proibido transmitir outros servidores SA-MP em call.**
    **17. Você é responsável pela vinculação correta da sua conta.**
    
    > Ao permanecer no servidor, você aceita todas as regras.
    *📅 Atualizado em: 16/06/2025*
    """
    embed_regras = discord.Embed(title="📜 Regras do Discord - Altura RP City", description=regras_texto, color=discord.Color.orange())
    await interaction.response.send_message(embed=embed_regras)

@tree.command(name="redes_sociais", description="Mostra as redes sociais oficiais do servidor.")
async def redes_sociais(interaction: discord.Interaction):
    embed_redes = discord.Embed(title="📱 Nossas Redes Sociais", description="Siga-nos para ficar por dentro de tudo!", color=discord.Color.purple())
    embed_redes.add_field(name="YouTube", value="[Clique aqui para acessar](https://youtube.com/@snow_pr25)", inline=False)
    embed_redes.add_field(name="TikTok", value="[Clique aqui para acessar](https://www.tiktok.com/@snow_pr37?_t=8xl9kFMFyDQ&_r=1)", inline=False)
    embed_redes.add_field(name="Instagram", value="[Clique aqui para acessar](https://www.instagram.com/snow_pr25?igsh=MTNsNnA2d2xlMG9jdA==)", inline=False)
    await interaction.response.send_message(embed=embed_redes)

@tree.command(name="status", description="Verifica o status do servidor SAMP.")
async def status(interaction: discord.Interaction):
    IP_DO_SERVIDOR = "179.127.16.157"
    PORTA_DO_SERVIDOR = 29015
    try:
        with SampClient(address=IP_DO_SERVIDOR, port=PORTA_DO_SERVIDOR) as samp_client:
            info = samp_client.get_server_info()
            embed_status = discord.Embed(title=f"✅ Status do Servidor: ONLINE", color=discord.Color.green())
            embed_status.add_field(name="Nome do Servidor", value=info.hostname, inline=False)
            embed_status.add_field(name="Jogadores", value=f"{info.players}/{info.max_players}", inline=True)
            embed_status.add_field(name="Ping", value=f"{samp_client.ping()}ms", inline=True)
    except Exception as e:
        print(f"Erro ao checar status do servidor: {e}")
        embed_status = discord.Embed(title=f"❌ Status do Servidor: OFFLINE", description="Não foi possível conectar ao servidor. Tente novamente mais tarde.", color=discord.Color.red())
    await interaction.response.send_message(embed=embed_status)

@tree.command(name="sugestao", description="Envie uma sugestão para a equipe.")
async def sugestao(interaction: discord.Interaction, texto_da_sugestao: str):
    # Busca o ID do canal no banco de dados
    id_canal_str = get_setting('sugestao_channel_id')
    if not id_canal_str:
        await interaction.response.send_message("❌ O canal de sugestões não foi configurado no dashboard.", ephemeral=True)
        return
    
    canal_sugestoes = client.get_channel(int(id_canal_str))
    if not canal_sugestoes:
        await interaction.response.send_message("❌ O ID do canal de sugestões no dashboard é inválido.", ephemeral=True)
        return

    embed_sugestao = discord.Embed(title="💡 Nova Sugestão", description=texto_da_sugestao, color=discord.Color.yellow())
    embed_sugestao.set_author(name=f"Sugestão de: {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
    mensagem_enviada = await canal_sugestoes.send(embed=embed_sugestao)
    await mensagem_enviada.add_reaction("👍")
    await mensagem_enviada.add_reaction("👎")
    await interaction.response.send_message("✅ Sua sugestão foi enviada com sucesso!", ephemeral=True)

@tree.command(name="rank", description="Mostra seu nível e XP no servidor.")
async def rank(interaction: discord.Interaction, membro: discord.Member = None):
    target_user = membro or interaction.user
    db = SessionLocal()
    try:
        user_data = db.query(User).filter(User.id == target_user.id).first()
        if not user_data:
            await interaction.response.send_message(f"{target_user.name} ainda não tem XP. Comece a conversar!", ephemeral=True)
            return
        level = user_data.level
        xp = user_data.xp
        xp_para_proximo_level = (5 * (level ** 2)) + (50 * level) + 100
        embed_rank = discord.Embed(title=f"🏆 Rank de {target_user.name}", color=target_user.color)
        embed_rank.set_thumbnail(url=target_user.display_avatar.url)
        embed_rank.add_field(name="Nível", value=f"**{level}**", inline=True)
        embed_rank.add_field(name="XP", value=f"**{xp} / {xp_para_proximo_level}**", inline=True)
        progresso = int((xp / xp_para_proximo_level) * 20)
        barra = "🟩" * progresso + "⬛" * (20 - progresso)
        embed_rank.add_field(name="Progresso", value=barra, inline=False)
        await interaction.response.send_message(embed=embed_rank)
    finally:
        db.close()

# NOVO COMANDO /leaderboard
@tree.command(name="leaderboard", description="Mostra os membros com mais XP no servidor.")
async def leaderboard(interaction: discord.Interaction):
    await interaction.response.defer() # Adia a resposta, pois a busca no DB pode demorar um pouco

    db = SessionLocal()
    try:
        # Pega os 10 usuários com mais XP, em ordem decrescente
        top_users = db.query(User).order_by(User.xp.desc()).limit(10).all()

        embed = discord.Embed(
            title="🏆 Ranking de Atividade do Servidor",
            description="Os membros mais ativos do Altura RP City!",
            color=discord.Color.gold()
        )

        if not top_users:
            embed.description = "Ainda não há ninguém no ranking. Comece a conversar!"
        else:
            # Cria a lista de texto para o ranking
            leaderboard_text = ""
            for i, user_data in enumerate(top_users):
                try:
                    # Tenta encontrar o membro no servidor pelo ID
                    member = await interaction.guild.fetch_member(user_data.id)
                    member_name = member.display_name
                except discord.NotFound:
                    # Se o membro não for encontrado (saiu do servidor), mostra o ID
                    member_name = f"Membro Desconhecido ({user_data.id})"
                
                # Monta a linha do ranking
                leaderboard_text += f"**{i+1}.** {member_name} - **Nível {user_data.level}** ({user_data.xp} XP)\n"
            
            embed.description = leaderboard_text

    except Exception as e:
        print(f"Erro ao buscar o leaderboard: {e}")
        embed = discord.Embed(title="❌ Erro", description="Não foi possível buscar o ranking no momento.", color=discord.Color.red())
    finally:
        db.close()

    # Usa followup.send() porque já adiamos a resposta
    await interaction.followup.send(embed=embed)

@tree.command(name="set_goodbye_message", description="Define a mensagem de despedida do servidor (Staff only).")
@app_commands.checks.has_permissions(manage_guild=True)
async def set_goodbye_message(interaction: discord.Interaction, message: str):
    db = SessionLocal()
    try:
        setting = db.query(Setting).filter(Setting.key == 'goodbye_message').first()
        if setting:
            setting.value = message
        else:
            new_setting = Setting(key='goodbye_message', value=message)
            db.add(new_setting)
        db.commit()
        await interaction.response.send_message("✅ Mensagem de despedida definida com sucesso!", ephemeral=True)
    finally:
        db.close()

@tree.command(name="aviso", description="Envia um aviso para um membro e registra em um canal de logs.")
@app_commands.checks.has_permissions(kick_members=True)
async def aviso(interaction: discord.Interaction, membro: discord.Member, motivo: str):
    # Busca o ID do canal de logs no banco de dados
    id_canal_logs_str = get_setting('warn_log_channel_id')
    if not id_canal_logs_str:
        await interaction.response.send_message("❌ O canal de logs de avisos não foi configurado no dashboard.", ephemeral=True)
        return

    canal_logs = client.get_channel(int(id_canal_logs_str))
    if not canal_logs:
        await interaction.response.send_message("❌ O ID do canal de logs de avisos no dashboard é inválido.", ephemeral=True)
        return
    
    if membro == interaction.user:
        await interaction.response.send_message("Você não pode avisar a si mesmo.", ephemeral=True)
        return
    if membro.bot:
        await interaction.response.send_message("Você não pode avisar um bot.", ephemeral=True)
        return
    try:
        embed_dm = discord.Embed(title="🚨 Você Recebeu um Aviso!", description=f"Você foi avisado no servidor **{interaction.guild.name}**.", color=discord.Color.yellow())
        embed_dm.add_field(name="Motivo do Aviso", value=motivo, inline=False)
        embed_dm.set_footer(text=f"Aviso aplicado por: {interaction.user.name}")
        await membro.send(embed=embed_dm)
        dm_enviada = True
    except discord.Forbidden:
        dm_enviada = False
    
    embed_log = discord.Embed(title="📝 Log de Aviso", color=discord.Color.orange(), timestamp=datetime.now())
    embed_log.add_field(name="Membro Avisado", value=membro.mention, inline=True)
    embed_log.add_field(name="Aplicado por", value=interaction.user.mention, inline=True)
    embed_log.add_field(name="Motivo", value=motivo, inline=False)
    embed_log.set_footer(text=f"ID do Membro: {membro.id}")
    await canal_logs.send(embed=embed_log)

    confirmacao = f"✅ Aviso para {membro.mention} registrado com sucesso."
    if not dm_enviada:
        confirmacao += "\n⚠️ Não foi possível enviar a DM para o membro."
    await interaction.response.send_message(confirmacao, ephemeral=True)

@aviso.error
async def aviso_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message("❌ Você não tem permissão para usar este comando.", ephemeral=True)
    else:
        await interaction.response.send_message("Ocorreu um erro inesperado.", ephemeral=True)
        print(error)

# --- NOVO COMANDO /anunciar ---
@tree.command(name="anunciar", description="Cria um anúncio formatado em um canal específico.")
@app_commands.checks.has_permissions(manage_guild=True) # Só quem pode gerenciar o servidor pode usar
@app_commands.choices(ping=[ # Define as opções para o ping
    app_commands.Choice(name="Everyone", value="everyone"),
    app_commands.Choice(name="Here", value="here"),
    app_commands.Choice(name="Nenhum", value="none")
])
async def anunciar(interaction: discord.Interaction, titulo: str, mensagem: str, ping: app_commands.Choice[str], imagem_url: str = None):
    # ▼▼▼ COLOQUE O ID DO SEU CANAL #avisos AQUI DENTRO DAS ASPAS ▼▼▼
    ID_CANAL_ANUNCIOS = "1380958104228724789" 

    # Converte o ID para um número inteiro
    try:
        id_numerico = int(ID_CANAL_ANUNCIOS)
        canal_anuncios = client.get_channel(id_numerico)
    except (ValueError, TypeError):
        canal_anuncios = None

    if not canal_anuncios:
        await interaction.response.send_message("❌ Canal de anúncios não configurado corretamente. Verifique o ID.", ephemeral=True)
        return

    # Define o texto do ping
    ping_text = ""
    if ping.value == "everyone":
        ping_text = "@everyone"
    elif ping.value == "here":
        ping_text = "@here"

    # Cria o embed do anúncio
    embed = discord.Embed(
        title=titulo,
        description=mensagem,
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    if imagem_url:
        embed.set_thumbnail(url=imagem_url)
    
    embed.set_footer(text=f"Anúncio feito por: {interaction.user.name}")

    try:
        await canal_anuncios.send(content=ping_text if ping_text else None, embed=embed)
        await interaction.response.send_message("✅ Anúncio enviado com sucesso!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Ocorreu um erro ao enviar o anúncio: {e}", ephemeral=True)

# --- COMANDOS DE MÚSICA COM SISTEMA DE FILA ---

@tree.command(name="play", description="Toca uma música ou a adiciona na fila.")
async def play(interaction: discord.Interaction, busca: str):
    if not interaction.user.voice:
        await interaction.response.send_message("❌ Você precisa estar em um canal de voz.", ephemeral=True)
        return

    voice_client = interaction.guild.voice_client
    if not voice_client:
        voice_client = await interaction.user.voice.channel.connect()

    guild_id = interaction.guild.id
    if guild_id not in music_queues:
        music_queues[guild_id] = []
    
    music_queues[guild_id].append({'query': busca, 'channel': interaction.channel, 'title': busca})
    
    if not voice_client.is_playing() and not voice_client.is_paused():
        await interaction.response.send_message(f"▶️ Iniciando a festa com: `{busca}`")
        await play_next(interaction)
    else:
        await interaction.response.send_message(f"✅ Adicionado à fila: `{busca}`")

@tree.command(name="join", description="Faz o bot entrar no seu canal de voz.")
async def join(interaction: discord.Interaction):
    if not interaction.user.voice:
        await interaction.response.send_message("❌ Você não está em um canal de voz!", ephemeral=True)
        return
    channel = interaction.user.voice.channel
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.move_to(channel)
        await interaction.response.send_message(f"✅ Movido para: **{channel.name}**")
    else:
        await channel.connect()
        await interaction.response.send_message(f"✅ Conectado a: **{channel.name}**")

@tree.command(name="leave", description="Faz o bot sair do canal de voz e limpa a fila.")
async def leave(interaction: discord.Interaction):
    if not interaction.guild.voice_client:
        await interaction.response.send_message("❌ O bot não está em nenhum canal de voz.", ephemeral=True)
        return
    
    guild_id = interaction.guild.id
    if guild_id in music_queues:
        music_queues[guild_id].clear()

    await interaction.guild.voice_client.disconnect()
    await interaction.response.send_message("👋 Desconectado e fila limpa.")

@tree.command(name="stop", description="Para a música, limpa a fila e desconecta o bot.")
async def stop(interaction: discord.Interaction):
    if not interaction.guild.voice_client:
        await interaction.response.send_message("❌ O bot não está fazendo nada.", ephemeral=True)
        return
        
    guild_id = interaction.guild.id
    if guild_id in music_queues:
        music_queues[guild_id].clear()
    
    interaction.guild.voice_client.stop()
    await interaction.guild.voice_client.disconnect()
    await interaction.response.send_message("⏹️ Música parada, fila limpa e bot desconectado.")
    
@tree.command(name="skip", description="Pula para a próxima música da fila.")
async def skip(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await interaction.response.send_message("⏭️ Música pulada!")
    else:
        await interaction.response.send_message("❌ Não há música tocando para pular.", ephemeral=True)

@tree.command(name="queue", description="Mostra a fila de músicas.")
async def queue(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    if guild_id not in music_queues or not music_queues[guild_id]:
        await interaction.response.send_message("A fila de músicas está vazia.", ephemeral=True)
        return

    embed = discord.Embed(title="🎵 Fila de Músicas", color=discord.Color.blue())
    queue_list = ""
    for i, song in enumerate(music_queues[guild_id]):
        queue_list += f"**{i+1}.** `{song['title']}`\n"
    
    embed.description = queue_list
    await interaction.response.send_message(embed=embed)

@tree.command(name="clear", description="Limpa todas as músicas da fila.")
async def clear(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    if guild_id in music_queues:
        music_queues[guild_id].clear()
        await interaction.response.send_message("🗑️ Fila de músicas limpa com sucesso!")
    else:
        await interaction.response.send_message("A fila já está vazia.", ephemeral=True)

@tree.command(name="pause", description="Pausa a música que está tocando.")
async def pause(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await interaction.response.send_message("⏸️ Música pausada.")
    else:
        await interaction.response.send_message("❌ Não há nenhuma música tocando para pausar.", ephemeral=True)

@tree.command(name="resume", description="Continua a música que foi pausada.")
async def resume(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_paused():
        voice_client.resume()
        await interaction.response.send_message("▶️ Retomando a música.")
    else:
        await interaction.response.send_message("❌ A música não está pausada.", ephemeral=True)

# =================================================================================
# --- SEÇÃO DE EVENTOS DO DISCORD ---
# =================================================================================

@client.event
async def on_ready():
    client.add_view(TicketView())
    client.add_view(CloseTicketView())
    await tree.sync()
    print("Comandos de barra sincronizados.")
    activity = discord.Game(name="na cidade do Altura RP City")
    await client.change_presence(status=discord.Status.online, activity=activity)
    print(f'{client.user} conectou-se ao Discord!')
    print('Bot está online e pronto para uso.')

# DENTRO DO main.py, SUBSTITUA APENAS ESTA FUNÇÃO
@client.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    # Verifica se o sistema de XP está ativado no banco de dados
    xp_enabled_str = get_setting('xp_system_enabled')
    # Se a configuração for 'false', a função para aqui e não dá XP.
    if xp_enabled_str == 'false':
        return 

    user_id = message.author.id
    current_time = time.time()

    if user_id in xp_cooldowns and current_time - xp_cooldowns.get(user_id, 0) < 60:
        return

    xp_cooldowns[user_id] = current_time
    xp_ganho = random.randint(15, 25)
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            user = User(id=user_id, xp=0, level=1)
            db.add(user)

        user.xp += xp_ganho
        xp_necessario = (5 * (user.level ** 2)) + (50 * user.level) + 100

        if user.xp >= xp_necessario:
            user.level += 1
            user.xp -= xp_necessario
            level_up_embed = discord.Embed(title="🎉 LEVEL UP! 🎉", description=f"Parabéns, {message.author.mention}! Você alcançou o **Nível {user.level}**!", color=discord.Color.magenta())
            await message.channel.send(embed=level_up_embed)
        
        db.commit()
    finally:
        db.close()

@client.event
async def on_member_join(member):
    welcome_channel = discord.utils.get(member.guild.text_channels, name='👏│ᴡᴇʟᴄᴏᴍᴇ')

    if welcome_channel:
        guild = member.guild
        member_count = guild.member_count
        
        db = SessionLocal()
        try:
            setting = db.query(Setting).filter(Setting.key == 'welcome_message').first()
            if setting and setting.value:
                welcome_text = setting.value
            else:
                welcome_text = f"Seja muito bem-vindo(a), {{member.mention}}, ao {{server_name}}! Configure a mensagem de boas-vindas no dashboard."
        finally:
            db.close()

        description_text = welcome_text.format(member=member, server=guild, member_mention=member.mention, member_name=member.name, server_name=guild.name, server_member_count=member_count)
        
        embed = discord.Embed(description=description_text, color=discord.Color.from_rgb(70, 130, 180))
        if client.user.avatar:
            embed.set_author(name=client.user.name, icon_url=client.user.avatar.url)
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        footer_text = "© Todos os direitos reservados do Altura RP City"
        if client.user.avatar:
            embed.set_footer(text=footer_text, icon_url=client.user.avatar.url)
        else:
            embed.set_footer(text=footer_text)
        await welcome_channel.send(embed=embed)
    else:
        print(f"Aviso: Canal de boas-vindas não encontrado no servidor '{member.guild.name}'.")

@client.event
async def on_member_update(before, after):
    # Busca todos os IDs do sistema de parceria no banco de dados
    id_cargo_gatilho_str = get_setting('parceria_gatilho_role_id')
    id_canal_anuncio_str = get_setting('parceria_anuncio_channel_id')
    id_cargo_ping_str = get_setting('parceria_ping_role_id')

    # Se algum ID não estiver configurado no dashboard, a função não faz nada
    if not all([id_cargo_gatilho_str, id_canal_anuncio_str, id_cargo_ping_str]):
        return 

    cargo_gatilho = after.guild.get_role(int(id_cargo_gatilho_str))
    canal_anuncio = after.guild.get_channel(int(id_canal_anuncio_str))
    
    if not cargo_gatilho or not canal_anuncio:
        return

    if cargo_gatilho not in before.roles and cargo_gatilho in after.roles:
        embed_parceria = discord.Embed(title="🤝 Nova Parceria Fechada!", description=f"Temos o prazer de anunciar uma nova parceria com o membro {after.mention}!", color=discord.Color.gold())
        if after.display_avatar:
            embed_parceria.set_thumbnail(url=after.display_avatar.url)
        embed_parceria.set_footer(text=f"Membro desde: {after.joined_at.strftime('%d/%m/%Y') if after.joined_at else 'Data indisponível'}")
        mensagem_ping = f"Atenção, <@&{id_cargo_ping_str}>!"
        await canal_anuncio.send(content=mensagem_ping, embed=embed_parceria)

@client.event
async def on_message_delete(message):
    if message.author.bot:
        return

    # Busca o ID do canal de logs no banco de dados
    id_canal_logs_str = get_setting('delete_log_channel_id')
    if not id_canal_logs_str:
        return

    canal_logs = client.get_channel(int(id_canal_logs_str))
    if not canal_logs:
        return

    conteudo = message.content if message.content else "Nenhum texto na mensagem (provavelmente uma imagem ou embed)."
    embed = discord.Embed(description="**📝 Mensagem de texto deletada**", color=discord.Color.dark_red(), timestamp=datetime.now())
    embed.set_author(name=f"{message.author.name}", icon_url=message.author.display_avatar.url)
    embed.add_field(name="Canal de texto:", value=message.channel.mention, inline=False)
    embed.add_field(name="Mensagem:", value=f"```{conteudo}```", inline=False)
    embed.set_footer(text=f"ID do Usuário: {message.author.id}")
    await canal_logs.send(embed=embed)

# DENTRO DO main.py, SUBSTITUA APENAS ESTA FUNÇÃO
@client.event
async def on_member_remove(member):
    from database_setup import SessionLocal, Setting

    # Pega o canal de despedida pelo nome
    goodbye_channel_name = '✋│ᴇxɪᴛ' # Você pode mudar isso se quiser
    goodbye_channel = discord.utils.get(member.guild.text_channels, name=goodbye_channel_name)

    if goodbye_channel:
        guild = member.guild
        member_count = guild.member_count # O Discord já atualizou a contagem

        # Conecta ao banco de dados para buscar a mensagem
        db = SessionLocal()
        try:
            setting = db.query(Setting).filter(Setting.key == 'goodbye_message').first()
            # Se encontrar uma mensagem salva, usa ela. Se não, usa uma padrão.
            if setting and setting.value:
                goodbye_text = setting.value
            else:
                goodbye_text = f"**{member.name}** deixou o servidor. Sentiremos sua falta! 👋"
        finally:
            db.close()

        # Substitui as variáveis na mensagem
        description_text = goodbye_text.format(
            member=member, 
            server=guild, 
            member_name=member.name, 
            server_name=guild.name, 
            server_member_count=member_count
        )

        embed = discord.Embed(description=description_text, color=discord.Color.from_rgb(255, 99, 71)) # Cor vermelha/laranja
        if client.user.avatar:
            embed.set_author(name=client.user.name, icon_url=client.user.avatar.url)
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        footer_text = "© Todos os direitos reservados do Altura RP City"
        if client.user.avatar:
            embed.set_footer(text=footer_text, icon_url=client.user.avatar.url)
        else:
            embed.set_footer(text=footer_text)
        await goodbye_channel.send(embed=embed)
    else:
        print(f"Aviso: Canal de despedida '{goodbye_channel_name}' não encontrado no servidor '{member.guild.name}'.")

# NOVO EVENTO on_voice_state_update (VERSÃO PROFISSIONAL)
@client.event
async def on_voice_state_update(member, before, after):
    # Ignora bots
    if member.bot:
        return

    # Pega o ID do canal de logs do banco de dados
    id_canal_logs_str = get_setting('voice_log_channel_id')
    if not id_canal_logs_str:
        return 

    log_channel = client.get_channel(int(id_canal_logs_str))
    if not log_channel:
        return

    # --- LÓGICA DE ENTRADA ---
    if not before.channel and after.channel:
        # Armazena o horário de entrada
        voice_join_times[member.id] = datetime.now()
        
        embed = discord.Embed(color=discord.Color.green(), timestamp=datetime.now())
        embed.set_author(name=f"Usuário {member.name} entrou no canal de voz", icon_url=member.display_avatar.url)
        
        embed.add_field(name="Membro", value=member.mention, inline=False)
        embed.add_field(name="Canal", value=f"🔊 {after.channel.mention}", inline=False)
        
        membros_no_canal = ", ".join([m.mention for m in after.channel.members])
        embed.add_field(name=f"Membros no canal ({len(after.channel.members)})", value=membros_no_canal, inline=False)
        
        limite = after.channel.user_limit
        embed.add_field(name="Limite do canal", value=f"{len(after.channel.members)}/{limite if limite > 0 else '∞'}", inline=False)
        
        await log_channel.send(embed=embed)

    # --- LÓGICA DE SAÍDA ---
    elif before.channel and not after.channel:
        embed = discord.Embed(color=discord.Color.red(), timestamp=datetime.now())
        embed.set_author(name=f"Usuário {member.name} saiu do canal de voz", icon_url=member.display_avatar.url)

        embed.add_field(name="Membro", value=member.mention, inline=False)
        embed.add_field(name="Canal", value=f"🔊 `{before.channel.name}`", inline=False)

        # Lógica para calcular o tempo gasto
        if member.id in voice_join_times:
            duracao = datetime.now() - voice_join_times[member.id]
            del voice_join_times[member.id] # Remove o registro de tempo

            dias = duracao.days
            horas, resto = divmod(duracao.seconds, 3600)
            minutos, segundos = divmod(resto, 60)
            
            tempo_gasto_str = ""
            if dias > 0: tempo_gasto_str += f"{dias} dia(s), "
            if horas > 0: tempo_gasto_str += f"{horas} hora(s), "
            if minutos > 0: tempo_gasto_str += f"{minutos} minuto(s), "
            tempo_gasto_str += f"{segundos} segundo(s)"
            
            embed.add_field(name="Tempo gasto no canal", value=tempo_gasto_str, inline=False)

        await log_channel.send(embed=embed)
        
    # --- LÓGICA DE MUDANÇA DE CANAL ---
    elif before.channel and after.channel and before.channel != after.channel:
        # Log de saída do canal antigo
        embed_leave = discord.Embed(color=discord.Color.red(), timestamp=datetime.now())
        embed_leave.set_author(name=f"Usuário {member.name} saiu do canal de voz", icon_url=member.display_avatar.url)
        embed_leave.add_field(name="Membro", value=member.mention, inline=False)
        embed_leave.add_field(name="Canal", value=f"🔊 `{before.channel.name}`", inline=False)
        # Calcula o tempo gasto no canal antigo
        if member.id in voice_join_times:
            duracao = datetime.now() - voice_join_times[member.id]
            # ... (código de formatação de tempo omitido para simplicidade, mas a lógica está acima)
            embed_leave.add_field(name="Tempo gasto no canal", value=f"{int(duracao.total_seconds())} segundos", inline=False)
        await log_channel.send(embed=embed_leave)
        
        # Log de entrada no canal novo
        voice_join_times[member.id] = datetime.now() # Reseta o tempo de entrada para o novo canal
        embed_join = discord.Embed(color=discord.Color.green(), timestamp=datetime.now())
        embed_join.set_author(name=f"Usuário {member.name} entrou no canal de voz", icon_url=member.display_avatar.url)
        embed_join.add_field(name="Membro", value=member.mention, inline=False)
        embed_join.add_field(name="Canal", value=f"🔊 {after.channel.mention}", inline=False)
        await log_channel.send(embed=embed_join)

# --- NOVOS EVENTOS DE LOG DE AUDITORIA ---

@client.event
async def on_guild_channel_create(channel):
    # Pega o ID do canal de logs do banco de dados
    log_channel_id_str = get_setting('audit_log_channel_id')
    if not log_channel_id_str: return
    log_channel = client.get_channel(int(log_channel_id_str))
    if not log_channel: return

    # Pega o registro de auditoria para saber quem criou o canal
    executor = None
    async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_create):
        if entry.target.id == channel.id:
            executor = entry.user
            break
    
    embed = discord.Embed(title="✅ Canal Criado", color=discord.Color.green(), timestamp=datetime.now())
    embed.add_field(name="Canal", value=channel.mention, inline=False)
    if executor:
        embed.add_field(name="Executor", value=executor.mention, inline=False)
    if channel.category:
        embed.add_field(name="Categoria", value=channel.category.name, inline=False)

    await log_channel.send(embed=embed)


@client.event
async def on_guild_channel_delete(channel):
    log_channel_id_str = get_setting('audit_log_channel_id')
    if not log_channel_id_str: return
    log_channel = client.get_channel(int(log_channel_id_str))
    if not log_channel: return

    executor = None
    async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
        if entry.target.id == channel.id:
            executor = entry.user
            break

    embed = discord.Embed(title="🗑️ Canal Deletado", color=discord.Color.red(), timestamp=datetime.now())
    embed.add_field(name="Nome do Canal", value=f"`# {channel.name}`", inline=False)
    if executor:
        embed.add_field(name="Executor", value=executor.mention, inline=False)
    if channel.category:
        embed.add_field(name="Categoria", value=channel.category.name, inline=False)

    await log_channel.send(embed=embed)


@client.event
async def on_guild_role_update(before, after):
    log_channel_id_str = get_setting('audit_log_channel_id')
    if not log_channel_id_str: return
    log_channel = client.get_channel(int(log_channel_id_str))
    if not log_channel: return

    executor = None
    async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_update):
        if entry.target.id == after.id:
            executor = entry.user
            break
            
    # Se nada mudou de relevante, não loga
    if before.name == after.name and before.color == after.color and before.permissions == after.permissions:
        return

    embed = discord.Embed(title="🎭 Cargo Atualizado", color=discord.Color.yellow(), timestamp=datetime.now())
    embed.add_field(name="Cargo", value=after.mention, inline=False)
    
    mudancas = ""
    if before.name != after.name:
        mudancas += f"**Nome:** `{before.name}` -> `{after.name}`\n"
    if before.color != after.color:
        mudancas += f"**Cor:** `{before.color}` -> `{after.color}`\n"
    if before.permissions != after.permissions:
        mudancas += "**Permissões foram alteradas.**\n"
        
    embed.add_field(name="Mudanças", value=mudancas, inline=False)
    
    if executor:
        embed.add_field(name="Executor", value=executor.mention, inline=False)

    await log_channel.send(embed=embed)
# =================================================================================
# --- INICIA O SITE E O BOT ---
# =================================================================================
if __name__ == "__main__":
    setup_database()
    start_web_server()
    client.run(TOKEN)
