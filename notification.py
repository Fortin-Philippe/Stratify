from flask import Blueprint, render_template, session, redirect, url_for, flash
import bd

bp_notification = Blueprint("notification", __name__)

@bp_notification.route("/notifications")
def notifications():
    utilisateur_id = session.get("user_id")
    if not utilisateur_id:
        return redirect(url_for("compte.connexion"))
    notifications = bd.obtenir_notifications(utilisateur_id)
    return render_template("notification.jinja", notifications=notifications)

@bp_notification.route("/accepter-demande/<int:demande_id>")
def accepter_demande(demande_id):
    bd.marquer_demande_acceptee(demande_id)
    bd.supprimer_notification_avec_demande(demande_id)
    flash("Demande acceptée.", "success")
    return redirect(url_for("notification.notifications"))

@bp_notification.route("/refuser-demande/<int:demande_id>")
def refuser_demande(demande_id):
    bd.marquer_demande_refusee(demande_id)
    bd.supprimer_notification_avec_demande(demande_id)
    flash("Demande refusée.", "warning")
    return redirect(url_for("notification.notifications"))