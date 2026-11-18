# Hackathon requirement audit — 18 November 2026

Scope: supplied challenge screenshot, local SQLite database (read-only), deployment seed, dataset files, frontend/backend code and saved evaluation results. No production database query, live provider test or fresh cultural evaluation was performed. No records were changed.

| Requirement | Evidence | Status / gap |
|---|---|---|
| 200+ proverbs/idioms | 100 distinct Kannada records, all marked APPROVED; deployment seed also has 100 | 50% of minimum; need at least 100 more |
| Collect from elders/neighbours | All 100 cite websites: Yaksha Deepa 55, Kannadapedia 20, Vishaya 20, LingoDesi 5. Contributor field empty for all | Oral collection not evidenced; existing web corpus cannot be claimed as elder-collected |
| Meaning and example per entry | Literal/contextual meaning and example fields filled on 100/100, but all contextual meanings retain draft markers | Present as drafts; native-speaker correctness review still required. Database APPROVED status does not establish cultural validation |
| English equivalent | 83 current, fingerprint-valid translation drafts have proverb_en | Partial. English renderings are not necessarily equivalent English idioms; clarify expected interpretation with organizers |
| Region per entry | 0/100 populated; dialect also 0/100 | Missing; collect actual region, do not infer from district explorer |
| Theme per entry | Category populated on 100/100 | Present, but category taxonomy/coverage needs review against money/work/study/family/friends/character |
| 400+ situations; two per proverb | 100 positive labeled situations covering 50 records, two per record; 8 no-match cases. Another 10 Kannada test situations stored separately | Primary labeled set meets 25% of minimum. Need at least 300 further labeled positives to reach 400; review/de-duplicate separate test examples |
| gaade_id situation links | JSONL uses primary_proverb_id and expected_ids; CSV available | Linked internally; submission schema should normalize to gaade_id and check IDs against final corpus |
| 200+ readings, one per entry | recordings table has 0 rows; no linked approved human recordings. Five cached narration WAVs exist at 24 kHz | Missing oral dataset. Generated explanation audio is not a substitute for elder readings |
| 16 kHz WAV submission audio | Decoder uses 16 kHz temporary processing; narration caches are 24 kHz | No compliant linked reading corpus/export verified; preserve originals and create 16 kHz WAV submission copies |
| Typed situation → proverb → why | Local and optional Gemini/Groq selection, approved-record retrieval, reasons and details implemented | Implemented; correctness remains partially evaluated |
| Voice input | Browser/recorded-audio workflows implemented; SearchBox currently fixes language to en | Partial: Kannada recognition is not established; add language-aware recognition or automatic detection and test actual speakers |
| Voice output | Kannada narration endpoint/player/cache implemented; 83 valid Kannada explanation drafts | Partial coverage; 17 records lack valid translation drafts. Availability depends on configured provider/quota; pronunciation requires listening review |
| Gaade CSV + situations CSV + audio folder | Situation CSV present; corpus packaged as JSON seed; runtime narration folder exists | Complete submission bundle with required fields and gaade_id-matched oral audio not found |
| README with sources / collectors | README and source audit exist; web references present | Partial: collector/elder provenance not documented |
| Consent form for every elder | No consent forms or consent workflow found | Missing; store signed forms privately and reference consent IDs in export |

Saved local retrieval evaluation: 76/108 cases passed (~70.4%). This is an older development result, includes 8 no-match cases, uses draft labels covering 50 records, and does not establish current Gemini/Groq accuracy or independent held-out performance.

Priority: organize genuine oral collection and consent; reach 200 entries; capture 200 readings; complete two reviewed situations per entry; fill regions and English equivalents; export a validated bundle; test Kannada voice and unseen situations with native speakers. Animation and district explorer are additional features, not substitutes for the required corpus.
