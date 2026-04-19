import json
import os
import re
import statistics
import subprocess
import tempfile
import time
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Tuple

LOCAL_API = "http://127.0.0.1:11434/api/generate"
LOCAL_TAGS_API = "http://127.0.0.1:11434/api/tags"
CLOUD_API = "https://models.github.ai/inference/chat/completions"
CLOUD_MODEL = "openai/gpt-4o-mini"
WATCHDOG_SCRIPT = r"C:\Users\user\Desktop\codex\ops\watchdog_ollama.ps1"


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def call_local(model: str, prompt: str, timeout: int = 180) -> str:
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")
    req = urllib.request.Request(LOCAL_API, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read().decode("utf-8"))
    return data.get("response", "")


def call_cloud(prompt: str, token: str, timeout: int = 180) -> str:
    payload = {
        "model": CLOUD_MODEL,
        "messages": [
            {"role": "system", "content": "You are a precise coding assistant. Return only the requested JSON object."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 1800,
    }
    req = urllib.request.Request(
        CLOUD_API,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


def local_healthcheck() -> bool:
    try:
        req = urllib.request.Request(LOCAL_TAGS_API, method="GET")
        with urllib.request.urlopen(req, timeout=10):
            return True
    except Exception:
        return False


def run_watchdog() -> Tuple[bool, str]:
    try:
        out = subprocess.check_output(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                WATCHDOG_SCRIPT,
            ],
            stderr=subprocess.STDOUT,
            timeout=90,
            text=True,
        )
        return True, out.strip()
    except subprocess.CalledProcessError as e:
        return False, e.output.strip()
    except Exception as e:
        return False, str(e)


def extract_json(text: str) -> Dict[str, str]:
    block = text.strip()
    m = re.search(r"```json\s*(\{.*?\})\s*```", block, flags=re.S)
    if m:
        block = m.group(1)
    else:
        first = block.find("{")
        last = block.rfind("}")
        if first != -1 and last != -1 and last > first:
            block = block[first : last + 1]
    obj = json.loads(block)
    files = obj.get("files") if isinstance(obj, dict) else None
    if isinstance(files, dict):
        return {str(k): str(v) for k, v in files.items()}
    if isinstance(obj, dict):
        return {str(k): str(v) for k, v in obj.items() if isinstance(v, str)}
    return {}


def run_js_test(code: str) -> Tuple[bool, str]:
    with tempfile.TemporaryDirectory() as d:
        js_path = os.path.join(d, "main.js")
        test_path = os.path.join(d, "test.js")
        with open(js_path, "w", encoding="utf-8") as f:
            f.write(code)
        with open(test_path, "w", encoding="utf-8") as f:
            f.write(
                "const assert = require('assert');\n"
                "const m = require('./main.js');\n"
                "(async () => {\n"
                "try {\n"
                """
                + "\n"
                + """
                "} catch(e) { console.error(e.message || String(e)); process.exit(1); }\n"
                "})();\n"
            )
        return True, ""


def test_node(module_code: str, test_body: str) -> Tuple[bool, str]:
    with tempfile.TemporaryDirectory() as d:
        mod = os.path.join(d, "module.js")
        test = os.path.join(d, "test.js")
        with open(mod, "w", encoding="utf-8") as f:
            f.write(module_code)
        with open(test, "w", encoding="utf-8") as f:
            f.write(
                "const assert = require('assert');\n"
                "const m = require('./module.js');\n"
                "(async () => {\n"
                "  try {\n"
                f"{test_body}\n"
                "    process.exit(0);\n"
                "  } catch(e) { console.error(e.stack || e.message || String(e)); process.exit(1); }\n"
                "})();\n"
            )
        p = subprocess.run(["node", test], capture_output=True, text=True, timeout=35)
        ok = p.returncode == 0
        msg = (p.stdout + "\n" + p.stderr).strip()
        return ok, msg


def validate_layout_hero(files: Dict[str, str]) -> Tuple[int, str]:
    defects = []
    html = files.get("index.html", "")
    css = files.get("styles.css", "")
    full = (html + "\n" + css).lower()
    checks = [
        ("hero section", "<section" in full and "hero" in full),
        ("headline", "<h1" in full),
        ("cta button", "button" in full and "cta" in full),
        ("responsive media query", "@media" in full),
    ]
    for name, ok in checks:
        if not ok:
            defects.append(name)
    return len(defects), ", ".join(defects)


def validate_layout_pricing(files: Dict[str, str]) -> Tuple[int, str]:
    defects = []
    html = files.get("index.html", "")
    css = files.get("styles.css", "")
    if html.lower().count("pricing-card") < 3:
        defects.append("need 3 pricing cards")
    if "popular" not in html.lower():
        defects.append("missing popular plan")
    if "--accent" not in css:
        defects.append("missing CSS variable --accent")
    return len(defects), ", ".join(defects)


def validate_layout_contact(files: Dict[str, str]) -> Tuple[int, str]:
    defects = []
    html = files.get("index.html", "").lower()
    for token in ["<form", "name=\"name\"", "name=\"email\"", "name=\"message\"", "aria-label"]:
        if token not in html:
            defects.append(f"missing {token}")
    return len(defects), ", ".join(defects)


def validate_todo_state(files: Dict[str, str]) -> Tuple[int, str]:
    code = files.get("state.js", "")
    if not code:
        return 1, "missing state.js"
    tests = """
const { addTodo, toggleTodo, removeTodo } = m;
assert.equal(typeof addTodo, 'function');
assert.equal(typeof toggleTodo, 'function');
assert.equal(typeof removeTodo, 'function');
const s1 = [];
const s2 = addTodo(s1, 'A');
assert.equal(s1.length, 0);
assert.equal(s2.length, 1);
const s3 = toggleTodo(s2, s2[0].id);
assert.equal(s3[0].done, true);
const s4 = removeTodo(s3, s3[0].id);
assert.equal(s4.length, 0);
"""
    ok, msg = test_node(code, tests)
    return (0, "") if ok else (1, msg)


def validate_tabs(files: Dict[str, str]) -> Tuple[int, str]:
    code = files.get("tabs.js", "")
    if not code:
        return 1, "missing tabs.js"
    tests = """
const { createTabs } = m;
assert.equal(typeof createTabs, 'function');
const t = createTabs(['home','profile','billing'], 'home');
assert.equal(t.getActive(), 'home');
t.select('billing');
assert.equal(t.getActive(), 'billing');
assert.throws(() => t.select('bad'));
"""
    ok, msg = test_node(code, tests)
    return (0, "") if ok else (1, msg)


def validate_cart(files: Dict[str, str]) -> Tuple[int, str]:
    code = files.get("cart.js", "")
    if not code:
        return 1, "missing cart.js"
    tests = """
const { createCart } = m;
const c = createCart();
c.addItem({id:'a', price:10}, 2);
assert.equal(c.getTotal(), 20);
c.setQuantity('a', 3);
assert.equal(c.getTotal(), 30);
c.removeItem('a');
assert.equal(c.getTotal(), 0);
"""
    ok, msg = test_node(code, tests)
    return (0, "") if ok else (1, msg)


def validate_debounce_fix(files: Dict[str, str]) -> Tuple[int, str]:
    code = files.get("debounce.js", "")
    if not code:
        return 1, "missing debounce.js"
    tests = """
const { debounce } = m;
let calls = 0;
const obj = { x: 2, fn: debounce(function(v){ calls += this.x + v; }, 30) };
obj.fn(1); obj.fn(1); obj.fn(1);
await new Promise(r => setTimeout(r, 80));
assert.equal(calls, 3);
"""
    ok, msg = test_node(code, tests)
    return (0, "") if ok else (1, msg)


def validate_retry_fix(files: Dict[str, str]) -> Tuple[int, str]:
    code = files.get("retry.js", "")
    if not code:
        return 1, "missing retry.js"
    tests = """
const { fetchWithRetry } = m;
let c = 0;
const fn = async () => { c += 1; if (c < 3) throw new Error('x'); return 42; };
const v = await fetchWithRetry(fn, 3);
assert.equal(v, 42);
let c2 = 0;
const fn2 = async () => { c2 += 1; throw new Error('fail'); };
let threw = false;
try { await fetchWithRetry(fn2, 2); } catch(_) { threw = true; }
assert.equal(threw, true);
"""
    ok, msg = test_node(code, tests)
    return (0, "") if ok else (1, msg)


def validate_refactor_format(files: Dict[str, str]) -> Tuple[int, str]:
    code = files.get("format.js", "")
    if not code:
        return 1, "missing format.js"
    tests = """
const { formatUser, formatAdmin } = m;
assert.equal(formatUser({name:'Ann', age:20}), 'Ann (20)');
assert.equal(formatAdmin({name:'Bob', age:30, role:'root'}), 'Bob (30) [root]');
"""
    ok, msg = test_node(code, tests)
    if not ok:
        return 1, msg
    if "formatPerson" not in code:
        return 1, "missing shared helper formatPerson"
    return 0, ""


def validate_refactor_classes(files: Dict[str, str]) -> Tuple[int, str]:
    code = files.get("classnames.js", "")
    if not code:
        return 1, "missing classnames.js"
    tests = """
const { classNames } = m;
assert.equal(classNames({primary:true, disabled:false, rounded:true}), 'btn btn--primary btn--rounded');
assert.equal(classNames({primary:false, disabled:true, rounded:false}), 'btn btn--disabled');
"""
    ok, msg = test_node(code, tests)
    if not ok:
        return 1, msg
    if "RULES" not in code and "rules" not in code:
        return 1, "missing rule map"
    return 0, ""


@dataclass
class Task:
    id: str
    category: str
    files_count: str
    prompt: str
    validator: object
    local_model: str


def tasks() -> List[Task]:
    return [
        Task(
            "T1",
            "layout",
            "2",
            """Create responsive hero section. Return JSON only: {\"files\":{\"index.html\":\"...\",\"styles.css\":\"...\"}}.\nRequirements: section.hero, h1, short paragraph, button class cta, gradient background, one @media rule for <=768px.""",
            validate_layout_hero,
            "qwen2.5-coder:7b",
        ),
        Task(
            "T2",
            "layout",
            "2",
            """Create pricing section. Return JSON only with index.html and styles.css.\nRequirements: exactly 3 cards with class pricing-card, one has class popular, include CSS variable --accent, mobile responsive.""",
            validate_layout_pricing,
            "qwen2.5-coder:7b",
        ),
        Task(
            "T3",
            "layout",
            "2",
            """Create contact form section. Return JSON only with index.html and styles.css.\nRequirements: form contains inputs name,email,message and each field has aria-label.""",
            validate_layout_contact,
            "qwen2.5-coder:7b",
        ),
        Task(
            "T4",
            "ui_state",
            "2",
            """Write state.js only. Return JSON {\"files\":{\"state.js\":\"...\"}}.\nImplement pure functions: addTodo(state,text), toggleTodo(state,id), removeTodo(state,id). Use module.exports. Keep immutable updates.""",
            validate_todo_state,
            "qwen2.5-coder:14b",
        ),
        Task(
            "T5",
            "ui_state",
            "2",
            """Write tabs.js only in JSON format.\nImplement createTabs(ids, initialId) returning {select(id), getActive()}. select throws on unknown id. Use module.exports.""",
            validate_tabs,
            "deepseek-r1:8b",
        ),
        Task(
            "T6",
            "ui_state",
            "2",
            """Write cart.js only in JSON format.\nImplement createCart() with methods addItem(item,qty), removeItem(id), setQuantity(id,qty), getTotal(). Use module.exports.""",
            validate_cart,
            "qwen2.5-coder:14b",
        ),
        Task(
            "T7",
            "bugfix",
            "1",
            """Fix buggy debounce implementation and return debounce.js in JSON.\nBuggy code:\nfunction debounce(fn, wait){ let t; return (...args)=>{ setTimeout(()=>fn(args), wait); }; }\nNeed: clear previous timer, pass args correctly, preserve this, export as module.exports={debounce}.""",
            validate_debounce_fix,
            "deepseek-r1:8b",
        ),
        Task(
            "T8",
            "bugfix",
            "1",
            """Fix fetchWithRetry and return retry.js in JSON.\nBuggy version does not await and never throws after retries.\nNeed async function fetchWithRetry(fn,retries) that retries then throws last error. Export module.exports={fetchWithRetry}.""",
            validate_retry_fix,
            "qwen2.5-coder:7b",
        ),
        Task(
            "T9",
            "refactor",
            "1",
            """Refactor duplicated formatting code and return format.js in JSON.\nCurrent behavior must remain: formatUser({name,age}) => 'Name (age)', formatAdmin({name,age,role}) => 'Name (age) [role]'.\nRequirement: extract shared helper formatPerson.""",
            validate_refactor_format,
            "qwen2.5-coder:14b",
        ),
        Task(
            "T10",
            "refactor",
            "1",
            """Refactor classNames builder and return classnames.js in JSON.\nNeed function classNames(flags) with base 'btn' and modifiers: primary=>btn--primary, disabled=>btn--disabled, rounded=>btn--rounded.\nUse rule-map object, export module.exports={classNames}.""",
            validate_refactor_classes,
            "qwen3:8b",
        ),
    ]


def env_token() -> str:
    for scope in ("",):
        pass
    return os.environ.get("GITHUB_TOKEN", "")


def run_mode_for_task(task: Task, mode: str, token: str, max_iter: int = 3) -> Dict:
    assert mode in {"LOCAL_FIRST", "CLOUD_ONLY"}
    start = time.perf_counter()
    first_draft = None
    defects_total = 0
    cloud_fallback = False
    fallback_reason = ""
    iterations = 0
    accepted = False
    last_issue = ""
    local_events = []

    prompt = task.prompt

    for i in range(1, max_iter + 1):
        iterations = i
        use_cloud = mode == "CLOUD_ONLY"
        model = CLOUD_MODEL if use_cloud else task.local_model

        if mode == "LOCAL_FIRST" and i >= 3 and defects_total > 0:
            use_cloud = True
            model = CLOUD_MODEL
            cloud_fallback = True
            fallback_reason = "validator failures after 2 local attempts"

        t0 = time.perf_counter()
        text = ""
        error = ""
        try:
            if use_cloud:
                text = call_cloud(prompt, token)
            else:
                if not local_healthcheck():
                    ok, msg = run_watchdog()
                    local_events.append(f"watchdog_triggered:{'ok' if ok else 'fail'}")
                    if not local_healthcheck():
                        raise RuntimeError(f"local healthcheck failed after watchdog: {msg}")
                text = call_local(model, prompt)
        except Exception as e:
            error = str(e)
            defects_total += 1
            last_issue = f"model call error: {error[:240]}"
            prompt = (
                task.prompt
                + "\nPrevious attempt failed to run. Return strict JSON object only in the required format."
            )
            if first_draft is None:
                first_draft = time.perf_counter() - start
            continue

        if first_draft is None:
            first_draft = time.perf_counter() - start

        try:
            files = extract_json(text)
            defects, issue = task.validator(files)
        except Exception as e:
            defects, issue = 1, f"parse/validation error: {str(e)[:240]}"

        defects_total += defects
        if defects == 0:
            accepted = True
            ready = time.perf_counter() - start
            return {
                "task_id": task.id,
                "category": task.category,
                "files_count": task.files_count,
                "mode": mode,
                "local_model": task.local_model if mode == "LOCAL_FIRST" else "none",
                "cloud_model": CLOUD_MODEL if (mode == "CLOUD_ONLY" or cloud_fallback) else "none",
                "first_draft_sec": round(first_draft or 0.0, 2),
                "ready_sec": round(ready, 2),
                "defects_found": defects_total,
                "iterations_to_acceptance": iterations,
                "cloud_fallback": "yes" if cloud_fallback else "no",
                "fallback_reason": fallback_reason,
                "accepted": True,
                "local_events": ";".join(local_events) if local_events else "",
            }

        last_issue = issue
        prompt = (
            task.prompt
            + "\nFix all issues from validator: "
            + issue
            + "\nReturn full corrected JSON only."
        )

    ready = time.perf_counter() - start
    return {
        "task_id": task.id,
        "category": task.category,
        "files_count": task.files_count,
        "mode": mode,
        "local_model": task.local_model if mode == "LOCAL_FIRST" else "none",
        "cloud_model": CLOUD_MODEL if (mode == "CLOUD_ONLY" or cloud_fallback) else "none",
        "first_draft_sec": round(first_draft or ready, 2),
        "ready_sec": round(ready, 2),
        "defects_found": defects_total,
        "iterations_to_acceptance": iterations,
        "cloud_fallback": "yes" if cloud_fallback else "no",
        "fallback_reason": fallback_reason or last_issue,
        "accepted": accepted,
        "local_events": ";".join(local_events) if local_events else "",
    }


def summarize(rows: List[Dict], mode: str) -> Dict:
    s = [r for r in rows if r["mode"] == mode]
    fd = [r["first_draft_sec"] for r in s]
    rd = [r["ready_sec"] for r in s]
    df = [r["defects_found"] for r in s]
    it = [r["iterations_to_acceptance"] for r in s]
    ok = [r for r in s if r["accepted"]]
    return {
        "count": len(s),
        "success": len(ok),
        "first_draft_avg": round(sum(fd) / len(fd), 2),
        "first_draft_median": round(statistics.median(fd), 2),
        "ready_avg": round(sum(rd) / len(rd), 2),
        "ready_median": round(statistics.median(rd), 2),
        "defects_avg": round(sum(df) / len(df), 2),
        "defects_median": round(statistics.median(df), 2),
        "iterations_avg": round(sum(it) / len(it), 2),
        "iterations_median": round(statistics.median(it), 2),
    }


def to_markdown(checks: Dict, rows: List[Dict], sum_local: Dict, sum_cloud: Dict, stability: Dict) -> str:
    lines = []
    lines.append("# LOCAL LLM A/B Benchmark")
    lines.append("")
    lines.append(f"- generated_at: {now_iso()}")
    lines.append("- hardware: RTX 3060 Ti 8GB")
    lines.append("- tasks: 10 (each run in LOCAL_FIRST and CLOUD_ONLY)")
    lines.append("")
    lines.append("## Environment Readiness")
    lines.append(f"- ollama_list_ok: {checks['ollama_list_ok']}")
    lines.append(f"- ready_probe: {checks['ready_probe']}")
    lines.append(f"- OllamaServeAtLogon: {checks['serve_task_status']}")
    lines.append(f"- OllamaWatchdog10m: {checks['watchdog_task_status']}")
    lines.append(f"- watchdog_log_tail: {checks['watchdog_log_tail'].replace(chr(10), ' | ')}")
    lines.append(f"- D_free_gb: {checks['d_free_gb']}")
    lines.append("")
    lines.append("## Per-Task Metrics")
    lines.append("| Task | Category | LOCAL_FIRST first_draft_sec | LOCAL_FIRST ready_sec | LOCAL_FIRST defects | LOCAL_FIRST iter | LOCAL_FIRST fallback | CLOUD_ONLY first_draft_sec | CLOUD_ONLY ready_sec | CLOUD_ONLY defects | CLOUD_ONLY iter |")
    lines.append("|---|---|---:|---:|---:|---:|---|---:|---:|---:|---:|")
    by_task = {}
    for r in rows:
        by_task.setdefault(r["task_id"], {})[r["mode"]] = r
    for t in sorted(by_task.keys(), key=lambda x: int(x[1:])):
        l = by_task[t].get("LOCAL_FIRST", {})
        c = by_task[t].get("CLOUD_ONLY", {})
        lines.append(
            f"| {t} | {l.get('category','')} | {l.get('first_draft_sec','')} | {l.get('ready_sec','')} | {l.get('defects_found','')} | {l.get('iterations_to_acceptance','')} | {l.get('cloud_fallback','')} | {c.get('first_draft_sec','')} | {c.get('ready_sec','')} | {c.get('defects_found','')} | {c.get('iterations_to_acceptance','')} |"
        )
    lines.append("")
    lines.append("## Aggregate")
    lines.append("| Mode | Success | First Draft Avg | First Draft Median | Ready Avg | Ready Median | Defects Avg | Defects Median | Iter Avg | Iter Median |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    lines.append(
        f"| LOCAL_FIRST | {sum_local['success']}/{sum_local['count']} | {sum_local['first_draft_avg']} | {sum_local['first_draft_median']} | {sum_local['ready_avg']} | {sum_local['ready_median']} | {sum_local['defects_avg']} | {sum_local['defects_median']} | {sum_local['iterations_avg']} | {sum_local['iterations_median']} |"
    )
    lines.append(
        f"| CLOUD_ONLY | {sum_cloud['success']}/{sum_cloud['count']} | {sum_cloud['first_draft_avg']} | {sum_cloud['first_draft_median']} | {sum_cloud['ready_avg']} | {sum_cloud['ready_median']} | {sum_cloud['defects_avg']} | {sum_cloud['defects_median']} | {sum_cloud['iterations_avg']} | {sum_cloud['iterations_median']} |"
    )
    lines.append("")
    lines.append("## Stability")
    lines.append(f"- local_fail_events: {stability['local_fail_events']}")
    lines.append(f"- watchdog_recoveries: {stability['watchdog_recoveries']}")
    lines.append(f"- successful_runs_without_manual_intervention_pct: {stability['success_no_manual_pct']}")
    lines.append("")
    lines.append("## Raw JSON")
    lines.append("```json")
    lines.append(json.dumps({"checks": checks, "rows": rows, "sum_local": sum_local, "sum_cloud": sum_cloud, "stability": stability}, ensure_ascii=False, indent=2))
    lines.append("```")
    return "\n".join(lines)


def main() -> None:
    token = env_token()
    if not token:
        raise RuntimeError("GITHUB_TOKEN is required for CLOUD_ONLY run via GitHub Models API")

    checks = {
        "ollama_list_ok": False,
        "ready_probe": "",
        "serve_task_status": "",
        "watchdog_task_status": "",
        "watchdog_log_tail": "",
        "d_free_gb": "",
    }

    try:
        subprocess.check_output(["ollama", "list"], stderr=subprocess.STDOUT, text=True, timeout=30)
        checks["ollama_list_ok"] = True
    except Exception as e:
        checks["ollama_list_ok"] = False
        checks["ready_probe"] = f"ollama list failed: {e}"

    try:
        checks["ready_probe"] = subprocess.check_output(
            ["ollama", "run", "qwen2.5-coder:7b", "Reply exactly: READY"],
            stderr=subprocess.STDOUT,
            text=True,
            timeout=90,
        ).strip()
    except Exception as e:
        checks["ready_probe"] = f"probe_failed:{e}"

    def task_status(name: str) -> str:
        try:
            out = subprocess.check_output(["schtasks", "/Query", "/TN", name, "/V", "/FO", "LIST"], text=True, timeout=20)
            m = re.search(r"Status:\s*(.+)", out)
            lr = re.search(r"Last Result:\s*(.+)", out)
            return f"{m.group(1).strip() if m else 'unknown'}; last_result={lr.group(1).strip() if lr else 'unknown'}"
        except Exception as e:
            return f"error:{e}"

    checks["serve_task_status"] = task_status("OllamaServeAtLogon")
    checks["watchdog_task_status"] = task_status("OllamaWatchdog10m")

    try:
        with open(r"C:\Users\user\Desktop\codex\ops\watchdog_ollama.log", "r", encoding="utf-8") as f:
            tail = f.readlines()[-5:]
        checks["watchdog_log_tail"] = "".join(tail).strip()
    except Exception as e:
        checks["watchdog_log_tail"] = f"error:{e}"

    try:
        out = subprocess.check_output(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "(Get-PSDrive -Name D).Free / 1GB",
            ],
            text=True,
            timeout=20,
        ).strip()
        checks["d_free_gb"] = round(float(out.replace(",", ".")), 2)
    except Exception as e:
        checks["d_free_gb"] = f"error:{e}"

    rows = []
    local_fail_events = 0
    watchdog_recoveries = 0

    for task in tasks():
        r_local = run_mode_for_task(task, "LOCAL_FIRST", token)
        rows.append(r_local)
        if r_local.get("local_events"):
            local_fail_events += 1
            if "watchdog_triggered:ok" in r_local["local_events"]:
                watchdog_recoveries += 1

        r_cloud = run_mode_for_task(task, "CLOUD_ONLY", token)
        rows.append(r_cloud)

    sum_local = summarize(rows, "LOCAL_FIRST")
    sum_cloud = summarize(rows, "CLOUD_ONLY")

    ok_runs = len([r for r in rows if r["accepted"]])
    success_no_manual_pct = round((ok_runs / len(rows)) * 100.0, 2) if rows else 0.0
    stability = {
        "local_fail_events": local_fail_events,
        "watchdog_recoveries": watchdog_recoveries,
        "success_no_manual_pct": success_no_manual_pct,
    }

    os.makedirs("reports", exist_ok=True)
    with open("reports/ab_results.json", "w", encoding="utf-8") as f:
        json.dump({"checks": checks, "rows": rows, "sum_local": sum_local, "sum_cloud": sum_cloud, "stability": stability}, f, ensure_ascii=False, indent=2)

    md = to_markdown(checks, rows, sum_local, sum_cloud, stability)
    with open("LOCAL_LLM_BENCHMARK.md", "w", encoding="utf-8") as f:
        f.write(md)

    print("Benchmark complete")
    print(json.dumps({"sum_local": sum_local, "sum_cloud": sum_cloud, "stability": stability}, ensure_ascii=False))


if __name__ == "__main__":
    main()
