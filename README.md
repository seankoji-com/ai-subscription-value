# AI subscription value

An interactive report on which AI coding subscription gives the most agentic-coding work per dollar, at each model and effort level.

**Report:** https://seankoji-com.github.io/ai-subscription-value/

## What it shows

Each point is one model at one effort level, priced on its provider's top subscription plan:

- Claude Ultra ($200)
- ChatGPT Pro ($500)
- Google AI Ultra 20× ($199.99)
- SuperGrok Heavy ($300)
- Muse Code Maximum ($200)
- OpenCode Go ($10), for DeepSeek and Kimi, which have no plan of their own here

The chart plots subscription cost per task against benchmark score or minutes per task. Sliders set a minimum score, a maximum cost and a maximum time, and the frontier marks the options nothing else beats. Click a provider to filter, or a point to highlight that model at every effort level.

## Method

For each model at each effort level:

```
tasks per month = plan capacity (API-equivalent $/month) ÷ API cost per task
cost per task   = plan price ÷ tasks per month
```

- **Benchmark:** [Artificial Analysis Coding Agent Index v2.0](https://artificialanalysis.ai/agents/coding-agents) (27 Oct 2026). It gives the API cost, wall time and score for one attempt at a coding-agent task in each model's own harness.
- **Effort levels:** AA's current index tests most models at a single effort level. The other levels are filled in as follows, and none of these points is recommended:
  - Sonnet 5.5 and GPT-6.1 Sol: rescaled from AA's 5 Oct snapshot through each model's max row.
  - Opus 5.5: modelled from Anthropic's published effort curve.
  - Fable, Haiku, Astra, Luna and Grok: modelled from AA's Intelligence Index effort curves.
  - DeepSeek V4.1 Flash low, medium and high: modelled between its measured no-reasoning and max results.
  - Gemini 3.8 Flash low and medium, and Muse Wonder Full below max: modelled from the median effort curve of the models AA ran at every effort.
  - Kimi K3.1 Pro: no coding-agent row exists, so it is scaled from Kimi K3's row using both models' Intelligence Index results.

The page's "How the numbers are calculated" section explains each step. Tapping any point shows its full working: score components, API cost, capacity source, tasks per month and cost per task.
- **Capacity:** vendors don't publish plan quotas in tokens or dollars. Each figure comes from a third-party measurement, a published allowance or a stated assumption, and the page lists the source for every one. Points are graded:
  - **Measured:** a capacity measurement that includes this model's traffic.
  - **Inferred:** capacity measured for other models on the plan, a scaled scenario, or a benchmark run in a different harness.
  - **Modelled:** no published benchmark at that effort level.

Every figure is an estimate. A task here is one benchmark task, not a unit of your own work.

## Build

Requires Python 3 and no extra packages.

```sh
python3 src/generate.py data site/data.json
python3 src/build.py site/data.json data/logos.json site/index.html
```

Open `site/index.html`. Pushing to `main` rebuilds the page and deploys it to GitHub Pages through `.github/workflows/pages.yml`.

## Data sources

| File | Source |
|---|---|
| `data/aa-coding-agents-2026-10-27.json` | Artificial Analysis Coding Agent Index, as collected by [hraness/aicharts](https://github.com/hraness/aicharts) (MIT) at commit `e8e50a2316` |
| `data/aa-coding-agents-2026-10-05.json` | The same dataset at commit `0529938df7`, the previous index version |
| `data/logos.json` | Provider logos from [@lobehub/icons-static-svg](https://www.npmjs.com/package/@lobehub/icons-static-svg) 1.102.0 (MIT) |

Effort curves embedded in `src/generate.py` come from [BenchLeader](https://www.benchleader.com/effort) (CC BY 4.0) and Anthropic's [effort guidance](https://platform.claude.com/docs/en/about-claude/models/optimizing-for-cost-and-intelligence). Capacity figures are cited on the page: [wokey.ai](https://wokey.ai/claude-usage-limits), SemiAnalysis, [aiandtractors](https://aiandtractors.com/coding-agent-subscription-costs/), [OpenCode Go](https://opencode.ai/go) and [ratelimitnow](https://ratelimitnow.com/limits/muse-code/).

Benchmark results belong to their publishers. This project is not affiliated with any provider, and logos and trademarks belong to their owners.
