# One-step setup and launch. Installs prerequisites when missing; saves stay separate.
$ErrorActionPreference = 'Stop'
function Refresh-ToolPath {
    $machinePath = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
    $env:PATH = "$userPath;$machinePath;$env:PATH"
}
Refresh-ToolPath
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        throw 'Windows App Installer (winget) is missing. Install App Installer from Microsoft Store, then run this setup again.'
    }
    Write-Host 'Installing the package manager...' -ForegroundColor Cyan
    & winget install --id astral-sh.uv --exact --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) { throw 'Could not install uv. Copy the error text for help.' }
    Refresh-ToolPath
}
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { throw 'uv could not be located. Reopen Windows Terminal and run setup again.' }
$releaseWheel = if ($PSScriptRoot) { Join-Path $PSScriptRoot 'releases/matchterm-0.1.2-py3-none-any.whl' } else { $null }
$setupTemp = $null
try {
    if ($releaseWheel -and (Test-Path $releaseWheel)) {
        $installSource = $releaseWheel
    } else {
        # Download the source snapshot; Git is not required.
        $setupTemp = Join-Path ([IO.Path]::GetTempPath()) ([Guid]::NewGuid().ToString())
        New-Item -ItemType Directory -Path $setupTemp | Out-Null
        $archive = Join-Path $setupTemp 'matchterm.zip'
        Invoke-WebRequest 'https://github.com/fasaziz/matchterm/archive/4721a1be64bf0d0102d778b46b2af33eda51b9d8.zip' -OutFile $archive
        Expand-Archive -Path $archive -DestinationPath $setupTemp
        $installSource = (Get-ChildItem $setupTemp -Directory | Select-Object -First 1).FullName
        if (-not (Test-Path (Join-Path $installSource 'pyproject.toml'))) { throw 'The downloaded source is incomplete.' }
    }
    & uv tool install --python 3.12 --force $installSource
    if ($LASTEXITCODE -ne 0) { throw 'Installation failed. Copy the error text for help.' }
} finally {
    if ($setupTemp -and (Test-Path $setupTemp)) { Remove-Item -Recurse -Force $setupTemp }
}
& uv tool update-shell
if ($LASTEXITCODE -ne 0) { throw 'Could not update the command path.' }
$toolBin = (& uv tool dir --bin | Out-String).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Could not locate the installed tool.' }
$env:PATH = "$toolBin;$env:PATH"
$launcher = Join-Path $toolBin 'matchterm.exe'
if (-not (Test-Path $launcher)) { throw "MATCHTERM launcher was not found at $launcher" }
Write-Host 'MATCHTERM is ready. Your saves are in %LOCALAPPDATA%\MATCHTERM.' -ForegroundColor Green
& $launcher
