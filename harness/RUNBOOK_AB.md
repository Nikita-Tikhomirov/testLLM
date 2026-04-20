# AB Runbook (24x2)

1. Prepare real live metrics in `harness/live_inputs.json` using `harness/live_inputs.example.json` as schema.
2. Run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File harness/run_ab_bench.ps1 -LiveInput harness/live_inputs.json
```

What the script does:
- creates isolated run folder `bench_runs/<timestamp>`;
- runs `smoke`;
- enforces one valid `LOCAL_FIRST` and one valid `CLOUD_ONLY` per task from `C:\Users\user\.codex\harness\bench_set.json`;
- retries same `task_id+mode` immediately with next provided attempt if previous audit is invalid;
- runs `ab --require-complete` and `gate`;
- fails if `pair_count != 24`.
