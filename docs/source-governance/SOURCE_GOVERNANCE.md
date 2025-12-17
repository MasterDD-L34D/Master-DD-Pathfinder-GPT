# Sezione “Fonti” — Governance, Ruoli e Validazione (Source Governance v1)

Questa sezione definisce **come vengono scoperte, consultate, valutate e validate** le fonti utilizzate per Pathfinder 1E.  
L’obiettivo è garantire **correttezza RAW**, **trasparenza epistemica** e **utilità pratica**, distinguendo chiaramente tra:

- **autorità normativa** (cosa è vero: RAW/RAI/PFS)
- **autorità analitica** (come si gioca: pattern, ottimizzazione, prassi)

---

## 1. Principi Fondanti

1) **Separazione dei ruoli**
- *Normativo* ≠ *Analitico*.
- Le fonti ufficiali determinano **cosa è vero** (RAW/RAI/PFS).
- Le fonti community determinano **come si gioca** (pattern/ottimizzazione), ma **non fanno legge**.

2) **Consultazione primaria ≠ verità**
- Una fonte può essere consultata come **primaria di analisi** senza essere **normativa**.

3) **Gate di validazione obbligatorio**
- Nessuna informazione non ufficiale è utilizzabile senza **verifica di allineamento RAW**.

4) **Trasparenza**
- Ogni informazione indica **origine**, **ruolo della fonte** e **stato di validazione**.

---

## 2. Classificazione delle Fonti

### 2.1 Fonti Normative (Autorità di Verità)
**Ruolo:** stabilire le regole ufficiali.

- **Archives of Nethys (AoN)** — testo RAW ufficiale Paizo, aggiornato con errata.
- **Paizo.com** — manuali, FAQ, errata, post degli sviluppatori.
- **Pathfinder Society (PFS)** — override e limitazioni per Organized Play.

**Tag:** `RAW`, `RAI`, `PFS`

> In caso di conflitto: **Errata/FAQ > RAW > PFS (se attivo)**.

---

### 2.2 Fonti Analitiche Primarie (Community / META)
**Ruolo:** analisi, pattern di gioco, ottimizzazione, prassi diffuse.

Esempi:
- guide in **PDF/DOC/Google Docs**
- blog tecnici
- forum storici
- discussioni strutturate

**Importante:** queste fonti sono **primarie per l’analisi**, **mai normative**.

**Tag:** `META-ANALYSIS`

---

### 2.3 Fonti Secondarie Enciclopediche
**Ruolo:** supporto informativo (lore, collegamenti, cronologie).

- Pathfinder Wiki

**Limitazioni:** non determinano regole.

**Tag:** `SECONDARY`

---

## 2.4 Strumenti META — Ricerca Attiva di Guide Non Ufficiali
**Ruolo:** individuare e raccogliere materiale analitico (guide, handbook, build) prodotto dalla community PF1e.

Questi strumenti **non sono fonti di verità**, ma **strumenti di scoperta** di fonti META da sottoporre al processo di validazione.

Tipologie di ricerca ammesse:
- motori di ricerca generalisti (query avanzate)
- ricerca mirata su domini noti della community
- repository pubblici (PDF/DOC/Google Docs/GitHub)

**Tag:** `META-SEARCH`

---

## 2.5 Query Standard META (per tema)

Le seguenti query sono **pattern standardizzati** per la scoperta di materiale META.  
Ogni risultato è automaticamente classificato come `META-CANDIDATE`.

### Classi
- `"pathfinder 1e" <classe> guide filetype:pdf`
- `"pathfinder 1e" <classe> handbook`
- `"pathfinder 1e" <classe> optimization`
- `site:docs.google.com "pathfinder 1e" <classe>`

### Razze
- `"pathfinder 1e" <razza> racial guide`
- `"pathfinder 1e" <razza> build`
- `"pathfinder 1e" <razza> optimization`

### Incantesimi
- `"pathfinder 1e" "<spell name>" guide`
- `"pathfinder 1e" "<spell name>" optimization`
- `"pathfinder 1e" "<spell name>" interaction`

### Oggetti
- `"pathfinder 1e" "<item name>" guide`
- `"pathfinder 1e" "<item name>" optimization`
- `"pathfinder 1e" "<item name>" combo`

---

## 2.5.1 Query Preset Pronte all’Uso (Build Archetype)

