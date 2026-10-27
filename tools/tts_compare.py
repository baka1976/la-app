#!/usr/bin/env python3
"""예문(LASENT1 JSON)을 Google Cloud Text-to-Speech의 일본어 음성 여러 개로 읽혀 비교 페이지(HTML 한 파일)를 만든다.

  GOOGLE_TTS_API_KEY=... python3 tools/tts_compare.py 예문.json 비교.html

- API 키는 환경 변수로만 받는다(파일·저장소에 두지 않는다).
- 목표 단어(hit)는 SSML <sub alias="가나">로 읽기를 고정한다(身を「しん」으로 읽는 식의 오독 방지).
  SSML을 받지 않는 Chirp 계열은 가나 문장(kana)을 그대로 읽힌다.
- 음성은 등급(Standard·Wavenet·Neural2·Chirp-HD·Chirp3-HD)마다 하나씩 고르고, --voices로 직접 지정할 수 있다.
- 결과 HTML에는 음성이 data URI로 들어간다. 예문은 개인 학습 자료이므로 공개 저장소에 올리지 않는다.
"""
import argparse, base64, html, json, os, sys, urllib.request

API = "https://texttospeech.googleapis.com/v1"


def call(path, body=None):
    key = os.environ.get("GOOGLE_TTS_API_KEY")
    if not key:
        sys.exit("GOOGLE_TTS_API_KEY 환경 변수가 없습니다.")
    req = urllib.request.Request(f"{API}/{path}{'&' if '?' in path else '?'}key={key}",
                                 data=json.dumps(body).encode() if body else None,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"API 오류 {e.code}: {e.read().decode()[:400]}")


def pick_voices():
    vs = sorted(v["name"] for v in call("voices?languageCode=ja-JP")["voices"])
    out = []
    for tier in ("Standard", "Wavenet", "Neural2", "Chirp-HD", "Chirp3-HD"):
        names = [n for n in vs if f"-{tier}-" in n]
        if names:
            out.append(names[0])
    return out


def ssml(t):
    ja = html.escape(t["ja"])
    hit = html.escape(t["hit"])
    return "<speak>" + ja.replace(hit, f'<sub alias="{html.escape(t["hit_kana"])}">{hit}</sub>', 1) + "</speak>"


def synth(voice, t):
    chirp = "Chirp" in voice
    inp = {"text": t["kana"]} if chirp else {"ssml": ssml(t)}
    r = call("text:synthesize", {"input": inp,
                                 "voice": {"languageCode": "ja-JP", "name": voice},
                                 "audioConfig": {"audioEncoding": "MP3"}})
    return r["audioContent"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--voices", help="쉼표로 구분한 음성 이름 (생략하면 등급마다 하나씩)")
    a = ap.parse_args()
    d = json.load(open(a.src, encoding="utf-8"))
    voices = a.voices.split(",") if a.voices else pick_voices()
    rows = []
    for s in d["sets"]:
        for t in s["sents"]:
            cells = []
            for v in voices:
                b64 = synth(v, t)
                cells.append(f'<td><audio controls preload="none" src="data:audio/mpeg;base64,{b64}"></audio></td>')
            rows.append(f'<tr><td lang="ja">{html.escape(t["ja"])}<br><small>{html.escape(t.get("ko", ""))}</small></td>{"".join(cells)}</tr>')
            print(".", end="", flush=True)
    head = "".join(f"<th>{html.escape(v)}</th>" for v in voices)
    page = f"""<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>음성 비교</title><style>body{{font-family:sans-serif;margin:16px;background:#fff;color:#111}}table{{border-collapse:collapse}}td,th{{border:1px solid #ccc;padding:6px;vertical-align:top}}audio{{width:160px}}.w{{overflow-x:auto}}</style>
<h1>음성 비교 (Google Cloud TTS)</h1><p>같은 문장을 음성별로 듣고 가장 자연스러운 음성을 고르세요. 목표 단어의 억양은 사전(OJAD·NHK)과 따로 대조합니다.</p>
<div class="w"><table><tr><th>문장</th>{head}</tr>{''.join(rows)}</table></div>"""
    open(a.out, "w", encoding="utf-8").write(page)
    print(f"\n{a.out} ({len(voices)}개 음성 × {len(rows)}문장)")


if __name__ == "__main__":
    main()
