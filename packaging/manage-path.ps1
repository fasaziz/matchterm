param([ValidateSet('Add','Remove')][string]$Action, [Parameter(Mandatory)][string]$Directory)
$ErrorActionPreference = 'Stop'
$current = [Environment]::GetEnvironmentVariable('Path','User')
$parts = @($current -split ';' | Where-Object { $_ -and $_.TrimEnd('\') -ine $Directory.TrimEnd('\') })
if ($Action -eq 'Add') { $parts = @($Directory) + $parts }
[Environment]::SetEnvironmentVariable('Path',($parts -join ';'),'User')
