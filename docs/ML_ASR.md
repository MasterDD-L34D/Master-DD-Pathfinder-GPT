# Servizio ASR (REF-09 v1)

Trascrizione audio → testo italiano con timestamp, come primo servizio ML di Taverna (decisione PRD 2026-07-25: servizi ML in Taverna, Python). Implementa il requisito REQ-003 di pathmaster ("Trascrizione IT con timestamp") lato produttore.

## Endpoint

| Metodo | Path | Funzione |
|---|---|---|
| GET | `/ml/health` | Stato del servizio e engine attivo |
| POST | `/ml/transcribe` | Upload audio (`multipart/form-data`, campo `file`) → transcript JSON |

L'app parte **senza dipendenze ML**: il router è registrato con guard e l'engine di default è `fake` (deterministico, per test/sviluppo). Con `ML_ASR_ENGINE=faster_whisper` richiesto ma non installato: **501 onesto** (mai un default silenzioso).

## Contratto output (identico a pathmaster ADR-C2)

L'output è **1:1** con `transcriptImportSchema` di pathmaster (`apps/server/src/lib/transcript-import.ts`): il loro import non richiede modifiche.

```json
{
  "language": "it",
  "segments": [
    {"start": 0.0, "end": 1.5, "text": "...", "confidence": 0.98}
  ]
}
```

- `start`/`end`: secondi (float), `end >= start`
- `confidence`: opzionale, [0,1]
- `speaker`: **omesso in v1** (predisposto per la diarizzazione futura, REQ-010)

## Configurazione (env)

| Variabile | Default | Note |
|---|---|---|
| `ML_ASR_ENGINE` | `fake` | `fake` (mock deterministico) \| `faster_whisper` |
| `ML_ASR_MODEL` | `small` | modello whisper (tiny/base/small/medium/large-v3) |
| `ML_ASR_DEVICE` | `auto` | `auto`/`cpu`/`cuda` |
| `ML_ASR_COMPUTE_TYPE` | `int8` | quantization (int8 = default onesto su CPU) |
| `ML_AUDIO_DIR` | `src/data/ml/audio` | storage WORM dell'audio originale |

## Engine reale (opt-in)

```bash
.venv/Scripts/python -m pip install -r requirements-ml.txt
ML_ASR_ENGINE=faster_whisper .venv/Scripts/uvicorn src.app:app --port 8000
# altro terminale:
curl -F "file=@clip-test.ogg" http://localhost:8000/ml/transcribe
```

Il primo uso scarica il modello (~500 MB per `small`).

### Nota device (smoke 2026-07-26)

Su macchina con GPU NVIDIA ma **senza le librerie CUDA 12** (`cublas64_12.dll` ecc.), `ML_ASR_DEVICE=auto` fallisce a runtime (`RuntimeError: Library cublas64_12.dll is not found`). Opzioni: `ML_ASR_DEVICE=cpu` (default onesto, usato nello smoke) oppure installare le librerie CUDA via pip (`nvidia-cublas-cu12`, `nvidia-cudnn-cu12`) per usare la GPU.

## Smoke test con modello reale (E2, 2026-07-26)

Eseguito su `faster-whisper` 1.2.1, modello `small`, `device=cpu`, `compute_type=int8`:

