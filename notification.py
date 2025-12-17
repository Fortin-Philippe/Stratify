from flask import Blueprint, render_template, session, redirect, url_for, flash
import bd

bp_notification = Blueprint("notification", __name__)

def verifier_connexion():
    utilisateur_id = session.get("user_id")
    if not utilisateur_id:
        flash("Veuillez vous connecter.", "warning")
        return None
    return utilisateur_id

@bp_notification.route("/notifications")
def notifications():
    utilisateur_id = verifier_connexion()
    if not utilisateur_id:
        return redirect(url_for("compte.connexion"))

    notifications = bd.obtenir_notifications(utilisateur_id)
    bd.marquer_notifications_comme_lues(utilisateur_id)
    return render_template("notification.jinja", notifications=notifications)

@bp_notification.route("/accepter-demande/<int:demande_id>")
def accepter_demande(demande_id):
    utilisateur_id = session.get("user_id")
    if not utilisateur_id:
        flash("Veuillez vous connecter.", "warning")
        return redirect(url_for("compte.connexion"))

    succes = bd.traiter_demande_et_notifier(demande_id, accepter=True)
    if succes:
        flash("Demande acceptée et message envoyé à l'utilisateur.", "success")
    else:
        flash("Demande introuvable.", "error")
    return redirect(url_for("notification.notifications"))

@bp_notification.route("/refuser-demande/<int:demande_id>")
def refuser_demande(demande_id):
    utilisateur_id = verifier_connexion()
    if not utilisateur_id:
        return redirect(url_for("compte.connexion"))

    bd.traiter_demande_et_notifier(demande_id, accepter=False)
    flash("Demande refusée.", "warning")
    return redirect(url_for("notification.notifications"))