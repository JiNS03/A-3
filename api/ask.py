"""
Vercel Serverless Function (Python)
POST /api/ask
입력: { typeName, typeCode, typeDesc, question }
출력: { answer: "질문에 대한 2~3문장 답변" }

결과 화면의 'AI에게 더 물어보기' 기능에서 사용됩니다.
사용자가 자신의 성향 유형에 대해 자유롭게 질문하면,
해당 유형 정보를 맥락으로 넣어 Gemini가 답변합니다.
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


class handler(BaseHTTPRequestHandler):
    def _send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            self._send_json(500, {"error": "GEMINI_API_KEY가 설정되지 않았습니다."})
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

        # 실패 처리: 빈 입력
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
            self._send_json(504, {"error": "AI 응답이 지연되고 있습니다. 잠시 후 다시 시도해주세요."})
            return
        except requests.exceptions.RequestException as e:
            self._send_json(502, {"error": f"AI 호출 중 오류가 발생했습니다: {e}"})
            return

        if resp.status_code != 200:
            self._send_json(
                resp.status_code,
                {"error": f"Gemini API 오류: {resp.status_code}", "detail": resp.text[:300]},
            )
            return

        try:
            data = resp.json()
            answer = (
                data["candidates"][0]["content"]["parts"][0]["text"].strip()
            )
        except (KeyError, IndexError, ValueError):
            self._send_json(502, {"error": "AI 응답을 해석하지 못했습니다."})
            return

        self._send_json(200, {"answer": answer})

    def do_GET(self):
        self._send_json(405, {"error": "POST 요청만 지원합니다."})
