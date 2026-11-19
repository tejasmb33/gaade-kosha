# ಹಿಂದಿನ ತಾಂತ್ರಿಕ ಟಿಪ್ಪಣಿಗಳು · Technical history

ಈ ದಾಖಲೆ 19 ನವೆಂಬರ್ 2026ರ README ಪರಿಷ್ಕರಣೆಗೆ ಮುಂಚಿನ ಟಿಪ್ಪಣಿಗಳನ್ನು ಉಳಿಸುತ್ತದೆ. ಇಲ್ಲಿನ ಹಳೆಯ ಎಣಿಕೆಗಳು, ಮಾದರಿಗಳ ಸ್ಥಿತಿ ಮತ್ತು ಪರೀಕ್ಷಾ ಫಲಿತಾಂಶಗಳನ್ನು ಪ್ರಸ್ತುತ ಸ್ಥಿತಿಯೆಂದು ಪರಿಗಣಿಸಬೇಡಿ. ಪ್ರಸ್ತುತ ವಿವರಗಳಿಗೆ [ಮುಖ್ಯ README](../README.md) ನೋಡಿ.

# ಗಾದೆಕೋಶ · GAADE KOSHA

A local Kannada proverb archive with human review. The public database starts empty: no sourced dataset was supplied. AI retrieves existing approved records; it never creates proverbs.

## Run locally

Prerequisites: Python 3.12, Node/npm, FFmpeg/ffprobe. On this Mac, Python 3.12.10 was present; Node and FFmpeg were installed with Homebrew.

```sh
cd /Users/tejasmb/Desktop/modalapada/project
.venv/bin/python -m pip install -r backend/requirements.txt
npm ci --prefix frontend
.venv/bin/python scripts/dev.py --check
.venv/bin/python scripts/dev.py
```

Open http://localhost:5173. API documentation: http://localhost:8000/docs.
The launcher reads `.env` as plain configuration; exported variables take precedence. It generates a private `data/admin-token` when `ADMIN_TOKEN` is empty. Copy that token locally into the Review view; never share or commit it. Ctrl+C stops both services.

Manual startup, in separate terminals:

```sh
# Export desired configuration first: direct uvicorn does not read .env.
.venv/bin/python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
npm run dev --prefix frontend -- --host 127.0.0.1
```

## Local model setup

```sh
.venv/bin/python -m pip install -r backend/requirements-ai.txt
.venv/bin/python scripts/download_models.py --inspect
.venv/bin/python scripts/download_models.py --download
.venv/bin/python scripts/check_models.py
# Optional: actual Kannada speech execution, followed by human transcript review
.venv/bin/python scripts/check_models.py --speech-sample /absolute/path/to/kannada.wav
```

Downloads happen only with the explicit `--download` command. Runtime sets Hugging Face/Transformers offline mode, E5 uses `local_files_only=True` and `trust_remote_code=False`, and speech requires local configuration and weight files. No paid API or key is needed. `.env` sets `E5_MODEL_PATH` and `WHISPER_MODEL_PATH` to the downloaded directories. Restart the launcher after configuration changes.

Selected immutable snapshots (upstream inspected on 2026-11-17):

| Model | Revision | Selected weights | Bytes |
| --- | --- | --- | ---: |
| intfloat/multilingual-e5-small | `614241f622f53c4eeff9890bdc4f31cfecc418b3` | `model.safetensors` | 470,641,600 |
| mlx-community/whisper-small-mlx | `45f3915923c7a79a5a5b5a7d909d39aeb0e5630e` | `weights.npz` | 481,307,592 |

Total selected weights: **951,949,192 bytes**. All selected upstream files, including tokenizers/configuration/cards: **974,601,029 bytes** (about 975 MB decimal). Tiny locally generated evidence manifests add to that total. No duplicate ONNX, OpenVINO, or PyTorch weight variants are selected.

