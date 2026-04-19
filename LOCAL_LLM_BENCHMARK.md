# LOCAL LLM A/B Benchmark

- generated_at: 2026-04-19T05:05:46
- hardware: RTX 3060 Ti 8GB
- tasks: 10 (each run in LOCAL_FIRST and CLOUD_ONLY)

## Environment Readiness
- ollama_list_ok: True
- ready_probe: [?2026h[?25l[1Gв ™ [K[?25h[?2026l[?25l[?2026h[?25l[1G[K[?25h[?2026l[2K[1G[?25hREADY[?25l[?25h

[?25l[?25h
- OllamaServeAtLogon: Ready; last_result=0
- OllamaWatchdog10m: Ready; last_result=0
- watchdog_log_tail: ﻿[2026-04-19 04:16:55] OK: health-check passed | [2026-04-19 04:30:20] OK: health-check passed | [2026-04-19 04:46:02] OK: health-check passed
- D_free_gb: 58.64

## Per-Task Metrics
| Task | Category | LOCAL_FIRST first_draft_sec | LOCAL_FIRST ready_sec | LOCAL_FIRST defects | LOCAL_FIRST iter | LOCAL_FIRST fallback | CLOUD_ONLY first_draft_sec | CLOUD_ONLY ready_sec | CLOUD_ONLY defects | CLOUD_ONLY iter |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|---:|
| T1 | layout | 6.25 | 6.25 | 0 | 1 | no | 5.54 | 5.54 | 0 | 1 |
| T2 | layout | 12.5 | 19.86 | 3 | 2 | no | 6.55 | 6.55 | 0 | 1 |
| T3 | layout | 6.59 | 6.59 | 0 | 1 | no | 6.58 | 6.58 | 0 | 1 |
| T4 | ui_state | 180.0 | 240.05 | 3 | 3 | yes | 3.96 | 11.03 | 3 | 3 |
| T5 | ui_state | 70.76 | 134.23 | 3 | 3 | yes | 3.08 | 9.8 | 3 | 3 |
| T6 | ui_state | 67.64 | 119.94 | 3 | 3 | yes | 4.26 | 11.51 | 3 | 3 |
| T7 | bugfix | 84.83 | 155.33 | 2 | 3 | yes | 2.69 | 2.83 | 0 | 1 |
| T8 | bugfix | 15.59 | 20.1 | 3 | 3 | yes | 2.9 | 6.19 | 1 | 2 |
| T9 | refactor | 39.98 | 55.22 | 3 | 3 | yes | 2.55 | 8.18 | 3 | 3 |
| T10 | refactor | 62.28 | 82.05 | 3 | 3 | yes | 3.24 | 9.35 | 3 | 3 |

## Aggregate
| Mode | Success | First Draft Avg | First Draft Median | Ready Avg | Ready Median | Defects Avg | Defects Median | Iter Avg | Iter Median |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| LOCAL_FIRST | 4/10 | 54.64 | 51.13 | 83.96 | 68.63 | 2.3 | 3.0 | 2.5 | 3.0 |
| CLOUD_ONLY | 5/10 | 4.13 | 3.6 | 7.76 | 7.38 | 1.6 | 2.0 | 2.1 | 2.5 |

## Stability
- local_fail_events: 0
- watchdog_recoveries: 0
- successful_runs_without_manual_intervention_pct: 45.0

## Raw JSON
```json
{
  "checks": {
    "ollama_list_ok": true,
    "ready_probe": "\u001b[?2026h\u001b[?25l\u001b[1Gв ™ \u001b[K\u001b[?25h\u001b[?2026l\u001b[?25l\u001b[?2026h\u001b[?25l\u001b[1G\u001b[K\u001b[?25h\u001b[?2026l\u001b[2K\u001b[1G\u001b[?25hREADY\u001b[?25l\u001b[?25h\n\n\u001b[?25l\u001b[?25h",
    "serve_task_status": "Ready; last_result=0",
    "watchdog_task_status": "Ready; last_result=0",
    "watchdog_log_tail": "﻿[2026-04-19 04:16:55] OK: health-check passed\n[2026-04-19 04:30:20] OK: health-check passed\n[2026-04-19 04:46:02] OK: health-check passed",
    "d_free_gb": 58.64
  },
  "rows": [
    {
      "task_id": "T1",
      "category": "layout",
      "files_count": "2",
      "mode": "LOCAL_FIRST",
      "local_model": "qwen2.5-coder:7b",
      "cloud_model": "none",
      "first_draft_sec": 6.25,
      "ready_sec": 6.25,
      "defects_found": 0,
      "iterations_to_acceptance": 1,
      "cloud_fallback": "no",
      "fallback_reason": "",
      "accepted": true,
      "local_events": ""
    },
    {
      "task_id": "T1",
      "category": "layout",
      "files_count": "2",
      "mode": "CLOUD_ONLY",
      "local_model": "none",
      "cloud_model": "openai/gpt-4o-mini",
      "first_draft_sec": 5.54,
      "ready_sec": 5.54,
      "defects_found": 0,
      "iterations_to_acceptance": 1,
      "cloud_fallback": "no",
      "fallback_reason": "",
      "accepted": true,
      "local_events": ""
    },
    {
      "task_id": "T2",
      "category": "layout",
      "files_count": "2",
      "mode": "LOCAL_FIRST",
      "local_model": "qwen2.5-coder:7b",
      "cloud_model": "none",
      "first_draft_sec": 12.5,
      "ready_sec": 19.86,
      "defects_found": 3,
      "iterations_to_acceptance": 2,
      "cloud_fallback": "no",
      "fallback_reason": "",
      "accepted": true,
      "local_events": ""
    },
    {
      "task_id": "T2",
      "category": "layout",
      "files_count": "2",
      "mode": "CLOUD_ONLY",
      "local_model": "none",
      "cloud_model": "openai/gpt-4o-mini",
      "first_draft_sec": 6.55,
      "ready_sec": 6.55,
      "defects_found": 0,
      "iterations_to_acceptance": 1,
      "cloud_fallback": "no",
      "fallback_reason": "",
      "accepted": true,
      "local_events": ""
    },
    {
      "task_id": "T3",
      "category": "layout",
      "files_count": "2",
      "mode": "LOCAL_FIRST",
      "local_model": "qwen2.5-coder:7b",
      "cloud_model": "none",
      "first_draft_sec": 6.59,
      "ready_sec": 6.59,
      "defects_found": 0,
      "iterations_to_acceptance": 1,
      "cloud_fallback": "no",
      "fallback_reason": "",
      "accepted": true,
      "local_events": ""
    },
    {
      "task_id": "T3",
      "category": "layout",
      "files_count": "2",
      "mode": "CLOUD_ONLY",
      "local_model": "none",
      "cloud_model": "openai/gpt-4o-mini",
      "first_draft_sec": 6.58,
      "ready_sec": 6.58,
      "defects_found": 0,
      "iterations_to_acceptance": 1,
      "cloud_fallback": "no",
      "fallback_reason": "",
      "accepted": true,
      "local_events": ""
    },
    {
      "task_id": "T4",
      "category": "ui_state",
      "files_count": "2",
      "mode": "LOCAL_FIRST",
      "local_model": "qwen2.5-coder:14b",
      "cloud_model": "openai/gpt-4o-mini",
      "first_draft_sec": 180.0,
      "ready_sec": 240.05,
      "defects_found": 3,
      "iterations_to_acceptance": 3,
      "cloud_fallback": "yes",
      "fallback_reason": "validator failures after 2 local attempts",
      "accepted": false,
      "local_events": ""
    },
    {
      "task_id": "T4",
      "category": "ui_state",
      "files_count": "2",
      "mode": "CLOUD_ONLY",
      "local_model": "none",
      "cloud_model": "openai/gpt-4o-mini",
      "first_draft_sec": 3.96,
      "ready_sec": 11.03,
      "defects_found": 3,
      "iterations_to_acceptance": 3,
      "cloud_fallback": "no",
      "fallback_reason": "TypeError: state.todos is not iterable\n    at addTodo (C:\\Users\\user\\AppData\\Local\\Temp\\tmphjj7lpbz\\module.js:5:26)\n    at C:\\Users\\user\\AppData\\Local\\Temp\\tmphjj7lpbz\\test.js:11:12\n    at Object.<anonymous> (C:\\Users\\user\\AppData\\Local\\Temp\\tmphjj7lpbz\\test.js:21:3)\n    at Module._compile (node:internal/modules/cjs/loader:1099:14)\n    at Object.Module._extensions..js (node:internal/modules/cjs/loader:1153:10)\n    at Module.load (node:internal/modules/cjs/loader:975:32)\n    at Function.Module._load (node:internal/modules/cjs/loader:822:12)\n    at Function.executeUserEntryPoint [as runMain] (node:internal/modules/run_main:77:12)\n    at node:internal/main/run_main_module:17:47",
      "accepted": false,
      "local_events": ""
    },
    {
      "task_id": "T5",
      "category": "ui_state",
      "files_count": "2",
      "mode": "LOCAL_FIRST",
      "local_model": "deepseek-r1:8b",
      "cloud_model": "openai/gpt-4o-mini",
      "first_draft_sec": 70.76,
      "ready_sec": 134.23,
      "defects_found": 3,
      "iterations_to_acceptance": 3,
      "cloud_fallback": "yes",
      "fallback_reason": "validator failures after 2 local attempts",
      "accepted": false,
      "local_events": ""
    },
    {
      "task_id": "T5",
      "category": "ui_state",
      "files_count": "2",
      "mode": "CLOUD_ONLY",
      "local_model": "none",
      "cloud_model": "openai/gpt-4o-mini",
      "first_draft_sec": 3.08,
      "ready_sec": 9.8,
      "defects_found": 3,
      "iterations_to_acceptance": 3,
      "cloud_fallback": "no",
      "fallback_reason": "missing tabs.js",
      "accepted": false,
      "local_events": ""
    },
    {
      "task_id": "T6",
      "category": "ui_state",
      "files_count": "2",
      "mode": "LOCAL_FIRST",
      "local_model": "qwen2.5-coder:14b",
      "cloud_model": "openai/gpt-4o-mini",
      "first_draft_sec": 67.64,
      "ready_sec": 119.94,
      "defects_found": 3,
      "iterations_to_acceptance": 3,
      "cloud_fallback": "yes",
      "fallback_reason": "validator failures after 2 local attempts",
      "accepted": false,
      "local_events": ""
    },
    {
      "task_id": "T6",
      "category": "ui_state",
      "files_count": "2",
      "mode": "CLOUD_ONLY",
      "local_model": "none",
      "cloud_model": "openai/gpt-4o-mini",
      "first_draft_sec": 4.26,
      "ready_sec": 11.51,
      "defects_found": 3,
      "iterations_to_acceptance": 3,
      "cloud_fallback": "no",
      "fallback_reason": "missing cart.js",
      "accepted": false,
      "local_events": ""
    },
    {
      "task_id": "T7",
      "category": "bugfix",
      "files_count": "1",
      "mode": "LOCAL_FIRST",
      "local_model": "deepseek-r1:8b",
      "cloud_model": "openai/gpt-4o-mini",
      "first_draft_sec": 84.83,
      "ready_sec": 155.33,
      "defects_found": 2,
      "iterations_to_acceptance": 3,
      "cloud_fallback": "yes",
      "fallback_reason": "validator failures after 2 local attempts",
      "accepted": true,
      "local_events": ""
    },
    {
      "task_id": "T7",
      "category": "bugfix",
      "files_count": "1",
      "mode": "CLOUD_ONLY",
      "local_model": "none",
      "cloud_model": "openai/gpt-4o-mini",
      "first_draft_sec": 2.69,
      "ready_sec": 2.83,
      "defects_found": 0,
      "iterations_to_acceptance": 1,
      "cloud_fallback": "no",
      "fallback_reason": "",
      "accepted": true,
      "local_events": ""
    },
    {
      "task_id": "T8",
      "category": "bugfix",
      "files_count": "1",
      "mode": "LOCAL_FIRST",
      "local_model": "qwen2.5-coder:7b",
      "cloud_model": "openai/gpt-4o-mini",
      "first_draft_sec": 15.59,
      "ready_sec": 20.1,
      "defects_found": 3,
      "iterations_to_acceptance": 3,
      "cloud_fallback": "yes",
      "fallback_reason": "validator failures after 2 local attempts",
      "accepted": false,
      "local_events": ""
    },
    {
      "task_id": "T8",
      "category": "bugfix",
      "files_count": "1",
      "mode": "CLOUD_ONLY",
      "local_model": "none",
      "cloud_model": "openai/gpt-4o-mini",
      "first_draft_sec": 2.9,
      "ready_sec": 6.19,
      "defects_found": 1,
      "iterations_to_acceptance": 2,
      "cloud_fallback": "no",
      "fallback_reason": "",
      "accepted": true,
      "local_events": ""
    },
    {
      "task_id": "T9",
      "category": "refactor",
      "files_count": "1",
      "mode": "LOCAL_FIRST",
      "local_model": "qwen2.5-coder:14b",
      "cloud_model": "openai/gpt-4o-mini",
      "first_draft_sec": 39.98,
      "ready_sec": 55.22,
      "defects_found": 3,
      "iterations_to_acceptance": 3,
      "cloud_fallback": "yes",
      "fallback_reason": "validator failures after 2 local attempts",
      "accepted": false,
      "local_events": ""
    },
    {
      "task_id": "T9",
      "category": "refactor",
      "files_count": "1",
      "mode": "CLOUD_ONLY",
      "local_model": "none",
      "cloud_model": "openai/gpt-4o-mini",
      "first_draft_sec": 2.55,
      "ready_sec": 8.18,
      "defects_found": 3,
      "iterations_to_acceptance": 3,
      "cloud_fallback": "no",
      "fallback_reason": "missing format.js",
      "accepted": false,
      "local_events": ""
    },
    {
      "task_id": "T10",
      "category": "refactor",
      "files_count": "1",
      "mode": "LOCAL_FIRST",
      "local_model": "qwen3:8b",
      "cloud_model": "openai/gpt-4o-mini",
      "first_draft_sec": 62.28,
      "ready_sec": 82.05,
      "defects_found": 3,
      "iterations_to_acceptance": 3,
      "cloud_fallback": "yes",
      "fallback_reason": "validator failures after 2 local attempts",
      "accepted": false,
      "local_events": ""
    },
    {
      "task_id": "T10",
      "category": "refactor",
      "files_count": "1",
      "mode": "CLOUD_ONLY",
      "local_model": "none",
      "cloud_model": "openai/gpt-4o-mini",
      "first_draft_sec": 3.24,
      "ready_sec": 9.35,
      "defects_found": 3,
      "iterations_to_acceptance": 3,
      "cloud_fallback": "no",
      "fallback_reason": "missing classnames.js",
      "accepted": false,
      "local_events": ""
    }
  ],
  "sum_local": {
    "count": 10,
    "success": 4,
    "first_draft_avg": 54.64,
    "first_draft_median": 51.13,
    "ready_avg": 83.96,
    "ready_median": 68.63,
    "defects_avg": 2.3,
    "defects_median": 3.0,
    "iterations_avg": 2.5,
    "iterations_median": 3.0
  },
  "sum_cloud": {
    "count": 10,
    "success": 5,
    "first_draft_avg": 4.13,
    "first_draft_median": 3.6,
    "ready_avg": 7.76,
    "ready_median": 7.38,
    "defects_avg": 1.6,
    "defects_median": 2.0,
    "iterations_avg": 2.1,
    "iterations_median": 2.5
  },
  "stability": {
    "local_fail_events": 0,
    "watchdog_recoveries": 0,
    "success_no_manual_pct": 45.0
  }
}
```