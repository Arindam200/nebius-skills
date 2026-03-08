# Nebius DataLab — Overview Reference

> **When to read:** When the user asks about DataLab data types, SQL filtering, or the relationship between inference logs and fine-tuning.

Source: [Data Lab Overview](https://docs.tokenfactory.nebius.com/data-lab/overview)

---

## What DataLab stores

| Data type | Source |
|-----------|--------|
| **Inference Logs** | Chat completions via API or Playground (unless Zero Data Retention) |
| **Filtered Datasets** | SQL queries over inference logs |
| **Uploaded Datasets** | Manual upload |
| **Batch Inference Outputs** | Results from batch jobs |
| **Fine-tuning Outputs** | Checkpoints and fine-tuned model artifacts |

---

## DataLab capabilities

- **Reusable datasets** for batch inference and fine-tuning
- **Unified interface** for preparing datasets via SQL queries
- **Single place** to view, filter, and export inference logs

---

## Pipeline stages (typical)

1. **Import / generate** inference logs (chat completions)
2. **Upload** or **filter** raw datasets (SQL over logs)
3. **Batch inference** — teacher model generates responses
4. **Curate** — quality filter, format for fine-tuning
5. **Fine-tune** — train student model on curated data
6. **Deploy** — serve LoRA adapter
7. **Smoke test** — validate deployed model

---

## Reproducibility

By keeping datasets versioned and centralized, DataLab enables:
- Consistent training inputs across experiments
- Easier comparison of fine-tuning results
- Safer iteration without accidental data changes
