"""The context prompt every speech-recognition pass uses: plain Mandarin narration plus the episode's domain terms
(episodes/<ep>/script/asr_terms.txt), so technical words are recognised as words, not as everyday homophones."""
import os

from paths import EP


def asr_terms():
    p = os.path.join(EP, "script", "asr_terms.txt")
    if not os.path.exists(p):
        return []
    return [ln.strip() for ln in open(p, encoding="utf-8") if ln.strip() and not ln.startswith("#")]


def asr_prompt():
    terms = asr_terms()
    return "以下是普通话科普旁白，使用简体中文。" + ("术语：" + "、".join(terms) + "。" if terms else "")
