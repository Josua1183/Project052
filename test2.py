import requests

BASE_URL = "https://discord.com/api/v10"
TOKEN = "MTI2MDYxNTAwNjk2MjMyMzU4Ng.GKIcaQ.GsYPtuP9bDnCHmyfv9li1oL29PzSBOwH2lPgck"


def remove_role(guild_id, user_id, role_id):
    url = f"{BASE_URL}/guilds/{guild_id}/members/{user_id}/roles/{role_id}"
    headers = {
        "Authorization": f"Bot {TOKEN}"
    }

    response = requests.delete(url, headers=headers)

    if response.status_code == 204:
        print("Rolle wurde erfolgreich entfernt.")
    else:
        print(f"Fehler: {response.status_code} - {response.json()}")


# Beispielwerte
guild_id = "1248352430366920875"
user_id = "1032657055271628881"
role_id = "1314187574708928539"

remove_role(guild_id, user_id, role_id)
