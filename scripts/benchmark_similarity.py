"""Benchmark reproducível do limite de similaridade da task #7-1.

O script usa o mesmo modelo e o mesmo endpoint Ollama do pipeline de
indexação. Ele depende apenas da biblioteca padrão do Python.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Iterable, Mapping, Sequence
from urllib.request import Request, urlopen


CSV_FIELDNAMES = [
    "id",
    "category",
    "similar",
    "source_a",
    "source_b",
    "similarity",
    "cosine_distance",
    "predicted_alert",
    "a",
    "b",
]


def cosine_similarity(vector_a: Sequence[float], vector_b: Sequence[float]) -> float:
    """Calcula a similaridade de cosseno entre dois vetores não nulos."""
    if len(vector_a) != len(vector_b):
        raise ValueError("vectors must have the same dimension")

    norm_a = math.sqrt(sum(value * value for value in vector_a))
    norm_b = math.sqrt(sum(value * value for value in vector_b))
    if norm_a == 0.0 or norm_b == 0.0:
        raise ValueError("cosine similarity is undefined for a zero vector")

    dot_product = sum(a * b for a, b in zip(vector_a, vector_b))
    return dot_product / (norm_a * norm_b)


def evaluate_threshold(
    results: Iterable[Mapping[str, object]], threshold: float
) -> dict[str, float | int]:
    """Avalia um limiar com a regra operacional ``similaridade >= limiar``."""
    tp = fp = tn = fn = 0
    for result in results:
        expected = bool(result["similar"])
        predicted = float(result["similarity"]) >= threshold
        if expected and predicted:
            tp += 1
        elif not expected and predicted:
            fp += 1
        elif not expected and not predicted:
            tn += 1
        else:
            fn += 1

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    accuracy = (tp + tn) / (tp + fp + tn + fn) if tp + fp + tn + fn else 0.0
    return {
        "threshold": threshold,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy": accuracy,
    }


def choose_threshold(results: Sequence[Mapping[str, object]]) -> dict[str, object]:
    """Escolhe o limiar que separa melhor pares equivalentes e não equivalentes.

    Quando há separação perfeita, usa o ponto médio da margem. Em caso de
    sobreposição, maximiza F1 e desempata por menos falsos positivos, maior
    precisão, maior recall e maior limiar, nessa ordem.
    """
    positive_scores = [
        float(result["similarity"]) for result in results if bool(result["similar"])
    ]
    negative_scores = [
        float(result["similarity"]) for result in results if not bool(result["similar"])
    ]
    if not positive_scores or not negative_scores:
        raise ValueError("benchmark requires both similar and non-similar pairs")

    minimum_positive = min(positive_scores)
    maximum_negative = max(negative_scores)
    if maximum_negative < minimum_positive:
        threshold = (maximum_negative + minimum_positive) / 2
        return {
            "threshold": threshold,
            "strategy": "perfect-separation-midpoint",
            "margin": minimum_positive - maximum_negative,
            "metrics": evaluate_threshold(results, threshold),
        }

    candidates = sorted({float(result["similarity"]) for result in results})
    evaluated = [evaluate_threshold(results, candidate) for candidate in candidates]
    best = max(
        evaluated,
        key=lambda metrics: (
            float(metrics["f1"]),
            -int(metrics["fp"]),
            float(metrics["precision"]),
            float(metrics["recall"]),
            float(metrics["threshold"]),
        ),
    )
    return {
        "threshold": best["threshold"],
        "strategy": "best-f1",
        "margin": minimum_positive - maximum_negative,
        "metrics": best,
    }


def operational_threshold(
    selection: Mapping[str, object], results: Sequence[Mapping[str, object]]
) -> float:
    """Converte o corte medido em um valor estável para configuração."""
    raw_threshold = float(selection["threshold"])
    if selection["strategy"] != "perfect-separation-midpoint":
        # Prefere duas casas sem alterar a classificação que selecionou o
        # melhor F1. Entre opções equivalentes, o maior corte é conservador;
        # se nenhuma preserva a matriz de confusão, mantém o valor medido.
        raw_metrics = evaluate_threshold(results, raw_threshold)
        rounded_candidates = {
            math.floor((raw_threshold + 1e-12) * 100) / 100,
            math.ceil((raw_threshold - 1e-12) * 100) / 100,
        }
        confusion_keys = ("tp", "fp", "tn", "fn")
        preserving_candidates = [
            candidate
            for candidate in rounded_candidates
            if all(
                evaluate_threshold(results, candidate)[key] == raw_metrics[key]
                for key in confusion_keys
            )
        ]
        return max(preserving_candidates, default=raw_threshold)

    minimum_positive = min(
        float(result["similarity"])
        for result in results
        if bool(result["similar"])
    )
    maximum_negative = max(
        float(result["similarity"])
        for result in results
        if not bool(result["similar"])
    )
    rounded_up = math.ceil((raw_threshold - 1e-12) * 100) / 100
    if maximum_negative < rounded_up <= minimum_positive:
        return rounded_up
    return raw_threshold


def request_embeddings(
    texts: Sequence[str],
    *,
    base_url: str,
    model: str,
    timeout: int = 120,
) -> list[list[float]]:
    """Gera todos os embeddings em uma chamada batch ao endpoint do Ollama."""
    payload = json.dumps({"model": model, "input": list(texts)}).encode("utf-8")
    request = Request(
        f"{base_url.rstrip('/')}/api/embed",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))

    embeddings = data.get("embeddings")
    if not isinstance(embeddings, list) or len(embeddings) != len(texts):
        raise ValueError("Ollama returned an invalid number of embeddings")
    if not embeddings:
        return []

    dimensions = {len(vector) for vector in embeddings if isinstance(vector, list)}
    if len(dimensions) != 1 or len(embeddings) != sum(
        isinstance(vector, list) for vector in embeddings
    ):
        raise ValueError("Ollama returned embeddings with inconsistent dimensions")
    return embeddings


def benchmark_pairs(
    pairs: Sequence[Mapping[str, object]],
    vectors_by_text: Mapping[str, Sequence[float]],
) -> list[dict[str, object]]:
    """Calcula similaridade e distância para cada par rotulado."""
    results = []
    for pair in pairs:
        similarity = cosine_similarity(
            vectors_by_text[str(pair["a"])], vectors_by_text[str(pair["b"])]
        )
        results.append(
            {
                **pair,
                "similarity": similarity,
                "cosine_distance": 1.0 - similarity,
            }
        )
    return results


def write_results_csv(
    results: Sequence[Mapping[str, object]], output_path: Path
) -> None:
    """Grava os resultados e preserva a origem dos requisitos comparados."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        writer.writerows(results)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset",
        type=Path,
        default=repo_root / "scripts" / "similarity_pairs.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=repo_root
        / "docs"
        / "technical-docs"
        / "resultados-benchmark-similaridade.csv",
    )
    parser.add_argument("--ollama-url", default="http://localhost:11434")
    parser.add_argument("--model", default="nomic-embed-text")
    args = parser.parse_args()

    pairs = json.loads(args.dataset.read_text(encoding="utf-8"))
    required_fields = {
        "id",
        "category",
        "similar",
        "source_a",
        "source_b",
        "a",
        "b",
    }
    if not isinstance(pairs, list) or not pairs:
        raise ValueError("dataset must be a non-empty JSON list")
    for pair in pairs:
        if not isinstance(pair, dict) or not required_fields.issubset(pair):
            raise ValueError(f"invalid pair in dataset: {pair!r}")

    texts = list(dict.fromkeys(str(pair[key]) for pair in pairs for key in ("a", "b")))
    embeddings = request_embeddings(
        texts,
        base_url=args.ollama_url,
        model=args.model,
    )
    vectors_by_text = dict(zip(texts, embeddings))
    results = benchmark_pairs(pairs, vectors_by_text)
    selection = choose_threshold(results)
    threshold = operational_threshold(selection, results)
    metrics = evaluate_threshold(results, threshold)

    for result in results:
        result["predicted_alert"] = float(result["similarity"]) >= threshold

    write_results_csv(results, args.output)

    print(f"Modelo: {args.model}")
    print(f"Pares: {len(results)} | textos únicos: {len(texts)}")
    print(f"Dimensões: {len(embeddings[0]) if embeddings else 0}")
    print(f"Estratégia: {selection['strategy']}")
    print(f"Limiar bruto: {float(selection['threshold']):.6f}")
    print(f"Limiar operacional: {threshold:.4f}")
    print(f"Distância máxima: {1.0 - threshold:.4f}")
    print(
        "Métricas: "
        f"TP={metrics['tp']} FP={metrics['fp']} TN={metrics['tn']} FN={metrics['fn']} "
        f"precision={float(metrics['precision']):.3f} "
        f"recall={float(metrics['recall']):.3f} F1={float(metrics['f1']):.3f}"
    )
    print(f"CSV: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
