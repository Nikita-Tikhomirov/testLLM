# Cost-First Hybrid Validation Report

- generated_at: 2026-04-19T07:04:56
- hardware: RTX 3060 Ti 8GB
- tasks: 12 x 2 modes

## Smoke/Ready
```text
NAME                              ID              SIZE      MODIFIED          
qwen2.5-coder:7b-instruct-q6_K    764353927508    6.3 GB    About an hour ago    
bge-m3:latest                     790764642607    1.2 GB    2 hours ago          
deepseek-r1:8b                    6995872bfe4c    5.2 GB    2 hours ago          
qwen2.5-coder:14b                 9ec8897f747e    9.0 GB    37 hours ago         
qwen3:8b                          500a1f067a9f    5.2 GB    37 hours ago         
qwen2.5-coder:7b                  dae161e27b0e    4.7 GB    38 hours ago
```
- ready_7b: READY
- ready_q6: READY_Q6
- runtime:
  - OLLAMA_KEEP_ALIVE=30m
  - OLLAMA_MAX_LOADED_MODELS=2
  - OLLAMA_NUM_PARALLEL=1
  - OLLAMA_CONTEXT_LENGTH=4096
- OllamaServeAtLogon:
```text
Folder: \
HostName:                             WIN-OJ03BVT2CLP
TaskName:                             \OllamaServeAtLogon
Next Run Time:                        N/A
Status:                               Ready
Logon Mode:                           Interactive only
Last Run Time:                        18.04.2026 11:00:32
Last Result:                          0
Author:                               WIN-OJ03BVT2CLP\user
Task To Run:                          C:\Users\user\AppData\Local\Programs\Ollama\ollama.exe serve
Start In:                             N/A
Comment:                              N/A
Scheduled Task State:                 Enabled
Idle Time:                            Disabled
Power Management:                     Stop On Battery Mode, No Start On Batteries
Run As User:                          user
Delete Task If Not Rescheduled:       Disabled
Stop Task If Runs X Hours and X Mins: 72:00:00
Schedule:                             Scheduling data is not available in this format.
Schedule Type:                        At logon time
Start Time:                           N/A
Start Date:                           N/A
End Date:                             N/A
Days:                                 N/A
Months:                               N/A
Repeat: Every:                        N/A
Repeat: Until: Time:                  N/A
Repeat: Until: Duration:              N/A
Repeat: Stop If Still Running:        N/A
```
- OllamaWatchdog10m:
```text
Folder: \
HostName:                             WIN-OJ03BVT2CLP
TaskName:                             \OllamaWatchdog10m
Next Run Time:                        19.04.2026 6:46:00
Status:                               Ready
Logon Mode:                           Interactive only
Last Run Time:                        19.04.2026 6:36:01
Last Result:                          0
Author:                               WIN-OJ03BVT2CLP\user
Task To Run:                          C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File C:\Users\user\Desktop\codex\ops\watchdog_ollama.ps1
Start In:                             N/A
Comment:                              N/A
Scheduled Task State:                 Enabled
Idle Time:                            Disabled
Power Management:                     Stop On Battery Mode, No Start On Batteries
Run As User:                          user
Delete Task If Not Rescheduled:       Disabled
Stop Task If Runs X Hours and X Mins: 72:00:00
Schedule:                             Scheduling data is not available in this format.
Schedule Type:                        One Time Only, Minute 
Start Time:                           4:16:00
Start Date:                           19.04.2026
End Date:                             N/A
Days:                                 N/A
Months:                               N/A
Repeat: Every:                        0 Hour(s), 10 Minute(s)
Repeat: Until: Time:                  None
Repeat: Until: Duration:              Disabled
Repeat: Stop If Still Running:        Disabled
```
- watchdog log tail (20):
```text
[2026-04-19 04:16:55] OK: health-check passed
[2026-04-19 04:30:20] OK: health-check passed
[2026-04-19 04:46:02] OK: health-check passed
[2026-04-19 04:56:02] OK: health-check passed
[2026-04-19 05:16:02] OK: health-check passed
[2026-04-19 05:36:48] OK: health-check passed
[2026-04-19 05:37:49] OK: health-check passed
[2026-04-19 05:46:02] OK: health-check passed
[2026-04-19 05:56:02] OK: health-check passed
[2026-04-19 06:36:02] OK: health-check passed
```
- D free GB: 52.82

