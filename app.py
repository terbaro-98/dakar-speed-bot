from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from dotenv import load_dotenv
import os
from bot_logic import handle_message, sessions

load_dotenv()

app = Flask(__name__)

# === Twilio Config ===
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")  # Ex: whatsapp:+14155238886
BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.values.get("Body", "").strip()
    sender_number = request.values.get("From", "")
    
    print(f"📩 Nouveau message reçu de {sender_number} : '{incoming_msg}'")

    try:
        reply_text = handle_message(sender_number, incoming_msg)
        print(f"✏️ Réponse générée pour {sender_number} : '{reply_text}'")
    except Exception as e:
        print(f"❌ Erreur lors du traitement de handle_message : {e}")
        reply_text = "Désolé, une erreur est survenue lors du traitement de votre message."

    resp = MessagingResponse()
    resp.message(reply_text)

    # 📎 Si un PDF a été généré, l'envoyer
    session = sessions.get(sender_number)
    if session and "pdf_url" in session:
        pdf_url = session["pdf_url"]
        print(f"📎 PDF détecté pour {sender_number} → {pdf_url}")
        send_pdf_via_whatsapp(sender_number, pdf_url)
        session.pop("pdf_url")
        sessions[sender_number] = session
    else:
        print(f"ℹ️ Aucun PDF à envoyer pour {sender_number}")

    return str(resp)


def send_pdf_via_whatsapp(to_number, pdf_url):
    """Envoie le PDF généré via WhatsApp"""
    try:
        message = twilio_client.messages.create(
            from_=TWILIO_PHONE_NUMBER,
            to=to_number,
            media_url=[pdf_url],
            body="📄 Voici votre bon de livraison au format PDF."
        )
        print(f"✅ PDF envoyé à {to_number} | SID: {message.sid}")
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi du PDF à {to_number} : {e}")


@app.route("/", methods=["GET"])
def home():
    return "✅ Bot WhatsApp Dakar Speed Pro est en ligne !"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render fournit la variable d’environnement PORT
    app.run(host="0.0.0.0", port=port)
