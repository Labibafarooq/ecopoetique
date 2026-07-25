"""
Ask Labiba — Humanistica RAG
==============================
Unified RAG interface for digital humanities researchers.
Formation HANDS — Sorbonne Université, 11 juin 2026.

Launch:
    streamlit run pipeline/ask_labiba.py --server.port 8505
"""

import json, re, sys, requests, hashlib
from pathlib import Path
from datetime import datetime
from collections import Counter
from typing import Optional
from lxml import etree

import streamlit as st
from bs4 import BeautifulSoup

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "pipeline"))

from llama_index.core import (
    Settings, StorageContext, load_index_from_storage,
    VectorStoreIndex, Document
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

CORPUS_BASE      = PROJECT_ROOT / "data" / "corpus"
STORE_BASE       = PROJECT_ROOT / "data" / "vector_stores"
EMBEDDING_MODEL  = "intfloat/multilingual-e5-large"
TESTBED_LOG_PATH = PROJECT_ROOT / "data" / "prompt_testbed_log.jsonl"
TEI_NS           = {"tei": "http://www.tei-c.org/ns/1.0"}

# 🔑 Mistral API key
MISTRAL_API_KEY = "key"

# Local Ollama models running on server
OLLAMA_BASE_URL_11434 = "http://localhost:11434"
OLLAMA_BASE_URL_11435 = "http://localhost:11435"

DEFAULT_PROMPTS = {
    "Generic DH": (
        "Tu es un assistant spécialisé dans les éditions numériques en humanités.\n"
        "Réponds uniquement en te basant sur les documents fournis.\n"
        "Cite toujours tes sources avec la date et le titre du document.\n"
        "Si plusieurs documents sont présents, traite chacun séparément."
    ),
    "Historical Analyst": (
        "You are a historical analyst working with digital editions.\n"
        "Answer precisely based only on the provided documents.\n"
        "Always cite your sources and note the date and document title.\n"
        "If multiple documents are present, address each one separately.\n"
        "If information is absent from the sources, state it explicitly."
    ),
    "Minimal / Retrieval": (
        "Answer based on the documents provided. Be concise. Cite sources [Source 1], [Source 2]...\n"
        "If multiple documents, address each separately."
    ),
}

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DH Humanistica",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS — refined dark academic aesthetic ─────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;700&family=Source+Sans+3:wght@300;400;600&family=JetBrains+Mono:wght@400;500&display=swap');

/* Global */
html, body, [class*="css"] {
    font-family: 'Source Sans 3', sans-serif;
}

/* Hide footer only */
footer {visibility: hidden;}

/* Main background */
.stApp {
    background: linear-gradient(135deg, #0f1117 0%, #1a1f2e 50%, #0f1117 100%);
}

/* Main title */
.ask-labiba-title {
    font-family: 'Playfair Display', serif;
    font-size: 3.2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #c9a96e 0%, #f0d080 50%, #c9a96e 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-align: center;
    letter-spacing: -0.02em;
    margin-bottom: 0.2rem;
}

.ask-labiba-subtitle {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 0.9rem;
    color: #8892a4;
    text-align: center;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 2rem;
}

/* Corpus info banner */
.corpus-banner {
    background: linear-gradient(90deg, #1e2d1e, #243324);
    border: 1px solid #2d4a2d;
    border-left: 4px solid #4caf50;
    border-radius: 8px;
    padding: 0.8rem 1.2rem;
    margin: 1rem 0;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    color: #81c784;
}

/* Pedagogy box */
.pedagogy-box {
    background: linear-gradient(135deg, #1a2340, #1e2a4a);
    border: 1px solid #2d3f6b;
    border-left: 4px solid #c9a96e;
    border-radius: 8px;
    padding: 1.2rem 1.4rem;
    margin: 1.2rem 0;
    font-size: 0.9rem;
    line-height: 1.7;
    color: #b8c5d6;
}

.pedagogy-box strong {
    color: #c9a96e;
}

/* Answer box */
.answer-box {
    background: linear-gradient(135deg, #1a2a1a, #1e301e);
    border: 1px solid #2d4a2d;
    border-left: 4px solid #66bb6a;
    border-radius: 8px;
    padding: 1.4rem;
    margin: 1rem 0;
    line-height: 1.8;
    color: #c8e6c9;
    font-family: 'Source Sans 3', sans-serif;
    font-size: 0.95rem;
}

/* Source card */
.source-card {
    background: #161b27;
    border: 1px solid #252d3d;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin: 0.6rem 0;
    transition: border-color 0.2s;
}
.source-card:hover {
    border-color: #c9a96e;
}

/* Score badges */
.score-green { color: #66bb6a; font-weight: 600; }
.score-yellow { color: #ffd54f; font-weight: 600; }
.score-orange { color: #ffa726; font-weight: 600; }
.score-red { color: #ef5350; font-weight: 600; }

/* Section headers */
.section-header {
    font-family: 'Playfair Display', serif;
    font-size: 1.3rem;
    color: #c9a96e;
    border-bottom: 1px solid #2d3547;
    padding-bottom: 0.4rem;
    margin: 1.5rem 0 0.8rem 0;
}

/* Info box */
.info-box {
    background: #161b27;
    border: 1px solid #252d3d;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin: 1rem 0;
    font-size: 0.88rem;
    color: #8892a4;
    line-height: 1.6;
}

/* Sidebar styling */
section[data-testid="stSidebar"] {
    background: #0d1117 !important;
    border-right: 1px solid #21262d;
}

section[data-testid="stSidebar"] .stMarkdown {
    color: #8892a4;
}

/* Buttons */
.stButton > button {
    font-family: 'Source Sans 3', sans-serif;
    font-weight: 600;
    letter-spacing: 0.05em;
}

/* Text input */
.stTextInput > div > div > input {
    background: #161b27 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    color: #e6edf3 !important;
    font-family: 'Source Sans 3', sans-serif !important;
    font-size: 1rem !important;
}

.stTextInput > div > div > input:focus {
    border-color: #c9a96e !important;
    box-shadow: 0 0 0 2px rgba(201, 169, 110, 0.15) !important;
}

/* Selectbox */
.stSelectbox > div > div {
    background: #161b27 !important;
    border: 1px solid #30363d !important;
}

/* File uploader */
.stFileUploader {
    background: #161b27;
    border: 2px dashed #30363d;
    border-radius: 12px;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: transparent;
    border-bottom: 1px solid #21262d;
}
.stTabs [data-baseweb="tab"] {
    color: #8892a4;
    font-family: 'Source Sans 3', sans-serif;
}
.stTabs [aria-selected="true"] {
    color: #c9a96e !important;
    border-bottom-color: #c9a96e !important;
}

/* Expander */
.streamlit-expanderHeader {
    background: #161b27 !important;
    border: 1px solid #252d3d !important;
    border-radius: 8px !important;
}

/* Info cards */
.info-card {
    background: linear-gradient(135deg, #161b27, #1a2035);
    border: 1px solid #252d3d;
    border-radius: 12px;
    padding: 1.4rem;
    text-align: center;
    height: 100%;
    transition: border-color 0.2s, transform 0.2s;
}
.info-card:hover {
    border-color: #c9a96e;
    transform: translateY(-2px);
}
.card-icon {
    font-size: 2rem;
    margin-bottom: 0.6rem;
}
.card-title {
    font-family: 'Playfair Display', serif;
    font-size: 1rem;
    color: #c9a96e;
    font-weight: 700;
    margin-bottom: 0.5rem;
}
.card-text {
    font-size: 0.85rem;
    color: #8892a4;
    line-height: 1.5;
}

/* Score legend in main page */
.score-legend {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
    margin: 0.5rem 0;
    font-size: 0.82rem;
    color: #8892a4;
}
</style>
""", unsafe_allow_html=True)


# ── Translations ───────────────────────────────────────────────────────────────
T = {
    "fr": {
        "subtitle": "BY OBTIC · SCAI",
        "tab1": "📚 Corpus existant",
        "tab2": "📤 Téléverser un corpus",
        "no_corpus": "Aucun corpus indexé trouvé sur le serveur.",
        "choose": "👆 Choisissez un corpus dans l'un des onglets ci-dessus pour commencer.",
        "use_corpus": "✅ Utiliser ce corpus",
        "upload_info": "Uploadez vos fichiers **TEI-XML** pour les interroger avec le RAG.\nLe système extrait automatiquement le titre, l'auteur et la date depuis les métadonnées TEI.",
        "corpus_name_label": "Nom du corpus (optionnel)",
        "index_btn": "⚙️ Indexer et utiliser",
        "indexing": "Extraction des métadonnées TEI et calcul des embeddings...",
        "search_title": "🔍 Interroger :",
        "examples_label": "Questions suggérées :",
        "ex1": "Quel est le sujet principal de ce corpus ?",
        "ex2": "Quels personnages sont mentionnés ?",
        "ex3": "Quels événements historiques sont décrits ?",
        "ex4": "Quelle est la période couverte ?",
        "ex5": "De quoi parle ce corpus ?",
        "placeholder": "Posez votre question en français ou en anglais...",
        "search_btn": "🔍 Rechercher",
        "preset_label": "Style de réponse :",
        "presets": {
            "🎓 Réponse générale": DEFAULT_PROMPTS["Generic DH"],
            "🏛️ Analyse historique": DEFAULT_PROMPTS["Historical Analyst"],
            "📝 Résumé court": DEFAULT_PROMPTS["Minimal / Retrieval"],
        },
        "generating": "Génération de la réponse...",
        "answer_title": "🤖 Réponse",
        "sources_title": "📄 Sources utilisées",
        "passages": "passages trouvés",
        "pedagogy": "💡 <strong>Comment le système a trouvé ces résultats :</strong><br>Votre question a été transformée en vecteur numérique, puis comparée aux passages du corpus <strong>{corpus}</strong>. Les <strong>{n}</strong> passages ci-dessous sont les plus proches sémantiquement de votre question.",
        "content": "Contenu :",
        "date": "Date", "author": "Auteur", "type": "Type", "title_label": "Titre",
        "how_title": "ℹ️ Comment ça marche",
        "how_steps": "**1.** Choisissez un corpus\n**2.** Posez votre question\n**3.** Lisez la réponse et les sources\n\nLe système cherche par **sens**, pas par mots-clés exacts.",
        "scores_title": "🎯 Scores de pertinence",
        "scores_text": "🟢 **> 0.6** — Très pertinent\n\n🟡 **0.4–0.6** — Pertinent\n\n🟠 **0.2–0.4** — Peu pertinent\n\n🔴 **< 0.2** — Faiblement lié",
        "very_relevant": "Très pertinent",
        "relevant": "Pertinent",
        "not_relevant": "Peu pertinent",
        "weakly": "Faiblement lié",
        "no_api": "⚠️ Clé API non configurée.",
        "tei_only": "⚠️ Seuls les fichiers TEI-XML (.xml) sont acceptés.",
        "no_text": "Aucun texte extrait des fichiers TEI.",
    },
    "en": {
        "subtitle": "BY OBTIC · SCAI",
        "tab1": "📚 Existing corpus",
        "tab2": "📤 Upload corpus",
        "no_corpus": "No indexed corpus found on the server.",
        "choose": "👆 Choose a corpus from one of the tabs above to get started.",
        "use_corpus": "✅ Use this corpus",
        "upload_info": "Upload your **TEI-XML** files to query them with RAG.\nThe system automatically extracts title, author and date from TEI metadata.",
        "corpus_name_label": "Corpus name (optional)",
        "index_btn": "⚙️ Index and use",
        "indexing": "Extracting TEI metadata and computing embeddings...",
        "search_title": "🔍 Search:",
        "examples_label": "Suggested questions:",
        "ex1": "What is the main subject of this corpus?",
        "ex2": "Which characters are mentioned?",
        "ex3": "What historical events are described?",
        "ex4": "What time period is covered?",
        "ex5": "What is this corpus about?",
        "placeholder": "Ask your question in French or English...",
        "search_btn": "🔍 Search",
        "preset_label": "Answer style:",
        "presets": {
            "🎓 General answer": (
                "You are a digital humanities assistant. "
                "Answer ONLY in English based strictly on the provided sources. "
                "Cite sources [Source 1], [Source 2]. "
                "If multiple documents are present, address each one separately. "
                "NEVER answer in French. Always use English."
            ),
            "🏛️ Historical analysis": (
                "You are a historical analyst. "
                "Answer ONLY in English based strictly on the provided documents. "
                "Place documents in their historical context, cite sources [Source 1], [Source 2]. "
                "If multiple documents are present, address each one separately. "
                "NEVER answer in French. Always use English."
            ),
            "📝 Short summary": (
                "Answer ONLY in English in 3-4 sentences maximum. "
                "Be concise. Cite sources [Source 1]. "
                "If multiple documents, summarise each separately. "
                "NEVER answer in French. Always use English."
            ),
        },
        "generating": "Generating answer...",
        "answer_title": "🤖 Answer",
        "sources_title": "📄 Sources used",
        "passages": "passages found",
        "pedagogy": "💡 <strong>How the system found these results:</strong><br>Your question was transformed into a numerical vector, then compared to passages in corpus <strong>{corpus}</strong>. The <strong>{n}</strong> passages below are the most semantically close to your question.",
        "content": "Content:",
        "date": "Date", "author": "Author", "type": "Type", "title_label": "Title",
        "how_title": "ℹ️ How it works",
        "how_steps": "**1.** Choose a corpus\n**2.** Ask your question\n**3.** Read the answer and sources\n\nThe system searches by **meaning**, not exact keywords.",
        "scores_title": "🎯 Relevance scores",
        "scores_text": "🟢 **> 0.6** — Very relevant\n\n🟡 **0.4–0.6** — Relevant\n\n🟠 **0.2–0.4** — Not relevant\n\n🔴 **< 0.2** — Weakly linked",
        "very_relevant": "Very relevant",
        "relevant": "Relevant",
        "not_relevant": "Not relevant",
        "weakly": "Weakly linked",
        "no_api": "⚠️ API key not configured.",
        "tei_only": "⚠️ Only TEI-XML (.xml) files are accepted.",
        "no_text": "No text extracted from TEI files.",
    }
}


# ── Utilities ──────────────────────────────────────────────────────────────────

def clean_text(text):
    return re.sub(r"\s+", " ", BeautifulSoup(text, "lxml").get_text()).strip()

def score_label(score, lang):
    t = T[lang]
    if score >= 0.6:   return f'<span class="score-green">🟢 {t["very_relevant"]}</span>'
    elif score >= 0.4: return f'<span class="score-yellow">🟡 {t["relevant"]}</span>'
    elif score >= 0.2: return f'<span class="score-orange">🟠 {t["not_relevant"]}</span>'
    else:              return f'<span class="score-red">🔴 {t["weakly"]}</span>'

def safe_get(d, *keys, default=""):
    try:
        r = d
        for k in keys: r = r.get(k, default)
        return r or default
    except: return default

def extract_year(date_str):
    if not date_str: return None
    try:
        if "-" in date_str: return int(date_str.split("-")[0])
        if len(date_str) == 4: return int(date_str)
    except: pass
    return None


# ── TEI extraction ─────────────────────────────────────────────────────────────

def extract_tei_metadata(root):
    """Extract title, author, date from teiHeader."""
    ns = TEI_NS
    meta = {"doc_title": "", "doc_author": "", "doc_date": "", "doc_language": ""}

    # Title
    for xpath in [
        ".//tei:teiHeader//tei:titleStmt/tei:title",
        ".//tei:title",
    ]:
        el = root.find(xpath, ns)
        if el is not None and el.text:
            meta["doc_title"] = re.sub(r"\s+", " ", el.text).strip()
            break

    # Author
    for xpath in [
        ".//tei:teiHeader//tei:titleStmt/tei:author",
        ".//tei:author",
        ".//tei:correspDesc//tei:correspAction[@type='sent']//tei:persName",
    ]:
        el = root.find(xpath, ns)
        if el is not None:
            text = re.sub(r"\s+", " ", "".join(el.itertext())).strip()
            if text:
                meta["doc_author"] = text
                break

    # Date — try @when attribute first, then text
    for xpath in [
        ".//tei:teiHeader//tei:creation/tei:date",
        ".//tei:teiHeader//tei:date[@when]",
        ".//tei:teiHeader//tei:date",
        ".//tei:correspDesc//tei:correspAction[@type='sent']/tei:date",
    ]:
        el = root.find(xpath, ns)
        if el is not None:
            date = el.get("when") or el.get("notBefore") or (el.text or "").strip()
            if date:
                meta["doc_date"] = date.strip()[:10]
                break

    # Language
    body = root.find(".//tei:text", ns)
    if body is not None:
        lang = body.get("{http://www.w3.org/XML/1998/namespace}lang", "")
        if lang: meta["doc_language"] = lang

    return meta


def extract_tei_text(root):
    """Extract clean text from TEI body."""
    ns = TEI_NS
    body = root.find(".//tei:text/tei:body", ns)
    if body is None:
        body = root.find(".//tei:text", ns)
    if body is None:
        body = root

    # Remove header elements
    for tag in body.findall(".//tei:teiHeader", ns):
        tag.getparent().remove(tag) if tag.getparent() is not None else None

    return re.sub(r"\s+", " ", "".join(body.itertext())).strip()


def process_tei_file(uploaded_file):
    """Process a single TEI-XML file. Returns (metadata, text) or (None, None)."""
    try:
        content = uploaded_file.read()
        root = etree.fromstring(content)
        meta = extract_tei_metadata(root)
        text = extract_tei_text(root)
        if not text.strip():
            return None, None
        # Add filename
        meta["file_name"] = uploaded_file.name
        return meta, text
    except Exception as e:
        st.warning(f"⚠️ Could not parse {uploaded_file.name}: {e}")
        return None, None



def process_txt_file(uploaded_file):
    """Process a plain .txt file. Uses filename as the document identifier."""
    try:
        content = uploaded_file.read()
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            text = content.decode("latin-1")
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            return None, None
        stem = Path(uploaded_file.name).stem
        meta = {
            "doc_title": stem,
            "doc_author": "",
            "doc_date": "",
            "doc_language": "",
            "file_name": uploaded_file.name,
            "file_type": "txt",
        }
        return meta, text
    except Exception as e:
        st.warning(f"⚠️ Could not read {uploaded_file.name}: {e}")
        return None, None

# ── Index building from TEI ────────────────────────────────────────────────────

def build_tei_index(files_data):
    """
    Build index from list of (metadata, text) tuples.
    Each file gets its own metadata so they can be differentiated.
    """
    Settings.embed_model = load_embed_model()
    Settings.llm = None
    splitter = SentenceSplitter(chunk_size=400, chunk_overlap=80)

    documents = []
    for meta, text in files_data:
        if not text.strip(): continue
        # Create a header label for the document
        if meta.get("file_type") == "txt":
            doc_label = Path(meta.get("file_name", "Document")).stem
        else:
            label_parts = []
            if meta.get("doc_title"): label_parts.append(meta["doc_title"])
            if meta.get("doc_author"): label_parts.append(f"by {meta['doc_author']}")
            if meta.get("doc_date"): label_parts.append(f"({meta['doc_date']})")
            doc_label = " — ".join(label_parts) if label_parts else meta.get("file_name", "Document")

        # Prepend label to text so chunks know which document they're from
        full_text = f"[Document: {doc_label}]\n\n{text}"

        doc = Document(text=full_text, metadata=dict(meta))
        doc.metadata["doc_label"] = doc_label
        documents.append(doc)

    if not documents: return None, []

    index = VectorStoreIndex.from_documents(
        documents, transformations=[splitter], show_progress=True
    )

    # Return index and list of document labels for display
    labels = [d.metadata.get("doc_label", "?") for d in documents]
    return index, labels


# ── Corpus discovery ───────────────────────────────────────────────────────────

def discover_corpora():
    result = {}
    if not CORPUS_BASE.exists(): return result
    for d in sorted(CORPUS_BASE.iterdir()):
        if not d.is_dir(): continue
        store_dir = STORE_BASE / d.name
        if not (store_dir / "docstore.json").exists(): continue
        config = {}
        cfg_path = store_dir / "corpus_config.json"
        if cfg_path.exists():
            try:
                with open(cfg_path) as f: config = json.load(f)
            except: pass
        result[d.name] = config
    return result


# ── Model loading ──────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner="⏳ Loading embedding model... (1–2 min first time)")
def load_embed_model():
    return HuggingFaceEmbedding(
        model_name=EMBEDDING_MODEL, device="cpu", trust_remote_code=True
    )

@st.cache_resource(show_spinner="⏳ Loading corpus...")
def load_corpus_index(corpus_name):
    Settings.embed_model = load_embed_model()
    Settings.llm = None
    ctx = StorageContext.from_defaults(persist_dir=str(STORE_BASE / corpus_name))
    return load_index_from_storage(ctx)


# ── LLM calls ─────────────────────────────────────────────────────────────────

def call_mistral_api(messages, temperature=0.7, max_tokens=512):
    """Call Mistral via API."""
    resp = requests.post(
        "https://api.mistral.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {MISTRAL_API_KEY}", "Content-Type": "application/json"},
        json={"model": "mistral-small-latest", "messages": messages,
              "temperature": temperature, "max_tokens": max_tokens},
        timeout=60
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def call_ollama(messages, model="qwen3:30b", temperature=0.7, max_tokens=512):
    """Call local Ollama model. Routes to correct port based on model."""
    # qwen3:30b runs on port 11435, everything else on 11434
    base_url = OLLAMA_BASE_URL_11435 if model == "qwen3:30b" else OLLAMA_BASE_URL_11434
    prompt = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in messages])
    # qwen3 reasons before answering and burns num_predict on that reasoning first;
    # too low a budget hits the token cap before it ever writes the actual answer,
    # so give it enough room regardless of the user's slider setting.
    effective_max_tokens = max(max_tokens, 1500) if model == "qwen3:30b" else max_tokens
    resp = requests.post(
        f"{base_url}/api/generate",
        json={"model": model, "prompt": prompt, "stream": False, "think": False,
              "options": {"temperature": temperature, "num_predict": effective_max_tokens}},
        timeout=300
    )
    resp.raise_for_status()
    data = resp.json()
    answer = data.get("response", "")
    # qwen3 can still emit its reasoning inline even with think=False — sometimes as a
    # full <think>...</think> pair, sometimes with only the closing tag present. Strip
    # up to and including the last closing tag either way, keeping just the final answer.
    if "</think>" in answer:
        answer = answer.rsplit("</think>", 1)[1]
    answer = answer.strip()
    return answer


def call_llm(messages, model_choice, temperature, max_tokens):
    """Route to appropriate LLM based on model choice."""
    if model_choice == "🌐 Mistral API (backup)":
        if not MISTRAL_API_KEY or MISTRAL_API_KEY == "YOUR_MISTRAL_KEY_HERE":
            return None, "API key not configured"
        try:
            return call_mistral_api(messages, temperature, max_tokens), None
        except Exception as e:
            return None, str(e)
    else:
        # Extract model name from choice
        model_map = {
            "🖥️ Qwen3 30B (local)": "qwen3:30b",
            "🖥️ Qwen2.5 7B (local, fast)": "qwen2.5:7b",
        }
        ollama_model = model_map.get(model_choice, "qwen3:30b")
        try:
            return call_ollama(messages, ollama_model, temperature, max_tokens), None
        except Exception as e:
            return None, f"Local model error: {e}"


# ── Post-retrieval filtering ───────────────────────────────────────────────────

def apply_filters(nodes, year_range=None, kw_filter=None, file_filter=None):
    filtered = []
    for node in nodes:
        meta = node.metadata
        if year_range:
            y = extract_year(safe_get(meta, "doc_date"))
            if y and not (year_range[0] <= y <= year_range[1]): continue
        if kw_filter:
            if kw_filter.lower() not in node.text.lower(): continue
        if file_filter:
            fname = safe_get(meta, "file_name", default="")
            if fname not in file_filter: continue
        filtered.append(node)
    return filtered


# ── Analytics ─────────────────────────────────────────────────────────────────

def display_analytics(nodes, lang):
    years, types, files = [], [], []
    for node in nodes:
        y = extract_year(safe_get(node.metadata, "doc_date"))
        if y: years.append(y)
        types.append(safe_get(node.metadata, "chunk_type") or "text")
        fname = safe_get(node.metadata, "file_name")
        if fname: files.append(fname)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Results" if lang == "en" else "Résultats", len(nodes))
    c2.metric("Period" if lang == "en" else "Période",
              f"{min(years)}–{max(years)}" if len(years) > 1 else (str(years[0]) if years else "N/A"))
    c3.metric("Main type" if lang == "en" else "Type principal",
              Counter(types).most_common(1)[0][0] if types else "N/A")
    c4.metric("Files" if lang == "en" else "Fichiers", len(set(files)))

    if len(set(files)) > 1:
        with st.expander("📁 " + ("Files in results" if lang == "en" else "Fichiers dans les résultats")):
            for f in sorted(set(files)):
                st.caption(f"• {f}")


# ── Build context from nodes ───────────────────────────────────────────────────

def build_context(nodes):
    """Build context string, grouping by source file for better differentiation."""
    # Group nodes by file
    by_file = {}
    for i, node in enumerate(nodes, 1):
        fname = safe_get(node.metadata, "file_name") or "Unknown"
        label = safe_get(node.metadata, "doc_label") or fname
        if label not in by_file:
            by_file[label] = {"meta": node.metadata, "passages": []}
        by_file[label]["passages"].append((i, node))

    parts = []
    for label, data in by_file.items():
        meta = data["meta"]
        header_parts = [f"Document: {label}"]
        if safe_get(meta, "doc_author"): header_parts.append(f"Author: {safe_get(meta, 'doc_author')}")
        if safe_get(meta, "doc_date"):   header_parts.append(f"Date: {safe_get(meta, 'doc_date')}")
        header = " | ".join(header_parts)
        passages = "\n".join([f"  [Source {i}]: {clean_text(node.text)[:500]}"
                               for i, node in data["passages"]])
        parts.append(f"{'='*50}\n{header}\n{passages}")

    return "\n\n".join(parts)


# ── Display results ────────────────────────────────────────────────────────────

def display_results(nodes, query, corpus_label, lang, system_prompt,
                    retrieval_only, show_analytics, expand_first,
                    model_choice, temperature, max_tokens,
                    log_enabled, run_label, annotator_note, top_k):
    t = T[lang]

    # Pedagogy box
    st.markdown(
        f'<div class="pedagogy-box">{t["pedagogy"].format(corpus=corpus_label, n=len(nodes))}</div>',
        unsafe_allow_html=True
    )

    # Analytics
    if show_analytics:
        display_analytics(nodes, lang)
        st.markdown("---")

    # LLM Answer
    if not retrieval_only:
        context = build_context(nodes[:5])
        user_msg = f"Documents:\n\n{context}\n\nQuestion: {query}\n\nPlease address each document separately if multiple documents are present."

        with st.spinner(t["generating"]):
            answer, error = call_llm(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg}
                ],
                model_choice=model_choice,
                temperature=temperature,
                max_tokens=max_tokens
            )

        if answer:
            st.markdown(f'<div class="section-header">{t["answer_title"]}</div>', unsafe_allow_html=True)
            st.markdown(answer)
        elif error:
            st.warning(f"Generation failed: {error}")

    # Sources
    st.markdown("---")
    with st.expander(
        f"📄 {t['sources_title']} ({len(nodes)} {t['passages']})",
        expanded=True
    ):
        for i, node in enumerate(nodes, 1):
            meta   = node.metadata
            score  = node.score or 0.0
            title  = safe_get(meta, "doc_title")
            fname  = safe_get(meta, "file_name")
            date   = safe_get(meta, "doc_date")
            author = safe_get(meta, "doc_author")
            chunk  = safe_get(meta, "chunk_type")
            slabel = score_label(score, lang)

            with st.expander(
                f"Source {i} — score: {score:.3f}" + (f" — {title[:45]}" if title else f" — {fname}"),
                expanded=(i == 1 and expand_first)
            ):
                c1, c2, c3, c4 = st.columns(4)
                if date:   c1.metric(t["date"], date[:10])
                if author: c2.metric(t["author"], author[:20])
                if title:  c3.metric(t["title_label"], title[:25])
                if chunk:  c4.metric(t["type"], chunk)
                if fname:  st.caption(f"📁 {fname}")
                st.markdown(slabel, unsafe_allow_html=True)
                cleaned = clean_text(node.text)
                # Remove the [Document: ...] prefix we added
                cleaned = re.sub(r'^\[Document:[^\]]+\]\s*', '', cleaned)
                st.markdown(f"> {cleaned[:700]}{'...' if len(cleaned)>700 else ''}")

    # Log
    if log_enabled and run_label:
        TESTBED_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.now().isoformat(),
            "corpus": corpus_label, "query": query,
            "model": model_choice, "system_prompt": system_prompt[:200],
            "top_k": top_k, "n_results": len(nodes),
            "run_label": run_label, "note": annotator_note,
            "top_scores": [round(n.score, 4) for n in nodes[:5]],
        }
        with open(TESTBED_LOG_PATH, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        st.info(f"✅ Logged: {run_label}")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    # Session state
    for key, val in [
        ("lang", "fr"), ("results", None), ("last_query", ""),
        ("active_index", None), ("active_corpus_label", ""),
        ("uploaded_doc_labels", []),
        ("show_info_panel", True),
        ("onboarding_seen", False),
    ]:
        if key not in st.session_state:
            st.session_state[key] = val

    lang = st.session_state.lang
    t = T[lang]

    # ── ONBOARDING MODAL (forced-read on first load) ─────────────────────────
    if not st.session_state.onboarding_seen:
        if hasattr(st, "dialog"):
            @st.dialog("👋 Bienvenue sur DH Humanistica" if lang == "fr" else "👋 Welcome to DH Humanistica")
            def _onboarding_dialog():
                if lang == "fr":
                    st.markdown("""
**1.** Choisissez un corpus existant ou téléversez vos fichiers (.xml ou .txt)
**2.** Sélectionnez votre style de réponse
**3.** Posez votre question — le système cherche par **sens**, pas par mots-clés
**4.** Lisez la réponse et consultez les sources citées

---
**Contact — Obtic**
Une question, un souci ? Écrivez à labibafarooq23@gmail.com
""")
                    close_label = "✓ J'ai lu — Fermer"
                else:
                    st.markdown("""
**1.** Choose an existing corpus or upload your files (.xml or .txt)
**2.** Select your answer style
**3.** Ask your question — the system searches by **meaning**, not keywords
**4.** Read the answer and consult the cited sources

---
**Contact — Obtic**
Questions or issues? Write to labibafarooq23@gmail.com
""")
                    close_label = "✓ I've read it — Close"
                if st.button(close_label, use_container_width=True):
                    st.session_state.onboarding_seen = True
                    st.rerun()
            _onboarding_dialog()
        else:
            # Older Streamlit without st.dialog support — skip the forced popup,
            # side info rail (show_info_panel) is shown by default instead.
            st.session_state.onboarding_seen = True

    # ── SIDEBAR (LEFT) ────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### ⚙️ Paramètres" if lang == "fr" else "### ⚙️ Settings")
        st.markdown("---")

        with st.expander("🤖 Modèle" if lang == "fr" else "🤖 Model", expanded=True):
            retrieval_only = st.checkbox(
                "Récupération uniquement (sans LLM)" if lang == "fr" else "Retrieval only (no LLM)",
                value=False
            )
            model_choice = "🖥️ Qwen2.5 7B (local, fast)"
            temperature = st.slider(
                "🌡️ Température" if lang == "fr" else "🌡️ Temperature",
                0.0, 1.0, 0.7, 0.1, disabled=retrieval_only,
                help=("Contrôle la créativité des réponses.\n• 0.0 = réponses précises et répétables\n• 0.7 = bon équilibre (recommandé)\n• 1.0 = réponses plus variées et créatives") if lang == "fr" else ("Controls response creativity.\n• 0.0 = precise and repeatable\n• 0.7 = good balance (recommended)\n• 1.0 = more varied and creative")
            )
            max_tokens = st.slider(
                "📏 Tokens max" if lang == "fr" else "📏 Max tokens",
                128, 2048, 512, 128, disabled=retrieval_only,
                help=("Longueur maximale de la réponse générée.\n• 128–512 = réponses courtes\n• 512–1024 = réponses standard\n• 1024–2048 = analyses longues et détaillées") if lang == "fr" else ("Maximum length of the generated answer.\n• 128–512 = short answers\n• 512–1024 = standard answers\n• 1024–2048 = long detailed analyses")
            )

        preset_names = list(t["presets"].keys())
        idx_preset = min(st.session_state.get("selected_preset_idx", 0), len(preset_names)-1)
        system_prompt = t["presets"][preset_names[idx_preset]]

        with st.expander("🔍 Récupération" if lang == "fr" else "🔍 Retrieval", expanded=False):
            top_k = st.slider("Top-k", 1, 20, 5,
                help=("Nombre de passages extraits du corpus pour répondre.\n• 3–5 = réponses ciblées et rapides\n• 10–15 = plus de contexte, couverture large\n• 20 = exploration maximale (plus lent)") if lang == "fr" else ("Number of passages retrieved from the corpus.\n• 3–5 = focused and fast answers\n• 10–15 = more context, broader coverage\n• 20 = maximum exploration (slower)"))
            show_analytics = st.checkbox("Afficher les analytics" if lang == "fr" else "Show analytics", value=True)
            expand_first = st.checkbox("Développer le 1er résultat" if lang == "fr" else "Expand first result", value=True)

        with st.expander("🎛️ Filtres" if lang == "fr" else "🎛️ Filters", expanded=False):
            use_year = st.checkbox("Filtrer par année" if lang == "fr" else "Filter by year",
                help=("Restreint les résultats aux documents dont la date est dans cette plage.\nUtile pour isoler une période historique précise.") if lang == "fr" else ("Restricts results to documents whose date falls in this range.\nUseful for isolating a specific historical period."))
            year_range = None
            if use_year:
                year_range = st.slider("Période" if lang == "fr" else "Year range", 1000, 2024, (1800, 1950))
            kw_filter = st.text_input(
                "Mot-clé dans le texte" if lang == "fr" else "Keyword in text",
                placeholder="e.g. guerre, médecine...",
                help=("Garde uniquement les passages qui contiennent ce mot.\nAttention : insensible à la casse mais sensible aux accents.") if lang == "fr" else ("Keeps only passages that contain this word.\nNote: case-insensitive but accent-sensitive.")
            ).strip() or None
            file_filter = None
            if len(st.session_state.uploaded_doc_labels) > 1:
                st.markdown("**Filtrer par document :**" if lang == "fr" else "**Filter by document:**")
                selected_files = st.multiselect(
                    "Documents",
                    options=st.session_state.uploaded_doc_labels,
                    default=st.session_state.uploaded_doc_labels,
                    help="Interrogez uniquement les documents sélectionnés." if lang == "fr" else "Query only selected documents."
                )
                if selected_files and len(selected_files) < len(st.session_state.uploaded_doc_labels):
                    file_filter = selected_files

        with st.expander("🖥️ Système" if lang == "fr" else "🖥️ System", expanded=False):
            try:
                import torch
                if torch.cuda.is_available():
                    props = torch.cuda.get_device_properties(0)
                    used = torch.cuda.memory_allocated(0) / 1e9
                    total = props.total_memory / 1e9
                    st.metric("GPU", f"{used:.1f}/{total:.1f} GB")
                else:
                    st.info("Mode CPU" if lang == "fr" else "CPU mode")
            except:
                st.info("Mode CPU" if lang == "fr" else "CPU mode")

        run_label = ""
        annotator_note = ""
        log_enabled = False

    # ── MAIN PAGE ─────────────────────────────────────────────────────────────
    col_lang_spacer, col_lang = st.columns([6, 1])
    with col_lang:
        flag = "🇬🇧 EN" if lang == "fr" else "🇫🇷 FR"
        if st.button(flag, use_container_width=True):
            st.session_state.lang = "en" if lang == "fr" else "fr"
            st.rerun()

    show_panel = st.session_state.show_info_panel
    col_widths = [3, 1] if show_panel else [1]
    cols = st.columns(col_widths)
    col_main = cols[0]
    col_info = cols[1] if show_panel else None

    # ── RIGHT INFO PANEL ──────────────────────────────────────────────────────
    if show_panel and col_info is not None:
        with col_info:
            # Close button at top
            close_lbl = "✕ Fermer le guide" if lang == "fr" else "✕ Close guide"
            if st.button(close_lbl, key="close_panel", use_container_width=True):
                st.session_state.show_info_panel = False
                st.rerun()
            if lang == "fr":
                st.markdown("""
<div style='background:linear-gradient(135deg,#161b27,#1a2035);border:1px solid #252d3d;border-left:4px solid #c9a96e;border-radius:10px;padding:1.1rem 1rem;font-size:0.82rem;color:#b8c5d6;line-height:1.7;'>
<div style='font-family:Playfair Display,serif;color:#c9a96e;font-size:1rem;font-weight:700;margin-bottom:0.6rem;'>ℹ️ Comment ça marche</div>
<b>1.</b> Choisissez un corpus existant ou téléversez vos fichiers (.xml ou .txt)<br>
<b>2.</b> Sélectionnez votre style de réponse<br>
<b>3.</b> Posez votre question — le système cherche par <b>sens</b>, pas par mots-clés<br>
<b>4.</b> Lisez la réponse et consultez les sources citées
<hr style='border-color:#2d3547;margin:0.8rem 0;'>
<div style='color:#c9a96e;font-weight:700;margin-bottom:0.4rem;'>🎯 Styles de réponse</div>
<b>🎓 Réponse générale</b><br><span style='color:#8892a4;'>Réponse claire, idéale pour explorer le corpus.</span><br><br>
<b>🏛️ Analyse historique</b><br><span style='color:#8892a4;'>Analyse rigoureuse avec contexte et citations.</span><br><br>
<b>📝 Résumé court</b><br><span style='color:#8892a4;'>3-4 phrases concises — pour des questions rapides.</span>
<hr style='border-color:#2d3547;margin:0.8rem 0;'>
<div style='color:#c9a96e;font-weight:700;margin-bottom:0.4rem;'>🎯 Scores de pertinence</div>
🟢 <b>&gt; 0.6</b> — Très pertinent<br>
🟡 <b>0.4–0.6</b> — Pertinent<br>
🟠 <b>0.2–0.4</b> — Peu pertinent<br>
🔴 <b>&lt; 0.2</b> — Faiblement lié
<hr style='border-color:#2d3547;margin:0.8rem 0;'>
<div style='color:#c9a96e;font-weight:700;margin-bottom:0.4rem;'>📁 Formats acceptés</div>
<b>TEI-XML (.xml)</b> — titre, auteur, date extraits auto.<br><br>
<b>Texte brut (.txt)</b> — le nom du fichier sert d'identifiant.
<hr style='border-color:#2d3547;margin:0.8rem 0;'>
<div style='color:#8892a4;font-size:0.78rem;'>Le système compare votre question aux passages du corpus par <i>similarité sémantique</i>, pas par mots exacts.</div>
<hr style='border-color:#2d3547;margin:0.8rem 0;'>
<div style='color:#c9a96e;font-weight:700;margin-bottom:0.4rem;'>📬 Contact — Obtic</div>
<div style='color:#8892a4;font-size:0.78rem;'>Une question, un souci ? Écrivez à labibafarooq23@gmail.com</div>
</div>""", unsafe_allow_html=True)
            else:
                st.markdown("""
<div style='background:linear-gradient(135deg,#161b27,#1a2035);border:1px solid #252d3d;border-left:4px solid #c9a96e;border-radius:10px;padding:1.1rem 1rem;font-size:0.82rem;color:#b8c5d6;line-height:1.7;'>
<div style='font-family:Playfair Display,serif;color:#c9a96e;font-size:1rem;font-weight:700;margin-bottom:0.6rem;'>ℹ️ How it works</div>
<b>1.</b> Choose an existing corpus or upload your files (.xml or .txt)<br>
<b>2.</b> Select your answer style<br>
<b>3.</b> Ask your question — the system searches by <b>meaning</b>, not keywords<br>
<b>4.</b> Read the answer and consult the cited sources
<hr style='border-color:#2d3547;margin:0.8rem 0;'>
<div style='color:#c9a96e;font-weight:700;margin-bottom:0.4rem;'>🎯 Answer styles</div>
<b>🎓 General answer</b><br><span style='color:#8892a4;'>Clear answer, ideal for exploring the corpus.</span><br><br>
<b>🏛️ Historical analysis</b><br><span style='color:#8892a4;'>Rigorous analysis with context and citations.</span><br><br>
<b>📝 Short summary</b><br><span style='color:#8892a4;'>3-4 concise sentences — for quick factual questions.</span>
<hr style='border-color:#2d3547;margin:0.8rem 0;'>
<div style='color:#c9a96e;font-weight:700;margin-bottom:0.4rem;'>🎯 Relevance scores</div>
🟢 <b>&gt; 0.6</b> — Very relevant<br>
🟡 <b>0.4–0.6</b> — Relevant<br>
🟠 <b>0.2–0.4</b> — Not relevant<br>
🔴 <b>&lt; 0.2</b> — Weakly linked
<hr style='border-color:#2d3547;margin:0.8rem 0;'>
<div style='color:#c9a96e;font-weight:700;margin-bottom:0.4rem;'>📁 Accepted formats</div>
<b>TEI-XML (.xml)</b> — title, author, date extracted automatically.<br><br>
<b>Plain text (.txt)</b> — filename used as document identifier.
<hr style='border-color:#2d3547;margin:0.8rem 0;'>
<div style='color:#8892a4;font-size:0.78rem;'>The system compares your question to corpus passages by <i>semantic similarity</i>, not exact words.</div>
<hr style='border-color:#2d3547;margin:0.8rem 0;'>
<div style='color:#c9a96e;font-weight:700;margin-bottom:0.4rem;'>📬 Contact — Obtic</div>
<div style='color:#8892a4;font-size:0.78rem;'>Questions or issues? Write to labibafarooq23@gmail.com</div>
</div>""", unsafe_allow_html=True)

    # ── MAIN CONTENT COLUMN ───────────────────────────────────────────────────
    with col_main:
        st.markdown('<div class="ask-labiba-title">🤖 DH Humanistica</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="ask-labiba-subtitle">{t["subtitle"]}</div>', unsafe_allow_html=True)

        if not show_panel:
            open_lbl = "📖 Ouvrir le guide" if lang == "fr" else "📖 Open guide"
            if st.button(open_lbl, key="open_panel"):
                st.session_state.show_info_panel = True
                st.rerun()

        preset_label_main = "🎯 Choisissez votre style de réponse :" if lang == "fr" else "🎯 Choose your answer style:"
        st.markdown(f"<p style='color:#8892a4;font-size:0.85rem;margin-bottom:0.5rem;'>{preset_label_main}</p>", unsafe_allow_html=True)

        preset_data = {
            "fr": [
                ("🎓", "Réponse générale", "Réponse claire et accessible basée sur les sources"),
                ("🏛️", "Analyse historique", "Analyse rigoureuse avec contexte historique et citations"),
                ("📝", "Résumé court", "Réponse en 3-4 phrases, concise et directe"),
            ],
            "en": [
                ("🎓", "General answer", "Clear and accessible answer based on the sources"),
                ("🏛️", "Historical analysis", "Rigorous analysis with historical context and citations"),
                ("📝", "Short summary", "Answer in 3-4 sentences, concise and direct"),
            ]
        }

        if "selected_preset_idx" not in st.session_state:
            st.session_state.selected_preset_idx = 0

        pc1, pc2, pc3 = st.columns(3)
        for card_idx, (card_col, (icon, title, desc)) in enumerate(zip([pc1, pc2, pc3], preset_data[lang])):
            is_selected = st.session_state.selected_preset_idx == card_idx
            border_color = "#c9a96e" if is_selected else "#252d3d"
            with card_col:
                st.markdown(
                    f'''<div class="info-card" style="border-color:{border_color};cursor:pointer;">
                    <div class="card-icon">{icon}</div>
                    <div class="card-title">{title}</div>
                    <div class="card-text">{desc}</div>
                    </div>''',
                    unsafe_allow_html=True
                )
                if st.button(
                    "✓ Selected" if is_selected else "Select",
                    key=f"preset_card_{card_idx}",
                    use_container_width=True,
                    type="primary" if is_selected else "secondary"
                ):
                    st.session_state.selected_preset_idx = card_idx
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        tab1, tab2 = st.tabs([t["tab1"], t["tab2"]])

        with tab1:
            corpora = discover_corpora()
            if not corpora:
                st.warning(t["no_corpus"])
            else:
                names = list(corpora.keys())
                placeholder = "— Sélectionnez —" if lang == "fr" else "— Select —"
                selected = st.selectbox(
                    "📚 " + ("Choisissez un corpus" if lang == "fr" else "Choose a corpus"),
                    options=[placeholder] + names
                )
                if selected and selected not in ["— Sélectionnez —", "— Select —"]:
                    cfg = corpora[selected]
                    st.markdown(
                        f'<div class="corpus-banner">✓ {selected} — '
                        f'{cfg.get("total_chunks","?")} chunks · '
                        f'doc_type: {cfg.get("doc_type","?")} · '
                        f'{cfg.get("total_files","?")} files</div>',
                        unsafe_allow_html=True
                    )
                    if st.button(t["use_corpus"], type="primary", use_container_width=True):
                        try:
                            loaded_idx = load_corpus_index(selected)
                            st.session_state.active_index = loaded_idx
                            st.session_state.active_corpus_label = selected
                            st.session_state.uploaded_doc_labels = []
                            st.session_state.results = None
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

        with tab2:
            st.markdown(f'<div class="info-box">{t["upload_info"]}</div>', unsafe_allow_html=True)
            uploaded = st.file_uploader(
                "TEI-XML or plain text files",
                type=["xml", "txt"],
                accept_multiple_files=True,
                help="TEI-XML (.xml) or plain text (.txt) files accepted"
            )
            corpus_name = st.text_input(t["corpus_name_label"], value="Mon corpus")

            if uploaded:
                xml_files = [f for f in uploaded if f.name.endswith(".xml")]
                txt_files = [f for f in uploaded if f.name.endswith(".txt")]
                summary = f"{len(uploaded)} fichier(s)" if lang == "fr" else f"{len(uploaded)} file(s)"
                if xml_files and txt_files:
                    summary += f" — {len(xml_files)} TEI-XML, {len(txt_files)} TXT"
                st.info(summary + " : " + ", ".join(f.name for f in uploaded))

                if st.button(t["index_btn"], type="primary", use_container_width=True):
                    files_data = []
                    doc_labels = []
                    prog = st.progress(0, text=t["indexing"])
                    for i, f in enumerate(uploaded):
                        prog.progress(int(i / len(uploaded) * 50), text=f"Extracting: {f.name}")
                        if f.name.endswith(".txt"):
                            meta, text = process_txt_file(f)
                            if meta and text:
                                files_data.append((meta, text))
                                label = Path(f.name).stem
                                doc_labels.append(label)
                                st.success(f"✅ **{f.name}** — identifié comme : «{label}»" if lang == "fr" else f"✅ **{f.name}** — identified as: «{label}»")
                            else:
                                st.warning(f"⚠️ Rien extrait de {f.name}" if lang == "fr" else f"⚠️ Nothing extracted from {f.name}")
                        else:
                            meta, text = process_tei_file(f)
                            if meta and text:
                                files_data.append((meta, text))
                                label = meta.get("doc_label") or meta.get("doc_title") or f.name
                                doc_labels.append(label)
                                st.success(
                                    f"✅ **{f.name}** — Titre: {meta.get('doc_title','?')} · Auteur: {meta.get('doc_author','?')} · Date: {meta.get('doc_date','?')}"
                                    if lang == "fr" else
                                    f"✅ **{f.name}** — Title: {meta.get('doc_title','?')} · Author: {meta.get('doc_author','?')} · Date: {meta.get('doc_date','?')}"
                                )
                            else:
                                st.warning(f"⚠️ Rien extrait de {f.name}" if lang == "fr" else f"⚠️ Nothing extracted from {f.name}")

                    if files_data:
                        prog.progress(60, text=t["indexing"])
                        try:
                            built_idx, labels = build_tei_index(files_data)
                            if built_idx:
                                prog.progress(100, text="✅ Index créé !" if lang == "fr" else "✅ Index created!")
                                st.session_state.active_index = built_idx
                                st.session_state.active_corpus_label = corpus_name or "Mon corpus"
                                st.session_state.uploaded_doc_labels = doc_labels
                                st.session_state.results = None
                                st.rerun()
                        except Exception as e:
                            st.error(f"Erreur d'indexation : {e}" if lang == "fr" else f"Indexing error: {e}")
                    else:
                        st.error(t["no_text"])

        st.markdown("---")

        if not st.session_state.active_index:
            st.markdown(f'<div class="info-box">👆 {t["choose"]}</div>', unsafe_allow_html=True)
        else:
            corpus_label = st.session_state.active_corpus_label
            st.markdown(f'<div class="section-header">{t["search_title"]} {corpus_label}</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="score-legend">'
                '<span>🟢 > 0.6 Très pertinent</span><span>🟡 0.4–0.6 Pertinent</span>'
                '<span>🟠 0.2–0.4 Modéré</span><span>🔴 < 0.2 Faible</span></div>'
                if lang == "fr" else
                '<div class="score-legend">'
                '<span>🟢 > 0.6 Very relevant</span><span>🟡 0.4–0.6 Relevant</span>'
                '<span>🟠 0.2–0.4 Moderate</span><span>🔴 < 0.2 Weak</span></div>',
                unsafe_allow_html=True
            )

            if len(st.session_state.uploaded_doc_labels) > 1:
                label_header = "📁 <strong>Documents dans ce corpus :</strong>" if lang == "fr" else "📁 <strong>Documents in this corpus:</strong>"
                st.markdown(
                    f'<div class="info-box">{label_header}<br>' +
                    "<br>".join(f"• {l}" for l in st.session_state.uploaded_doc_labels) + "</div>",
                    unsafe_allow_html=True
                )

            preset_names2 = list(t["presets"].keys())
            p_idx = min(st.session_state.get("selected_preset_idx", 0), len(preset_names2) - 1)
            final_system_prompt = t["presets"][preset_names2[p_idx]]

            st.markdown(f"**{t['examples_label']}**")
            ex_keys = ["ex1", "ex2", "ex3", "ex4", "ex5"]
            ex_cols = st.columns(2)
            for i, key in enumerate(ex_keys):
                if ex_cols[i % 2].button(t[key], key=f"ex_{key}", use_container_width=True):
                    st.session_state.last_query = t[key]

            query = st.text_input(
                "Question",
                value=st.session_state.last_query,
                placeholder=t["placeholder"],
                label_visibility="collapsed"
            )
            search = st.button(t["search_btn"], type="primary", use_container_width=True)

            if search and query.strip():
                st.session_state.last_query = query
                with st.spinner("Searching..." if lang == "en" else "Recherche..."):
                    try:
                        retriever = st.session_state.active_index.as_retriever(similarity_top_k=top_k)
                        nodes = retriever.retrieve(query)
                        nodes = apply_filters(nodes, year_range=year_range, kw_filter=kw_filter, file_filter=file_filter)
                        st.session_state.results = {
                            "query": query, "nodes": nodes, "corpus": corpus_label,
                            "system_prompt": final_system_prompt,
                            "model_choice": model_choice,
                            "temperature": temperature, "max_tokens": max_tokens,
                        }
                    except Exception as e:
                        st.error(f"Search error: {e}")
            elif search:
                st.warning("Please enter a question." if lang == "en" else "Veuillez entrer une question.")

            if st.session_state.results:
                r = st.session_state.results
                display_results(
                    r["nodes"], r["query"], r["corpus"], lang,
                    r["system_prompt"], retrieval_only, show_analytics,
                    expand_first, r.get("model_choice", model_choice),
                    r.get("temperature", 0.7), r.get("max_tokens", 512),
                    log_enabled, run_label, annotator_note, top_k
                )


if __name__ == "__main__":
    main()