## Per-task Metrics
| Task | Category | Mode | first_draft_sec | ready_sec | local_passes | cloud_calls | cloud_fallback | fallback_trigger | retrieval_used | retrieval_hit_score | defects_found | success |
|---|---|---|---:|---:|---:|---:|---|---|---|---:|---:|---|
| T1 | layout | LOCAL_FIRST | 17.38 | 80.56 | 3 | 0 | no | none | no | 0.0 | 2 | yes |
| T1 | layout | CLOUD_ONLY | 4.96 | 4.96 | 0 | 1 | no | none | no | 0.0 | 0 | yes |
| T2 | layout | LOCAL_FIRST | 21.12 | 21.12 | 1 | 0 | no | none | no | 0.0 | 0 | yes |
| T2 | layout | CLOUD_ONLY | 6.48 | 11.24 | 0 | 2 | no | defects | no | 0.0 | 6 | no |
| T3 | layout | LOCAL_FIRST | 7.01 | 7.01 | 1 | 0 | no | none | no | 0.0 | 0 | yes |
| T3 | layout | CLOUD_ONLY | 5.48 | 5.48 | 0 | 1 | no | none | no | 0.0 | 0 | yes |
| T4 | layout | LOCAL_FIRST | 6.29 | 6.29 | 1 | 0 | no | none | no | 0.0 | 0 | yes |
| T4 | layout | CLOUD_ONLY | 5.74 | 5.74 | 0 | 1 | no | none | no | 0.0 | 0 | yes |
| T5 | ui_logic | LOCAL_FIRST | 3.06 | 125.44 | 3 | 2 | yes | defects | yes | 0.095 | 5 | no |
| T5 | ui_logic | CLOUD_ONLY | 3.2 | 6.83 | 0 | 2 | no | defects | yes | 0.095 | 2 | no |
| T6 | ui_logic | LOCAL_FIRST | 16.79 | 147.89 | 3 | 2 | yes | defects | yes | 0.261 | 5 | no |
| T6 | ui_logic | CLOUD_ONLY | 5.6 | 9.36 | 0 | 2 | no | defects | yes | 0.261 | 2 | no |
| T7 | ui_logic | LOCAL_FIRST | 16.02 | 191.12 | 3 | 2 | yes | defects | yes | 0.05 | 5 | no |
| T7 | ui_logic | CLOUD_ONLY | 6.33 | 12.56 | 0 | 2 | no | defects | yes | 0.05 | 2 | no |
| T8 | ui_logic | LOCAL_FIRST | 15.21 | 142.28 | 3 | 2 | yes | defects | yes | 0.048 | 5 | no |
| T8 | ui_logic | CLOUD_ONLY | 3.03 | 5.8 | 0 | 2 | no | defects | yes | 0.048 | 2 | no |
| T9 | bugfix | LOCAL_FIRST | 13.66 | 130.88 | 3 | 2 | yes | defects | no | 0.0 | 5 | no |
| T9 | bugfix | CLOUD_ONLY | 2.93 | 5.68 | 0 | 2 | no | defects | no | 0.0 | 2 | no |
| T10 | bugfix | LOCAL_FIRST | 22.9 | 138.74 | 3 | 2 | yes | defects | yes | 0.318 | 5 | no |
| T10 | bugfix | CLOUD_ONLY | 3.56 | 7.35 | 0 | 2 | no | defects | yes | 0.318 | 2 | no |
| T11 | refactor | LOCAL_FIRST | 14.67 | 123.44 | 3 | 2 | yes | defects | yes | 0.182 | 5 | no |
| T11 | refactor | CLOUD_ONLY | 3.29 | 6.2 | 0 | 2 | no | defects | yes | 0.182 | 2 | no |
| T12 | refactor | LOCAL_FIRST | 13.82 | 102.81 | 3 | 2 | yes | defects | yes | 0.136 | 5 | no |
| T12 | refactor | CLOUD_ONLY | 2.64 | 5.33 | 0 | 2 | no | defects | yes | 0.136 | 2 | no |

## Summary
| Mode | success_rate % | first_draft avg/median | ready avg/median | local_passes avg | cloud_calls avg | retrieval_hit avg | defects avg/median |
|---|---:|---|---|---:|---:|---:|---|
| LOCAL_FIRST | 33.33 | 13.99 / 14.94 | 101.46 / 124.44 | 2.5 | 1.33 | 0.091 | 3.5 / 5.0 |
| CLOUD_ONLY | 25.0 | 4.44 / 4.26 | 7.21 / 6.0 | 0.0 | 1.75 | 0.091 | 1.83 / 2.0 |

## Acceptance Gate
- cloud_calls_reduction_pct: 23.81 (>=40 required) -> FAIL
- success_rate_delta_guard: LOCAL 33.33 vs CLOUD 25.0 (not worse by >5pp) -> PASS
- defects_avg_guard: LOCAL 3.5 vs CLOUD 1.83 (+0.3 max) -> FAIL
- layout+simple_bugfix local_accept_no_cloud: 66.67% (>=80 required) -> FAIL
- overall_gate: FAIL

## Stability
- watchdog_restarts_day: 0
- crash_count: 0
- successful_runs_without_manual_pct: 29.17