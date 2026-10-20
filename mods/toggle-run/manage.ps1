param(
    [ValidateSet('Install', 'Restore', 'Status')]
    [string]$Action = 'Status',
    [string]$GameDir = 'D:\Program Files (x86)\Steam\steamapps\common\Order of the Sinking Star'
)
$ErrorActionPreference = 'Stop'
$manifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'manifest.json') -Raw | ConvertFrom-Json
$target = Join-Path $GameDir 'sinking_star.exe'
$backup = Join-Path $PSScriptRoot 'sinking_star.original.exe'
function Get-BytesSha([byte[]]$Data) {
    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try {
        return ([System.BitConverter]::ToString($algorithm.ComputeHash($Data))).Replace('-', '').ToLowerInvariant()
    } finally {
        $algorithm.Dispose()
    }
}
function Get-Sha([string]$Path) {
    $stream = [System.IO.File]::OpenRead($Path)
    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try {
        return ([System.BitConverter]::ToString($algorithm.ComputeHash($stream))).Replace('-', '').ToLowerInvariant()
    } finally {
        $algorithm.Dispose()
        $stream.Dispose()
    }
}
$current = Get-Sha $target
if ($Action -eq 'Status') {
    if ($current -eq $manifest.patched_sha256) { Write-Output 'Installed: toggle run patch.' }
    elseif ($current -eq $manifest.original_sha256) { Write-Output 'Original supported game version; patch not installed.' }
    else { Write-Output 'Unknown game version; no files changed.' }
    exit 0
}
if (Get-Process -Name 'sinking_star' -ErrorAction SilentlyContinue) {
    throw 'Close the game before installing or restoring.'
}
if ($Action -eq 'Install') {
    if ($current -eq $manifest.patched_sha256) { Write-Output 'Already installed.'; exit 0 }
    if ($current -ne $manifest.original_sha256) { throw 'Unsupported game version; refusing to overwrite.' }
    # 从玩家本机原程序生成补丁，发行包无需携带完整游戏程序。
    $data = [System.IO.File]::ReadAllBytes($target)
    if ((Get-BytesSha $data) -ne $manifest.original_sha256) { throw 'Game changed during preflight.' }
    $before = [string]$manifest.original_bytes
    $after = [string]$manifest.patched_bytes
    $offset = [int]$manifest.file_offset
    $size = [int]$manifest.size
    if ($before.Length -ne $size * 2 -or $after.Length -ne $size * 2 -or $offset -lt 0 -or $offset + $size -gt $data.Length) { throw 'Invalid patch range.' }
    for ($index = 0; $index -lt $size; $index++) {
        if ($data[$offset + $index] -ne [Convert]::ToByte($before.Substring($index * 2, 2), 16)) { throw 'Original callback mismatch.' }
        $data[$offset + $index] = [Convert]::ToByte($after.Substring($index * 2, 2), 16)
    }
    if ((Get-BytesSha $data) -ne $manifest.patched_sha256) { throw 'Generated patch hash mismatch.' }
    if (Test-Path -LiteralPath $backup) {
        if ((Get-Sha $backup) -ne $manifest.original_sha256) { throw 'Existing backup hash mismatch.' }
    } else {
        [System.IO.File]::Copy($target, $backup, $false)
    }
    if ((Get-Sha $backup) -ne $manifest.original_sha256) { throw 'Backup verification failed.' }
    if ((Get-Sha $target) -ne $current) { throw 'Game changed during preflight.' }
    [System.IO.File]::WriteAllBytes($target, $data)
    if ((Get-Sha $target) -ne $manifest.patched_sha256) { throw 'Installation verification failed; original backup preserved.' }
    Write-Output 'Installed and verified. Original backup preserved in the output folder.'
} else {
    if ($current -eq $manifest.original_sha256) { Write-Output 'Already original.'; exit 0 }
    if ($current -ne $manifest.patched_sha256) { throw 'Game changed since installation; refusing to overwrite.' }
    if ((Get-Sha $backup) -ne $manifest.original_sha256) { throw 'Original backup hash mismatch.' }
    [System.IO.File]::Copy($backup, $target, $true)
    if ((Get-Sha $target) -ne $manifest.original_sha256) { throw 'Restore verification failed.' }
    Write-Output 'Original game restored and verified.'
}
