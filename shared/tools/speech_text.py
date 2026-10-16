"""Turn script text into what the narrator should say (numbers and acronyms read the Chinese way).

  python3 tools/speech_text.py "2023 年底，250 多个板条箱……"     # print the spoken form

Rules:
  * 4-digit year before 年: digit by digit (2023 年 -> 二零二三年)
  * percent: 70% -> 百分之七十
  * decimal: 13.5 -> 十三点五, 0.33 -> 零点三三
  * integer: 250 -> 两百五十, 1840 -> 一千八百四十, 5100 -> 五千一百, 50000 -> 五万
  * a bare 2 before 百/千/万/亿/倍/个/次… -> 两 (2 万次 -> 两万次, 2 倍 -> 两倍)
  * acronyms / names / unit letters from episodes/<episode>/script/pronunciation.yaml
"""
import os
import re
import sys

import yaml

from paths import AUDIO, EP, REPO, RENDERS, SHARED  # noqa: E402,F401
DIG = "零一二三四五六七八九"
LIANG_BEFORE = "百千万亿倍个次位张台面片种发层吨辆家条年"


def _lex():
    p = os.path.join(EP, "script/pronunciation.yaml")
    d = yaml.safe_load(open(p, encoding="utf-8"))
    return d.get("lexicon") or {}, d.get("units_after_number") or {}


def _below_10k(n):
    """Chinese reading of 0 < n < 10000 with colloquial 两 for leading 2 in 百/千 places."""
    out, zero = "", False
    for unit, name in ((1000, "千"), (100, "百"), (10, "十")):
        q, n = divmod(n, unit)
        if q:
            if zero:
                out += "零"
            digit = "两" if (q == 2 and name in "千百") else DIG[q]
            out += digit + name
            zero = False
        elif out:
            zero = True
    if n:
        out += ("零" if zero else "") + DIG[n]
    return out


def int_zh(n):
    if n == 0:
        return "零"
    parts, out = [], ""
    for unit, name in ((100000000, "亿"), (10000, "万"), (1, "")):
        q, n = divmod(n, unit)
        parts.append((q, name))
    started, need_zero = False, False
    for q, name in parts:
        if q:
            seg = _below_10k(q)
            if started and (need_zero or q < 1000):
                out += "零"
            if q == 2 and name:
                seg = "两"
            out += seg + name
            started, need_zero = True, False
        elif started:
            need_zero = True
    if out.startswith("一十"):
        out = out[1:]
    return out


def _number(m):
    s = m.group(0).replace(",", "")
    if "." in s:
        a, b = s.split(".", 1)
        return int_zh(int(a)) + "点" + "".join(DIG[int(c)] for c in b)
    return int_zh(int(s))


def normalize(text):
    lex, units = _lex()
    s = text
    # years: digit by digit
    s = re.sub(r"(\d{4})\s*年", lambda m: "".join(DIG[int(c)] for c in m.group(1)) + "年", s)
    # percents
    s = re.sub(r"(\d+(?:\.\d+)?)\s*%",
               lambda m: "百分之" + _number(re.match(r".+", m.group(1))), s)
    # unit letters right after a number: "8 g" -> "8 G"
    for k, v in units.items():
        s = re.sub(rf"(\d)\s*{re.escape(k)}(?![A-Za-z])", rf"\1 {v}", s)
    # a bare 2 before a measure word or a large unit reads 两
    s = re.sub(rf"(?<![\d.])2\s*(?=[{LIANG_BEFORE}])", "两", s)
    # remaining numbers
    s = re.sub(r"\d[\d,]*(?:\.\d+)?", _number, s)
    # acronyms and names (longest first)
    for k in sorted(lex, key=len, reverse=True):
        s = re.sub(rf"(?<![A-Za-z]){re.escape(k)}(?![A-Za-z])", lex[k], s)
    # tidy spaces between CJK and the spelled-out pieces
    s = re.sub(r"(?<=[一-鿿])\s+(?=[一-鿿])", "", s)
    return s


if __name__ == "__main__":
    for t in sys.argv[1:] or ["2023 年底，一批特殊的货物从荷兰出发，运往美国俄勒冈。",
                              "250 多个板条箱，装满 43 个集装箱，坐了好几架货机，落地后又换上 20 辆卡车。",
                              "在 High-NA 上，晶圆台的加速度达到 8 g，掩模台达到 32 g。",
                              "每秒校正 2 万次，反射率最高能到约 70%，1840 亿个元件，5100 家供应商，0.33 和 0.55。"]:
        print(t, "\n→", normalize(t))
