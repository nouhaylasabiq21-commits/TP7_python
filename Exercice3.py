import datetime
import copy

class ValidationMixin:
    def __init__(self):
        super().__init__()
    
    def valider_titre(self, titre):
        if not titre or not isinstance(titre, str) or not titre.strip():
            raise ValueError("Le titre doit etre une chaine non vide")
        return True
    
    def verifier_titre(self):
        if not hasattr(self, 'titre') or not self.titre:
            raise ValueError("Titre manquant ou invalide")

class HistoriqueMixin:
    def __init__(self):
        super().__init__()
        self._historique = []
        self._index_actuel = -1
    
    def ajouter_historique(self, description, action="Modification"):
        timestamp = datetime.datetime.now()
        entree = {
            'timestamp': timestamp,
            'description': copy.deepcopy(description),
            'action': action
        }
        self._historique.append(entree)
        self._index_actuel = len(self._historique) - 1
    
    def obtenir_derniere_description(self):
        if not self._historique:
            return None
        return self._historique[-1]['description']
    
    def afficher_historique(self):
        print(f"\n Historique de la tache: {getattr(self, 'titre', 'Inconnue')} ")
        if not self._historique:
            print("Aucun historique disponible.")
            return
        
        for i, entree in enumerate(self._historique):
            ts = entree['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
            desc = entree['description'][:50] + "..." if len(entree['description']) > 50 else entree['description']
            print(f"{i+1}. [{ts}] {entree['action']}: {desc}")
    
    def restaurer_version(self, index):
        if 0 <= index < len(self._historique):
            version = self._historique[index]['description']
            if hasattr(self, 'description'):
                self.description = copy.deepcopy(version)
            self._index_actuel = index
            return version
        raise IndexError("Index d'historique invalide")

class JournalisationMixin:
    def __init__(self, niveau="INFO"):
        super().__init__()
        self._niveau_journal = niveau
        self._journal = []
    
    def journaliser(self, message, niveau=None):
        if niveau is None:
            niveau = self._niveau_journal
        
        timestamp = datetime.datetime.now()
        entree = (timestamp, niveau, message)
        self._journal.append(entree)
        
        prefixe = f"[{niveau}]"
        if niveau == "ERREUR":
            prefixe = f"\033[91m[{niveau}]\033[0m"
        elif niveau == "SUCCES":
            prefixe = f"\033[92m[{niveau}]\033[0m"
        
        print(f"{prefixe} {timestamp.strftime('%Y-%m-%d %H:%M:%S')}: {message}")
    
    def afficher_journal_complet(self):
        print(f"\n Journal complet de la tache")
        for timestamp, niveau, message in self._journal:
            print(f"[{niveau}] {timestamp.strftime('%Y-%m-%d %H:%M:%S')}: {message}")
    
    def exporter_journal(self):
        return [
            {
                'timestamp': ts.isoformat(),
                'niveau': niveau,
                'message': msg
            }
            for ts, niveau, msg in self._journal
        ]

class Tache(ValidationMixin, HistoriqueMixin, JournalisationMixin):
    def __init__(self, titre, description="", niveau_journal="INFO"):
        ValidationMixin.__init__(self)
        HistoriqueMixin.__init__(self)
        JournalisationMixin.__init__(self, niveau_journal)
        
        self.valider_titre(titre)
        self.titre = titre.strip()
        self.description = description
        self.date_creation = datetime.datetime.now()
        self.date_modification = self.date_creation
        self.terminee = False
        
        self.journaliser(f"Tâche créée: {self.titre}", "SUCCES")
        self.ajouter_historique(description, "Création")
    
    def mettre_a_jour(self, nouvelle_description):
        self.verifier_titre()
        
        ancienne_description = self.description
        self.description = nouvelle_description
        self.date_modification = datetime.datetime.now()
        
        self.journaliser(f"Description mise à jour: '{self.titre}'", "INFO")
        self.journaliser(f"Ancienne: {ancienne_description[:30]}...", "DEBUG")
        self.journaliser(f"Nouvelle: {nouvelle_description[:30]}...", "DEBUG")
        
        self.ajouter_historique(nouvelle_description, "Mise à jour")
    
    def completer(self):
        if self.terminee:
            self.journaliser(f"Tache deja terminee: {self.titre}", "AVERTISSEMENT")
            return
        
        self.terminee = True
        self.date_modification = datetime.datetime.now()
        self.journaliser(f"Tache marquee comme terminee: {self.titre}", "SUCCES")
        self.ajouter_historique(self.description, "Complétion")
    
    def modifier_titre(self, nouveau_titre):
        self.valider_titre(nouveau_titre)
        ancien_titre = self.titre
        self.titre = nouveau_titre.strip()
        self.date_modification = datetime.datetime.now()
        
        self.journaliser(f"Titre modifie: '{ancien_titre}' -> '{nouveau_titre}'", "INFO")
    
    def obtenir_infos(self):
        self.verifier_titre()
        return {
            'titre': self.titre,
            'description': self.description,
            'date_creation': self.date_creation.isoformat(),
            'date_modification': self.date_modification.isoformat(),
            'terminee': self.terminee,
            'versions': len(self._historique),
            'entrees_journal': len(self._journal)
        }
    
    def afficher_resume(self):
        infos = self.obtenir_infos()
        print(f"\nTache: {infos['titre']} ")
        print(f"Description: {infos['description'][:100]}{'...' if len(infos['description']) > 100 else ''}")
        print(f"Créée le: {infos['date_creation']}")
        print(f"Dernière modification: {infos['date_modification']}")
        print(f"Statut: {'Terminée' if infos['terminee'] else 'En cours'}")
        print(f"Nombre de versions: {infos['versions']}")
        print(f"Entrées de journal: {infos['entrees_journal']}")

def main():
    print(" Systeme de Gestion de Tâches Professionnelles \n")
    
    tache1 = Tache("Rapport trimestriel", "Analyser les données du Q3 2024")
    print("\n Initialisation ")
    tache1.afficher_resume()
    
    print("\n Premiere mise a jour ")
    tache1.mettre_a_jour("Analyser les donnees du Q3 2024 et preparer presentation")
    
    print("\n Deuxiee mise a jour ")
    tache1.mettre_a_jour("Analyser les données du Q3 2024, préparer présentation et inclure recommandations")
    
    print("\nModification du titre ")
    tache1.modifier_titre("Rapport et présentation Q3 2024")
    
    print("\nAffichage de l'historique ")
    tache1.afficher_historique()
    
    print("\nTest de restauration ")
    try:
        version_restauree = tache1.restaurer_version(0)
        print(f"Version restauree (premiere): {version_restauree[:50]}...")
    except IndexError as e:
        print(f"Erreur de restauration: {e}")
    
    print("\n Complétion de la tâche ")
    tache1.completer()
    tache1.afficher_resume()
    
    print("\n Affichage du journal complet ")
    tache1.afficher_journal_complet()
    
    print("\n Test de validation (devrait échouer)")
    try:
        tache_invalide = Tache("", "Description")
    except ValueError as e:
        print(f"Erreur attendue: {e}")
    
    try:
        tache_invalide = Tache("   ", "Description")
    except ValueError as e:
        print(f"Erreur attendue: {e}")
    
    print("\n--- Export du journal ---")
    journal_export = tache1.exporter_journal()
    print(f"Journal exporté avec {len(journal_export)} entrées")

if __name__ == "__main__":
    main()