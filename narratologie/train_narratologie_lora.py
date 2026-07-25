"""
LoRA Fine-tuning for Narratological Classification
Uses standard HuggingFace Trainer (not SFTTrainer) for maximum compatibility.
Compatible with transformers>=4.x, peft>=0.19, trl not required.
"""

import os
import csv
import json
import random
import torch
from pathlib import Path
from torch.utils.data import Dataset

# ── Config ────────────────────────────────────────────────────────────────────
MODEL_NAME   = "Qwen/Qwen2.5-7B-Instruct"
GOLD_FILE    = "GOLD_narratologie_clean.csv"
CORPUS_DIR   = os.path.expanduser("~/ecopoetique/CORPUS_TOTAL")
OUTPUT_DIR   = os.path.expanduser("~/ecopoetique/narratologie/lora_model")
RESULTS_FILE = "resultats_lora_eval.csv"
SAMPLE_LINES = 120
SEED         = 42
TRAIN_RATIO  = 0.85
MAX_EPOCHS   = 5
BATCH_SIZE   = 1
GRAD_ACCUM   = 8
LR           = 2e-4
LORA_R       = 8
LORA_ALPHA   = 16
LORA_DROPOUT = 0.05
MAX_SEQ_LEN  = 2048

VALID_CODES = {
    "TYPE NARRATEUR":  ["NAR_AUTOD", "NAR_TEM", "NAR_EXT", "NAR_VAR"],
    "FOCALISATION":    ["FOC_INT", "FOC_EXT", "FOC_ZERO", "FOC_VAR"],
    "MODE NARRATIF":   ["MOD_EVT", "MOD_DESC", "MOD_INTR", "MOD_MIX", "MOD_DIA"],
    "REGIME NARRATIF": ["REG_AUTO", "REG_REAL", "REG_FANT", "REG_SPEC"],
    "ESPACE":          ["ESP_UNIT", "ESP_FRAG", "ESP_ITIN", "ESP_IMAG"],
    "INTRIGUE":        ["INTR_LIN", "INTR_FRAG", "INTR_CYC"],
    "TEMPORALITÉ":     ["TEMP_LIN", "TEMP_DIS", "TEMP_DESORD"],
}
CRITERIA_ORDER = list(VALID_CODES.keys())

# ── Data ──────────────────────────────────────────────────────────────────────

def load_gold(gold_file):
    gold = {}
    with open(gold_file, encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            fn = row["File"].strip()
            gold[fn] = {c: row.get(c, "").strip() for c in CRITERIA_ORDER}
    return gold

def load_excerpt(filename, n_lines=SAMPLE_LINES):
    path = os.path.join(CORPUS_DIR, filename)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    total = len(lines)
    if total <= n_lines:
        return "".join(lines)
    per = n_lines // 4
    sections = []
    for ratio in [0, 0.30, 0.60, 1.0]:
        pos = min(int(total * ratio), total - per)
        sections.append("".join(lines[pos:pos+per]))
    return "\n\n[...]\n\n".join(sections)

def make_text(excerpt, labels=None):
    codes_desc = "\n".join(
        f"- {c}: {' | '.join(v)}" for c, v in VALID_CODES.items()
    )
    user_msg = f"""Tu es un expert en narratologie française. Analyse cet extrait de roman et classe-le selon les 7 critères narratologiques.

CRITÈRES ET CODES VALIDES:
{codes_desc}

RÈGLES: Utilise UNIQUEMENT les codes listés. Réponds en JSON uniquement.

EXTRAIT:
{excerpt[:2000]}

Réponds avec exactement ce JSON:
{{"TYPE NARRATEUR": "CODE", "FOCALISATION": "CODE", "MODE NARRATIF": "CODE", "REGIME NARRATIF": "CODE", "ESPACE": "CODE", "INTRIGUE": "CODE", "TEMPORALITÉ": "CODE"}}"""

    if labels:
        assistant_msg = json.dumps(labels, ensure_ascii=False)
        return f"<|im_start|>user\n{user_msg}<|im_end|>\n<|im_start|>assistant\n{assistant_msg}<|im_end|>"
    return f"<|im_start|>user\n{user_msg}<|im_end|>\n<|im_start|>assistant\n"

def prepare_samples(gold):
    samples, missing = [], 0
    for fn, labels in gold.items():
        excerpt = load_excerpt(fn)
        if excerpt is None:
            missing += 1
            continue
        if not all(labels.get(c) for c in CRITERIA_ORDER):
            continue
        samples.append({"filename": fn, "excerpt": excerpt, "labels": labels})
    print(f"  Prepared {len(samples)} samples ({missing} missing from corpus)")
    return samples

class NarrDataset(Dataset):
    def __init__(self, samples, tokenizer):
        self.items = []
        for s in samples:
            text = make_text(s["excerpt"], s["labels"])
            enc = tokenizer(
                text, truncation=True, max_length=MAX_SEQ_LEN,
                padding="max_length", return_tensors="pt"
            )
            input_ids = enc["input_ids"][0]
            labels = input_ids.clone()
            # Mask user prompt — only train on assistant response
            user_text = make_text(s["excerpt"])  # no labels = just prompt
            user_enc = tokenizer(user_text, return_tensors="pt")
            prompt_len = user_enc["input_ids"].shape[1]
            labels[:prompt_len] = -100
            self.items.append({"input_ids": input_ids, "attention_mask": enc["attention_mask"][0], "labels": labels})

    def __len__(self):
        return len(self.items)

    def __getitem__(self, idx):
        return self.items[idx]

# ── Training ──────────────────────────────────────────────────────────────────

def train_lora(train_samples, val_samples):
    from transformers import (
        AutoTokenizer, AutoModelForCausalLM,
        TrainingArguments, Trainer, BitsAndBytesConfig,
        DataCollatorForSeq2Seq
    )
    from peft import LoraConfig, get_peft_model, TaskType

    print("\nLoading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME, trust_remote_code=True, padding_side="right"
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print("Loading model in 4-bit...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
    )
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )
    model.config.use_cache = False

    lora_config = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
        lora_dropout=LORA_DROPOUT,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    print("Tokenizing dataset...")
    train_ds = NarrDataset(train_samples, tokenizer)
    val_ds   = NarrDataset(val_samples,   tokenizer)

    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=MAX_EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRAD_ACCUM,
        learning_rate=LR,
        bf16=True,
        logging_steps=5,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        warmup_steps=10,
        lr_scheduler_type="cosine",
        report_to="none",
        remove_unused_columns=False,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        processing_class=tokenizer,
    )

    print("\nStarting LoRA training...")
    trainer.train()
    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"\n✅ Model saved to {OUTPUT_DIR}")
    return model, tokenizer

