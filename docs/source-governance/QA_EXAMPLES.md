# QA Examples — Source Governance v1

Questi esempi servono come “golden prompts” per verificare che:

- **STEP -1** (META-SEARCH) venga usato solo per discovery → **META-CANDIDATE**
- **STEP 0** (RAW anchoring AoN/Paizo) avvenga prima di qualunque verdetto su regole/combo/build
- i **4 gate** vengano rispettati quando entra META
- la breadcrumb sia presente quando qualunque elemento deriva da META:

  🔍 META-SEARCH → 📖 RAW check ✔ → 🧠 META-ANALYSIS → VERDETTO

> Nota: gli URL AoN/Paizo qui sono indicativi (vanno sostituiti con i link effettivi usati dal sistema). Le citazioni dirette devono restare ≤25 parole.

---

## Esempio 1 — Ruling (stacking / legalità)

### Prompt
"Posso applicare **Dazing Spell** a **fireball** con **Magical Lineage** per ridurre il costo di metamagia? Funziona a PFS?"

### Risposta attesa (schema)

**🔍 META-SEARCH → 📖 RAW check ✔ → 🧠 META-ANALYSIS → VERDETTO**

**STEP -1 — META-CANDIDATE (discovery, nessun verdetto)**
- Claim META: “Magical Lineage riduce di 1 il livello di metamagia su uno specifico incantesimo.”
- Claim META: “In PFS alcune riduzioni di metamagia hanno limitazioni/FAQ.”

**STEP 0 — RAW anchoring (AoN/Paizo)**
- Fonte RAW: AoN/Paizo per **Magical Lineage** (trait) + testo del metamagic **Dazing Spell**.
- (Parafrasi breve) indica cosa riduce e in quali condizioni.

**4 gate**
1) Consultazione (tesi): elenca i claim trovati in META (senza assumerli veri).
2) Valutazione autore: classifica la fonte (ufficiale / guida / forum / sconosciuto).
3) Verifica RAW: confronta i claim col testo AoN/Paizo (e con eventuale FAQ/errata ufficiale).
4) Classificazione finale:
   - **RAW-COMPLIANT** se il testo RAW supporta chiaramente l'interazione;
   - **RAW-AMBIGUOUS** se il RAW è interpretabile e servono FAQ/GM call;
   - **RAW-INCOMPATIBLE** se il RAW contraddice il claim.

**VERDETTO (solo dopo STEP 0)**
- Conclusione: [RAW-COMPLIANT | RAW-AMBIGUOUS | RAW-INCOMPATIBLE].
- Nota PFS: se non c'è testo ufficiale, indicare “serve riferimento PFS/FAQ; senza, niente verdetto PFS definitivo”.

---

## Esempio 2 — Minmax / build (combo da guide/community)

### Prompt
"Ho visto online una combo **Shikigami Style** + **Traveler’s Any-Tool** per fare danni enormi. È RAW?"

### Risposta attesa (schema)

**🔍 META-SEARCH → 📖 RAW check ✔ → 🧠 META-ANALYSIS → VERDETTO**

**STEP -1 — META-CANDIDATE (discovery)**
- Claim META: “Any-Tool può contare come improvised weapon di categoria più alta”.
- Claim META: “Shikigami Style aumenta i dadi come se l’arma fosse più grande”.

**STEP 0 — RAW anchoring (AoN/Paizo)**
- Fonte RAW: AoN/Paizo per **Traveler’s Any-Tool** e per la catena **Shikigami Style**.

**4 gate + verdetto**
- Se il testo RAW non supporta l'assunto chiave (es. l'oggetto non è un'arma o non ha la proprietà richiesta) ⇒ **RAW-INCOMPATIBLE**.
- Se supporta, ma lascia dubbi su “improvised / counts as / size” ⇒ **RAW-AMBIGUOUS** e spiegare i punti di ambiguità.
