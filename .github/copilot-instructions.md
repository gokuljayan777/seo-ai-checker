# SEO AI Checker - AI Agent Guidelines

## Project Architecture

**SEO AI Checker** is a Django + Next.js application that analyzes web pages for SEO quality using rule-based scoring and LLM-powered suggestions.

### Core Data Flow
1. **Frontend** (Next.js) → HTTP POST to `/api/analyze/` with `{"url": "..."}`
2. **Views** (`seo_app/views.py`) → orchestrates the analysis pipeline
3. **Crawler** (`crawler.py`) → fetches HTML, normalizes URL
4. **Parser** (in `crawler.py`) → extracts title, meta, headings, images, word count
5. **Rules Analyzer** (`analyzer_rules.py`) → scores 5 components (title, meta, H1, word count, images)
6. **LLM Analyzer** (`analyzer_llm.py`) → generates JSON suggestions (improved title/meta/H1, SEO summary)
7. **Database** → stores Page and PageAnalysis records with caching

### Key Components

- **`seo_app/models.py`**: `Page` (URL entry) and `PageAnalysis` (analysis result with LLM fields: `llm_suggestions`, `llm_generated_at`, `llm_model`)
- **`seo_app/services/`**: modular service layer (crawler, rule analyzer, LLM integration)
- **Frontend**: Next.js at `frontend/` calls `/api/analyze/` and displays results
- **Backend**: Django 5.2.8 with DRF, CORS enabled, SQLite database

## Critical Workflows

### Running the Application
```powershell
# Backend (Django)
cd d:\seo-ai-checker
env\Scripts\activate
python manage.py runserver  # localhost:8000

# Frontend (Next.js)
cd frontend
npm install
npm run dev  # localhost:3000
```

### Testing Analysis Endpoint
```powershell
# Basic analysis (uses cache if available)
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/analyze/" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"url":"https://example.com"}'

# Force LLM regeneration (ignore cache)
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/analyze/?force_llm=true" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"url":"https://example.com"}'
```

### Environment Configuration
- **`.env` file** (root): `OPENAI_API_KEY`, `LLM_MODEL` (default: `gpt-4o-mini`), `LLM_TIMEOUT` (default: 20s), `LLM_CACHE_DAYS` (default: 7)
- Missing `OPENAI_API_KEY` → LLM suggestions gracefully disabled; only rule-based scoring works

## Project-Specific Patterns

### LLM Integration (Key Difference)
- **Dual OpenAI library support**: code gracefully handles both old (`openai` v0.28) and new (`openai` v1+) API styles
- **JSON extraction**: `_extract_json_from_text()` in `analyzer_llm.py` extracts JSON from LLM response (handles markdown blocks, extra text)
- **Caching by timestamp**: `PageAnalysis.llm_generated_at` tracks when suggestions were generated; `force_llm=true` bypasses cache
- **Graceful degradation**: if OpenAI key missing, analysis still works (no LLM suggestions)

### Rule-Based Scoring
Each rule in `analyzer_rules.py` returns `(points: int, issues: list[str])`:
- **Title**: 0–20 pts (optimal 30–60 chars)
- **Meta Description**: 0–20 pts (optimal 50–160 chars)
- **H1**: 0–15 pts (must have exactly 1)
- **Word Count**: 0–20 pts (optimal ≥800 words)
- **Images**: 0–10 pts (scaled by alt text coverage)
- **Total**: 0–100 pts (sum of components)

### HTML Parsing Strategy
`parse_page()` in `crawler.py` uses BeautifulSoup with fallback logic:
1. Prefer `<main>` or `<article>` for main text extraction
2. Fall back to largest `<div>` or `<section>`
3. If all fail, use `<body>` text
4. Image sources: resolve relative URLs to absolute using `urljoin(base_url, src)`

### LLM Prompt Structure
- `_build_prompt()` in `analyzer_llm.py` injects page metadata (title, meta, H1s, word count, issues, HTML snippet)
- Expects **strict JSON output** with keys: `improved_title`, `improved_meta_description`, `improved_h1`, `seo_summary`, `suggestions`
- Strips markdown/commentary; uses `json.loads()` for parsing

## Integration Points & Dependencies

### External APIs
- **OpenAI API**: called in `generate_suggestions()` (with timeout, retry logic)
- **URLs fetched**: user-provided in POST request; defaults to HTTPS if scheme missing

### Database Queries
- `Page.objects.get_or_create(url=...)` ensures one record per unique URL
- `PageAnalysis` records are created fresh each call (multiple analyses per page allowed)
- Filtering cache: check `pa.llm_suggestions`, `pa.llm_generated_at`, compare age to `LLM_CACHE_DAYS`

### CORS & API Routing
- CORS enabled for all origins (see `MIDDLEWARE` in `settings.py`)
- Single endpoint: `/api/analyze/` (GET info, POST to analyze)
- Frontend calls this from localhost:3000 to localhost:8000

## Common Implementation Patterns

### Adding New Scoring Rules
1. Add function in `analyzer_rules.py` with signature: `def score_<component>(data) -> (int, list[str])`
2. Call from `run_all_rules()`, append to `breakdown` list
3. Ensure max points don't exceed component's allocated budget

### Extending LLM Suggestions
1. Modify `_build_prompt()` to include new metadata
2. Update JSON schema keys in prompt and `_extract_json_from_text()` parsing
3. Update `PageAnalysis.llm_suggestions` model field if adding new top-level keys

### Debugging Analysis Flow
- Check `page.analyses.all()` in Django shell for PageAnalysis records
- Log raw HTML response in `fetch_html()` if parsing issues
- Print `parsed` dict before LLM call to verify extracted data

## File Reference Guide

| File | Purpose |
|------|---------|
| `seo_app/views.py` | Main API endpoint; orchestrates crawler → rules → LLM |
| `seo_app/models.py` | Page and PageAnalysis ORM models |
| `seo_app/services/crawler.py` | HTML fetching and parsing (BeautifulSoup) |
| `seo_app/services/analyzer_rules.py` | Rule-based scoring functions |
| `seo_app/services/analyzer_llm.py` | OpenAI integration and LLM suggestions |
| `backend/settings.py` | Django config, database, CORS, installed apps |
| `backend/urls.py` | URL routing |
| `frontend/src/app/` | Next.js app pages and components |