Queste query sono **preset tematici** per casi ricorrenti. Servono a velocizzare lo scouting META.

### Full Caster (controllo / save-or-lose)
- `"pathfinder 1e" full caster optimization`
- `wizard sorcerer cleric druid guide "pathfinder 1e"`
- `site:docs.google.com "pathfinder 1e" caster handbook`

### Martial DPR
- `"pathfinder 1e" martial dpr build`
- `fighter slayer barbarian optimization "pathfinder 1e"`
- `"pathfinder 1e" power attack dpr guide`

### Gish / Spellblade
- `"pathfinder 1e" gish build`
- `magus eldritch knight optimization "pathfinder 1e"`

### Skill Monkey / Trickster
- `"pathfinder 1e" skill monkey build`
- `rogue bard investigator optimization "pathfinder 1e"`

### Debuffer / Feint / Dirty Tricks
- `"pathfinder 1e" feint build`
- `"pathfinder 1e" debuff optimization`

---

## 2.6 Domini Seed Affidabili (META)

Questi domini sono considerati **seed di scoperta affidabili** per materiale META.  
La presenza su questi domini **non implica validità RAW**.

### Blog e Guide Storiche
- `zenithgames.blogspot.com`
- `treantmonk.wordpress.com`

### Forum Tecnici
- `forums.giantitp.com`
- `paizo.com/community/forums` (sezioni non ufficiali/community)

### Repository Documentali
- `docs.google.com`
- `github.com` (repository di guide PF1e)

### Community Aggregate
- `reddit.com/r/Pathfinder_RPG`

**Nota:** i domini seed servono **solo a restringere il campo di ricerca**, non a saltare i gate di validazione.

---

## 3. Processo di Validazione delle Fonti Analitiche (META)

### STEP -1 — Ricerca META (scoperta guidata)
Questo step serve a **trovare** fonti META, non a validarle.

- uso di query strutturate (vedi §2.5–2.5.1) e domini seed (vedi §2.6)
- nessuna conclusione viene tratta in questa fase
- tutti i risultati sono considerati **non validati**

**Output dello step:** elenco di fonti candidate `META-CANDIDATE`.

---

### STEP 0 — Ancoraggio RAW (obbligatorio, preliminare)
Prima di qualsiasi analisi, inferenza o valutazione META:

- devono essere recuperati e letti **i testi ufficiali completi** di:
  - talenti
  - capacità razziali
  - archetipi
  - incantesimi
  - oggetti/regole coinvolte
- fonti ammesse: **Archives of Nethys / Paizo**
- **è vietato** dedurre il funzionamento “per somiglianza” o memoria

> Se il testo RAW non è disponibile o non è stato consultato, l’analisi **non può procedere**.

---

Dopo STEP -1 e STEP 0, ogni informazione proveniente da fonti META segue **obbligatoriamente** questo flusso:

1) **Consultazione**
- la fonte viene letta come **primaria di analisi**
- si esplicita la **tesi** (“cosa sostiene la build/guida”)

2) **Valutazione dell’Autore**
- identità riconoscibile?
- storico nella community PF1e?
- coerenza terminologica Paizo?
- red flags: “GM fiat”, house rule implicite, definizioni non Paizo

3) **Verifica di Allineamento RAW**
- talenti/archetipi/incantesimi verificati su AoN/Paizo
- prerequisiti e action economy verificati
- stacking e interazioni controllate
- nessuna house rule implicita

4) **Classificazione Finale**
- `RAW-COMPLIANT` — pienamente legale e coerente col testo
- `RAW-AMBIGUOUS` — dipende da interpretazione (indicare il punto esatto)
- `RAW-INCOMPATIBLE` — contraddice RAW o richiede HR

5) **Dichiarazione Trasparente**
- il risultato della validazione viene **esplicitato** (vedi §13–14)

---

## 4. Regole di Utilizzo

- Le fonti **META**:
  - ✅ possono ispirare build e strategie (analisi)
  - ❌ non possono sostituire AoN/Paizo (normativa)

- Con **PFS ON**:
  - tutti i contenuti META vengono **filtrati**
  - le opzioni non legali sono marcate come `NON PFS`

- In assenza di conferma RAW (STEP 0 non completabile):
  - l’informazione **non viene presentata come vera**
  - va dichiarato il limite e proposta ricerca/estrazione testo RAW

