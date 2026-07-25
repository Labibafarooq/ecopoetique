import os, sys, requests, json, re
sys.path.insert(0, os.path.expanduser("~/ecopoetique/métaphore"))
from run_task2_subcategories import make_prompt, OLLAMA_URL, MODEL

token = "guimauve"
ctx = ("Je sais bien qu’il est trop tard pour oser ce tête-à-tête ; quand bien même "
       "me déciderais-je enfin à frapper à sa porte, elle n’entendrait pas mes poings "
       "de guimauve, les mortels sont sourds aux fantômes qui appellent.")
cat = "CH"

prompt = make_prompt(token, ctx, cat)
resp = requests.post(OLLAMA_URL, json={
    "model": MODEL,
    "messages": [{"role": "user", "content": prompt}],
    "stream": False,
    "options": {"temperature": 0, "num_predict": 8000, "num_ctx": 16384},
}, timeout=300)
content = resp.json()["message"]["content"]
print("=== RAW OUTPUT ===")
print(content)
