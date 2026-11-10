import datetime
import os
import discord
from discord.ext import commands
from discord import app_commands, TextStyle

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Database in memoria per Staff, Ore e Sanzioni
turni_attivi_staff = {}
ore_servizio_staff = {}
database_sanzioni = {}  # {user_id: [{"id": 1, "tipo": "...", "motivazione": "...", "staff": "..."}, ...]}

# ID del canale log (puoi impostarlo o lasciarlo attivo sul canale del comando)
CANALE_LOG_ID = 0  

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Bot Principale Trani RP online come {bot.user} e comandi sincronizzati!")


# ==================== 1. SISTEMA SANZIONI (WARN / SANZIONA) ====================

@bot.tree.command(name="sanziona", description="Emetti una sanzione ufficiale a un utente")
@app_commands.describe(utente="L'utente da sanzionare", tipo="Tipo di sanzione (es. Avvertimento, Warn, Sospensione)", motivazione="Motivazione dettagliata")
async def sanziona(interaction: discord.Interaction, utente: discord.User, tipo: str, motivazione: str):
    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message("❌ Non hai i permessi per sanzionare gli utenti.", ephemeral=True)
        return

    user_id = utente.id
    if user_id not in database_sanzioni:
        database_sanzioni[user_id] = []
    
    sanzione_id = len(database_sanzioni[user_id]) + 1
    dati_sanzione = {
        "id": sanzione_id,
        "tipo": tipo,
        "motivazione": motivazione,
        "staff": interaction.user.name,
        "data": datetime.datetime.now().strftime('%d/%m/%Y %H:%M')
    }
    database_sanzioni[user_id].append(dati_sanzione)
    totale_sanzioni = len(database_sanzioni[user_id])

    embed = discord.Embed(
        title="⚠️ REGISTRAZIONE SANZIONE | Trani RP",
        description=f"L'utente {utente.mention} ha ricevuto una sanzione ufficiale.",
        color=discord.Color.orange()
    )
    embed.add_field(name="👤 Utente Sanzionato", value=utente.mention, inline=False)
    embed.add_field(name="📌 Tipo Sanzione", value=tipo, inline=True)
    embed.add_field(name="🔢 ID Sanzione", value=f"#{sanzione_id} (Totali: {totale_sanzioni})", inline=True)
    embed.add_field(name="📝 Motivazione", value=motivazione, inline=False)
    embed.add_field(name="🛠️ Staff Responsabile", value=interaction.user.mention, inline=False)
    embed.set_footer(text=f"Trani RP • Log Sanzioni | {dati_sanzione['data']}")

    # Invia notifica in privato all'utente
    try:
        await utente.send(embed=embed)
    except:
        pass

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="togli-sanzione", description="Rimuovi una sanzione specifica da un utente")
@app_commands.describe(utente="L'utente a cui rimuovere la sanzione", sanzione_id="ID numerico della sanzione da rimuovere")
async def togli_sanzione(interaction: discord.Interaction, utente: discord.User, sanzione_id: int):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Comando riservato agli amministratori.", ephemeral=True)
        return

    user_id = utente.id
    if user_id in database_sanzioni:
        for s in database_sanzioni[user_id]:
            if s["id"] == sanzione_id:
                database_sanzioni[user_id].remove(s)
                embed = discord.Embed(
                    title="🗑️ SANZIONE RIMOSSA",
                    description=f"La sanzione **#{sanzione_id}** ({s['tipo']}) è stata rimossa all'utente {utente.mention}.",
                    color=discord.Color.green()
                )
                embed.set_footer(text=f"Rimosso da {interaction.user.name}")
                await interaction.response.send_message(embed=embed)
                return

    await interaction.response.send_message("❌ Nessuna sanzione trovata con questo ID per l'utente specificato.", ephemeral=True)


@bot.tree.command(name="lista-sanzioni", description="Mostra lo storico delle sanzioni di un utente")
@app_commands.describe(utente="L'utente di cui visualizzare lo storico")
async def lista_sanzioni(interaction: discord.Interaction, utente: discord.User):
    user_id = utente.id
    sanzioni = database_sanzioni.get(user_id, [])

    embed = discord.Embed(
        title=f"📋 Storico Sanzioni: {utente.name}",
        color=discord.Color.blue()
    )
    
    if not sanzioni:
        embed.description = "Questo cittadino non ha alcuna sanzione registrata nel database. Fedina pulita! ✨"
    else:
        desc = ""
        for s in sanzioni:
            desc += f"**ID #{s['id']}** | *Tipo:* {s['tipo']} | Data: {s['data']}\n📝 *Motivo:* {s['motivazione']}\n🛠️ *Staff:* {s['staff']}\n\n"
        embed.description = desc

    await interaction.response.send_message(embed=embed)


# ==================== 2. COMANDI REGOLAMENTO / REQUISITI ====================

