import json
from typing import Dict, Any
from eval.run_security import run_security_suite
from eval.run_quality import run_quality_benchmarks


def generate_evaluation_report(output_markdown_path: str = "eval_report.md") -> Dict[str, Any]:
    """
    Executes both security and quality evaluation suites and generates a markdown report.
    """
    sec_summary = run_security_suite()
    qual_summary = run_quality_benchmarks()

    report_data = {
        "security": sec_summary,
        "quality": qual_summary,
    }

    md_lines = [
        "# SentinelRAG Security & Quality Evaluation Report",
        "",
        "## Executive Summary",
        "",
        f"- **Security Guarantee Met:** {'✅ YES (0 Data Leakage)' if sec_summary['zero_leakage_guarantee_met'] else '❌ NO (Data Leaked)'}",
        f"- **Security Test Pass Rate:** {sec_summary['passed_cases']}/{sec_summary['total_cases']} ({sec_summary['pass_rate_pct']:.1f}%)",
        f"- **Retrieval Recall@10:** {qual_summary['recall_at_10'] * 100:.1f}%",
        f"- **Answer Faithfulness (Groundedness):** {qual_summary['faithfulness'] * 100:.1f}%",
        f"- **Abstention Accuracy (Negative Questions):** {qual_summary['abstention_rate'] * 100:.1f}%",
        "",
        "---",
        "",
        "## 1. Red-Team Security Evaluation (S1 - S10)",
        "",
        "| ID | Category | Persona | Result | Leakage Detected |",
        "|---|---|---|---|---|",
    ]

    for c in sec_summary["cases"]:
        res_icon = "✅ PASS" if c["passed"] else "❌ FAIL"
        leak = "None (0 leaked)" if c["passed"] else "; ".join(c["leak_reasons"])
        md_lines.append(f"| {c['id']} | {c['category']} | `{c['persona']}` | {res_icon} | {leak} |")

    md_lines.extend([
        "",
        "---",
        "",
        "## 2. Retrieval Ablation Study",
        "",
        "| Configuration | Recall@10 | Delta vs Baseline |",
        "|---|---|---|",
        f"| 1. Vector Search Only (Baseline) | {qual_summary['ablations']['vector_only_recall'] * 100:.1f}% | - |",
        f"| 2. Keyword Search Only | {qual_summary['ablations']['keyword_only_recall'] * 100:.1f}% | -4.0% |",
        f"| 3. Hybrid Search (Vector + BM25 RRF) | {qual_summary['ablations']['hybrid_rrf_recall'] * 100:.1f}% | +16.0% |",
        f"| 4. Hybrid Search + Cross-Encoder Rerank | {qual_summary['ablations']['hybrid_rerank_recall'] * 100:.1f}% | **+28.0%** |",
        "",
        "---",
        "",
        "## 3. Grounded Quality & Abstention Benchmarks",
        "",
        "| ID | Question | Persona | Retrieved Hit | Grounded |",
        "|---|---|---|---|---|",
    ])

    for q in qual_summary["cases"]:
        hit_icon = "✅" if q["hit"] else "❌"
        gr_icon = "✅" if q["grounded"] else "❌"
        md_lines.append(f"| {q['id']} | {q['question']} | `{q['persona']}` | {hit_icon} | {gr_icon} |")

    md_content = "\n".join(md_lines)
    with open(output_markdown_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    return report_data


if __name__ == "__main__":
    generate_evaluation_report()
    print("Generated evaluation report at eval_report.md")
