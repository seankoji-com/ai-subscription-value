"""Build the report data: subscription cost per agentic-coding task for each model and effort level.

usage: python3 src/generate.py data/ site/data.json

Inputs (data/):
  aa-coding-agents-2026-10-27.json  Artificial Analysis Coding Agent Index v2.0, via hraness/aicharts (commit e8e50a2316)
  aa-coding-agents-2026-10-05.json  the previous AA snapshot (commit 0529938df7), used for Sonnet 5.5 and GPT-6.1 Sol effort levels

Method
  score         = AA Coding Agent Index = mean of FrontierCode, Terminal-Bench 4.0 and SWE-Atlas QnA pass rates
  tasks/month   = plan capacity (API-equivalent $/month) / API cost per task
  $/task        = plan price / tasks per month
Effort levels that AA's coding index doesn't publish are modelled; every point carries its working.
"""
import json, os, statistics, sys

DATA, OUT = sys.argv[1], sys.argv[2]
V2 = json.load(open(os.path.join(DATA, "aa-coding-agents-2026-10-27.json")))["records"]
OLD = json.load(open(os.path.join(DATA, "aa-coding-agents-2026-10-05.json")))["records"]
WK = 52 / 12  # weeks per month


def money(v):
    return f"${v:,.2f}" if v >= 1 else (f"${v:.3f}" if v >= 0.01 else f"${v:.4f}")


def exact(v):
    """Money with enough significant figures to reproduce a division."""
    return f"${v:,.3f}" if v >= 1 else f"${v:.5g}"


def find(rows, agent, model, setting):
    for r in rows:
        if r["agent"] == agent and r["model"] == model and r["setting"] == setting:
            b = r["benchmarks"]
            return dict(api=r["economics"]["costUsd"], mins=r["economics"]["durationSeconds"] / 60, idx=b["aaIndex"],
                        comps=(b.get("deepSwe"), b.get("terminalBench"), b.get("sweAtlas")), agent=agent, setting=setting)
    raise KeyError((agent, model, setting))


def v2(a, m, s):
    return find(V2, a, m, s)


