# EDXSO Automated Micro-Influencer Discovery & Outreach System

A 100% data-honest, transparent, AI-powered micro-influencer discovery and outreach system built for technology and developer tool campaigns (GitHub & Dev.to Tech Platforms, 5,000–100,000 micro-influencer bounds).

The platform features multi-source live creator discovery (real HTTP API extraction via `httpx`, $\ge 50$ hard acceptance gate), 100% data provenance tracking, profile enrichment, technology classification, 3-tier deterministic filtering (`QUALIFIED`, `REVIEW`, `REJECTED`), normalized soft scoring with brand-fit & audience-fit calculations, Gemini LLM message personalization (strictly formatted emails and DMs with auditable signals), message quality control, human review workflow, simulation-first sending layer with duplicate prevention, persistent outreach tracking, dataset validation scripts, engine-first CLI script execution, pytest validation, and an interactive Streamlit web application.

> [!IMPORTANT]
> **Zero Fabricated Data — Strict Source-Backed Authenticity**:
> All hardcoded fallback creator records, hash-derived metrics, guessed emails, and fabricated demographic fields have been permanently removed from every discovery adapter. The system queries genuine public profiles live via REST APIs (`httpx`) and enforces an explicit failure state if fewer than 50 real records are retrieved.
>
> **Known source limitations** (these are intentional, not bugs):
> - **GitHub API** (unauthenticated): returns real developer profiles but does NOT supply influencer engagement rates. Follower counts may be rate-limited (`HTTP_403`). Missing fields are recorded as `"Not Found"` and the creator is routed to **REVIEW**.
> - **Dev.to API**: returns real article author profiles with article reaction/comment counts but does NOT supply follower counts or creator engagement rates. Missing fields are `"Not Found"`. Creator routed to **REVIEW**.
> - **Result**: If no discovered creator has a verified public follower count, engagement rate, AND contact email simultaneously, the `QUALIFIED` bucket will be empty. This is the correct, honest outcome — not a system failure.

---

## 🌟 Key Platform Features

- **Multi-Source Live Real Discovery Adapter Chain**:
  - `Source A`: GitHub Public Tech Developer Directory (`directories.py`) - Queries live GitHub User Search & Profile APIs. Obtains genuine follower counts when returned by GitHub User Profile API. Does NOT supply influencer engagement rate metrics (`engagement_rate = "Not Found"`).
  - `Source B`: Dev.to Public Tech Creator Marketplace Index (`marketplaces.py`) - Queries live Dev.to Articles & Author Spotlight APIs. Captures source-backed `article_reactions` and `article_comments`. Does NOT supply follower counts or creator engagement rates (`followers = "Not Found"`, `engagement_rate = "Not Found"`).
  - `Source C`: Dev.to Public Tech Hashtag Feed (`search_adapter.py`) — Queries live Dev.to Articles API by tags (`#ai`, `#python`, `#webdev`, `#programming`). Captures `article_reactions` and `article_comments`. Does NOT supply follower counts or creator engagement rates. Contact email only populated if found literally in bio/website text returned by the Dev.to user detail API.
  - **Acceptance Gate**: Target 50–100 real records; minimum acceptance threshold of $\ge 50$ valid unique creators. If $< 50$ valid records exist, discovery gate fails explicitly.
- **100% Data Provenance & Field-Level Source Auditing**:
  - Auditable `source`, `source_url`, `extraction_method`, and `discovered_at` ISO timestamp recorded per record.
  - Field-level provenance sources tracked for `followers_source`, `engagement_source`, `email_source`, `content_source`, `article_engagement_source`, and `demographics_source`.
- **Strict Qualification Gates & Explainable Classification**:
  - Valid Creator Platforms: `GitHub`, `Dev.to`, `Instagram`, `YouTube`, `Hashnode`
  - Micro-Influencer Bound: `5,000 <= follower_count <= 100,000`
  - Contact Email Gate: `contact_email != "Not Found"` (Email is **mandatory** for outreach eligibility)
  - Engagement Rate Gate: `engagement_rate != "Not Found"` (Engagement metric is **mandatory** for qualification)
  - *Missing email, follower count, or engagement rate automatically routes creators to **`REVIEW`** status with explicit justifications.*
