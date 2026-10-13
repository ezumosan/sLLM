# SimpleQA評価の実行

採点器とベンチマーク実装はOpenAIのGitリポジトリから取得したソースを使います。出典、固定コミット、MITライセンスは[git_ripo/simple_evals/UPSTREAM.md](../git_ripo/simple_evals/UPSTREAM.md)に記録しています。`src/eval/simpleqa_eval.py`は公式コードをOllama samplerにつなぐ実行アダプターです。

## 準備

```sh
ollama pull phi3.5
ollama pull qwen2.5:3b
```

Ollamaサーバーを起動した状態で実行します。Python環境にはリポジトリの`requirements.txt`をインストールしてください。

## 全問題を評価

`--num-examples`を省略すると、上流実装が公式CSVの全問題を取得して評価します。Macのアイドルスリープを抑えるため、夜間実行では`caffeinate -i`を付けます。

```sh
caffeinate -i venv/bin/python src/eval/simpleqa_eval.py \
  --model phi3.5 \
  --grader-model qwen2.5:3b \
  --output-dir results/simpleqa
```

実行結果の集計JSONを`results/simpleqa/`に保存します。公式評価器の実行はシリアルにして、回答モデルと採点モデルが同時に大量のリクエストを受けないようにしています。

10問だけで動作を見たい場合は次のようにします。

```sh
venv/bin/python src/eval/simpleqa_eval.py \
  --model phi3.5 --grader-model qwen2.5:3b --num-examples 10
```

## 出典と採点の解釈

OpenAIの`SimpleQAEval`、公式採点プロンプト、3値ラベル処理、指標実装を上流ソースから利用します。Ollama互換にするためのSamplerクラスとコマンドライン部分は、このリポジトリで追加しています。

採点モデルは論文で使用されたChatGPTではなく、`--grader-model`で指定するローカルOllamaモデルです。そのため、論文掲載値とは直接比較できません。モデル間の比較では採点モデルと設定を固定してください。

出典: [OpenAI simple-evals](https://github.com/openai/simple-evals)、[SimpleQA公式CSV](https://openaipublic.blob.core.windows.net/simple-evals/simple_qa_test_set.csv)、[SimpleQA論文](https://cdn.openai.com/papers/simpleqa.pdf)。
