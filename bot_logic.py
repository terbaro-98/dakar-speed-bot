import re
import os
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import black, HexColor

sessions = {}

QUARTIERS = {
    "1": "Plateau 🏙️",
    "2": "Medina 🕌",
    "3": "Yoff 🌴",
    "4": "Almadies 🏝️",
    "5": "Ouakam 🗼",
    "6": "Pikine 🏘️",
    "7": "Guédiawaye 🚏",
    "8": "Dakar Plateau 📍",
    "9": "Liberté 6 🏢",
    "10": "Parcelles Assainies 🛣️",
    "11": "Autre (envoyez votre géolocalisation) 📍"
}

def is_valid_senegal_number(number):
    return re.match(r'^\+221(70|75|76|77|78|33)\d{7}$', number) is not None

def is_valid_hour_format(text):
    return re.match(r'^([01]?[0-9]|2[0-3])[:h][0-5][0-9]$', text)

def handle_message(user_id, msg):
    session = sessions.get(user_id, {"step": "start"})
    msg = msg.strip()

    if session["step"] == "start":
        session["step"] = "ask_name"
        sessions[user_id] = session
        return "👋 Bienvenue chez *Dakar Speed Pro* ! Quel est votre *nom complet* ?"

    if session["step"] == "ask_name":
        if len(msg) >= 3 and len(msg.split()) >= 2:
            session["name"] = msg
            session["step"] = "ask_phone"
            sessions[user_id] = session
            return "📞 Merci ! Entrez votre *numéro de téléphone* (+2217XXXXXXXX)"
        else:
            return "❌ Nom trop court ou incomplet."

    if session["step"] == "ask_phone":
        phone = msg.replace(" ", "")
        if is_valid_senegal_number(phone):
            session["phone"] = phone
            session["step"] = "choose_service"
            sessions[user_id] = session
            return (
                "✅ Numéro validé !\n"
                "1️⃣ Livraison Classique 📦\n"
                "2️⃣ Livraison Repas 🍽️\n"
                "3️⃣ Livraison Entreprise 🏢\n"
                "➡️ Répondez par *1*, *2*, ou *3*."
            )
        return "❌ Numéro invalide. Format attendu : +2217XXXXXXXX"

    if session["step"] == "choose_service":
        if msg == "1":
            session["service"] = "classique"
            session["step"] = "quartier"
            sessions[user_id] = session
            return "📍 Choisissez le *quartier de départ* :\n" + "\n".join([f"{k}. {v}" for k, v in QUARTIERS.items()])
        elif msg == "2":
            session["service"] = "repas"
            session["step"] = "restaurant_name"
            sessions[user_id] = session
            return "🍽️ Quel est le *nom du restaurant* ?"
        elif msg == "3":
            session["service"] = "entreprise"
            session["step"] = "entreprise_depart"
            sessions[user_id] = session
            return "🏢 Quelle est l'*adresse de départ* ?"
        else:
            return "❌ Choix invalide. Répondez par 1, 2 ou 3."

    # === CLASSIQUE
    if session["service"] == "classique":
        if session["step"] == "quartier":
            if msg in QUARTIERS:
                session["quartier"] = QUARTIERS[msg]
                session["step"] = "adresse_livraison"
                sessions[user_id] = session
                return "📍 Adresse de livraison ?"
            return "❌ Choix invalide. Répondez avec le numéro du quartier."

        if session["step"] == "adresse_livraison":
            session["adresse_livraison"] = msg
            session["step"] = "description_colis"
            sessions[user_id] = session
            return "📦 Description du colis ?"

        if session["step"] == "description_colis":
            session["description_colis"] = msg
            session["step"] = "destinataire"
            sessions[user_id] = session
            return "👤 Nom et numéro du destinataire ?"

        if session["step"] == "destinataire":
            parts = msg.strip().split()
            if len(parts) >= 2 and is_valid_senegal_number(parts[-1]):
                session["destinataire"] = msg
                resume = (
                    f"✅ *Bon récapitulatif Livraison Classique*\n"
                    f"Nom : {session['name']}\n"
                    f"Téléphone : {session['phone']}\n"
                    f"Quartier : {session['quartier']}\n"
                    f"Adresse : {session['adresse_livraison']}\n"
                    f"Colis : {session['description_colis']}\n"
                    f"Destinataire : {session['destinataire']}\n"
                    "🎉 Merci pour votre confiance !"
                )
                filename = f"receipt_whatsapp_{session['phone'].replace('+', '')}.pdf"
                generate_delivery_receipt(session, filename)
                session["pdf_url"] = f"{os.getenv('BASE_URL')}/static/pdfs/{filename}"
                sessions[user_id] = session
                return resume
            else:
                return "❌ Numéro invalide. Format : Jean +2217XXXXXXX"

    # === REPAS
    if session["service"] == "repas":
        if session["step"] == "restaurant_name":
            session["restaurant_name"] = msg
            session["step"] = "restaurant_address"
            sessions[user_id] = session
            return "📍 Adresse du restaurant ?"

        if session["step"] == "restaurant_address":
            session["restaurant_address"] = msg
            session["step"] = "client_address"
            sessions[user_id] = session
            return "🏠 Adresse du client ?"

        if session["step"] == "client_address":
            session["client_address"] = msg
            session["step"] = "commande_details"
            sessions[user_id] = session
            return "🧾 Détails de la commande ?"

        if session["step"] == "commande_details":
            session["commande_details"] = msg
            resume = (
                f"✅ *Bon récapitulatif Livraison Repas*\n"
                f"Nom : {session['name']}\n"
                f"Téléphone : {session['phone']}\n"
                f"Restaurant : {session['restaurant_name']}\n"
                f"Adresse resto : {session['restaurant_address']}\n"
                f"Client : {session['client_address']}\n"
                f"Détails : {session['commande_details']}\n"
                "🎉 Merci !"
            )
            filename = f"receipt_whatsapp_{session['phone'].replace('+', '')}.pdf"
            generate_delivery_receipt(session, filename)
            session["pdf_url"] = f"{os.getenv('BASE_URL')}/static/pdfs/{filename}"
            sessions[user_id] = session
            return resume

    # === ENTREPRISE
    if session["service"] == "entreprise":
        if session["step"] == "entreprise_depart":
            session["entreprise_depart"] = msg
            session["step"] = "entreprise_livraison"
            sessions[user_id] = session
            return "📍 Adresse de livraison ?"

        if session["step"] == "entreprise_livraison":
            session["entreprise_livraison"] = msg
            session["step"] = "entreprise_colis"
            sessions[user_id] = session
            return "📦 Description du colis ?"

        if session["step"] == "entreprise_colis":
            session["entreprise_colis"] = msg
            session["step"] = "entreprise_heure"
            sessions[user_id] = session
            return "⏰ Heure de récupération ?"

        if session["step"] == "entreprise_heure":
            session["entreprise_heure"] = msg
            session["step"] = "entreprise_ref"
            sessions[user_id] = session
            return "🔖 Référence interne (facultatif) :"

        if session["step"] == "entreprise_ref":
            session["entreprise_ref"] = msg
            resume = (
                f"✅ *Bon récapitulatif Livraison Entreprise*\n"
                f"Nom : {session['name']}\n"
                f"Téléphone : {session['phone']}\n"
                f"Départ : {session['entreprise_depart']}\n"
                f"Livraison : {session['entreprise_livraison']}\n"
                f"Colis : {session['entreprise_colis']}\n"
                f"Heure : {session['entreprise_heure']}\n"
                f"Référence : {session['entreprise_ref']}\n"
                "🎉 Merci !"
            )
            filename = f"receipt_whatsapp_{session['phone'].replace('+', '')}.pdf"
            generate_delivery_receipt(session, filename)
            session["pdf_url"] = f"{os.getenv('BASE_URL')}/static/pdfs/{filename}"
            sessions[user_id] = session
            return resume

    return "🔄 Une erreur est survenue. Tapez *Bonjour* pour recommencer."


