from bson import ObjectId
from flask import Flask
from pymongo import MongoClient
from ask_sdk_core.skill_builder import SkillBuilder
from flask_ask_sdk.skill_adapter import SkillAdapter
from ask_sdk_core.dispatch_components import (
    AbstractRequestHandler, AbstractExceptionHandler,
    AbstractResponseInterceptor, AbstractRequestInterceptor)
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model.ui import SimpleCard
from ask_sdk_model.ui import StandardCard
from ask_sdk_model.ui.image import Image
from ask_sdk_model import Response
from pyssml.AmazonSpeech import AmazonSpeech
from ssml_builder.core import Speech

from ask_sdk_model.slu.entityresolution.resolutions import Resolutions
from ask_smapi_model.v1.skill.evaluations.resolutions_per_authority_value_items import ResolutionsPerAuthorityValueItems
from ask_smapi_model.v1.skill.evaluations.slot_resolutions import SlotResolutions

from ask_sdk_model.dialog import (
    ElicitSlotDirective, DelegateDirective)
from ask_sdk_model import (
    Response, IntentRequest, DialogState, SlotConfirmationStatus, Slot)
from ask_sdk_model.slu.entityresolution import StatusCode
from ask_sdk_model import Response
import ask_sdk_core.utils as ask_utils

import time

app = Flask(__name__)

client = MongoClient(port=27017)
db = client['SpieleVonHades']
gameaccount = db['Accounts']
playerID="62017d66fbcb30f3ce904adb"
playerGender = ""
switchRightValue={'1': "1", '2': "-1", '3': "1", '4': "1", '5': "-1", '6': "-1"}
playerTimeStarted = 0
playerTimeEnded = 0
playerSavedTime = 0

sb = SkillBuilder()

Voice = Speech()
PlayerInnerVoice = Speech()


# lastSpeech for repeating due Amazon.RepeatIntent
def lastSpeech(speech, playerGender=""):
    if playerGender=='Vicki':
        gender="weiblich"
    elif playerGender=='Hans':
        gender="männlich"
    else:
        gender=""
    return {"LastSpeech": speech, "gender": gender}


# def IsTimeUp(): glob funk bei Handlungen abzuchecken, ob die Zeit abgleuafen ist.


class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        speech_text01 = "Willkommen im Spiel Escape Room - Spiele von Hades. "
        speech_text02 = "Falls du dir die Einleitung anhören möchtest, sage einfach: Einführung in das Spiel! Falls du einen Spielstand laden möchtest, sage " \
                        ": Spielstand laden"

        repromt_text = "Sage zum Fortfahren Einführung in das Spiel oder Spielstand laden!"

        handler_input.attributes_manager.session_attributes.update(lastSpeech(speech_text01 + speech_text02))

        # handler_input.attributes_manager.session_attributes.
        print(playerID)

        Voice.excited(speech_text01 + speech_text02, 'low')

        handler_input.response_builder.speak(Voice.speak()).ask(repromt_text) \
            .set_card(StandardCard("Willkommen in das Spiel Escape Room - Spiele von Hades", "",
                                   Image(
                                       "https://lincolnescaperoom.com/wp-content/uploads/2017/03/Escape-Room-Web-logo.png"))) \
            .set_should_end_session(False)
        return handler_input.response_builder.response


class LoadGameHistoryIntentHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("LoadGameHistoryIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        slots = handler_input.request_envelope.request.intent.slots
        gamerName = slots["gamerName"].value
        print("gamername in load" + gamerName)
        global playerID
        global playerGender
        cursor = gameaccount.find({'name': gamerName})
        results = list(cursor)

        # falls es keinen Spielstand mit gamerName existiert
        if len(results) == 0:
            speech_text = "Der Name wurde nicht gefunden. Bitte versuche es erneut."
            Voice.disappointed(speech_text)
        elif len(results) == 1:

            global playerID
            playerID = results[0]['_id']
            print("Testeapl id neu elif: " + str(results[0]['_id']))
            #playerGender = str(results[0]['gender'])
            if str(results[0]['gender'])=="männlich":
                playerGender='Hans'
            elif str(results[0]['gender'])=="weiblich":
                playerGender='Vicki'

            speech_text = "Du bist eingeloggt als " + str(
                gamerName) + ". Sage Spiel fortsetzen um weiterzuspielen"
            Voice.excited(speech_text, 'low')
        else:
            # wähle den Account mit größtem Spielstand aus

            newCursor = gameaccount.find({'name': gamerName}).sort('time', -1).limit(1)
            for document in newCursor:
                playerID = document['_id']
                print(" playerID:" + str(playerID))
                #playerGender = str(document['gender'])
                if str(results[0]['gender']) == "männlich":
                    playerGender = 'Hans'
                elif str(results[0]['gender']) == "weiblich":
                    playerGender = 'Vicki'

            speech_text = "Du bist eingeloggt als " + str(
                gamerName) + ". Sage Spiel fortsetzen um weiterzuspielen"
            Voice.excited(speech_text, 'low')

        handler_input.attributes_manager.session_attributes.update(lastSpeech(speech_text))
        handler_input.response_builder.speak(Voice.speak()).set_should_end_session(
            False)
        return handler_input.response_builder.response


class IntroductionIntentHandler(AbstractRequestHandler):
    """Handler for Hello World Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("IntroductionIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speech_text = "Ziel des Spiels ist es innerhalb von einer Stunde aus dem Raum zu Entkommen. Falls du nicht mehr weiterkommst, " \
                      "kannst du nach Hinweisen fragen. Der Spielename und der Stand werden gespeichert. " \
                      "Um deinen Namen zu speichern sage einfach: Der Spielername ist und deinen Namen"

        #Voice.excited(speech_text, 'low')

        repromt_text = "Welchen Spielernamen soll ich für dich speichern?"

        handler_input.attributes_manager.session_attributes.update(lastSpeech(speech_text))

        handler_input.response_builder.speak(speech_text).ask(repromt_text).set_should_end_session(
            False)
        return handler_input.response_builder.response


class StoreNameRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("StoreName")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        slots = handler_input.request_envelope.request.intent.slots
        name = slots["name"].value

        # frage nach obsein Name richtig verstanden wurde!!
        # fehlerbehandlung falls name bereits existent

        # switch: 0=neutral, -1=runter 1=hoch
        # position: center=c, ahead=a, right=r, back=b, left=l
        nameDoc = {
            'name': name,
            'gender': "",
            'position': "c",
            'lightFound': False,
            'lightOn': False,
            'time': 0,
            'switch': {'1': 0, '2': 0, '3': 0, '4': 0, '5': 0, '6': 0},
            'safeOpen': False,
            'door': "closed"
        }
        global playerID
        playerID = gameaccount.insert_one(nameDoc).inserted_id
        print(playerID)

        speech_text = "Der Name wurde gespeichert. Wähle ein Geschlecht aus, in das du hineinschlüpfen möchtest. " \
                      "Du hast weiblich und männlich zur Auswahl"
        Voice.excited(speech_text, 'low')

        handler_input.attributes_manager.session_attributes.update(lastSpeech(speech_text))

        handler_input.response_builder.speak(Voice.speak()).set_should_end_session(
            False)
        return handler_input.response_builder.response


class PlayerInnerVoiceIntentHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("PlayerInnerVoiceIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        slots = handler_input.request_envelope.request.intent.slots
        gender = slots["gender"].value

        # gameaccount.update_one({'gender':""}, {'$set': nameDoc})

        gameaccount.find_one_and_update({'_id': ObjectId(playerID.__str__())}, {'$set': {'gender': gender}})
        global playerGender
        if gender=="weiblich":
            playerGender='Vicki'
        elif gender=="männlich":
            playerGender='Hans'


        speech_text = "Dein Geschlecht wurde gespeichert. Jetzt kannst du das Spiel starten"
        Voice.excited(speech_text, 'low')

        handler_input.attributes_manager.session_attributes.update(lastSpeech(speech_text))
        handler_input.response_builder.speak(Voice.speak()).set_should_end_session(
            False)
        return handler_input.response_builder.response


class StartTheGameIntentHandler(AbstractRequestHandler):
    """Handler for Hello World Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("StartTheGameIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # falls der Spieler Spiel starten sagt, aber forsetzen meint.
        if gameaccount.distinct('lightFound', {'_id': ObjectId(playerID.__str__())}) == [True]:
            speech_text01 = "Wow. Du bist ja ein Fortgeschrittener! "
            speech_text02 = "Falls du vom letzten Stand weiterspielen willst, sage: Spiel fortsetzen. Du kannst aber auch komplett" \
                            "von Null anfangen, indem du einen neuen Spielernamen speicherst. Wie möchtest du fortfahren?"
            speech_text = speech_text02
            repromt_text = "Spiel Fortsetzen oder einen neuen Spielernamen anlegen?"
            handler_input.attributes_manager.session_attributes.update(lastSpeech(speech_text))
            Voice.excited(speech_text01, 'medium')
            Voice.add_text(Voice.excited(speech_text02, 'low', True))
        else:
            speech_text = "Es ist dunkel, es wäre gut wenn ich etwas sehen könnte"
            Voice.audio("soundbank://soundlibrary/nature/amzn_sfx_rain_01")

            #aufpassen dass gender stimme gesetzt ist
            Voice.add_text(Voice.voice(Voice.prosody(speech_text, 'slow', 'medium', 'soft', True), playerGender, True))

            repromt_text = "Falls du einen Hinweis möchtest, sage: Hinweis."
            handler_input.attributes_manager.session_attributes.update(lastSpeech(speech_text, playerGender))

            global playerTimeStarted
            playerTimeStarted = time.time()

        # hier entweder der Entführer oder die Gedanke des Spielers

        handler_input.response_builder.speak(Voice.speak()).ask(repromt_text).set_should_end_session(False)
        return handler_input.response_builder.response


class ContinueTheGameIntentHandler(AbstractRequestHandler):
    """Handler for Hello World Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.ResumeIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # falls der Spieler Spiel starten sagt, aber forsetzen meint.
        if gameaccount.distinct('gender', {'_id': ObjectId(playerID.__str__())}) != [""]:
            global playerTimeStarted
            playerTimeStarted = time.time()

            if gameaccount.distinct('door', {'_id': ObjectId(playerID.__str__())}) == ["open"]:
                speech_text = "Die Tür ist bereits offen, du bist bereits entkommen! "
                Voice.audio("soundbank://soundlibrary/ui/gameshow/amzn_ui_sfx_gameshow_bridge_01")
                Voice.add_text(Voice.excited(speech_text, 'medium', True))

            elif gameaccount.distinct('safeOpen', {'_id': ObjectId(playerID.__str__())}) == [True]:
                speech_text = "Du hast das letzte Mal sehr weit geschafft. Der Safe ist offen. Was ist da nur drin?"
                Voice.audio("soundbank://soundlibrary/doors/doors_key_lock/key_lock_07")
                Voice.add_text(Voice.excited(speech_text, 'low', True))
                Voice.add_text(Voice.audio("soundbank://soundlibrary/foley/amzn_sfx_clock_ticking_01", True))

            elif gameaccount.distinct('switch', {'_id': ObjectId(playerID.__str__())}) != [
                switchRightValue]:
                print(gameaccount.distinct('switch', {'_id': ObjectId(playerID.__str__())}))
                speech_text = "Die Schalter an der Wand! Wozu sind sie? "
                Voice.audio("soundbank://soundlibrary/nature/amzn_sfx_strong_wind_whistling_01")
                Voice.add_text(Voice.excited(speech_text, 'low', True))
                Voice.add_text(Voice.audio("soundbank://soundlibrary/foley/amzn_sfx_clock_ticking_01", True))

            elif gameaccount.distinct('lightFound', {'_id': ObjectId(playerID.__str__())}) == [True]:
                print(str(playerID))
                speech_text = "Du hast bereits eine Lichtquelle gefunden. Die größte Hürde hast du hinter dir.Viel Erfolg."
                Voice.audio("soundbank://soundlibrary/nature/amzn_sfx_strong_wind_desert_01")
                Voice.add_text(Voice.excited(speech_text, 'low', True))
                Voice.add_text(Voice.audio("soundbank://soundlibrary/foley/amzn_sfx_clock_ticking_01", True))
            else:
                speech_text = "Du steckst im dunklen Zimmer fest. Wo Schatten ist, ist auch Licht. Ach, oder war das umgekehrt? " \
                              "Naja.. Du hast noch  xmin Zeit. Viel Erfolg"
                Voice.audio("soundbank://soundlibrary/horror/horror_04")
                Voice.add_text(Voice.disappointed(speech_text, True))
                Voice.add_text(Voice.audio("soundbank://soundlibrary/foley/amzn_sfx_clock_ticking_01", True))
        else:
            speech_text = "Du musst zuerst ein Geschlecht auswählen, in das du hineinschlüpfen möchtest. Du hast " \
                          "weiblich oder männlich zur Auswahl. Wähle eins aus!"
            Voice.excited(speech_text, 'low')
        handler_input.attributes_manager.session_attributes.update(lastSpeech(speech_text))
        handler_input.response_builder.speak(Voice.speak()).set_should_end_session(
            False)
        return handler_input.response_builder.response


class PauseTheGameIntentHandler(AbstractRequestHandler):
    # """Handler for Hello World Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.PauseIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        global playerSavedTime
        cursor = gameaccount.find({'_id': playerID})
        for document in cursor:
            playerSavedTime = document['time']
            print(document['time'])

        playerTimeAlreadyPlayed = int(time.time() - playerTimeStarted + playerSavedTime)
        gameaccount.find_one_and_update({'_id': ObjectId(playerID.__str__())},
                                        {'$set': {'time': playerTimeAlreadyPlayed}})

        """
        if playerTimeAlreadyPlayed>=60:
            timeLeftAsString = str(3600-playerTimeAlreadyPlayed) +" Sekunden"
        else:
            timeLeftAsString=str(3600-playerTimeAlreadyPlayed)+" Sekunden"
        """

        # verbliebene Zeit ausgeben
        speech_text = "Du hast den Skill pausiert. Dein Spielstand ist lokal gespeichert. "
        handler_input.attributes_manager.session_attributes.update(lastSpeech(speech_text))

        handler_input.response_builder.speak(speech_text).set_should_end_session(
            False)
        return handler_input.response_builder.response


class InvalidLookForLightIntentHandler(AbstractRequestHandler):
    # """Handler for Hello World Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("InvalidLookForLightIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speech_text = "Es klappt nicht! Es ist zu dunkel! Es muss einfacher gehen!"
        # PlayerInnerVoice-uberracht
        #aufpasseb playergender soll gesetzt sein
        Voice.voice(Voice.prosody(speech_text, 'slow', 'medium', 'soft', True), playerGender)

        handler_input.attributes_manager.session_attributes.update(lastSpeech(speech_text, playerGender))
        handler_input.response_builder.speak(Voice.speak()).set_should_end_session(
            False)
        return handler_input.response_builder.response


class FlashlightInThePocketIntentHandler(AbstractRequestHandler):
    # """Handler for Hello World Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("FlashlightInThePocketIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        gameaccount.find_one_and_update({'_id': ObjectId(playerID.__str__())}, {'$set': {'lightFound': True}})

        speech_text = "Eine Taschenlampe! Gott sei Dank!"
        Voice.audio("soundbank://soundlibrary/cloth_leather_paper/cloth/cloth_01")
        Voice.add_text(Voice.voice(Voice.prosody(speech_text, 'medium', 'medium', 'loud', True), playerGender, True))

        handler_input.attributes_manager.session_attributes.update(lastSpeech(speech_text, playerGender))
        handler_input.response_builder.speak(Voice.speak()).set_should_end_session(
            False)
        return handler_input.response_builder.response


class LightOnIntentHandler(AbstractRequestHandler):
    # """Handler for Hello World Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("LightOnIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        # print(gameaccount.distinct('light', {'_id': ObjectId(playerID.__str__())}))
        if gameaccount.distinct('lightFound', {'_id': ObjectId(playerID.__str__())}) == [True]:
            gameaccount.find_one_and_update({'_id': ObjectId(playerID.__str__())}, {'$set': {'lightOn': True}})
            speech_text01 = "So! Jetzt sehe ich alles. "
            speech_text02 = "Was ist das? Das Bild? "
            speech_text03 = "Die Initialen von Hades?"
            speech_text = speech_text01 + speech_text02 + speech_text03

            Voice.audio("soundbank://soundlibrary/switches_levers/switches_levers_05")
            Voice.add_text(Voice.voice(Voice.prosody(speech_text01, 'medium', 'medium', 'loud', True), playerGender, True))
            Voice.add_text(Voice.pause('1s', True))
            Voice.add_text(Voice.voice(Voice.prosody(speech_text02, 'slow', 'medium', 'x-soft', True), playerGender, True))
            Voice.add_text(Voice.pause('1s', True))
            Voice.add_text(Voice.voice(Voice.prosody(speech_text03, 'medium', 'medium', 'loud', True), playerGender, True))
        # PlayerInnerVoice-uberracht
        # speech_organizer = "Willkommen. Lebe oder Sterbe. Du hast genau 1 h um hier rauszukommen." \
        # "Vergiss nicht! Hier geht es nur um DIch. Nur um dich!!Viel Spaß!"
        # speech_text2 = "Oh nein, ich muss mich beeilen"
        else:
            speech_text = "Es hat nicht geklappt. Ich muss zuerst eine Lichtquelle finden."
            Voice.voice(Voice.prosody(speech_text, 'slow', 'medium', 'x-soft', True), playerGender)

        handler_input.attributes_manager.session_attributes.update(lastSpeech(speech_text, playerGender))
        handler_input.response_builder.speak(Voice.speak()).set_should_end_session(
            False)
        return handler_input.response_builder.response


class PositionItemsIntentHandler(AbstractRequestHandler):
    # """Handler for Hello World Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("PositionItemsIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        # hier Abfrage nach Position und dementsprechend die Items ausgeben, die er sieht

        # Speeches, für das Sehen von der Ferne
        speech_couch = "Eine Couch. Toll, zum Ausruhen habe ich keine Zeit."
        speech_door = "Nur eine Tür, durch die ich hoffentlich entkommen kann."
        speech_switch = "Aha. 6 Schalter an der Wand. Was öffnen die denn?"
        speech_safe_table_picture = "Ein Schreibtisch, ein Porträt und ein Safe. Hm."
        speech_text=""
        if gameaccount.distinct('lightOn', {'_id': ObjectId(playerID.__str__())}) == [True]:
            slots = handler_input.request_envelope.request.intent.slots
            positionItem = str(slots['position'].resolutions.resolutions_per_authority[0].values[0].value.id)
            print(positionItem)
            playerPosition = gameaccount.distinct('position', {'_id': ObjectId(playerID.__str__())})
            # genaue Beschreibung mit mehr Details von Items, wenn Spieler/-in direkt vor den Items steht:
            # wenn positionItem==vorne
            if positionItem == "vorne":
                if playerPosition == ["a"]:
                    speech_text = "Ein Schreibtisch ohne Schubladen, sehr unordentlich. " \
                                  "An der Wand ist ein Porträt von Hades, darauf sind Pfeile zu sehen. " \
                                  "Neben dem Schreibtisch ist noch ein kleiner Safe."
                elif playerPosition == ["r"]:
                    speech_text = "Eine Tür, wohl aus Stahl. Mit vielen großen Beulen." \
                                  "zu stabil durchzubrechen. Nebendran ist nur ein Display, wo ich wohl" \
                                  "das Passwort eingeben muss."
                elif playerPosition == ["b"]:
                    speech_text = "6 große Schalter an der Wand, die man nach unten und nach oben schalten kann. "
                elif playerPosition == ["l"]:
                    speech_text = "Nur eine Couch für 2. Braun, aber sehr sauber. Sonst ist nix Hilfreiches hier"
                elif playerPosition == ["c"]:
                    speech_text = speech_safe_table_picture
            elif positionItem == "rechts":
                if playerPosition == ["a"] or playerPosition == ["c"]:
                    speech_text = speech_door
                elif playerPosition == ["r"]:
                    speech_text = speech_switch
                elif playerPosition == ["b"]:
                    speech_text = speech_couch
                elif playerPosition == ["l"]:
                    speech_text = speech_safe_table_picture
            elif positionItem == "hinten":
                if playerPosition == ["a"] or playerPosition == ["c"]:
                    speech_text = speech_switch
                elif playerPosition == ["r"]:
                    speech_text = speech_couch
                elif playerPosition == ["b"]:
                    speech_text = speech_safe_table_picture
                elif playerPosition == ["l"]:
                    speech_text = speech_door
            elif positionItem == "links":
                if playerPosition == ["a"] or playerPosition == ["c"]:
                    speech_text = speech_switch
                elif playerPosition == ["r"]:
                    speech_text = speech_couch
                elif playerPosition == ["b"]:
                    speech_text = speech_safe_table_picture
                elif playerPosition == ["l"]:
                    speech_text = speech_door
            else:
                speech_text = "Gar nix, was mir helfen soll."
        else:
            speech_text="Es hat nicht geklappt. Ich kann ja gar nix sehen."
            # speech_text = "Ein Schreibtisch mit einem Bild, ein Heft und ein kleiner Safe."

        Voice.voice(Voice.prosody(speech_text, 'slow', 'medium', 'x-soft', True), playerGender)
        handler_input.attributes_manager.session_attributes.update(lastSpeech(speech_text, playerGender))
        handler_input.response_builder.speak(Voice.speak()).set_should_end_session(
            False)
        return handler_input.response_builder.response


class InspectItemIntentHandler(AbstractRequestHandler):
    # """Handler for Hello World Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("InspectItemIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        # hier Abfrage nach gameitem und dementsprechend ausgabe
        # Zugriff auf Forschritt:Datenbankauslesen: Falls safe geöffnet, dann inspizieren

        safeOpen=gameaccount.distinct('safeOpen', {'_id': ObjectId(playerID.__str__())})

        slots = handler_input.request_envelope.request.intent.slots
        gameItem = slots["gameItem"].value
        position="c"
        # vorne: Bild, Safe, Schreibtisch, hinten:Schalter
        # rechts:Tür, Pwd-Eingabe, links: Couch
        if gameaccount.distinct('lightOn', {'_id': ObjectId(playerID.__str__())}) == [True]:

            if gameItem == "bild":
                position = "a"
                speech_text = "Was ist das? Sind das Pfeile? Nach oben, nach unten, 2 mal nach oben und 2mal nach unten. "
            elif gameItem == "schalter":
                position = "b"
                speech_text = "Ein Schalter an der Wand. Hm. Was öffnet er wohl? "
            elif gameItem == "schreibtisch":
                position = "a"
                speech_text = "Ein Schreibtisch ohne Schubladen, sehr unordentlich. " \
                                  "Neben dem Schreibtisch ist noch ein kleiner Safe."
            elif gameItem == "safe":
                position = "a"
                if safeOpen == [True]:
                    speech_text = "Ein Zettel! Zahlen! Vielleicht für die Tür! 1 7 8 9 5 6"
                else:
                    speech_text="Ein kleiner Safe. Was ist da wohl alles drin. "
            elif gameItem == "tür":
                position = "r"
                speech_text = "Neben der Tür rechts ist ein kleiner Monitor, wo ich ein 6-stelliger Zahlencode eingeben kann. Ich brauche Zahlen!"
            else:
                speech_text = "Hm. Es ist nichts, was ich nutzen kann."
        else:
            speech_text="Es hat nicht geklappt. Ich kann ja nix sehen."

        Voice.voice(Voice.prosody(speech_text, 'slow', 'medium', 'x-soft', True), playerGender)
        gameaccount.find_one_and_update({'_id': ObjectId(playerID.__str__())}, {'$set': {'position': position}})
        handler_input.attributes_manager.session_attributes.update(lastSpeech(speech_text, playerGender))
        handler_input.response_builder.speak(Voice.speak()).set_should_end_session(
            False)
        return handler_input.response_builder.response

class SwitchSolutionIntentHandler(AbstractRequestHandler):
    # """Handler for Hello World Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("SwitchSolutionIntent")(handler_input)

    # not sure about attirbute_map...

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # slots = handler_input.request_envelope.request.intent.slots
        #  switchDirection = slots["switchDir"].value
        #  switchOrder=slots["switchOrder"].value

        # Auslesen Switchorder und dir=>in der Datenbank speichern/ersetzen
        # Abfrage ob man ändern falls, falls bereits geshclatet: lesen ausm datenbank

        slots = handler_input.request_envelope.request.intent.slots

        switchDir = slots["switchDir"].value
        switchOrder = slots["switchOrder"].value

        if switchOrder == "1":
            switchFieldInDatabase = "switch.1"
        elif switchOrder == "2":
            switchFieldInDatabase = "switch.2"
        elif switchOrder == "3":
            switchFieldInDatabase = "switch.3"
        elif switchOrder == "4":
            switchFieldInDatabase = "switch.4"
        elif switchOrder == "5":
            switchFieldInDatabase = "switch.5"
        elif switchOrder == "6":
            switchFieldInDatabase = "switch.6"

        if switchDir == "hoch":
            switchDirField = "1"
        elif switchDir == "oben":
            switchDirField = "1"
        elif switchDir == "runter":
            switchDirField = "-1"
        elif switchDir == "unten":
            switchDirField = "-1"

        gameaccount.find_one_and_update({'_id': ObjectId(playerID.__str__())},
                                        {'$set': {switchFieldInDatabase: switchDirField}})

        """
        switchDirOne = slots["switchDirOne"].value
        switchDirTwo = slots["switchDirTwo"].value
        switchDirThree = slots["switchDirThree"].value
        switchDirFour = slots["switchDirFour"].value
        switchDirFive = slots["switchDirFive"].value
        switchDirSix = slots["switchDirSix"].value

        switch = {
            'switch': [switchDirOne, switchDirTwo, switchDirThree, switchDirFour, switchDirFive, switchDirSix],
        }
        gameaccount.find_one_and_update({'_id': ObjectId(playerID.__str__())}, {'$set': switch})
        """
        # Sound vom Safe: geöffnet dann players mind: safe geöffnet
        # zufällige -1 und 1 erstellen. damit jedes spiel anderen Ausgang hat->auf dem Bild als Pfeile anpassen
        # Idee die schalter sollte ich für den Spielverlauf eventuell speichern? Zugriff auf speicher nötig?
        if gameaccount.distinct('switch', {'_id': ObjectId(playerID.__str__())}) == [
            switchRightValue]:
            gameaccount.find_one_and_update({'_id': ObjectId(playerID.__str__())}, {'$set': {'safe': True}})
            speech_text = "Der Safe scheint sich geöffnet zu haben! "
            Voice.audio("soundbank://soundlibrary/doors/doors_key_lock/key_lock_07")
            Voice.add_text(Voice.voice(Voice.prosody(speech_text, 'medium', 'medium', 'loud', True), playerGender, True))

        else:
            print(gameaccount.distinct('switch', {'_id': ObjectId(playerID.__str__())}))
            print([switchRightValue])
            speech_text = "Ich muss noch etwas an den Schaltern machen."
            Voice.voice(Voice.prosody(speech_text, 'slow', 'medium', 'x-soft', True), playerGender)

        handler_input.attributes_manager.session_attributes.update(lastSpeech(speech_text, playerGender))
        handler_input.response_builder.speak(Voice.speak()).set_should_end_session(
            False)
        return handler_input.response_builder.response


class OpenTheDoorIntentHandler(AbstractRequestHandler):
    # """Handler for Hello World Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("OpenTheDoorIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # Auslesen Keyword: If abfrage: Falls Keyword richtig: öffne Tür
        slots = handler_input.request_envelope.request.intent.slots

        passwortDoor = slots["passwort"].value

        Voice.audio("soundbank://soundlibrary/doors/doors_key_lock/key_lock_07")
        Voice.add_text(Voice.audio("soundbank://soundlibrary/doors/doors_key_lock/key_lock_07", True))

        if passwortDoor == ["178956"]:
            gameaccount.find_one_and_update({'_id': ObjectId(playerID.__str__())}, {'$set': {'door': "open"}})
            speech_text = "Ich habs geschafft! Ich bin raus!"
            Voice.add_text(Voice.audio("soundbank://soundlibrary/doors/doors_regular/regular_15", True))
            Voice.add_text(Voice.voice(Voice.prosody(speech_text, 'medium', 'medium', 'loud', True), playerGender, True))
            # keine männliche Stimme übrig für Spielveranstallter
            # speech_text02 = "Du hast es geschafft, Gratulation Spieler!!"
            handler_input.response_builder.speak(Voice.speak()).set_should_end_session(True)

        else:
            speech_text = "Das Passwort ist falsch. Ich habe einen Fehler gemacht! "
            Voice.add_text(
                Voice.audio("soundbank://soundlibrary/ui/gameshow/amzn_ui_sfx_gameshow_negative_response_01", True))
            Voice.add_text(Voice.voice(Voice.prosody(speech_text, 'x-slow', 'medium', 'soft', True), playerGender, True))
            handler_input.response_builder.speak(Voice.speak()).set_should_end_session(False)
            # eventuell restzeit sagen?

        # Sound vom Tür: geöffnet dann players mind:
        handler_input.attributes_manager.session_attributes.update(lastSpeech(speech_text, playerGender))
        return handler_input.response_builder.response

class RemainingTimeIntentHandler(AbstractRequestHandler):
    # """Handler for Hello World Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("RemainingTimeIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        global playerSavedTime
        cursor = gameaccount.find({'_id': playerID})
        for document in cursor:
            playerSavedTime = document['time']
            print(document['time'])

        # + playerSavedTime
        playerTimeAlreadyPlayed = int(time.time() - playerTimeStarted + playerSavedTime)

        speech_text = "Du hast noch " +str((int(3600-playerTimeAlreadyPlayed)/60))+" Minuten Zeit."
        # PlayerInnerVoice-uberracht
        #aufpasseb playergender soll gesetzt sein

        handler_input.attributes_manager.session_attributes.update(lastSpeech(speech_text, playerGender))
        handler_input.response_builder.speak(speech_text).set_should_end_session(
            False)
        return handler_input.response_builder.response

class GiveMeHintIntentHandler(AbstractRequestHandler):
    # """Handler for Hello World Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("GiveMeHintIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        switch=gameaccount.distinct('switch', {'_id': ObjectId(playerID.__str__())})
        lightFound=gameaccount.distinct('lightFound', {'_id': ObjectId(playerID.__str__())})
        lightOn = gameaccount.distinct('lightOn', {'_id': ObjectId(playerID.__str__())})
        safe=gameaccount.distinct('switch', {'_id': ObjectId(playerID.__str__())})

        if lightFound!=[True]:
            speech_text="Was hatte ich denn an dem Tag der Entführung an? Habe ich etwas hilfreiches dabei?"
        elif lightOn!=[True]:
            speech_text="Was mache ich jetzt mit der Taschenlampe? Es ist so dunkel hier."
        elif switch!=[switchRightValue]:
            speech_text="Was sind das für Pfeile auf dem Porträt?"
        elif safe==[True]:
            speech_text="Was ist in dem Safe drin? Ich muss hier raus!"

        Voice.voice(Voice.prosody(speech_text, 'slow', 'medium', 'soft', True), playerGender)

        handler_input.attributes_manager.session_attributes.update(lastSpeech(speech_text, playerGender))
        handler_input.response_builder.speak(Voice.speak()).set_should_end_session(
            False)
        return handler_input.response_builder.response


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speech_text = "Falls du nicht mehr weiterkommst, kannst du nach Hinweisenmfragen."

        handler_input.attributes_manager.session_attributes.update(lastSpeech(speech_text))
        handler_input.response_builder.speak(speech_text).ask(
            speech_text)
        return handler_input.response_builder.response


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        global playerSavedTime
        cursor = gameaccount.find({'_id': playerID})
        for document in cursor:
            playerSavedTime = document['time']
            print(document['time'])

        # + playerSavedTime
        playerTimeAlreadyPlayed = int(time.time() - playerTimeStarted + playerSavedTime)
        gameaccount.find_one_and_update({'_id': ObjectId(playerID.__str__())},
                                        {'$set': {'time': playerTimeAlreadyPlayed}})

        speech_text = "Auf Wiedersehen!"

        handler_input.response_builder.speak(speech_text).set_should_end_session(True)
        return handler_input.response_builder.response


class FallbackIntentHandler(AbstractRequestHandler):
    """
    This handler will not be triggered except in supported locales,
    so it is safe to deploy on any locale.
    """

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        global playerSavedTime
        cursor = gameaccount.find({'_id': playerID})
        for document in cursor:
            playerSavedTime = document['time']
            print(document['time'])

        playerTimeAlreadyPlayed = int(time.time() - playerTimeStarted + playerSavedTime)
        gameaccount.find_one_and_update({'_id': ObjectId(playerID.__str__())},
                                        {'$set': {'time': playerTimeAlreadyPlayed}})

        speech_text = (
            "Ich kann dir dabei leider nicht helfen. Falls du dir das Letzte wieder anhören möchtest, sage: Wiederhole das Letzte")
        reprompt = "Es wäre sinnvoll, wenn du dir das Letzte nochmal anhören würdest. Sage dazu: Wiederhole das Letzte"
        handler_input.response_builder.speak(speech_text).ask(reprompt)
        return handler_input.response_builder.response


class RepeatIntentHandler(AbstractRequestHandler):

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.RepeatIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # geschlecht anpassen mit if...
        previousIntentGender = handler_input.attributes_manager.session_attributes.get("gender")
        speech_text = handler_input.attributes_manager.session_attributes.get("LastSpeech")
        if previousIntentGender != "" :
            Voice.voice(speech_text, playerGender, False)
            handler_input.response_builder.speak(Voice.speak())
        else:
            Voice.voice(speech_text, 'Vicki', False)
            handler_input.response_builder.speak(speech_text)
        # else nicht nötig! viki testen!!

        return handler_input.response_builder.response


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        global playerSavedTime
        cursor = gameaccount.find({'_id': playerID})
        for document in cursor:
            playerSavedTime = document['time']
            print(document['time'])

        playerTimeAlreadyPlayed = int(time.time() - playerTimeStarted + playerSavedTime)
        gameaccount.find_one_and_update({'_id': ObjectId(playerID.__str__())},
                                        {'$set': {'time': playerTimeAlreadyPlayed}})

        return handler_input.response_builder.response


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Catch all exception handler, log exception and
    respond with custom message.
    """

    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        app.logger.error(exception, exc_info=True)

        speech = "Es gab einen Fehler, bitte versuche es erneut!"
        handler_input.response_builder.speak(speech).ask(speech)

        return handler_input.response_builder.response


sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(StoreNameRequestHandler())
sb.add_request_handler(PlayerInnerVoiceIntentHandler())
sb.add_request_handler(IntroductionIntentHandler())
sb.add_request_handler(InvalidLookForLightIntentHandler())
sb.add_request_handler(LoadGameHistoryIntentHandler())
sb.add_request_handler(ContinueTheGameIntentHandler())
sb.add_request_handler(PauseTheGameIntentHandler())
sb.add_request_handler(FlashlightInThePocketIntentHandler())
sb.add_request_handler(LightOnIntentHandler())
sb.add_request_handler(OpenTheDoorIntentHandler())
sb.add_request_handler(SwitchSolutionIntentHandler())
sb.add_request_handler(StartTheGameIntentHandler())
sb.add_request_handler(PositionItemsIntentHandler())
sb.add_request_handler(InspectItemIntentHandler())
sb.add_request_handler(RemainingTimeIntentHandler())
sb.add_request_handler(GiveMeHintIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(RepeatIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_exception_handler(CatchAllExceptionHandler())

skill_adapter = SkillAdapter(
    skill=sb.create(), skill_id=1, app=app)


@app.route('/', methods=['GET', 'POST'])
def invoke_skill():
    return skill_adapter.dispatch_request()


if __name__ == '__main__':
    app.run()
