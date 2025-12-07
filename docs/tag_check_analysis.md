# Audit coerenza tag, checklist e disclaimer (aggiornamento)

## Sintesi
- I tre moduli ora condividono l'ordine di giurisdizione ✅ RAW → 📘 RAI → 🧭 PFS → ❗ HR e riprendono il gate PFS/HR dal profilo Ruling Expert.
- MinMax Builder espone badge di provenienza (RAW/RAI/PFS/HR), banner META con blocco HR in PFS e checklist QA minima.
- Encounter Designer normalizza i ruling_badge per ogni nemico, applica il gate HR se PFS è attivo e blocca l'export se i badge o i gate QA falliscono.

## Ruling Expert (baseline dei tag)
- Tag obbligatori definiti: ✅ RAW, 📘 RAI, 🧭 PFS, ❗ HR.【F:src/modules/ruling_expert.txt†L13-L16】
- Gerarchia di fonte e override PFS esplicitati, con hard-fail se mancano fonti (require_citation_strict).【F:src/modules/ruling_expert.txt†L24-L28】【F:src/modules/ruling_expert.txt†L40-L66】

## MinMax Builder
- Ruling policy allineata al baseline con PFS gate che blocca HR/META e obbligo di citazioni Paizo.【F:src/modules/minmax_builder.txt†L41-L66】
- Banner META che avvisa quando i suggerimenti non sono RAW e ricorda il blocco HR/META in PFS.【F:src/modules/minmax_builder.txt†L61-L66】
- Stato/benchmark includono `ruling_badge` per tracciare l'origine del ruling nei report e nei benchmark.【F:src/modules/minmax_builder.txt†L117-L234】【F:src/modules/minmax_builder.txt†L1251-L1292】
- QA/minimo checklist con voci `sources_ok`, `pfs_ok`, `hr_flagged`; `export_build` e `export_vtt` condividono i gate QA prima di esportare.【F:src/modules/minmax_builder.txt†L1010-L1028】【F:src/modules/minmax_builder.txt†L1040-L1064】【F:src/modules/minmax_builder.txt†L1785-L1807】

### Esempio aggiornato (bozza)
```
[QA] Benchmark Full — Badge Ruling: ✅ RAW-Summarized • PFS: ON
| DPR 1–3 | OK | +12% | META: 🧭 |
Se PFS è attivo, HR/META restano fuori export; per ruling dubbi usa Ruling Expert.
```

## Encounter Designer
- Ruling policy condivisa con ordine RAW→RAI→PFS→HR, gate HR su PFS attivo e disclaimer offline Paizo/AoN.【F:src/modules/Encounter_Designer.txt†L30-L38】
- Ogni nemico porta `ruling_badge`, normalizzato con fallback a PFS se HR è proibito; importazione auto rispetta PFS.【F:src/modules/Encounter_Designer.txt†L92-L294】【F:src/modules/Encounter_Designer.txt†L660-L688】
- QA valida presenza badge e gate PFS prima dell'export; export bloccato se QA non è `OK`.【F:src/modules/Encounter_Designer.txt†L379-L418】

### Esempio aggiornato (bozza)
```
[QA] Encounter "Emboscata" — badge OK • PFS gate OK
Nemici: Brute CR 4 (ruling_badge: 🧭 PFS), Artillery CR 3 (ruling_badge: ✅ RAW-Summarized)
Export VTT consentito solo dopo /validate_encounter.
```
