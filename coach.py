from flask import Blueprint, render_template, request, session, redirect, url_for, flash
import bd

bp_coach = Blueprint('coach', __name__)

@bp_coach.route('/coachs')
def liste_coachs():
    if not session.get("user_id"):
        flash("Vous devez être connecté pour voir les coachs.", "warning")
        return redirect(url_for("compte.connexion"))

    recherche = request.args.get("elem", "").strip()

    if recherche:
        coachs = bd.rechercher_coachs(recherche)
    else:
        coachs = [c for c in bd.obtenir_coachs() if c["id"] != session.get("user_id")]

    for coach in coachs:
        coach["jeux"] = bd.obtenir_jeux_utilisateur(coach["id"])

    return render_template("coachs.jinja", coachs=coachs, recherche=recherche)

@bp_coach.route("/<int:coach_id>/demande", methods=["GET", "POST"])
def demande_coach(coach_id):
    if not session.get("user_id"):
        flash("Vous devez être connecté pour envoyer une demande.", "warning")
        return redirect(url_for("compte.connexion"))

    if request.method == "POST":
        objectif = request.form.get("objectif")
        message = request.form.get("message")
        utilisateur_id = session["user_id"]
        utilisateur = bd.get_utilisateur_par_id(utilisateur_id)
        nom_utilisateur = utilisateur["user_name"]

        demande_id = bd.ajouter_demande(utilisateur_id, coach_id, objectif, message)

        bd.ajouter_notification(
            coach_id,
            "Nouvelle demande de coaching",
            f"{nom_utilisateur} vous a envoyé une demande : {objectif}.",
            demande_id
        )

        coach = bd.obtenir_coach_par_id(coach_id)
        flash(f"Votre demande a été envoyée à {coach['user_name']}", "success")
        return redirect(url_for("coach.liste_coachs"))

    coach = bd.obtenir_coach_par_id(coach_id)
    return render_template("demande_coach.jinja", coach=coach)
@bp_coach.route("/autocomplete_coach")
def autocomplete_coach():
    query = request.args.get("query", "").strip()
    if not query:
        return []

    coachs = bd.rechercher_coachs(query)


    suggestions = [{"id": c["id"], "nom": c["user_name"]} for c in coachs]

    return suggestions