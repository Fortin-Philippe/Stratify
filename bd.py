import os
import types
import contextlib
import mysql.connector
from dotenv import load_dotenv


load_dotenv(".env")

@contextlib.contextmanager
def creer_connexion():
    conn = mysql.connector.connect(
        user=os.getenv('BD_UTILISATEUR'),
        password=os.getenv('BD_MDP'),
        host=os.getenv('BD_SERVEUR'),
        database=os.getenv('BD_NOM_SCHEMA'),
        raise_on_warnings=True
    )
    conn.get_curseur = types.MethodType(get_curseur, conn)
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    else:
        conn.commit()
    finally:
        conn.close()

@contextlib.contextmanager
def get_curseur(self):
    curseur = self.cursor(dictionary=True, buffered=True)
    try:
        yield curseur
    finally:
        curseur.close()

def ajouter_utilisateur(utilisateur):
    with creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            curseur.execute(
                """INSERT INTO utilisateur
                   (user_name, courriel, mdp, description, est_coach, image)
                   VALUES (%(user_name)s, %(courriel)s, %(mdp)s, %(description)s, %(est_coach)s, %(image)s)""",
                utilisateur
            )
            return curseur.lastrowid

def connecter_utilisateur(courriel, mdp):
    with creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            curseur.execute(
                "SELECT * FROM utilisateur WHERE courriel = %(courriel)s AND mdp = %(mdp)s",
                {"courriel": courriel, "mdp": mdp}
            )
            return curseur.fetchone()


def get_utilisateur_par_id(user_id):
    with creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            curseur.execute(
                "SELECT * FROM utilisateur WHERE id = %(id)s",
                {"id": user_id}
            )
            return curseur.fetchone()

def get_utilisateur_par_username(user_name):
    with creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            curseur.execute(
                "SELECT * FROM utilisateur WHERE user_name = %(user_name)s",
                {"user_name": user_name}
            )
            return curseur.fetchone()


def update_utilisateur(user_id, data):
    colonnes = ", ".join(f"{k} = %({k})s" for k in data.keys())
    data["id"] = user_id
    requete = f"UPDATE utilisateur SET {colonnes} WHERE id = %(id)s"

    with creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            curseur.execute(requete, data)

def obtenir_discussions(jeu, niveau):
    """Récupère toutes les discussions pour un jeu et niveau donnés"""
    with creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            curseur.execute(
                """SELECT d.*,

                   (SELECT COUNT(*) FROM messages WHERE discussion_id = d.id) as nombre_messages
                   FROM discussions d
                   WHERE jeu = %(jeu)s AND niveau = %(niveau)s
                   ORDER BY epingle DESC, date_creation DESC""",
                {'jeu': jeu, 'niveau': niveau}
            )
            return curseur.fetchall()

def obtenir_discussion(discussion_id):
    """Récupère une discussion par son ID"""
    with creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            curseur.execute(
                "SELECT * FROM discussions WHERE id = %(id)s",
                {'id': discussion_id}
            )
            return curseur.fetchone()

def creer_discussion(discussion):
    """Crée une nouvelle discussion"""
    with creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            curseur.execute(
                """INSERT INTO discussions
                   (titre, contenu, auteur, jeu, niveau, categorie, date_creation)
                   VALUES (%(titre)s, %(contenu)s, %(auteur)s, %(jeu)s, %(niveau)s, %(categorie)s, NOW())""",
                discussion
            )
            return curseur.lastrowid

def incrementer_vues(discussion_id):
    """Incrémente le compteur de vues d'une discussion"""
    with creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            curseur.execute(
                "UPDATE discussions SET vues = vues + 1 WHERE id = %(id)s",
                {'id': discussion_id}
            )

def obtenir_messages(discussion_id):
    """Récupère tous les messages d'une discussion"""
    with creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            curseur.execute(

                """SELECT * FROM messages

                   WHERE discussion_id = %(discussion_id)s
                   ORDER BY date_creation ASC""",
                {'discussion_id': discussion_id}
            )
            return curseur.fetchall()

def ajouter_message(message):
    """Ajoute un message à une discussion"""
    with creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            curseur.execute(
                """INSERT INTO messages
                   (contenu, auteur, discussion_id, date_creation)
                   VALUES (%(contenu)s, %(auteur)s, %(discussion_id)s, NOW())""",
                message
            )
            return curseur.lastrowid


def obtenir_coachs():
    """Récupère tous les utilisateurs qui sont des coachs"""
    with creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            curseur.execute(
                """SELECT id, user_name, courriel, image, description, est_coach
                   FROM utilisateur
                   WHERE est_coach = 1
                   ORDER BY user_name ASC"""
            )
            return curseur.fetchall()

def obtenir_conversations_utilisateur(user_id):
    query = """
    SELECT 
        u.id, u.user_name, u.image,
        mp.contenu AS dernier_message,
        mp.date_envoi AS date_message
    FROM message_prive mp
    JOIN utilisateur u 
        ON (u.id = CASE 
            WHEN mp.expediteur_id = %(id)s THEN mp.destinataire_id 
            ELSE mp.expediteur_id END)
    WHERE mp.expediteur_id = %(id)s OR mp.destinataire_id = %(id)s
    GROUP BY u.id, u.user_name, u.image, mp.contenu, mp.date_envoi
    ORDER BY mp.date_envoi DESC;
    """
    
    with creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            curseur.execute(query, {'id': user_id})
            return curseur.fetchall()

def obtenir_messages_prives(user_id, autre_id):
    query = """
    SELECT mp.*, u.user_name AS expediteur_nom, u.image AS expediteur_image
    FROM message_prive mp
    JOIN utilisateur u ON mp.expediteur_id = u.id
    WHERE (mp.expediteur_id = %(user_id)s AND mp.destinataire_id = %(autre_id)s)
       OR (mp.expediteur_id = %(autre_id)s AND mp.destinataire_id = %(user_id)s)
    ORDER BY mp.date_envoi ASC;
    """
    with creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            curseur.execute(query, {'user_id': user_id, 'autre_id': autre_id})
            return curseur.fetchall()


def envoyer_message_prive(expediteur_id, destinataire_id, contenu):
    query = """
    INSERT INTO message_prive (expediteur_id, destinataire_id, contenu, date_envoi)
    VALUES (%(expediteur_id)s, %(destinataire_id)s, %(contenu)s, NOW())
    """
    with creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            curseur.execute(query, {
                'expediteur_id': expediteur_id,
                'destinataire_id': destinataire_id,
                'contenu': contenu
            })