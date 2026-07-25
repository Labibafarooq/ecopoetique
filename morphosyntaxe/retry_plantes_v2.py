#!/usr/bin/env python3
"""
Retry failed batches from Task 1 plantes run.
Reuses the EXACT same functions (build_batch_prompt, call_ollama, parse_batch,
CORE_DEFINITIONS, EXAMPLES, BATCH_SIZE) from run_task1_corpus.py via import,
so the retry cannot drift from the prompt/schema used in the main run.

Also patches the master output file (task1_plantes_labels.csv) in place once
reclassification is done, replacing the default "référentiel" placeholder
that was written for these rows during the main run. A backup is made first.
"""
import sys, os, csv, time, shutil

sys.path.insert(0, os.path.expanduser("~/ecopoetique/métaphore"))
import run_task1_corpus as t1

CATEGORY     = "plantes"
RESULTS_DIR  = os.path.expanduser("~/ecopoetique/resultats")
FAILED_FILE  = os.path.join(RESULTS_DIR, "task1_plantes_failed_keys_v2.tsv")
LABELS_FILE  = os.path.join(RESULTS_DIR, "task1_plantes_labels.csv")
NEW_FAILED   = os.path.join(RESULTS_DIR, "task1_plantes_failed_keys_v3.tsv")

BATCH_SIZE = t1.BATCH_SIZE
csv.field_size_limit(10**7)


def load_failed_keys():
    keys = []
    with open(FAILED_FILE, encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            keys.append((row["fichier"], row["token_lexique"], row["contexte"]))
    return keys


def build_corpus_lookup():
    all_rows = t1.load_corpus(CATEGORY)
    lookup = {}
    for r in all_rows:
        key = (r["fichier"], r["token_lexique"], r["contexte"])
        lookup[key] = r
    return lookup


def reclassify(failed_keys, lookup):
    corrected = {}
    new_failed = []
    times = []

    for start in range(0, len(failed_keys), BATCH_SIZE):
        batch_keys = failed_keys[start:start + BATCH_SIZE]
        chunk = [
            lookup.get(k, {"fichier": k[0], "token_lexique": k[1], "contexte": k[2]})
            for k in batch_keys
        ]
        items = [(j + 1, r["token_lexique"], r["contexte"]) for j, r in enumerate(chunk)]

        t0 = time.time()
        try:
            raw = t1.call_ollama(t1.build_batch_prompt(items, CATEGORY))
            preds = t1.parse_batch(raw, len(chunk))
        except Exception as e:
            print(f"  ERROR: {e} — retrying once...", flush=True)
            time.sleep(5)
            try:
                raw = t1.call_ollama(t1.build_batch_prompt(items, CATEGORY))
                preds = t1.parse_batch(raw, len(chunk))
            except Exception:
                preds = {}
        times.append(time.time() - t0)

        for j, key in enumerate(batch_keys):
            label = preds.get(j + 1)
            if label is None:
                label = "référentiel"
                new_failed.append(key)
            corrected[key] = label

        done = start + len(batch_keys)
        if done % 100 == 0 or done >= len(failed_keys):
            avg = sum(times) / len(times) / BATCH_SIZE
            eta_h = (len(failed_keys) - done) * avg / 3600
            fig = sum(1 for l in corrected.values() if l == "figuré")
            ref = sum(1 for l in corrected.values() if l == "référentiel")
            print(
                f"  [{done}/{len(failed_keys)}] ref={ref} fig={fig} "
                f"({fig / done * 100:.1f}% fig) speed={avg:.1f}s/row "
                f"ETA={eta_h:.1f}h still_failing={len(new_failed)}",
                flush=True,
            )

    return corrected, new_failed


def patch_file(path, corrected):
    backup = path + ".bak_before_retry_patch"
    if not os.path.exists(backup):
        shutil.copy2(path, backup)
        print(f"Backed up {path} -> {backup}", flush=True)

    tmp_path = path + ".tmp_patch"
    n_patched = 0
    with open(path, encoding="utf-8", newline="") as fin, \
         open(tmp_path, "w", encoding="utf-8", newline="") as fout:
        reader = csv.DictReader(fin, delimiter="\t")
        writer = csv.DictWriter(fout, fieldnames=reader.fieldnames, delimiter="\t")
        writer.writeheader()
        for row in reader:
            key = (row["fichier"], row["token_lexique"], row["contexte"])
            if key in corrected:
                row["task1_label"] = corrected[key]
                n_patched += 1
            writer.writerow(row)
    os.replace(tmp_path, path)
    print(f"Patched {n_patched} rows in {path}", flush=True)


def main():
    failed_keys = load_failed_keys()
    print(f"Reclassifying {len(failed_keys)} failed rows using run_task1_corpus.py's exact prompt logic", flush=True)

    print("Building corpus lookup for lemme/categorie recovery...", flush=True)
    lookup = build_corpus_lookup()

    corrected, new_failed = reclassify(failed_keys, lookup)

    if new_failed:
        with open(NEW_FAILED, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, delimiter="\t")
            w.writerow(["fichier", "token_lexique", "contexte"])
            for k in new_failed:
                w.writerow(k)
        print(f"{len(new_failed)} rows still failed after retry — logged to {NEW_FAILED}", flush=True)

    print("\nPatching master output file...", flush=True)
    patch_file(LABELS_FILE, corrected)

    ref_total = sum(1 for l in corrected.values() if l == "référentiel")
    fig_total = sum(1 for l in corrected.values() if l == "figuré")
    if corrected:
        print(f"\nDone. Reclassified: {ref_total} référentiel / {fig_total} figuré "
              f"({fig_total / len(corrected) * 100:.1f}% fig)", flush=True)
    else:
        print("\nNo rows to reclassify.", flush=True)


if __name__ == "__main__":
    main()
