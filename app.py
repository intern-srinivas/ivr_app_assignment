import os
from flask import Flask, request, render_template
from dotenv import load_dotenv
from xml.etree.ElementTree import Element, tostring
import plivo

load_dotenv()

# Simple XML builder for Plivo responses
class GetDigits:
    def __init__(self, node):
        self.node = node
    
    def addSpeak(self, text):
        speak = Element("Speak")
        speak.text = text
        self.node.append(speak)

class Dial:
    def __init__(self, node):
        self.node = node
    
    def addNumber(self, number):
        num = Element("Number")
        num.text = number
        self.node.append(num)

class Response:
    def __init__(self):
        self.root = Element("Response")
    
    def addGetDigits(self, action, method, numDigits, timeout, retries):
        gd = Element("GetDigits", {
            "action": action,
            "method": method,
            "numDigits": str(numDigits),
            "timeout": str(timeout),
            "retries": str(retries),
        })
        self.root.append(gd)
        return GetDigits(gd)
    
    def addSpeak(self, text):
        speak = Element("Speak")
        speak.text = text
        self.root.append(speak)
    
    def addPlay(self, url):
        play = Element("Play")
        play.text = url
        self.root.append(play)
    
    def addHangup(self):
        self.root.append(Element("Hangup"))
    
    def addDial(self):
        dial = Element("Dial")
        self.root.append(dial)
        return Dial(dial)
    
    def to_xml(self):
        return tostring(self.root, encoding="unicode")

app = Flask(__name__)

PLIVO_AUTH_ID = os.getenv("PLIVO_AUTH_ID")
PLIVO_AUTH_TOKEN = os.getenv("PLIVO_AUTH_TOKEN")
FROM_NUMBER = os.getenv("PLIVO_SOURCE_NUMBER")
HOST_URL = os.getenv("HOST_URL")  # e.g., https://<ngrok>.ngrok.io
ASSOCIATE_NUMBER = os.getenv("ASSOCIATE_NUMBER", "+11234567890")
AUDIO_URL = os.getenv(
    "AUDIO_URL",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
)

client = plivo.RestClient(auth_id=PLIVO_AUTH_ID, auth_token=PLIVO_AUTH_TOKEN)


@app.route("/")
def index():
    return render_template("index.html")


# -----------------------------------------------
# 1️⃣ Trigger Outbound Call
# -----------------------------------------------
@app.route("/call", methods=["POST"])
def make_call():
    to_number = request.form.get("to")

    if not to_number:
        return "Missing destination number", 400

    try:
        response = client.calls.create(
            from_=FROM_NUMBER,
            to_=to_number,
            answer_url=f"{HOST_URL}/answer",
            answer_method="POST"
        )
        return f"Call initiated. Request UUID: {response.request_uuid}"
    except Exception as e:
        return f"Error initiating call: {str(e)}", 500


# -----------------------------------------------
# 2️⃣ Level 1 – Language Menu
# -----------------------------------------------
@app.route("/answer", methods=["GET","POST"])
def answer_call():
    response = Response()

    get_digits = response.addGetDigits(
        action=f"{HOST_URL}/ivr/language",
        method="POST",
        numDigits=1,
        timeout=7,
        retries=1
    )
    get_digits.addSpeak(
        "Welcome to the InspireWorks IVR Demo. "
        "For English, press 1. Para español, oprima 2."
    )

    response.addSpeak("No input received. Goodbye.")
    return response.to_xml(), 200, {"Content-Type": "application/xml"}


# -----------------------------------------------
# 3️⃣ Level 2 – English or Spanish Menu
# -----------------------------------------------
@app.route("/ivr/language", methods=["POST"])
def ivr_language():
    digit = request.form.get("Digits")

    if digit == "1":
        lang = "en"
        message = (
            "You selected English. "
            "Press 1 to hear a short audio message. "
            "Press 2 to connect to an associate."
        )

    elif digit == "2":
        lang = "es"
        message = (
            "Has elegido español. "
            "Presione 1 para escuchar un breve mensaje. "
            "Presione 2 para ser conectado con un asociado."
        )

    else:
        # Invalid → repeat menu
        response = Response()
        get_digits = response.addGetDigits(
            action=f"{HOST_URL}/ivr/language",
            method="POST",
            numDigits=1,
            timeout=7,
            retries=1
        )
        get_digits.addSpeak(
            "Invalid option. "
            "For English press 1. Para español oprima 2."
        )
        response.addSpeak("Goodbye.")
        return response.to_xml(), 200, {"Content-Type": "application/xml"}

    response = Response()
    get_digits = response.addGetDigits(
        action=f"{HOST_URL}/ivr/action?lang={lang}",
        method="POST",
        numDigits=1,
        timeout=7,
        retries=1
    )
    get_digits.addSpeak(message)

    response.addSpeak("No input received. Goodbye.")
    return response.to_xml(), 200, {"Content-Type": "application/xml"}


# -----------------------------------------------
# 4️⃣ Final Action (Level 2 options)
# -----------------------------------------------
@app.route("/ivr/action", methods=["POST"])
def ivr_action():
    digit = request.form.get("Digits")
    lang = request.args.get("lang", "en")

    response = Response()

    # Option 1 → Play audio
    if digit == "1":
        response.addSpeak("Playing message..." if lang == "en" else "Reproduciendo mensaje...")
        response.addPlay(AUDIO_URL)
        response.addSpeak("Goodbye." if lang == "en" else "Adiós.")
        response.addHangup()
        return response.to_xml(), 200, {"Content-Type": "application/xml"}

    # Option 2 → Connect to associate
    if digit == "2":
        response.addSpeak(
            "Connecting you to an associate." if lang == "en"
            else "Conectando con un asociado."
        )
        dial = response.addDial()
        dial.addNumber(ASSOCIATE_NUMBER)
        return response.to_xml(), 200, {"Content-Type": "application/xml"}

    # Invalid input → repeat menu
    get_digits = response.addGetDigits(
        action=f"{HOST_URL}/ivr/action?lang={lang}",
        method="POST",
        numDigits=1,
        timeout=7,
        retries=1
    )
    if lang == "en":
        get_digits.addSpeak(
            "Invalid option. Press 1 to hear a message, or press 2 to speak to an associate."
        )
    else:
        get_digits.addSpeak(
            "Opción inválida. Presione 1 para escuchar un mensaje o presione 2 para hablar con un asociado."
        )
    response.addSpeak("Goodbye.")
    return response.to_xml(), 200, {"Content-Type": "application/xml"}


if __name__ == "__main__":
    app.run(port=5000, debug=True)
