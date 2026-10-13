#!/usr/bin/env python3
"""Run OpenAI's SimpleQA reference evaluator with local Ollama models.

The SimpleQA benchmark, grader prompt, grader implementation, and metrics come
from the pinned upstream source in ../../git_ripo/simple_evals. This file is
the project adapter that supplies Ollama samplers and a command-line entrypoint.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import ollama


ROOT = Path(__file__).resolve().parents[2]
UPSTREAM_ROOT = ROOT / "git_ripo"
sys.path.insert(0, str(UPSTREAM_ROOT))

from simple_evals.simpleqa_eval import SimpleQAEval  # noqa: E402
from simple_evals.types import SamplerBase, SamplerResponse  # noqa: E402


ANSWER_SYSTEM_PROMPT = """You are a precise, fact-based QA assistant.
Answer with only the single core answer in English, enclosed in <ans> and </ans>.
Do not include explanations or preambles.
If you do not know the answer with high certainty, reply exactly <ans>I don't know</ans>."""


class OllamaSampler(SamplerBase):
    """Adapt Ollama chat completions to the upstream Simple Evals sampler API."""

    def __init__(
        self,
        model: str,
        *,
        temperature: float,
        seed: int,
        system_prompt: str | None = None,
        num_predict: int = 128,
    ) -> None:
        self.model = model
        self.temperature = temperature
        self.seed = seed
        self.system_prompt = system_prompt
        self.num_predict = num_predict

    @staticmethod
    def _pack_message(content: str, role: str) -> dict[str, str]:
        return {"role": role, "content": content}

    def __call__(self, message_list: list[dict[str, Any]]) -> SamplerResponse:
        messages = list(message_list)
        if self.system_prompt:
            messages.insert(0, {"role": "system", "content": self.system_prompt})

        response = ollama.chat(
            model=self.model,
            messages=messages,
            options={
                "temperature": self.temperature,
                "seed": self.seed,
                "num_predict": self.num_predict,
            },
        )
        response_data = response.model_dump() if hasattr(response, "model_dump") else response
        message = response_data["message"]
        return SamplerResponse(
            response_text=message["content"],
            actual_queried_message_list=messages,
            response_metadata={
                "model": self.model,
                "seed": self.seed,
                "temperature": self.temperature,
                "total_duration": response_data.get("total_duration"),
                "prompt_eval_count": response_data.get("prompt_eval_count"),
                "eval_count": response_data.get("eval_count"),
            },
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="phi3.5", help="Ollama model that answers SimpleQA questions")
    parser.add_argument("--grader-model", default="qwen2.5:3b", help="Ollama model that applies the upstream grader")
    parser.add_argument("--num-examples", type=int, default=None, help="Run a fixed-size upstream sample; omit for the full dataset")
    parser.add_argument("--temperature", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=20261013)
    parser.add_argument("--num-predict", type=int, default=128)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "simpleqa")
    args = parser.parse_args()
    if args.num_examples is not None and args.num_examples < 1:
        parser.error("--num-examples must be a positive integer")
    return args


def main() -> int:
    args = parse_args()
    args.output_dir = args.output_dir.expanduser().resolve()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # The upstream evaluation uses a thread pool by default. Serial execution
    # avoids concurrently loading or querying two local models on a 16 GB Mac.
    os.environ["debug"] = "1"

    answer_sampler = OllamaSampler(
        args.model,
        temperature=args.temperature,
        seed=args.seed,
        system_prompt=ANSWER_SYSTEM_PROMPT,
        num_predict=args.num_predict,
    )
    grader_sampler = OllamaSampler(
        args.grader_model,
        temperature=0.0,
        seed=args.seed,
        num_predict=16,
    )

    started = time.perf_counter()
    evaluator = SimpleQAEval(
        grader_model=grader_sampler,
        num_examples=args.num_examples,
    )
    result = evaluator(answer_sampler)
    elapsed = time.perf_counter() - started

    metrics = result.metrics or {}
    overall_correct = float(metrics.get("is_correct", result.score or 0.0))
    overall_incorrect = float(metrics.get("is_incorrect", 0.0))
    attempted = overall_correct + overall_incorrect
    accuracy_given_attempted = overall_correct / attempted if attempted else 0.0
    f_score = (
        2 * overall_correct * accuracy_given_attempted / (overall_correct + accuracy_given_attempted)
        if overall_correct + accuracy_given_attempted else 0.0
    )

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = args.output_dir / f"simpleqa_{run_id}.json"
    payload = {
        "upstream_repository": "https://github.com/openai/simple-evals",
        "upstream_commit": "652c89d0ca9df547706735883097e9537d40dc47",
        "answer_model": args.model,
        "grader_model": args.grader_model,
        "num_examples": args.num_examples or len(evaluator.examples),
        "temperature": args.temperature,
        "seed": args.seed,
        "num_predict": args.num_predict,
        "elapsed_seconds": round(elapsed, 3),
        "score": float(result.score) if result.score is not None else None,
        "metrics": {key: float(value) for key, value in metrics.items()},
        "overall_correct_rate": overall_correct,
        "accuracy_given_attempted": accuracy_given_attempted,
        "simpleqa_f_score": f_score,
        "grader_note": "Uses the upstream SimpleQA grader prompt/function; local Ollama grading model differs from the model used in the paper.",
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"Saved results to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
