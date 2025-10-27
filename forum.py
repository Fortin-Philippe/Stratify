from flask import Blueprint, render_template, request, redirect, url_for, flash
import bd

forum_bp = Blueprint('forum', __name__)

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

@forum_bp.route('/forum')
def index():
    """Affiche la liste des discussions du forum avec recherche et filtres"""
    jeu_selectionne = request.cookies.get('jeu_selectionne')
    niveau_selectionne = request.cookies.get('niveau_selectionne')
    
    if not jeu_selectionne or not niveau_selectionne:
        return redirect(url_for('accueil.choisir_jeu'))
    
    search_query = request.args.get('search', '').strip()
    category_filter = request.args.get('filter', 'all')
    
    discussions = bd.obtenir_discussions(jeu_selectionne, niveau_selectionne)
    
    if search_query:
        discussions = [
            d for d in discussions 
            if (search_query.lower() in d['titre'].lower() or 
                search_query.lower() in d['contenu'].lower() or 
                search_query.lower() in d['auteur'].lower())
        ]
    
    if category_filter != 'all':
        discussions = [
            d for d in discussions 
            if d.get('categorie', 'discussion') == category_filter
        ]
    
    nom_jeu = JEUX.get(jeu_selectionne, {}).get('nom', jeu_selectionne)
    nom_niveau = NOMS_NIVEAUX.get(jeu_selectionne, {}).get(niveau_selectionne, niveau_selectionne)
    
    return render_template('forum.jinja',
                         discussions=discussions,
                         nom_jeu=nom_jeu,
                         nom_niveau=nom_niveau,
                         jeu_selectionne=jeu_selectionne,
                         niveau_selectionne=niveau_selectionne,
                         search_query=search_query,
                         category_filter=category_filter)


@forum_bp.route('/forum/nouvelle-discussion', methods=['GET', 'POST'])
def nouvelle_discussion():
    """Créer une nouvelle discussion"""
    jeu_selectionne = request.cookies.get('jeu_selectionne')
    niveau_selectionne = request.cookies.get('niveau_selectionne')
    
    if not jeu_selectionne or not niveau_selectionne:
        flash('Sélection de jeu invalide', 'error')
        return redirect(url_for('accueil.choisir_jeu'))
    
    if request.method == 'GET':
        nom_jeu = JEUX.get(jeu_selectionne, {}).get('nom', jeu_selectionne)
        nom_niveau = NOMS_NIVEAUX.get(jeu_selectionne, {}).get(niveau_selectionne, niveau_selectionne)
        
        return render_template('message.jinja',
                             nom_jeu=nom_jeu,
                             nom_niveau=nom_niveau)
    
    titre = request.form.get('titre')
    contenu = request.form.get('contenu')
    auteur = request.form.get('auteur')
    categorie = request.form.get('categorie', 'discussion')
    
    if not titre or not contenu or not auteur:
        flash('Tous les champs sont requis', 'error')
        return redirect(url_for('forum.nouvelle_discussion'))
    
    discussion_data = {
        'titre': titre,
        'contenu': contenu,
        'auteur': auteur,
        'jeu': jeu_selectionne,
        'niveau': niveau_selectionne,
        'categorie': categorie
    }
    
    discussion_id = bd.creer_discussion(discussion_data)
    
    flash('Discussion créée avec succès !', 'success')
    return redirect(url_for('forum.voir_discussion', discussion_id=discussion_id))


@forum_bp.route('/forum/discussion/<int:discussion_id>', methods=['GET', 'POST'])
def voir_discussion(discussion_id):
    """Voir une discussion et ses messages"""
    discussion = bd.obtenir_discussion(discussion_id)
    
    if not discussion:
        flash('Discussion introuvable', 'error')
        return redirect(url_for('forum.index'))

    bd.incrementer_vues(discussion_id)

    if request.method == 'POST':
        contenu = request.form.get('contenu')
        auteur = request.form.get('auteur')

        if not contenu or not auteur:
            flash('Tous les champs sont requis', 'error')
            return redirect(url_for('forum.voir_discussion', discussion_id=discussion_id))

        message_data = {
            'contenu': contenu,
            'auteur': auteur,
            'discussion_id': discussion_id
        }
        bd.ajouter_message(message_data)
        flash('Message posté avec succès !', 'success')
        return redirect(url_for('forum.voir_discussion', discussion_id=discussion_id))

    messages = bd.obtenir_messages(discussion_id)

    return render_template('discussion.jinja',
                         discussion=discussion,
                         messages=messages)