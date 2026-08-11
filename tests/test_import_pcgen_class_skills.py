"""Test per tools/import_pcgen_class_skills.py -- le abilita' di classe (CSKILL).

Fixture LST inline (MAI rete), forma reale ricostruita sui file veri al commit
PCGen 70057897.

Il caso che questo file esiste per fissare: nelle abilita' che concedono le
abilita' di classe il NOME VISUALIZZATO e' letteralmente "Class Skills" per
tutte, e la classe sta nella `KEY:`. Raggruppare per nome da' UNA voce per
l'intero gioco -- misurato mentre si scriveva l'estrattore.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_la_classe_viene_dalla_KEY_non_dal_nome_visualizzato():
    from tools import import_pcgen_class_skills as pcs

    # Riga reale (apg_abilities_class.lst): il nome e' "Class Skills", la
    # classe sta nella KEY. Se l'estrattore guardasse il nome, tutte le classi
    # collasserebbero su una voce sola chiamata "Class Skills".
    lst = (
        "Class Skills\tKEY:Alchemist ~ Class Skills\tCATEGORY:Internal\t"
        "CSKILL:Appraise|TYPE=Craft|Disable Device\n"
    )
    voci = pcs.from_abilities_file(lst, "APG")

    assert len(voci) == 1
    assert voci[0]["class"] == "Alchemist", "la classe viene dalla KEY"
    assert voci[0]["skills"] == ["Appraise", "TYPE=Craft", "Disable Device"]
