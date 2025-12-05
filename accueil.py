
from flask import Blueprint, render_template, request, make_response, redirect, url_for

bp = Blueprint('accueil', __name__)




JEUX = {
    'valorant': {'nom': 'Valorant', 'description': 'FPS tactique 5v5'},
    'lol': {'nom': 'League of Legends', 'description': 'MOBA stratégique'},
    'cs2': {'nom': 'Counter-Strike 2', 'description': 'FPS compétitif'},
    'rocketleague': {'nom': 'Rocket League', 'description': 'Jeu de voiture et football'}}


NIVEAUX = {
    'valorant': [
        {'id': 'fer', 'nom': 'Fer'},
        {'id': 'Platine', 'nom': 'Platine'},
        {'id': 'immortal', 'nom': 'Platine - immortal'}
    ],
    'lol': [
        {'id': 'bronze', 'nom': 'bronze'},
        {'id': 'platine', 'nom': 'platine'},
        {'id': 'grandmaster', 'nom': 'grandmaster'}
    ],
    'cs2': [
        {'id': 'Rank_15', 'nom': 'Rank_15'},
        {'id': 'Rank_30', 'nom': 'Rank_30'},
        {'id': 'rank_40', 'nom': 'rank_40'}
    ],
     'rocketleague': [
        {'id': 'bronze', 'nom': 'bronze'},
        {'id': 'or', 'nom': 'or'},
        {'id': 'champion', 'nom': 'champion'}
    ]
}


NOMS_NIVEAUX = {
    'valorant': {
        'fer': 'fer',
        'Platine': 'Platine',
        'immortal': 'immortal'
    },
    'lol': {
        'bronze': 'bronze',
        'platine': 'platine',
        'grandmaster': 'grandmaster'
    },
    'cs2': {
        'Rank_15': 'Rank_15',
        'Rank_30': 'Rank_30',
        'mRank_45': 'MRank_45'
    },
    'rocketleague': {
        'bronze': 'bronze',
        'or': 'or',
        'dchampion': 'champion'
    }
}




@bp.route('/')
@bp.route('/jeu/selection')
def choisir_jeu():
    """Affiche la page de sélection de jeu"""
    jeu_selectionne = request.cookies.get('jeu_selectionne')
    return render_template('accueil.jinja',
                         jeux=JEUX,
                         jeu_selectionne=jeu_selectionne)


@bp.route('/jeu/selectionner/<jeu_id>')
def selectionner_jeu(jeu_id):
    """Enregistre le jeu sélectionné dans un cookie"""
    if jeu_id not in JEUX:
        return redirect(url_for('accueil.choisir_jeu'))


    response = make_response(redirect(url_for('accueil.choisir_niveau')))


    response.set_cookie('jeu_selectionne', jeu_id, max_age=60*60*24*7)

    return response




@bp.route('/niveau/selection')
def choisir_niveau():
    """Affiche la page de sélection de niveau en fonction du jeu"""

    jeu_selectionne = request.cookies.get('jeu_selectionne')

    if not jeu_selectionne or jeu_selectionne not in NIVEAUX:
        return redirect(url_for('accueil.choisir_jeu'))


    niveau_selectionne = request.cookies.get('niveau_selectionne')

    niveaux = NIVEAUX[jeu_selectionne]
    nom_jeu = JEUX[jeu_selectionne]['nom']

    return render_template('accueil.jinja',
                         niveaux=niveaux,
                         jeu_selectionne=jeu_selectionne,
                         nom_jeu=nom_jeu,
                         niveau_selectionne=niveau_selectionne)


@bp.route('/niveau/selectionner/<niveau_id>')
def selectionner_niveau(niveau_id):
    """Enregistre le niveau sélectionné dans un cookie"""
    jeu_selectionne = request.cookies.get('jeu_selectionne')

    if not jeu_selectionne:
        return redirect(url_for('accueil.choisir_jeu'))


    response = make_response(redirect(url_for('accueil.confirmation')))


    response.set_cookie('niveau_selectionne', niveau_id, max_age=60*60*24*7)

    return response




@bp.route('/confirmation')
def confirmation():
    """Redirige vers le forum après confirmation des choix"""
    jeu_selectionne = request.cookies.get('jeu_selectionne')
    niveau_selectionne = request.cookies.get('niveau_selectionne')

    if not jeu_selectionne or not niveau_selectionne:
        return redirect(url_for('accueil.choisir_jeu'))

    return redirect(url_for('forum.index'))




@bp.route('/reinitialiser')
def reinitialiser():
    """Efface les cookies et recommence la sélection"""
    response = make_response(redirect(url_for('accueil.choisir_jeu')))
    response.set_cookie('jeu_selectionne', '', max_age=0)
    response.set_cookie('niveau_selectionne', '', max_age=0)
    return response
