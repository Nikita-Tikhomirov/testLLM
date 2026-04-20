param(
    [string]$RunRoot = "bench_runs",
    [string]$LiveInput = "harness/live_inputs.json"
)

$ErrorActionPreference = 'Stop'

$harness = 'C:\Users\user\.codex\scripts\harness.cmd'
$benchSet = 'C:\Users\user\.codex\harness\bench_set.json'

if (-not (Test-Path $harness)) {
    throw "Harness launcher not found: $harness"
}
if (-not (Test-Path $benchSet)) {
    throw "Bench set not found: $benchSet"
}
if (-not (Test-Path $LiveInput)) {
    throw "Live input file not found: $LiveInput"
}

$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$runDir = Join-Path (Join-Path (Get-Location).Path $RunRoot) $stamp
New-Item -ItemType Directory -Force -Path $runDir | Out-Null

$smokeOut = Join-Path $runDir 'smoke_report.json'
$runsOut = Join-Path $runDir 'runs.jsonl'
$abOut = Join-Path $runDir 'ab_results.json'
$gateOut = Join-Path $runDir 'gate_summary.json'

foreach ($f in @($runsOut, $abOut, $gateOut)) {
    if (Test-Path $f) {
        Remove-Item -LiteralPath $f -Force
    }
}

& $harness smoke --output $smokeOut
if ($LASTEXITCODE -ne 0) { throw 'smoke failed' }

$bench = Get-Content -Raw -Encoding UTF8 $benchSet | ConvertFrom-Json
$input = Get-Content -Raw -Encoding UTF8 $LiveInput | ConvertFrom-Json

if (-not $input.entries) {
    throw 'live_inputs.json must contain non-empty entries[]'
}

$queues = @{}
foreach ($entry in $input.entries) {
    if (-not $entry.task_id -or -not $entry.mode) {
        throw 'Every entry must include task_id and mode'
    }
    if ($entry.mode -notin @('LOCAL_FIRST', 'CLOUD_ONLY')) {
        throw "Unsupported mode '$($entry.mode)' in input"
    }
    $key = "$($entry.task_id)|$($entry.mode)"
    if (-not $queues.ContainsKey($key)) {
        $queues[$key] = New-Object System.Collections.ArrayList
    }
    [void]$queues[$key].Add($entry)
}

function Invoke-LiveRecord {
    param(
        [Parameter(Mandatory = $true)]$Task,
        [Parameter(Mandatory = $true)]$Entry,
        [Parameter(Mandatory = $true)][string]$RunsPath
    )

    $args = @(
        'live',
        '--task-id', $Task.task_id,
        '--task-type', $Task.task_type,
        '--mode', $Entry.mode,
        '--files-touched', [string]$Entry.files_touched,
        '--risk', $Entry.risk,
        '--local-model-chain', $Entry.local_model_chain,
        '--local-passes', [string]$Entry.local_passes,
        '--retrieval-used', $Entry.retrieval_used,
        '--retrieval-hit-score', [string]$Entry.retrieval_hit_score,
        '--first-draft-sec', [string]$Entry.first_draft_sec,
        '--ready-sec', [string]$Entry.ready_sec,
        '--defects-found', [string]$Entry.defects_found,
        '--success', $Entry.success,
        '--cloud-calls', [string]$Entry.cloud_calls,
        '--cloud-fallback', $Entry.cloud_fallback,
        '--fallback-trigger', $Entry.fallback_trigger,
        '--tests-passed', $Entry.tests_passed,
        '--reason', $Entry.reason,
        '--notes', $Entry.notes,
        '--output', $RunsPath
    )

    if ([bool]$Task.simple_bugfix) {
        $args += '--simple-bugfix'
    }

    & $harness @args
    if ($LASTEXITCODE -ne 0) {
        throw "live failed for $($Task.task_id)+$($Entry.mode)"
    }

    $last = Get-Content -Path $RunsPath -Encoding UTF8 | Select-Object -Last 1 | ConvertFrom-Json
    return $last
}

foreach ($task in $bench.tasks) {
    foreach ($mode in @('LOCAL_FIRST', 'CLOUD_ONLY')) {
        $key = "$($task.task_id)|$mode"
        if (-not $queues.ContainsKey($key) -or $queues[$key].Count -eq 0) {
            throw "Missing live inputs for $key"
        }

        $valid = $false
        while ($queues[$key].Count -gt 0 -and -not $valid) {
            $entry = $queues[$key][0]
            $queues[$key].RemoveAt(0)
            $row = Invoke-LiveRecord -Task $task -Entry $entry -RunsPath $runsOut
            if (-not [bool]$row.invalid_audit) {
                $valid = $true
                break
            }
            Write-Host "Invalid audit for $key, retrying next attempt. Reasons: $($row.invalid_reasons -join ',')"
        }

        if (-not $valid) {
            throw "No valid attempt for $key"
        }
    }
}

& $harness ab --input $runsOut --output $abOut --bench-set $benchSet --require-complete
if ($LASTEXITCODE -ne 0) { throw 'ab failed or incomplete pair coverage' }

& $harness gate --input $abOut --output $gateOut
if ($LASTEXITCODE -ne 0) { throw 'gate failed' }

$ab = Get-Content -Raw -Encoding UTF8 $abOut | ConvertFrom-Json
$gate = Get-Content -Raw -Encoding UTF8 $gateOut | ConvertFrom-Json

if ([int]$ab.pair_count -ne 24) {
    throw "Expected pair_count=24, got $($ab.pair_count)"
}

Write-Host "AB run complete"
Write-Host "run_dir=$runDir"
Write-Host "pair_count=$($ab.pair_count)"
Write-Host "gate_interpretable=$($gate.gate.interpretable)"
Write-Host "gate_verdict=$($gate.gate.verdict)"
