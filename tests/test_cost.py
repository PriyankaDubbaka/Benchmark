import os
import unittest
from unittest import mock

from bambench.cost import cost, gpu_share
from bambench.systems.vllm_vlm import VllmVlm


def summary(**kw):
    s = {"counts": {"pages": 10}, "runtime_s": 360.0, "card": {"slice": "20 GB"}}
    s.update(kw)
    return s


class Cost(unittest.TestCase):
    def test_slice_share(self):
        self.assertEqual(gpu_share({"slice": "20 GB"}), 0.25)
        self.assertEqual(gpu_share({"slice": "40 GB (8-bit)"}), 0.5)
        self.assertEqual(gpu_share({}), 0.0)  # CPU only

    def test_time_and_cost_from_old_summary(self):
        with mock.patch.dict(os.environ, {"BAMBENCH_A100_EUR_PER_HOUR": "2"}):
            c = cost(summary())
        self.assertEqual(c["seconds_per_page"], 36.0)
        # 36 s/page is 10 hours per 1,000 pages, a quarter A100 at 2 EUR/h
        self.assertEqual(c["eur_per_1000_pages"], 5.0)
        self.assertIsNone(c["output_tokens_per_page"])

    def test_tokens_per_page(self):
        c = cost(summary(usage={"requests": 10, "prompt_tokens": 15000, "completion_tokens": 8000, "truncated": 2}))
        self.assertEqual(c["prompt_tokens_per_page"], 1500)
        self.assertEqual(c["output_tokens_per_page"], 800)
        self.assertEqual(c["truncated_pages"], 2)

    def test_no_pages(self):
        self.assertIsNone(cost(summary(counts={"pages": 0}))["seconds_per_page"])


class Usage(unittest.TestCase):
    def test_counts_tokens_and_cutoffs(self):
        s = VllmVlm({"id": "x", "model": "m"})
        self.assertIsNone(s.usage)
        s._count({"choices": [{"finish_reason": "stop"}], "usage": {"prompt_tokens": 100, "completion_tokens": 40}})
        s._count({"choices": [{"finish_reason": "length"}], "usage": {"prompt_tokens": 120, "completion_tokens": 4096}})
        s._count({"choices": [{"finish_reason": "stop"}]})  # server without usage
        self.assertEqual(s.usage, {"requests": 3, "prompt_tokens": 220, "completion_tokens": 4136, "truncated": 1})


if __name__ == "__main__":
    unittest.main()
