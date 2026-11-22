# Changelog
- Packaged the supplied learner CSV (25 rows, 8 columns) and generated SQLite `learners` table.
- Updated DB lookup to recognize `learner_id`.
- Updated RAG splitting to tiktoken `cl100k_base`, 500-token target and 50-token overlap.
- Added tiktoken dependency.
- Documented that live job matching requires an approved vacancies/requirements source; the supplied CSV only contains learner profiles.
- Kept explicit security limitation: subprocess-based runner is a demonstration, not a secure hostile-code sandbox.
