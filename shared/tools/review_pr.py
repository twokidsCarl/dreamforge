"""Review a dreamforge pull request and enable auto-merge when it passes.

  python3 shared/tools/review_pr.py
  python3 shared/tools/review_pr.py --pr 12
  python3 shared/tools/review_pr.py --self-test

Checks YAML, facts.yaml, script lint, narration red lines, cross-episode
vocabulary, large binaries and secrets. On success, and only then:

  gh pr merge <pr> --auto --squash --match-head-commit <reviewed sha>

Never passes --admin and never force-merges. Branch protection is left to GitHub.
Exit 0 when the checks pass, even if the repo has not enabled auto-merge.
"""
import argparse
import json
import os
import re
import subprocess
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lint_script  # noqa: E402

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MARKER = "<!-- dreamforge-review -->"
MAX_BYTES = 2 * 1024 * 1024
EP_NAME = re.compile(r"^E[0-9]+-.+")
FACT_ID = re.compile(r"^F[0-9]+[a-z]?$")
FACT_MENTION = re.compile(r"F[0-9]+[a-z]?")
GRADE = re.compile(r"^(?:A|B|C)(?:/(?:A|B|C))*$")
MEDIA_EXT = {
    ".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v",
    ".blend", ".blend1",
    ".wav", ".mp3", ".flac", ".aac", ".aiff", ".aif", ".ogg",
    ".zip", ".7z", ".tar", ".gz", ".tgz", ".rar",
    ".psd", ".exr", ".hdr", ".tif", ".tiff",
    ".dmg", ".iso",
}
KEY_NAMES = {"id_rsa", "id_dsa", "id_ecdsa", "id_ed25519"}
BANNED = (
    "治愈失明",
    "治好盲人",
    "Boyden拿了诺奖",
    "Boyden是诺奖得主",
    "MCO-010已上市",
    "MCO-010已经上市",
    "光遗传已能操控思想",
    "洗脑",
    "改写人类记忆",
)
_BEGIN = "-----BEGIN "
_END = "PRIVATE KEY-----"
SECRET_RULES = (
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS access key"),
    (re.compile(r"ghp_[A-Za-z0-9]{36}"), "GitHub token"),
    (re.compile(r"github_pat_[A-Za-z0-9_]{22,}"), "GitHub fine-grained token"),
    (re.compile(r"ghs_[A-Za-z0-9]{36}"), "GitHub installation token"),
    (re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"), "Slack token"),
    (re.compile(r"sk-" + r"[A-Za-z0-9]{20,}"), "API key"),
    (re.compile(_BEGIN + r"(?:RSA |OPENSSH |EC |DSA )?" + _END), "private key"),
    (re.compile(r"(?i)(?:api[_-]?key|secret|password)\s*[:=]\s*['\"][^'\"]{8,}['\"]"), "assigned secret"),
)


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.notes = []
        self.merge = ""


def squash(text):
    return re.sub(r"[\s\u3000]", "", text or "")


def banned_in(text):
    flat = squash(text)
    return [phrase for phrase in BANNED if squash(phrase) in flat]


def secret_hits(text):
    return [name for pattern, name in SECRET_RULES if pattern.search(text or "")]


def grade_parts(grade):
    if not isinstance(grade, str) or not GRADE.match(grade):
        return None
    return grade.split("/")


def blob_problems(path, size):
    ext = os.path.splitext(path)[1].lower()
    base = os.path.basename(path)
    problems = []
    if base == ".env" or (base.startswith(".env.") and base != ".env.example"):
        problems.append("环境文件")
    if base in KEY_NAMES or ext in {".pem", ".p12", ".pfx", ".key"}:
        problems.append("密钥或证书")
    if ext in MEDIA_EXT:
        problems.append(f"媒体文件 {ext}")
    if size is not None and size > MAX_BYTES:
        problems.append(f"大于 2 MiB（{size} 字节）")
    return problems


def check_facts_mapping(data, label):
    errors = []
    if not isinstance(data, dict) or not data:
        return [f"{label}: 必须是非空映射"]
    seen = set()
    for fid, entry in data.items():
        where = f"{label}:{fid}"
        if not isinstance(fid, str) or not FACT_ID.match(fid):
            errors.append(f"{where}: 编号须为 F 加数字，最多再跟一个小写字母")
            continue
        if fid in seen:
            errors.append(f"{where}: 编号重复")
        seen.add(fid)
        if not isinstance(entry, dict):
            errors.append(f"{where}: 条目必须是映射")
            continue
        claim = entry.get("claim")
        if not isinstance(claim, str) or not claim.strip():
            errors.append(f"{where}: 缺少 claim")
        status = entry.get("status")
        allowed = {"verified", "disputed", "reported", "derived", "rejected", "needs_verification"}
        if status not in allowed:
            errors.append(f"{where}: status 不合法（{status!r}）")
            continue
        parts = None
        if "grade" in entry and entry.get("grade") is not None:
            parts = grade_parts(entry.get("grade"))
            if parts is None:
                errors.append(f"{where}: grade 只能是 A、B、C，或用 / 连起来（如 B/A）")
        elif status != "rejected":
            errors.append(f"{where}: 缺少 grade")
        if status == "needs_verification":
            if entry.get("verification") != "pending":
                errors.append(f"{where}: 必须写 verification: pending")
            source_type = entry.get("source_type")
            if not isinstance(source_type, str) or not source_type.strip():
                errors.append(f"{where}: 必须写 source_type")
            if parts and "C" in parts:
                errors.append(f"{where}: 待核实条目不能是 C 级")
        elif "verification" in entry:
            errors.append(f"{where}: verification 只和 needs_verification 一起用")
        if status in {"verified", "derived"} and parts not in (["A"], ["B"]):
            errors.append(f"{where}: {status} 的等级只能是 A 或 B")
        if status == "reported" and parts != ["C"]:
            errors.append(f"{where}: reported 必须是 C 级")
        if status == "disputed" and parts not in (["A"], ["B"], ["C"]):
            errors.append(f"{where}: disputed 的等级只能是 A、B 或 C")
        if status in {"verified", "disputed", "reported", "derived"}:
            sources = entry.get("sources")
            if not isinstance(sources, list) or not sources or not all(isinstance(s, str) and s.strip() for s in sources):
                errors.append(f"{where}: {status} 必须有非空 sources")
        elif "sources" in entry and entry.get("sources") not in (None, []):
            sources = entry.get("sources")
            if not isinstance(sources, list) or not all(isinstance(s, str) and s.strip() for s in sources):
                errors.append(f"{where}: sources 必须是非空字符串列表")
        if "segments" in entry:
            segments = entry["segments"]
            if not isinstance(segments, list) or not all(isinstance(s, str) and s.strip() for s in segments):
                errors.append(f"{where}: segments 必须是字符串列表")
        if "values" in entry and not isinstance(entry["values"], dict):
            errors.append(f"{where}: values 必须是映射")
        for key in ("notes", "narration", "source_type"):
            if key in entry and entry[key] is not None and not isinstance(entry[key], str):
                errors.append(f"{where}: {key} 必须是字符串")
    return errors


def duplicate_fact_keys(text, label):
    seen = {}
    errors = []
    for number, line in enumerate(text.splitlines(), 1):
        match = re.match(r"^(F[0-9]+[a-z]?):", line)
        if not match:
            continue
        fid = match.group(1)
        if fid in seen:
            errors.append(f"{label}:{fid}: 第 {seen[fid]} 行和第 {number} 行重复")
        else:
            seen[fid] = number
    return errors


def check_pronunciation(data, label):
    errors = []
    if data is None:
        data = {}
    if not isinstance(data, dict):
        return [f"{label}: pronunciation.yaml 必须是映射"]
    for key, expected in (("lexicon", "词表"), ("units_after_number", "单位表")):
        table = data.get(key, {})
        if table is None:
            table = {}
        if not isinstance(table, dict):
            errors.append(f"{label}: {key} 必须是映射")
            continue
        for name, spoken in table.items():
            if not isinstance(name, str) or not name.strip() or not isinstance(spoken, str) or not spoken.strip():
                errors.append(f"{label}: {expected}的「{name}」必须是非空字符串")
    return errors


def outline_mode(script_text):
    if "状态：定稿" in script_text:
        return False
    return "状态：大纲" in script_text


def iter_vo(node):
    if isinstance(node, dict):
        vo = node.get("vo")
        if isinstance(vo, str):
            yield vo
        elif isinstance(vo, list):
            for item in vo:
                if isinstance(item, str):
                    yield item
        for key, value in node.items():
            if key != "vo":
                yield from iter_vo(value)
    elif isinstance(node, list):
        for item in node:
            yield from iter_vo(item)


def parse_added_lines(diff_text):
    added = {}
    path = None
    new_line = None
    for line in diff_text.splitlines():
        if line.startswith("+++ "):
            raw = line[4:]
            path = raw[2:] if raw.startswith("b/") else None
            if path is not None:
                added.setdefault(path, set())
            new_line = None
            continue
        match = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
        if match:
            new_line = int(match.group(1))
            continue
        if path is None or new_line is None:
            continue
        if line.startswith("+"):
            added[path].add(new_line)
            new_line += 1
        elif line.startswith("-") or line.startswith("\\"):
            continue
        else:
            new_line += 1
    return added


def run(cmd, check=True, input=None):
    payload = None if input is None else input.encode("utf-8")
    proc = subprocess.run(cmd, cwd=REPO, capture_output=True, input=payload)
    stdout = proc.stdout.decode("utf-8", "replace")
    stderr = proc.stderr.decode("utf-8", "replace")
    if check and proc.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)}\n{stderr or stdout}")
    return proc.returncode, stdout, stderr


