# Implementation plan and progress
- [x] Inspect empty workspace and macOS arm64 / Python 3.12 environment.
- [ ] Implement SQLAlchemy database, private contribution lifecycle, FTS5 and optional local AI.
- [ ] Implement bounded audio validation and transcription workflow.
- [ ] Implement all React views and accessible responsive design.
- [ ] Implement launcher, import, model inspection/download and evaluation tools.
- [ ] Install dependencies; run API, launcher, browser and build checks; fix failures.
- [ ] Record exact model evidence, actual checks, and outstanding real-data validation.

No sourced dataset or real Kannada speech sample was supplied. Public collection starts empty.

## Local model setup — 2026-11-17
- [x] Inspect both upstream artifact lists and immutable revisions.
- [x] Verify E5 MIT metadata and original Whisper publisher's MIT weight licence; note absent licence metadata on MLX conversion card.
- [x] Install sentence-transformers and mlx-whisper; `pip check` reports no broken requirements.
- [x] Configure ignored local `.env` paths and force runtime Hugging Face offline mode.
- [x] Actual E5 offline Kannada/English inference: normalized 384-dimensional vectors.
- [x] Four synthetic model regression tests passed.
- [x] Both snapshots downloaded and checksum-verified; total directory size 974,616,119 bytes.
- [x] Actual MLX Whisper weights loaded on Metal GPU; Kannada-language execution on synthetic silence passed.
- [x] Isolated real-model API workflow passed: original audio retention, transcript/correction separation, pending privacy, protected audio access and blocked retranscription.
- [x] Local launcher restarted with both model paths configured.
- [ ] Real Kannada speech accuracy: no sample supplied.
- [ ] Real cultural/semantic retrieval quality: no reviewed dataset supplied.

Selected upstream files total 974,601,029 bytes; selected weights total 951,949,192 bytes. See MODELS.json for exact revisions and authoritative checksum evidence. No public demonstration records added.

## Recording repair — 2026-11-17
- [x] Empty capture rejection, timer, microphone device/input meter, permission guidance and inline errors.
- [x] WebM playback duration handling; track cleanup on stop/navigation.
- [x] Isolated fake-microphone Chromium checks pass: playable capture, FFmpeg upload, denied permission, empty output, navigation cleanup, no JS errors.
- [x] Frontend production build passed.
- [ ] Physical microphone behavior in user's VS Code preview requires a user recording; fake-device tests cannot establish this.

## Situation voice input — 2026-11-17
- [x] Home/results microphone, Kannada/English language choice, editable local transcription and speech-to-English translation.
- [x] Ephemeral search audio route, bounded FFmpeg validation, model failure fallback, no retained query audio.
- [x] Ten backend tests passed, frontend build passed, isolated Chromium voice/search/mobile journey passed (fake microphone, mocked ASR text).
- [ ] Real Kannada/English speech and translation accuracy requires human speech samples and review.

- [x] Actual MLX situation endpoint execution passed for Kannada/English transcription and speech-to-English tasks using synthetic silence; temporary audio retention checks passed. App restarted on localhost:5173.

## Reported translation error — 2026-11-17
User reported Kannada “manege ba” (ಮನೆಗೆ ಬಾ, “come home”) translated as “bye”. No recording was supplied, so actual acoustic reproduction is outstanding.
- [x] Disable stochastic temperature fallback for situation recognition/translation (temperature=0).
- [x] Return source-language transcription separately from English speech translation.
- [x] Show editable original transcript and an explicit action to search it directly; mark translation experimental.
- [x] Eleven backend tests pass, including mocked reported mismatch preservation; frontend build passed.
- [ ] Measure actual translation accuracy with the user's audio; no accuracy improvement claimed from synthetic tests.

## AI retrieval tuning — 2026-11-17
- [x] Confirm approved collection now contains 50 records; no review statuses changed.
- [x] Diagnose common-word lexical noise and overstrict semantic gate.
- [x] Context/keyword E5 passages, batched cache filling, exact-proverb preservation, semantic-first ranking and conservative abstention.
- [x] 15 backend regressions pass; frontend build passes.
- [x] 15 author-created development cases pass with actual E5 on an isolated snapshot (15/15 top-1/no-match).
- [ ] Held-out/native-speaker relevance evaluation and user-specific failure example remain outstanding. Development cases informed tuning and do not establish general accuracy.

