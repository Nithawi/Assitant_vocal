import edge_tts
import asyncio
import os
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import json
import queue
import webbrowser as wb
import time 
import psutil
from playsound3 import playsound
import imageio_ffmpeg
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import requests

#debug

debug= True
#open colpilot = ctrl + 7

# variables

text = ""
assistant_actif = False
commande_id = -1

#commande dictionnaire
                   
liste_commandes = ["stop", #0
                   "ouvre", #1
                   "lance", #2
                   "joue",  #3
                   "cherche", #4
                   "recherche", #5
                   "chercher", #6
                   "heures", #7
                   "heure", #8
                   "messages", #9
                   "ferme", #10
                   "video", #11
                   "vidéo", #12
                   "fermer", #13  
                   "kawaii", #14
                    "gueule",  #15
                    "tommy", #16
                    "polo", #17
                    "volume", #18
                    "baisse", #19
                    "augmente", #20
                    "ajoute", #21
                    "retire" #22
                   ]

dictionnaire_site = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "twitter": "https://www.twitter.com",
    "instagram": "https://www.instagram.com",
    "netflix": "https://www.netflix.com",
    "devoir": "https://0860037y.index-education.net/pronote/eleve.html?identifiant=HW8EfPwbMGPXEkPp",
    "emploi du temps": "https://0860037y.index-education.net/pronote/UrlUnique/Emploi%20du%20temps%20annuel%20de%20SOUCHAUD%20Timeo%20-%202025-2026.pdf?S=1977996&ID=BC01427C25544B4EB07F7F709D23433973951261716319"
}

dictionnaire_application = {
    "steam": "D:\\steam\\steam.exe",
    "discorde": "C:\\Users\\Utilisateur\\AppData\\Local\\Discord\\Update.exe",
    "musique":"C:\\Users\\Utilisateur\\AppData\\Local\\Programs\\deezer-desktop\\Deezer.exe",
    "fichier": "C:\\Windows\\explorer.exe",
    "ohio play": "C:\\Program Files\\HoYoPlay\\launcher.exe",
    "kuro": "D:\\Wuthering Waves\\launcher.exe",
    "google": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
}

# Constants

SAMPLE_RATE = 16000
MODEL_PATH = "vosk-model-small-fr-0.22"  # Path to the Vosk model directory
q = queue.Queue()

# initinalisation model

model = Model(MODEL_PATH)
recognizer = KaldiRecognizer(model, SAMPLE_RATE)

# fonctions


def audio_callback(indata, frames, time, status):
    if status:
        print(status, flush=True)
    q.put(bytes(indata))

# speech to text

def ecouter():
    global text
    try:
        data = q.get(timeout=2)
    except queue.Empty:
        print("micro desactivé")
        return ""
    
    if recognizer.AcceptWaveform(data):
        result = recognizer.Result()
        text = json.loads(result)["text"]
        if text:
            print(f"Vous avez dit: {text}")
            return text
    return ""

# text to speech

def dire(phrase):
    asyncio.run(parler(phrase))

async def parler(phrase):
    if os.path.exists("temp.mp3"):
        os.remove("temp.mp3")

    communicate = edge_tts.Communicate(phrase, voice = "fr-CH-ArianeNeural")
    await communicate.save("temp.mp3")
    playsound("temp.mp3")
    os.remove("temp.mp3")

# volume
def set_system_volume(level):
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    volume.SetMasterVolumeLevelScalar(level, None)

def change_system_volume(delta):
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    current = volume.GetMasterVolumeLevelScalar()
    new_level = min(max(current + delta, 0.0), 1.0)
    volume.SetMasterVolumeLevelScalar(new_level, None)

#detect commandes

def detection_commande():
        global commande_id
        commande_id = -1

        #diviser 
        texte_split = text.lower().split()
        for mot in texte_split:
            if mot in liste_commandes:
                commande_id = liste_commandes.index(mot)
            if debug:
                    print(f"commande détectée: {mot} (id: {commande_id})")
            


def change_chrome_volume(delta):
    for proc in psutil.process_iter(['name', 'pid']):
        if proc.info['name'] == "chrome.exe":
            sessions = AudioUtilities.GetAllSessions()
            for session in sessions:
                if session.Process and session.Process.pid == proc.info['pid']:
                    volume = session._ctl.QueryInterface(IAudioEndpointVolume)
                    current = volume.GetMasterVolumeLevelScalar()
                    new_level = min(max(current + delta, 0.0), 1.0)
                    volume.SetMasterVolumeLevelScalar(new_level, None)
                    return True
    return False

#envoyer message discord

# def envoyer_message_discord(message, webhook_url):
#     webhook = DiscordWebhook(url=webhook_url, content=message)
#     response = webhook.execute()

# executer commande