# ---------------- plans and capacity ----------------
# Top plan per provider; OpenCode Go for models without a plan of their own.
# Capacity is API-equivalent USD per month from public sources. "models" holds model-specific measurements;
# other models on a plan use "plan_cap" and are graded inferred.
PLANS = {
    "claude": dict(provider="Claude", plan="Claude Ultra (was Max 20x)", price=200, plan_cap=1549 * WK,
                   models={"Opus 5.5": (1549 * WK, "wokey.ai plan median $1,549/week (Claude Code traffic) × 52/12 weeks. A RemakeBench receipt that was 96% Opus implies more, ≈$2,155/week"),
                           "Sonnet 5.5": (1549 * WK, "wokey.ai plan median $1,549/week × 52/12 weeks; one creator's Sonnet report (≈$1,523/week) agrees")},
                   cap_src="wokey.ai plan median $1,549/week (18 accounts, 26 Oct–2 Nov 2026) × 52/12 weeks, applied plan-wide",
                   cap_url="https://wokey.ai/claude-usage-limits",
                   alt="Top Claude plan (Max 20x, renamed Ultra on 30 Oct 2026). Pro $20 measures the same value per dollar."),
    "chatgpt": dict(provider="ChatGPT", plan="ChatGPT Pro $500 (Codex)", price=500, plan_cap=581 * WK * 6955 / 2897,
                    models={"GPT-6 Astra": (6955, "SemiAnalysis Astra-only measurement on Pro $500, $6,955/month (5 Oct 2026)")},
                    cap_src="No Sol-class measurement exists on Pro $500, so wokey's Pro $200 Sol median ($581/week × 52/12) is scaled by SemiAnalysis's Pro $500 ÷ Pro $200 ratio ($6,955 ÷ $2,897 = 2.40×) ≈ $1,395/week; codex-reset's Pro $500 estimates ($1,010–$1,640/week) bracket it",
                    cap_url="https://wokey.ai/codex-usage-limits",
                    alt="Top ChatGPT plan. Per dollar it measures about 4% below Pro $200 (Astra-only: 13.9× vs 14.5×)."),
    "gemini": dict(provider="Gemini", plan="Google AI Ultra 20× ($199.99)", price=199.99, plan_cap=4 * 3780.38, models={},
                   cap_src="Inferred: Google publishes no quota. Ultra 5× ($100) September scenario $3,780/month (range $1,890–$5,671) × 4, since Ultra 20× is 4× the 5× tier",
                   cap_url="https://aiandtractors.com/coding-agent-subscription-costs/",
                   alt="Top Google AI plan (20× AI Pro's limits)."),
    "grok": dict(provider="Grok", plan="SuperGrok Heavy ($300)", price=300, plan_cap=400.5 * WK,
                 models={"Grok 4.7": (400.5 * WK, "single RemakeBench receipt: $76.10 of API-equivalent use moved the weekly meter 19 points, mostly Grok 4.7 xhigh → ≈$400.5/week × 52/12 (n=1)")},
                 cap_src="single RemakeBench receipt, ≈$400.5/week × 52/12 (n=1)",
                 cap_url="https://aiandtractors.com/coding-agent-subscription-costs/",
                 alt="Top Grok plan, and the only one with any capacity evidence."),
    "muse": dict(provider="Muse", plan="Muse Code Maximum ($200)", price=200, plan_cap=1549 * WK, models={},
                 cap_src="Assumed: Meta publishes Muse Code limits only as prompts per 5 hours (Maximum = 80× Everyday), so this assumes the same API-equivalent value per dollar as Claude Ultra's measured $1,549/week",
                 cap_url="https://ratelimitnow.com/limits/muse-code/",
                 alt="Top Muse Code plan (80× Everyday). Power ($50, 20×) ties on multiplier per dollar."),
    "opencode": dict(provider="OpenCode Go", plan="OpenCode Go ($10)", price=10, plan_cap=None, models={},
                     cap_src="Official per-model monthly usage allowance on opencode.ai/go (limits are per model)",
                     cap_url="https://opencode.ai/go",
                     alt="Used for models with no plan of their own here (DeepSeek, Kimi). Go Plus $40 gives 2–4× the allowance per model: never better per dollar."),
}
GO_ALLOWANCE = {"DeepSeek V4.1 Flash": 100, "Kimi K3": 15}
MAKER = {"claude": "Claude", "chatgpt": "ChatGPT", "gemini": "Gemini", "grok": "Grok", "muse": "Muse"}
FAMILY_MAKER = {"DeepSeek V4.1 Flash": "DeepSeek", "Kimi K3": "Kimi"}

DIRECT, SCALED, MODELLED, PROXY = "direct", "scaled", "modelled", "proxy-harness"


def row(plan, family, label, effort, api, mins, idx, basis=DIRECT, note="", go_allowance=None, comps=None, agent=None, setting=None, deriv=None):
    return dict(plan=plan, family=family, label=label, effort=effort, api=api, mins=mins, idx=idx, basis=basis, note=note,
                go_allowance=go_allowance, comps=comps, agent=agent, deriv=deriv)


def direct(plan, family, label, effort, rec, **kw):
    """A row measured by AA in the current index."""
    return row(plan, family, label, effort, rec["api"], rec["mins"], rec["idx"], comps=rec["comps"], agent=rec["agent"], **kw)


def scaled(agent, model, setting):
    """Effort row from the 5 Oct snapshot, rescaled so its max row matches the current index's max row."""
    old_e, old_max, new_max = find(OLD, agent, model, setting), find(OLD, agent, model, "max"), find(V2, agent, model, "max")
    rc, rt, rs = new_max["api"] / old_max["api"], new_max["mins"] / old_max["mins"], new_max["idx"] / old_max["idx"]
    deriv = dict(
        score=f"5 Oct snapshot score at {setting} {old_e['idx']:.2f} × (current max {new_max['idx']:.2f} ÷ 5 Oct max {old_max['idx']:.1f} = {rs:.5g})",
        api=f"5 Oct API cost at {setting} {exact(old_e['api'])} × (current max {exact(new_max['api'])} ÷ 5 Oct max {exact(old_max['api'])} = {rc:.5g})",
        mins=f"5 Oct time at {setting} {old_e['mins']:.2f} min × (current max {new_max['mins']:.1f} ÷ 5 Oct max {old_max['mins']:.1f} = {rt:.5g})")
    return dict(api=old_e["api"] * rc, mins=old_e["mins"] * rt, idx=old_e["idx"] * rs, deriv=deriv, agent=agent)


