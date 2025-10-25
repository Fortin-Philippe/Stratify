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
    return render_template('messages_liste.jinja', conversations=conversations)