@bot.tree.command(name="requisiti-permadeath", description="Invia il regolamento permadeath di Trani RP")
async def requisiti_permadeath(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📜 Regolamento Permadeath | Trani RP",
        description="Il Permadeath decreta la morte biologica e la fine permanente della storia di un personaggio all'interno di **Trani RP**.",
        color=discord.Color.dark_red()
    )
    embed.add_field(name="📋 Requisiti", value="• Almeno 5 motivi validi.\n• Epilogo coerente di una traccia RP solida.\n• Clip video integrale dell'evento.", inline=False)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="requisiti-permajail", description="Invia il regolamento permajail di Trani RP")
async def requisiti_permajail(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🔒 Regolamento PermaJail | Trani RP",
        description="Il PermaJail rappresenta la detenzione a vita del personaggio senza possibilità di rilascio.",
        color=discord.Color.dark_orange()
    )
    embed.add_field(name="🚨 Condizioni", value="• Sentenza Giudiziaria irrevocabile dal Tribunale.\n• Criminalità di alto livello o atti eversivi.", inline=False)
    await interaction.response.send_message(embed=embed)


# ==================== 3. REGISTRAZIONE PERMADEATH / PERMAJAIL ====================

@bot.tree.command(name="permadeath", description="Registra un Permadeath (Riservato)")
@app_commands.describe(nome="Nome RP", utente="Utente Discord", motivazione="Motivazione dettagliata")
async def permadeath(interaction: discord.Interaction, nome: str, utente: discord.User, motivazione: str):
    ROLE_ID = 1563921698531840210
    if not any(role.id == ROLE_ID for role in interaction.user.roles):
        await interaction.response.send_message("❌ Non hai i permessi necessari per eseguire questo comando.", ephemeral=True)
        return

    embed = discord.Embed(
        title="⚰️ REGISTRAZIONE PERMADEATH",
        description=f"Il personaggio **{nome}** è stato dichiarato deceduto in via definitiva.",
        color=discord.Color.dark_embed()
    )
    embed.add_field(name="👤 Nome RP", value=nome, inline=False)
    embed.add_field(name="👤 Utente Discord", value=utente.mention, inline=False)
    embed.add_field(name="📝 Motivazione", value=motivazione, inline=False)
    embed.add_field(name="🛠️ Registrato da", value=interaction.user.mention, inline=False)
    embed.set_footer(text=f"Trani RP • {datetime.datetime.now().strftime('%d/%m/%Y, %H:%M')}")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="permajail", description="Registra un PermaJail (Riservato)")
@app_commands.describe(nome="Nome RP", utente="Utente Discord", motivazione="Motivazione dettagliata")
async def permajail(interaction: discord.Interaction, nome: str, utente: discord.User, motivazione: str):
    ROLE_ID = 1563921697629798454
    if not any(role.id == ROLE_ID for role in interaction.user.roles):
        await interaction.response.send_message("❌ Non hai i permessi necessari per eseguire questo comando.", ephemeral=True)
        return

    embed = discord.Embed(
        title="⛓️ REGISTRAZIONE PERMAJAIL",
        description=f"Il personaggio **{nome}** è stato condannato alla prigione permanente.",
        color=discord.Color.from_rgb(139, 0, 0)
    )
    embed.add_field(name="👤 Nome RP", value=nome, inline=False)
    embed.add_field(name="👤 Utente Discord", value=utente.mention, inline=False)
    embed.add_field(name="📝 Motivazione", value=motivazione, inline=False)
    embed.add_field(name="🛠️ Registrato da", value=interaction.user.mention, inline=False)
    embed.set_footer(text=f"Trani RP • {datetime.datetime.now().strftime('%d/%m/%Y, %H:%M')}")
    await interaction.response.send_message(embed=embed)


# ==================== 4. STATO SERVER (SSD / SSU) ====================

@bot.tree.command(name="ssd", description="Annuncia la chiusura del server (SSD)")
async def ssd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🔴 · TRANI RP – SSD CHIUSO 🚀",
        description="Il server di Trani RP è ufficialmente offline. 🇮🇹\n🎮 Codice server: `pcitpp2k`\n🔴 Stato: **OFFLINE**",
        color=discord.Color.red()
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="ssu", description="Annuncia l'apertura del server (SSU)")
async def ssu(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🟢 · TRANI RP – SERVER APERTO 🚀",
        description="Il server di Trani RP è ufficialmente online! 🇮🇹\n🎮 Codice server: `pcitpp2k`\n🟢 Stato: **ONLINE**",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)


# ==================== 5. MODALS & VIEWS ====================