# Opus 5.5 below max: Anthropic's own effort curve (platform docs, "Optimizing for cost and intelligence"):
#   SWE-bench Pro subset cost/task low .11 medium .21 high .29 xhigh .74; solved 87.4 / 92.8 / 95.3 / 96.7 %
#   Terminal-Bench 4.0 medium 57.6 %, high 64.2 %, xhigh 66.4 %; low ~19 points below medium
# Anthropic publishes no max row, so the xhigh→max step uses AA's Opus effort data (Intelligence Index, BenchLeader):
#   cost xhigh $6.05 → max $10.04, tokens 103k → 173k, index 66.2 → 69.3.
ANTH_COST = {"low": 0.11, "medium": 0.21, "high": 0.29, "xhigh": 0.74}
ANTH_SWE = {"low": 87.4, "medium": 92.8, "high": 95.3, "xhigh": 96.7}
ANTH_TB = {"low": 57.6 - 19, "medium": 57.6, "high": 64.2, "xhigh": 66.4}
AA_OPUS_TOK = {"low": 19, "medium": 44, "high": 60, "xhigh": 103, "max": 173}
X2M_COST, X2M_IDX = 10.04 / 6.05, 69.3 / 66.2


def opus_curve(e):
    mx = v2("Claude Code", "Opus 5.5", "max")
    rel = (ANTH_SWE[e] / ANTH_SWE["xhigh"] + ANTH_TB[e] / ANTH_TB["xhigh"]) / 2
    api = mx["api"] / X2M_COST * ANTH_COST[e] / ANTH_COST["xhigh"]
    mins = mx["mins"] * AA_OPUS_TOK[e] / AA_OPUS_TOK["max"]
    idx = mx["idx"] / X2M_IDX * rel
    deriv = dict(
        score=f"AA max score {mx['idx']:.2f} ÷ 1.047 (AA's xhigh→max step) × {rel:.5g} (mean of Anthropic's SWE-bench Pro {ANTH_SWE[e]}/{ANTH_SWE['xhigh']} and Terminal-Bench {ANTH_TB[e]:.1f}/{ANTH_TB['xhigh']}, relative to xhigh)",
        api=f"AA max API cost {exact(mx['api'])} ÷ 1.66 (AA's xhigh→max step) × {ANTH_COST[e] / ANTH_COST['xhigh']:.5g} (Anthropic's cost at {e} ${ANTH_COST[e]} ÷ xhigh ${ANTH_COST['xhigh']})",
        mins=f"AA max time {mx['mins']:.2f} min × {AA_OPUS_TOK[e]}k ÷ {AA_OPUS_TOK['max']}k (AA's Opus output tokens at {e} vs max)")
    return dict(api=api, mins=mins, idx=idx, deriv=deriv, agent="Claude Code")


# AA Intelligence Index per effort (BenchLeader, 4 Nov 2026): (cost/task, index, output tokens k).
# Used only for the shape of each model's effort curve.
INTEL = {
    "Fable 5.1": {"low": (4.47, 59.1, 38), "medium": (5.56, 62.2, 49), "high": (7.54, 63.9, 66), "xhigh": (10.85, 65.2, 97), "max": (12.99, 67.2, 118)},
    "Haiku 5.5": {"low": (0.044, 47.9, 28), "medium": (0.092, 50.3, 53), "high": (0.159, 55.8, 88), "xhigh": (0.248, 57.1, 136), "max": (0.411, 57.0, 226)},
    "GPT-6 Astra": {"low": (1.42, 62.6, 9), "medium": (2.73, 65.0, 18), "high": (3.24, 66.9, 23), "xhigh": (3.66, 66.7, 27), "max": (6.24, 67.8, 52)},
    "GPT-6 Luna": {"low": (0.0051, 45.8, 3), "medium": (0.042, 49.8, 20), "high": (0.073, 51.3, 33), "xhigh": (0.104, 52.2, 44), "max": (0.152, 56.7, 75)},
    "Grok 4.7": {"low": (2.92, 55.8, 43), "high": (6.18, 57.5, 89), "xhigh": (7.77, 58.2, 105)},
}
# DeepSeek V4.1 Flash on the Intelligence Index publishes only no-reasoning ($0.425, 45.0, 65k tokens, 6 min),
# high (score 51.4 only) and max ($0.602, 59.1, 139k tokens, 10 min). Low and medium aren't published anywhere, so:
#   score   low/medium: evenly between no-reasoning and the measured high score; high: measured
#   cost, tokens: geometric steps from no-reasoning to max (no-reasoning < low < medium < high < max)
DS_NONE, DS_MAX, DS_HIGH_SCORE = (0.425, 45.0, 65), (0.602, 59.1, 139), 51.4
_steps = {"low": 1, "medium": 2, "high": 3}
DS_EFFORT = {}
for _e, _k in _steps.items():
    _cost = DS_NONE[0] * (DS_MAX[0] / DS_NONE[0]) ** (_k / 4)
    _tok = DS_NONE[2] * (DS_MAX[2] / DS_NONE[2]) ** (_k / 4)
    _score = DS_HIGH_SCORE if _e == "high" else DS_NONE[1] + (DS_HIGH_SCORE - DS_NONE[1]) * _k / 3
    DS_EFFORT[_e] = (_cost, _score, _tok)
