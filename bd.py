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
                   (titre, contenu, auteur, auteur_id, jeu, niveau, categorie, date_creation)
                   VALUES (%(titre)s, %(contenu)s, %(auteur)s, %(auteur_id)s, %(jeu)s, %(niveau)s, %(categorie)s, NOW())""",
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
                   (contenu, auteur, auteur_id, discussion_id, date_creation)
                   VALUES (%(contenu)s, %(auteur)s, %(auteur_id)s, %(discussion_id)s, NOW())""",
                message
            )
            return curseur.lastrowid


def obtenir_coachs():
    """Récupère tous les utilisateurs qui sont des coachs"""
    with creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            curseur.execute(
                """SELECT id, user_name, courriel, image, description, est_coach, est_supprime
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

def obtenir_conversations_utilisateur(user_id):
    query = """
    SELECT 
        u.id AS id,
        u.user_name,
        u.image,
        u.est_supprime,
        MAX(mp.date_envoi) AS date_message,
        MAX(
            CASE 
                WHEN mp.supprime = TRUE THEN 'message supprimé'
                ELSE mp.contenu
            END
        ) AS dernier_message
    FROM message_prive mp
    JOIN utilisateur u 
        ON u.id = CASE 
            WHEN mp.expediteur_id = %(id)s THEN mp.destinataire_id 
            ELSE mp.expediteur_id 
        END
    WHERE mp.expediteur_id = %(id)s OR mp.destinataire_id = %(id)s
    GROUP BY u.id, u.user_name, u.image, u.est_supprime
    ORDER BY date_message DESC;
    """
    
    with creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            curseur.execute(query, {'id': user_id})
            return curseur.fetchall()

def obtenir_messages_prives(user_id, autre_id):
    query = """
    SELECT mp.*, u.user_name AS expediteur_nom, u.image AS expediteur_image, u.est_supprime,
    CASE 
        WHEN mp.supprime = TRUE THEN 'message supprimé'
        ELSE mp.contenu
    END AS contenu
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

            curseur.execute("SELECT user_name FROM utilisateur WHERE id = %s", (expediteur_id,))
            expediteur = curseur.fetchone()

            if expediteur:
                titre = "Nouveau message privé"
                message = f"Vous avez reçu un message de {expediteur['user_name']}."
                curseur.execute("""
                    INSERT INTO notifications (utilisateur_id, titre, message, lu, date_envoi, autre_id)
                    VALUES (%s, %s, %s, FALSE, NOW(), %s)
                """, (destinataire_id, titre, message, expediteur_id))

def rechercher_coachs(recherche):
    with creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            curseur.execute(
                """SELECT id, user_name, courriel, image, description, est_coach, est_supprime
                   FROM utilisateur
                   WHERE est_coach = 1
                   AND (LOWER(user_name) LIKE %(recherche)s OR LOWER(courriel) LIKE %(recherche)s)
                   ORDER BY user_name ASC""",
                {'recherche': f"%{recherche.lower()}%"}
            )
            return curseur.fetchall()
def ajouter_jeux_utilisateur(user_id, jeux_ids):
    """Associe plusieurs jeux à un utilisateur"""
    with creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            for jeu_id in jeux_ids:
                curseur.execute(
                    """INSERT INTO utilisateur_jeux (utilisateur_id, jeu_id)
                       VALUES (%(user_id)s, %(jeu_id)s)""",
                    {"user_id": user_id, "jeu_id": jeu_id}
                )

def obtenir_jeux_utilisateur(user_id):
    """Récupère tous les jeux d'un utilisateur"""
    with creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            curseur.execute(
                """SELECT j.id, j.nom
                   FROM jeux j
                   JOIN utilisateur_jeux uj ON j.id = uj.jeu_id
                   WHERE uj.utilisateur_id = %(user_id)s""",
                {"user_id": user_id}
            )
            return curseur.fetchall()

def obtenir_jeux():
    """Récupère tous les jeux disponibles"""
    with creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            curseur.execute("SELECT id, nom FROM jeux ORDER BY nom ASC")
            return curseur.fetchall()

def obtenir_notifications(utilisateur_id):
    with creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            curseur.execute("""
                SELECT id, titre, message, date_envoi, lu, demande_id, autre_id
                FROM notifications
                WHERE utilisateur_id = %s
                ORDER BY date_envoi DESC
            """, (utilisateur_id,))
            return curseur.fetchall()

def notifications_non_lues(utilisateur_id):
    with creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            curseur.execute("""
                SELECT COUNT(*) AS nb
                FROM notifications
                WHERE utilisateur_id = %s AND lu = FALSE
            """, (utilisateur_id,))
            resultat = curseur.fetchone()
            if resultat:
                return resultat["nb"]
            else:
                return 0

def ajouter_demande(utilisateur_id, coach_id, objectif, message):
    with creer_connexion() as conn:
        with conn.cursor(dictionary=True) as curseur:
            curseur.execute("""
                INSERT INTO demandes_coach (utilisateur_id, coach_id, objectif, message, statut)
                VALUES (%s, %s, %s, %s, %s)
            """, (utilisateur_id, coach_id, objectif, message, "en_attente"))
            return curseur.lastrowid

def marquer_demande_acceptee(demande_id):
    with creer_connexion() as conn:
        with conn.cursor() as curseur:
            curseur.execute("UPDATE demandes_coach SET statut = 'acceptee' WHERE id = %s", (demande_id,))
        conn.commit()

def marquer_demande_refusee(demande_id):
    with creer_connexion() as conn:
        with conn.cursor() as curseur:
            curseur.execute("UPDATE demandes_coach SET statut = 'refusee' WHERE id = %s", (demande_id,))
        conn.commit()

def obtenir_coach_par_id(coach_id):
    with creer_connexion() as conn:
        with conn.cursor(dictionary=True) as curseur:
            curseur.execute("SELECT id, user_name FROM utilisateur WHERE id = %s AND est_coach = 1", (coach_id,))
            return curseur.fetchone()
def ajouter_notification(utilisateur_id, titre, message, demande_id=None):
    with creer_connexion() as conn:
        with conn.cursor(dictionary=True) as curseur:
            curseur.execute("""
                INSERT INTO notifications (utilisateur_id, titre, message, demande_id)
                VALUES (%s, %s, %s, %s)
            """, (utilisateur_id, titre, message, demande_id))
        conn.commit()
def supprimer_notification_avec_demande(demande_id):
    with creer_connexion() as conn:
        with conn.cursor() as curseur:
            curseur.execute("DELETE FROM notifications WHERE demande_id = %s", (demande_id,))
        conn.commit()

def marquer_notifications_comme_lues(utilisateur_id):
    query = "UPDATE notifications SET lu = TRUE WHERE utilisateur_id = %s"
    with creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            curseur.execute(query, (utilisateur_id,))

def est_admin(user_id):
    with creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            curseur.execute(
                "SELECT 1 FROM admin WHERE id_utilisateur = %(id)s",
                {"id": user_id}
            )
            return curseur.fetchone() is not None

def get_tous_les_utilisateurs():
    with creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            curseur.execute("SELECT id, user_name, courriel, description, est_coach, image, est_supprime FROM utilisateur")
            return curseur.fetchall()
        
def set_est_coach(id_utilisateur, valeur: bool):
    with creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            curseur.execute(
                "UPDATE utilisateur SET est_coach = %s WHERE id = %s",
                (1 if valeur else 0, id_utilisateur)
            )
            conn.commit()

def archiver_utilisateur(id_utilisateur):
    with creer_connexion() as conn:
        with conn.get_curseur() as curseur:

            curseur.execute(""" UPDATE utilisateur SET est_supprime = 1 WHERE id = %s """, (id_utilisateur,))

            curseur.execute(""" UPDATE messages SET supprime = 1 WHERE auteur_id = %s""", (id_utilisateur,))

            curseur.execute(""" UPDATE message_prive SET supprime = 1 WHERE expediteur_id = %s""", (id_utilisateur,))
