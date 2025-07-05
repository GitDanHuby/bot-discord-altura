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
            "compra": 1386744693659799603,
            "suporte": 1386764302828048494,
            "reportar_bug": 1386772360820166706,
            "denuncia": 1386772324488974456
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


# =================================================================================
# --- SEÇÃO DE COMANDOS DE BARRA (/) ---
# =================================================================================

@tree.command(name="configurar_tickets", description="Posta o painel de abertura de tickets neste canal.")
@app_commands.checks.has_permissions(manage_guild=True)
async def configurar_tickets(interaction: discord.Interaction):
    embed = discord.Embed(title="🎫 Central de Atendimento - Altura RP City", description="**ESCOLHA O TIPO DE TICKET QUE DESEJA ABRIR NO MENU ABAIXO**\n\nÉ importante lembrar-se de abrir tickets apenas quando necessário. Nossa equipe está aqui para ajudar e fornecer suporte sempre que você precisar.", color=discord.Color.blue())
    embed.set_thumbnail(url=client.user.display_avatar.url)
    embed.set_footer(text="© Altura RolePlay / SEASON 1 ✓")
    await interaction.channel.send(embed=embed, view=TicketView())
    await interaction.response.send_message("Painel de tickets configurado!", ephemeral=True)

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
    ID_DO_CANAL_SUGESTOES = 1386752647767265541
    canal_sugestoes = client.get_channel(ID_DO_CANAL_SUGESTOES)
    if not canal_sugestoes:
        await interaction.response.send_message("Erro: Canal de sugestões não configurado.", ephemeral=True)
        return
    embed_sugestao = discord.Embed(title="💡 Nova Sugestão", description=texto_da_sugestao, color=discord.Color.yellow())
    embed_sugestao.set_author(name=f"Sugestão de: {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
    mensagem_enviada = await canal_sugestoes.send(embed=embed_sugestao)
    await mensagem_enviada.add_reaction("👍")
    await mensagem_enviada.add_reaction("👎")
    await interaction.response.send_message("✅ Sua sugestão foi enviada com sucesso para o canal de sugestões!", ephemeral=True)

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
    ID_CANAL_LOGS = 1390917419748299002
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
        await membro.send(embed=dm)
        dm_enviada = True
    except discord.Forbidden:
        dm_enviada = False
    canal_logs = client.get_channel(ID_CANAL_LOGS)
    if canal_logs:
        embed_log = discord.Embed(title="📝 Log de Aviso", color=discord.Color.orange(), timestamp=datetime.now())
        embed_log.add_field(name="Membro Avisado", value=membro.mention, inline=True)
        embed_log.add_field(name="Aplicado por", value=interaction.user.mention, inline=True)
        embed_log.add_field(name="Motivo", value=motivo, inline=False)
        embed_log.set_footer(text=f"ID do Membro: {membro.id}")
        await canal_logs.send(embed=embed_log)
    confirmacao = f"✅ Aviso para {membro.mention} registrado com sucesso."
    if not dm_enviada:
        confirmacao += "\n⚠️ Não foi possível enviar a DM para o membro (provavelmente ele tem DMs desativadas)."
    await interaction.response.send_message(confirmacao, ephemeral=True)

@aviso.error
async def aviso_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message("❌ Você não tem permissão para usar este comando.", ephemeral=True)
    else:
        await interaction.response.send_message("Ocorreu um erro inesperado.", ephemeral=True)
        print(error)


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

@client.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return
    user_id = message.author.id
    current_time = time.time()
    if user_id in xp_cooldowns and current_time - xp_cooldowns[user_id] < 60:
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
    ID_DO_CARGO_GATILHO = 1387535159120629770
    ID_DO_CANAL_ANUNCIO = 1390048422815338596
    ID_DO_CARGO_PING    = 1380958005331230742
    cargo_gatilho = after.guild.get_role(ID_DO_CARGO_GATILHO)
    canal_anuncio = after.guild.get_channel(ID_DO_CANAL_ANUNCIO)
    if not cargo_gatilho or not canal_anuncio:
        return
    if cargo_gatilho not in before.roles and cargo_gatilho in after.roles:
        embed_parceria = discord.Embed(title="🤝 Nova Parceria Fechada!", description=f"Temos o prazer de anunciar uma nova parceria com o membro {after.mention}!", color=discord.Color.gold())
        if after.display_avatar:
            embed_parceria.set_thumbnail(url=after.display_avatar.url)
        embed_parceria.set_footer(text=f"Membro desde: {after.joined_at.strftime('%d/%m/%Y') if after.joined_at else 'Data indisponível'}")
        mensagem_ping = f"Atenção, <@&{ID_DO_CARGO_PING}>!"
        print(f"Anunciando nova parceria com {after.name} no canal {canal_anuncio.name}.")
        await canal_anuncio.send(content=mensagem_ping, embed=embed_parceria)

@client.event
async def on_message_delete(message):
    if message.author.bot:
        return
    ID_CANAL_LOGS_DELETADOS = 1386759472126623874
    canal_logs = client.get_channel(ID_CANAL_LOGS_DELETADOS)
    if not canal_logs:
        return
    conteudo = message.content if message.content else "Nenhum texto na mensagem (provavelmente uma imagem ou embed)."
    embed = discord.Embed(description="**📝 Mensagem de texto deletada**", color=discord.Color.dark_red(), timestamp=datetime.now())
    embed.set_author(name=f"{message.author.name}", icon_url=message.author.display_avatar.url)
    embed.add_field(name="Canal de texto:", value=message.channel.mention, inline=False)
    embed.add_field(name="Mensagem:", value=f"```{conteudo}```", inline=False)
    embed.set_footer(text=f"ID do Usuário: {message.author.id}")
    await canal_logs.send(embed=embed)

@client.event
async def on_member_remove(member):
    goodbye_channel_name = '✋│ᴇxɪᴛ'
    goodbye_channel = discord.utils.get(member.guild.text_channels, name=goodbye_channel_name)
    if goodbye_channel:
        guild = member.guild
        member_count = guild.member_count
        db = SessionLocal()
        try:
            setting = db.query(Setting).filter(Setting.key == 'goodbye_message').first()
            if setting and setting.value:
                goodbye_text = setting.value
            else:
                goodbye_text = f"**{member.name}** deixou o servidor. Sentiremos sua falta! 👋"
        finally:
            db.close()

        description_text = goodbye_text.format(member=member, server=guild, member_name=member.name, server_name=guild.name, server_member_count=member_count)

        embed = discord.Embed(description=description_text, color=discord.Color.from_rgb(255, 99, 71))
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


# =================================================================================
# --- INICIA O SITE E O BOT ---
# =================================================================================
if __name__ == "__main__":
    setup_database()
    start_web_server()
    client.run(TOKEN)