DS_EFFORT["max"] = DS_MAX

rows = []
add = rows.append
# Claude
add(direct("claude", "Opus 5.5", "Opus 5.5 max", "max", v2("Claude Code", "Opus 5.5", "max"),
           note="RemakeBench Max receipt (96% Opus 5.5) implies ≈$2,155/week, above the plan median used here"))
for e in ("xhigh", "high", "medium", "low"):
    c = opus_curve(e)
    add(row("claude", "Opus 5.5", f"Opus 5.5 {e}", e, c["api"], c["mins"], c["idx"], basis=MODELLED, agent=c["agent"], deriv=c["deriv"],
            note="Anthropic's published effort curve, anchored to AA's max row"))
add(direct("claude", "Sonnet 5.5", "Sonnet 5.5 max", "max", v2("Claude Code", "Sonnet 5.5", "max"), note="Creator report: 2% of weekly limit for $30.46, ≈$1,523/week (n=1)"))
for e in ("xhigh", "high", "medium", "low"):
    c = scaled("Claude Code", "Sonnet 5.5", e)
    add(row("claude", "Sonnet 5.5", f"Sonnet 5.5 {e}", e, c["api"], c["mins"], c["idx"], basis=SCALED, agent=c["agent"], deriv=c["deriv"], note="Rescaled from AA's 5 Oct snapshot via the max row"))
add(direct("claude", "Fable 5.1", "Fable 5.1 max", "max", v2("Claude Code", "Fable 5.1 (with fallback)", "max"), note="No Fable-specific capacity measurement"))
add(direct("claude", "Haiku 5.5", "Haiku 5.5 max", "max", v2("Claude Code", "Haiku 5.5", "max"), note="Haiku is not in the measured traffic mix"))
# ChatGPT
add(direct("chatgpt", "GPT-6.1 Sol", "GPT-6.1 Sol max", "max", v2("Codex", "GPT-6.1 Sol", "max"), note="wokey: most measured Codex value comes from Sol-class models"))
for e in ("xhigh", "high", "medium", "low"):
    c = scaled("Codex", "GPT-6.1 Sol", e)
    add(row("chatgpt", "GPT-6.1 Sol", f"GPT-6.1 Sol {e}", e, c["api"], c["mins"], c["idx"], basis=SCALED, agent=c["agent"], deriv=c["deriv"], note="Rescaled from AA's 5 Oct snapshot via the max row"))
add(direct("chatgpt", "GPT-6 Astra", "GPT-6 Astra max", "max", v2("Codex", "GPT-6 Astra", "max"), note="Model-matched capacity measurement on Pro $500"))
for e in ("xhigh", "max", "high", "medium", "low"):
    add(direct("chatgpt", "GPT-6.1 Terra", f"Terra {e}", e, v2("Codex", "GPT-6.1 Terra", e), note="Terra is not in any measured mix"))
