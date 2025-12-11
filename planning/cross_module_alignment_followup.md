# Allineamento cross-modulo — Encounter/MinMax e Hub/Persistenza

## Scopo
- Consolidare l'allineamento tra i moduli di bilanciamento (Encounter_Designer, minmax_builder) sulle convenzioni di naming export e sui gate QA prima del rilascio.
- Verificare con i referenti di Taverna_NPC, tavern_hub e Cartelle di servizio la coerenza delle policy di salvataggio/quarantena e dei marker di troncamento.
- Registrare eventuali blocchi/disallineamenti e, se assenti, chiudere le epic come "ready" e sbloccare i moduli dipendenti.

## 1) Sync tecnico Encounter_Designer ↔ minmax_builder
- Checklist usata: sezioni "Task" dei moduli (gate QA e naming export).
- Esito: **allineamento confermato**. I gate QA di Encounter_Designer bloccano l'export finché non passano pacing/loot/badge/PFS/balance e richiamano i comandi correttivi; minmax_builder esporta solo dopo `/qa_check` con naming condiviso `MinMax_<nome>.*` coerente con Encounter_Designer.
- Decisione: mantenere naming condiviso e CTA di export invariati; nessun backlog aperto.

## 2) Review Hub/Persistenza (Taverna_NPC, tavern_hub, Cartelle di servizio)
- Checklist usata: sezioni "Task" per storage/quarantine/troncamento.
- Esito: **coerenza confermata**.
  - Taverna_NPC: storage `taverna_saves/` con auto-name e quota, marker di troncamento `[…TRUNCATED ALLOW_MODULE_DUMP=false…]` e risposta standard “⚠️ Output parziale” quando il dump è disabilitato; export/report bloccati da Echo/QA gate con CTA di remediation.
  - tavern_hub.json: asset non testuale bloccato quando `ALLOW_MODULE_DUMP=false`, con metadati version/compatibility esposti.
  - Cartelle di servizio: directory di salvataggio `taverna_saves/` e cartelle di quarantena documentate con policy di sanificazione/isolamento e remediation per Echo/QA gate.
- Decisione: nessun disallineamento; mantenere policy di quarantena e troncamento come da indice moduli.

## 3) Stato finale e follow-up
- Blocco/disallineamenti: **nessuno rilevato** durante il sync.
- Azioni: segnare le epic correlate come **Ready** e sbloccare i moduli dipendenti nei board (builder/bilanciamento e hub/persistenza).
- Prossimi passi: nessun task aggiuntivo richiesto; monitorare nei prossimi smoke test che i marker di troncamento e i gate QA restino coerenti con le policy attuali.
