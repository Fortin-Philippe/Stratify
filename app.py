

from flask import Flask, render_template, redirect, request, url_for
from bd import ajouter_utilisateur
from accueil import bp as acceuil_bp
from forum import forum_bp as forum_bp
from compte import bp_compte
from coach import bp_coach
from message import message_bp
import os

app = Flask(__name__)

app.secret_key = os.urandom(24)
app.register_blueprint(bp_compte)
app.register_blueprint(acceuil_bp)
app.register_blueprint(forum_bp)
app.register_blueprint(bp_coach)
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

if __name__ == "__main__":
    app.run(debug=True)