---

## 5. Sistema di Tag

| Tag | Significato |
|---|---|
| `RAW` | Regola ufficiale Paizo |
| `RAI` | Intenzione sviluppatori (FAQ/errata/dev) |
| `PFS` | Organized Play |
| `META-SEARCH` | Ricerca/discovery di fonti META |
| `META-CANDIDATE` | Fonte META trovata, non validata |
| `META-ANALYSIS` | Analisi community (primaria, non normativa) |
| `RAW-COMPLIANT` | Verificata RAW |
| `RAW-AMBIGUOUS` | Interpretazione necessaria (punto indicato) |
| `RAW-INCOMPATIBLE` | Contraddice RAW / richiede HR |
| `HR` | House Rule esplicita |

---

## 6. Sintesi Operativa

- **AoN/Paizo** = verità normativa.
- **META** = verità analitica *condizionata*.
- **Nessuna scorciatoia:** ogni informazione passa da **STEP 0 (RAW)**.
- **Ogni risposta è tracciabile** (breadcrumb + verdict).

---

## 7. Checklist Operativa META → RAW (uso pratico)

Usare questa checklist **ogni volta** che una fonte META (DOC/PDF/blog/forum) viene consultata.

**A. Identificazione**
- [ ] tipo documento: guida / handbook / build / analisi
- [ ] autore identificabile (nome o alias storico)
- [ ] periodo PF1e (≈ 2009–2018)

**B. Valutazione autore**
- [ ] presenza storica nella community PF1e
- [ ] linguaggio coerente con termini Paizo
- [ ] nessun riferimento a “GM fiat” implicito

**C. Verifica RAW (obbligatoria)**
- [ ] testi completi verificati su AoN/Paizo (STEP 0)
- [ ] prerequisiti verificati
- [ ] tipi di bonus corretti (stacking)
- [ ] action economy corretta
- [ ] nessuna house rule implicita
- [ ] se PFS ON: legalità verificata o marcata `NON PFS`

**D. Classificazione finale**
- [ ] `RAW-COMPLIANT`
- [ ] `RAW-AMBIGUOUS` (specificare perché)
- [ ] `RAW-INCOMPATIBLE` (scartare o marcare HR)

---

## 8. Esempio Applicativo (caso reale)

**Fonte META:** guida/idea “Feint + Flame Blade” (build community)

**Tesi:** “con Ifrit + Blistering Feint e Flame Blade posso fare danni su feint come move action”

**STEP 0:** lettura testi RAW (talenti, spell, archetipo) su AoN/Paizo.

**Esito:** può risultare `RAW-COMPLIANT` o `RAW-AMBIGUOUS` a seconda delle parole-chiave (“hit” vs “deal damage”) — dichiarare il punto esatto.

> Nota: l’efficacia è META, la legalità è RAW.

---

## 9. Versione Ridotta (Policy sintetica)

> Le fonti META sono consultate come **primarie di analisi**, mai come fonti normative. Ogni contenuto META è utilizzabile solo dopo **STEP 0 (Ancoraggio RAW)** su AoN/Paizo (e PFS se attivo) e viene esplicitamente marcato come `RAW-COMPLIANT`, `RAW-AMBIGUOUS` o `RAW-INCOMPATIBLE`. Nessuna analisi community sostituisce le fonti ufficiali.

---

## 10. Allineamento con il Sistema Complessivo

Questa sezione è compatibile con:
- Archivist (lore e canone)
- Ruling Expert (RAW/RAI/PFS)
- MinMax Builder (ottimizzazione)

Funziona come **layer di governance trasversale** alle modalità.

---

## 11. Policy Formale (versione normativa)

**Regola vincolante:**
> Ogni contenuto proveniente da fonti META è utilizzabile **solo** se passa *tutti e quattro* i seguenti gate, senza eccezioni:
> 1. Consultazione come fonte primaria di analisi
> 2. Valutazione esplicita dell’autore
> 3. Verifica di allineamento RAW (AoN / Paizo / PFS se attivo) — **STEP 0**
> 4. Classificazione finale dichiarata
>
> L’assenza di uno qualsiasi dei quattro gate invalida l’uso del contenuto.

Questa policy ha priorità su scorciatoie, consuetudini o precedenti.

---

## 12. Automazione — Gate META → RAW (decision matrix)

### 12.1 Flusso logico

