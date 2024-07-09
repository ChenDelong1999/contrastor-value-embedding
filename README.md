
**Disclaimer**: This codebase only serves as a reference for UniVar training implementation.

```bash
# example usage

cd /src/contrastors

torchrun --nproc-per-node=4 train.py --config=configs/train/value_embedding.yaml --dtype=bf16
```