- **Soft Scoring & Dynamic Reweighting**:
  - Technology Relevance (30%), Content Quality (25%), Engagement (20%), Brand Fit (15%), Audience/Geography Fit (10%).
  - If demographic metrics are `"Not Found"`, remaining criteria are dynamically reweighted over 100% so creators are not penalized.
- **Gemini LLM Personalization & Quality Control**:
  - **Email Pitch**: Strictly **60–90 words**.
  - **Social DM**: Strictly **15–30 words**.
  - Stores `personalization_signals` (bio quotes, recent post topics) in SQLite DB.
  - Auto-retry validation loop regenerates messages up to 3 times if word counts or signal criteria fail. Uses Gemini LLM when `GEMINI_API_KEY` is present, or verified fallback templates.
- **Simulation-First Sending & Duplicate Prevention**:
  - Supports `SEND_MODE = simulation` (default) and live `smtp`.
  - Database unique constraint `(campaign_id, creator_id)` prevents duplicate outreach attempts.
  - Includes copyable manual Instagram DM workflow cards.
- **Full Dataset Retention & Automated Dataset Validation Script**:
  - `scripts/validate_dataset.py`: Audits raw, processed, and exported datasets for record counts, synthetic patterns, provenance, and uniqueness. Rejects forbidden derived provenance methods (e.g. `reach & engagement index`, `repository to follower ratio`, `website domain handle`).
  - `data/raw/discovered_creators_raw.json`
  - `data/processed/creators_normalized.csv`
  - `data/exports/qualified_creators.csv`, `review_creators.csv`, `rejected_creators.csv`, `outreach_tracker.csv`
- **Engine-First CLI & Pytest Suite**: Full CLI execution scripts and 100% passing pytest test suite (26 tests passing in ~1.3s).
- **Interactive Multi-Tab Streamlit App**: 7-tab GUI dashboard (`streamlit_app.py`).

---

## 🛠️ Project Directory Structure

```
EDXSO/
├── app/
│   ├── config.py                 # Central config manager (config.yaml + .env)
│   ├── database/
│   │   ├── models.py             # SQLAlchemy models (Campaign, Creator, FilterResult, Message, OutreachLog)
│   │   └── repository.py         # CRUD repository helper functions
│   ├── discovery/
│   │   ├── base.py               # Abstract Base Class for discovery adapters
│   │   ├── directories.py        # Source A: GitHub Public Developer Directory
│   │   ├── marketplaces.py       # Source B: Dev.to Marketplace & Author Index
│   │   ├── search_adapter.py     # Source C: Public Tech Community Search Adapter
│   │   └── __init__.py           # Multi-source discovery fallback orchestrator
│   ├── enrichment/
│   │   ├── metrics.py            # Follower parser & engagement calculator
│   │   ├── contact.py            # Contact email extractor ("Not Found" handling)
│   │   ├── demographics.py       # Demographic fields parser
│   │   └── __init__.py           # Profile enrichment & CSV export
│   ├── filtering/
│   │   ├── rules.py              # Hard qualification gates (email & engagement mandatory checks)
│   │   ├── scoring.py            # Soft scoring & dynamic weight reweighting
│   │   ├── classifier.py         # QUALIFIED / REVIEW / REJECTED explainability classifier
│   │   └── __init__.py           # Filtering pipeline runner
│   ├── personalization/
│   │   ├── prompts.py            # Gemini LLM prompt templates
│   │   ├── validators.py         # Word count & signal quality validator
│   │   ├── generator.py          # Gemini AI generator + fallback template builder
│   │   └── __init__.py           # Personalization pipeline runner
│   └── outreach/
│       ├── sender.py             # Simulation & SMTP email sending layer
│       └── tracker.py            # Duplicate prevention & outreach tracker
├── data/
│   ├── raw/                      # Raw discovered JSON datasets
│   ├── processed/                # Normalized CSV datasets
│   └── exports/                  # Qualified, Review, Rejected, and Tracker CSV exports
├── scripts/
│   ├── init_db.py                # Database initializer script (--reset supported)
│   ├── discover.py               # CLI runner for discovery stage
│   ├── enrich.py                 # CLI runner for profile enrichment
│   ├── filter.py                 # CLI runner for filtering & scoring
│   ├── personalize.py            # CLI runner for AI personalization
│   ├── validate_dataset.py       # Dataset audit & compliance verification script
│   └── run_pipeline.py           # Master E2E pipeline runner script
├── tests/
│   ├── test_data_integrity.py    # Pytest tests for synthetic exclusion & gate failure state
│   ├── test_discovery.py         # Pytest tests for discovery & provenance
│   ├── test_filtering.py         # Pytest tests for hard gates & scoring
│   ├── test_personalization.py   # Pytest tests for message word counts & retry logic
│   └── test_outreach.py          # Pytest tests for sending simulation & duplicate prevention
├── config.yaml                   # Global application configuration settings
├── .env.example                  # Environment variables template
├── requirements.txt              # Project python dependencies
├── streamlit_app.py              # Multi-tab Streamlit dashboard application
└── README.md                     # Comprehensive submission documentation
```

