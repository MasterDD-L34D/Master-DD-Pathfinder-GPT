# ASR-ItaCSC — fonte, licenza e attribuzione

Benchmark DER (REQ-010) su **ASR-ItaCSC: An Italian Conversational Speech
Corpus** di Magic Data.

- **Fonte**: <https://magichub.com/datasets/italian-conversational-speech-corpus/>
  (download dopo registrazione gratuita MagicHub; nessun mirror pubblico
  noto a 2026-07).
- **Copyright**: Beijing Magic Data Technology Co., Ltd. — licenza
  dichiarata "Magic Data open-source license" sulla pagina del dataset; il
  README nello zip vieta ridistribuzione senza permesso.
- **Contenuto**: WAV 16 kHz/16 bit/mono + TXT UTF-8 per traccia
  (`[start,end]\tspeaker_id\tgender\ttranscript`), 14 conversazioni
  (28 tracce, una per speaker) tra 3 coppie di parlanti (G0001-G0002,
  G0003-G0004, G0005-G0006), ~22-25 min ciascuna.
- **Uso in questo repo**: solo misura locale DER. Zip, audio estratti,
  mix, transcript e ground truth JSON in `data/ml_benchmark/itacsc/` sono
  **gitignored e mai committati** (dati di terzi, rigenerabili riscaricando
  il dataset). Si committano solo gli script (`prepare_itacsc_groundtruth.py`,
  `run_itacsc_der.py`), i numeri aggregati in `docs/ML_ASR.md` e questo
  NOTICE.

Attribuzione richiesta in ogni uso pubblico dei risultati:
*"ASR-ItaCSC, Magic Data Technology Co., Ltd., via MagicHub"*.
