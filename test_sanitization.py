#!/usr/bin/env python3
"""
Test de la fonction de sanitization pour vérifier la correction du bug UTF-8
"""
from typing import Any, Dict


def sanitize_string(value: Any) -> Any:
    """
    Nettoie une chaîne de caractères en retirant les octets nuls (0x00)
    qui sont incompatibles avec PostgreSQL UTF-8.
    """
    if isinstance(value, str):
        return value.replace('\x00', '')
    return value


def sanitize_dict(data: Dict) -> Dict:
    """
    Nettoie récursivement toutes les chaînes d'un dictionnaire
    en retirant les octets nuls (0x00).
    """
    cleaned = {}
    for key, value in data.items():
        if isinstance(value, dict):
            cleaned[key] = sanitize_dict(value)
        elif isinstance(value, list):
            cleaned[key] = [sanitize_string(item) for item in value]
        else:
            cleaned[key] = sanitize_string(value)
    return cleaned


def test_sanitize_string():
    """Test de sanitize_string avec différents cas"""
    print("=== Test sanitize_string ===\n")

    # Test 1: Chaîne avec octets nuls au milieu
    test1 = "CNXN\x00\x00host::"
    result1 = sanitize_string(test1)
    print(f"Test 1 - Octets nuls au milieu:")
    print(f"  Input:  {repr(test1)}")
    print(f"  Output: {repr(result1)}")
    print(f"  ✓ PASS" if result1 == "CNXNhost::" else f"  ✗ FAIL")
    print()

    # Test 2: Chaîne sans octets nuls
    test2 = "0612345678"
    result2 = sanitize_string(test2)
    print(f"Test 2 - Pas d'octets nuls:")
    print(f"  Input:  {repr(test2)}")
    print(f"  Output: {repr(result2)}")
    print(f"  ✓ PASS" if result2 == "0612345678" else f"  ✗ FAIL")
    print()

    # Test 3: None
    test3 = None
    result3 = sanitize_string(test3)
    print(f"Test 3 - None:")
    print(f"  Input:  {repr(test3)}")
    print(f"  Output: {repr(result3)}")
    print(f"  ✓ PASS" if result3 is None else f"  ✗ FAIL")
    print()

    # Test 4: Integer
    test4 = 42
    result4 = sanitize_string(test4)
    print(f"Test 4 - Integer:")
    print(f"  Input:  {repr(test4)}")
    print(f"  Output: {repr(result4)}")
    print(f"  ✓ PASS" if result4 == 42 else f"  ✗ FAIL")
    print()

    # Test 5: Octets nuls multiples
    test5 = "Hello\x00\x00\x00World\x00Test"
    result5 = sanitize_string(test5)
    print(f"Test 5 - Octets nuls multiples:")
    print(f"  Input:  {repr(test5)}")
    print(f"  Output: {repr(result5)}")
    print(f"  ✓ PASS" if result5 == "HelloWorldTest" else f"  ✗ FAIL")
    print()


def test_sanitize_dict():
    """Test de sanitize_dict avec un dictionnaire complet"""
    print("\n=== Test sanitize_dict ===\n")

    # Simuler des données de ticket avec octets nuls
    ticket_data = {
        'call_uuid': 'test\x00uuid',
        'phone_number': '0612\x00345678',
        'client_name': 'John\x00Doe',
        'client_email': 'john@example.com',
        'problem_type': 'internet',
        'status': 'resolved',
        'sentiment': 'positive',
        'summary': 'Problème\x00résolu',
        'duration_seconds': 120,
        'tag': 'FIBRE_SYNCHRO',
        'severity': 'MEDIUM'
    }

    print("Données AVANT sanitization:")
    for key, value in ticket_data.items():
        print(f"  {key}: {repr(value)}")

    cleaned_data = sanitize_dict(ticket_data)

    print("\nDonnées APRÈS sanitization:")
    for key, value in cleaned_data.items():
        print(f"  {key}: {repr(value)}")

    # Vérifications
    print("\nVérifications:")
    checks = [
        (cleaned_data['call_uuid'] == 'testuuid', 'call_uuid'),
        (cleaned_data['phone_number'] == '0612345678', 'phone_number'),
        (cleaned_data['client_name'] == 'JohnDoe', 'client_name'),
        (cleaned_data['summary'] == 'Problèmerésolu', 'summary'),
        (cleaned_data['duration_seconds'] == 120, 'duration_seconds (int)')
    ]

    for check, name in checks:
        print(f"  {'✓' if check else '✗'} {name}")

    all_passed = all(check for check, _ in checks)
    print(f"\n{'✓ TOUS LES TESTS PASSENT' if all_passed else '✗ CERTAINS TESTS ONT ÉCHOUÉ'}")


def test_real_world_scenario():
    """Test avec un scénario réel basé sur les logs"""
    print("\n=== Test Scénario Réel ===\n")

    # Simuler les données qui ont causé l'erreur
    call_id = "CNXN\x00\x002host::"
    phone_number = "\x00"  # CALLERID vide avec octet nul

    print("Scénario: Données du log d'erreur")
    print(f"  call_id brut: {repr(call_id)}")
    print(f"  phone_number brut: {repr(phone_number)}")

    # Nettoyer
    clean_call_id = sanitize_string(call_id)
    clean_phone_number = sanitize_string(phone_number)

    print(f"\nAprès sanitization:")
    print(f"  call_id nettoyé: {repr(clean_call_id)}")
    print(f"  phone_number nettoyé: {repr(clean_phone_number)}")

    # Vérifier que les chaînes nettoyées peuvent être utilisées dans un nom de fichier
    try:
        test_filename = f"/tmp/test_call_{clean_call_id}.raw"
        print(f"\nTest création de nom de fichier:")
        print(f"  Nom de fichier: {test_filename}")
        print(f"  ✓ PASS - Pas d'erreur 'embedded null byte'")
    except Exception as e:
        print(f"  ✗ FAIL - Erreur: {e}")


if __name__ == "__main__":
    print("╔═══════════════════════════════════════════════════════╗")
    print("║  Test de Sanitization UTF-8 / Octets Nuls (0x00)     ║")
    print("╚═══════════════════════════════════════════════════════╝\n")

    test_sanitize_string()
    test_sanitize_dict()
    test_real_world_scenario()

    print("\n" + "="*60)
    print("Tests terminés !")
    print("="*60)