# =============== PDF STYLISÉ ================
def generate_delivery_receipt(session, filename):
    os.makedirs("static/pdfs", exist_ok=True)
    filepath = f"static/pdfs/{filename}"
    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4

    # Logo
    logo_path = "static/logo/Dsp_logo-1.png"
    if os.path.exists(logo_path):
        c.drawImage(logo_path, 50, height - 100, width=80, preserveAspectRatio=True, mask='auto')

    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(HexColor("#0033cc"))
    c.drawString(150, height - 70, "REÇU DE LIVRAISON")

    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(black)
    c.drawString(150, height - 90, "Dakar Speed Pro")

    c.line(50, height - 100, width - 50, height - 100)

    y = height - 130
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Date : {datetime.now().strftime('%d/%m/%Y à %H:%M')}")
    c.drawRightString(width - 50, y, f"N° Commande : DSP-{datetime.now().strftime('%H%M%S')}")

    y -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "INFORMATIONS CLIENT")
    c.setFont("Helvetica", 10)
    y -= 15
    c.drawString(70, y, f"Nom : {session['name']}")
    y -= 15
    c.drawString(70, y, f"Téléphone : {session['phone']}")

    y -= 25
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "DÉTAILS DE LA COMMANDE")
    c.setFont("Helvetica", 10)
    y -= 15

    if session["service"] == "classique":
        c.drawString(70, y, f"Quartier : {session['quartier']}")
        y -= 15
        c.drawString(70, y, f"Adresse : {session['adresse_livraison']}")
        y -= 15
        c.drawString(70, y, f"Colis : {session['description_colis']}")
        y -= 15
        c.drawString(70, y, f"Destinataire : {session['destinataire']}")

    elif session["service"] == "repas":
        c.drawString(70, y, f"Restaurant : {session['restaurant_name']}")
        y -= 15
        c.drawString(70, y, f"Adresse resto : {session['restaurant_address']}")
        y -= 15
        c.drawString(70, y, f"Client : {session['client_address']}")
        y -= 15
        c.drawString(70, y, f"Détails : {session['commande_details']}")

    elif session["service"] == "entreprise":
        c.drawString(70, y, f"Départ : {session['entreprise_depart']}")
        y -= 15
        c.drawString(70, y, f"Livraison : {session['entreprise_livraison']}")
        y -= 15
        c.drawString(70, y, f"Colis : {session['entreprise_colis']}")
        y -= 15
        c.drawString(70, y, f"Heure : {session['entreprise_heure']}")
        y -= 15
        c.drawString(70, y, f"Référence : {session['entreprise_ref']}")

    y -= 25
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "INFORMATIONS DE LIVRAISON")
    c.setFont("Helvetica", 10)
    y -= 15
    c.drawString(70, y, f"Date prévue : {datetime.now().strftime('%d/%m/%Y')}")
    y -= 15
    c.drawString(70, y, "Créneau : 9h00 - 18h00")
    y -= 15
    c.drawString(70, y, "Statut : Confirmée ✅")

    y -= 30
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(HexColor("#0033cc"))
    c.drawString(50, y, "Merci pour votre confiance ! 🙏")

    y -= 25
    c.setFillColor(black)
    c.setFont("Helvetica", 9)
    c.drawString(50, y, "Pour toute question, contactez-nous :")
    y -= 12
    c.drawString(70, y, "📧 contact@gospeedpro.com")
    y -= 12
    c.drawString(70, y, "📞 +221 784 44 85 24")
    y -= 12
    c.drawString(70, y, "🌐 www.gospeedpro.com")

    c.save()
