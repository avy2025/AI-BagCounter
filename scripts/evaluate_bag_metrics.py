import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score, precision_score, f1_score, roc_auc_score

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "evaluation", "bag_events.csv")

def main():
    if not os.path.exists(CSV_PATH):
        print(f"[ERROR] Label file not found: {CSV_PATH}")
        print("Create 'evaluation/bag_events.csv' with columns:")
        print("scenario_id,bag_id,gt_crossed,pred_crossed,score")
        return

    df = pd.read_csv(CSV_PATH)

    # Clean up any extra header or non-numeric rows
    for col in ["gt_crossed", "pred_crossed"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    if "score" in df.columns:
        df["score"] = pd.to_numeric(df["score"], errors="coerce")

    # Drop rows where required fields are missing
    df = df.dropna(subset=["gt_crossed", "pred_crossed"])
    if df.empty:
        print("[ERROR] No valid numeric rows found in bag_events.csv.")
        print("Ensure gt_crossed and pred_crossed are 0/1 values.")
        return

    # Ground truth and predictions
    y_true = df["gt_crossed"].to_numpy().astype(int)
    y_pred = df["pred_crossed"].to_numpy().astype(int)

    # If you have a proper score column, use it; otherwise fall back to pred_crossed
    if "score" in df.columns:
        y_score = df["score"].to_numpy()
    else:
        y_score = y_pred.astype(float)

    # Metrics (binary 0/1 expectation)
    accuracy = accuracy_score(y_true, y_pred)
    # If labels somehow contain more than two classes, fallback to macro average
    unique_labels = np.unique(np.concatenate([y_true, y_pred]))
    avg_mode = "binary" if set(unique_labels).issubset({0, 1}) else "macro"

    precision = precision_score(y_true, y_pred, average=avg_mode, zero_division=0)
    f1 = f1_score(y_true, y_pred, average=avg_mode, zero_division=0)

    # AUC requires both classes present
    if len(np.unique(y_true)) == 2:
        auc = roc_auc_score(y_true, y_score)
    else:
        auc = float("nan")

    print(f"Accuracy : {accuracy:.3f}")
    print(f"Precision: {precision:.3f}")
    print(f"F1-score : {f1:.3f}")
    print(f"AUC      : {auc:.3f}" if not np.isnan(auc) else "AUC      : N/A (only one class present)")

    # Bar chart
    metrics_names = ["Accuracy", "Precision", "F1", "AUC"]
    metrics_values = [accuracy, precision, f1, 0.0 if np.isnan(auc) else auc]

    plt.figure(figsize=(6, 4))
    bars = plt.bar(metrics_names, metrics_values,
                   color=["#3b82f6", "#10b981", "#f59e0b", "#ef4444"])
    plt.ylim(0, 1.0)
    plt.ylabel("Score")
    plt.title("Bag Counting Performance (Per-Bag Labels)")

    # Labels on bars
    for bar, val in zip(bars, metrics_values):
        plt.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + 0.02,
                 f"{val:.2f}",
                 ha="center", va="bottom", fontsize=9)

    plt.tight_layout()

    # Save figure
    out_dir = os.path.join(BASE_DIR, "evaluation")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "bag_metrics.png")
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"Saved metrics plot to: {out_path}")

if __name__ == "__main__":
    main()