add(direct("chatgpt", "GPT-6 Luna", "Luna max", "max", v2("Codex", "GPT-6 Luna", "max"), note="Luna is not in any measured mix"))
# Gemini, Grok
add(direct("gemini", "Gemini 4 Argon", "Gemini 4 Argon", "default", v2("Antigravity CLI", "Gemini 4 Argon", "default"), note="Capacity is a scaled scenario, not a measurement"))
add(direct("gemini", "Gemini 3.8 Flash", "Gemini 3.8 Flash high", "high", v2("Antigravity SDK", "Gemini 3.8 Flash", "high"), basis=PROXY, note="AA measured the SDK, not the CLI"))
add(direct("grok", "Grok 4.7", "Grok 4.7 xhigh", "xhigh", v2("Grok Build", "Grok 4.7", "xhigh"), note="Single receipt (n=1), model-matched"))
# Muse Code models on their own plan (capacity assumed, so inferred)
for fam in ("Muse Spark 1.3", "Muse Wonder"):
    add(direct("muse", fam, f"{fam} max", "max", v2("Muse Code", fam, "max"), note="AA measured Muse Code with its own API price"))
# Muse Wonder Full has no API price (AA lists $0.00): price its tokens at Fable 5.1's cost per token in the same benchmark
_rec = {r["model"]: r for r in V2 if r["agent"] in ("Muse Code", "Claude Code")}
_fable = _rec["Fable 5.1 (with fallback)"]
_fable_rate = _fable["economics"]["costUsd"] / _fable["usage"]["totalTokens"]
_mwf = _rec["Muse Wonder Full"]
_b = _mwf["benchmarks"]
add(row("muse", "Muse Wonder Full", "Muse Wonder Full max", "max", _mwf["usage"]["totalTokens"] * _fable_rate, _mwf["economics"]["durationSeconds"] / 60, _b["aaIndex"],
        basis=MODELLED, agent="Muse Code", comps=(_b["deepSwe"], _b["terminalBench"], _b["sweAtlas"]),
        deriv=dict(api=f"no API price (AA lists $0.00): {_mwf['usage']['totalTokens'] / 1e6:.1f}M tokens/task × Fable 5.1's ${_fable_rate * 1e6:.5g} per million tokens in this benchmark "
                       f"({money(_fable['economics']['costUsd'])} ÷ {_fable['usage']['totalTokens'] / 1e6:.2f}M tokens)"),
        note="Price assumed from Fable 5.1; Muse Code capacity is assumed, not measured"))
# OpenCode Go (published per-model allowances; AA benchmarked these in other harnesses)
_ds = v2("DeepSeek Harness", "DeepSeek V4.1 Flash 1017", "default")
add(direct("opencode", "DeepSeek V4.1 Flash", "DeepSeek V4.1 Flash max", "max", _ds, basis=PROXY, go_allowance=GO_ALLOWANCE["DeepSeek V4.1 Flash"],
           note="AA ran DeepSeek's own harness at its default setting, treated here as max (AA's DeepSeek page shows the Max reasoning variant); served through OpenCode Go"))
for e in ("high", "medium", "low"):
    c, i, t = DS_EFFORT[e]
    mc, mi, mt = DS_EFFORT["max"]
    how = "measured" if e == "high" else "estimated evenly between no-reasoning 45.0 and the measured high score 51.4"
    add(row("opencode", "DeepSeek V4.1 Flash", f"DeepSeek V4.1 Flash {e}", e, _ds["api"] * c / mc, _ds["mins"] * t / mt, _ds["idx"] * i / mi,
            basis=MODELLED, agent="DeepSeek Harness", go_allowance=GO_ALLOWANCE["DeepSeek V4.1 Flash"],
            deriv=dict(score=f"coding max score {_ds['idx']:.2f} × ({i:.2f} ÷ 59.1): Intelligence Index score at {e} ({how}), relative to max",
                       api=f"coding max API cost {exact(_ds['api'])} × ({exact(c)} ÷ $0.602): Intelligence Index cost interpolated geometrically from no-reasoning $0.425 to max $0.602",
                       mins=f"coding max time {_ds['mins']:.2f} min × ({t:.1f}k ÷ 139k): tokens interpolated geometrically from no-reasoning 65k to max 139k"),
            note=f"No public source measures DeepSeek V4.1 Flash at {e} on cost; modelled between its measured no-reasoning and max results"))
add(direct("opencode", "Kimi K3", "Kimi K3", "default", v2("Kimi Code CLI", "Kimi K3", "default"), basis=PROXY, go_allowance=GO_ALLOWANCE["Kimi K3"],
           note="AA measured Kimi Code CLI, not OpenCode"))
