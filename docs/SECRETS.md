**Secrets & Environment Variables**

- **Do not commit** plaintext secrets. Use `.env` for local convenience but keep it in `.gitignore`.
- Prefer setting secrets in your OS environment or CI provider (GitHub Actions, Azure, etc.).

Local (PowerShell) quick options

- To set for current PowerShell session only:
  ```powershell
  $Env:SERPAPI_KEY = "your_serpapi_key_here"
  ```

- To persist for the current user (Windows):
  ```powershell
  [Environment]::SetEnvironmentVariable('SERPAPI_KEY', 'your_serpapi_key_here', 'User')
  ```

- Use the included helper script which prompts securely and optionally persists:
  ```powershell
  .\scripts\set-env.ps1 -User
  ```

CI / Deployment

- Add `SERPAPI_KEY` as a secret in your CI or cloud provider (GitHub Actions -> repository settings -> Secrets). Use that secret in workflows and runtime environments instead of storing in repo.

Removing secrets from git history (if accidentally committed)

- If a secret was committed, remove it from history using `git filter-repo` or BFG. Example with `git filter-repo`:
  ```bash
  pip install git-filter-repo
  git filter-repo --invert-paths --path .env
  ```

Notes

- `.env.example` includes placeholders for collaborators.
- `backend/settings.py` loads `.env` via `python-dotenv` but priority should be environment variables provided by the OS or CI.
