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
        
def supprimer_discussion(discussion_id):
    """Supprime une discussion et tous ses messages"""
    with creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            curseur.execute('DELETE FROM messages WHERE discussion_id = %s', (discussion_id,))
            
            curseur.execute('DELETE FROM discussions WHERE id = %s', (discussion_id,))


def supprimer_message(message_id):
    """Supprime un message"""
    with creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            curseur.execute('DELETE FROM messages WHERE id = %s', (message_id,))


def obtenir_message(message_id):
    """Recupere un message par son ID"""
    with creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            curseur.execute('SELECT * FROM messages WHERE id = %s', (message_id,))
            resultat = curseur.fetchone()
            return resultat if resultat else None