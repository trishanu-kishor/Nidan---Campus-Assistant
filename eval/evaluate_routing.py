"""
Campus Assistant - Routing Evaluation & Benchmark Harness
File: eval/evaluate_routing.py

Evaluates the CampusIntentClassifier against the benchmark dataset (eval/test_dataset.json).
Calculates Top-1 Accuracy, Multi-Label Precision/Recall/F1, Per-domain metrics,
Confusion Matrix, Latency benchmarks, and Error Analysis.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Set, Optional

# Ensure utf-8 output encoding on Windows consoles
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Add parent directory to path to import router
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from router.classifier import CampusIntentClassifier, DOMAINS, DOMAIN_NAMES


def load_benchmark_dataset(dataset_path: Path) -> List[Dict[str, Any]]:
    """Loads benchmark queries from JSON file."""
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found at {dataset_path}")
    with open(dataset_path, "r", encoding="utf-8") as f:
        return json.load(f)


def calculate_metrics(y_true_list: List[Set[str]], y_pred_list: List[Set[str]], all_classes: List[str]):
    """Calculates multi-label precision, recall, and F1-score."""
    per_class_tp = {c: 0 for c in all_classes}
    per_class_fp = {c: 0 for c in all_classes}
    per_class_fn = {c: 0 for c in all_classes}

    for y_true, y_pred in zip(y_true_list, y_pred_list):
        for c in all_classes:
            in_true = c in y_true
            in_pred = c in y_pred
            if in_true and in_pred:
                per_class_tp[c] += 1
            elif not in_true and in_pred:
                per_class_fp[c] += 1
            elif in_true and not in_pred:
                per_class_fn[c] += 1

    per_class_stats = {}
    for c in all_classes:
        tp = per_class_tp[c]
        fp = per_class_fp[c]
        fn = per_class_fn[c]
        precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        per_class_stats[c] = {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
        }

    # Micro average
    total_tp = sum(per_class_tp.values())
    total_fp = sum(per_class_fp.values())
    total_fn = sum(per_class_fn.values())
    micro_p = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 1.0
    micro_r = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 1.0
    micro_f1 = (2 * micro_p * micro_r) / (micro_p + micro_r) if (micro_p + micro_r) > 0 else 0.0

    # Macro average
    macro_p = sum(s["precision"] for s in per_class_stats.values()) / len(all_classes)
    macro_r = sum(s["recall"] for s in per_class_stats.values()) / len(all_classes)
    macro_f1 = sum(s["f1"] for s in per_class_stats.values()) / len(all_classes)

    return {
        "per_class": per_class_stats,
        "micro": {"precision": round(micro_p, 4), "recall": round(micro_r, 4), "f1": round(micro_f1, 4)},
        "macro": {"precision": round(macro_p, 4), "recall": round(macro_r, 4), "f1": round(macro_f1, 4)},
    }


def run_evaluation(dataset_path: Optional[Path] = None, output_json: bool = True) -> Dict[str, Any]:
    """Runs full benchmark evaluation and prints formatted results."""
    if dataset_path is None:
        dataset_path = project_root / "eval" / "test_dataset.json"

    dataset = load_benchmark_dataset(dataset_path)
    classifier = CampusIntentClassifier()

    eval_classes = DOMAINS + ["out_of_domain"]
    total_queries = len(dataset)

    correct_top1 = 0
    exact_multi_matches = 0
    subset_multi_matches = 0

    y_true_sets: List[Set[str]] = []
    y_pred_sets: List[Set[str]] = []

    category_stats: Dict[str, Dict[str, int]] = {}
    difficulty_stats: Dict[str, Dict[str, int]] = {}
    latencies: List[float] = []
    errors_and_warnings: List[Dict[str, Any]] = []

    # Confusion Matrix mapping for primary domains
    confusion_matrix = {t: {p: 0 for p in eval_classes} for t in eval_classes}

    print("=" * 80)
    print("🚀 NIDAN - INTENT ROUTING BENCHMARK EVALUATION")
    print(f"📁 Dataset: {dataset_path.name} | Total Queries: {total_queries}")
    print("=" * 80)

    for item in dataset:
        qid = item["id"]
        query = item["query"]
        expected_primary = item.get("primary_domain", "out_of_domain")
        expected_domains = set(item.get("expected_domains", []))
        if not expected_domains:
            expected_domains = {"out_of_domain"}

        category = item.get("category", "Unspecified")
        difficulty = item.get("difficulty", "Standard")

        category_stats.setdefault(category, {"total": 0, "correct": 0})
        difficulty_stats.setdefault(difficulty, {"total": 0, "correct": 0})

        category_stats[category]["total"] += 1
        difficulty_stats[difficulty]["total"] += 1

        # Classify
        result = classifier.classify(query)
        latencies.append(result.processing_time_ms)

        pred_primary = result.primary_domain
        pred_domains = set(result.detected_domains)
        if not pred_domains:
            pred_domains = {"out_of_domain"}

        y_true_sets.append(expected_domains)
        y_pred_sets.append(pred_domains)

        # Update confusion matrix
        if expected_primary in confusion_matrix and pred_primary in confusion_matrix[expected_primary]:
            confusion_matrix[expected_primary][pred_primary] += 1

        # Check Top-1 primary match
        top1_match = (pred_primary == expected_primary)
        if top1_match:
            correct_top1 += 1
            category_stats[category]["correct"] += 1
            difficulty_stats[difficulty]["correct"] += 1

        # Multi-label match criteria
        is_exact_match = (pred_domains == expected_domains)
        is_subset_match = expected_domains.issubset(pred_domains) or pred_domains.issubset(expected_domains)

        if is_exact_match:
            exact_multi_matches += 1
        if is_subset_match:
            subset_multi_matches += 1

        # Log errors/mismatches
        if not top1_match or not is_exact_match:
            errors_and_warnings.append({
                "id": qid,
                "query": query,
                "expected_primary": expected_primary,
                "pred_primary": pred_primary,
                "expected_domains": list(expected_domains),
                "pred_domains": list(pred_domains),
                "confidence": result.confidence,
                "top1_match": top1_match,
                "exact_match": is_exact_match,
                "notes": item.get("notes", ""),
            })

    # Calculations
    top1_acc = correct_top1 / total_queries if total_queries > 0 else 0
    exact_multi_acc = exact_multi_matches / total_queries if total_queries > 0 else 0
    subset_multi_acc = subset_multi_matches / total_queries if total_queries > 0 else 0
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

    metrics = calculate_metrics(y_true_sets, y_pred_sets, eval_classes)

    # CLI Output Display
    print("\n📊 OVERALL PERFORMANCE SUMMARY:")
    print(f"  • Top-1 Primary Intent Accuracy:  {top1_acc * 100:6.2f}% ({correct_top1}/{total_queries})")
    print(f"  • Exact Multi-Label Match Rate:    {exact_multi_acc * 100:6.2f}% ({exact_multi_matches}/{total_queries})")
    print(f"  • Subset / Relaxed Match Rate:     {subset_multi_acc * 100:6.2f}% ({subset_multi_matches}/{total_queries})")
    print(f"  • Micro-Averaged F1-Score:        {metrics['micro']['f1']:6.4f}")
    print(f"  • Macro-Averaged F1-Score:        {metrics['macro']['f1']:6.4f}")
    print(f"  • Average Routing Latency:        {avg_latency:6.2f} ms")

    print("\n🏷️  CATEGORY-WISE ACCURACY BREAKDOWN:")
    for cat, stats in category_stats.items():
        acc = (stats["correct"] / stats["total"]) * 100 if stats["total"] > 0 else 0
        print(f"  • {cat:<20}: {acc:6.2f}% ({stats['correct']}/{stats['total']})")

    print("\n🎯 DIFFICULTY-WISE ACCURACY BREAKDOWN:")
    for diff, stats in difficulty_stats.items():
        acc = (stats["correct"] / stats["total"]) * 100 if stats["total"] > 0 else 0
        print(f"  • {diff:<20}: {acc:6.2f}% ({stats['correct']}/{stats['total']})")

    print("\n📋 PER-DOMAIN PRECISION, RECALL & F1-SCORE:")
    print(f"  {'Domain':<18} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10} | {'Support (TP+FN)'}")
    print("  " + "-" * 65)
    for c in eval_classes:
        stats = metrics["per_class"][c]
        support = stats["tp"] + stats["fn"]
        print(f"  {c:<18} | {stats['precision']:<10.4f} | {stats['recall']:<10.4f} | {stats['f1']:<10.4f} | {support}")

    print("\n🔢 CONFUSION MATRIX (Rows: Expected, Columns: Predicted):")
    header_cols = " ".join([f"{c[:4]:>6}" for c in eval_classes])
    print(f"  {'Expected / Pred':<16} {header_cols}")
    print("  " + "-" * 55)
    for true_c in eval_classes:
        row_vals = " ".join([f"{confusion_matrix[true_c][pred_c]:>6}" for pred_c in eval_classes])
        print(f"  {true_c:<16} {row_vals}")

    if errors_and_warnings:
        print(f"\n⚠️  QUERY MISMATCH / EDGE CASE ANALYSIS ({len(errors_and_warnings)} occurrences):")
        for err in errors_and_warnings:
            print(f"  [{err['id']}] '{err['query']}'")
            print(f"      Expected: {err['expected_domains']} (Primary: {err['expected_primary']})")
            print(f"      Predicted: {err['pred_domains']} (Primary: {err['pred_primary']}, Conf: {err['confidence']})")
            print(f"      Note: {err['notes']}")
    else:
        print("\n✨ Perfect Score! 100% Classification Accuracy detected across benchmark dataset.")

    print("\n" + "=" * 80)

    report = {
        "summary": {
            "total_queries": total_queries,
            "top1_accuracy": round(top1_acc, 4),
            "overall_accuracy_percentage": round(top1_acc * 100, 2),
            "exact_multi_accuracy": round(exact_multi_acc, 4),
            "subset_multi_accuracy": round(subset_multi_acc, 4),
            "micro_f1": metrics["micro"]["f1"],
            "macro_f1": metrics["macro"]["f1"],
            "avg_latency_ms": round(avg_latency, 2),
        },
        "category_breakdown": category_stats,
        "category_stats": category_stats,
        "difficulty_stats": difficulty_stats,
        "per_domain_metrics": metrics["per_class"],
        "confusion_matrix": confusion_matrix,
        "errors": errors_and_warnings,
    }

    if output_json:
        out_file1 = project_root / "eval" / "evaluation_report.json"
        out_file2 = project_root / "eval" / "evaluate_routing.json"
        with open(out_file1, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        with open(out_file2, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"📁 Benchmark JSON reports saved to: {out_file1.name} & {out_file2.name}")

    return report


if __name__ == "__main__":
    run_evaluation(output_json=True)
