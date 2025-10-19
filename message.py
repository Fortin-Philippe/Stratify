from flask import Blueprint, render_template, session
import bd

bp_messagerie = Blueprint("messagerie", __name__)

@bp_messagerie.route("/conversations")
def liste_conversations():
    user_id = session.get("user_id")
    if not user_id:
        return "Non connecté", 403

    conversations = bd.obtenir_conversations_utilisateur(user_id)
    return render_template("conversations.jinja", conversations=conversations)