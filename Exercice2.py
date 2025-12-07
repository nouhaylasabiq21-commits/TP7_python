import json
import csv
from datetime import datetime
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import xml.etree.ElementTree as ET
from io import StringIO

class Serializable:
    
    def to_json(self, include_history: bool = False) -> str:
        data = self._get_serializable_data()
        if include_history and hasattr(self, 'historique'):
            data['_historique'] = [
                {
                    'timestamp': ts.isoformat(),
                    'etat': etat
                }
                for ts, etat in self.historique
            ]
        
        data['_class'] = self.__class__.__name__
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def _get_serializable_data(self) -> Dict[str, Any]:
        data = {}
        for attr_name, attr_value in self.__dict__.items():
            if attr_name.startswith('_') and attr_name != '_class':
                continue
            if isinstance(attr_value, datetime):
                data[attr_name] = attr_value.isoformat()
            elif hasattr(attr_value, '_get_serializable_data'):
                data[attr_name] = attr_value._get_serializable_data()
            else:
                try:
                    json.dumps(attr_value)
                    data[attr_name] = attr_value
                except (TypeError, ValueError):
                    data[attr_name] = str(attr_value)
        
        return data
    
    @classmethod
    def from_json(cls, json_str: str):
        data = json.loads(json_str)
        return cls(**data)

class Historisable:
    
    def __init__(self):
        self.historique: List[tuple] = []
    
    def enregistrer_etat(self, action: str = "Modification"):
        etat_copie = self._copier_etat()
        self.historique.append((datetime.now(), action, etat_copie))
        
        if hasattr(self, 'journaliser'):
            self.journaliser(f"Etat enregistre pour {action}")
    
    def _copier_etat(self) -> Dict[str, Any]:
        etat = {}
        for attr, value in self.__dict__.items():
            if attr != 'historique':  
                if isinstance(value, (list, dict)):
                    import copy
                    etat[attr] = copy.deepcopy(value)
                else:
                    etat[attr] = value
        return etat
    
    def restaurer_etat(self, index: int = -1):
        if not self.historique:
            raise ValueError("Aucun etat historique disponible")
        
        if index < 0:
            index = len(self.historique) + index
        
        timestamp, action, etat = self.historique[index]
        
        for attr, value in etat.items():
            setattr(self, attr, value)
        
        if hasattr(self, 'journaliser'):
            self.journaliser(f"Etat restaue depuis {timestamp} ({action})")
        
        return timestamp, action
    def afficher_historique(self):
        print(f"\n=== Historique de {self.__class__.__name__} {getattr(self, 'id', '')} ===")
        for i, (ts, action, etat) in enumerate(self.historique):
            print(f"{i+1}. [{ts.strftime('%Y-%m-%d %H:%M:%S')}] {action}")
            if i > 0:
                _, _, etat_precedent = self.historique[i-1]
                changements = self._detecter_changements(etat_precedent, etat)
                if changements:
                    print("   Changements:", ", ".join(changements))
    
    def _detecter_changements(self, etat_precedent: Dict, etat_actuel: Dict) -> List[str]:
        changements = []
        for attr in set(etat_precedent.keys()) | set(etat_actuel.keys()):
            if etat_precedent.get(attr) != etat_actuel.get(attr):
                changements.append(attr)
        return changements