```text
Input META
  ↓
[Step -1] META-SEARCH → META-CANDIDATE
  ↓
[Step 0] RAW anchoring (AoN/Paizo)
  ↓
[Gate 1] Consultazione (tesi)
  ↓
[Gate 2] Autore valido?
  ├─ no → max verdict: RAW-AMBIGUOUS (o scarta se red flags)
  ↓ sì
[Gate 3] Verifica RAW (prereq/stacking/azioni)
  ├─ no → RAW-INCOMPATIBLE / HR
  ↓ sì
[Gate 4] Classificazione
  → RAW-COMPLIANT | RAW-AMBIGUOUS
```

### 12.2 Regole automatiche
- se **autore sconosciuto** → verdict massimo: `RAW-AMBIGUOUS`
- se **stacking o prerequisiti non chiari** → `RAW-AMBIGUOUS`
- se **contraddice AoN/Errata** → `RAW-INCOMPATIBLE`
- con **PFS ON**, ogni opzione non esplicitamente legale → `NON PFS`

---

## 13. Template di Risposta (uso pratico)

Questo template è usato implicitamente o esplicitamente ogni volta che una fonte META influenza una risposta.  
Include automaticamente lo **STEP -1 (ricerca)** e lo **STEP 0 (RAW)**.

### 13.1 Template esteso

**Fonte META:** <titolo / link / autore>

**Ricerca (STEP -1):** <query/preset + dominio seed usato>

**Valutazione autore:** <affidabile | parziale | sconosciuto>

**Ancoraggio RAW (STEP 0):**
- testi verificati su AoN/Paizo: <elenco>
- note: <parole chiave rilevanti: “hit”, “attack”, “damage roll”, ecc.>

**Verifica RAW:**
- prerequisiti/azioni: <ok | nota>
- stacking/interazioni: <ok | nota>
- PFS (se attivo): <legal | NON PFS>

**Classificazione finale:** `RAW-COMPLIANT | RAW-AMBIGUOUS | RAW-INCOMPATIBLE`

**Uso consentito:**
- ✔ build / analisi
- ⚠ richiede interpretazione (indicare punto)
- ❌ non utilizzabile senza HR

### 13.2 Template compatto (inline)

> 🔍 META-SEARCH → 📖 RAW check ✔ → 🧠 META-ANALYSIS → **RAW-COMPLIANT / RAW-AMBIGUOUS / RAW-INCOMPATIBLE**

---

## 14. Integrazione Automatica nei Template di Risposta

Quando viene usato materiale META, il sistema deve automaticamente:

1) dichiarare se è stata usata **ricerca META (STEP -1)**
2) dichiarare che è stato fatto **Ancoraggio RAW (STEP 0)**
3) mostrare la **classificazione finale**

**Output compatto obbligatorio**

> 🔍 META-SEARCH → 📖 RAW check ✔ → 🧠 META-ANALYSIS → **VERDETTO**

---

## 15. Allineamento delle Istruzioni (file da modificare)

Per allineare il funzionamento del sistema a questo metodo, tipicamente vanno aggiornati:

- **core/base profile** (es. `base_profile.*`): rendere obbligatori STEP -1 e STEP 0; vietare inferenze senza testo RAW.
- **ruling module** (es. `ruling_expert.*`): META solo dopo STEP 0 e solo come contesto, mai per stabilire RAW.
- **minmax module** (es. `minmax_builder.*`): breadcrumb + verdict obbligatori quando META entra nella risposta; applicare regole automatiche §12.2.
- **explain module** (es. `explain_methods.*`): prima di spiegazioni tecniche su regole/feat/spell/item, richiedere STEP 0.
- **response templates** (es. `templates/*`): inserire hook/placeholder per stampare breadcrumb solo quando necessario.

> I nomi file possono variare: in repo si identificano per contenuto (principles/sources/templates).

---

## 16. Sintesi Finale

- Le fonti META sono **sempre** analizzate, **mai** assunte come vere.
- STEP -1 (ricerca) e STEP 0 (RAW anchoring) rendono il metodo **ripetibile** e **anti-errore**.
- I quattro gate sono **obbligatori e non negoziabili**.
- Policy, automazione e template garantiscono coerenza, auditabilità e chiarezza.

Questa sezione rappresenta la **definizione finale e completa** della governance delle fonti.