## Labeled situation dataset — 2026-11-17
- [x] Created 108 authored draft examples: 100 positive situations for 50 approved proverbs, 8 no-match cases; Kannada/English balanced.
- [x] Full JSONL, spreadsheet CSV and minimal evaluator JSONL; explicit acceptable alternatives and label provenance.
- [x] Validated JSON, unique case IDs, length limits and all referenced approved database IDs.
- [ ] Native-speaker label/translation review and model evaluation on the 108 cases remain outstanding. No database records or approval statuses changed.

## Database-connected semantic index — 2026-11-17
- [x] Include approved example usage alongside contextual meanings in two cached E5 passage views.
- [x] Add explicit offline `scripts/index_search.py` command; indexed 50 approved records.
- [x] Selected phone-search situation retrieves intended Kannada proverb; earlier 15 development cases pass.
- [x] Broader 108-case draft dataset evaluated: 76 matched, 32 failed; results preserved without changing labels.
- [x] Cache regression includes example-usage edits; no unreviewed dataset labels added to public retrieval.
- [ ] Resolve remaining relevance failures through human-reviewed descriptions and independent queries; correct inference for every situation is not established.

## Optional cloud reasoning / web fallback — 2026-11-17
- [x] Add opt-in OpenAI/Gemini database-ID selection from approved metadata, then optional grounded web-source links on no match.
- [x] Reject invented/private IDs; web findings are visibly unverified and never auto-imported.
- [x] Backend-only keys, environment examples, local fallback, health configuration state.
- [x] 23 backend tests pass (mock provider requests); frontend production build passes.
- [ ] Live API integration/quality remains blocked by provider/model selection and a locally configured API key. No live API request made.

## Gemini selected — 2026-11-17
- [x] Configure gemini-2.5-flash-lite and grounded web fallback in local env/example; preserve all secrets.
- [x] Verify official free-tier model/grounding documentation and current availability; no paid-provider fallback.
- [x] Add check_cloud.py and actionable quota/auth/model errors; 26 backend tests pass.
- [ ] User must create a free-tier project API key and save GEMINI_API_KEY locally. Key absent; no live Gemini request made. Restart/test after key is saved.

## Gemini credential test — 2026-11-17
- [x] Supplied key stored in ignored owner-only .env without echoing.
- [x] Google model-list endpoint authenticated successfully (HTTP 200).
- [ ] Configured gemini-2.5-flash-lite generation returned HTTP 404; switched local configuration to the user's supplied gemini-flash-latest alias.
- [ ] Generation tests are timing out; successful model-list authentication does not establish working inference.
- [x] User explicitly approved sending the scholarship situation and approved catalog to Google after automatic approval review initially rejected that payload.
- [x] Backend regression tests remain 26 passed.

Final live generic test: ReadTimeout after a 90-second timeout. Inference remains unresolved; app restarted with saved local Gemini configuration.

## Gemini activated — 2026-11-17
- [x] Diagnose live errors: old 2.5 models reject new users; latest alias returned 503 high demand.
- [x] Explicit gemini-3.5-flash-lite live scholarship request succeeded, selecting ಮನಸಿದ್ದರೆ ಮಾರ್ಗ first.
- [x] Disable paid-tier-only automatic web grounding for the free-tier configuration.
- [x] Home selects configured Gemini by default, Local AI remains available; overload/timeout messages improved.
- [x] 27 backend tests pass; production build passes.
- [ ] Wider Gemini relevance evaluation and provider-side free-tier eligibility/quotas are not established by one successful call.