def git(*args, check=True):
    return run(["git", "--no-pager", *args], check=check)


def have_commit(sha):
    code, _, _ = run(["git", "cat-file", "-e", f"{sha}^{{commit}}"], check=False)
    return code == 0


TEXT_EXT = {".md", ".yaml", ".yml", ".html", ".htm", ".py", ".txt", ".csv", ".json"}


def foreign_term_hits(text, terms):
    folded = text.casefold()
    return [term for term in terms if term.casefold() in folded]


def exclusive_terms_by_episode():
    found = {}
    for name in episodes_on_disk():
        path = os.path.join(REPO, "episodes", name, "storyboard", "page.yaml")
        if not os.path.isfile(path):
            continue
        data = yaml.safe_load(open(path, encoding="utf-8")) or {}
        raw = data.get("exclusive_terms") or []
        words = [term.strip() for term in raw if isinstance(term, str) and term.strip()]
        if words:
            found[name] = words
    return found


def cross_episode_terms(report):
    """Flag another episode's title or exclusive words inside this episode's files."""
    owned = exclusive_terms_by_episode()
    for name in episodes_on_disk():
        banned = [term for other, words in owned.items() if other != name for term in words]
        if not banned:
            continue
        root = os.path.join(REPO, "episodes", name)
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in {"renders", "audio", "__pycache__"}]
            for filename in filenames:
                if os.path.splitext(filename)[1].lower() not in TEXT_EXT:
                    continue
                path = os.path.join(dirpath, filename)
                try:
                    text = open(path, encoding="utf-8").read()
                except (UnicodeDecodeError, OSError):
                    continue
                hits = foreign_term_hits(text, banned)
                if hits:
                    rel = os.path.relpath(path, REPO)
                    report.errors.append(f"{rel}: 含有其他期的专属词 {', '.join(hits)}")


