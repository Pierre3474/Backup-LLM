#!/usr/bin/env python3
"""
Test du chargement des keywords STT depuis stt_keywords.yaml
"""
import yaml
from pathlib import Path


def test_load_keywords():
    """Test de chargement et validation des keywords"""
    print("═" * 60)
    print("  Test de chargement des STT Keywords")
    print("═" * 60)
    print()

    keywords_file = Path(__file__).parent / "stt_keywords.yaml"

    # Vérifier existence du fichier
    if not keywords_file.exists():
        print(f"❌ ERREUR : {keywords_file} n'existe pas")
        return False

    print(f"✓ Fichier trouvé : {keywords_file}")
    print()

    # Charger le fichier YAML
    try:
        with open(keywords_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ ERREUR de lecture YAML : {e}")
        return False

    print("✓ Fichier YAML valide")
    print()

    # Analyser les catégories
    print("📊 Analyse des catégories :")
    print("-" * 60)

    total_keywords = 0
    categories_info = {}

    for category, keywords_list in data.items():
        if isinstance(keywords_list, list):
            count = len(keywords_list)
            total_keywords += count
            categories_info[category] = count
            print(f"  • {category:25s} : {count:3d} keywords")

    print("-" * 60)
    print(f"  TOTAL                      : {total_keywords:3d} keywords")
    print()

    # Vérifications de sécurité
    print("🔍 Vérifications de sécurité :")
    print("-" * 60)

    # Check 1: Limite de keywords
    if total_keywords > 200:
        print(f"  ⚠️  WARNING : {total_keywords} keywords > 200 (limite recommandée)")
        print("     → Risque de ralentissement et faux positifs")
    elif total_keywords > 150:
        print(f"  ⚠️  INFO : {total_keywords} keywords > 150")
        print("     → Proche de la limite, surveiller les performances")
    else:
        print(f"  ✓ {total_keywords} keywords < 150 (bon niveau)")

    # Check 2: Validation du format
    print()
    invalid_keywords = []
    for category, keywords_list in data.items():
        if isinstance(keywords_list, list):
            for keyword in keywords_list:
                if not isinstance(keyword, str):
                    invalid_keywords.append((category, keyword))
                elif ':' not in keyword:
                    invalid_keywords.append((category, keyword))
                else:
                    # Vérifier le format "mot:intensité"
                    parts = keyword.rsplit(':', 1)
                    if len(parts) != 2:
                        invalid_keywords.append((category, keyword))
                    else:
                        try:
                            intensity = int(parts[1])
                            if intensity < 0 or intensity > 4:
                                invalid_keywords.append((category, f"{keyword} (intensité hors limites 0-4)"))
                        except ValueError:
                            invalid_keywords.append((category, f"{keyword} (intensité non numérique)"))

    if invalid_keywords:
        print(f"  ❌ {len(invalid_keywords)} keyword(s) invalide(s) :")
        for cat, kw in invalid_keywords[:5]:  # Afficher max 5 erreurs
            print(f"     → {cat} : {kw}")
        if len(invalid_keywords) > 5:
            print(f"     ... et {len(invalid_keywords) - 5} autres")
        return False
    else:
        print("  ✓ Tous les keywords ont un format valide (mot:intensité)")

    # Check 3: Distribution des intensités
    print()
    intensities = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
    for category, keywords_list in data.items():
        if isinstance(keywords_list, list):
            for keyword in keywords_list:
                if isinstance(keyword, str) and ':' in keyword:
                    try:
                        intensity = int(keyword.rsplit(':', 1)[1])
                        intensities[intensity] = intensities.get(intensity, 0) + 1
                    except:
                        pass

    print("  Distribution des intensités de boost :")
    for level in [4, 3, 2, 1, 0]:
        count = intensities.get(level, 0)
        bar = '█' * (count // 5)  # Barre visuelle
        status = ""
        if level == 4 and count > 0:
            status = " ⚠️  (trop agressif, déconseillé)"
        elif level == 0 and count > 0:
            status = " ⚠️  (inutile)"
        print(f"    Niveau {level} : {count:3d} {bar}{status}")

    if intensities.get(4, 0) > 0:
        print()
        print("  ⚠️  WARNING : Intensité 4 détectée (trop agressive)")
        print("     → Recommandation : Utiliser intensité 3 pour noms propres")

    # Exemples de keywords
    print()
    print("📝 Exemples de keywords (premiers de chaque catégorie) :")
    print("-" * 60)
    for category, keywords_list in data.items():
        if isinstance(keywords_list, list) and keywords_list:
            examples = keywords_list[:3]  # 3 premiers
            print(f"  {category:25s} : {', '.join(examples)}")

    print()
    print("═" * 60)
    print("✅ Test réussi ! Les keywords sont prêts à être utilisés.")
    print("═" * 60)
    print()
    print(f"💡 Pour activer : Redémarrer le serveur voicebot")
    print(f"📊 Charge actuelle : {total_keywords}/200 keywords")
    print()

    return True


if __name__ == "__main__":
    success = test_load_keywords()
    exit(0 if success else 1)