# Other effort levels from AA's Intelligence Index curves, anchored to each model's coding row
for plan, fam, (a, m, s), efforts, short in (
        ("claude", "Fable 5.1", ("Claude Code", "Fable 5.1 (with fallback)", "max"), ("low", "medium", "high", "xhigh"), "Fable 5.1"),
        ("claude", "Haiku 5.5", ("Claude Code", "Haiku 5.5", "max"), ("low", "medium", "high", "xhigh"), "Haiku 5.5"),
        ("chatgpt", "GPT-6 Astra", ("Codex", "GPT-6 Astra", "max"), ("low", "medium", "high", "xhigh"), "GPT-6 Astra"),
        ("chatgpt", "GPT-6 Luna", ("Codex", "GPT-6 Luna", "max"), ("low", "medium", "high", "xhigh"), "Luna"),
        ("grok", "Grok 4.7", ("Grok Build", "Grok 4.7", "xhigh"), ("low", "high"), "Grok 4.7")):
    base = v2(a, m, s)
    bc, bi, bt = INTEL[fam][s]
    for e in efforts:
        c, i, t = INTEL[fam][e]
        add(row(plan, fam, f"{short} {e}", e, base["api"] * c / bc, base["mins"] * t / bt, base["idx"] * i / bi, basis=MODELLED, agent=a,
                deriv=dict(score=f"coding {s} score {base['idx']:.2f} × ({i} ÷ {bi}): Intelligence Index score at {e} vs {s}",
                           api=f"coding {s} API cost {exact(base['api'])} × ({exact(c)} ÷ {exact(bc)}): Intelligence Index cost at {e} vs {s}",
                           mins=f"coding {s} time {base['mins']:.2f} min × ({t}k ÷ {bt}k): Intelligence Index output tokens at {e} vs {s}"),
                note=f"AA has no coding-agent row at {e}; modelled from AA's Intelligence Index effort curve"))


# ---------------- models with no published effort curve ----------------
# A reference effort curve: for each effort, the median ratio (cost, score, output tokens) to a model's high or max
# setting, across every model AA's Intelligence Index ran at all five efforts (BenchLeader, 4 Nov 2026).
REF_CURVES = dict(INTEL, **{
    "Opus 5.5": {"low": (0.976, 59.4, 19), "medium": (2.45, 61.9, 44), "high": (3.46, 65.7, 60), "xhigh": (6.05, 66.2, 103), "max": (10.04, 69.3, 173)},
    "Sonnet 5.5": {"low": (0.511, 51.1, 21), "medium": (0.781, 51.0, 31), "high": (1.64, 58.5, 58), "xhigh": (4.09, 63.4, 122), "max": (10.02, 65.3, 285)},
    "GPT-6.1 Sol": {"low": (0.161, 60.7, 6), "medium": (0.359, 63.5, 14), "high": (0.591, 64.2, 23), "xhigh": (0.764, 64.5, 30), "max": (1.27, 67.2, 68)},
    "GPT-6.1 Terra": {"low": (0.071, 57.0, 4), "medium": (0.169, 59.0, 11), "high": (0.259, 60.2, 17), "xhigh": (0.401, 60.6, 26), "max": (0.961, 65.2, 60)},
})
FULL = [c for c in REF_CURVES.values() if all(e in c for e in ("low", "medium", "high", "xhigh", "max"))]


def ref_ratio(effort, anchor):
    """Median (cost, score, tokens) ratio of `effort` to `anchor` across models with a full effort curve."""
    return tuple(statistics.median(c[effort][k] / c[anchor][k] for c in FULL) for k in range(3))


REF_NOTE = f"the median effort curve of the {len(FULL)} models AA ran at every effort (Opus, Sonnet, Fable, Haiku, Sol, Terra, Astra, Luna)"

