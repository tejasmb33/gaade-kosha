# Gaadamrutha — audit against all five supplied slides

Updated 18 November 2026 after completing local Kannada translation drafts.

Scope: read-only inspection of local SQLite records, translation caches, narration files, labeled datasets, stored retrieval results, frontend code, and repository documentation. This is not a live production audit, a new matching benchmark, a listening assessment, or cultural approval. No public records or approval states were changed. The supplied slides are the requirement source.

## Requirement comparison

| Requirement | Current evidence | Gap |
|---|---|---|
| 200+ proverbs/idioms | 100 approved database rows with 100 distinct exact Kannada texts | At least 100 more required; textual uniqueness does not establish unique traditional variants or correct meanings |
| Collected from grandparents/neighbours | Sources: Yaksha Deepa 55, Kannadapedia 20, Vishaya 20, LingoDesi 5; contributors empty on all 100 | Existing website-sourced corpus does not establish oral collection; collect genuine speaker provenance |
| Meaning, English equivalent, example | Stored literal/contextual meanings and examples on 100; 100 fingerprint-valid local bilingual draft caches | Draft translations are not independent native-speaker validation; English renderings are not necessarily equivalent English idioms |
| Region and theme | Category on 100; region and dialect on zero | Record genuine region and review coverage against money/work/study/family/friends/character; district explorer is not proverb provenance |
| 400+ situations, two per gaade | 100 positive labels, exactly two each for 50 primary IDs, plus 8 no-match cases | Need at least 300 more positive situations for a 200-entry corpus; existing 50 other proverbs have no primary labeled pair |
| Reliable situation labels | All 108 labels marked DRAFT_EDITORIAL_REQUIRES_NATIVE_SPEAKER_REVIEW | Human review, acceptable alternative matches, and independent unseen cases needed |
| 200+ recorded readings | Recordings table contains zero linked recordings | Need at least 200 human readings, linked one per entry; generated narration does not meet oral collection requirement |
| Audio: 16 kHz mono WAV | Seven local generated narration WAVs found, 24 kHz mono; 100 scripts can be constructed | No compliant human-reading submission corpus established; preserve originals and export 16 kHz mono copies |
| Chatbot: situation → gaade → explanation → speech | Typed search, approved-ID retrieval, optional Gemini/Groq, meanings, relevance, dictionary and narration implemented | Full real-input accuracy and pronunciation quality not established; availability depends on backend/provider |
| Kannada speech input | SearchBox fixes language to en for browser and recorded speech requests | Kannada-first input is not established; language-aware recognition and actual Kannada speaker/browser tests needed |
| Voice output for all entries | 100/100 local Kannada narration scripts valid; button requests and caches audio on demand | Does not mean 100 recordings exist or were listened to; translation, pronunciation, quota and generation failures remain possible |
| Required deliverable: gaade CSV | Approved corpus available as runtime database and deployment JSON | Complete gaade CSV with required fields and stable gaade_id not found |
| Required deliverable: situations CSV | situations-labeled.csv exists; primary_proverb_id and expected_ids used in JSONL | Normalize submission field names/linkage to gaade_id and validate final referential integrity |
| One metadata CSV | No final team submission metadata manifest found | Prepare manifest linking text, audio, contributors, source, consent, region and synthetic status |
| UTF-8 Unicode Kannada | Unicode text used by app and datasets; situation CSV includes UTF-8 BOM | Include final bundle validation; no need for legacy Nudi/Baraha encoding |
| Signed consent from speakers/writers | No consent forms or per-speaker consent references found | Collect actual signed consent; form templates alone would not satisfy this |
| Credit and privacy | Original recordings/admin credentials kept private by design | Contributor fields empty; no completed consent-based export, identity minimization, face/plate review evidenced |
| Peer review by another team | Technical tests and historical automated source audit available | No other-team review or reviewer score evidence found; database APPROVED flag is not proof of independent review |
| Transcript exactly matches audio | No linked human recordings | Need paired transcript/audio review, clipping and duplicate checks |
| Images: JPEG, at least 1280 px | Website includes decorative and district images in varied formats/sizes | If submitted as dataset images, validate dimensions/format, privacy and reuse rights; website assets are not automatically the required dataset |
| Planned CC-BY 4.0 release | No completed dataset release/rights documentation found | Document rights and contributor consent; website source links do not by themselves authorize relicensing |
| Synthetic examples flagged | Situation labels described as authored draft examples in README | Add explicit synthetic/generated flags in final metadata, including generated speech and translation drafts |
| GitHub repository submission | Repository exists | Verify organizer submission and reviewer access; private repository access cannot be assumed |
| Demo video and dataset Google Drive links | No final links evidenced in inspected documentation | Produce video, dataset bundle, accessible links and add submission instructions |
| Required folder team_XX/problem_YY/ | Current project/ layout | Prepare separate submission layout, using actual team/problem identifiers |
| Team 2–4, registration and deadline | Slides specify registration 16 Nov 2026; submission 18 Nov 2026 | Team size, registration, exact cutoff time and submission receipt cannot be verified from repository; confirm directly |

## Technical and evaluation limits

- Saved local retrieval result: 76/108 draft cases passed, 32 failed, approximately 70.4%. All 76 also passed top-1 in that saved file. This is older local development evidence, not current Gemini/Groq accuracy or an independent benchmark.
- No evidence of custom model fine-tuning. The system uses retrieval and configured pretrained/cloud models. Describe the corpus as retrieval/evaluation data rather than a training dataset; document model origins separately.
- Narration scripts read stored Kannada metadata; they are not proof that the cultural interpretation or pronunciation is correct. Translation drafts remain drafts even if the parent proverb is database-approved.
- Cloud features need network and valid provider configuration. Temporary translation failures occurred during preparation. Free hosting sleep and provider quotas can delay a demonstration; current latency was not benchmarked here.
- Local models are optional; hosted architecture differs from the Mac. Do not claim identical offline capabilities on all devices.
- Chat UI stores independent situation turns in component memory, not durable multi-turn reasoning or saved history.
- Local data improvements do not automatically reach Supabase/Render: ignored translation caches are not Git files, and an already-populated cloud database is not reseeded on every deployment.
- Most recent existing checks: backend 39 passed/1 skipped, frontend build passed, isolated dictionary journey passed. These test software behavior with synthetic fixtures, not real microphone accuracy or cultural quality.
- Dataset README and earlier source audit still refer to an earlier 50-entry stage and need updating for final submission.

## Priority by judging rubric

1. Dataset quantity/quality (40%): genuine collection and signed consent; reach 200 entries, 400 reviewed positive situations and 200 linked human readings; complete regions and submission exports.
2. Working prototype (30%): restore/test Kannada voice input, verify current hosted data, exercise unseen situations, unrelated inputs and complete narration on actual devices.
3. Kannada/cultural relevance (20%): native-speaker meaning/usage/pronunciation review and genuine regional diversity. Kannada UI and district map help presentation but do not replace provenance.
4. Documentation/demo (10%): final schema, rights/consent references, model/data provenance, peer-review evidence, correct team folder layout, demo video and accessible submission links.

No predicted judge score is assigned: peer review, collection authenticity, speaker tests and final submission status are not established. The prototype has substantial implemented functionality, while the required original dataset and submission evidence remain incomplete.
