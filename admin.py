from flask import Blueprint, render_template, session, abort, redirect, url_for, flash
import bd

bp_admin = Blueprint("admin", __name__)

def check_admin():
    if not session.get("est_admin"):
        abort(403)
@bp_admin.route("/utilisateurs")
def liste_utilisateurs():
    check_admin()

    utilisateurs = bd.get_tous_les_utilisateurs()
    return render_template("liste_utilisateurs.jinja", utilisateurs=utilisateurs)

@bp_admin.route("/utilisateur/<int:id_utilisateur>")
def detail_utilisateur(id_utilisateur):
    check_admin()

    utilisateur = bd.get_utilisateur_par_id(id_utilisateur)
    if not utilisateur:
        abort(404)
    utilisateur.pop("mdp", None)
    return render_template("detail_utilisateur.jinja", utilisateur=utilisateur)

@bp_admin.route("/utilisateur/<int:id_utilisateur>/supprimer", methods=["POST"])
def supprimer_utilisateur(id_utilisateur):
    check_admin()

    utilisateur = bd.get_utilisateur_par_id(id_utilisateur)
    if not utilisateur:
        abort(404)
    if bd.est_utilisateur_admin(id_utilisateur):
        flash(f"Impossible de supprimer l'utilisateur {utilisateur['user_name']} car il est également administrateur.", "error")
        return redirect(url_for("admin.detail_utilisateur", id_utilisateur=id_utilisateur))

    bd.archiver_utilisateur(id_utilisateur)

    return redirect(url_for("admin.liste_utilisateurs"))

@bp_admin.route("/utilisateur/<int:id_utilisateur>/verifier-suppression", methods=["POST"])
def verifier_suppression(id_utilisateur):
    check_admin()

    utilisateur = bd.get_utilisateur_par_id(id_utilisateur)
    if not utilisateur:
        return {"ok": False, "message": "Utilisateur introuvable."}, 404

    if bd.est_utilisateur_admin(id_utilisateur):
        return {
            "ok": False,
            "message": "Impossible de supprimer un administrateur."
        }, 400

    return {"ok": True}, 200