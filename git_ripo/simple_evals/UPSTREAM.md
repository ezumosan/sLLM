# Upstream source

The files `simpleqa_eval.py`, `common.py`, `types.py`, and `LICENSE` in this
directory were copied from OpenAI's public Git repository:

- Repository: <https://github.com/openai/simple-evals>
- Source file: <https://github.com/openai/simple-evals/blob/652c89d0ca9df547706735883097e9537d40dc47/simpleqa_eval.py>
- Pinned commit: `652c89d0ca9df547706735883097e9537d40dc47`
- Commit date: 2026-04-22
- License: MIT (see `LICENSE`)

The upstream source files are kept unchanged. The project-specific adapter in
`src/eval/simpleqa_eval.py` imports the upstream `SimpleQAEval` class and adds
an Ollama sampler and command-line entrypoint. Those adapter pieces are local
integration code, not part of the upstream repository.
