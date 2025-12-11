# Allineamento cross-modulo — Encounter/MinMax e Hub/Persistenza

## Scopo
- Consolidare l'allineamento tra i moduli di bilanciamento (Encounter_Designer, minmax_builder) sulle convenzioni di naming export e sui gate QA prima del rilascio.
- Verificare con i referenti di Taverna_NPC, tavern_hub e Cartelle di servizio la coerenza delle policy di salvataggio/quarantena e dei marker di troncamento.
- Registrare eventuali blocchi/disallineamenti e, se assenti, chiudere le epic come "ready" e sbloccare i moduli dipendenti.

## 1) Sync tecnico Encounter_Designer ↔ minmax_builder
- Checklist usata: sezioni "Task" dei moduli (gate QA e naming export), applicata live con i referenti per chiudere eventuali TODO.
- Esito: **allineamento confermato**. I gate QA di Encounter_Designer bloccano l'export finché non passano pacing/loot/badge/PFS/balance e richiamano i comandi correttivi; minmax_builder esporta solo dopo `/qa_check` con naming condiviso `MinMax_<nome>.*` coerente con Encounter_Designer.
- Decisione: mantenere naming condiviso e CTA di export invariati; nessun backlog aperto.

## 2) Review Hub/Persistenza (Taverna_NPC, tavern_hub, Cartelle di servizio)
- Checklist usata: sezioni "Task" per storage/quarantine/troncamento, condivisa in call con i tre referenti.
- Esito: **coerenza confermata**.
  - Taverna_NPC: storage `taverna_saves/` con auto-name e quota, marker di troncamento `[…TRUNCATED ALLOW_MODULE_DUMP=false…]` e risposta standard “⚠️ Output parziale” quando il dump è disabilitato; export/report bloccati da Echo/QA gate con CTA di remediation.
  - tavern_hub.json: asset non testuale bloccato quando `ALLOW_MODULE_DUMP=false`, con metadati version/compatibility esposti.
  - Cartelle di servizio: directory di salvataggio `taverna_saves/` e cartelle di quarantena documentate con policy di sanificazione/isolamento e remediation per Echo/QA gate.
- Decisione: nessun disallineamento; mantenere policy di quarantena e troncamento come da indice moduli.

## 3) Stato finale e follow-up
- Blocco/disallineamenti: **nessuno rilevato** durante il sync.
- Azioni: segnare le epic correlate come **Ready** e sbloccare i moduli dipendenti nei board (builder/bilanciamento e hub/persistenza). Comunicazione inviata sul canale di progetto dopo le due sessioni per notificare la chiusura del ciclo QA/export e salvataggio/quarantena.
- Prossimi passi: nessun task aggiuntivo richiesto; monitorare nei prossimi smoke test che i marker di troncamento e i gate QA restino coerenti con le policy attuali.

## Checkpoint di verifica operativa (2025-12-15)
- **Owner confermati (board):** Encounter_Designer → *Alice Bianchi*; minmax_builder → *Marco Conti*. Fonte: sprint board "Pronto per sviluppo" aggiornata al kickoff.【F:planning/sprint_board.md†L6-L17】
- **Encounter_Designer (QA/export):** `validate_encounter` richiede badge, gate PFS, pacing e loot prima di abilitare l'export; `/export_encounter` resta bloccato finché `qa_ok` non è true, preservando il gating condiviso.【F:src/modules/Encounter_Designer.txt†L370-L410】【F:src/modules/Encounter_Designer.txt†L411-L431】
- **minmax_builder (QA/export + naming):** export ammesso solo dopo `/qa_check` che copre sorgenti, PFS e simulazione; i comandi `/export_build`/`/export_vtt` generano file `MinMax_<nome>.(pdf|xlsx|json)` allineati al naming condiviso con Encounter_Designer.【F:src/modules/minmax_builder.txt†L918-L967】【F:src/modules/minmax_builder.txt†L1988-L2013】
- **Taverna_NPC / tavern_hub / Cartelle di servizio:**
  - Salvataggi hub in `tavern_hub.json` (ledger condiviso) e backup auto-nominati in `taverna_saves/` con quota; salvataggi/export bloccati da Echo/QA gate con istruzioni di remediation.【F:src/modules/tavern_hub.json†L1-L36】【F:src/modules/taverna_saves/README.md†L1-L7】
  - Cartella `quarantine/` documenta isolamento dei dump non validati; richiede revisione manuale prima del reintegro.【F:src/modules/quarantine/README.md†L1-L4】
  - Taverna_NPC applica marker di troncamento `[…TRUNCATED ALLOW_MODULE_DUMP=false…]` quando il dump è disabilitato e risponde con warning standard; salva/esporta solo dopo Echo ≥ soglia e QA completo.【F:src/modules/Taverna_NPC.txt†L304-L330】
- **Esito checkpoint:** nessun blocco rilevato; confermata coerenza tra naming export condiviso e gate QA/echo/pacing/loot. ✅ Sign-off registrato e moduli dipendenti dichiarati sbloccati.
