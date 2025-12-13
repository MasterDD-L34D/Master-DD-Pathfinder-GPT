# Checklist PR

Compila questa checklist prima di richiedere la review. Ogni elemento deve avere un'evidenza di test collegata alla storia che chiude.

> Nota: il workflow di validazione richiede che ogni controllo sia marcato come completato (`[x]`) **e** che nella tabella sottostante esista una riga con valori reali (senza placeholder). Usa l'esempio indicato per sostituire i campi.
> Se il workflow segnala errori, controlla di aver (1) sostituito gli esempi in corsivo con valori reali, (2) aggiunto una riga per **ognuno** dei controlli obbligatori e (3) spuntato le checkbox corrispondenti.

## Controlli obbligatori
- [ ] Test con dump disabilitato (marker/header)
- [ ] Naming export corretto
- [ ] CTA QA presenti
- [ ] 401/403 per endpoint protetti

## Evidenze di test per ciascun controllo
Compila una riga per ogni controllo sostituendo gli esempi in corsivo con i valori effettivi (es. `ABC-123`, `unit`, link a log o PR comment con marker/header).

| Controllo | Storia collegata | Tipo di test (unit/integration/manuale) | Evidenza (link/log, includere header/marker rilevante) |
| --- | --- | --- | --- |
| Test con dump disabilitato (marker/header) | _es. ABC-123_ | _es. integration_ | _link/log con marker/header_ |
| Naming export corretto | _es. ABC-123_ | _es. unit_ | _link/log_ |
| CTA QA presenti | _es. ABC-123_ | _es. manuale_ | _link/log_ |
| 401/403 per endpoint protetti | _es. ABC-123_ | _es. integration_ | _link/log_ |

## Note aggiuntive
- Dettagli aggiuntivi o rischi noti.