def episodes_on_disk():
    root = os.path.join(REPO, "episodes")
    names = []
    if not os.path.isdir(root):
        return names
    for name in sorted(os.listdir(root)):
        if EP_NAME.match(name) and os.path.isdir(os.path.join(root, name)):
            names.append(name)
    return names


def self_test():
    failures = []

    def check(cond, message):
        if not cond:
            failures.append(message)

    check(banned_in("Boyden 拿了诺奖") == ["Boyden拿了诺奖"], "spaced Boyden phrase")
    check(banned_in("Boyden 等人；诺奖三人的名单里没有这一位") == [], "Boyden attribution")
    check(banned_in("MCO-010已上市") == ["MCO-010已上市"], "listed phrase")
    check(banned_in("MCO-010 尚未获批") == [], "not yet approved")
    check(banned_in("没有上市许可") == [], "no licence")
    check("治愈失明" in banned_in("不能说治愈失明"), "cure phrase")
    check(banned_in("部分复明") == [], "partial restoration")

    sample_key = "AKIA" + "IOSFODNN7EXAMPLE"
    check(secret_hits(sample_key) == ["AWS access key"], "aws sample")
    check(secret_hits("ghp_" + ("a" * 36)) == ["GitHub token"], "ghp sample")
    check(secret_hits("ghp_short") == [], "short token")
    check(secret_hits(_BEGIN + _END) == ["private key"], "pem header")
    own = open(os.path.abspath(__file__), encoding="utf-8").read()
    check(secret_hits(own) == [], "scanner matches its own source: " + ",".join(secret_hits(own)))
    for rel in ("docs/REVIEW.md", ".github/workflows/review.yml"):
        path = os.path.join(REPO, rel)
        if os.path.exists(path):
            hits = secret_hits(open(path, encoding="utf-8").read())
            check(hits == [], f"{rel} secret false positive: {hits}")

    check(blob_problems("episodes/E2/renders/a.mp4", 10) == ["媒体文件 .mp4"], "video")
    check(blob_problems("episodes/E2/tex/a.png", 1000) == [], "small png")
    check(blob_problems("notes.txt", MAX_BYTES + 1) == [f"大于 2 MiB（{MAX_BYTES + 1} 字节）"], "size")
    check(blob_problems(".env", 4)[0] == "环境文件", "dotenv")

    pending = {
        "F1": {
            "claim": "示例",
            "grade": "B/A",
            "status": "needs_verification",
            "verification": "pending",
            "source_type": "论文 + 公告",
            "segments": [],
        }
    }
    check(check_facts_mapping(pending, "seed") == [], "pending B/A")
    bad = {"F1": {"claim": "示例", "grade": "C", "status": "verified", "sources": ["https://example.test"]}}
    check(any("等级只能是 A 或 B" in item for item in check_facts_mapping(bad, "bad")), "verified C")
    rejected = {"F9": {"claim": "不用", "status": "rejected", "notes": "没有出处"}}
    check(check_facts_mapping(rejected, "rej") == [], "rejected without grade")
    missing = {"F1": {"claim": "示例", "grade": "A", "status": "verified"}}
    check(any("sources" in item for item in check_facts_mapping(missing, "src")), "verified needs sources")

    diff = "\n".join([
        "diff --git a/f b/f",
        "--- a/f",
        "+++ b/f",
        "@@ -10,0 +11,2 @@",
        "+line a",
        "+line b",
        "@@ -20 +22 @@",
        "-old",
        "+new",
    ])
    added = parse_added_lines(diff)
    check(added.get("f") == {11, 12, 22}, f"added lines {added}")

    check(outline_mode("状态：大纲\n") is True, "outline")
    check(outline_mode("状态：大纲\n状态：定稿\n") is False, "final overrides")
    check(outline_mode("定稿旁白") is False, "no marker")
    check(foreign_term_hits("这里写了 EUV 光刻机", ["光刻机", "EUV"]) == ["光刻机", "EUV"], "foreign terms")
    check(foreign_term_hits("通道是 euv 的误植", ["EUV"]) == ["EUV"], "casefold foreign term")
    check(foreign_term_hits("光遗传学的开关", ["光刻机", "EUV", "ASML"]) == [], "own episode")
    vocab = Report()
    cross_episode_terms(vocab)
    check(vocab.errors == [], "episode trees mix foreign terms: " + " | ".join(vocab.errors[:4]))
    check(check_pronunciation({"lexicon": {}, "units_after_number": {}}, "p") == [], "empty lexicon")

    for rel in (
        "episodes/E1-euv-lithography/research/facts.yaml",
        "episodes/E2-optogenetics/research/facts.yaml",
    ):
        path = os.path.join(REPO, rel)
        if not os.path.exists(path):
            continue
        text = open(path, encoding="utf-8").read()
        data = yaml.safe_load(text)
        problems = duplicate_fact_keys(text, rel) + check_facts_mapping(data, rel)
        check(problems == [], f"{rel}: {problems[:3]}")
    e2_script = os.path.join(REPO, "episodes/E2-optogenetics/script/script_zh.md")
    if os.path.exists(e2_script):
        hits = banned_in(open(e2_script, encoding="utf-8").read())
        check(hits == [], f"E2 script banned {hits}")
    if failures:
        raise SystemExit("self-test failed:\n" + "\n".join(failures))


