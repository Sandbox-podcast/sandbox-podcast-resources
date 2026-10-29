"""Exercise account isolation without credentials, network access or Git mutations."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


POWERSHELL = shutil.which('pwsh')
HELPER = Path(__file__).with_name('github.ps1').resolve()
HARNESS = r'''
$ErrorActionPreference = 'Stop'
$global:factoryCalls = [Collections.Generic.List[object]]::new()
function global:gh {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
    $global:factoryCalls.Add(@{tool='gh'; arguments=$Arguments})
    $global:LASTEXITCODE = 0
    if ($Arguments[0] -eq 'auth') {
        if ($env:FACTORY_TEST_MISSING -eq '1') { $global:LASTEXITCODE=1; return }
        return 'synthetic-account-token'
    }
    if ($Arguments[0] -eq 'api' -and $Arguments[1] -eq 'user') {
        return $env:FACTORY_TEST_LOGIN
    }
    $global:LASTEXITCODE = [int]$env:FACTORY_TEST_TARGET_EXIT
}
function global:git {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
    $global:factoryCalls.Add(@{tool='git'; arguments=$Arguments;
        verified_token=($env:GH_TOKEN -eq 'synthetic-account-token')})
    $global:LASTEXITCODE = [int]$env:FACTORY_TEST_TARGET_EXIT
}
$env:GH_TOKEN='original-gh-environment'
$env:GITHUB_TOKEN='original-github-environment'
$factoryBeforeLocation=(Get-Location).Path
$factoryExit=0
try {
    $factoryParameters=@{GitHubArguments=@('pr','list')}
    if ($env:FACTORY_TEST_ACCOUNT) { $factoryParameters.Account=$env:FACTORY_TEST_ACCOUNT }
    if ($env:FACTORY_TEST_GIT -eq '1') { $factoryParameters.Git=$true }
    & $env:FACTORY_TEST_HELPER @factoryParameters
    $factoryExit=$LASTEXITCODE
} catch {
    $factoryExit=1
} finally {
    @{calls=@($global:factoryCalls.ToArray());
      gh_restored=($env:GH_TOKEN -eq 'original-gh-environment');
      github_restored=($env:GITHUB_TOKEN -eq 'original-github-environment');
      location_restored=((Get-Location).Path -eq $factoryBeforeLocation)
    } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $env:FACTORY_TEST_RESULT
}
exit $factoryExit
'''


@unittest.skipUnless(POWERSHELL, 'PowerShell 7 requis pour tester le script du dépôt')
class GithubHelperTests(unittest.TestCase):
    def run_helper(self, *, account=None, login='loukan42', missing=False, git=False, target_exit=0):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            harness = root / 'harness.ps1'
            result_path = root / 'result.json'
            harness.write_text(HARNESS, encoding='utf-8')
            env = {**os.environ, 'FACTORY_TEST_HELPER': str(HELPER),
                   'FACTORY_TEST_RESULT': str(result_path), 'FACTORY_TEST_ACCOUNT': account or '',
                   'FACTORY_TEST_LOGIN': login, 'FACTORY_TEST_MISSING': '1' if missing else '0',
                   'FACTORY_TEST_GIT': '1' if git else '0', 'FACTORY_TEST_TARGET_EXIT': str(target_exit)}
            process = subprocess.run([POWERSHELL, '-NoProfile', '-NonInteractive', '-File', str(harness)],
                                     env=env, cwd=root, capture_output=True, text=True, timeout=30)
            result = json.loads(result_path.read_text(encoding='utf-8-sig'))
        self.assertTrue(result['gh_restored'])
        self.assertTrue(result['github_restored'])
        self.assertTrue(result['location_restored'])
        return process.returncode, result['calls']

    def test_default_account_is_still_loukan42(self):
        code, calls = self.run_helper()
        self.assertEqual(code, 0)
        self.assertEqual(calls[0]['arguments'][-1], 'loukan42')
        self.assertEqual(calls[-1]['arguments'], ['pr', 'list'])

    def test_explicit_azerothl_selects_and_verifies_that_account(self):
        code, calls = self.run_helper(account='azerothl', login='azerothl')
        self.assertEqual(code, 0)
        self.assertEqual(calls[0]['arguments'][-1], 'azerothl')
        self.assertEqual(calls[1]['arguments'][:2], ['api', 'user'])
        self.assertEqual(calls[-1]['arguments'], ['pr', 'list'])

    def test_mismatched_identity_blocks_command_without_fallback(self):
        code, calls = self.run_helper(account='azerothl', login='loukan42')
        self.assertNotEqual(code, 0)
        self.assertEqual(len(calls), 2)

    def test_missing_account_blocks_before_identity_and_command(self):
        code, calls = self.run_helper(account='azerothl', missing=True)
        self.assertNotEqual(code, 0)
        self.assertEqual(len(calls), 1)

    def test_unapproved_account_is_rejected_before_any_command(self):
        code, calls = self.run_helper(account='another-account')
        self.assertNotEqual(code, 0)
        self.assertEqual(calls, [])

    def test_git_uses_verified_token_and_command_scoped_helper(self):
        code, calls = self.run_helper(account='azerothl', login='azerothl', git=True)
        self.assertEqual(code, 0)
        self.assertEqual(calls[-1]['tool'], 'git')
        self.assertTrue(calls[-1]['verified_token'])
        self.assertEqual(calls[-1]['arguments'][:4], [
            '-c', 'credential.helper=', '-c', 'credential.https://github.com.helper=!gh auth git-credential'])

    def test_command_failure_is_propagated_and_environment_restored(self):
        code, _ = self.run_helper(account='azerothl', login='azerothl', target_exit=73)
        self.assertEqual(code, 73)


if __name__ == '__main__':
    unittest.main()
