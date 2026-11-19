# ಗಾದಾಮೃತ — ದತ್ತಾಂಶ ಕಡತಗಳ ವಿವರಣೆ

**ಸ್ಥಳೀಯ ಪ್ರಸ್ತುತ ಸ್ಥಿತಿ: 19 ನವೆಂಬರ್ 2026.** ದತ್ತಸಂಚಯದಲ್ಲಿ 200 ಬಳಕೆದಾರ-ಅನುಮೋದಿತ ಗಾದೆಗಳಿವೆ. ಪ್ರತಿ ಗಾದೆಗೆ ಎರಡು ಸಂದರ್ಭಗಳಂತೆ 400 ಸಂದರ್ಭಗಳನ್ನು ಸಿದ್ಧಪಡಿಸಲಾಗಿದೆ. ಅರ್ಥ/ಅನುವಾದ/ಸಂದರ್ಭಗಳಿಗೆ ಸ್ವತಂತ್ರ ಕನ್ನಡ ಪರಿಶೀಲನೆ ಇನ್ನೂ ಅಗತ್ಯ.

## ಈಗ ಬಳಸಬೇಕಾದ ಕಡತಗಳು

| ಕಡತ ಅಥವಾ directory | ಬಳಕೆ |
|---|---|
| `submission/gaade.csv` | ಸಲ್ಲಿಕೆಗಾಗಿ 200 ಗಾದೆಗಳ ಮುಖ್ಯ ಕ್ಷೇತ್ರಗಳು |
| `submission/situations.csv` | `gaade_id` ಮೂಲಕ ಜೋಡಿಸಿದ 400 ದ್ವಿಭಾಷಾ ಸಂದರ್ಭಗಳು |
| `submission/metadata.csv` | ಮೂಲ category, source, ಅನುವಾದ ಮತ್ತು ಪ್ರದೇಶದ ಸ್ಥಿತಿ |
| `submission/validation.json` | ಎಣಿಕೆಗಳು ಮತ್ತು CSV hash ಮೌಲ್ಯಗಳು |
| `situations-bilingual.jsonl` / `.csv` | 400 ಸಂದರ್ಭಗಳ ಕನ್ನಡ/ಇಂಗ್ಲಿಷ್ export |
| `situations-complete.jsonl` / `.csv` | ಮೂಲ ಉದಾಹರಣೆ ಮತ್ತು ಹೆಚ್ಚುವರಿ ರಚಿಸಿದ ಸಂದರ್ಭದ ಜೋಡಿ; ಎಲ್ಲ ಪಠ್ಯಗಳು ದ್ವಿಭಾಷೆಯಾಗುವ ಮುಂಚಿನ ಮೂಲ ರೂಪ |

ಪ್ರತಿ ಸಂದರ್ಭಕ್ಕೆ `gaade_id` ಮತ್ತು ಸ್ಥಿರ `situation_id` ಇವೆ. ದ್ವಿಭಾಷಾ CSVಯ ಒಂದೇ ಸಾಲಿನ Kannada/English ಪಠ್ಯಗಳು ಒಂದೇ ಸಂದರ್ಭ; ಎರಡು ಪ್ರತ್ಯೇಕ ಸಂದರ್ಭಗಳೆಂದು ಎಣಿಸಬೇಡಿ.

[ಸಲ್ಲಿಕೆ README](submission/README.md)ಯಲ್ಲಿ ಕ್ಷೇತ್ರಗಳ ವಿವರ, ಪ್ರಸ್ತುತ ಎಣಿಕೆಗಳು ಮತ್ತು ಉಳಿದ ಕೊರತೆಗಳಿವೆ. Main submission CSVಯ 200 ಪ್ರದೇಶಗಳು random demo ಮೌಲ್ಯಗಳು; ಪ್ರತಿಯೊಂದಕ್ಕೂ synthetic ಗುರುತು ಇದೆ. Backendನಲ್ಲಿ ನಿಜವಾದ ಪ್ರದೇಶಗಳು ದಾಖಲಾಗಿಲ್ಲ.

## ಹಳೆಯ evaluation ಕಡತಗಳು

`situations-labeled.csv`, `situations-labeled.jsonl` ಮತ್ತು `situations-evaluation.jsonl`ಗಳನ್ನು ಹಿಂದಿನ evaluationಗಾಗಿ ಹಾಗೆಯೇ ಉಳಿಸಲಾಗಿದೆ:

- ಒಟ್ಟು 108 draft ಪ್ರಕರಣಗಳು: 50 ಗಾದೆಗಳಿಗೆ 100 positive ಉದಾಹರಣೆಗಳು ಮತ್ತು 8 no-match ಪ್ರಕರಣಗಳು.
- ಭಾಷೆವಾರು 54 Kannada, 54 English.
- Label ಸ್ಥಿತಿ: `DRAFT_EDITORIAL_REQUIRES_NATIVE_SPEAKER_REVIEW`.
- ಹಳೆಯ local retrieval ಫಲಿತಾಂಶ: 76/108 pass; 32 fail. `retrieval-results.json`ನಲ್ಲಿ ವಿವರಗಳಿವೆ.

ಇದು ಪ್ರಸ್ತುತ 200 ಗಾದೆಗಳು ಅಥವಾ cloud providerಗಳ ಸಾಮಾನ್ಯ accuracy ಅಳತೆಯಲ್ಲ. ಹಲವು ಭಾಷಾ ಜೋಡಿಗಳು ಒಂದೇ ಸಂದರ್ಭದ ರೂಪಾಂತರಗಳಾಗಿವೆ. ಹೊಸ 400 ಸಂದರ್ಭಗಳ ಸಂಗ್ರಹಕ್ಕೂ ಹಳೆಯ ಉದಾಹರಣೆಗಳಿಗೂ overlap ಇದೆ; ಇವುಗಳನ್ನು ಸ್ವತಂತ್ರ training/test splits ಎಂದು ಹೇಳಬೇಡಿ.

