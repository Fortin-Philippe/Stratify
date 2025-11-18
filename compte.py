import re
import hashlib

import os
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import bd

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "img", "profiles")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


bp_compte = Blueprint('compte', __name__)

@bp_compte.route('/creer-utilisateur', methods=['GET', 'POST'])
def form_utilisateur():
    jeux = bd.obtenir_jeux()
    erreurs = {}
    if request.method == 'POST':
        user_name = request.form['user_name'].strip()


        courriel = request.form['courriel'].strip()
        mdp = request.form['mdp'].strip()
        mdp_confirmation = request.form['mdp_confirmation'].strip()
        description = request.form.get('description', None)

        est_coach = 1 if request.form.get('est_coach') else 0
        est_connecte = 0

        if len(user_name) < 4 or len(user_name) > 60:
            erreurs['user_name'] = "Le nom doit contenir entre 4 et 60 caractères."
        if not re.match(r"[^@]+@[^@]+\.[^@]+", courriel):
            erreurs['courriel'] = "Veuillez entrer un courriel valide."
        if len(mdp) < 3:
            erreurs['mdp'] = "Le mot de passe doit avoir au moins 3 caractères."
        if mdp != mdp_confirmation:
            erreurs['mdp_confirmation'] = "Les mots de passe ne correspondent pas."

        if erreurs:
            return render_template('form-utilisateur.jinja', erreurs=erreurs)


        utilisateur = {
            "user_name": user_name,

            "courriel": courriel,
            "mdp": hacher_mdp(mdp),
            "description": description,
            "est_coach": est_coach,
            "image":None,
            "est_connecte": est_connecte


        }

        user_id = bd.ajouter_utilisateur(utilisateur)
        jeux_selectionnes = request.form.getlist('jeux')
        bd.ajouter_jeux_utilisateur(user_id, jeux_selectionnes)
        session.permanent = True
        session['user_id'] = user_id
        session['user_name'] = utilisateur['user_name']
        session['est_coach'] = est_coach

        session['est_connecte'] = 1
        flash("Utilisateur créé avec succès !", "success")
        return redirect(url_for('accueil.choisir_jeu'))

    return render_template("form-utilisateur.jinja", erreurs=erreurs, jeux=jeux)

@bp_compte.route('/connexion', methods=['GET', 'POST'])
def connexion():
    erreurs = {}
    if request.method == 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            courriel = request.form['courriel'].strip()
            mdp = request.form['mdp'].strip()

            if not re.match(r"[^@]+@[^@]+\.[^@]+", courriel):
                return {"success": False, "erreurs": {"courriel": "Veuillez entrer un courriel valide."}}, 400

            utilisateur = bd.connecter_utilisateur(courriel, hacher_mdp(mdp))
            if utilisateur:
                session['user_id'] = utilisateur['id']
                session['user_name'] = utilisateur['user_name']
                session['est_coach'] = utilisateur['est_coach']
                session['est_connecte'] = 1
                
                return {"success": True, "message": "Vous êtes connecté !", "redirect": url_for('accueil.choisir_jeu')}, 200
            else:
                return {"success": False, "erreurs": {"connexion": "Le courriel ou le mot de passe est invalide."}}, 400

        courriel = request.form['courriel'].strip()
        mdp = request.form['mdp'].strip()

        if not re.match(r"[^@]+@[^@]+\.[^@]+", courriel):
            erreurs['courriel'] = "Veuillez entrer un courriel valide."
        else:
            utilisateur = bd.connecter_utilisateur(courriel, hacher_mdp(mdp))
            if utilisateur and utilisateur.get("est_supprime"):
                erreurs["connexion"] = "Ce compte a été supprimé."
                return render_template("connexion.jinja", erreurs=erreurs)
            if utilisateur:
                session['user_id'] = utilisateur['id']
                session['user_name'] = utilisateur['user_name']
                session['est_coach'] = utilisateur['est_coach']
                session['est_connecte'] = 1


                est_admin = bd.est_admin(utilisateur['id'])
                session['est_admin'] = est_admin

                if est_admin:
                    bd.set_est_coach(utilisateur['id'], True)
                    session['est_coach'] = 1

                flash("Vous êtes connecté !", "success")
                return redirect('/')
            else:
                erreurs['connexion'] = "Le courriel ou le mot de passe est invalide."

    return render_template('connexion.jinja', erreurs=erreurs)


@bp_compte.route('/profile')
def profile():
    if not session.get('user_id'):
        flash("Vous devez être connecté pour voir votre profil", "danger")
        return redirect(url_for('compte.connexion'))

    utilisateur = bd.get_utilisateur_par_id(session['user_id'])
    if not utilisateur:
        flash("Utilisateur introuvable", "danger")
        return redirect(url_for('accueil.choisir_jeu'))
    return render_template('profile.jinja', utilisateur=utilisateur)


@bp_compte.route("/profile/modifier", methods=["GET", "POST"])
def profile_modif():
    if "user_id" not in session:
        flash("Tu dois être connecté.", "danger")
        return redirect(url_for("compte.connexion"))

    user = bd.get_utilisateur_par_id(session["user_id"])
    if not user:
        flash("Utilisateur introuvable.", "danger")
        return redirect(url_for("accueil.choisir_jeu"))

    dossier_images = os.path.join(os.path.dirname(__file__), "static", "img", "profiles")
    images_profiles = [f"img/profiles/{f}" for f in os.listdir(dossier_images) if f.endswith(".webp")]

    if request.method == "POST":
        user_name = request.form.get("user_name", user["user_name"]).strip()
        description = request.form.get("description", user["description"]).strip()
        est_coach = 1 if request.form.get("est_coach") else 0
        mdp = request.form.get("mdp", None)
        image_path = request.form.get("image", user.get("image"))

        utilisateur_exist = bd.get_utilisateur_par_username(user_name)
        if utilisateur_exist and utilisateur_exist["id"] != user["id"]:
            flash(f"Le nom d'utilisateur '{user_name}' est déjà pris.", "danger")
            return render_template("profile_modif.jinja", user=user, images_profiles=images_profiles)

        update_data = {
            "user_name": user_name,
            "description": description,
            "est_coach": est_coach,
            "image": image_path
        }

        if mdp:
            update_data["mdp"] = hacher_mdp(mdp)

        bd.update_utilisateur(user["id"], update_data)

        session['user_name'] = user_name
        session['est_coach'] = est_coach
        session['image'] = image_path
        session['est_connecte'] = 1

        flash("Profil mis à jour ✅", "success")
        return redirect(url_for("compte.profile"))

    return render_template("profile_modif.jinja", user=user, images_profiles=images_profiles)


@bp_compte.route('/deconnexion')
def deconnexion():
    session.clear()
    flash("Vous avez été déconnecté.", "success")
    return redirect(url_for('accueil.choisir_jeu'))

def hacher_mdp(mdp):
    return hashlib.sha512(mdp.encode()).hexdigest()

@bp_compte.route('/profil/<int:user_id>')
def voir_profil(user_id):
    if 'user_id' not in session:
        flash("Veuillez vous connecter pour accéder aux profils.", "warning")
        return redirect(url_for('compte.connexion'))

    utilisateur = bd.get_utilisateur_par_id(user_id)
    if not utilisateur:
        flash("Profil introuvable.", "danger")
        return redirect(url_for('accueil.choisir_jeu'))

    est_propre_profil = (user_id == session['user_id'])
    return render_template('profil_autre.jinja', utilisateur=utilisateur, est_propre_profil=est_propre_profil)