def load_yaml_files(report):
    code, listing, err = git("ls-tree", "-r", "--name-only", "HEAD")
    if code != 0:
        report.errors.append(f"无法列出 HEAD 的文件：{err.strip()}")
        return {}
    paths = [p for p in listing.splitlines() if p.endswith((".yaml", ".yml"))]
    loaded = {}
    for path in paths:
        code, text, err = git("show", f"HEAD:{path}")
        if code != 0:
            report.errors.append(f"{path}: 读不出文件（{err.strip()}）")
            continue
        try:
            loaded[path] = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            report.errors.append(f"{path}: YAML 无法解析（{exc}）")
            continue
        if path.endswith("/research/facts.yaml"):
            report.errors.extend(duplicate_fact_keys(text, path))
            if loaded[path] is None:
                report.errors.append(f"{path}: 是空文件")
            else:
                report.errors.extend(check_facts_mapping(loaded[path], path))
        if path.endswith("/script/pronunciation.yaml"):
            report.errors.extend(check_pronunciation(loaded[path], path))
    report.notes.append(f"YAML：{len(paths)} 个文件可解析" if not any(e.startswith(p) for p in paths for e in report.errors) else f"YAML：检查了 {len(paths)} 个文件")
    return loaded


def lint_episodes(report):
    for name in episodes_on_disk():
        script = os.path.join(REPO, "episodes", name, "script", "script_zh.md")
        facts = os.path.join(REPO, "episodes", name, "research", "facts.yaml")
        pron = os.path.join(REPO, "episodes", name, "script", "pronunciation.yaml")
        if not os.path.isfile(facts):
            report.errors.append(f"{name}: 缺少 research/facts.yaml")
        if not os.path.isfile(script):
            report.errors.append(f"{name}: 缺少 script/script_zh.md")
            continue
        if not os.path.isfile(pron):
            report.errors.append(f"{name}: 缺少 script/pronunciation.yaml")
        env = os.environ.copy()
        env["DREAMFORGE_EPISODE"] = name
        proc = subprocess.run(
            [sys.executable, os.path.join(REPO, "shared/tools/lint_script.py"), script],
            cwd=REPO, env=env, capture_output=True,
        )
        out = (proc.stdout + proc.stderr).decode("utf-8", "replace")
        total = next((line for line in out.splitlines() if line.startswith("total")), "")
        if proc.returncode != 0:
            tail = "\n".join(line for line in out.splitlines() if line.startswith("ERROR"))
            report.errors.append(f"{name}: lint_script.py 失败\n{tail or out[-1500:]}")
        else:
            report.notes.append(f"lint {name}：通过{(' ' + total) if total else ''}")


