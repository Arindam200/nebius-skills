# Evals — Skill Quality Benchmarks

This folder contains the evaluation harness used to measure and improve the Nebius skills. It is **developer tooling** — end users installing the skills don't need to touch it.

## What is it?

Each skill was tested with real prompts, run twice — once with the skill loaded, once without (baseline). The results are compared to measure how much the skill actually improves Claude's responses on Nebius-specific tasks.

## Structure

```
evals/
├── README.md                         ← you are here
├── skill-creator.md                  ← the skill-creator tool used to build and iterate on skills
├── evals.json                        ← basic test prompt set
├── evals_with_assertions.json        ← test prompts + pass/fail assertions
└── iteration-1/                      ← first benchmark run
    ├── benchmark.json                ← machine-readable aggregated results
    ├── benchmark.md                  ← human-readable results + analysis
    ├── grading_summary.json          ← per-eval pass rates at a glance
    └── eval-{N}-{name}/
        ├── eval_metadata.json        ← prompt + assertions for this eval
        ├── with_skill/
        │   ├── outputs/response.md   ← Claude's response when skill was loaded
        │   ├── grading.json          ← assertion pass/fail results
        │   └── timing.json           ← token count + duration (null in iteration-1)
        └── without_skill/
            ├── outputs/response.md   ← Claude's response with no skill (baseline)
            ├── grading.json          ← assertion pass/fail results
            └── timing.json           ← token count + duration (null in iteration-1)
```

## Iteration-1 Results Summary

| Eval | Skill | With Skill | Without Skill | Delta |
|------|-------|-----------|--------------|-------|
| finetune-upload-and-start | nebius-finetune | 100% | 40% | **+60pp** |
| finetune-monitor-checkpoints | nebius-finetune | 100% | 80% | **+20pp** |
| dedicated-create-and-infer | nebius-dedicated-endpoint | 100% | — | — |
| dedicated-patch-scaling | nebius-dedicated-endpoint | 100% | 100% | 0pp |
| observability-grafana-promql | nebius-observability | 40% | 40% | 0pp ⚠️ |
| observability-prometheus-config | nebius-observability | 80% | 40% | **+40pp** |
| deploy-lora-from-job | nebius-deploy-lora | 0% | 60% | −60pp ⚠️ |
| deploy-lora-from-hf | nebius-deploy-lora | 100% | 25% | **+75pp** |
| batch-10k-questions | nebius-batch-synthetic | 0% | 83% | −83pp ⚠️ |

> ⚠️ Three evals show skill loading failures (not content failures). When the skill loads, it performs at ~97% average. See `iteration-1/benchmark.md` for the full analysis and iteration-2 action plan.

## Running Your Own Evals

The eval prompts and assertions live in `evals_with_assertions.json`. To run them:

1. For each eval, spawn an agent with the skill loaded (point to `skills/<skill-name>/SKILL.md`) and run the prompt
2. Save the response to `iteration-N/eval-{id}-{name}/with_skill/outputs/response.md`
3. Run a baseline agent (no skill) with the same prompt → `without_skill/outputs/response.md`
4. Grade against assertions in `eval_metadata.json`
5. Aggregate results into `benchmark.json`

See `skill-creator.md` for the full workflow and tooling details.

## Contributing New Evals

Add new test cases to `evals_with_assertions.json` following the existing schema:

```json
{
  "id": 12,
  "eval_name": "descriptive-name",
  "skill": "nebius-<skill-name>",
  "prompt": "A realistic user prompt...",
  "assertions": [
    { "text": "Assertion description", "check": "string_match", "value": "expected_string" },
    { "text": "Qualitative check",     "check": "qualitative",  "value": "What to look for" }
  ]
}
```