class Journalisable:
    def __init__(self, niveau_log: str = "INFO"):
        self.niveau_log = niveau_log
        self.journal: List[tuple] = []
    
    def journaliser(self, message: str, niveau: str = None):
        if niveau is None:
            niveau = self.niveau_log
        
        timestamp = datetime.now()
        entree = (timestamp, niveau, message)
        self.journal.append(entree)
        print(f"[{niveau}] {timestamp.strftime('%Y-%m-%d %H:%M:%S')}: {message}")
    
    def exporter_journal(self, format: str = "text") -> str:
        if format == "text":
            return self._exporter_journal_text()
        elif format == "json":
            return self._exporter_journal_json()
        elif format == "csv":
            return self._exporter_journal_csv()
        else:
            raise ValueError(f"Format non supporté: {format}")
    
    def _exporter_journal_text(self) -> str:
        output = StringIO()
        output.write(f" Journal {self.__class__.__name__} \n")
        for ts, niveau, message in self.journal:
            output.write(f"[{niveau}] {ts.strftime('%Y-%m-%d %H:%M:%S')}: {message}\n")
        return output.getvalue()
    
    def _exporter_journal_json(self) -> str:
        data = {
            'classe': self.__class__.__name__,
            'entrees': [
                {
                    'timestamp': ts.isoformat(),
                    'niveau': niveau,
                    'message': message
                }
                for ts, niveau, message in self.journal
            ]
        }
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def _exporter_journal_csv(self) -> str:
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['timestamp', 'niveau', 'message'])
        for ts, niveau, message in self.journal:
            writer.writerow([ts.isoformat(), niveau, message])
        return output.getvalue()
class Horodatable:
    def __init__(self):
        self.date_creation = datetime.now()
        self.date_modification = self.date_creation
    
    def horodater(self, operation: str = None):
        ancienne_date = self.date_modification
        self.date_modification = datetime.now()
        
        if operation and hasattr(self, 'journaliser'):
            self.journaliser(
                f"Horodatage: {operation} - "
                f"De {ancienne_date.strftime('%H:%M:%S')} à "
                f"{self.date_modification.strftime('%H:%M:%S')}"
            )

class ExportableCSV(ABC):  
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        pass
    
    def to_csv(self) -> str:
        data = self.to_dict()
        output = StringIO()
        writer = csv.writer(output)
        
        writer.writerow(data.keys())
        writer.writerow(data.values())
        
        return output.getvalue()

class ExportableXML:
    def to_xml(self) -> str:
        root = ET.Element(self.__class__.__name__)
        
        for attr_name, attr_value in self.__dict__.items():
            if not attr_name.startswith('_'):
                elem = ET.SubElement(root, attr_name)
                if isinstance(attr_value, datetime):
                    elem.text = attr_value.isoformat()
                else:
                    elem.text = str(attr_value)
        if hasattr(self, 'historique') and self.historique:
            hist_elem = ET.SubElement(root, 'historique')
            for i, (ts, action, _) in enumerate(self.historique):
                entree = ET.SubElement(hist_elem, f'entree_{i}')
                ET.SubElement(entree, 'timestamp').text = ts.isoformat()
                ET.SubElement(entree, 'action').text = action
        
        return ET.tostring(root, encoding='unicode', method='xml')
class Contrat(Serializable, Historisable, Journalisable, Horodatable, ExportableCSV, ExportableXML):
    def __init__(self, id: int, description: str, client: str = "", montant: float = 0.0):
        Historisable.__init__(self)
        Journalisable.__init__(self, "INFO")
        Horodatable.__init__(self)
        
        self.id = id
        self.description = description
        self.client = client
        self.montant = montant
        self.statut = "Créé"
        self.enregistrer_etat("Création")
        self.journaliser(f"Contrat {id} créé pour {client}")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'description': self.description,
            'client': self.client,
            'montant': self.montant,
            'statut': self.statut,
            'date_creation': self.date_creation.isoformat(),
            'date_modification': self.date_modification.isoformat()
        }
    
    def modifier(self, nouvelle_desc: str = None, nouveau_montant: float = None, nouveau_client: str = None):
        self.journaliser(f"Début modification contrat {self.id}")
        self.enregistrer_etat("Avant modification")
        if nouvelle_desc:
            self.description = nouvelle_desc
        if nouveau_montant is not None:
            self.montant = nouveau_montant
        if nouveau_client:
            self.client = nouveau_client
        
        self.statut = "Modifié"
        self.horodater("Modification contrat")
        self.enregistrer_etat("Apres modification")
        
        self.journaliser(f"Fin modification contrat {self.id}")
    
    def valider(self):
        """Valide le contrat."""
        self.journaliser(f"Validation contrat {self.id}")
        self.statut = "Validé"
        self.enregistrer_etat("Validation")
        self.horodater("Validation contrat")