def narration_red_lines(report, loaded, added):
    c_warn = {}
    pending_warn = {}
    for name in episodes_on_disk():
        rel = f"episodes/{name}/script/script_zh.md"
        path = os.path.join(REPO, rel)
        if not os.path.isfile(path):
            continue
        text = open(path, encoding="utf-8").read()
        hits = banned_in(text)
        if hits:
            report.errors.append(f"{rel}: 含禁止说法 {', '.join(hits)}")
        facts = loaded.get(f"episodes/{name}/research/facts.yaml")
        if not isinstance(facts, dict):
            continue
        new_lines = added.get(rel, set())
        pending_ids = set()
        pending_errors = 0
        for seg in lint_script.parse(path):
            for line in seg["lines"]:
                for ref in line["refs"]:
                    fact = facts.get(ref)
                    if not isinstance(fact, dict):
                        continue
                    if fact.get("grade") == "C":
                        if line["ln"] in new_lines:
                            report.errors.append(f"{rel}:{line['ln']}: 新旁白引用 C 级事实 {ref}")
                        else:
                            c_warn.setdefault(name, {}).setdefault(ref, 0)
                            c_warn[name][ref] += 1
                    if fact.get("status") == "needs_verification":
                        if outline_mode(text):
                            pending_ids.add(ref)
                        else:
                            pending_errors += 1
                            report.errors.append(f"{rel}:{line['ln']}: 定稿旁白引用了未核实事实 {ref}")
        if pending_ids:
            ids = ", ".join(sorted(pending_ids, key=lambda s: (int(re.sub(r'\D', '', s) or 0), s)))
            pending_warn[name] = (ids, len(pending_ids))
        if pending_errors:
            pass
    for name, refs in sorted(c_warn.items()):
        ids = ", ".join(sorted(refs))
        count = sum(refs.values())
        report.warnings.append(
            f"{name}: 既存旁白有 {count} 句引用 C 级事实（{ids}）。这些行不在本次 diff 里，只警告；改到它们会变成错误。"
        )
    for name, (ids, count) in sorted(pending_warn.items()):
        report.warnings.append(
            f"{name}: 大纲引用了 {count} 条未核实事实（{ids}）。文件仍标着「状态：大纲」，所以只警告；去掉该标记后这些引用会变成错误。"
        )
    for path, new_lines in added.items():
        if "/storyboard/" not in path or not path.endswith((".yaml", ".yml")):
            continue
        match = re.match(r"episodes/([^/]+)/", path)
        if not match:
            continue
        facts = loaded.get(f"episodes/{match.group(1)}/research/facts.yaml")
        if not isinstance(facts, dict):
            continue
        code, text, _ = git("show", f"HEAD:{path}", check=False)
        if code != 0:
            continue
        lines = text.splitlines()
        for number in sorted(new_lines):
            if number < 1 or number > len(lines):
                continue
            for fid in FACT_MENTION.findall(lines[number - 1]):
                fact = facts.get(fid)
                if isinstance(fact, dict) and fact.get("grade") == "C":
                    report.errors.append(f"{path}:{number}: 新分镜行引用 C 级事实 {fid}")
    for path, data in loaded.items():
        if "/storyboard/" not in path:
            continue
        for vo in iter_vo(data):
            hits = banned_in(vo)
            if hits:
                report.errors.append(f"{path}: 旁白含禁止说法 {', '.join(hits)}")