```sh
# project/ directoryಯಿಂದ, ಸ್ಥಳೀಯ API ಚಾಲನೆಯಲ್ಲಿರುವಾಗ:
.venv/bin/python scripts/evaluate_search.py datasets/situations-evaluation.jsonl
```

ಈ ಕಡತಗಳು E5ಯನ್ನು ಸ್ವಯಂಚಾಲಿತವಾಗಿ fine-tune ಮಾಡುವುದಿಲ್ಲ. ಸಂದರ್ಭ ಕಡತಗಳನ್ನು `import_proverbs.py`ಗೆ ಕೊಟ್ಟು ಗಾದೆಗಳಂತೆ import ಮಾಡಬೇಡಿ.

## 100 ಹೊಸ ಗಾದೆಗಳ import ಇತಿಹಾಸ

`pending-proverbs-2026-11-18.jsonl`ನಲ್ಲಿ ಬಳಕೆದಾರರು ಕೊಟ್ಟ ಎರಡು ಕಡತಗಳ 100 ಮೂಲ ದಾಖಲೆಗಳಿವೆ. Schema ಮತ್ತು NFC/spacing/punctuation ಆಧಾರಿತ duplicate ಪರಿಶೀಲನೆಯ ನಂತರ ಮೊದಲು pending ಆಗಿ import ಮಾಡಲಾಯಿತು. ಬಳಿಕ ಬಳಕೆದಾರರ ಸ್ಪಷ್ಟ ಸೂಚನೆಯಂತೆ review API ಮೂಲಕ ಅನುಮೋದಿಸಲಾಯಿತು. ಈಗ ಸ್ಥಳೀಯವಾಗಿ 200 APPROVED, 0 pending.

ಇದು ಮೂಲ ಪದಗಳು/ಅರ್ಥಗಳ ಸ್ವತಂತ್ರ ಸಾಂಸ್ಕೃತಿಕ ಪರಿಶೀಲನೆಗೆ ಸಾಕ್ಷಿಯಲ್ಲ. ಹೊಸ 100 ಗಾದೆಗಳಿಗೆ ಮಾನವ ಧ್ವನಿ ದಾಖಲೆಗಳನ್ನು import ಮಾಡಿಲ್ಲ. Private approval audit ಮತ್ತು database backupಗಳು `data/`ಯಲ್ಲಿ ಉಳಿದಿವೆ; Gitಗೆ ಸೇರಿಸುವುದಿಲ್ಲ.

## ಮೂಲ, ಭಾಷೆ ಮತ್ತು synthetic ಗುರುತುಗಳು

ಗಾದೆಗಳ website ಉಲ್ಲೇಖಗಳನ್ನು ಉಳಿಸಲಾಗಿದೆ. ಸಂದರ್ಭಗಳು ಲೇಖಕರಿಂದ ರಚಿಸಿದ ನೈಜ ಜೀವನದಂತಿರುವ ಕಲ್ಪಿತ ಉದಾಹರಣೆಗಳು; ಹಿರಿಯರ ಮಾತಿನ ನೇರ ದಾಖಲೆಗಳಲ್ಲ. ಗಾದೆಯ source URL ಅನ್ನು ಆ ಸಂದರ್ಭದ source ಎಂದು ಪರಿಗಣಿಸಬೇಡಿ. Region, dialect ಅಥವಾ collector ಮೂಲವನ್ನು ಊಹಿಸಬೇಡಿ.

ಕನ್ನಡ Unicode ರೂಪದಲ್ಲಿದೆ; CSVಗಳು UTF-8 BOM ಬಳಸುತ್ತವೆ. ಮೂಲ Kannada combining marks ಉಳಿಸಲಾಗಿದೆ. CSVಯಲ್ಲಿನ ಪ್ರದರ್ಶನ ಮುನ್ನುಡಿ ತೆಗೆದುಹಾಕಿದ್ದರೂ draft/synthetic metadata ಹಾಗೆಯೇ ಉಳಿಯುತ್ತದೆ.

## Export ಮತ್ತು hosted ಆವೃತ್ತಿ

```sh
# project/ directoryಯಿಂದ:
.venv/bin/python scripts/export_bilingual_situations.py
.venv/bin/python scripts/export_submission.py
```

ಇವು ಮೂಲ database approval ಅಥವಾ ಪಠ್ಯಗಳನ್ನು ಬದಲಾಯಿಸುವುದಿಲ್ಲ. Submission export ಅನ್ನು ಪುನಃ ನಡೆಸಿದರೆ ಕೈಯಾರೆ ಹಾಕಿದ random ಪ್ರದೇಶಗಳು ತೆಗೆದುಹೋಗುತ್ತವೆ. Translation/display cacheಗಳು ಸ್ಥಳೀಯ private ಕಡತಗಳು; Git push ಮಾಡಿದಷ್ಟರಿಂದ Supabaseಗೆ ನಕಲಾಗುವುದಿಲ್ಲ. Hosted data migration ಪ್ರತ್ಯೇಕ ಕೆಲಸ.

`district-image-updates.json` ಜಿಲ್ಲೆಗಳ ಚಿತ್ರ ಬದಲಾವಣೆಯ mapping ಮಾತ್ರ; ಗಾದೆಯ region metadata ಅಲ್ಲ. Consent, human recordings, peer review ಮತ್ತು reuse rightsಗಳಿಗೆ ಪ್ರತ್ಯೇಕ ಸಾಕ್ಷಿ ಅಗತ್ಯ.
