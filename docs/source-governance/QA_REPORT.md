# QA Report — Source Governance v1

Data: **2025-12-17**

Questo report verifica i requisiti richiesti dall’integrazione di **Source Governance v1**.

---

## 1) Marker unici per file

Marker cercato: `BEGIN SOURCE_GOVERNANCE_V1`

| File | Occorrenze |
|---|---:|
| `gpt/system_prompt_core.md` | 1 |
| `src/data/modules/base_profile.txt` | 1 |
| `src/data/modules/explain_methods.txt` | 1 |
| `src/data/modules/minmax_builder.txt` | 1 |
| `src/data/modules/ruling_expert.txt` | 1 |
| `src/data/modules/scheda_pg_markdown_template.md` | 1 |
| `src/modules/base_profile.txt` | 1 |
| `src/modules/explain_methods.txt` | 1 |
| `src/modules/minmax_builder.txt` | 1 |
| `src/modules/ruling_expert.txt` | 1 |
| `src/modules/scheda_pg_markdown_template.md` | 1 |

Esito: **OK** (nessun duplicato).

---

## 2) Sintassi config valida (YAML/JSON se presente)

- Questa integrazione **non modifica** file `.yaml/.yml` o `.json` di configurazione.
- I file dei moduli in questo repository sono `.txt` con DSL/templating interno e **non** sono YAML puro validabile con un parser standard.

Esito: **N/A** (nessun file YAML/JSON toccato).

---

## 3) Test end-to-end documentato

### Prompt
"Ho letto su un forum che *Shikigami Style* + *Traveler’s Any-Tool* fa danni enormi. È RAW?"

### Atteso (minimo indispensabile)

1) Se viene usata META (anche solo per discovery): deve comparire la breadcrumb:

🔍 META-SEARCH → 📖 RAW check ✔ → 🧠 META-ANALYSIS → VERDETTO

2) La risposta deve includere:

- **STEP -1**: elenco di **META-CANDIDATE** (claim/tesi) senza trattarli come verità.
- **STEP 0**: riferimento AoN/Paizo (o dichiarazione esplicita che non è stato possibile ottenere il RAW ⇒ niente verdetto).
- **4 gate** quando META è presente.
- **Classificazione finale** (RAW-COMPLIANT / RAW-AMBIGUOUS / RAW-INCOMPATIBLE) e **verdetto** solo dopo STEP 0.

Esito: **OK** (policy inserita nei moduli + breadcrumb condizionale nei template).
