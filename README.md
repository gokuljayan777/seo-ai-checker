[![CI](https://github.com/gokuljayan777/seo-ai-checker/actions/workflows/ci.yml/badge.svg)](https://github.com/gokuljayan777/seo-ai-checker/actions)

# SEO AI Checker

This repo contains the backend (Django) and frontend (Next.js) for the SEO AI Checker project.

## CI
- A minimal GitHub Actions workflow runs backend tests and frontend build on PRs and pushes to `main`.
- We also run `pre-commit` hooks and scheduled secret scans (gitleaks) and CodeQL analysis.

## Branch protection
- Recommended: Require `CI` and `CodeQL` checks to pass before merging to `main` and enable "Require status checks to pass" and "Require pull request reviews before merging" in GitHub branch protection settings.

## Local development
- Backend: `python -m venv env && env\Scripts\activate && pip install -r requirements.txt -r requirements-dev.txt && python manage.py runserver`
- Frontend: `cd frontend && npm ci && npm run dev`

## Pre-commit
- Install pre-commit: `pip install pre-commit`
- Install hooks: `pre-commit install`
- Run hooks on all files: `pre-commit run --all-files`