## Additional Groq provider — 2026-11-17
- [x] Store supplied key in ignored owner-only .env without displaying it.
- [x] Add Groq strict structured-output adapter with hosted openai/gpt-oss-20b.
- [x] Add independent Groq selection in the UI/API; preserve Gemini default and disallow automatic Groq web calls.
- [x] Backend-only key handling; 29 backend tests pass; production build passes.
- [x] User explicitly approved sending scholarship/catalog metadata to Groq after automatic approval review requested it.
- [x] Isolated browser checks pass for separate Groq selection.
- [x] Live Groq request passed (HTTP 200) after reducing response budget to 1500 tokens with low reasoning and respecting the TPM wait. Scholarship example selected ಮನಸಿದ್ದರೆ ಮಾರ್ಗ first.

## Gaade Dictionary — 2026-11-17
- [x] Dedicated navigation page with approved-only ordered entries, search, category filtering, pagination and deep links.
- [x] Full entry meanings, relevance, example situation, keywords, provenance, contributor/review metadata and related entries; unknown region/dialect explicitly marked.
- [x] Accessible heading focus and responsive mobile/tablet navigation; existing dialogs link to full entries.
- [x] Isolated synthetic browser dictionary journey passed; frontend production build and 29 backend tests pass. No AI calls or collection changes needed.

## Bilingual dictionary — 2026-11-17
- [x] Kannada/English labels and entry field presentation, category filters, keyword lists and related entries.
- [x] Separate fingerprinted draft cache; preserve original records, sources, names and approval status. Hide stale drafts.
- [x] User explicitly approved sending all 50 approved records to Google for translation.
- [x] Final coverage: 50/50 approved entries; 47 Gemini drafts, 3 locally authored AI drafts following provider overload. Provenance retained and draft status visible.
- [x] Live API confirms every record has populated required bilingual fields.
- [x] 30 backend tests, isolated bilingual dictionary browser checks and frontend build pass.
- [ ] Native-speaker review of the translation drafts is outstanding; no new claims of cultural verification.

## Site-wide palace background — 2026-11-17
- [x] Use a local matching copy of the user's supplied palace photograph (different crop; source recorded with the asset).
- [x] Apply a fixed decorative background at 12% opacity, cream base, opaque foreground, readable navigation/forms/cards, and stronger secondary text contrast.
- [x] Production build passes. Desktop/mobile visual checks confirm the image loads, foreground opacity remains 1, no mobile horizontal overflow and no JavaScript errors.

## Kannada-first visual theme — 2026-11-17
- [x] Yellow accents/action buttons, cream text and dark maroon panels inspired by supplied hackathon reference; retain Hampi background.
- [x] Kannada-first hero, navigation, page/dictionary headings, search labels, contribution field labels and footer; English secondary.
- [x] Display existing cached Kannada translations first on home/result cards with draft attribution.
- [x] Build and 30 backend tests pass; isolated dictionary and recording/provider browser journeys pass; desktop/mobile visual check has no overflow or JS errors.

## Kannada narration — 2026-11-17
- [x] Result-card ವಿವರಣೆ ಕೇಳಿ button, pause/resume/stop, one active player, navigation cleanup and inline errors.
- [x] User approved approved-proverb Kannada text/explanation transfer to Google TTS; enabled explicit-request generation with local cache.
- [x] Verbatim stored Kannada script; draft attribution spoken; no generated cultural explanations, query text or original microphone audio sent.
- [x] Real Gemini 3.8 Flash-Lite TTS sample generated: ಮನಸಿದ್ದರೆ ಮಾರ್ಗ, 43.2-second 24 kHz mono WAV.
- [x] 33 backend tests pass; browser playback controls/cache/cleanup pass with synthetic audio; build passes.
- [ ] Native-speaker pronunciation and listening-quality evaluation outstanding.

## Simplified visible copy — 2026-11-17
- [x] Remove narration provider/explanatory text, replay-cache prose and transient Play instructions; retain controls and actionable errors.
- [x] Remove repeated cloud/AI explanations and technical result-mode banners; simplify About to cultural purpose and review policy.
- [x] Keep actual provider choices, functional errors and compact translation-draft status. Presentation-only removal of editorial prefixes leaves original database text unchanged.
- [x] Frontend build and isolated dictionary/recording/narration browser checks pass without JS errors.

## Browser speech input — 2026-11-17

