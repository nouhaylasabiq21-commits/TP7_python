from datetime import datetime
import json
from abc import ABC, abstractmethod

class Horodatable:
    def horodatage(self):
        print(f"[LOG] Action a {datetime.now()}")

class Validable:
    def valider(self):
        if not getattr(self, "titre", None):
            raise ValueError("Titre manquant")
        print("Validation OK")

class Serializable:
    def to_json(self):
        """Serialise l'objet en JSON en incluant tous ses attributs non callable."""
        data = {}
        for attr_name in dir(self):
            if not attr_name.startswith('__'):  
                attr_value = getattr(self, attr_name)
                if not callable(attr_value):  
                    if isinstance(attr_value, datetime):
                        data[attr_name] = attr_value.isoformat()
                    elif hasattr(attr_value, 'to_json'):
                        data[attr_name] = attr_value.to_json()
                    else:
                        try:
                            json.dumps(attr_value)  
                            data[attr_name] = attr_value
                        except (TypeError, ValueError):
                            data[attr_name] = str(attr_value)
        
        data['_class'] = self.__class__.__name__
        
        return json.dumps(data, indent=2, ensure_ascii=False)

class Historisable:
    def __init__(self):
        super().__init__()
        self._historique = []
    
    def ajouter_historique(self, action, details=""):
        entree = {
            'action': action,
            'details': details,
            'timestamp': datetime.now()
        }
        self._historique.append(entree)
        print(f"[HISTORIQUE] {action} - {details}")
    
    def afficher_historique(self):
        """Affiche l'historique complet."""
        print(f"\n=== Historique de {getattr(self, 'titre', 'l\'objet')} ===")
        for i, entree in enumerate(self._historique, 1):
            ts = entree['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
            print(f"{i}. [{ts}] {entree['action']} - {entree['details']}")

class Loggable(ABC):
    
    @abstractmethod
    def log_action(self, action):
        pass
    
    @abstractmethod
    def get_log_level(self):
        pass

class LoggableImplementation(Loggable):
    
    def __init__(self, log_level="INFO"):
        super().__init__()
        self._log_level = log_level
    
    def log_action(self, action):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{self._log_level}] {timestamp} - {action}")
    
    def get_log_level(self):
        return self._log_level

class Document(Horodatable, Validable, Serializable, Historisable, LoggableImplementation):
    def __init__(self, titre, contenu, log_level="INFO"):
        Historisable.__init__(self)
        LoggableImplementation.__init__(self, log_level)
        
        self.titre = titre
        self.contenu = contenu
        self.date_creation = datetime.now()
    
    def sauvegarder(self):
        self.log_action("Début de sauvegarde")
        
        self.ajouter_historique("Sauvegarde", f"Document '{self.titre}'")
        
        self.horodatage()
        
        self.valider()
        
        print(f"Document '{self.titre}' sauvegardé.")
        
        self.log_action("Sauvegarde terminée")

class Rapport(Document):
    def __init__(self, titre, contenu, auteur, log_level="INFO"):
        super().__init__(titre, contenu, log_level)
        self.auteur = auteur
        self.version = 1.0
    
    def publier(self):
        self.log_action(f"Publication du rapport par {self.auteur}")
        self.ajouter_historique("Publication", f"Version {self.version} par {self.auteur}")
        print(f"Rapport '{self.titre}' publie par {self.auteur}")

def main():
    print(" Exemple 1: Document de base ")
    doc = Document("Rapport Annuel", "Contenu du rapport...")
    doc.sauvegarder()
    
    print("\n Exemple 2: Sérialisation en JSON ")
    json_str = doc.to_json()
    print("Document serialise :")
    print(json_str)
    
    print("\n Exemple 3: Affichage de l'historique ")
    doc.afficher_historique()
    
    print("\n Exemple 4: Rapport avec auteur ")
    rapport = Rapport(
        "Analyse Financiere Q4", 
        "Résultats du quatrieme trimestre...",
        "Alice Dupont",
        "DEBUG"
    )
    
    rapport.sauvegarder()
    rapport.publier()
    rapport.afficher_historique()
    
    print("\n Exemple 5: Test de validation (erreur) ")
    try:
        doc_invalide = Document("", "Contenu sans titre")
        doc_invalide.sauvegarder()
    except ValueError as e:
        print(f"Erreur de validation: {e}")
    
    print("\n Exemple 6: JSON du rapport ")
    rapport_json = rapport.to_json()
    print(rapport_json)

if __name__ == "__main__":
    main()