# ── Evaluation ────────────────────────────────────────────────────────────────

def evaluate_lora(model, tokenizer, val_samples):
    import re
    print("\nEvaluating on validation set...")
    scores = {c: {"correct": 0, "total": 0} for c in CRITERIA_ORDER}
    results = []
    model.eval()

    for i, sample in enumerate(val_samples, 1):
        print(f"  [{i}/{len(val_samples)}] {sample['filename'][:45]}", end="", flush=True)
        prompt = make_text(sample["excerpt"])
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=MAX_SEQ_LEN).to(model.device)
        with torch.no_grad():
            out = model.generate(
                **inputs, max_new_tokens=200,
                do_sample=False, pad_token_id=tokenizer.eos_token_id
            )
        response = tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        try:
            m = re.search(r'\{.*?\}', response, re.DOTALL)
            pred = json.loads(m.group(0)) if m else {}
        except Exception:
            pred = {}

        correct = 0
        for c in CRITERIA_ORDER:
            p = pred.get(c, "").strip()
            g = sample["labels"].get(c, "").strip()
            if p and g:
                scores[c]["total"] += 1
                if p == g:
                    scores[c]["correct"] += 1
                    correct += 1
        print(f" {correct}/7")
        results.append({"filename": sample["filename"],
                        "predicted": json.dumps(pred, ensure_ascii=False),
                        "gold": json.dumps(sample["labels"], ensure_ascii=False)})

    print("\n" + "="*60)
    print("LORA EVALUATION RESULTS")
    print("="*60)
    oc = ot = 0
    for c in CRITERIA_ORDER:
        s = scores[c]
        if s["total"] > 0:
            acc = s["correct"]/s["total"]*100
            print(f"  {c:<20} {s['correct']:>2}/{s['total']:>2}  ({acc:>5.1f}%)  {'█'*int(acc/5)}")
            oc += s["correct"]; ot += s["total"]
    print("-"*60)
    if ot:
        print(f"  {'OVERALL':<20} {oc}/{ot}  ({oc/ot*100:.1f}%)")
    print("="*60)
    print(f"\n  Map-reduce (76 novels):  65.4%")
    print(f"  Hybrid 3-way (60):       69.3%")
    print(f"  LoRA (this run):         {oc/ot*100:.1f}%" if ot else "  LoRA: N/A")
    return results

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    random.seed(SEED)
    print("="*60)
    print("LoRA Fine-tuning — Narratological Classification")
    print(f"Model: {MODEL_NAME} | LoRA r={LORA_R} | Epochs={MAX_EPOCHS}")
    print("="*60)

    gold = load_gold(GOLD_FILE)
    print(f"\nGold set: {len(gold)} novels")

    print("\nPreparing dataset...")
    samples = prepare_samples(gold)

    random.shuffle(samples)
    split = int(len(samples) * TRAIN_RATIO)
    train_s, val_s = samples[:split], samples[split:]
    print(f"  Train: {len(train_s)}  |  Val: {len(val_s)}")

    model, tokenizer = train_lora(train_s, val_s)
    results = evaluate_lora(model, tokenizer, val_s)

    with open(RESULTS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["filename","predicted","gold"])
        writer.writeheader()
        writer.writerows(results)
    print(f"\n✅ Results saved to {RESULTS_FILE}")

if __name__ == "__main__":
    main()
