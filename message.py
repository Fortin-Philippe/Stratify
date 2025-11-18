from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import bd

message_bp = Blueprint("message", __name__)

@message_bp.route("/conversations")
def liste_conversations():
    user_id = session.get("user_id")
    if not user_id:
        flash("Veuillez vous connecter pour voir vos conversations.", "warning")
        return redirect(url_for('compte.connexion'))

    conversations = bd.obtenir_conversations_utilisateur(user_id)
    admins = bd.obtenir_tous_admin()  
    
    return render_template(
        "messages_liste.jinja",
        conversations=conversations,
        admins=admins
    )
    

@message_bp.route("/conversation/<int:autre_id>", methods=["GET", "POST"])
def conversation(autre_id):
    user_id = session.get("user_id")
    if not user_id:
        flash("Veuillez vous connecter pour envoyer un message.", "warning")
        return redirect(url_for('compte.connexion'))

    if request.method == "POST":
        contenu = request.form.get("contenu")
        if contenu:
            bd.envoyer_message_prive(user_id, autre_id, contenu)
            return redirect(url_for("message.conversation", autre_id=autre_id))

    messages = bd.obtenir_messages_prives(user_id, autre_id)
    utilisateurs_ids = {msg['expediteur_id'] for msg in messages}
    utilisateurs_ids.add(autre_id)
    utilisateurs = {u['id']: u for u in [bd.get_utilisateur_par_id(uid) for uid in utilisateurs_ids]}
    autre_user = bd.get_utilisateur_par_id(autre_id)
    return render_template("messages_conversation.jinja", messages=messages, autre_user=autre_user, utilisateurs=utilisateurs)

