# SEU ARQUIVO main.py COMPLETO E ATUALIZADO

import discord
from discord import app_commands # Importa a biblioteca para slash commands
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Configuração das Intents
intents = discord.Intents.default()
intents.members = True
intents.messages = True

client = discord.Client(intents=intents)
# Cria uma "árvore de comandos" para o nosso bot
tree = app_commands.CommandTree(client)

# --- COMANDO DE BARRA /ping ---
# Este decorator registra o comando no Discord
@tree.command(name="ping", description="Testa se o bot está respondendo.")
async def ping(interaction: discord.Interaction):
    """Responde com Pong!"""
    await interaction.response.send_message("Pong! 🏓")

# ADICIONE ESTE NOVO BLOCO DE CÓDIGO ABAIXO DO COMANDO /ping

# --- COMANDO DE BARRA /ip ---
@tree.command(name="ip", description="Mostra o endereço de IP para se conectar ao servidor SAMP.")
async def ip(interaction: discord.Interaction):
    """Envia uma mensagem bonita com o IP do servidor."""
    
    # Cria a mensagem usando um Embed, para ficar mais estilizado
    embed_ip = discord.Embed(
        title="🚀 Conecte-se ao Altura RolePlay City!",
        description="Use o IP abaixo para entrar na melhor cidade do SAMP!",
        color=discord.Color.blue() # Ou qualquer outra cor que você goste
    )
    
    # Adiciona o campo principal com o IP, fácil de copiar
    embed_ip.add_field(name="Endereço do Servidor:", value="`179.127.16.157:29015`", inline=False)
    
    # Adiciona um rodapé para dar um toque final
    embed_ip.set_footer(text="Clique no IP para copiar. Te vemos lá!")
    
    # Envia a mensagem para o usuário que digitou o comando
    await interaction.response.send_message(embed=embed_ip)
@client.event
async def on_ready():
    """Função chamada quando o bot se conecta com sucesso."""
    # Sincroniza os comandos de barra com o Discord
    await tree.sync()
    print("Comandos de barra sincronizados.")
    
    print(f'{client.user} conectou-se ao Discord!')
    print('Bot está online e pronto para uso.')


@client.event
async def on_member_join(member):
    # ... (SUA FUNÇÃO DE BOAS-VINDAS CONTINUA EXATAMENTE IGUAL AQUI)
    # ... (NÃO PRECISA MUDAR NADA DENTRO DELA)
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

        embed = discord.Embed(
            description=description_text,
            color=discord.Color.from_rgb(70, 130, 180) # Um tom de azul "céu"
        )

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


client.run(TOKEN)