def executer_commande():
    global commande_id
    if commande_id == 0: # stop
        dire("Au revoir")
        exit()

    # ouvrir site

    elif commande_id == 1: # ouvre
        site = ""
        for nom_site in dictionnaire_site.keys():
            if nom_site in text.lower():
                site = dictionnaire_site[nom_site]
                break
        if site:
            dire(f"J'ouvre {nom_site}")
            wb.open(site)
        else:
            dire("Je n'ai pas compris le site à ouvrir.")
    
    # lance application

    elif commande_id == 2: # lance
        application = ""
        trouver = False
        for nom_app in dictionnaire_application.keys():
            if nom_app in text.lower():
                trouver = True
                application = dictionnaire_application[nom_app]
                dire(f"Je lance {nom_app}")
                try:
                    os.startfile(application)
                    break
                except Exception as e:
                    dire(f"Je n'ai pas pu lancer {nom_app}.")
                    if debug:
                        print(f"Erreur lors du lancement de l'application: {e}")
        if not trouver:
            dire("Je n'ai pas trouvé l'appilcation.")

    
    # rechercher dans google
    elif commande_id in [4, 6, 5]: # cherche  ou chercher
        mots = text.lower().split()
        # Retire le mot 'cherche' ou 'recherche' pour garder la requête
        requete = " ".join([mot for mot in mots if mot not in ["cherche", "recherche", "chercher"]])
        if requete:
            url = f"https://www.google.com/search?q={requete.replace(' ', '+')}"
            dire(f"Je recherche {requete} sur Google")
            wb.open(url)
        else:
            dire("Je n'ai pas compris ce que je dois rechercher.")

    # dire l'heure
    elif commande_id == 7 or commande_id == 8: # heures heure
        heure_actuelle = time.strftime("%H:%M")
        dire(f"Il est {heure_actuelle}")

    # recherche youtube
    elif commande_id in [12, 11]: #recherche youtube
        mots = text.lower().split()
        # Retire le mot 'cherche' ou 'recherche' pour garder la requête
        requete = " ".join([mot for mot in mots if mot not in ["vidéo", "video"]])
        if requete:
            url = f"https://www.youtube.com/results?search_query={requete.replace(' ', '+')}"
            dire(f"Je recherche {requete} sur YouTube")
            wb.open(url)
        else:
            dire("Que dois-je rechercher ?")

    # fermer application
    
    elif commande_id in [10, 13]:  # ferme ou fermer
        mots = text.lower().split()
        for nom_app in dictionnaire_application.keys():
            if nom_app in mots:
                # Récupère le nom du fichier exécutable
                exe_name = os.path.basename(dictionnaire_application[nom_app])
                # Ferme tous les processus correspondants
                found = False
                for proc in psutil.process_iter(['name']):
                    if proc.info['name'] == exe_name:
                        proc.terminate()
                        found = True
                if found:
                    dire(f"J'ai fermé {nom_app}")
                else:
                    dire(f"{nom_app} n'était pas ouvert.")
                break
        else:
            dire("Je n'ai pas trouvé l'application à fermer.")

    # volume general

    elif commande_id == 18:  # volume
        set_system_volume(0.5)
        dire("Volume général réglé à 50 pourcent.")

    elif commande_id == 19:  # baisse
        change_system_volume(-0.1)
        dire("Volume général baissé.")

    elif commande_id == 20:  # augmente
        change_system_volume(0.1)
        dire("Volume général augmenté.")
    #son

    elif commande_id == 14 :
        playsound("son\\uwu.mp3")
        print("(⁄ ⁄•⁄ω⁄•⁄ ⁄)⁄")

    elif commande_id == 15 :
        playsound("son\\geule.mp3")
        print("Ta geule")

    elif commande_id == 16 :
        playsound("son\\tomi.mp3")
        print("Tommy")

    elif commande_id == 17 :
        playsound("son\\pollo.mp3")
        print("Pollo")


    # envoyer message discord
    # elif commande_id == 9:  # Supposons que tu ajoutes "discord" à liste_commandes
    #     webhook_url = "https://discord.com/api/webhooks/TON_WEBHOOK_ID/TON_TOKEN"
    #     message = text  # Ou extrais le message à envoyer
    #     envoyer_message_discord(message, webhook_url)
    #     dire("Message envoyé sur Discord.")

# main  loop
with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=8000, dtype="int16", channels=1, callback=audio_callback):

    try:
        while True:
            text=ecouter()
            print("ecoute...")
            if "cookie" in text.lower() or "craquelins" in text.lower():
                print(f"Vous avez dit {text}")
                dire("Que puis-je faire pour vous ?")
                assistant_actif = True
                continue

            if assistant_actif and text:
                assistant_actif = False
                detection_commande()
                executer_commande()
        
    except KeyboardInterrupt:
        print("\nFin du programme")