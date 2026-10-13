import json
import unittest
from unittest.mock import MagicMock, patch

from scripts.benchmark_similarity import (
    benchmark_pairs,
    choose_threshold,
    cosine_similarity,
    evaluate_threshold,
    operational_threshold,
    request_embeddings,
)


class CosineSimilarityTests(unittest.TestCase):
    def test_identical_vectors_have_similarity_one(self):
        self.assertAlmostEqual(cosine_similarity([1.0, 2.0], [1.0, 2.0]), 1.0)

    def test_orthogonal_vectors_have_similarity_zero(self):
        self.assertAlmostEqual(cosine_similarity([1.0, 0.0], [0.0, 1.0]), 0.0)

    def test_rejects_vectors_with_different_dimensions(self):
        with self.assertRaisesRegex(ValueError, "same dimension"):
            cosine_similarity([1.0], [1.0, 2.0])

    def test_rejects_zero_vector(self):
        with self.assertRaisesRegex(ValueError, "zero vector"):
            cosine_similarity([0.0, 0.0], [1.0, 2.0])


class ThresholdTests(unittest.TestCase):
    RESULTS = [
        {"similar": True, "similarity": 0.91},
        {"similar": True, "similarity": 0.84},
        {"similar": False, "similarity": 0.73},
        {"similar": False, "similarity": 0.65},
    ]

    def test_evaluates_confusion_matrix_and_metrics(self):
        metrics = evaluate_threshold(self.RESULTS, threshold=0.80)

        self.assertEqual(metrics["tp"], 2)
        self.assertEqual(metrics["fp"], 0)
        self.assertEqual(metrics["tn"], 2)
        self.assertEqual(metrics["fn"], 0)
        self.assertEqual(metrics["precision"], 1.0)
        self.assertEqual(metrics["recall"], 1.0)
        self.assertEqual(metrics["f1"], 1.0)

    def test_chooses_midpoint_of_perfect_separation_gap(self):
        selection = choose_threshold(self.RESULTS)

        self.assertAlmostEqual(selection["threshold"], 0.785)
        self.assertEqual(selection["strategy"], "perfect-separation-midpoint")
        self.assertEqual(selection["metrics"]["f1"], 1.0)

    def test_overlapping_scores_choose_best_f1_then_fewer_false_positives(self):
        results = [
            {"similar": True, "similarity": 0.90},
            {"similar": True, "similarity": 0.70},
            {"similar": False, "similarity": 0.80},
            {"similar": False, "similarity": 0.60},
        ]

        selection = choose_threshold(results)

        self.assertEqual(selection["threshold"], 0.70)
        self.assertEqual(selection["strategy"], "best-f1")
        self.assertEqual(selection["metrics"]["tp"], 2)
        self.assertEqual(selection["metrics"]["fp"], 1)

    def test_rounds_perfect_separator_up_without_crossing_positive_scores(self):
        selection = choose_threshold(self.RESULTS)

        self.assertEqual(operational_threshold(selection, self.RESULTS), 0.79)

    def test_preserves_raw_separator_when_rounding_down_would_create_false_positive(self):
        results = [
            {"similar": True, "similarity": 0.80002},
            {"similar": False, "similarity": 0.80001},
        ]
        selection = choose_threshold(results)

        self.assertEqual(operational_threshold(selection, results), selection["threshold"])

    def test_preserves_raw_separator_when_rounding_up_would_create_false_negative(self):
        results = [
            {"similar": True, "similarity": 0.80009},
            {"similar": False, "similarity": 0.80008},
        ]
        selection = choose_threshold(results)

        self.assertEqual(operational_threshold(selection, results), selection["threshold"])

    def test_rounds_best_f1_cut_up_to_reduce_overfitting_and_false_positives(self):
        selection = {"threshold": 0.654449, "strategy": "best-f1"}

        self.assertEqual(operational_threshold(selection, self.RESULTS), 0.66)


class BenchmarkTests(unittest.TestCase):
    def test_requests_embeddings_in_one_batch(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(
            {"embeddings": [[1.0, 0.0], [0.0, 1.0]]}
        ).encode("utf-8")

        with patch("scripts.benchmark_similarity.urlopen", return_value=response) as urlopen:
            vectors = request_embeddings(
                ["texto a", "texto b"],
                base_url="http://localhost:11434",
                model="nomic-embed-text",
            )

        self.assertEqual(vectors, [[1.0, 0.0], [0.0, 1.0]])
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "http://localhost:11434/api/embed")
        self.assertEqual(
            json.loads(request.data),
            {"model": "nomic-embed-text", "input": ["texto a", "texto b"]},
        )

    def test_benchmarks_pairs_with_cosine_similarity_and_distance(self):
        pairs = [
            {
                "id": "eq-01",
                "category": "equivalent",
                "similar": True,
                "a": "login",
                "b": "autenticacao",
            }
        ]
        vectors = {"login": [1.0, 0.0], "autenticacao": [0.8, 0.6]}

        results = benchmark_pairs(pairs, vectors)

        self.assertAlmostEqual(results[0]["similarity"], 0.8)
        self.assertAlmostEqual(results[0]["cosine_distance"], 0.2)
        self.assertTrue(results[0]["similar"])


if __name__ == "__main__":
    unittest.main()
