# Import talenti (sotto-cataloghi per classe) da AoN (2026-07-26)

- Talenti totali: 806
- OGL (talents.json): 806
- PI -> talents_local.json: 0
- Duplicati (pool, name) scartati: 0
- Entry senza testo: 0

## Conteggi per pool (OGL)

- **advanced rogue talent**: 49
- **deed**: 23
- **discovery**: 169
- **grand discovery**: 7
- **grand hex**: 13
- **hex**: 60
- **ki power**: 31
- **major hex**: 31
- **mercy**: 26
- **rage power**: 234
- **rogue talent**: 163

## Anomalie

- (nessuna)

## Fix post-review (2026-07-26, seconda passata)

- 9 ki power troncati ai tag `<i>` inline (spell citate nel testo): il walk ora usa `next_elements` (find_all_next yields solo Tag, quindi i NavigableString non venivano mai accumulati). Discriminante entry invariato: `<i>` con next_sibling che inizia per ':'.
- 3 rogue talent (Black Market Connections, Rumormonger, Quick Disguise) con `<table class="inner">` appiattita in coda alla description: tabelle annidate escluse dal testo (assenza onesta — dato tabellare via reference_url).
- Cleanup punteggiatura del join per frammenti ('dimension door .' -> 'dimension door.') su entrambi i parser.
- Scan finale: 0 description con finale non '.', '!', '?', '”', '"', ')'.

## Nomi PI spostati in locale