- Added direct Web Speech input for Kannada (`kn-IN`) and English (`en-IN`) using the language selector. No browser API key required.
- Kept selectable local Whisper recording/translation; browsers without SpeechRecognition default to local mode.
- Added editable live transcript, bounded session, recoverable speech errors, and navigation cleanup.
- Validation: frontend build, 33 backend/launcher tests, and isolated recording/search/narration browser journey passed. Browser service mocked for locale/result/error/cleanup tests; real Kannada/English recognition accuracy is not measured by these checks.

## Browser speech failure recovery — 2026-11-17

- Browser error handlers now immediately release the listening state and abort failed sessions, without relying on a later end event.
- Added an explicit retry button that switches to local transcription, retains the spoken language, and starts recording from the user click. No automatic microphone restart.
- Live local health reports speech configured, MLX supported, and no startup error. Physical microphone and real Kannada recognition failure are not reproduced; user browser/error details requested.
- Frontend build and isolated browser journey pass, including simulated network/permission errors without end events and actual fake-device fallback recording.

## Kannada input default — 2026-11-17

- Repeated user reports showed browser recognition still selected and failing. Kannada now defaults to local transcription in all browsers, without user-agent assumptions; switching back to Kannada also restores local mode and transcription (not translation). English selects browser recognition when supported.
- Browser recognition remains an explicit manual option. This change avoids the reported failing service; it does not claim to fix the browser service itself.

## Spoken-language selector removed — 2026-11-17

- User requested removal of only the ಮಾತನಾಡುವ ಭಾಷೆ selector. Removed it and fixed situation voice input to English; voice method/search selectors remain. Typed Kannada input remains supported.

## Karnataka district explorer — 2026-11-17

- Added a separate lazy-loaded `/#districts` page and Kannada-first navigation item.
- Imported all 31 bilingual descriptions from the supplied DOCX and copied the 31 explicitly supplied district photographs. Editable JSON supports custom history, places, food, culture and images. Empty optional sections stay hidden.
- Extracted 31 district shapes from the attributed C1MM/Nayvik CC BY-SA 3.0 Wikimedia map, including Vijayanagara, and checked one-to-one district mapping. The supplied Bengaluru South label uses the Ramanagara shape; geometry is illustrative and not a certified boundary product.
- Added full Kannada/English content switching, hover/focus names, keyboard activation, selected-state highlighting, bilingual district search, mobile selector, focus/scroll to details, close/reopen and image fallback.
- Frontend build and isolated district, dictionary, recording/search/narration browser journeys passed. All 31 actual interior district clicks and image loads checked. Desktop/mobile screenshots inspected; no horizontal overflow or JavaScript errors.

## Default illustrated map and district lift — 2026-11-17

- Added the supplied PNG as the default artistic district-map view, with a bilingual toggle restoring the prior boundary map.
- Preserved 31 district cards, selected district, Kannada/English language, search, mobile selector and keyboard interactions between views. Added an SVG clipped artwork hover/focus layer with slight enlargement/lift and pointer-event isolation. Reduced-motion preference disables animation.
- The raster illustration is not georeferenced; transparent district hotspots are illustrative and may not follow decorative divisions. The original boundary view remains available, and the page labels the artwork accordingly.
- Frontend build and isolated district browser journey pass, including default/toggle state, hover scale, all 31 interior clicks and images, reduced motion, bilingual cards, responsive layout and no JS errors.

## Artwork hover-outline alignment fix — 2026-11-18

- Replaced the stretched geographic artwork hotspots with 31 contours traced from the uploaded PNG’s own white separators in native 1086×1448 image coordinates. Image, hit areas, clip paths and hover outlines now share one coordinate system; the geographic view remains separate.
- Added a reproducible build-time tracing utility and generated artwork-boundary JSON. The original raster image is unchanged. Decorative region identities remain illustrative, with the previous map available for geographic selection.
- Removed dashed selected outlines; retained pop-out motion, selected district, bilingual cards, both map modes and reduced-motion behavior.
- Build and isolated browser checks pass for all 31 regions, image loading, keyboard/mobile controls, map/language state, and hover scaling. Border-pixel regression checks show at least 97% of every region’s vertices within 7 native pixels of the image separators (observed 99–100%). Corrected hover screenshot inspected.
