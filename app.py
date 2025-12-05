

from gc import get_objects
from flask import Flask, jsonify, render_template, redirect, request, url_for, session
from bd import ajouter_utilisateur
from accueil import bp as acceuil_bp
from forum import forum_bp as forum_bp
from compte import bp_compte
from coach import bp_coach
from admin import bp_admin

from notification import bp_notification
from message import message_bp
import os, bd


app = Flask(__name__)

app.secret_key = os.urandom(24)
app.register_blueprint(bp_compte)
app.register_blueprint(acceuil_bp)
app.register_blueprint(forum_bp)
app.register_blueprint(bp_coach)
app.register_blueprint(bp_admin)

app.register_blueprint(bp_notification)
app.register_blueprint(message_bp)

@app.route('/')
def home():
        return render_template("accueil.jinja")

@app.route('/creer-utilisateur', methods=['GET', 'POST'])
def form_utilisateur():
    if request.method == 'POST':
        nom_utilisateur = request.form['nom_utilisateur']
        courriel = request.form['courriel']
        mdp = request.form['mdp']
        description = request.form.get('description', None)
        est_coach = bool(request.form.get('est_coach'))

        utilisateur = {
            "user_name": nom_utilisateur,
            "courriel": courriel,
            "mdp": mdp,
            "description": description,
            "est_coach": est_coach
        }

        ajouter_utilisateur(utilisateur)

        return redirect(url_for('home'))
    else:
         return render_template("form-utilisateur.jinja")

@app.context_processor
def injecter_nb_notifications():

    nb_notifications = 0
    utilisateur_id = session.get("user_id")
    if utilisateur_id:
        nb_notifications = bd.notifications_non_lues(utilisateur_id)
    return {"nb_notifications": nb_notifications}

if __name__ == "__main__":
    app.run(debug=True)

@app.route("/autocomplete")
def autocomplete():
    query = request.args.get("query", "").lower()
    results = [sujet['titre'] for sujet in get_objects() if query in sujet['titre'].lower()]
    return jsonify(results[:5])
def render_error(code, message):
    return render_template("erreur.jinja", code=code, message=message), code

@app.errorhandler(404)
def not_found(e):
    return render_error(404, "Page non trouvée")

@app.errorhandler(500)
def server_error(e):
    return render_error(500, "Erreur interne du serveur")

@app.errorhandler(403)
def forbidden(e):
    return render_error(403, "Accès interdit")

@app.errorhandler(401)
def unauthorized(e):
    return render_error(401, "Authentification requise")

@app.errorhandler(400)
def bad_request(e):
    return render_error(400, "Requête invalide")