def diff_hygiene(report, base, head, added):
    code, names, err = git("diff", "--name-only", "--diff-filter=AM", f"{base}...{head}")
    if code != 0:
        report.errors.append(f"无法比较 {base[:8]}...{head[:8]}：{err.strip()}")
        return
    for path in [p for p in names.splitlines() if p]:
        code, size_text, _ = git("cat-file", "-s", f"{head}:{path}", check=False)
        size = int(size_text.strip()) if code == 0 and size_text.strip().isdigit() else None
        problems = blob_problems(path, size)
        for problem in problems:
            report.errors.append(f"{path}: {problem}")
    code, diff_text, err = git("diff", "-U0", "--no-ext-diff", f"{base}...{head}")
    if code != 0:
        report.errors.append(f"无法读取 diff：{err.strip()}")
        return
    secret_files = {}
    current = None
    for line in diff_text.splitlines():
        if line.startswith("+++ "):
            raw = line[4:]
            current = raw[2:] if raw.startswith("b/") else None
            continue
        if current and line.startswith("+") and not line.startswith("+++"):
            hits = secret_hits(line[1:])
            if hits:
                secret_files.setdefault(current, set()).update(hits)
    for path, hits in sorted(secret_files.items()):
        report.errors.append(f"{path}: 新增内容像是秘密（{', '.join(sorted(hits))}）")
    added.clear()
    added.update(parse_added_lines(diff_text))


