---
base_model: Qwen/Qwen3-0.6B
library_name: peft
model_name: openzess_qwen3_0.6b_rl
tags:
- base_model:adapter:Qwen/Qwen3-0.6B
- grpo
- lora
- transformers
- trl
licence: license
pipeline_tag: text-generation
---

# Model Card for openzess_qwen3_0.6b_rl

This model is a fine-tuned version of [Qwen/Qwen3-0.6B](https://huggingface.co/Qwen/Qwen3-0.6B).
It has been trained using [TRL](https://github.com/huggingface/trl).

## Quick start

```python
from transformers import pipeline

question = "If you had a time machine, but could only go to the past or the future once and never return, which would you choose and why?"
generator = pipeline("text-generation", model="None", device_map="auto")
output = generator([{"role": "user", "content": question}], max_new_tokens=128, return_full_text=False)[0]
print(output["generated_text"])
```

## Training procedure

 



This model was trained with GRPO, a method introduced in [DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models](https://huggingface.co/papers/2402.03300).

### Framework versions

- PEFT 0.22.0
- TRL: 1.18.2
- Transformers: 5.17.0
- Pytorch: 2.11.0+cu128
- Datasets: 5.2.0
- Tokenizers: 0.23.1

## Citations

Cite GRPO as:

```bibtex
@article{shao2024deepseekmath,
    title        = {{DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models}},
    author       = {Zhihong Shao and Peiyi Wang and Qihao Zhu and Runxin Xu and Junxiao Song and Mingchuan Zhang and Y. K. Li and Y. Wu and Daya Guo},
    year         = 2024,
    eprint       = {arXiv:2402.03300},
}
```

Cite TRL as:
    
```bibtex
@software{vonwerra2020trl,
  title   = {{TRL: Transformers Reinforcement Learning}},
  author  = {von Werra, Leandro and Belkada, Younes and Tunstall, Lewis and Beeching, Edward and Thrush, Tristan and Lambert, Nathan and Huang, Shengyi and Rasul, Kashif and Gallouédec, Quentin and Dirhoussi, Amine},
  license = {Apache-2.0},
  url     = {https://github.com/huggingface/trl},
  year    = {2020}
}
```