param(
    [ValidateSet('loukan42', 'azerothl')]
    [string]$Account = 'loukan42',
    [switch]$Git,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$GitHubArguments
)

$ErrorActionPreference = 'Stop'
$sandboxPreviousGhToken = [Environment]::GetEnvironmentVariable('GH_TOKEN', 'Process')
$sandboxPreviousGithubToken = [Environment]::GetEnvironmentVariable('GITHUB_TOKEN', 'Process')
$sandboxRepositoryRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$sandboxCommandExit = 1

try {
    # Select the named stored account, regardless of the shell's active credentials.
    [Environment]::SetEnvironmentVariable('GH_TOKEN', $null, 'Process')
    [Environment]::SetEnvironmentVariable('GITHUB_TOKEN', $null, 'Process')
    $sandboxGithubToken = & gh auth token --hostname github.com --user $Account 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $sandboxGithubToken) {
        throw "Compte $Account indisponible : aucune opération GitHub exécutée."
    }
    [Environment]::SetEnvironmentVariable('GH_TOKEN', ($sandboxGithubToken -join '').Trim(), 'Process')
    $sandboxGithubLogin = & gh api user --jq '.login' 2>$null
    if ($LASTEXITCODE -ne 0 -or ($sandboxGithubLogin -join '').Trim() -cne $Account) {
        throw "Identité GitHub différente de $Account : opération interrompue."
    }
    if (-not $GitHubArguments) {
        throw 'Fournir une commande gh, par exemple : api user --jq .login'
    }
    Push-Location -LiteralPath $sandboxRepositoryRoot
    try {
        if ($Git) {
            # Use the verified account for this Git command only.
            & git -c credential.helper= -c 'credential.https://github.com.helper=!gh auth git-credential' @GitHubArguments
        } else {
            & gh @GitHubArguments
        }
        $sandboxCommandExit = $LASTEXITCODE
    } finally {
        Pop-Location
    }
} finally {
    [Environment]::SetEnvironmentVariable('GH_TOKEN', $sandboxPreviousGhToken, 'Process')
    [Environment]::SetEnvironmentVariable('GITHUB_TOKEN', $sandboxPreviousGithubToken, 'Process')
    $sandboxGithubToken = $null
}

exit $sandboxCommandExit