def classify_merge_failure(text):
    low = text.lower()
    if "auto merge is not allowed" in low or "enablepullrequestautomerge" in low or "allow auto-merge" in low:
        return "setting"
    if "resource not accessible" in low or "http 403" in low or "requires authentication" in low:
        return "permission"
    return "other"


def format_report(report, pr_url):
    passed = not report.errors
    lines = [MARKER, "", f"## 审查结果：{'通过' if passed else '未通过'}", ""]
    if pr_url:
        lines.append(pr_url)
        lines.append("")
    lines.append("### 检查")
    if report.notes:
        lines.extend(f"- {note}" for note in report.notes)
    else:
        lines.append("- （无）")
    lines.append("")
    lines.append("### 错误")
    if report.errors:
        lines.extend(f"- {item}" for item in report.errors)
    else:
        lines.append("- 无")
    lines.append("")
    lines.append("### 警告")
    if report.warnings:
        lines.extend(f"- {item}" for item in report.warnings)
    else:
        lines.append("- 无")
    lines.append("")
    lines.append("### 自动合并")
    lines.append(report.merge or "未执行。")
    lines.append("")
    lines.append("只使用 `gh pr merge --auto --squash`。不强制合并，也不绕过分支保护。")
    text = "\n".join(lines) + "\n"
    if len(text) > 60000:
        text = text[:59000] + "\n\n…（评论被截断）\n"
    return text


def repo_slug():
    _, out, _ = run(["gh", "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"])
    return out.strip()


def find_comment(repo, number):
    code, out, err = run(
        ["gh", "api", "--paginate", f"repos/{repo}/issues/{number}/comments",
         "--jq", r'.[] | "\(.id)\t\(.body[0:80])"'],
        check=False,
    )
    if code != 0:
        raise RuntimeError(err or out)
    found = None
    for line in out.splitlines():
        if "\t" not in line or MARKER not in line:
            continue
        found = line.split("\t", 1)[0].strip()
    return found


def post_comment(repo, number, body):
    existing = find_comment(repo, number)
    payload = json.dumps({"body": body}, ensure_ascii=False)
    if existing:
        run(["gh", "api", "--method", "PATCH", f"repos/{repo}/issues/comments/{existing}", "--input", "-"], input=payload)
        return "updated"
    run(["gh", "api", "--method", "POST", f"repos/{repo}/issues/{number}/comments", "--input", "-"], input=payload)
    return "created"


def pr_info(number):
    _, out, _ = run(["gh", "pr", "view", str(number), "--json",
                     "number,url,state,headRefOid,baseRefOid,isCrossRepository,headRepository"])
    return json.loads(out)


def same_repo(info):
    if "isCrossRepository" in info:
        return not info["isCrossRepository"]
    head = (info.get("headRepository") or {}).get("nameWithOwner")
    return bool(head)


def enable_auto_merge(number, sha):
    code, out, err = run(
        ["gh", "pr", "merge", str(number), "--auto", "--squash", "--match-head-commit", sha],
        check=False,
    )
    text = (out + "\n" + err).strip()
    if code == 0 or "already" in text.lower() and "auto" in text.lower():
        return True, text or "已启用 squash 自动合并。"
    return False, text


def disable_auto_merge(number):
    run(["gh", "pr", "merge", str(number), "--disable-auto"], check=False)


def review(base, head):
    report = Report()
    if not have_commit(base):
        code, _, err = run(["git", "fetch", "origin", base], check=False)
        if code != 0 or not have_commit(base):
            report.errors.append(f"找不到 base 提交 {base}：{err.strip()}")
            return report
    if not have_commit(head):
        report.errors.append(f"找不到 head 提交 {head}")
        return report
    added = {}
    diff_hygiene(report, base, head, added)
    loaded = load_yaml_files(report)
    lint_episodes(report)
    narration_red_lines(report, loaded, added)
    cross_episode_terms(report)
    if not report.errors:
        report.notes.append("旁白红线、大文件、秘密、跨期用词：通过")
    return report


