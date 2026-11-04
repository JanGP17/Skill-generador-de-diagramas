function Invoke-DiagramQuality {
  param(
    [Parameter(Mandatory = $true)] [string] $InputJson,
    [Parameter(Mandatory = $true)] [string] $OutputVsdx,
    [Parameter(Mandatory = $true)] [string] $OutputPng,
    [Parameter(Mandatory = $true)] [ValidateSet("pre", "post")] [string] $Stage,
    [string] $Config = "",
    [string] $Disabled = "",
    [string] $TraceManifest = "",
    [string] $ProjectRoot = ""
  )

  $qualityScript = Join-Path $PSScriptRoot "diagram_quality.py"
  if (-not (Test-Path -LiteralPath $qualityScript)) { throw "Missing quality script: $qualityScript" }
  $report = if ($Stage -eq "pre") { "$OutputVsdx.preflight.json" } else { "$OutputVsdx.quality.json" }
  if (Test-Path -LiteralPath $report) { throw "Quality report exists: $report" }
  $arguments = @($qualityScript, "inspect", "--model", $InputJson, "--stage", $Stage, "--out", $report)
  if ($Stage -eq "post") { $arguments += @("--vsdx", $OutputVsdx, "--png", $OutputPng) }
  if ($Config) { $arguments += @("--config", $Config) }
  if ($Disabled) { $arguments += @("--disable", $Disabled) }
  if ($TraceManifest) { $arguments += @("--trace", $TraceManifest) }
  if ($ProjectRoot) { $arguments += @("--project-root", $ProjectRoot) }
  & python @arguments | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "Diagram quality $Stage check failed" }
  return $report
}