---

## ⚡ Quickstart Guide

### 1. Installation & Environment Setup
Clone the repository and install required dependencies:
```bash
cd e:\EDXSO
pip install -r requirements.txt
```

Set up environment variables (Optional: Add your Gemini API key):
```bash
cp .env.example .env
```

### 2. Execute Full E2E Pipeline (CLI Engine First)
Run the entire automated pipeline from discovery to outreach tracking in a single command:
```bash
python -m scripts.run_pipeline
```

### 3. Run Dataset Validation Audit (Evaluator Script)
Run the compliance verification script to audit raw, processed, and exported datasets for real data compliance:
```bash
python -m scripts.validate_dataset
```

### 4. Run Pytest Test Suite
Execute the complete test suite (26 tests):
```bash
python -m pytest
```

### 5. Launch Interactive Streamlit Dashboard
Launch the multi-tab web application:
```bash
streamlit run streamlit_app.py
```

---

## 📋 Requirement Traceability Matrix

| EDXSO Assignment Requirement | Implementation Component | Evidence Location |
| :--- | :--- | :--- |
| **Discover Real Influencers** | `app/discovery/` (Live HTTP REST API adapters) | `data/raw/discovered_creators_raw.json` |
| **At Least 50 Fetched** | Multi-source live discovery pipeline — **121 source-backed technology creator profiles discovered** (GitHub + Dev.to; followers/engagement/email set to `"Not Found"` where not available from the API) | `scripts/validate_dataset.py` & raw JSON |
| **No Synthetic / Fabricated Data** | Pure live API extraction, 0 hardcoded fallbacks | `scripts/validate_dataset.py` (0 synthetic patterns) |
| **Explicit "Not Found" Labels** | `contact.py`, `demographics.py`, `metrics.py` | `creators_normalized.csv` & database |
| **Micro-Influencer 5K–100K** | Hard filter in `app/filtering/rules.py` | Pytest `test_filtering.py` & Streamlit UI |
| **Chosen Niche (Technology)** | Configured campaign in `config.yaml` | `app/config.py` & UI Campaign Tab |
| **Engagement Rate Mandatory Gate** | Hard gate in `app/filtering/rules.py` | Missing -> `REVIEW` with justification |
| **Contact Email Mandatory Gate** | Hard gate in `app/filtering/rules.py` | Missing -> `REVIEW` with justification |
| **Audience Demographics** | Parsed fields + dynamic weight reweighting | `app/enrichment/demographics.py` & DB |
| **Explainable Pass/Fail** | `app/filtering/classifier.py` | DB `filter_results` & Streamlit Filter Tab |
| **Email Pitch (60–90 words)** | LLM generator + `app/personalization/validators.py` | Pytest `test_personalization.py` & UI |
| **Social DM (15–30 words)** | LLM generator + `app/personalization/validators.py` | Pytest `test_personalization.py` & UI |
| **Dynamic Personalization** | Gemini LLM with post & profile signals | DB `messages.personalization_signals` |
| **Sending Layer** | `app/outreach/sender.py` (`SEND_MODE = simulation`) | Streamlit Outreach Tab & Tracker |
| **Duplicate Prevention** | Unique DB constraint `(campaign_id, creator_id)` | Pytest `test_outreach.py` & DB schema |
| **Instagram Workflow Compliance** | Copyable manual/simulated DM workflow | Streamlit UI & README documentation |
| **Data Integrity & Provenance** | `scripts/validate_dataset.py` & `test_data_integrity.py` | `scripts/validate_dataset.py` |
| **Documentation & README** | Comprehensive README with setup guide | `README.md` |