E5's [pinned model card](https://huggingface.co/intfloat/multilingual-e5-small/blob/614241f622f53c4eeff9890bdc4f31cfecc418b3/README.md) documents MIT licensing. The [MLX conversion card](https://huggingface.co/mlx-community/whisper-small-mlx/blob/45f3915923c7a79a5a5b5a7d909d39aeb0e5630e/README.md) omits a licence field; the original publisher's [pinned Whisper documentation](https://github.com/openai/whisper/blob/86098128c0b4f24f0e2aa2994de830614b474227/README.md#license) explicitly releases the code and model weights under MIT. The downloader records this distinction.

The downloader inspects exact upstream metadata, pins commit SHAs, checks declared sizes and authoritative LFS SHA-256/Git blob checksums, and counts existing files including stale variants against a 2,000,000,000-byte budget. HTTPS certificate validation stays enabled. Evidence is written to ignored `models/model-evidence.json` and each model's `revision.json`.

E5 prefixes are `query: ` and `passage: `. Vectors are normalized; passage cache keys include snapshot evidence and stored record content. Keyword retrieval uses FTS5 with encoded Unicode-aware whole words to preserve Kannada vowel signs/virama. Hybrid ranking embeds contextual meanings and bilingual keywords (excluding draft prefixes), and uses semantic cosine with a small whole-word coverage boost (0.015 × coverage). Exact proverb matches rank first. Provisional semantic cutoff is 0.80 with ambiguity and relative-score gates; additional results need at least 0.84. English function words are excluded from lexical coverage; negation is preserved. Keyword-only fallback uses >=0.25 meaningful-word coverage. These heuristics are development-tuned, not broadly calibrated; negation and nuanced cultural use remain limitations.

## Data and audio

Use the contribution page for manual text or original audio. WAV/WebM/MP4 uploads are validated with FFmpeg; original audio and original machine transcript remain separate from contributor corrections. Recordings are private and retained locally for moderation. Microphone access requires localhost or HTTPS. All contributions and imports begin pending; source verification and explicit approval are required for publication.

Import UTF-8 JSONL with `scripts/import_proverbs.py input.jsonl`. Required fields: `proverb_kn`, `literal_meaning`, `contextual_meaning`. Optional: `transliteration`, `example_usage`, `category`, `keywords` (string), `region`, `dialect`, `source`, `contributor`. Status cannot bypass review. Supply genuine source material, and keep undocumented region/dialect empty.

Evaluate supplied real cases with `scripts/evaluate_search.py cases.jsonl`, one `{"query":"…","expected_ids":["…"]}` per line. An empty `expected_ids` list expects no result. Zero cases fail evaluation.

## Validation and limitations

Model regression checks: `.venv/bin/python -m pytest backend/tests/test_models.py -q`.
Offline execution checks: `.venv/bin/python scripts/check_models.py`.
Frontend production build: `npm run build --prefix frontend`.

Four model regression tests pass: embedding cache reuse/content invalidation, keyword fallback on a known model failure, one-attempt-only failed model loading, and checksum validation (see the smoke-check output for actual inference). Test fixtures never populate the real collection. Real cultural retrieval evaluation needs reviewed data. Synthetic silence only verifies speech execution; it does not validate real Kannada speech accuracy.

### Actual model validation on this Mac (2026-11-17)

- Offline E5 Kannada/English encoding passed (384 dimensions, unit norms). Real passage-cache reuse and content invalidation passed.
- Whisper MLX weights loaded on `Device(gpu, 0)`; Kannada-language inference on one second of synthetic silence passed.
- Isolated audio API upload/transcription/submission passed, including retention, protected access, corrected text separation, empty public collection, and submitted-recording retranscription conflict.
- Model directory total: **974,616,119 bytes**, including evidence manifests; no extra weight formats downloaded.
- Four model unit regression tests passed; `pip check` passed. Installed Python versions are recorded in `backend/requirements-local.lock.txt`.
- Models configured in local ignored `.env`; launcher restarted.
- **Not validated:** real Kannada speech accuracy, real proverb relevance, calibrated semantic thresholds. No real speech sample or reviewed dataset was supplied.

The original broader project acceptance suite remains unfinished; these results specifically cover model setup and execution.

### Recording repair (2026-11-17)

Recording now shows microphone permission state, elapsed time, device name and input activity, rejects empty captures, surfaces recorder errors inside the audio panel, stops tracks on stop/unmount, and handles Chrome WebM's initially missing duration for playback. VS Code previews may restrict microphone access: open http://localhost:5173/#contribute in Chrome or Safari and grant browser/macOS microphone access.

Browser checks: `node frontend/tests/recording.cjs` (requires matching Playwright Chromium). To reuse another installed Chromium, set `PLAYWRIGHT_CHROMIUM_EXECUTABLE` to its executable path. Checks use a fake microphone and isolated temporary database on ports 15173/18123; they test playback, real FFmpeg-validated upload, microphone denial, empty output, navigation cleanup and absence of JavaScript errors. They do not validate the user's physical microphone or real Kannada transcription accuracy.

## Situation voice input

The home and search-result inputs include a microphone and a Kannada/English language selector. Kannada defaults to **ಸ್ಥಳೀಯ ಧ್ವನಿ · Local** in every browser. Switching to English selects **ನೇರ ಧ್ವನಿ · Browser** when supported; switching back to Kannada restores local transcription. Browser recognition remains manually selectable, using Web Speech recognition with `kn-IN` or `en-IN`. Press the microphone, speak, and press again to stop; recognized text appears directly in the editable situation field. No API key is used. Browser speech may send audio to its recognition service and require internet; availability and accuracy depend on the browser. Permission, network, unsupported-language and no-speech errors allow retry. Navigation aborts recognition.

Choose **ಸ್ಥಳೀಯ ಧ್ವನಿ · Local** for the existing recording workflow (also the default in Safari or when browser recognition is unavailable): record, stop, choose **Use voice as text**, correct the transcript, and search. **Translate speech to English** uses the installed multilingual Whisper model's translation task. It does not provide English-to-Kannada or typed-text translation; both languages already work directly with multilingual search.

`POST /api/search/voice` accepts multipart `file`, `language` (`kn`/`en`), and `task` (`transcribe`/`translate`). This is independent of proverb contributions: audio stays in a temporary directory and is removed after inference, without creating a recording/database row. Limits remain 10 MB/90 seconds with FFmpeg content validation. Model failure leaves typed search usable.

Validation: ten backend model/voice tests pass; isolated fake-device browser checks cover editable Kannada dictation, English speech translation controls, corrected-query search and 390px layout (ASR text mocked), alongside the contribution recording checks. Real-model execution uses synthetic audio; real bilingual speech/translation accuracy remains outstanding.

Kannada speech translation is experimental. For the reported “manege ba” → “bye” error, situation inference now uses deterministic zero-temperature decoding and exposes an independent original-language transcript beside the English output. You can edit that transcript and use it directly in multilingual search. This does not translate corrected text or guarantee correct English. Eleven backend tests pass, including preservation of the original transcript when mocked English output is wrong; real accuracy needs the original speech recording.

## Retrieval tuning (2026-11-17)

E5 now embeds contextual meanings and bilingual keywords separately from distracting literal imagery and editorial labels. New cache keys version the passage format, so old cached vectors cannot be mistaken for new ones. Missing passage vectors are encoded in a batch and then reused. Exact proverb matches are retained, common English words no longer inflate lexical coverage, and weak/ambiguous semantic candidates can return no match. Explanations quote the stored contextual meaning rather than generating cultural claims.

`evaluations/development.jsonl` contains 15 author-created development cases based on the existing approved collection (11 positive situations, including Kannada/English, and 4 unrelated/no-match cases). `development-results.json` records actual local E5 execution: 15/15 retrieval and top-1/no-match cases passed. These cases informed tuning, are not a held-out benchmark or native-speaker cultural validation, and should not be described as general accuracy. Re-run against the local server with `.venv/bin/python scripts/evaluate_search.py evaluations/development.jsonl`. Fifteen backend regression tests and the frontend production build also pass.

## Database-connected E5 index (2026-11-17)

The approved SQLite records are indexed with the existing local E5 model. Model weights remain in `models/e5`; embedding arrays live in `data/embeddings`, linked through record content/revision cache keys. A model is not installed inside the SQLite file. Build/reuse the index explicitly with:

```sh
.venv/bin/python scripts/index_search.py
```

Each approved record now has two passage views: contextual meaning plus keywords, and that context plus its approved example usage. Search takes the stronger normalized E5 similarity. Cache format `context-example-v4` invalidates old passage representations and updates when context, keywords or example usage changes. No draft situation-dataset records were imported into production retrieval.

A lower score (>=0.78) can qualify only for a descriptive query with a >=0.02 lead over the next candidate; other provisional gates remain in force. These are heuristics, not calibrated probabilities.

The selected query “I searched the whole room for my phone while it was already in my hand.” and its Kannada dataset counterpart return the intended proverb. Actual E5 checks: 15/15 earlier development cases passed; 76/108 broader draft labels matched and 32 failed (see `datasets/retrieval-results.json`). These results reveal continuing limitations. They are not held-out native-speaker cultural validation, and adding an embedding index does not guarantee a correct proverb for every situation.

## Optional OpenAI / Gemini reasoning and web references

The user's later request authorizes optional cloud reasoning, superseding the original local-only inference requirement for this explicitly selected mode. Local search and speech continue to work without cloud keys. No cloud calls occur from the ordinary `/api/search` endpoint.

Choose **Cloud AI + web fallback** under **Search with** to use `POST /api/search/ai`. The backend sends the situation plus approved catalog metadata to the selected provider, asks for an interpretation and up to three existing IDs, validates IDs against the approved snapshot, and loads the full records from SQLite. It never accepts model-invented/private IDs. Match explanations are visibly AI interpretations, not cultural verification. The current implementation supports catalogs of up to 100 records and a 120,000-character request catalog; larger catalogs use local search until a bounded shortlist is implemented.

If no database match is selected, `GAADE_AI_WEB_FALLBACK=true` enables a separate grounded search request. Only citation URLs from provider grounding metadata are shown, under **Unverified web references**. Generated proverb text and uncited links are discarded. No results are inserted or approved automatically. Gemini's returned search suggestions render inside a sandboxed frame. Sources still need human verification.

Configure the ignored local `project/.env` (do not paste keys into chat):

```dotenv
# Choose openai or gemini.
GAADE_AI_PROVIDER=
# An API model available to your account supporting structured output
# and, when enabled, the provider's web-search tool.
GAADE_AI_MODEL=
OPENAI_API_KEY=
GEMINI_API_KEY=
GAADE_AI_WEB_FALLBACK=false
```

Fill the selected provider/model/key, enable web fallback if desired, and restart `.venv/bin/python scripts/dev.py`. Keys stay in the backend environment; the launcher removes them before starting Vite. API calls may incur provider charges and send situation text/approved metadata outside this Mac. The UI explicitly identifies this optional mode. Missing keys or provider failures expose **Try local search**; no tracebacks or provider credentials are returned.

Official request contracts consulted:
- [OpenAI quickstart](https://developers.openai.com/api/docs/quickstart)
- [OpenAI structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
- [OpenAI web search](https://developers.openai.com/api/docs/guides/tools-web-search)
- [Gemini structured output](https://ai.google.dev/gemini-api/docs/structured-output)
- [Gemini Google Search grounding](https://ai.google.dev/gemini-api/docs/generate-content/google-search)

Validation: 23 backend tests pass, including mocked provider contracts, invalid/private ID rejection, external citation filtering, missing-key fallback and sanitized errors. Production build passed. Live provider quality, account/model compatibility, authentication, quotas, and actual web results are **untested until credentials are configured**. Mocked success is not evidence that the scholarship example will be interpreted correctly by a real provider.

### Selected Gemini free-tier configuration

Configured provider `gemini`, model `gemini-2.5-flash-lite`, and web fallback enabled. Google's pricing/deprecation pages checked on 2026-11-17 list free-tier input/output and limited Google Search grounding for this model; no shutdown is announced. Actual eligibility and quotas depend on the Google project. The app cannot force a billed Google project to use free-tier pricing, so use your free-tier project and review its quotas in AI Studio. No paid model/provider fallback is automatic.

1. Create a key in https://aistudio.google.com/apikey.
2. Set `GEMINI_API_KEY=...` in local `project/.env`; never share the value or commit the file.
3. From project/, run `.venv/bin/python scripts/check_cloud.py` to test the scholarship situation, then restart the launcher. This command performs a real cloud request only if a key is configured.

Use **Cloud AI + web fallback** in the web search controls. Quota exhaustion, missing model access and invalid authentication now produce actionable messages without exposing provider errors or keys. Twenty-six backend tests pass. The initial configuration check confirmed the key is absent and made no live request.

### Live Gemini check outcome

The supplied key authenticated the Google model-list endpoint (HTTP 200), but `gemini-2.5-flash-lite` generation returned HTTP 404 for this project. Local configuration now uses the user's supplied `gemini-flash-latest` alias. Generic generation requests timed out, including a tiny bounded prompt with a 90-second read timeout. Live scholarship matching is therefore not validated; configuration is saved and the app restarted, but inference is not confirmed working. Alias availability/pricing can change; listing a model does not establish generation access or free-tier eligibility. Local search remains available. Never copy keys into documentation, logs or chat; keep them only in local .env.

### Active Gemini model — verified 2026-11-17

Current configuration: `gemini-3.5-flash-lite`; automatic web grounding disabled (`GAADE_AI_WEB_FALLBACK=false`) because Google's current free-tier pricing excludes Search grounding for Gemini 3.x. The earlier Gemini 2.5 choices returned explicit new-user access errors, and the latest alias returned HTTP 503 high demand. The explicit supported model completed a live scholarship/catalog request successfully and selected **ಮನಸಿದ್ದರೆ ಮಾರ್ಗ** first, followed by work/reward proverbs. This is a real single-example success, not a general accuracy benchmark.

When cloud credentials are configured, the home page selects Gemini AI by default and shows the cloud-data notice; Local AI remains selectable. Restart the launcher after changing .env. Free-tier quotas and project billing status are controlled by Google, not this application. There is no automatic model/provider change or automatic paid web call. Official pricing: https://ai.google.dev/gemini-api/docs/pricing#gemini-3.5-flash-lite.

## Additional Groq provider

Groq is available alongside Gemini in **Search with → Groq AI**. Gemini stays the default. The selected hosted model is `openai/gpt-oss-20b`, using Groq's strict JSON-schema chat-completions API; no model weights are downloaded. The existing selection checks still reject invented/private IDs. Automatic web search is disabled for Groq.

Local configuration:

```dotenv
GROQ_API_KEY=
GAADE_GROQ_MODEL=openai/gpt-oss-20b
```

The key is backend-only and removed from the Vite child-process environment. Free-plan eligibility and limits are controlled by your Groq account. No automatic cross-provider failover occurs.

`POST /api/search/ai` accepts optional `provider: "groq"` (also `gemini`/`openai`); omitted provider uses the configured default. Health reports only Groq configuration presence, never credentials. After permission to send the situation/catalog to Groq, a live check can be run with `.venv/bin/python scripts/check_cloud.py --provider groq`.

Official request contract: https://console.groq.com/docs/structured-outputs. Unit tests mock the Groq provider; live verification is reported separately in PROGRESS.md.

Groq live check (2026-11-17): HTTP 200; scholarship situation selected ಮನಸಿದ್ದರೆ ಮಾರ್ಗ first. A first sequence hit the account’s 8,000 TPM limit; the response budget is now 1,500 tokens with low reasoning. The request was retried only after the indicated wait. Broader relevance accuracy and quotas are not established by this one successful example. Twenty-nine backend tests, the isolated provider-selection browser checks and frontend build pass.

## Gaade Dictionary

Open http://localhost:5173/#dictionary or choose **Dictionary** in navigation. Browse approved records in normalized Kannada text order, search by stored words/meanings, filter category and paginate. Open any entry for literal/contextual meanings, relevance, example usage, themes, source, contributor/review metadata and same-category related entries. Region/dialect stay explicitly undocumented when absent. Entries have reloadable `#dictionary/<id>` links; pending/rejected IDs remain inaccessible. Existing detail dialogs also link to complete dictionary entries.

Dictionary information comes from stored approved metadata, without extra AI-generated cultural claims. Draft labels remain visible if still present. Kannada text order uses NFC/code-point ordering rather than a specialist linguistic collation. Keyword filtering is whole-word filtering rather than semantic search; use situation search for AI matching.

Checks: `npm run test:dictionary --prefix frontend` (or set `PLAYWRIGHT_CHROMIUM_EXECUTABLE` to an installed Chromium). This starts isolated services on ports 15174/18124 and seeds explicitly synthetic temporary records. Empty state, ordering/pagination, filters, entry details, source links, focus, deep-link reload, related entries, private-record protection, mobile/tablet layout and no JavaScript errors are covered. Real data remains untouched.

## Bilingual dictionary fields

All 50 current approved entries now have English proverb renderings and Kannada translations of literal/contextual meanings, examples and categories, with Kannada/English keyword lists. Labels, guidance, dates, missing-metadata states and related-entry presentation are bilingual. Original Kannada is preserved. Names, transliteration and source URLs are not invented or silently rewritten; missing region/dialect remains undocumented in both languages.

Translations are separate, versioned `data/translations/<id>.json` artifacts with `MACHINE_TRANSLATION_DRAFT` status, input fingerprint, timestamp and origin. The page explicitly marks them as AI drafts requiring language review. Forty-seven current drafts came from the configured Gemini API; three remaining gaps after provider overload were authored locally with `provider: assistant`. These are translations of existing information, not new verified cultural interpretations or newly approved proverbs. Source records and moderation statuses are unchanged.

`GET /api/proverbs` and details expose a `translation` object when a matching draft exists. `GET /api/categories?bilingual=true` returns English/Kannada category labels; its default string response is unchanged. Dictionary word filtering includes translated text. Changing source fields invalidates the translation fingerprint, so stale translations are hidden.

To inspect missing translation coverage: `.venv/bin/python scripts/translate_dictionary.py`. To explicitly regenerate missing translations via the configured Gemini provider: `.venv/bin/python scripts/translate_dictionary.py --generate`. This sends approved record metadata to Google, uses cached drafts, runs sequentially with pacing, never changes original content, and may encounter provider limits. Cached translations survive restarts and are ignored in Git.

Actual checks: 50/50 live dictionary records contain populated required bilingual fields. Thirty backend tests pass, including cache invalidation and Kannada filtering. Isolated browser tests cover Kannada/English field display, draft notice, focus, filtering, related/deep links and mobile/tablet layout. Production build passes. Native-speaker translation accuracy review remains outstanding.

## Kannada-first hackathon theme

The interface now prioritizes Kannada: the main heading is “ನಿಮ್ಮ ಸಂದರ್ಭಕ್ಕೆ ಸೂಕ್ತ ಗಾದೆ.”, with Kannada navigation, search controls, contribution headings and form labels, dictionary headings, and collection descriptions. English remains secondary. Existing cached Kannada translations appear first on collection/result cards and keep their translation-draft notices.

`frontend/src/kannada-theme.css` applies the hackathon reference's yellow highlights/buttons, cream text and dark maroon/brown reading panels over the existing Hampi photograph. There are no new cloud translation requests for these UI changes. Desktop/mobile visual checks and isolated dictionary/recording/provider journeys passed without horizontal overflow or JavaScript errors; production build and 30 backend tests passed.

## Kannada narration after search

Each result card now has **ವಿವರಣೆ ಕೇಳಿ** (listen), pause/resume, and **ನಿಲ್ಲಿಸಿ** (stop), with native audio controls. Nothing speaks automatically on search; playback begins only after pressing the button. Starting another narration stops the previous one. Navigating away cancels the pending client request and pauses playback.

This Mac's inspected browser voice list contained no Kannada voice. With the user's explicit approval, narration uses the configured Gemini key and `gemini-3.8-flash-lite-tts` with the `Kore` voice. No new local model is downloaded. Only stored approved Kannada proverb/meaning/example/category and documented regional metadata are sent as a verbatim transcript; the search situation, microphone audio, private contributions and moderation token are not sent. The spoken script includes an attribution notice when using translation drafts and never generates new cultural explanations.

`POST /api/proverbs/{id}/narration` requires an approved record and adequate Kannada meaning. It returns WAV audio and caches it under ignored local `data/narrations/` using the narration text/model/voice hash. Repeat plays reuse the cache. Missing Kannada text, absent credentials, provider errors/quotas and invalid audio return recoverable errors. User consent enabled `GAADE_TTS_ENABLED=true`; disable it to prevent generation. `GAADE_TTS_MODEL` defaults to `gemini-3.8-flash-lite-tts`. Cloud generation may still finish/cache after a browser cancels its pending request.

Official speech contract and Kannada model support: https://ai.google.dev/gemini-api/docs/speech-generation. Free-tier availability/quotas are controlled by Google; pricing: https://ai.google.dev/gemini-api/docs/pricing#gemini-3.8-flash-lite-tts.

Actual live check: generated a 24 kHz mono WAV, 43.2 seconds, for ಮನಸಿದ್ದರೆ ಮಾರ್ಗ and retained it locally. This verifies generation and audio format; native-speaker pronunciation/quality review remains outstanding. Thirty-three backend tests pass, including cache reuse/stale-content behavior, private-record rejection, disabled/missing-key handling and safe provider errors. Browser checks use a synthetic WAV to verify click/playback, pause/resume, stop, replay reuse and navigation cleanup; they do not establish Kannada pronunciation quality. Production build passes.

## Independent cloud hosting

See [deployment/README.md](../deployment/README.md) for the prepared GitHub → Vercel/Render/Supabase setup. The Docker backend supports PostgreSQL, private durable audio/narration storage, and opt-in Groq speech. Local SQLite and MLX remain supported. Cloud hosting requires the owner's accounts/environment configuration and verification on the resulting URLs; source preparation alone is not a live deployment.

## Karnataka district explorer

Open `/#districts` from the **ಕರ್ನಾಟಕದ ಜಿಲ್ಲೆಗಳು / Districts** navigation item. The separate page includes 31 selectable SVG districts, the supplied photographs and bilingual reference descriptions, a Kannada/English toggle, searchable district list, keyboard access and responsive detail cards. It works without the backend. Edit [frontend/src/data/karnataka-districts.json](../frontend/src/data/karnataka-districts.json); see [the content/schema and map attribution guide](../frontend/src/data/README.md). Optional history, food, places and culture sections render when populated. Theme variables are scoped in `district-explorer.css`.

### Conversational home

The home page now presents independent situation searches as a chat thread. It reuses the same `/api/search` and `/api/search/ai` endpoints, provider choices, editable speech input, full dictionary details, and Kannada narration. Messages and the sidebar list are held only in component memory; reload/navigation starts a fresh conversation. No cross-turn backend memory or saved favourites are implied. New chat cancels pending search/recording and clears the thread. The original hash search URLs continue to work.

`node frontend/tests/chat.cjs` verifies sequential Kannada/English queries, dynamic responses, provider routing, loading, error/fallback, reset and responsive layout using synthetic API fixtures only. Existing recording checks cover microphone capture/transcription and narration within the chat.

## Single-request situation matching

Gemini/Groq receives the situation and a compact approved-record catalog in a single selection request. The backend validates returned IDs before loading full stored details. Catalogs above 100 entries use short temporary IDs to reduce token use; they are mapped back to database IDs only after validation. No separate proverb-recollection call or unverified model-proverb cards are used. Existing explicitly configured web fallback can still make an additional call when no match exists.

## Consistent bilingual proverb display

Chat cards, detail popups and dictionary entries share `ProverbInformation`: Kannada wording, English equivalent (a rendering, not necessarily a traditional English idiom), Kannada contextual meaning, English contextual meaning, bilingual existing usage example, documented region or an explicit unverified-region fallback, and two separately authored situations each in Kannada and English. Original literal meanings, categories, sources and editorial status remain stored unchanged.

`prepare_bilingual_display.py` inspects coverage by default. Explicit `--generate` sends approved records and their existing situation pairs to the configured Gemini provider in bounded batches. It writes fingerprint-checked `data/bilingual-display/` drafts and supplies missing standard translation caches for narration. Rerunning resumes missing displays. It does not approve, import or change proverb records. Situation and source edits invalidate the associated display cache.

The frontend removes leading editorial phrases (Draft, human verification, ಕರಡು, including combined prefixes) in presentation, without rewriting source text. Generated translations still require linguistic review; removing a presentation prefix does not establish cultural correctness. These ignored local caches are not automatically copied to the hosted database by a Git push.
