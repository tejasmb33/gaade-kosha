# Labeled situation examples

108 draft evaluation examples: 100 positive situations covering all 50 currently approved proverbs (one English and one Kannada situation each), plus 8 unrelated/no-match examples. Language totals: 54 Kannada and 54 English.

- `situations-labeled.csv`: open in Excel, Numbers or VS Code to browse situations and answers. UTF-8 BOM preserves Kannada in spreadsheet applications.
- `situations-labeled.jsonl`: full labels, database IDs, expected Kannada proverbs, source references and provenance.
- `situations-evaluation.jsonl`: minimal `query` / `expected_ids` format accepted by the search evaluation runner.

These are authored illustrative situations, not historical usage quotations. Proverb text and IDs were copied unchanged from the existing approved local collection on 2026-11-17. Labels use its stored contextual meanings, which still contain draft markers. **A native Kannada speaker should review the situations, translations and expected matches. These are not independent verified cultural ground truth.** Source URLs refer to the proverb records, not to the newly written situations. No database statuses, meanings, or proverbs were changed.

For overlapping meanings, `expected_ids` lists the primary proverb and explicitly selected acceptable alternatives. The primary label is the intended best answer; the existing evaluator accepts any listed ID in the top three. Empty expected IDs mean the app should abstain. Multiple other interpretations may be valid; expand the labels after human review rather than assuming a single proverb is universally correct.

Try examples in http://localhost:5173:

| Situation | Intended proverb |
| --- | --- |
| An unprepared presenter blamed the sound technician for his poor presentation. | ಆಟ ಕೆಟ್ಟರೆ ದೀವಟಿಗೆಯವನ ಸುತ್ತ |
| ಕೈಯಲ್ಲೇ ಇದ್ದ ಮೊಬೈಲನ್ನು ಮರೆತು ಇಡೀ ಕೋಣೆಯಲ್ಲಿ ಹುಡುಕಾಡಿದೆ. | ಕಂಕುಳಲ್ಲಿ ಮಗು ಇಟ್ಟುಕೊಂಡು ಊರೆಲ್ಲ ಹುಡುಕಿದರಂತೆ |
| Saving a small amount every week eventually helped us build a substantial fund. | ಹನಿ ಹನಿ ಕೂಡಿದರೆ ಹಳ್ಳ |
| ಆದಾಯ ಮೀರಿಸಿ ಸಾಲ ಮಾಡುವ ಬದಲು ನಮಗೆ ಕೈಗೆಟುಕುವಷ್ಟು ಖರ್ಚಿನಲ್ಲಿ ಸಮಾರಂಭ ಮಾಡಬೇಕು. | ಹಾಸಿಗೆ ಇದ್ದಷ್ಟು ಕಾಲು ಚಾಚು |

Run evaluation from project/ with the app running:

```sh
.venv/bin/python scripts/evaluate_search.py datasets/situations-evaluation.jsonl
```

Evaluation should reveal failures; labels were not changed to match current model predictions. Format, uniqueness, length limits and references to currently approved database IDs were checked. Subsequent local retrieval execution (2026-11-17) matched 76/108 draft labels; 32 failed. Results are recorded in `retrieval-results.json`. This is development feedback, not an independent cultural accuracy benchmark.

These files are evaluation data, not inputs to `import_proverbs.py`. Importing them as proverbs would be incorrect. They do not fine-tune E5 automatically. IDs are tied to this database; when moving to a new database, remap them using the preserved Kannada proverb text. The earlier 15 tuning examples remain separately under `evaluations/` and overlap conceptually with this collection; do not claim an independent held-out benchmark.
