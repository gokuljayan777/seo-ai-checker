<#
.\scripts\set-env.ps1 [-Key <string>] [-User]

Prompts for `SERPAPI_KEY` (hidden input) and sets it in the current PowerShell session.
If `-User` is passed, the key will also be saved to the current user's persistent environment variables.

Use:
  # interactive (hidden input) and persistent for current user
  .\scripts\set-env.ps1 -User

  # pass key on command line (not recommended for shared shells)
  .\scripts\set-env.ps1 -Key "your-key-here"
#>

param(
    [string]$Key = $null,
    [switch]$User
)

function Read-SecureStringToPlain {
    param([System.Security.SecureString]$s)
    if ($null -eq $s) { return $null }
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($s)
    try { [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) } finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
}

if (-not $Key) {
    $secure = Read-Host "Enter SERPAPI_KEY (input hidden)" -AsSecureString
    $Key = Read-SecureStringToPlain $secure
}

if (-not $Key) {
    Write-Error "No key provided. Aborting."
    exit 1
}

# Set in current session
$Env:SERPAPI_KEY = $Key
Write-Host "SERPAPI_KEY set in current session."

if ($User) {
    try {
        [Environment]::SetEnvironmentVariable("SERPAPI_KEY", $Key, "User")
        Write-Host "SERPAPI_KEY persisted to current user's environment variables."
    } catch {
        Write-Warning "Could not persist environment variable: $_"
    }
}

Write-Host "Done. To remove from this session: `Remove-Item Env:\SERPAPI_KEY`"
