"""
Vercel Serverless Function (Python)
POST /api/ask
입력: { typeName, typeCode, typeDesc, question }
출력: { answer: "질문에 대한 2~3문장 답변", provider: "gemini" | "groq" }

결과 화면의 'AI에게 더 물어보기' 기능에서 사용됩니다.
사용자가 자신의 성향 유형에 대해 자유롭게 질문하면,
해당 유형 정보를 맥락으로 넣어 답변합니다.

Gemini를 우선 사용하고, 무료 할당량 초과(429) 등으로 실패하면
Groq(GROQ_API_KEY가 설정된 경우)으로 자동 전환합니다.
"""

import json
import os
from http.server import BaseHTTPRequestHandler

import requests

GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)

GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

MAX_QUESTION_LENGTH = 200


def build_prompt(type_name, type_code, type_desc, question):
    return f"""당신은 성향 테스트 결과를 바탕으로 친근하게 답변해주는 상담사입니다.

사용자의 성향 유형: {type_name} ({type_code})
이 유형의 특징: {type_desc}

사용자의 질문: {question}

위 유형 정보를 바탕으로 사용자의 질문에 답변해주세요.
- 2~3문장, 150자 내외로 간결하게
- 친한 친구가 답해주는 듯한 편안한 말투
- 유형과 관련 없는 질문이면, 유형 설명과 자연스럽게 연결해서 답하거나 정중히 답하기 어렵다고 안내
- 따옴표, 마크다운 기호 없이 본문 텍스트만 출력
"""


def call_gemini(prompt, api_key):
    try:
        resp = requests.post(
            GEMINI_URL,
            params={"key": api_key},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.8,
                    "maxOutputTokens": 400,
                    "thinkingConfig": {"thinkingBudget": 0},
                },
            },
            timeout=12,
        )
    except requests.exceptions.Timeout:
        return None, {"status": 504, "error": "Gemini 응답 지연(타임아웃)"}
    except requests.exceptions.RequestException as e:
        return None, {"status": 502, "error": f"Gemini 호출 오류: {e}"}

    if resp.status_code != 200:
        return None, {"status": resp.status_code, "error": f"Gemini API 오류: {resp.status_code}"}

    try:
        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        return text, None
    except (KeyError, IndexError, ValueError):
        return None, {"status": 502, "error": "Gemini 응답 해석 실패"}


def call_groq(prompt, api_key):
    try:
        resp = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": GROQ_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.8,
                "max_tokens": 400,
            },
            timeout=12,
        )
    except requests.exceptions.Timeout:
        return None, {"status": 504, "error": "Groq 응답 지연(타임아웃)"}
    except requests.exceptions.RequestException as e:
        return None, {"status": 502, "error": f"Groq 호출 오류: {e}"}

    if resp.status_code != 200:
        return None, {"status": resp.status_code, "error": f"Groq API 오류: {resp.status_code}"}

    try:
        data = resp.json()
        text = data["choices"][0]["message"]["content"].strip()
        return text, None
    except (KeyError, IndexError, ValueError):
        return None, {"status": 502, "error": "Groq 응답 해석 실패"}


def generate_answer(prompt):
    gemini_key = os.environ.get("GEMINI_API_KEY")
    groq_key = os.environ.get("GROQ_API_KEY")

    if gemini_key:
        text, err = call_gemini(prompt, gemini_key)
        if text:
            return text, "gemini"
        print(f"[fallback] Gemini 실패({err}), Groq으로 전환 시도")
    else:
        err = {"status": 500, "error": "GEMINI_API_KEY가 설정되지 않았습니다."}

    if groq_key:
        text, groq_err = call_groq(prompt, groq_key)
        if text:
            return text, "groq"
        return None, groq_err

    return None, err


class handler(BaseHTTPRequestHandler):
    def _send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if not os.environ.get("GEMINI_API_KEY") and not os.environ.get("GROQ_API_KEY"):
            self._send_json(500, {"error": "GEMINI_API_KEY 또는 GROQ_API_KEY 중 하나 이상이 설정되어야 합니다."})
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length > 0 else b"{}"
            body = json.loads(raw or b"{}")
        except (ValueError, json.JSONDecodeError):
            self._send_json(400, {"error": "잘못된 요청 본문입니다."})
            return

        type_name = body.get("typeName", "")
        type_code = body.get("typeCode", "")
        type_desc = body.get("typeDesc", "")
        question = (body.get("question") or "").strip()

        if not question:
            self._send_json(400, {"error": "질문을 입력해주세요."})
            return
        if len(question) > MAX_QUESTION_LENGTH:
            self._send_json(400, {"error": f"질문은 {MAX_QUESTION_LENGTH}자 이내로 입력해주세요."})
            return
        if not type_name or not type_code:
            self._send_json(400, {"error": "typeName과 typeCode는 필수입니다."})
            return

        prompt = build_prompt(type_name, type_code, type_desc, question)
        answer, result = generate_answer(prompt)

        if answer is None:
            self._send_json(result.get("status", 502), {"error": result.get("error", "AI 호출 실패")})
            return

        self._send_json(200, {"answer": answer, "provider": result})

    def do_GET(self):
        self._send_json(405, {"error": "POST 요청만 지원합니다."})