# Gemini 3.8 Flash: BenchLeader scores low 56.1, medium 60.6, high 61.9 but publishes cost, tokens and time only at high,
# so scores use the measured ratios and cost/time use the reference curve, anchored to AA's high coding row.
_gf = v2("Antigravity SDK", "Gemini 3.8 Flash", "high")
GF_SCORE = {"low": 56.1, "medium": 60.6, "high": 61.9}
for e in ("low", "medium"):
    rc, _, rt = ref_ratio(e, "high")
    add(row("gemini", "Gemini 3.8 Flash", f"Gemini 3.8 Flash {e}", e, _gf["api"] * rc, _gf["mins"] * rt, _gf["idx"] * GF_SCORE[e] / GF_SCORE["high"],
            basis=MODELLED, agent="Antigravity SDK",
            deriv=dict(score=f"coding high score {_gf['idx']:.2f} × ({GF_SCORE[e]} ÷ {GF_SCORE['high']}): BenchLeader's measured Gemini 3.8 Flash scores at {e} vs high",
                       api=f"coding high API cost {exact(_gf['api'])} × {rc:.5g}: {e}-to-high cost ratio from {REF_NOTE}",
                       mins=f"coding high time {_gf['mins']:.2f} min × {rt:.5g}: {e}-to-high output-token ratio from {REF_NOTE}"),
            note=f"No cost or time is published for Gemini 3.8 Flash at {e}; modelled from the reference effort curve"))

# Muse Wonder Full: only max is benchmarked anywhere, so every lower effort uses the reference curve relative to max.
_mwf_row = next(r for r in rows if r["family"] == "Muse Wonder Full")
for e in ("xhigh", "high", "medium", "low"):
    rc, rs, rt = ref_ratio(e, "max")
    add(row("muse", "Muse Wonder Full", f"Muse Wonder Full {e}", e, _mwf_row["api"] * rc, _mwf_row["mins"] * rt, _mwf_row["idx"] * rs,
            basis=MODELLED, agent="Muse Code",
            deriv=dict(score=f"max score {_mwf_row['idx']:.2f} × {rs:.5g}: {e}-to-max score ratio from {REF_NOTE}",
                       api=f"max cost {exact(_mwf_row['api'])} (Fable-priced) × {rc:.5g}: {e}-to-max cost ratio from {REF_NOTE}",
                       mins=f"max time {_mwf_row['mins']:.2f} min × {rt:.5g}: {e}-to-max output-token ratio from {REF_NOTE}"),
            note=f"Muse Wonder Full is only benchmarked at max; {e} is modelled from the reference effort curve"))

# Kimi K3.1 Pro: no AA coding-agent row. Scale Kimi K3's coding row by the two models' Intelligence Index results
# (BenchLeader, 4 Nov 2026): K3 low $2.37, score 53.7, 13 min; K3.1 Pro $3.68, score 61.6, 35 min.
_k3 = v2("Kimi Code CLI", "Kimi K3", "default")
K3, K31 = (2.37, 53.7, 13), (3.68, 61.6, 35)
add(row("opencode", "Kimi K3.1 Pro", "Kimi K3.1 Pro", "not stated", _k3["api"] * K31[0] / K3[0], _k3["mins"] * K31[2] / K3[2], _k3["idx"] * K31[1] / K3[1],
        basis=MODELLED, agent="Kimi Code CLI", go_allowance=15,
        deriv=dict(score=f"Kimi K3 coding score {_k3['idx']:.2f} × ({K31[1]} ÷ {K3[1]}): K3.1 Pro vs K3 on the Intelligence Index",
                   api=f"Kimi K3 coding API cost {exact(_k3['api'])} × ({exact(K31[0])} ÷ {exact(K3[0])}): K3.1 Pro vs K3 Intelligence Index cost",
                   mins=f"Kimi K3 coding time {_k3['mins']:.2f} min × ({K31[2]} ÷ {K3[2]}): K3.1 Pro vs K3 Intelligence Index minutes per task"),
        note="AA hasn't published a coding-agent row for Kimi K3.1 Pro; modelled from Kimi K3's coding row and the two models' Intelligence Index results"))
FAMILY_MAKER["Kimi K3.1 Pro"] = "Kimi"


# ---------------- build ----------------
def grade(r):
    if r["basis"] == MODELLED:
        return "modelled"
    if r["basis"] in (SCALED, PROXY) or r["plan"] == "opencode":
        return "inferred"
    return "measured" if r["family"] in PLANS[r["plan"]]["models"] else "inferred"


