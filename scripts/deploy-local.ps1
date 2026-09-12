[CmdletBinding()]
param(
    [ValidatePattern('^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,100}$')]
    [string]$Tag = ('local-' + (Get-Date -Format 'yyyyMMddHHmmss')),
    [switch]$BuildOnly,
    [switch]$UseExistingImages
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$repoRoot = Split-Path $PSScriptRoot -Parent
$context = 'order-platform'
$namespace = 'order-platform'

function Invoke-Checked {
    param([string]$Program, [string[]]$Arguments)
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Program failed (exit $LASTEXITCODE). Deployment stopped." }
}
function Get-Volumes {
    $json = Invoke-Checked kubectl @("--context=$context", '-n', $namespace, 'get', 'pvc', '-o', 'json')
    $claims = ($json | ConvertFrom-Json).items
    return (($claims | Sort-Object { $_.metadata.name } | ForEach-Object {
        "$($_.metadata.name)|$($_.metadata.uid)|$($_.spec.volumeName)|$($_.status.phase)"
    }) -join "`n")
}

foreach ($tool in @('docker', 'minikube', 'kubectl')) { Get-Command $tool -ErrorAction Stop | Out-Null }
Invoke-Checked docker @('info', '--format', '{{.ServerVersion}}')
Invoke-Checked minikube @('status', '-p', $context)
Invoke-Checked kubectl @("--context=$context", 'get', 'namespace', $namespace)
Invoke-Checked kubectl @("--context=$context", '-n', $namespace, 'get', 'secret', 'postgres-credentials', 'rabbitmq-credentials', '-o', 'name')
foreach ($dependency in @('postgres', 'rabbitmq')) {
    Invoke-Checked kubectl @("--context=$context", '-n', $namespace, 'rollout', 'status', "statefulset/$dependency", '--timeout=120s')
}
$before = Get-Volumes
Write-Host "Volumes before deployment:`n$before"
$images = [ordered]@{
    'order-service' = 'services/order-service'
    'inventory-service' = 'services/inventory-service'
    'payment-service' = 'services/payment-service'
    'notification-service' = 'services/notification-service'
    'order-platform-frontend' = 'frontend'
}
foreach ($entry in $images.GetEnumerator()) {
    $imageName = "$($entry.Key):$Tag"
    $existing = @(Invoke-Checked minikube @('-p', $context, 'image', 'ls'))
    if ($existing | Where-Object { $_ -match "(^|/)$([regex]::Escape($imageName))$" }) {
        if ($UseExistingImages) { continue }
        throw "Image $imageName already exists. Use a new tag to avoid silently reusing old code."
    }
    if ($UseExistingImages) { throw "Required image $imageName is missing." }
    Invoke-Checked minikube @('-p', $context, 'image', 'build', '-t', $imageName, '-f', $(if ($entry.Key -eq 'order-platform-frontend') { 'Dockerfile' } else { $entry.Value + '/Dockerfile' }), $(if ($entry.Key -eq 'order-platform-frontend') { Join-Path $repoRoot 'frontend' } else { $repoRoot }))
    $available = @(Invoke-Checked minikube @('-p', $context, 'image', 'ls'))
    if (-not ($available | Where-Object { $_ -match "(^|/)$([regex]::Escape($imageName))$" })) {
        throw "Build did not produce $imageName. No application manifests have been applied."
    }
}
if ($BuildOnly) { Write-Host "PASS: all images built and verified for $Tag"; return }
# Render application manifests in memory. Never apply the secret or storage directories.
$documents = foreach ($component in @('order', 'inventory', 'payment', 'notification', 'frontend')) {
    foreach ($file in Get-ChildItem (Join-Path $repoRoot "k8s/$component") -Filter '*.yaml' | Sort-Object Name) {
        $content = Get-Content $file.FullName -Raw
        foreach ($name in $images.Keys) {
            $pattern = '(?m)^(\s*image:\s*)' + [regex]::Escape($name) + ':[^\s]+\s*$'
            $content = [regex]::Replace($content, $pattern, '${1}' + $name + ':' + $Tag)
        }
        $content.Trim()
    }
}
$manifest = $documents -join "`n---`n"
$manifest | & kubectl "--context=$context" -n $namespace apply --dry-run=server -f -
if ($LASTEXITCODE -ne 0) { throw 'Server validation failed. No application manifests applied.' }
$manifest | & kubectl "--context=$context" -n $namespace apply -f -
if ($LASTEXITCODE -ne 0) { throw 'Application apply failed; inspect workloads before rerunning.' }
foreach ($deployment in @('order-service', 'inventory-service', 'payment-service', 'notification-service', 'frontend')) {
    Invoke-Checked kubectl @("--context=$context", '-n', $namespace, 'rollout', 'status', "deployment/$deployment", '--timeout=180s')
}
$after = Get-Volumes
if ($before -ne $after) { throw "PVC identity or binding changed. Inspect storage before proceeding." }
Invoke-Checked kubectl @("--context=$context", '-n', $namespace, 'get', 'pods,pvc')
Write-Host "PASS: application deployed with tag $Tag; PVC identities and bindings unchanged."
Write-Host 'Next: port-forward frontend-service, then run tests/local_scenarios.py (consumes one stock unit).'

