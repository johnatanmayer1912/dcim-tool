# Sync read-only knowledge libraries into .cursor/ via directory junctions (no source edits).
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$cursorDir = Join-Path $root '.cursor'

function Ensure-Junction($link, $target) {
    if (-not (Test-Path $target)) {
        Write-Warning "Skip junction - target missing: $target"
        return
    }
    if (-not (Test-Path $cursorDir)) { New-Item -ItemType Directory -Path $cursorDir | Out-Null }
    if (Test-Path $link) {
        $item = Get-Item $link -Force
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            Write-Host "OK  $link"
            return
        }
        Write-Error "Path exists and is not a junction: $link"
    }
    cmd /c mklink /J "$link" "$target"
    Write-Host "Created junction: $link -> $target"
}

Ensure-Junction (Join-Path $cursorDir 'skills-devin') (Join-Path $root '.devin\skills')
Ensure-Junction (Join-Path $cursorDir 'skills-sickn33') (Join-Path $root 'skillss\antigravity-awesome-skills-main\plugins\antigravity-awesome-skills-claude\skills')
Ensure-Junction (Join-Path $cursorDir 'skills-antigravity-vault') (Join-Path $root 'skillss\antigravity-skills-main\skills')

Write-Host ''
Write-Host 'Building SKILL_CATALOG.json...'
python (Join-Path $root 'scripts\build_skill_catalog.py')
Write-Host 'Done. See AGENTS.md and .cursor/KNOWLEDGE_BASE_INDEX.md'
