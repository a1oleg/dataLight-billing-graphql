# Start the billing GraphQL service.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$python = $env:DSH_PYTHON
if (-not $python) {
    $bundled = "C:\Users\a1ole\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
    if (Test-Path $bundled) {
        $python = $bundled
    } else {
        $cmd = Get-Command python -ErrorAction SilentlyContinue
        if ($cmd) { $python = $cmd.Source }
    }
}
if (-not $python -or -not (Test-Path $python)) {
    throw "Python interpreter not found; set DSH_PYTHON or put python on PATH."
}

$env:PYTHONPATH = (Resolve-Path (Join-Path $root "deps")).Path
if (-not $env:PORT) { $env:PORT = "8765" }

Write-Host "Billing GraphQL -> http://127.0.0.1:$($env:PORT)/"
& $python (Join-Path $root "server.py")
