# Backward-compatible entry — use sync_knowledge_base.ps1
& (Join-Path (Split-Path $MyInvocation.MyCommand.Path) 'sync_knowledge_base.ps1')