class CittadinanzaModal(discord.ui.Modal, title="Modulo Richiesta Cittadinanza"):
    nome_rp = discord.ui.TextInput(label="Nome e Cognome RP", placeholder="Es. Mario Rossi", required=True)
    eta_rp = discord.ui.TextInput(label="Età del Personaggio", placeholder="Es. 25", required=True)
    storia = discord.ui.TextInput(label="Breve Background / Storia RP", style=TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("✅ La tua richiesta di cittadinanza è stata inviata allo Staff!", ephemeral=True)


class CittadinanzaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Richiedi Cittadinanza 🪪", style=discord.ButtonStyle.primary, custom_id="req_cittadinanza")
    async def richiedi(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CittadinanzaModal())


class PortoDArmiView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Richiedi Porto d'Armi 🔫", style=discord.ButtonStyle.success, custom_id="req_porto_armi")
    async def richiedi(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("✅ Richiesta porto d'armi inoltrata alle autorità!", ephemeral=True)


class PatenteView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Richiedi Esame Patente 🚗", style=discord.ButtonStyle.primary, custom_id="req_patente")
    async def richiedi(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("✅ Richiesta esame patente registrata!", ephemeral=True)


class TurniStaffView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Inizia Turno 🟢", style=discord.ButtonStyle.green, custom_id="inizia_turno_staff")
    async def inizia(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if user_id in turni_attivi_staff:
            await interaction.response.send_message("❌ Sei già in turno Staff!", ephemeral=True)
            return
        turni_attivi_staff[user_id] = datetime.datetime.now()
        await interaction.response.send_message("🟢 Turno Staff iniziato!", ephemeral=True)

    @discord.ui.button(label="Termina Turno 🔴", style=discord.ButtonStyle.red, custom_id="termina_turno_staff")
    async def termina(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if user_id not in turni_attivi_staff:
            await interaction.response.send_message("❌ Non hai un turno attivo.", ephemeral=True)
            return

        start_time = turni_attivi_staff.pop(user_id)
        durata = datetime.datetime.now() - start_time
        secondi = int(durata.total_seconds())
        ore_servizio_staff[user_id] = ore_servizio_staff.get(user_id, 0) + secondi
        ore = secondi // 3600
        minuti = (secondi % 3600) // 60

        await interaction.response.send_message(f"🔴 Turno terminato! Sessione: **{ore}h e {minuti}m**.", ephemeral=True)


# ==================== 6. COMANDI PANNELLI ====================

@bot.tree.command(name="pannello-cittadinanza", description="Invia il pannello cittadinanza")
async def pannello_cittadinanza(interaction: discord.Interaction):
    embed = discord.Embed(title="🪪 Richiesta Cittadinanza | Trani RP", description="Clicca sotto per richiedere la cittadinanza.", color=discord.Color.blue())
    await interaction.response.send_message(embed=embed, view=CittadinanzaView())


@bot.tree.command(name="pannello-porto-darmi", description="Invia il pannello porto d'armi")
async def pannello_porto_darmi(interaction: discord.Interaction):
    embed = discord.Embed(title="🔫 Gestione Porto d'Armi | Trani RP", description="Avvia la procedura per la licenza d'armi.", color=discord.Color.gold())
    await interaction.response.send_message(embed=embed, view=PortoDArmiView())


@bot.tree.command(name="pannello-patente", description="Invia il pannello patente")
async def pannello_patente(interaction: discord.Interaction):
    embed = discord.Embed(title="🚗 Scuola Guida & Patenti | Trani RP", description="Richiedi l'esame per la patente di guida.", color=discord.Color.dark_green())
    await interaction.response.send_message(embed=embed, view=PatenteView())


@bot.tree.command(name="pannello-turni", description="Invia il pannello turni staff")
async def pannello_turni(interaction: discord.Interaction):
    embed = discord.Embed(title="📊 Gestione Turni Staff | Trani RP", description="Gestisci il tuo servizio staff.", color=discord.Color.purple())
    await interaction.response.send_message(embed=embed, view=TurniStaffView())


# ==================== 7. COMANDI ORE STAFF ====================

@bot.tree.command(name="mostra-ore-servizio", description="Mostra le ore di servizio Staff")
async def mostra_ore_servizio(interaction: discord.Interaction, utente: discord.User = None):
    target = utente or interaction.user
    user_id = target.id
    secondi_totali = ore_servizio_staff.get(user_id, 0)
    stato = "Fuori servizio"

    if user_id in turni_attivi_staff:
        secondi_totali += int((datetime.datetime.now() - turni_attivi_staff[user_id]).total_seconds())
        stato = "In servizio"

    ore = secondi_totali // 3600
    minuti = (secondi_totali % 3600) // 60

    embed = discord.Embed(title="⏱️ Ore Servizio Staff", color=discord.Color.purple())
    embed.add_field(name="Staffer", value=target.mention, inline=False)
    embed.add_field(name="Ore Totali", value=f"**{ore}h e {minuti}m**", inline=False)
    embed.add_field(name="Stato", value=stato, inline=False)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="rimuovi-ore", description="Rimuovi ore staff a un utente")
async def rimuovi_ore(interaction: discord.Interaction, utente: discord.User, ore: int, minuti: int = 0):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Solo gli amministratori possono farlo.", ephemeral=True)
        return
    user_id = utente.id
    secondi_da_scalare = (ore * 3600) + (minuti * 60)
    ore_servizio_staff[user_id] = max(0, ore_servizio_staff.get(user_id, 0) - secondi_da_scalare)
    await interaction.response.send_message(f"📉 Scalate {ore}h e {minuti}m a {utente.mention}.", ephemeral=True)


bot.run(os.getenv("DISCORD_TOKEN"))
