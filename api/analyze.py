"""
Vercel Serverless Function (Python)
POST /api/analyze
입력: { typeName, typeCode, typeDesc, answersText }
출력: { comment: "AI가 생성한 2~3문장 개인화 코멘트" }

Gemini API 키는 반드시 환경 변수(GEMINI_API_KEY)로 관리합니다.
로컬 개발 시 .env 파일 등을 사용하고, Vercel 배포 시에는
프로젝트 Settings > Environment Variables 에 등록하세요.
"""

import json
import os
from http.server import BaseHTTPRequestHandler

import requests

GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)


def build_prompt(type_name, type_code, type_desc, answers_text):
    return f"""당신은 성향 테스트 결과를 재미있고 따뜻하게 설명해주는 카피라이터입니다.

사용자의 성향 유형: {type_name} ({type_code})
이 유형의 특징: {type_desc}

사용자의 답변 내역:
{answers_text}

위 내용을 참고해서 이 사람만을 위한 개인화된 한마디를 작성해주세요.
- 2~3문장으로 작성
- 형식적이지 않고, 친한 친구가 다정하게 얘기해주는 듯한 말투
- 마지막 문장은 오늘 하루를 위한 짧은 응원이나 조언으로 마무리
- 다른 설명, 따옴표, 마크다운 기호 없이 본문 텍스트만 출력
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
        answers_text = body.get("answersText", "")

        if not type_name or not type_code:
            self._send_json(400, {"error": "typeName과 typeCode는 필수입니다."})
            return

        prompt = build_prompt(type_name, type_code, type_desc, answers_text)

        try:
            resp = requests.post(
                GEMINI_URL,
                params={"key": api_key},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.9,
                        "maxOutputTokens": 200,
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
            comment = (
                data["candidates"][0]["content"]["parts"][0]["text"].strip()
            )
        except (KeyError, IndexError, ValueError):
            self._send_json(502, {"error": "AI 응답을 해석하지 못했습니다."})
            return

        self._send_json(200, {"comment": comment})

    def do_GET(self):
        self._send_json(405, {"error": "POST 요청만 지원합니다."})
