"""Vocabulary table app — tiny local server.

Run:  python3 server.py   then open http://localhost:8000
Your words are saved in words.json next to this file.
Auto-fill uses Claude, so set ANTHROPIC_API_KEY before starting.
"""
import json
import os
import re
import threading
import uuid
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import anthropic

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(HERE, "words.json")
PORT = int(os.environ.get("PORT", 8000))
FIELDS = ["word", "phonetic", "pos", "meaning_vi", "meaning_en", "sentence",
          "collocations", "synonyms", "example", "notes"]
LOCK = threading.Lock()
MODEL = "claude-opus-5-5"


# ---------- storage ----------
def load_words():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_words(words):
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA_FILE)


# ---------- auto-fill with Claude ----------
SYSTEM = """You are an English-Vietnamese dictionary for a Vietnamese learner of English.
You get an English word and a sentence that uses it. Work out the ONE sense the word has in
that sentence and describe only that sense. Never list other meanings of the word.
Fields:
- phonetic: IPA of the word (US), e.g. /bæŋk/
- pos: part of speech in this sentence, in Vietnamese (danh từ, động từ, tính từ, trạng từ, giới từ, cụm động từ, thành ngữ...)
- meaning_vi: short, natural Vietnamese meaning for this sense only
- meaning_en: short English learner's-dictionary definition of this sense only
- collocations: 3-5 common collocations for this sense, separated by "; "
- synonyms: up to 4 English synonyms for this sense, separated by ", " (empty if none)
- example: one new, simple English example sentence using the word in the same sense
If no sentence is given, use the most common sense."""

SCHEMA = {
    "type": "object",
    "properties": {k: {"type": "string"} for k in
                   ["phonetic", "pos", "meaning_vi", "meaning_en", "collocations", "synonyms", "example"]},
    "required": ["phonetic", "pos", "meaning_vi", "meaning_en", "collocations", "synonyms", "example"],
    "additionalProperties": False,
}

_client = None


def lookup(word, sentence):
    """Ask Claude for the meaning of `word` as used in `sentence`. Returns a dict of fields."""
    global _client
    _client = _client or anthropic.Anthropic()
    response = _client.beta.messages.create(
        model=MODEL,
        max_tokens=4000,
        system=SYSTEM,
        messages=[{"role": "user", "content": f"Word: {word}\nSentence: {sentence or '(none)'}"}],
        output_config={"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}},
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    )
    if response.stop_reason == "refusal":
        raise RuntimeError("Claude từ chối tra từ này.")
    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)


def lookup_error_message(e):
    if isinstance(e, anthropic.AuthenticationError) or "api_key" in str(e).lower() or "auth" in str(e).lower():
        return "Chưa có hoặc sai khóa API (ANTHROPIC_API_KEY). Xem hướng dẫn trong README."
    if isinstance(e, anthropic.RateLimitError):
        return "Đã gửi quá nhiều yêu cầu, hãy thử lại sau ít phút."
    if isinstance(e, anthropic.APIConnectionError):
        return "Không kết nối được Internet."
    return f"Không tra được từ: {e}"


# ---------- HTTP ----------
class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=os.path.join(HERE, "static"), **kw)

    def send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}")

    def row_id(self):
        m = re.fullmatch(r"/api/words/([\w-]+)", self.path)
        return m.group(1) if m else None

    def do_GET(self):
        if self.path == "/api/words":
            with LOCK:
                return self.send_json(load_words())
        return super().do_GET()

    def do_POST(self):
        if self.path != "/api/words":
            return self.send_json({"error": "not found"}, 404)
        data = self.read_json()
        word = str(data.get("word") or "").strip()
        sentence = str(data.get("sentence") or "").strip()
        if not word:
            return self.send_json({"error": "Hãy nhập một từ."}, 400)
        try:
            filled = lookup(word, sentence)
        except Exception as e:
            return self.send_json({"error": lookup_error_message(e)}, 502)
        row = {f: str(filled.get(f) or "").strip() for f in FIELDS}
        row.update({"id": uuid.uuid4().hex[:12], "word": word, "sentence": sentence})
        with LOCK:
            words = load_words()
            words.insert(0, row)
            save_words(words)
        self.send_json(row, 201)

    def do_PUT(self):
        rid = self.row_id()
        data = self.read_json()
        with LOCK:
            words = load_words()
            for row in words:
                if row["id"] == rid:
                    row.update({k: str(v) for k, v in data.items() if k in FIELDS})
                    save_words(words)
                    return self.send_json(row)
        self.send_json({"error": "not found"}, 404)

    def do_DELETE(self):
        rid = self.row_id()
        with LOCK:
            words = load_words()
            save_words([r for r in words if r["id"] != rid])
        self.send_json({"ok": True})

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Cảnh báo: chưa đặt ANTHROPIC_API_KEY — ứng dụng sẽ không tự điền được.")
    print(f"Ứng dụng đang chạy tại http://localhost:{PORT}  (nhấn Ctrl+C để dừng)")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
