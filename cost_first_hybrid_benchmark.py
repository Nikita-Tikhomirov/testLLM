import json
import os
import re
import statistics
import subprocess
import tempfile
import time
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

LOCAL_API = "http://127.0.0.1:11434/api/generate"
LOCAL_TAGS_API = "http://127.0.0.1:11434/api/tags"
CLOUD_API = "https://models.github.ai/inference/chat/completions"
CLOUD_MODEL = "openai/gpt-4o-mini"

FAST_MODEL = "qwen2.5-coder:7b"
STRONG_MODEL = "qwen2.5-coder:7b-instruct-q6_K"
REVIEW_MODEL = "deepseek-r1:8b"

WATCHDOG_SCRIPT = r"C:\Users\user\Desktop\codex\ops\watchdog_ollama.ps1"
WATCHDOG_LOG = r"C:\Users\user\Desktop\codex\ops\watchdog_ollama.log"

RUNTIME_EXPECTED = {
    "OLLAMA_KEEP_ALIVE": "30m",
    "OLLAMA_MAX_LOADED_MODELS": "2",
    "OLLAMA_NUM_PARALLEL": "1",
    "OLLAMA_CONTEXT_LENGTH": "4096",
}

CORPUS = [
    {"id": "ui-state-immutable", "text": "Use immutable updates in state reducers. Never mutate input arrays. Return new arrays with map/filter/spread."},
    {"id": "tabs-pattern", "text": "Tabs manager must validate incoming id against allowed set and throw on unknown values."},
    {"id": "cart-pattern", "text": "Cart helpers should preserve quantities >=0 and compute total as sum(price*qty)."},
    {"id": "retry-pattern", "text": "fetchWithRetry is async and rethrows last error after retries. Await function call every attempt."},
    {"id": "debounce-pattern", "text": "debounce clears previous timer, preserves this with apply, and spreads arguments."},
    {"id": "format-refactor", "text": "Extract shared helper formatPerson(name,age). Keep output contracts for formatUser and formatAdmin."},
    {"id": "class-map", "text": "classNames should use RULES map from flag to class modifier. Always include base class btn."},
    {"id": "layout-accessibility", "text": "Layout sections must include semantic tags and aria labels for form controls."},
]


def tokenize(s: str) -> List[str]:
    return re.findall(r"[a-zA-Z0-9_]+", s.lower())


def retrieval(query: str, topk: int = 6) -> Tuple[List[Dict], float]:
    q = set(tokenize(query))
    ranked = []
    for doc in CORPUS:
        t = set(tokenize(doc["text"]))
        score = len(q & t) / len(q | t) if t else 0.0
        ranked.append((score, doc))
    ranked.sort(key=lambda x: x[0], reverse=True)
    top = [d for s, d in ranked[:topk]]
    hit = ranked[0][0] if ranked else 0.0
    return top, round(hit, 3)


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def local_healthcheck() -> bool:
    try:
        req = urllib.request.Request(LOCAL_TAGS_API, method="GET")
        with urllib.request.urlopen(req, timeout=8):
            return True
    except Exception:
        return False


def run_watchdog() -> bool:
    try:
        subprocess.check_output(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", WATCHDOG_SCRIPT],
            stderr=subprocess.STDOUT,
            timeout=90,
            text=True,
        )
        return True
    except Exception:
        return False


def call_local(model: str, prompt: str, timeout: int) -> str:
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")
    req = urllib.request.Request(LOCAL_API, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read().decode("utf-8"))
    return data.get("response", "")


