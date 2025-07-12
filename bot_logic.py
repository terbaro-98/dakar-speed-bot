sessions = {}

def handle_message(user_number, incoming_msg):
    print(f"[📩] Message reçu de {user_number} : '{incoming_msg}'")

    # Initialisation de session si nécessaire
    if user_number not in sessions:
        sessions[user_number] = {
            "step": "ask_name",
            "data": {}
        }
        print(f"[ℹ️] Nouvelle session créée pour {user_number}")

    session = sessions[user_number]
    step = session["step"]
    data = session["data"]

    print(f"[🔄] Étape actuelle : {step}")
    
    # === Étapes de la conversation ===

    if step == "ask_name":
        data["name"] = incoming_msg
        session["step"] = "ask_phone"
        print(f"[✅] Nom enregistré : {data['name']}")
        return "📞 Merci ! Entrez votre *numéro de téléphone* (+221XXXXXXXXX)"

    elif step == "ask_phone":
        data["phone"] = incoming_msg
        session["step"] = "ask_type"
        print(f"[✅] Téléphone enregistré : {data['phone']}")
        return (
            "✅ Numéro validé !\n"
            "1️⃣ Livraison Classique 📦\n"
            "2️⃣ Livraison Repas 🍛\n"
            "3️⃣ Livraison Entreprise 🏢\n"
            "➡️ Répondez par *1, 2, ou 3.*"
        )

    elif step == "ask_type":
        if incoming_msg not in ["1", "2", "3"]:
            print(f"[⚠️] Réponse invalide pour le type de livraison : {incoming_msg}")
            return "⛔️ Veuillez répondre uniquement par 1, 2 ou 3."

        livraison_map = {
            "1": "classique",
            "2": "repas",
            "3": "entreprise"
        }

        choix = livraison_map[incoming_msg]
        session["step"] = f"{choix}_details"
        print(f"[✅] Type de livraison choisi : {choix}")

        if choix == "classique":
            return "📦 Entrez les détails de la livraison (adresse, poids, etc.)"
        elif choix == "repas":
            return "🍛 Entrez les détails du repas à livrer (nom, quantité, etc.)"
        elif choix == "entreprise":
            return "🏢 Entrez les infos de la livraison entreprise (nom société, point de contact, etc.)"

    elif step.endswith("_details"):
        data["details"] = incoming_msg
        session["step"] = "confirm"
        print(f"[📝] Détails enregistrés : {data['details']}")
        return (
            f"🧾 Merci {data['name']} ! Voici le résumé :\n"
            f"- Téléphone : {data['phone']}\n"
            f"- Type : {step.replace('_details', '').capitalize()}\n"
            f"- Détails : {data['details']}\n\n"
            "✅ Répondez *oui* pour valider ou *non* pour recommencer."
        )

    elif step == "confirm":
        if incoming_msg.lower() == "oui":
            print(f"[✅] Commande confirmée pour {user_number}")
            # 👉 Tu pourrais générer ici un PDF ou enregistrer en base
            session["step"] = "done"
            return "🎉 Votre demande a été enregistrée. Merci pour votre confiance !"
        else:
            print(f"[↩️] Utilisateur souhaite recommencer : {user_number}")
            sessions.pop(user_number, None)
            return "🔄 D'accord, reprenons. Quel est votre nom complet ?"

    elif step == "done":
        return "✅ Votre demande a déjà été prise en compte. Merci !"

    # Cas inattendu
    print(f"[❓] Étape inconnue pour {user_number} : {step}")
    return "Une erreur est survenue. Veuillez recommencer svp."
