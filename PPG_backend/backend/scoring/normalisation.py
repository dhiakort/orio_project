"""normalisation.py — Fonctions utilitaires pour normaliser les notes."""


def normaliser_note_sur_100(note: float | int | None) -> float | None:
    """Convertit une note sur 20 en note sur 100.

    Retourne None si la note ne peut pas être interprétée comme un nombre.
    """
    if note is None:
        return None
    try:
        valeur = float(note)
    except (TypeError, ValueError):
        return None

    valeur = max(0.0, min(valeur, 20.0))
    return round((valeur / 20.0) * 100.0, 2)


def normaliser_notes_dict(notes_dict: dict) -> dict:
    """Normalise toutes les valeurs d'un dictionnaire de notes sur 100."""
    if not isinstance(notes_dict, dict):
        return {}

    normalized = {}
    for cle, valeur in notes_dict.items():
        note_normalisee = normaliser_note_sur_100(valeur)
        if note_normalisee is not None:
            normalized[cle] = note_normalisee
    return normalized