def call_cloud(prompt: str, token: str, timeout: int = 120) -> str:
    payload = {
        "model": CLOUD_MODEL,
        "messages": [
            {"role": "system", "content": "You are a coding assistant. Return strict JSON only."},
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


def extract_json_files(text: str) -> Dict[str, str]:
    block = text.strip()
    m = re.search(r"```json\s*(\{.*?\})\s*```", block, flags=re.S)
    if m:
        block = m.group(1)
    else:
        first, last = block.find("{"), block.rfind("}")
        if first >= 0 and last > first:
            block = block[first : last + 1]
    obj = json.loads(block)
    files = obj.get("files") if isinstance(obj, dict) else None
    if isinstance(files, dict):
        return {str(k): str(v) for k, v in files.items()}
    if isinstance(obj, dict):
        return {str(k): str(v) for k, v in obj.items() if isinstance(v, str)}
    return {}


def node_test(module_name: str, module_code: str, test_body: str) -> Tuple[bool, str]:
    with tempfile.TemporaryDirectory() as d:
        mod = os.path.join(d, module_name)
        tst = os.path.join(d, "test.js")
        with open(mod, "w", encoding="utf-8") as f:
            f.write(module_code)
        with open(tst, "w", encoding="utf-8") as f:
            f.write(
                "const assert = require('assert');\n"
                f"const m = require('./{module_name}');\n"
                "(async()=>{\n"
                "try {\n"
                f"{test_body}\n"
                "process.exit(0);\n"
                "} catch(e) { console.error(e.stack || e.message || String(e)); process.exit(1); }\n"
                "})();\n"
            )
        p = subprocess.run(["node", tst], capture_output=True, text=True, timeout=35)
        return p.returncode == 0, (p.stdout + "\n" + p.stderr).strip()


def validate_layout_hero(files: Dict[str, str]) -> Tuple[int, str, bool]:
    html, css = files.get("index.html", "").lower(), files.get("styles.css", "").lower()
    defects = []
    for cond, msg in [
        ("<section" in html and "hero" in html, "hero section"),
        ("<h1" in html, "h1"),
        ("cta" in html and "button" in html, "cta button"),
        ("@media" in css, "media query"),
    ]:
        if not cond:
            defects.append(msg)
    return len(defects), ", ".join(defects), True


def validate_layout_pricing(files: Dict[str, str]) -> Tuple[int, str, bool]:
    html, css = files.get("index.html", "").lower(), files.get("styles.css", "")
    defects = []
    if html.count("pricing-card") < 3:
        defects.append("3 pricing-card")
    if "popular" not in html:
        defects.append("popular class")
    if "--accent" not in css:
        defects.append("--accent var")
    return len(defects), ", ".join(defects), True


def validate_layout_contact(files: Dict[str, str]) -> Tuple[int, str, bool]:
    html = files.get("index.html", "").lower()
    defects = []
    for token in ['<form', 'name="name"', 'name="email"', 'name="message"', "aria-label"]:
        if token not in html:
            defects.append(token)
    return len(defects), ", ".join(defects), True


def validate_layout_features(files: Dict[str, str]) -> Tuple[int, str, bool]:
    html, css = files.get("index.html", "").lower(), files.get("styles.css", "").lower()
    defects = []
    if html.count("feature-card") < 4:
        defects.append("4 feature-card")
    if "display:grid" not in css.replace(" ", ""):
        defects.append("grid")
    return len(defects), ", ".join(defects), True


def validate_todo(files: Dict[str, str]) -> Tuple[int, str, bool]:
    code = files.get("state.js", "")
    if not code:
        return 1, "missing state.js", True
    test = """
const { addTodo, toggleTodo, removeTodo } = m;
const s1 = [];
const s2 = addTodo(s1, 'A');
assert.equal(s1.length, 0);
assert.equal(s2.length, 1);
const s3 = toggleTodo(s2, s2[0].id);
assert.equal(s3[0].done, true);
const s4 = removeTodo(s3, s3[0].id);
assert.equal(s4.length, 0);
"""
    ok, msg = node_test("state.js", code, test)
    return (0, "", False) if ok else (1, msg, True)


def validate_tabs(files: Dict[str, str]) -> Tuple[int, str, bool]:
    code = files.get("tabs.js", "")
    if not code:
        return 1, "missing tabs.js", True
    test = """
const { createTabs } = m;
const t = createTabs(['home','billing'], 'home');
assert.equal(t.getActive(), 'home');
t.select('billing');
assert.equal(t.getActive(), 'billing');
assert.throws(() => t.select('x'));
"""
    ok, msg = node_test("tabs.js", code, test)
    return (0, "", False) if ok else (1, msg, True)


def validate_cart(files: Dict[str, str]) -> Tuple[int, str, bool]:
    code = files.get("cart.js", "")
    if not code:
        return 1, "missing cart.js", True
    test = """
const { createCart } = m;
const c = createCart();
c.addItem({id:'a',price:10},2);
assert.equal(c.getTotal(),20);
c.setQuantity('a',3);
assert.equal(c.getTotal(),30);
c.removeItem('a');
assert.equal(c.getTotal(),0);
"""
    ok, msg = node_test("cart.js", code, test)
    return (0, "", False) if ok else (1, msg, True)


def validate_modal(files: Dict[str, str]) -> Tuple[int, str, bool]:
    code = files.get("modal.js", "")
    if not code:
        return 1, "missing modal.js", True
    test = """
const { createModalStore } = m;
const s = createModalStore();
assert.equal(s.isOpen(), false);
s.open('settings');
assert.equal(s.isOpen(), true);
assert.equal(s.getActive(), 'settings');
s.close();
assert.equal(s.isOpen(), false);
"""
    ok, msg = node_test("modal.js", code, test)
    return (0, "", False) if ok else (1, msg, True)


def validate_debounce(files: Dict[str, str]) -> Tuple[int, str, bool]:
    code = files.get("debounce.js", "")
    if not code:
        return 1, "missing debounce.js", True
    test = """
const { debounce } = m;
let val = 0;
const o = { x:2, f: debounce(function(v){ val += this.x + v; }, 25) };
o.f(1); o.f(1); o.f(1);
await new Promise(r => setTimeout(r, 80));
assert.equal(val, 3);
"""
    ok, msg = node_test("debounce.js", code, test)
    return (0, "", False) if ok else (1, msg, True)


def validate_retry(files: Dict[str, str]) -> Tuple[int, str, bool]:
    code = files.get("retry.js", "")
    if not code:
        return 1, "missing retry.js", True
    test = """
const { fetchWithRetry } = m;
let c = 0;
const fn = async () => { c += 1; if (c < 3) throw new Error('x'); return 42; };
const v = await fetchWithRetry(fn, 3);
assert.equal(v, 42);
let c2 = 0;
const fn2 = async () => { c2 += 1; throw new Error('fail'); };
let threw = false;
try { await fetchWithRetry(fn2, 2); } catch (_) { threw = true; }
assert.equal(threw, true);
"""
    ok, msg = node_test("retry.js", code, test)
    return (0, "", False) if ok else (1, msg, True)


def validate_format(files: Dict[str, str]) -> Tuple[int, str, bool]:
    code = files.get("format.js", "")
    if not code:
        return 1, "missing format.js", True
    test = """
const { formatUser, formatAdmin } = m;
assert.equal(formatUser({name:'Ann', age:20}), 'Ann (20)');
assert.equal(formatAdmin({name:'Bob', age:30, role:'root'}), 'Bob (30) [root]');
"""
    ok, msg = node_test("format.js", code, test)
    if not ok:
        return 1, msg, True
    if "formatPerson" not in code:
        return 1, "missing formatPerson", True
    return 0, "", False


def validate_classnames(files: Dict[str, str]) -> Tuple[int, str, bool]:
    code = files.get("classnames.js", "")
    if not code:
        return 1, "missing classnames.js", True
    test = """
const { classNames } = m;
assert.equal(classNames({primary:true,disabled:false,rounded:true}), 'btn btn--primary btn--rounded');
assert.equal(classNames({primary:false,disabled:true,rounded:false}), 'btn btn--disabled');
"""
    ok, msg = node_test("classnames.js", code, test)
    if not ok:
        return 1, msg, True
    if "RULES" not in code and "rules" not in code:
        return 1, "missing rules map", True
    return 0, "", False


@dataclass
class Task:
    task_id: str
    category: str
    files_count: int
    prompt: str
    validator: object
    nontrivial: bool
    high_risk: bool


def build_tasks() -> List[Task]:
    return [
        Task("T1", "layout", 2, "Create hero section in index.html and styles.css. Require .hero, h1, cta button, and one media query. Return JSON {files:{...}} only.", validate_layout_hero, False, False),
        Task("T2", "layout", 2, "Create pricing section with exactly 3 .pricing-card cards, one .popular, CSS var --accent, responsive. Return JSON only.", validate_layout_pricing, False, False),
        Task("T3", "layout", 2, "Create contact form section with fields name,email,message and aria-labels. Return index.html/styles.css JSON.", validate_layout_contact, False, False),
        Task("T4", "layout", 2, "Create features section with 4 .feature-card items and CSS grid responsive layout. Return JSON only.", validate_layout_features, False, False),
        Task("T5", "ui_logic", 2, "Write state.js with pure functions addTodo,toggleTodo,removeTodo and module.exports.", validate_todo, True, False),
        Task("T6", "ui_logic", 2, "Write tabs.js implementing createTabs(ids,initialId) with select/getActive and throw on unknown id.", validate_tabs, True, False),
        Task("T7", "ui_logic", 2, "Write cart.js implementing createCart with addItem/removeItem/setQuantity/getTotal.", validate_cart, True, False),
        Task("T8", "ui_logic", 2, "Write modal.js implementing createModalStore with open(id), close(), isOpen(), getActive().", validate_modal, True, False),
        Task("T9", "bugfix", 1, "Fix debounce bug: clear previous timer, preserve this, spread args. Return debounce.js JSON.", validate_debounce, False, False),
        Task("T10", "bugfix", 1, "Fix fetchWithRetry bug: await attempts and throw last error after retries. Return retry.js JSON.", validate_retry, True, False),
        Task("T11", "refactor", 1, "Refactor format functions preserving behavior and extracting shared helper formatPerson. Return format.js JSON.", validate_format, True, True),
        Task("T12", "refactor", 1, "Refactor classNames with rules map and stable output. Return classnames.js JSON.", validate_classnames, True, True),
    ]


def routing_prompt(task: Task, base_prompt: str, retrieval_docs: List[Dict], issue: str = "") -> str:
    docs = "\n".join([f"- {d['id']}: {d['text']}" for d in retrieval_docs])
    extra = ""
    if task.nontrivial:
        extra += f"\nUse retrieval context (top-k=6):\n{docs}\n"
    if issue:
        extra += f"\nFix all validator issues: {issue}\n"
    return base_prompt + "\nReturn strict JSON object with top-level key 'files'." + extra


def try_validate(task: Task, text: str) -> Tuple[int, str, bool]:
    try:
        files = extract_json_files(text)
        return task.validator(files)
    except Exception as e:
        return 1, f"parse/validation error: {str(e)[:240]}", True


def run_local_first(task: Task, token: str) -> Dict:
    start = time.perf_counter()
    first_draft_sec = None
    local_passes = 0
    cloud_calls = 0
    cloud_fallback = "no"
    fallback_trigger = "none"
    defects_found = 0
    crash_count = 0
    issue = ""

    retrieved, hit = retrieval(task.prompt, 6)
    retrieval_used = task.nontrivial

    if not local_healthcheck():
        if not run_watchdog() or not local_healthcheck():
            crash_count += 1

    prompt = routing_prompt(task, task.prompt, retrieved)
    stage_output = ""
    try:
        local_passes += 1
        t1 = time.perf_counter()
        stage_output = call_local(FAST_MODEL, prompt, timeout=30)
        if first_draft_sec is None:
            first_draft_sec = time.perf_counter() - start
        if (time.perf_counter() - t1) > 30 and fallback_trigger == "none":
            fallback_trigger = "time_budget"
    except Exception:
        if first_draft_sec is None:
            first_draft_sec = time.perf_counter() - start
        fallback_trigger = "time_budget"
        stage_output = ""

    defects, issue, tests_red = try_validate(task, stage_output) if stage_output else (1, "empty output from fast local", True)
    defects_found += defects

    if defects > 0:
        try:
            local_passes += 1
            stage_output = call_local(STRONG_MODEL, routing_prompt(task, task.prompt, retrieved, issue), timeout=75)
            defects, issue, tests_red = try_validate(task, stage_output)
            defects_found += defects
            if first_draft_sec is None:
                first_draft_sec = time.perf_counter() - start
        except Exception as e:
            defects_found += 1
            issue = f"strong local error: {str(e)[:160]}"
            tests_red = True

    if defects > 0:
        review_prompt = "You are reviewer. Produce corrected final code in strict JSON files format.\n" + routing_prompt(task, task.prompt, retrieved, issue)
        try:
            local_passes += 1
            stage_output = call_local(REVIEW_MODEL, review_prompt, timeout=90)
            defects, issue, tests_red = try_validate(task, stage_output)
            defects_found += defects
            if first_draft_sec is None:
                first_draft_sec = time.perf_counter() - start
        except Exception as e:
            defects_found += 1
            issue = f"reviewer error: {str(e)[:160]}"
            tests_red = True

    if defects > 0:
        cloud_fallback = "yes"
        if fallback_trigger == "none":
            fallback_trigger = "high_risk" if task.high_risk else "validation_failed"
        try:
            cloud_calls += 1
            stage_output = call_cloud(routing_prompt(task, task.prompt, retrieved, issue), token)
            defects, issue, tests_red = try_validate(task, stage_output)
            defects_found += defects
            if first_draft_sec is None:
                first_draft_sec = time.perf_counter() - start
        except Exception as e:
            defects_found += 1
            crash_count += 1
            issue = f"cloud error: {str(e)[:160]}"
            tests_red = True

    if defects > 0 and tests_red and cloud_calls == 1:
        try:
            cloud_calls += 1
            fallback_trigger = "defects"
            stage_output = call_cloud(routing_prompt(task, task.prompt, retrieved, issue), token)
            defects, issue, tests_red = try_validate(task, stage_output)
            defects_found += defects
        except Exception:
            defects_found += 1
            crash_count += 1

    success = defects == 0
    ready_sec = time.perf_counter() - start
    return {
        "task_id": task.task_id,
        "category": task.category,
        "mode": "LOCAL_FIRST",
        "first_draft_sec": round(first_draft_sec if first_draft_sec is not None else ready_sec, 2),
        "ready_sec": round(ready_sec, 2),
        "local_passes": local_passes,
        "cloud_calls": cloud_calls,
        "cloud_fallback": cloud_fallback,
        "fallback_trigger": fallback_trigger,
        "retrieval_used": "yes" if retrieval_used else "no",
        "retrieval_hit_score": hit if retrieval_used else 0.0,
        "defects_found": defects_found,
        "success": "yes" if success else "no",
        "crash_count": crash_count,
        "local_accept_no_cloud": success and cloud_calls == 0,
        "files_count": task.files_count,
    }


def run_cloud_only(task: Task, token: str) -> Dict:
    start = time.perf_counter()
    first_draft_sec = None
    cloud_calls = 0
    defects_found = 0
    crash_count = 0

    retrieved, hit = retrieval(task.prompt, 6)
    retrieval_used = task.nontrivial
    prompt = routing_prompt(task, task.prompt, retrieved)
    issue = ""
    tests_red = False
    defects = 1

    for i in range(2):
        try:
            cloud_calls += 1
            out = call_cloud(prompt, token)
            if first_draft_sec is None:
                first_draft_sec = time.perf_counter() - start
            defects, issue, tests_red = try_validate(task, out)
            defects_found += defects
            if defects == 0:
                break
            if i == 0 and tests_red:
                prompt = routing_prompt(task, task.prompt, retrieved, issue)
            else:
                break
        except Exception:
            crash_count += 1
            defects_found += 1
            break

    success = defects == 0
    ready_sec = time.perf_counter() - start
    trigger = "defects" if cloud_calls == 2 else "none"
    return {
        "task_id": task.task_id,
        "category": task.category,
        "mode": "CLOUD_ONLY",
        "first_draft_sec": round(first_draft_sec if first_draft_sec is not None else ready_sec, 2),
        "ready_sec": round(ready_sec, 2),
        "local_passes": 0,
        "cloud_calls": cloud_calls,
        "cloud_fallback": "no",
        "fallback_trigger": trigger,
        "retrieval_used": "yes" if retrieval_used else "no",
        "retrieval_hit_score": hit if retrieval_used else 0.0,
        "defects_found": defects_found,
        "success": "yes" if success else "no",
        "crash_count": crash_count,
        "local_accept_no_cloud": False,
        "files_count": task.files_count,
    }


def summarize(rows: List[Dict], mode: str) -> Dict:
    s = [r for r in rows if r["mode"] == mode]
    fd = [r["first_draft_sec"] for r in s]
    rd = [r["ready_sec"] for r in s]
    lp = [r["local_passes"] for r in s]
    cc = [r["cloud_calls"] for r in s]
    rh = [r["retrieval_hit_score"] for r in s]
    df = [r["defects_found"] for r in s]
    succ = [1 if r["success"] == "yes" else 0 for r in s]
    return {
        "count": len(s),
        "success_rate": round(100 * sum(succ) / len(s), 2),
        "first_draft_avg": round(sum(fd) / len(fd), 2),
        "first_draft_median": round(statistics.median(fd), 2),
        "ready_avg": round(sum(rd) / len(rd), 2),
        "ready_median": round(statistics.median(rd), 2),
        "local_passes_avg": round(sum(lp) / len(lp), 2),
        "cloud_calls_avg": round(sum(cc) / len(cc), 2),
        "retrieval_hit_avg": round(sum(rh) / len(rh), 3),
        "defects_avg": round(sum(df) / len(df), 2),
        "defects_median": round(statistics.median(df), 2),
    }


def parse_watchdog_stats() -> Tuple[int, int]:
    restarts = 0
    warns = 0
    try:
        with open(WATCHDOG_LOG, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        threshold = datetime.now() - timedelta(days=1)
        for line in lines:
            m = re.search(r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]", line)
            if not m:
                continue
            ts = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
            if ts < threshold:
                continue
            low = line.lower()
            if "service restarted successfully" in low:
                restarts += 1
            if "error" in low or "warn" in low:
                warns += 1
    except Exception:
        pass
    return restarts, warns


def acceptance(local_sum: Dict, cloud_sum: Dict, rows: List[Dict]) -> Dict:
    local_cloud_calls = sum(r["cloud_calls"] for r in rows if r["mode"] == "LOCAL_FIRST")
    cloud_cloud_calls = sum(r["cloud_calls"] for r in rows if r["mode"] == "CLOUD_ONLY")
    reduction = (1 - (local_cloud_calls / cloud_cloud_calls)) * 100 if cloud_cloud_calls > 0 else 0.0
    c1 = reduction >= 40
    c2 = local_sum["success_rate"] >= (cloud_sum["success_rate"] - 5)
    c3 = local_sum["defects_avg"] <= (cloud_sum["defects_avg"] + 0.3)

    target = [r for r in rows if r["mode"] == "LOCAL_FIRST" and (r["category"] == "layout" or r["task_id"] in {"T9", "T10"})]
    local_accept = 100 * (sum(1 for r in target if r["local_accept_no_cloud"]) / len(target)) if target else 0.0
    c4 = local_accept >= 80

    return {
        "cloud_call_reduction_pct": round(reduction, 2),
        "gate_cloud_calls": c1,
        "gate_success_rate": c2,
        "gate_defects": c3,
        "layout_bugfix_local_accept_pct": round(local_accept, 2),
        "gate_layout_bugfix": c4,
        "passed": c1 and c2 and c3 and c4,
    }


def smoke_checks() -> Dict:
    checks = {}
    checks["ollama_list"] = subprocess.check_output(["ollama", "list"], text=True, timeout=30)
    checks["ready_7b"] = subprocess.check_output(["ollama", "run", "qwen2.5-coder:7b", "Reply exactly: READY"], text=True, timeout=90).strip()
    checks["ready_q6"] = subprocess.check_output(["ollama", "run", "qwen2.5-coder:7b-instruct-q6_K", "Reply exactly: READY_Q6"], text=True, timeout=120).strip()
    checks["serve_task"] = subprocess.check_output(["schtasks", "/Query", "/TN", "OllamaServeAtLogon", "/V", "/FO", "LIST"], text=True, timeout=25)
    checks["watchdog_task"] = subprocess.check_output(["schtasks", "/Query", "/TN", "OllamaWatchdog10m", "/V", "/FO", "LIST"], text=True, timeout=25)
    checks["watchdog_tail"] = subprocess.check_output(["powershell", "-NoProfile", "-Command", f"Get-Content -Path '{WATCHDOG_LOG}' -Tail 20"], text=True, timeout=20)
    checks["d_free"] = subprocess.check_output(["powershell", "-NoProfile", "-Command", "(Get-PSDrive -Name D).Free/1GB"], text=True, timeout=20).strip()
    checks["runtime"] = {k: os.environ.get(k, "") for k in RUNTIME_EXPECTED}
    return checks


def render_report(checks: Dict, rows: List[Dict], local_sum: Dict, cloud_sum: Dict, gate: Dict, stability: Dict) -> str:
    lines = []
    lines.append("# Cost-First Hybrid Validation Report")
    lines.append("")
    lines.append(f"- generated_at: {now_iso()}")
    lines.append("- hardware: RTX 3060 Ti 8GB")
    lines.append("- tasks: 12 x 2 modes")
    lines.append("")
    lines.append("## Smoke/Ready")
    lines.append("```text")
    lines.append(checks["ollama_list"].strip())
    lines.append("```")
    lines.append(f"- ready_7b: {checks['ready_7b'].replace(chr(10), ' ')}")
    lines.append(f"- ready_q6: {checks['ready_q6'].replace(chr(10), ' ')}")
    lines.append("- runtime:")
    for k, v in checks["runtime"].items():
        lines.append(f"  - {k}={v}")
    lines.append("- OllamaServeAtLogon:")
    lines.append("```text")
    lines.append(checks["serve_task"].strip())
    lines.append("```")
    lines.append("- OllamaWatchdog10m:")
    lines.append("```text")
    lines.append(checks["watchdog_task"].strip())
    lines.append("```")
    lines.append("- watchdog log tail (20):")
    lines.append("```text")
    lines.append(checks["watchdog_tail"].strip())
    lines.append("```")
    lines.append(f"- D free GB: {round(float(checks['d_free'].replace(',', '.')), 2)}")
    lines.append("")
    lines.append("## Per-task Metrics")
    lines.append("| Task | Category | Mode | first_draft_sec | ready_sec | local_passes | cloud_calls | cloud_fallback | fallback_trigger | retrieval_used | retrieval_hit_score | defects_found | success |")
    lines.append("|---|---|---|---:|---:|---:|---:|---|---|---|---:|---:|---|")
    for r in rows:
        lines.append(f"| {r['task_id']} | {r['category']} | {r['mode']} | {r['first_draft_sec']} | {r['ready_sec']} | {r['local_passes']} | {r['cloud_calls']} | {r['cloud_fallback']} | {r['fallback_trigger']} | {r['retrieval_used']} | {r['retrieval_hit_score']} | {r['defects_found']} | {r['success']} |")
    lines.append("")
    lines.append("## Summary")
    lines.append("| Mode | success_rate % | first_draft avg/median | ready avg/median | local_passes avg | cloud_calls avg | retrieval_hit avg | defects avg/median |")
    lines.append("|---|---:|---|---|---:|---:|---:|---|")
    lines.append(f"| LOCAL_FIRST | {local_sum['success_rate']} | {local_sum['first_draft_avg']} / {local_sum['first_draft_median']} | {local_sum['ready_avg']} / {local_sum['ready_median']} | {local_sum['local_passes_avg']} | {local_sum['cloud_calls_avg']} | {local_sum['retrieval_hit_avg']} | {local_sum['defects_avg']} / {local_sum['defects_median']} |")
    lines.append(f"| CLOUD_ONLY | {cloud_sum['success_rate']} | {cloud_sum['first_draft_avg']} / {cloud_sum['first_draft_median']} | {cloud_sum['ready_avg']} / {cloud_sum['ready_median']} | {cloud_sum['local_passes_avg']} | {cloud_sum['cloud_calls_avg']} | {cloud_sum['retrieval_hit_avg']} | {cloud_sum['defects_avg']} / {cloud_sum['defects_median']} |")
    lines.append("")
    lines.append("## Acceptance Gate")
    lines.append(f"- cloud_calls_reduction_pct: {gate['cloud_call_reduction_pct']} (>=40 required) -> {'PASS' if gate['gate_cloud_calls'] else 'FAIL'}")
    lines.append(f"- success_rate_delta_guard: LOCAL {local_sum['success_rate']} vs CLOUD {cloud_sum['success_rate']} (not worse by >5pp) -> {'PASS' if gate['gate_success_rate'] else 'FAIL'}")
    lines.append(f"- defects_avg_guard: LOCAL {local_sum['defects_avg']} vs CLOUD {cloud_sum['defects_avg']} (+0.3 max) -> {'PASS' if gate['gate_defects'] else 'FAIL'}")
    lines.append(f"- layout+simple_bugfix local_accept_no_cloud: {gate['layout_bugfix_local_accept_pct']}% (>=80 required) -> {'PASS' if gate['gate_layout_bugfix'] else 'FAIL'}")
    lines.append(f"- overall_gate: {'PASS' if gate['passed'] else 'FAIL'}")
    lines.append("")
    lines.append("## Stability")
    lines.append(f"- watchdog_restarts_day: {stability['watchdog_restarts_day']}")
    lines.append(f"- crash_count: {stability['crash_count']}")
    lines.append(f"- successful_runs_without_manual_pct: {stability['successful_runs_without_manual_pct']}")
    return "\n".join(lines)


def main() -> None:
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        raise RuntimeError("GITHUB_TOKEN missing")

    checks = smoke_checks()
    rows = []
    for task in build_tasks():
        rows.append(run_local_first(task, token))
        rows.append(run_cloud_only(task, token))

    local_sum = summarize(rows, "LOCAL_FIRST")
    cloud_sum = summarize(rows, "CLOUD_ONLY")

    watchdog_restarts_day, watchdog_warns_day = parse_watchdog_stats()
    crash_count = sum(r["crash_count"] for r in rows) + watchdog_warns_day
    success_cnt = sum(1 for r in rows if r["success"] == "yes")
    successful_runs_without_manual_pct = round((success_cnt / len(rows)) * 100, 2)
    stability = {
        "watchdog_restarts_day": watchdog_restarts_day,
        "crash_count": crash_count,
        "successful_runs_without_manual_pct": successful_runs_without_manual_pct,
    }

    gate = acceptance(local_sum, cloud_sum, rows)

    os.makedirs("reports", exist_ok=True)
    with open("reports/cost_first_hybrid_results.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "checks": checks,
                "rows": rows,
                "summary": {"local": local_sum, "cloud": cloud_sum},
                "gate": gate,
                "stability": stability,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    with open("COST_FIRST_HYBRID_REPORT.md", "w", encoding="utf-8") as f:
        f.write(render_report(checks, rows, local_sum, cloud_sum, gate, stability))

    print("Cost-first benchmark complete")
    print(json.dumps({"local": local_sum, "cloud": cloud_sum, "gate": gate, "stability": stability}, ensure_ascii=False))


if __name__ == "__main__":
    main()