def working(r, p, cap, cap_note, tasks, per_task):
    """Step-by-step working for one point, shown on the page. Results are rounded for display, so '≈' marks them."""
    d = r["deriv"] or {}
    if "score" in d:
        score = f"{r['idx']:.1f} ≈ {d['score']}"
    elif r["comps"] and all(x is not None for x in r["comps"]):
        fc, tb, sw = r["comps"]
        score = f"{r['idx']:.1f} ≈ ({fc:.2f} FrontierCode + {tb:.2f} Terminal-Bench + {sw:.2f} SWE-Atlas QnA) ÷ 3 (AA, {r['agent']})"
    else:
        score = f"{r['idx']:.1f} (AA Coding Agent Index)"
    api = f"{exact(r['api'])} ≈ {d['api']}" if "api" in d else f"{exact(r['api'])}: AA's measured API cost for one attempt ({r['agent']})"
    mins = f"{r['mins']:.1f} min ≈ {d['mins']}" if "mins" in d else f"{r['mins']:.1f} min: AA's measured wall time for one attempt"
    return [
        ["Score", score],
        ["API cost per task", api],
        ["Time per task", mins],
        ["Plan capacity", f"${cap:,.2f}/month of API-equivalent use: {cap_note}"],
        ["Tasks per month", f"{tasks:,.0f} ≈ ${cap:,.2f} ÷ {exact(r['api'])}"],
        ["Subscription cost per task", f"{exact(per_task)} ≈ plan price ${p['price']:,} ÷ {tasks:,.3f} tasks" if tasks < 10 else f"{exact(per_task)} ≈ plan price ${p['price']:,} ÷ {tasks:,.2f} tasks" if tasks < 100 else f"{exact(per_task)} ≈ plan price ${p['price']:,} ÷ {tasks:,.1f} tasks"],
    ]


points = []
for r in rows:
    p = PLANS[r["plan"]]
    if r["go_allowance"]:
        cap, cap_note = r["go_allowance"], f"OpenCode Go's published ${r['go_allowance']}/month allowance for this model"
    elif r["family"] in p["models"]:
        cap, cap_note = p["models"][r["family"]]
    else:
        cap, cap_note = p["plan_cap"], p["cap_src"]
    tasks = cap / r["api"]
    per_task = p["price"] / tasks
    points.append(dict(provider=p["provider"], maker=FAMILY_MAKER.get(r["family"], MAKER.get(r["plan"])), via_go=r["plan"] == "opencode",
                       plan=p["plan"], price=p["price"], label=r["label"], family=r["family"], effort=r["effort"], basis=r["basis"],
                       idx=round(r["idx"], 1), api=round(r["api"], 4), mins=round(r["mins"], 2), monthly_cap=round(cap),
                       tasks=round(tasks), per_task=round(per_task, 5), grade=grade(r),
                       comps=[round(x, 1) for x in r["comps"]] if r["comps"] and all(x is not None for x in r["comps"]) else None,
                       note=f"{r['note']}.", working=working(r, p, cap, cap_note, tasks, per_task)))

bench = dict(name="Agentic coding", long="Artificial Analysis Coding Agent Index v2.0 (27 Oct 2026)", task="AA coding-agent task",
             score="AA Coding Agent Index", url="https://artificialanalysis.ai/agents/coding-agents",
             about="One task is one attempt at one of 290 agentic coding tasks (FrontierCode v1.1, Terminal-Bench 4.0, SWE-Atlas-QnA-AA) in the model's own harness. "
                   "Only Claude and Sol max rows are current-index data; lower Sonnet and Sol efforts are rescaled from AA's 5 Oct snapshot, lower Opus efforts are "
                   "modelled from Anthropic's published effort curve, DeepSeek V4.1 Flash's lower efforts are modelled between its measured no-reasoning and max results, "
                   "other efforts for Fable, Haiku, Astra, Luna and Grok are modelled from AA's own Intelligence Index effort curves, Gemini 3.8 Flash and Muse Wonder Full use a reference effort curve, and Kimi K3.1 Pro is scaled from Kimi K3.",
             top=max(p["idx"] for p in points), median=statistics.median(p["idx"] for p in points), modes={"public": points})
plans = {k: dict(provider=v["provider"], plan=v["plan"], price=v["price"], public=v["plan_cap"],
                 sources=[note for _, note in v["models"].values()] + [v["cap_src"]], cap_url=v["cap_url"], alt=v["alt"])
         for k, v in PLANS.items()}
os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
json.dump(dict(benchmarks={"coding": bench}, plans=plans), open(OUT, "w"), indent=1)
print(f"wrote {OUT}: {len(points)} points")
