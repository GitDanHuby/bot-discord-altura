# SEU ARQUIVO main.py COMPLETO E ATUALIZADO

import discord
from discord import app_commands
import os
from dotenv import load_dotenv
from samp_client.client import SampClient

# Carrega as variáveis de ambiente
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Configuração das Intents
intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.guilds = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# --- SEÇÃO DE COMANDOS ---

# COMANDO /ping
@tree.command(name="ping", description="Testa se o bot está respondendo.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong! 🏓")

# COMANDO /ip
@tree.command(name="ip", description="Mostra o endereço de IP para se conectar ao servidor SAMP.")
async def ip(interaction: discord.Interaction):
    embed_ip = discord.Embed(title="🚀 Conecte-se ao Altura RolePlay City!", description="Use o IP abaixo para entrar na melhor cidade do SAMP!", color=discord.Color.blue())
    embed_ip.add_field(name="Endereço do Servidor:", value="`179.127.16.157:29015`", inline=False)
    embed_ip.set_footer(text="Clique no IP para copiar. Te vemos lá!")
    await interaction.response.send_message(embed=embed_ip)

# COMANDO /regras ATUALIZADO
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

# COMANDO /redes_sociais ATUALIZADO
@tree.command(name="redes_sociais", description="Mostra as redes sociais oficiais do servidor.")
async def redes_sociais(interaction: discord.Interaction):
    embed_redes = discord.Embed(title="📱 Nossas Redes Sociais", description="Siga-nos para ficar por dentro de tudo!", color=discord.Color.purple())
    embed_redes.add_field(name="YouTube", value="[Clique aqui para acessar](https://youtube.com/@snow_pr25)", inline=False)
    embed_redes.add_field(name="TikTok", value="[Clique aqui para acessar](https://www.tiktok.com/@snow_pr37?_t=8xl9kFMFyDQ&_r=1)", inline=False)
    embed_redes.add_field(name="Instagram", value="[Clique aqui para acessar](https://www.instagram.com/snow_pr25?igsh=MTNsNnA2d2xlMG9jdA==)", inline=False)
    await interaction.response.send_message(embed=embed_redes)

# COMANDO /status
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

# COMANDO /sugestao ATUALIZADO
@tree.command(name="sugestao", description="Envie uma sugestão para a equipe.")
async def sugestao(interaction: discord.Interaction, texto_da_sugestao: str):
    ID_DO_CANAL_SUGESTOES = 1386752647767265541 # ID JÁ CONFIGURADO

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


# --- SEÇÃO DE EVENTOS ---

@client.event
async def on_ready():
    await tree.sync()
    print("Comandos de barra sincronizados.")
    print(f'{client.user} conectou-se ao Discord!')
    print('Bot está online e pronto para uso.')

# ... (A função on_member_join continua aqui, igual a antes) ...
@client.event
async def on_member_join(member):
    welcome_channel = discord.utils.get(member.guild.text_channels, name='👏│ᴡᴇʟᴄᴏᴍᴇ')

    if welcome_channel:
        guild = member.guild
        member_count = guild.member_count
        description_text = f"""
👉 <@519353941255913487> 👋✨ Seja muito bem-vindo(a), ao Altura RolePlay City — onde a sua história começa nas alturas! 🚁🌆
🛬 Você acaba de pousar na cidade mais viva e realista do SAMP! Aqui, cada escolha conta e o roleplay é levado a sério.
👥 Agora somos **{member_count} membros** vivendo essa experiência com você! 🎉
📝 **Antes de iniciar sua jornada:**
📜 Leia atentamente as regras em <#1384229192933310585>
📢 Fique de olho nos eventos e atualizações em <#1380958104228724789>
🎮 **IP do Servidor:** `179.127.16.157:29015`
💬 Em caso de dúvidas, fale com a equipe <@&1380957723159433326>
💜 O Altura RolePlay agradece sua presença. Nos vemos nas ruas da cidade! 🚓🚶‍♂️🚕
"""
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


# ... (A função on_member_update continua aqui, igual a antes) ...
@client.event
async def on_member_update(before, after):
    ID_DO_CARGO_GATILHO = 123456789012345678 # Lembre-se de configurar estes IDs
    ID_DO_CANAL_ANUNCIO = 123456789012345678
    ID_DO_CARGO_PING    = 123456789012345678

    cargo_gatilho = after.guild.get_role(ID_DO_CARGO_GATILHO)
    canal_anuncio = after.guild.get_channel(ID_DO_CANAL_ANUNCIO)

    if not cargo_gatilho or not canal_anuncio:
        # print("ERRO: Cargo de gatilho ou Canal de anúncio não encontrado. Verifique os IDs.")
        return

    if cargo_gatilho not in before.roles and cargo_gatilho in after.roles:
        embed_parceria = discord.Embed(title="🤝 Nova Parceria Fechada!", description=f"Temos o prazer de anunciar uma nova parceria com o membro {after.mention}!", color=discord.Color.gold())
        if after.display_avatar:
            embed_parceria.set_thumbnail(url=after.display_avatar.url)
        embed_parceria.set_footer(text=f"Membro desde: {after.joined_at.strftime('%d/%m/%Y') if after.joined_at else 'Data indisponível'}")
        mensagem_ping = f"Atenção, <@&{ID_DO_CARGO_PING}>!"
        print(f"Anunciando nova parceria com {after.name} no canal {canal_anuncio.name}.")
        await canal_anuncio.send(content=mensagem_ping, embed=embed_parceria)


# --- INICIA O BOT ---
client.run(TOKEN)
