Directory di output dove il modulo Taverna salva i backup JSON (NPC, quest, voci di taverna, ledger di gioco).
I file vengono creati automaticamente dal modulo con naming timestamped e con un limite massimo di elementi:
non è necessario creare manualmente i file per il database, a meno di fixture di test o import manuali.
Se salvataggi o export vengono bloccati (Echo gate <8.5 o QA CHECK incompleto), ripeti /grade o /refine_npc finché il punteggio non supera la soglia e lancia /self_check (QA CHECK/repair) per completare Canvas+Ledger prima di riprovare.