- clip: TTS italiano (`edge-tts`, voce `it-IT-DiegoNeural`) da `data/ml_smoke/ground_truth.txt` (3 frasi a tema PF, ~15s) — ground truth nota;
- `POST /ml/transcribe` → HTTP 200 in **5,4s** (3 segmenti, contratto 1:1 con `transcriptImportSchema`: `language=it`, `start/end/confidence`, niente `speaker`);
- **mini WER 4,3% / CER 0,4%** contro la ground truth (`data/ml_smoke/eval_wer.py`, Levenshtein stdlib su testo normalizzato) — le differenze sono tokenizzazione (l'ascia/lascia), non errori acustici. Misura una tantum sul sintetico: la REQ-003 formale richiede un corpus reale annotato (resta in coda);
- fix collaterale: i 2 test del 501 onesto ora simulano l'assenza di faster-whisper via `sys.modules` invece di dipendere dall'ambiente (restano verdi con la dipendenza installata);
- clip mp3 e transcript sono gitignored (rigenerabili da ground truth + script).

## Diarizzazione v1 (E3, REQ-010, 2026-07-26)

`POST /ml/transcribe` con campo form `diarize=true` aggiunge la chiave
`speaker` ("S1".."Sn") a ogni segmento — la chiave opzionale prevista da
`transcriptImportSchema` (→ `speakerLabel` lato pathmaster, fallback "S?"
se assente). Implementazione: embedding vocali **resemblyzer** (GE2E,
modello MIT da GitHub, nessun gate HuggingFace) calcolati sulle fette
d'audio dei segmenti whisper + clustering in ordine temporale (coseno,
soglia 0.30, nuovo cluster oltre soglia; ABA riassegnato al cluster
originale; segmenti <0,6s ereditano l'etichetta). `src/ml/diarize.py`.

Smoke (`faster-whisper` small/cpu + resemblyzer): clip 1 voce → 3/3
segmenti S1; clip 2 voci (Diego+Elsa concatenate) → S1 sulle battute della
voce A, S2 sulla battuta della voce B, split esatto al confine (8,2s).

**Privacy (design E3)**: gli embedding sono calcolati in memoria e MAI
persistiti — il WORM contiene solo l'audio originale (REQ-001). Le
etichette S1..Sn sono anonime e stabili solo dentro la singola chiamata.
**REQ-012 (voiceprint persistente) resta fuori scope**: un DB di
voiceprint è dato biometrico e richiede design dedicato (consenso
esplicito per-partecipante, storage separato, retention, diritto di
cancellazione) — da affrontare con REQ-010 completa nel blocco ML Fase 6.

### DER su sintetico degradato (2026-07-27)

Harness DER in casa (`src/ml/der.py` + CLI `data/ml_smoke/eval_der.py`,
~70 righe, nessuna dipendenza nuova): NIST semplificato su griglia da
10 ms — DER = (miss + false alarm + confusion) / speaker-time reference,
con mapping ottimo S1..Sn → speaker veri per forza bruta (le etichette
ipotesi sono anonime); overlap contato per speaker-time come NIST; niente
collare di tolleranza ai confini (semplificazione dichiarata).

Campione `data/ml_smoke/clip_overlap.wav` (gitignored, rigenerabile con
`gen_overlap_clip.py`): clip_a (Diego, 8,2s) + clip_b (Elsa, 7,2s) mixate
con **3,0s di overlap artificiale** al centro + rumore bianco leggero;
ground truth a intervalli in `ground_truth_overlap.json` (presenza clip
nel mix, non attività vocale esatta — approssimazione dichiarata).

Risultato pipeline reale (faster-whisper small/cpu + resemblyzer,
`diarize=true`): **DER 35,0%** (scored 15,4s speaker-time; miss 3,4s,
confusion 2,0s, false alarm 0; mapping S1→A, S2→B corretto). La pipeline
tiene i due cluster ma **sull'overlap whisper attribuisce il parlato
misto a una sola voce** (i segmenti whisper non possono rappresentare due
speaker simultanei) e la voce B entra solo a overlap finito: il DER sale
da ~0% (2voci senza overlap) a 35%. È il comportamento atteso di una
diarizzazione segment-level su audio sovrapposto, documentato com'è.

**Questa misura NON chiude REQ-010**: il gate formale della REQ-010 piena
richiede DER/attribution misurati su **audio reale di sessione**
(registrazione di gioco multivoce annotata), che oggi non esiste. Il
sintetico degradato serve solo a fissare un harness e un baseline di
riferimento; REQ-010 piena resta aperta in attesa di audio reale.

### DER su conversazioni reali italiane (ASR-ItaCSC, 2026-07-28)

Dataset **ASR-ItaCSC** (Magic Data Technology Co., Ltd., via MagicHub,
"Magic Data open-source license"; fonte, licenza e attribuzione in
`data/ml_benchmark/NOTICE.md`): 14 conversazioni spontanee registrate su
mobile indoor, 3 coppie di parlanti, WAV 16 kHz mono **una traccia per
speaker** + TXT per traccia con `[start,end]\tspeaker\tgender\ttesto` —
timestamp e speaker già presenti, **nessun forced alignment necessario**
(converter `data/ml_benchmark/prepare_itacsc_groundtruth.py`, test
`tests/test_prepare_itacsc_groundtruth.py`).

**Metodo**: per ogni conversazione scelta si mixano le due tracce 50/50 in
mono (stesso clock condiviso, verificato: il primo turno annotato di G0002
"OK grande Fra sì sta registrando" [1,2-4,3s] coincide col primo segmento
whisper del mix [1,0-8,4s]) e si limita ai **primi 300 s** (costo CPU);
ground truth = unione dei turni annotati delle due tracce sulla stessa
finestra (overlap naturale, contato per speaker-time dalla griglia di
`src/ml/der.py`). Pipeline reale invariata: faster-whisper small/cpu/int8
+ resemblyzer, `diarize=true` (`data/ml_benchmark/run_itacsc_der.py`).
Criteri di scelta: una conversazione per coppia di parlanti (3 voci
diverse per genere), coprendo il caso peggiore F/F e l'overlap massimo
del corpus: A0001_S001 (F+M, overlap 116 s su 1301 s), A0002_S006 (F+M,
overlap 298,7 s — il massimo), A0003_S001 (F+F, overlap 106 s).

**Risultati** (300 s per conversazione, griglia 10 ms, mapping ottimo):

| conversazione | DER | scored (speaker-time) | miss | false alarm | confusion | mapping |
|---|---|---|---|---|---|---|
| A0001_S001 (F+M) | **53,3%** | 303,8 s | 0,7 s | 79,0 s | 82,1 s | S1→G0002 (un solo cluster!) |
| A0002_S006 (F+M) | **81,0%** | 334,6 s | 0,3 s | 116,2 s | 154,3 s | S1→G0003, S2→G0004 (S2: 4 s) |
| A0003_S001 (F+F) | **38,8%** | 278,2 s | 31,2 s | 37,2 s | 39,6 s | S1→G0006, S2→G0005 (bilanciato) |

Media aritmetica: **57,7%** — molto peggio del baseline sintetico (35,0%).
Diagnosi onesta, confermata dai transcript (gitignored): su audio reale
mobile il clustering sequenziale resemblyzer (soglia 0,30) **collassa i
due parlanti in un cluster unico** nei casi F+M (A0001: 48/48 segmenti
S1; A0002: S2 solo 4 s su 296) mentre separa bene la coppia F/F (A0003:
S1 137 s / S2 108 s) — l'effetto "una sola voce sull'overlap" visto sul
sintetico qui si somma al fallimento di separazione; inoltre i segmenti
whisper fondono turni brevi adiacenti (A0001: 299,9 s coperti su 300),
gonfiando il false alarm nei micro-silenzi fra turni. Il sintetico TTS
(voci pulite e molto distanti) era quindi un proxy **ottimista**.

**Frase onesta**: questa è una misura su conversazioni reali italiane
annotate — proxy molto più fedele del sintetico — ma **NON è ancora il
gate formale REQ-010**, che resta "audio reale di sessione di gioco"
(registrazione multivoce consensuale annotata). Zip, mix, transcript e
ground truth JSON restano in `data/ml_benchmark/itacsc/` (gitignored,
rigenerabili; licenza Magic Data: dati mai in git).

## Privacy e vincoli

- **Audio originale immutabile (REQ-001)**: WORM in `ML_AUDIO_DIR/<sha16>_<nome>`, dedup per sha256, mai riscritto.
- **Consenso (REQ-002)**: gate lato pathmaster alla creazione sessione; questo servizio è un transcodificatore "dumb" e non gestisce consenso.
- **Upload max**: 200 MB (sessioni da ore restano fuori v1).
- **Fuori scope v1**: voiceprint (REQ-012), purge (REQ-015), misura WER/CER formale (serve corpus audio reale). Diarizzazione: v1 shipped (sezione sopra); DER/attribution su audio reale resta gate aperto di REQ-010 piena.

## Test

`tests/test_ml_asr.py` (engine/factory/guard) e `tests/test_ml_router.py` (contratto endpoint, 501, WORM dedup) — tutti verdi senza faster-whisper installato.

Piano: `planning/2026-07-25-ref09-asr-service.md`.
