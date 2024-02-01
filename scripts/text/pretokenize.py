from argparse import ArgumentParser
from itertools import chain

from datasets import concatenate_datasets, load_dataset
from transformers import AutoTokenizer


def parse_args():
    parser = ArgumentParser()
    parser.add_argument("--tokenizer_name", required=True)
    parser.add_argument("--seq_len", required=True, type=int)
    parser.add_argument("--hf_save_name", required=True)
    parser.add_argument("--num_workers", default=8, type=int)

    return parser.parse_args()


args = parse_args()


tokenizer = AutoTokenizer.from_pretrained(args.tokenizer_name)
if tokenizer.cls_token is None:
    tokenizer.add_special_tokens({"cls_token": "<s>"})

tokenizer.model_max_length = args.seq_len

bookcorpus = load_dataset("bookcorpus", split="train")
wiki = load_dataset("wikimedia/wikipedia", "20231101.en", split="train")
wiki = wiki.remove_columns([col for col in wiki.column_names if col != "text"])  # only keep the 'text' column

assert bookcorpus.features.type == wiki.features.type
raw_datasets = concatenate_datasets([bookcorpus, wiki])

num_proc = args.num_workers
print(f"The max length for the tokenizer is: {tokenizer.model_max_length}")


def group_texts(examples):
    tokenized_inputs = tokenizer(
        examples["text"], return_special_tokens_mask=True, truncation=False, max_length=tokenizer.model_max_length
    )
    return tokenized_inputs


# preprocess dataset
tokenized_datasets = raw_datasets.map(group_texts, batched=True, remove_columns=["text"], num_proc=num_proc)


def group_texts(examples):
    # Concatenate all texts.
    concatenated_examples = {k: list(chain(*examples[k])) for k in examples.keys()}
    total_length = len(concatenated_examples[list(examples.keys())[0]])
    # We drop the small remainder, we could add padding if the model supported it instead of this drop, you can
    # customize this part to your needs.
    if total_length >= tokenizer.model_max_length:
        total_length = (total_length // tokenizer.model_max_length) * tokenizer.model_max_length
    # Split by chunks of max_len.
    result = {
        k: [t[i : i + tokenizer.model_max_length] for i in range(0, total_length, tokenizer.model_max_length)]
        for k, t in concatenated_examples.items()
    }
    return result


tokenized_datasets = tokenized_datasets.map(group_texts, batched=True, num_proc=num_proc, desc="Grouping texts")

tokenized_datasets.push_to_hub(args.hf_save_name, private=True)
