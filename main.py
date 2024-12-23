import discord
from discord.ext import commands, tasks

import nest_asyncio
import json
import requests
from datetime import datetime, timedelta
from typing import Optional
import os

TOKEN = os.getenv("TOKEN")
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

with open("questions.json", "r") as f:
    data = json.load(f)

current_question_index = 0  # Variable zum Verfolgen der aktuellen Frage

class FeedbackModal(discord.ui.Modal, title="Feedback"):
    feedback_input = discord.ui.TextInput(
        label="Dein Feedback",
        style=discord.TextStyle.long,
        placeholder="Schreib hier dein Feedback...",
        required=True,
        min_length=10,
        max_length=2000
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Erstelle die Buttons für die kombinierte View
        view = Questionview("Bearbeiten")
        view2 = Questionview("Noch ein Feedback")
        for item in view2.children:
            view.add_item(item)
        await interaction.response.send_message(
            f"Danke für dein Feedback!\n\nDu hast geschrieben:\n{self.feedback_input.value}",
            ephemeral=True, view=view
        )
        try:
            with open("feedback.json", "r") as f:
                feedback_data = json.load(f)
                if str(interaction.user.id) in feedback_data:
                    feedback_data[str(interaction.user.id)].append(self.feedback_input.value)
                else:
                    feedback_data[str(interaction.user.id)] = [self.feedback_input.value]
        except FileNotFoundError:
            feedback_data = {}
            feedback_data[str(interaction.user.id)] = [self.feedback_input.value]

        with open("feedback.json", "w") as f:
            json.dump(feedback_data, f)


# Du müsstest auch die interaction_check Methode in deiner Questionview anpassen,
# um die custom_ids der neuen Buttons zu berücksichtigen.
class Questionview(discord.ui.View):
    def __init__(self, label, timeout=180):
        super().__init__(timeout=timeout)
        self.message = None
        self.label = label
        if label == "Bearbeiten":
            self.add_item(
                discord.ui.Button(label=self.label, style=discord.ButtonStyle.primary, custom_id="bearbeiten_button"))
        elif label == "Noch ein Feedback":
            self.add_item(discord.ui.Button(label=self.label, style=discord.ButtonStyle.secondary,
                                            custom_id="feedback_button"))
        elif label == "Feedback senden":
            self.add_item(
                discord.ui.Button(label=self.label, style=discord.ButtonStyle.primary, custom_id="feedback_button"))
        else:
            self.add_item(
                discord.ui.Button(label=self.label, style=discord.ButtonStyle.primary, custom_id="question_button"))

    async def on_timeout(self):
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
        if self.message:
            await self.message.edit(view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.data["custom_id"] == "question_button":
            try:
                with open("data.json", "r") as f:
                    data1 = json.load(f)
            except FileNotFoundError:
                data1 = []
            # Überprüfe, ob alle Fragen beantwortet wurden
            if len(data1) >= len(data):
                await interaction.response.send_message(
                    "Du hast alle Fragen beantwortet! Vielen Dank!",
                    ephemeral=True
                )
                return False  # Beende die Funktion, wenn alle Fragen beantwortet wurden

                question = data[len(data1)]
                await interaction.response.send_modal(QuestionModal(question))
        elif interaction.data["custom_id"] == "bearbeiten_button":
            print("Hallo")
            # Hier die Logik für den "Bearbeiten" Button einfügen
            await interaction.response.send_message("Du hast auf 'Bearbeiten' geklickt!", ephemeral=True)
        elif interaction.data["custom_id"] == "feedback_button":
            await interaction.response.send_modal(FeedbackModal())

        return True


class QuestionModal(discord.ui.Modal, title="Train AI"):
    def __init__(self, question):
        super().__init__()
        self.question = question
        self.question_input = discord.ui.TextInput(
            label="Beantworte hier ehrlich die Frage...",
            style=discord.TextStyle.long,
            placeholder=self.question,
            required=True,
            min_length=5,
            max_length=1000
        )
        self.add_item(self.question_input)

    async def on_submit(self, interaction: discord.Interaction):
        user = interaction.user  # Hole das Member-Objekt direkt
        person = str(user.id)  # Name für die Nachrichten
        answer = self.question_input.value
        print(f"Frage: {self.question}\nAntwort: {answer}")

        try:
            with open("persons.json", "r") as f:
                persons = json.load(f)
            with open("helpers.json", "r") as f:
                helpers = json.load(f)
        except FileNotFoundError:
            persons = {}
            helpers = {}

        message = ""
        if person in helpers:
            message = ""
            helpers[person]["count"] += 1
        else:
            expiry_date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
            helpers[person] = {"expiry_date": expiry_date, "count": 1}

            role_id = 1314187574708928539  # Definiere die Rollen-ID hier
            role = interaction.guild.get_role(role_id)
            if role:
                try:
                    await user.add_roles(role)
                    message += f"\nDu hast die Rolle '{role.name}' erhalten!"
                except discord.Forbidden:
                    message += "\nIch konnte dir die Helper-Rolle nicht zuweisen (fehlende Berechtigungen)."
                except Exception as e:
                    message += f"\nFehler beim Zuweisen der Rolle: {e}"
            else:
                message += f"\nDie Helper-Rolle mit der ID {role_id} wurde nicht gefunden."

        with open("helpers.json", "w") as f:
            json.dump(helpers, f)

        if person in persons:
            persons[person] += 1
        else:
            persons[person] = 1

        with open("persons.json", "w") as f:
            json.dump(persons, f)

        try:
            with open("data.json", "r") as f:
                data1 = json.load(f)
        except FileNotFoundError:
            data1 = []
        data1.append({"question": self.question, "answer": answer})
        with open("data.json", "w") as f:
            json.dump(data1, f)

        if persons[person] > 1:
            response_message = f"Danke <@{person}>, dass du {persons[person]} Fragen beantwortet hast:\n**Frage:** {self.question}\n**Deine Antwort:** {answer}"
        else:
          response_message = f"Danke <@{person}>, dass du deine erste Frage beantwortet hast:\n**Frage:** {self.question}\n**Deine Antwort:** {answer}"

        if message:
            response_message += message


        view = Questionview("Nächste Frage beantowrten")
        await interaction.response.send_message(response_message, ephemeral=True, view=view)

@tree.command(name="question", description="Beantworte eine Frage")
async def question(interaction: discord.Interaction):
    view = Questionview("Frage beantworten")
    if view:
        view.message = await interaction.response.send_message(
            "Klicke auf den Button, um die Frage zu beantworten!", view=view,
            ephemeral=True
        )

@tree.command(name="feedback", description="Sende uns dein Feedback")
async def question(interaction: discord.Interaction):
    view = Questionview("Feedback senden")
    if view:
        view.message = await interaction.response.send_message(
            "Klicke auf den Button, um dein Feedback zu senden!", view=view,
            ephemeral=True
        )

@tree.command(name="statistic", description="Zeigt die Statistik der Fragenantworten an.")
@discord.app_commands.describe(person="Optional: Der Benutzer, dessen Statistik angezeigt werden soll.")
async def statistic(interaction: discord.Interaction, person: Optional[discord.User] = None):
    if person is None:
        person = interaction.user
    try:
        with open("persons.json", "r") as f:
            persons = json.load(f)
    except FileNotFoundError:
        persons = {}
    person_id = str(person.id)
    if person_id in persons:
        if persons[person_id] > 1:
            response = f"<@{person_id}> hat {persons[person_id]} Fragen beantwortet! "
        else:
            response = f"<@{person_id}> hat eine Frage beantwortet!"
        try:
            with open("helpers.json", "r") as f:
                helpers = json.load(f)
            if str(person.id) in helpers:
                delta = (datetime.strptime(helpers[str(person.id)]["expiry_date"], "%Y-%m-%d").date() - datetime.today().date() + timedelta(days=helpers[str(person.id)]["count"]))
                message = (f"Er hat noch {delta.days} Tage den Rang <@&1314187574708928539>!")
            else:
                message = f"Er hat den Rang <@&1314187574708928539> nicht mehr!"
        except FileNotFoundError:
            message = f"Er hat den Rang <@&1314187574708928539> nicht mehr!"
    else:
        response = f"<@{person.id}> hat noch keine Fragen beantwortet!"

    try:
        await interaction.response.send_message(response + message)
    except Exception as e:
        await interaction.response.send_message(response)

@tasks.loop(minutes=1)
async def my_five_minute_task():
    print("task")
    try:
        with open("helpers.json", "r") as f:
            helpers = json.load(f)
    except FileNotFoundError:
        helpers = {}
    heute = datetime.now().strftime("%Y-%m-%d")

    for person_id, data in list(helpers.items()):  # list() zum sicheren iterieren und löschen
        expiry_date_str = data.get("expiry_date")
        if expiry_date_str and datetime.strptime(expiry_date_str, "%Y-%m-%d").date() <= datetime.strptime(heute, "%Y-%m-%d").date():
            BASE_URL = "https://discord.com/api/v10"
            TOKEN = os.getenv("TOKEN")
            guild_id = os.getenv("GUILD_ID")
            role_id = "1314187574708928539"
            url = f"{BASE_URL}/guilds/{guild_id}/members/{person_id}/roles/{role_id}"
            headers = {
                "Authorization": f"Bot {TOKEN}"
            }

            response = requests.delete(url, headers=headers)

            if response.status_code == 204:
                print("Rolle wurde erfolgreich entfernt.")
                helpers.pop(person_id)
            else:
                print(f"Fehler: {response.status_code} - {response.json()}")

    with open("helpers.json", "w") as f:
        json.dump(helpers, f)

@bot.event
async def on_ready():
    print(f"Eingeloggt als {bot.user.name}")
    try:
        synced = await bot.tree.sync()
        print(f"Synchronisierte {len(synced)} Slash-Befehl(e)")
    except Exception as e:
        print(f"Fehler beim Synchronisieren von Slash-Befehlen: {e}")

    my_five_minute_task.start()


nest_asyncio.apply()
bot.run(TOKEN)