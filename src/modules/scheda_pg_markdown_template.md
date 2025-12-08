### 🧙 Scheda Personaggio in Markdown

---

{# ========== SETUP & MACROS ========== #}
{% set PRINT_MODE    = print_mode    | default(false) %}
{% set SHOW_MINMAX   = show_minmax   | default(true)  %}
{% set SHOW_VTT      = show_vtt      | default(true)  %}
{% set SHOW_QA       = show_qa       | default(true)  %}
{% set SHOW_EXPLAIN  = show_explain  | default(true)  %}
{% set SHOW_LEDGER   = show_ledger   | default(true)  %}  {# <-- nuovo: Libro Mastro #}
{% set DECIMAL_COMMA = decimal_comma | default(true)  %}

{% macro d(val, fallback='—') -%}{{ (val if (val is not none and val != '') else fallback) }}{%- endmacro %}
{% macro mod(x) -%}{{ (((x|default(10))|int) - 10) // 2 }}{%- endmacro %}
{% macro j(list, sep=', ') -%}{{ (list or []) | select('string') | list | join(sep) }}{%- endmacro %}
{% macro signed(x) -%}{% if x is not none %}{{ "+" if x>=0 else "" }}{{ x }}{% else %}—{% endif %}{%- endmacro %}

{# --- Monete / Valorizzazioni (per Adventurer Ledger) --- #}
{% macro to_gp(pp=0,gp=0,sp=0,cp=0) -%}{{ (pp|float)*10 + (gp|float) + (sp|float)/10 + (cp|float)/100 }}{%- endmacro %}
{% macro coin_str(pp=0,gp=0,sp=0,cp=0) -%}
PP {{pp|default(0)}} • GP {{gp|default(0)}} • SP {{sp|default(0)}} • CP {{cp|default(0)}}
{%- endmacro %}
{% macro fmt_gp(x) -%}
{%- set raw = ('{:.2f}'.format(x|float)).rstrip('0').rstrip('.') -%}
{{ (raw.replace('.', ',') if DECIMAL_COMMA else raw) }} gp
{%- endmacro %}

{% set ST  = statistiche or {} %}
{% set STK = statistiche_chiave or {} %}
{% set SAL = salvezze or {} %}
{% set BM  = benchmarks or {} %}

{% set CL = classi or [] %}
{% set FIRST_CLASS = (CL[0].nome if CL and CL|length>0 else '—') %}

{# ----- CA: dodge separato + ricostruzione ----- #}
{% set AC_arm   = AC_arm   | default(0) %}
{% set AC_scudo = AC_scudo | default(0) %}
{% set AC_des   = AC_des   | default(0) %}
{% set AC_defl  = AC_defl  | default(0) %}
{% set AC_nat   = AC_nat   | default(0) %}
{% set AC_dodge = AC_dodge | default(0) %}
{% set AC_misc  = AC_misc  | default(AC_altro | default(0)) %}

{% set AC_tot = AC_tot if (AC_tot is not none)
  else (10 + AC_arm + AC_scudo + AC_des + AC_defl + AC_nat + AC_dodge + AC_misc) %}

{% set CA_touch = 10 + AC_des + AC_defl + AC_dodge + AC_misc %}
{% set CA_ff    = 10 + AC_arm + AC_scudo + AC_defl + AC_nat + AC_misc %}

{# ----- Spell table: robust ----- #}
{% set spell_levels    = spell_levels or [] %}
{% set has_spell_table = (spell_levels|length) > 0 %}

{# Hook Percezione auto se presente skills_map #}
{% set skills_map = skills_map or {} %}
{% if skills_map and skills_map.Percezione and skills_map.Percezione.totale is not none %}
  {% set percezione_tot = skills_map.Percezione.totale %}
{% endif %}

# {{ nome | default('—') }} — Liv. {{ get_total_level(CL)|default('—') }} ({{ razza | default('—') }} · {% for c in CL %}{{ c.nome }} ({{ c.livelli }}){% if c.archetipi %} — {{ c.archetipi | join(', ') }}{% endif %}{% if not loop.last %} / {% endif %}{% endfor %})

**Allineamento:** {{ d(allineamento) }}  
**Divinità:** {{ d(divinita) }}  
**Taglia:** {{ d(taglia) }} | **Età:** {{ d(eta) }} | **Sesso:** {{ d(sesso) }} | **Altezza/Peso:** {{ d(altezza) }} / {{ d(peso) }}  
**Ruolo consigliato:** {{ d(ruolo) }}  
**Stile interpretativo:** {{ d(player_style) }} — {{ d(style_hint(player_style)) }}  
**Background breve (5–10 righe):** {{ d(background) }}

---

## Statistiche fondamentali
- **For** {{ ST.Forza|default(10) }} (mod {{ mod(ST.Forza) }})
- **Des** {{ ST.Destrezza|default(10) }} (mod {{ mod(ST.Destrezza) }})
- **Cos** {{ ST.Costituzione|default(10) }} (mod {{ mod(ST.Costituzione) }})
- **Int** {{ ST.Intelligenza|default(10) }} (mod {{ mod(ST.Intelligenza) }})
- **Sag** {{ ST.Saggezza|default(10) }} (mod {{ mod(ST.Saggezza) }})
- **Car** {{ ST.Carisma|default(10) }} (mod {{ mod(ST.Carisma) }})

- **PF (HP):** {{ d(STK.PF) }} | **CA:** {{ d(STK.CA, AC_tot) }}  
- **CA (breakdown):** {{ AC_tot }} = 10 + Arm {{ AC_arm }} + Scudo {{ AC_scudo }} + Des {{ AC_des }} + Defl {{ AC_defl }} + Nat {{ AC_nat }} + Dodge {{ AC_dodge }} + Altro {{ AC_misc }}  
- **CA Var.:** Contatto {{ CA_touch }} · Colto alla sprovvista {{ CA_ff }}  
- **Tiri Salvezza:** Temp {{ d(SAL.Tempra) }} / Riflessi {{ d(SAL.Riflessi) }} / Volontà {{ d(SAL.Volontà) }}  
- **BAB:** {{ d(BAB) }} | **Iniziativa:** {{ d(init) }} | **Velocità:** {{ d(speed) }}  
- **CMB/CMD:** {{ d(CMB) }} / {{ d(CMD) }}  

{% set CMD_base = 10 + (BAB|default(0)) + (mod(ST.Forza) if use_str_for_cmd|default(true) else mod(ST.Destrezza)) + mod(ST.Destrezza) + size_mod_cmd|default(0) + cmd_altro|default(0) %}
- **CMD (dettaglio):** {{ CMD|default(CMD_base) }} = 10 + BAB {{ BAB|default(0) }} + For/Des {{ (mod(ST.Forza) if use_str_for_cmd|default(true) else mod(ST.Destrezza)) }} + Des {{ mod(ST.Destrezza) }} + Taglia {{ size_mod_cmd|default(0) }} + Altro {{ cmd_altro|default(0) }}

- **PE (XP):** {{ d(xp_correnti) }} / {{ d(xp_prossimo_livello) }}

---

## Difese Speciali
- **RD/Res/Imm:** {{ d(rd_res_imm) }}  
- **RS:** {{ d(rs) }} | **Guarigione rapida/Rigenerazione:** {{ d(heal_regen) }}  
- **Sensi:** {{ d(sensi) }} | **Percezione (tot):** {{ d(percezione_tot) }}

---

## Combattimento
### Armi e attacchi
| Arma | Tipo | Attacco | Danni | Critico | Portata | Note |
|---|---|---:|---|---|---|---|
{% for a in (armi or []) -%}
| {{ d(a.nome) }} | {{ d(a.tipo) }} | {{ d(a.attacco) }} | {{ d(a.danni) }} | {{ d(a.critico) }} | {{ d(a.portata) }} | {{ a.note | default('') }} |
{%- endfor %}
{% if (armi or [])|length == 0 %}_(Nessuna arma strutturata: derivabile da `equipaggiamento` o aggiungerla qui.)_{% endif %}

- **Attacchi naturali:** {{ d(attacchi_naturali) }}  
- **Capacità speciali:** {{ d(capitolo_capacita, capacita_speciali) }}

### Manovre CMB
| Manovra | Bonus |
|---|---:|
| Disarm | {{ d(cmb_disarm) }} |
| Trip   | {{ d(cmb_trip) }} |
| Grapple| {{ d(cmb_grapple) }} |
| Bull Rush | {{ d(cmb_bull_rush) }} |
| Sunder | {{ d(cmb_sunder) }} |

---

## Economia d’Azione
- **AoO/round:** {{ d(aoo_per_round) }}  
- **Swift usata?:** {{ d(swift_used,'no') }}  
- **Immediate pronte?:** {{ d(immediate_ready,'sì') }}

---

## Armatura (tecnica)
- **ACP:** {{ d(acp) }} | **Max Des:** {{ d(max_dex) }} | **ASF:** {{ d(asf_pct) }}% | **Velocità ridotta:** {{ d(speed_armor_penalty) }}

---

## Abilità (Skills)
| Abilità | Gradi | Mod Car | Var | Classe? | Totale |
|---|---:|---:|---:|:--:|---:|
{% for s in (skills or []) -%}
| {{ d(s.nome) }} | {{ s.gradi|default(0) }} | {{ signed(s.mod_car|default(0)) }} | {{ signed(s.var|default(0)) }} | {{ '✓' if s.classe else '' }} | {{ s.totale|default(s.gradi|default(0) + s.mod_car|default(0) + s.var|default(0) + (3 if s.classe else 0)) }} |
{%- endfor %}
{% if (skills or [])|length == 0 %}_Nessuna abilità strutturata._{% endif %}

---

## Talenti, Tratti & Difetti
- **Talenti:** {% set feats = (progressione or []) | map(attribute='talento') | select('string') | reject('equalto', None) | list %}{{ j(feats) or '—' }}
- **Tratti:** {% if tratti %}{% for t in tratti %}{{ d(t.nome) }}{{ ', ' if not loop.last }}{% endfor %}{% else %}—{% endif %}
- **Difetti:** {{ d(difetti) }}

---

## Poteri di Classe / Archetipi
{{ d(poteri_classe) }}

**Usi/giorno chiave:** {{ d(usi_giorno_chiave) }}

---

## Incantesimi / Capacità Magiche
- **Classe da incantatore:** {{ d(classe_incantatore, FIRST_CLASS) }}  
- **CD base incantesimi:** {{ d(spell_dc_base) }} | **LI:** {{ d(livello_incantatore) }}  
- **Slot per giorno:** {{ d(slot_incantesimi) }}

**Conosciuti/Preparati**
{% for lvl in (magia or {}).keys() | map('int') | list | sort %}
- **{{ lvl }}°:** {{ (magia[lvl] or []) | join(', ') }}
{% endfor %}
{% if (magia or {})|length == 0 %}_Nessun incantesimo conosciuto o preparato specificato._{% endif %}

{% if has_spell_table %}
| Liv | Conosciuti | Preparati | Slot/giorno | CD |
|---:|---:|---:|---:|---:|
{% for sl in spell_levels -%}
| {{ sl.liv }} | {{ d(sl.known) }} | {{ d(sl.prepared) }} | {{ d(sl.per_day) }} | {{ d(sl.dc) }} |
{%- endfor %}
{% else %}
_Nessuna tabella incantesimi disponibile._
{% endif %}

### Incantatore (tecnico)
{% if concentration_bonus is not none %}
- **Concentrazione:** {{ concentration_bonus }}
{% else %}
- **Concentrazione (hint):** LI {{ d(livello_incantatore,0) }} + mod stat chiave + vari
{% endif %}
- **Penetrazione Magica:** {{ d(spell_penetration_bonus) }}  
- **CD per Scuola:** {{ d(dc_per_school) }}

---

## Routine di Round (rapida)
1) **Buff chiave:** {{ d(buffs_open) }}  
2) **Posizionamento:** {{ d(movement_plan) }}  
3) **Output:** {{ d(attack_plan) }}  
**Priorità reattive:** {{ d(reactions_list, 'Step laterale; AoO; Immediate') }}

---

## Risorse Giornaliere
| Risorsa | Max | Usate | Rimaste | Reset |
|---|---:|---:|---:|---|
{% set risorse = risorse_giornaliere or [] %}
{% if risorse %}
{% for r in risorse -%}
| {{ d(r.nome) }} | {{ d(r.max) }} | {{ d(r.usate,0) }} | {{ (r.max|default(0)) - (r.usate|default(0)) }} | {{ d(r.reset,'giornaliero') }} |
{%- endfor %}
{% else %}
| Rage / Ki / Panache / Grit / Arcane Pool / Performance | {{ d(res_max) }} | {{ d(res_used,0) }} | {{ (res_max|default(0)) - (res_used|default(0)) }} | {{ d(res_reset,'giornaliero') }} |
{% endif %}

---

## Consumabili
- **Pozioni:** {{ d(consum_potions) }}  
- **Pergamene:** {{ d(consum_scrolls) }}  
- **Bacchette (cariche):** {{ d(consum_wands) }}

---

## WBL & Shopping
- **Budget attuale:** {{ gp|default(0) }} gp | **Breakpoint prossimo:** {{ d(next_wbl_gp) }} gp
- **Priorità acquisti:** {{ d(buylist_priority) }}

---

## Equipaggiamento
- {{ (equipaggiamento or []) | join(', ') if equipaggiamento else '—' }}
- **Armi/Armature/Oggetti:** {{ d(equip_base) }}  
- **Peso totale trasportato:** {{ d(peso_totale) }}  
- **Capacità di trasporto:** L {{ d(carico_leggero) }} / M {{ d(carico_medio) }} / P {{ d(carico_pesante) }}  
- **Valute:** Rame {{ cp|default(0) }} • Argento {{ sp|default(0) }} • Oro {{ gp|default(0) }} • Platino {{ pp|default(0) }}

---

## Lingue & Varie
- **Lingue:** {{ (lingue or []) | join(', ') if lingue else '—' }}  
- **Punti Eroe (opz.):** {{ d(hero_points) }}  
- **Altre note:** {{ d(note_varie) }}

---

## Companion / Famigli
{{ d(companion) }}

---

## Psicologia & Roleplay
- **Sinergie**: {{ j(sinergie, ', ') or d(roleplay_sinergie) }}
- **Teoria dominante**: {{ d(teoria_dominante, 'Jung/OCEAN/Enneagramma') }}
- **Comportamento prevalente**: {{ d(comportamento_prevalente, 'es. introverso, impulsivo, empatico') }}
- **Stile decisionale**: {{ d(stile_decisionale, 'es. segue l’istinto, valuta i rischi, ecc.') }}
- **Motto/Frase tipica/Modi di dire/Accento**: {{ d(motto_o_frase, 'es. accento locale, intercalare ricorrente') }}
- **Spunti per interpretazione**: {{ d(spunti_interpretativi, 'es. parla per enigmi, ama raccontare storie') }}
- **Background Narrativo**: {{ d(background_narrativo, 'breve backstory coerente con razza, classe e tratti') }}

---

{# ========== LIBRO MASTRO DELL’AVVENTURIERO (LEDGER) ========== #}
{% if SHOW_LEDGER %}
## 💰 Adventurer Ledger — KPI & Movimenti
{% set cur_pp = (currency.pp if currency is defined else pp) | default(0) %}
{% set cur_gp = (currency.gp if currency is defined else gp) | default(0) %}
{% set cur_sp = (currency.sp if currency is defined else sp) | default(0) %}
{% set cur_cp = (currency.cp if currency is defined else cp) | default(0) %}
{% set gp_liquidi = to_gp(cur_pp,cur_gp,cur_sp,cur_cp) %}
{% set gp_investiti = ledger_invested_gp | default(0) %}
{% set gp_totali = gp_liquidi + gp_investiti %}
{% set wbl_target_gp = wbl_target_gp | default(next_wbl_gp | default(0)) %}
{% set wbl_delta_gp = (gp_totali - (wbl_target_gp|float)) %}

- **Cassa (liquidi):** {{ coin_str(cur_pp,cur_gp,cur_sp,cur_cp) }} = **{{ fmt_gp(gp_liquidi) }}**  
- **Valore investito (gear):** **{{ fmt_gp(gp_investiti) }}** · **Wealth totale:** **{{ fmt_gp(gp_totali) }}**  
- **WBL target (liv {{ get_total_level(CL)|default(1) }}):** {{ fmt_gp(wbl_target_gp) }} · **Δ vs WBL:** {{ signed((wbl_delta_gp)|round(1)) }} gp  
- **Encumbrance hint:** {{ d(ledger_encumbrance_hint, 'ok') }}

### Movimenti (ultimi / sessione)
| Data | Tipo | Oggetto/Voce | Q.tà | Val. unit | Totale | Δ GP | Fonte (AP/SX) | PFS |
|---|---|---|---:|---:|---:|---:|---|:--:|
{% for m in (ledger_movimenti or []) -%}
| {{ d(m.data) }} | {{ d(m.tipo) }} | {{ d(m.oggetto) }} | {{ d(m.qty,1) }} | {{ d(m.vu) }} | {{ d(m.tot) }} | {{ d(m.delta_gp) }} | {{ d(m.source) }} | {{ '✓' if m.pfs else '' }} |
{%- endfor %}
{% if (ledger_movimenti or [])|length == 0 %}_Nessun movimento registrato._{% endif %}

### Loot Parcels (non ancora liquidati)
| Parcella | Stima gp | Assegnatario | Note |
|---|---:|---|---|
{% for p in (ledger_parcels or []) -%}
| {{ d(p.nome) }} | {{ d(p.val_gp) }} | {{ d(p.assegnatario) }} | {{ d(p.note) }} |
{%- endfor %}
{% if (ledger_parcels or [])|length == 0 %}_Nessun loot in attesa._{% endif %}

### Coda Crafting
| Item | DC | Giorni | Costo materie | Risparmio | Stato |
|---|---:|---:|---:|---:|---|
{% for c in (ledger_crafting or []) -%}
| {{ d(c.item) }} | {{ d(c.dc) }} | {{ d(c.days) }} | {{ d(c.cost) }} | {{ d(c.saving) }} | {{ d(c.status,'open') }} |
{%- endfor %}
{% if (ledger_crafting or [])|length == 0 %}_Nessun crafting pianificato._{% endif %}

### Audit & PFS
- **Flag non PFS-legal:** {{ d(ledger_pfs_flags, '—') }}
- **Note GM/Audit:** {{ d(ledger_audit_notes, '—') }}

{% endif %}

{% if not PRINT_MODE and SHOW_VTT %}
---
## Hook VTT / Export
- **Map ID:** {{ d(map_id) }} | **Bundle asset:** {{ d(vtt_bundle_path) }}
- **Preset luci:** {{ d(vtt_light, 'day') }} | **Token scale:** {{ d(token_scale_hint, 'M') }}
- **Grid consigliata:** {{ d(recommended_grid_size) }} | **Safe/Bleed:** {{ d(safe_area_pct, 5) }}% / {{ d(bleed_pct, 2) }}%
- **Note GM:** {{ d(vtt_gm_notes) }}  <!-- 2–3 POI, percorsi, consigli Foundry/Roll20 -->
- **Formati supportati:** Markdown strutturato, JSON ledger/vtt_json, blocchi compatibili con VTT.
- **Note localizzazione numerica:** separatore {{ ',' if DECIMAL_COMMA else '.' }}, unità in gp.
- **CTA export:** /export_pg_sheet • /export_pg_sheet_json
{% endif %}

---

{# ========== SEZIONE DIDATTICA INTEGRATA (EXPLAIN) ========== #}
{% if not PRINT_MODE and SHOW_EXPLAIN %}
---
## Explain – Regola & Procedura (multi‑metodo)
- **Regola (in una riga):** {{ d(explain.tldr) }}
- **Contesto & Scopo:** {{ d(explain.context) }}

### Procedura passo‑passo
{{ d(explain.step_by_step) }}

### Metodo 2 – Algoritmico / Flow
{{ d(explain.algorithmic) }}

### Metodo 3 – Analogia / Metafora
{{ d(explain.analogy) }}

### Errori comuni (e come evitarli)
{{ d(explain.common_mistakes) }}

### RAW vs RAI (edge cases)
{{ d(explain.raw_vs_rai) }}

### Esempio numerico rapido
{{ d(explain.numeric_example) }}

### Verifica / Quiz lampo (3 domande)
{{ d(explain.quick_quiz) }}

### Checklist di applicazione al tavolo
- {{ d(explain.checklist) }}

### Fonti didattiche (puntuali)
- {{ d(explain.sources) }}  {# es. AoN → CRB p.X; FAQ Paizo (link), blog dev #}
{% endif %}

{# ========== TECNICO/ANALISI (toggle) ========== #}
{% if not PRINT_MODE and SHOW_MINMAX %}
---
## Analisi MinMax
- **DPR medio (base/nova):** {{ d(STK.DPR_Base) }} / {{ d(STK.DPR_Nova) }}
- **Sostenibilità difensiva:** {{ d(BM.Defense_status) }} {{ (BM.Defense_delta ~ '%') if BM.Defense_delta is not none else '' }}
- **Meta Tier:** {{ d(BM.meta_tier, STK.meta_tier) }}

**Benchmark (auto) — Ref: {{ d(benchmark_reference_label, FIRST_CLASS) }}**
| Parametro | Stato | Δ vs Ref |
|---|---:|---:|
| DPR 1–3 | {{ d(BM.DPR_early_status) }} | {{ BM.DPR_early_delta if BM.DPR_early_delta is not none else '—' }}% |
| DPR 4+  | {{ d(BM.DPR_late_status)  }} | {{ BM.DPR_late_delta  if BM.DPR_late_delta  is not none else '—' }}% |
| Difesa  | {{ d(BM.Defense_status)   }} | {{ BM.Defense_delta   if BM.Defense_delta   is not none else '—' }}% |
| Buff    | {{ d(BM.Buff_status) }} | – |
| Azioni  | {{ d(BM.Actions_status) }} | – |
| Scaling | {{ d(BM.Scaling_status) }} | – |

🔥 **Risk Heatmap (≥2):** Feat → {{ j(BM.risk_top3.feats) }} · Spell → {{ j(BM.risk_top3.spells) }}  
🏷 **Origine suggerimenti:** {{ source_mix_summary() }}
{% if benchmark_comparison %}
---
## Benchmark Comparativo
**Riferimento:** {{ benchmark_comparison.reference_label }} ({{ 'Auto' if benchmark_comparison.auto else 'Manuale' }}){% if benchmark_comparison.timestamp %} — {{ benchmark_comparison.timestamp }}{% endif %}
| Categoria | Stato | Δ % |
|---|---|---:|
{% for k,v in benchmark_comparison.comparison.items() -%}
| {{ k }} | {{ v.status }} | {{ v.diff }} |
{%- endfor %}
{% endif %}

{% if not PRINT_MODE and SHOW_QA %}
---
## QA rapido
- **Tabelle popolate?:** armi/skill/incantesimi non vuote o placeholder indicato.
- **Valute normalizzate:** {{ coin_str(pp, gp, sp, cp) }} (usa fmt_gp per export).
- **Coerenza WBL:** Δ vs target {{ d(wbl_delta_gp) }} gp; vendite/acquisti loggati nel ledger.
- **Badge/Lingua:** tag PFS/RAW se noti; lingua coerente con prompt.
{% endif %}

---
## Output checklist (inserire nel render finale)
- Header con toggle attivi (MINMAX/VTT/QA/EXPLAIN/LEDGER) e lingua.
- Fonti/tag: RAW/PFS/HR/META e richiami al Ledger/Explain/MinMax usati.
- Struttura minima: sommario PG, blocchi statistici, economia (ledger/WBL), eventuale sezione Explain/MinMax.
- Dati numerici formattati con {{ ',' if DECIMAL_COMMA else '.' }} come separatore decimale e unità gp/%. 
- Sezioni vuote: sostituire con placeholder espliciti per evitare header orfani.
{% endif %}

{% if not PRINT_MODE %}
---
## Suggerimenti interpretativi
- {{ d(spunti_interpretativi) }}
{% endif %}

---
> 📎 Fonti Meta (badge sintetico): {{ lookup_meta_badges('any') or '—' }}

---
## Profilo ruolistico (“alla Locanda”)
- **Modello psicologico:** {{ d(modello_psico) }} (es. Jung/OCEAN/Enneagramma)  
- **Stile decisionale:** {{ d(stile_decisionale) }}  
- **Storia personale (perché in avventura):** {{ d(storia_personale) }}  
- **Relazioni & legami:** {{ d(relazioni_legami) }} *(un PNG caro, una rivalità, un giuramento)*  
- **Ganci di campagna:** {{ d(ganci_campagna) }} *(per restare nel party)*  
- **Flavor RP:** {{ d(flavor_rp) }} *(tic, frasi tipiche, feticci/ricordi)*

---
## Canone & Fonti
- **Edizione di riferimento:** PF1e  
- **Fonti primarie (📗):** {{ d(fonti_primarie) }}  
- **Secondarie (🔎):** {{ d(fonti_secondarie) }}  
- **Varianti PFS-Lore (🧭):** {{ d(pfs_varianti) }}  
- **Dev Insight (🧪):** {{ d(dev_insight) }}  
- **House Lore (❗):** {{ d(house_lore_note) }}  
- **Citazioni brevi (≤25 parole):**
{% for c in (citazioni_brevi or []) -%}
- “{{ c.estratto }}” — {{ c.fonte }}{{ ' ' ~ c.pagina_opz if c.pagina_opz else '' }}
{%- endfor %}

---
## Collegamenti di Campagna
- **SX00 (dashboard):** {{ d(sx00_link) }}
- **AV corrente:** {{ d(av_code) }} | **SX correlate:** {{ d(sx_codes) }}
- **Fazioni (NC) collegate:** {{ d(fazioni_collegate) }}
- **Thread aperti / milestone:** {{ d(thread_aperti) }}
{% if not PRINT_MODE and SHOW_QA %}
---
## QA & Spoiler
- **spoiler_mode:** {{ d(spoiler_mode, 'light') }}  
- **AP warning:** {{ d(ap_warning) }}  
- **Confidence:** {{ d(confidence_score) }} | **Uncertainty flags:** {{ d(uncertainty_flags) }}

{% if glossario_golarion %}
---
## Glossario Golarion (rapido)
{% for g in glossario_golarion.termini or [] -%}
- **{{ g.termine }}**: {{ g.def }}
{%- endfor %}
{% endif %}

---
## Canone & Fonti META
- **Fonti (RAW/PFS se presenti):** {{ (fonti or []) | join(', ') if fonti else '—' }}
- **Fonti META (ord. autorità):** {% for f in (fonti_meta or []) %}{{ f.badge }} [{{ f.tipo }}]({{ f.link }}){% if not loop.last %} · {% endif %}{% endfor %}

---
## Regole & QA
- **Regole attive:** {{ rules_status_text() }}  
- **QA export gate:** Core={{ 'OK' if validate_core_ok else '—' }}, Feats={{ 'OK' if validate_feats_ok else '—' }}, Sim={{ 'OK' if simulate_ok else '—' }}
{% endif %}