class Tache(Serializable, Historisable, Journalisable, Horodatable):
    def __init__(self, id: int, titre: str, assigne_a: str = ""):
        Historisable.__init__(self)
        Journalisable.__init__(self, "DEBUG")
        Horodatable.__init__(self)
        
        self.id = id
        self.titre = titre
        self.assigne_a = assigne_a
        self.terminee = False
        self.priorite = "Moyenne"
        
        self.enregistrer_etat("Creation")
        self.journaliser(f"Tâche {titre} créée")
    
    def completer(self):
        self.journaliser(f"Completion tache {self.id}")
        self.terminee = True
        self.enregistrer_etat("Complétion")
        self.horodater("Tâche terminee")
    
    def reassigner(self, nouvelle_personne: str):
        ancien = self.assigne_a
        self.assigne_a = nouvelle_personne
        self.enregistrer_etat(f"Reassignation: {ancien} -> {nouvelle_personne}")
        self.journaliser(f"Tâche réassignée de {ancien} à {nouvelle_personne}")

class Commande(Serializable, Historisable, Journalisable, ExportableCSV, ExportableXML):
    def __init__(self, id: int, produits: List[str], client: str):
        Historisable.__init__(self)
        Journalisable.__init__(self, "INFO")
        
        self.id = id
        self.produits = produits
        self.client = client
        self.date_commande = datetime.now()
        self.statut = "En attente"
        self.total = 0.0
        
        self.enregistrer_etat("Création")
        self.journaliser(f"Commande {id} créée pour {client}")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'produits': ', '.join(self.produits),
            'client': self.client,
            'date_commande': self.date_commande.isoformat(),
            'statut': self.statut,
            'total': self.total
        }
    
    def calculer_total(self, prix_produits: Dict[str, float]):
        self.total = sum(prix_produits.get(prod, 0.0) for prod in self.produits)
        self.enregistrer_etat(f"Calcul total: {self.total}")
        self.journaliser(f"Total commande {self.id}: {self.total}€")
    
    def expedier(self):
        self.statut = "Expédiée"
        self.enregistrer_etat("Expédition")
        self.journaliser(f"Commande {self.id} expédiée")
def main():
    
    print("1. Creation et manipulation d'un Contrat")
    print("-" * 40)
    contrat = Contrat(101, "Développement site web", "Entreprise ABC", 5000.0)
    contrat.modifier(nouveau_montant=5500.0, nouvelle_desc="Développement site e-commerce")
    contrat.valider()
    
    print("\n2. Export du contrat en différents formats")
    print("-" * 40)
    print("JSON (avec historique):")
    print(contrat.to_json(include_history=True)[:300] + "...")
    
    print("\nCSV:")
    print(contrat.to_csv())
    
    print("\nXML:")
    print(contrat.to_xml()[:200] + "...")
    
    print("\n3. Affichage de l'historique du contrat")
    print("-" * 40)
    contrat.afficher_historique()
    
    print("\n4. Création et manipulation d'une Tâche")
    print("-" * 40)
    tache = Tache(1, "Tests unitaires", "Alice")
    tache.reassigner("Bob")
    tache.completer()
    
    print("\n5. Export du journal de la tâche")
    print("-" * 40)
    print("Journal en CSV:")
    print(tache.exporter_journal("csv"))
    
    print("\n6. Création et manipulation d'une Commande")
    print("-" * 40)
    commande = Commande(1001, ["Laptop", "Souris", "Clavier"], "Client XYZ")
    commande.calculer_total({"Laptop": 1200.0, "Souris": 50.0, "Clavier": 80.0})
    commande.expedier()
    
    print("\n7. Test de restauration d'état")
    print("-" * 40)
    print(f"Avant restauration: {contrat.description}")
    contrat.restaurer_etat(0) 
    print(f"Après restauration: {contrat.description}")
    
    print("\n8. Test de sérialisation/désérialisation")
    print("-" * 40)
    json_contrat = contrat.to_json(include_history=False)
    print(f"JSON original: {json_contrat[:100]}...")
if __name__ == "__main__":
    main()