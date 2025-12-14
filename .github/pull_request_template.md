# Checklist PR

Compila questa checklist prima di richiedere la review. Ogni elemento deve avere un'evidenza di test collegata alla storia che chiude.

> Nota: il workflow di validazione richiede che ogni controllo sia marcato come completato (`[x]`) **e** che nella tabella sottostante esista una riga con valori reali (senza placeholder). I placeholder tra `< >` fanno fallire il check finché non vengono sostituiti.
> Se il workflow segnala errori, controlla di aver (1) sostituito tutti i placeholder `<...>` con valori reali, (2) aggiunto una riga per **ognuno** dei controlli obbligatori e (3) spuntato le checkbox corrispondenti.

### Come superare il controllo
1. Esegui i test richiesti e annota ID storia, tipo di test e link/log dell'evidenza.
2. Sostituisci i placeholder `<...>` nella tabella con i valori reali (nessun `<` o `>` deve rimanere).
3. Spunta `[x]` solo dopo aver inserito l'evidenza nella riga corrispondente.

## Controlli obbligatori
- [ ] Test con dump disabilitato (marker/header)
- [ ] Naming export corretto
- [ ] CTA QA presenti
- [ ] 401/403 per endpoint protetti

## Evidenze di test per ciascun controllo
Compila una riga per ogni controllo sostituendo i placeholder con i valori effettivi (es. `ABC-123`, `unit`, link a log o PR comment con marker/header).

Le righe tra i marker `<!-- AUTO-QA-START -->` e `<!-- AUTO-QA-END -->` possono essere sovrascritte automaticamente dal workflow di QA.

<!-- AUTO-QA-START -->
| Controllo | Storia collegata | Tipo di test (unit/integration/manuale) | Evidenza (link/log, includere header/marker rilevante) |
| --- | --- | --- | --- |
| Test con dump disabilitato (marker/header) | <ID-storia> | <unit/integration/manuale> | <link/log con marker/header> |
| Naming export corretto | <ID-storia> | <unit/integration/manuale> | <link/log> |
| CTA QA presenti | <ID-storia> | <unit/integration/manuale> | <link/log> |
| 401/403 per endpoint protetti | <ID-storia> | <unit/integration/manuale> | <link/log> |
<!-- AUTO-QA-END -->

> Esempio di evidenze (le checkbox vanno spuntate nella sezione precedente):
>
> | Controllo | Storia collegata | Tipo di test (unit/integration/manuale) | Evidenza (link/log, includere header/marker rilevante) |
> | --- | --- | --- | --- |
> | Test con dump disabilitato (marker/header) | ABC-123 | integration | https://example.com/logs/123#marker |
> | Naming export corretto | ABC-123 | unit | https://example.com/logs/456 |
> | CTA QA presenti | ABC-123 | manuale | https://example.com/logs/789 |
> | 401/403 per endpoint protetti | ABC-123 | integration | https://example.com/logs/987 |

## Note aggiuntive
- Dettagli aggiuntivi o rischi noti.
