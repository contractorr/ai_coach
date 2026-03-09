$ErrorActionPreference = 'Stop'

$root = 'C:\Users\Raj Contractor\Documents\Code\stewardme'

$backendCmd = @'
$env:COACH_HOME='C:\Users\Raj Contractor\Documents\Code\stewardme\eval\ux-audit\coach-home'
$env:PYTHONPATH='C:\Users\Raj Contractor\Documents\Code\stewardme\src'
$env:SECRET_KEY='_1zjVhryb5vKueT8cR5hxoXHXj1bZQZrZLRB29wVHlw='
$env:NEXTAUTH_SECRET='stewardme-local-test-secret'
$env:ANTHROPIC_API_KEY='shared-test-key'
$env:DISABLE_INTEL_SCHEDULER='true'
$env:ADMIN_USER_IDS='credentials:junior_dev'
Set-Location 'C:\Users\Raj Contractor\Documents\Code\stewardme'
.\.venv311\Scripts\python.exe -m uvicorn web.app:app --host 127.0.0.1 --port 8100
'@

$frontendCmd = @'
$env:NEXTAUTH_URL='http://127.0.0.1:3100'
$env:NEXTAUTH_SECRET='stewardme-local-test-secret'
$env:ENABLE_TEST_AUTH='true'
$env:NEXT_PUBLIC_ENABLE_TEST_AUTH='true'
$env:NEXT_PUBLIC_API_URL='http://127.0.0.1:8100'
$env:GITHUB_CLIENT_ID='test'
$env:GITHUB_CLIENT_SECRET='test'
$env:GOOGLE_CLIENT_ID='test'
$env:GOOGLE_CLIENT_SECRET='test'
Set-Location 'C:\Users\Raj Contractor\Documents\Code\stewardme\web'
npm run dev -- --hostname 127.0.0.1 --port 3100
'@

$backend = Start-Process powershell.exe -ArgumentList '-NoProfile','-Command',$backendCmd -PassThru
$frontend = Start-Process powershell.exe -ArgumentList '-NoProfile','-Command',$frontendCmd -PassThru

try {
  for ($i = 0; $i -lt 90; $i++) {
    $ok3100 = $false
    $ok8100 = $false
    try {
      Invoke-WebRequest -UseBasicParsing http://127.0.0.1:3100/login -TimeoutSec 10 | Out-Null
      $ok3100 = $true
    } catch {}
    try {
      Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8100/docs -TimeoutSec 10 | Out-Null
      $ok8100 = $true
    } catch {}
    if ($ok3100 -and $ok8100) {
      break
    }
    Start-Sleep -Seconds 2
  }

  Invoke-WebRequest -UseBasicParsing http://127.0.0.1:3100/login -TimeoutSec 10 | Out-Null
  Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8100/docs -TimeoutSec 10 | Out-Null

  Set-Location $root
  node eval/ux-audit/run-workflows.mjs
}
finally {
  Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue
  Stop-Process -Id $frontend.Id -Force -ErrorAction SilentlyContinue
}