def main():
    parser = argparse.ArgumentParser(description="审查 dreamforge 拉取请求，通过后启用 squash 自动合并")
    parser.add_argument("--pr", type=int, help="拉取请求编号；默认读 PR_NUMBER，再否则看当前分支")
    parser.add_argument("--no-comment", action="store_true")
    parser.add_argument("--no-merge", action="store_true")
    parser.add_argument("--allow-dirty", action="store_true", help="工作区不干净也继续（不会用于自动合并）")
    parser.add_argument("--self-test", action="store_true", help="只跑内置自检")
    args = parser.parse_args()
    self_test()
    if args.self_test:
        print("self-test passed")
        return 0

    _, porcelain, _ = git("status", "--porcelain")
    if porcelain.strip() and not args.allow_dirty:
        print(porcelain)
        print("工作区有未提交的改动。先提交，再审查。")
        return 1

    number = args.pr
    if number is None and os.environ.get("PR_NUMBER"):
        number = int(os.environ["PR_NUMBER"])
    if number is None and not args.no_comment:
        code, out, _ = run(["gh", "pr", "view", "--json", "number", "--jq", ".number"], check=False)
        if code == 0 and out.strip().isdigit():
            number = int(out.strip())

    info = None
    if number is not None:
        try:
            info = pr_info(number)
        except RuntimeError as exc:
            print(exc)
            return 1
        base = os.environ.get("REVIEW_BASE") or info["baseRefOid"]
        head = os.environ.get("REVIEW_HEAD") or info["headRefOid"]
        _, local, _ = git("rev-parse", "HEAD")
        if local.strip() != info["headRefOid"]:
            print(f"本地 HEAD {local.strip()} 不是 PR #{number} 的头 {info['headRefOid']}。先推送。")
            return 1
        head = info["headRefOid"]
    else:
        base = os.environ.get("REVIEW_BASE") or "origin/main"
        _, head, _ = git("rev-parse", "HEAD")
        head = head.strip()

    report = review(base, head)
    if info and not same_repo(info):
        report.merge = "PR 来自 fork，不启用自动合并。"
    elif info and info.get("state") != "OPEN":
        report.merge = f"PR 状态是 {info.get('state')}，不启用自动合并。"
    elif report.errors:
        report.merge = "检查未通过，不启用自动合并。"
        if info and not args.no_merge:
            disable_auto_merge(info["number"])
            report.merge += " 已尝试关闭这一 PR 上已有的自动合并。"
    elif info and args.no_merge:
        report.merge = "检查通过。按参数跳过了自动合并。"
    elif info:
        ok, detail = enable_auto_merge(info["number"], info["headRefOid"])
        if ok:
            report.merge = "检查通过，已执行 `gh pr merge --auto --squash`。"
            if detail:
                report.merge += " " + detail.splitlines()[0][:400]
        else:
            kind = classify_merge_failure(detail)
            if kind == "setting":
                report.merge = (
                    "检查通过，但仓库没有打开 Allow auto-merge，GitHub 拒绝了 `gh pr merge --auto --squash`。"
                    "需要有管理员权限的人在 Settings → General → Pull Requests 里打开 Allow auto-merge。"
                    "脚本改不了这项设置，也没有改用强制合并。"
                )
            elif kind == "permission":
                report.merge = (
                    "检查通过，但当前令牌不能启用自动合并（GitHub 403）。"
                    "没有改用强制合并。请用有 Pull requests 写权限的身份重跑，并确认仓库已打开 Allow auto-merge。"
                )
            else:
                report.merge = "检查通过，但启用自动合并失败，没有改用强制合并。GitHub 说：" + detail[:800]
    else:
        report.merge = "检查已跑完。当前没有 PR，所以没有评论，也没有启用自动合并。"

    if not report.errors and info and report.merge.startswith("检查通过，但"):
        report.notes.append("自动合并没有打开，原因见文末。这不把内容检查判失败。")

    body = format_report(report, info.get("url") if info else "")
    print(body)
    if info and not args.no_comment:
        try:
            action = post_comment(repo_slug(), info["number"], body)
            print(f"comment {action}")
        except RuntimeError as exc:
            print(f"评论没有发出：{exc}")
            if not report.errors:
                report.notes.append("评论失败")
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
