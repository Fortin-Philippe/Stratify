from flask import Blueprint, render_template, request, redirect, url_for, flash, session
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
    auteur = session.get('user_name')
    auteur_id = session.get('user_id')
    categorie = request.form.get('categorie', 'discussion')
    
    if not titre or not contenu or not auteur:
        flash('Tous les champs sont requis', 'error')
        return redirect(url_for('forum.nouvelle_discussion'))
    
    discussion_data = {
        'titre': titre,
        'contenu': contenu,
        'auteur': auteur,
        'auteur_id': auteur_id,
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
        auteur = session.get('user_name')
        auteur_id = session.get('user_id')

        if not contenu or not auteur:
            flash('Tous les champs sont requis', 'error')
            return redirect(url_for('forum.voir_discussion', discussion_id=discussion_id))

        message_data = {
            'contenu': contenu,
            'auteur': auteur,
            'auteur_id': auteur_id,
            'discussion_id': discussion_id
        }
        bd.ajouter_message(message_data)
        flash('Message posté avec succès !', 'success')
        return redirect(url_for('forum.voir_discussion', discussion_id=discussion_id))

    messages = bd.obtenir_messages(discussion_id)
    discussion_auteur = bd.get_utilisateur_par_username(discussion['auteur'])
    messages_auteurs = {m['auteur']: bd.get_utilisateur_par_username(m['auteur']) for m in messages}

    return render_template('discussion.jinja',
                         discussion=discussion,
                         messages=messages,
                         discussion_auteur=discussion_auteur,
                         messages_auteurs=messages_auteurs)


@forum_bp.route('/forum/discussion/<int:discussion_id>/supprimer', methods=['POST'])
def supprimer_discussion(discussion_id):
    """Supprimer une discussion (réservé aux coachs)"""
    if not session.get('user_name'):
        flash('Vous devez être connecté', 'error')
        return redirect(url_for('compte.connexion'))
    
    if not session.get('est_coach'):
        flash('Vous n\'avez pas les permissions pour supprimer cette discussion', 'error')
        return redirect(url_for('forum.voir_discussion', discussion_id=discussion_id))
    
    discussion = bd.obtenir_discussion(discussion_id)
    if discussion:
        bd.supprimer_discussion(discussion_id)
        flash('Discussion supprimée avec succès', 'success')
        return redirect(url_for('forum.index'))
    else:
        flash('Discussion introuvable', 'error')
        return redirect(url_for('forum.index'))


@forum_bp.route('/forum/message/<int:message_id>/supprimer', methods=['POST'])
def supprimer_message(message_id):
    """Supprimer un message (réservé aux coachs)"""
    if not session.get('user_name'):
        flash('Vous devez être connecté', 'error')
        return redirect(url_for('compte.connexion'))
    
    if not session.get('est_coach'):
        flash('Vous n\'avez pas les permissions pour supprimer ce message', 'error')
        return redirect(url_for('forum.index'))
    
    message = bd.obtenir_message(message_id)
    if message:
        discussion_id = message['discussion_id']
        bd.supprimer_message(message_id)
        flash('Message supprimé avec succès', 'success')
        return redirect(url_for('forum.voir_discussion', discussion_id=discussion_id))
    else:
        flash('Message introuvable', 'error')
        return redirect(url_for('forum.index'))
