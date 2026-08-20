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

GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)

# Groq은 Gemini 무료 할당량이 소진(429)되었을 때 자동으로 넘어가는 백업 provider입니다.
# GROQ_API_KEY가 설정되어 있지 않으면 이 fallback은 자동으로 건너뜁니다.
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def call_gemini(prompt, api_key):
    """Gemini API 호출. 성공 시 (text, None) 실패 시 (None, 에러정보) 반환."""
    try:
        resp = requests.post(
            GEMINI_URL,
            params={"key": api_key},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.9,
                    "maxOutputTokens": 700,
                    # gemini-2.5-flash는 기본적으로 내부 사고(thinking)에 토큰을 먼저 소모합니다.
                    # thinkingBudget을 0으로 두면 바로 답변 생성에 토큰을 사용해 잘림을 방지합니다.
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
    """Groq API 호출 (Gemini 실패 시 백업). 성공 시 (text, None) 실패 시 (None, 에러정보) 반환."""
    try:
        resp = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": GROQ_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.9,
                "max_tokens": 700,
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


def generate_comment(prompt):
    """Gemini를 우선 시도하고, 실패하면 Groq으로 자동 전환합니다.
    성공 시 (text, provider) 실패 시 (None, 에러정보) 반환."""
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

    # Groq 키도 없으면 원래 Gemini 에러를 그대로 반환
    return None, err


def build_prompt(type_name, type_code, type_desc, answers_text):
    return f"""당신은 성향 테스트 결과를 재미있고 통찰력 있게 설명해주는 카피라이터입니다.

사용자의 성향 유형: {type_name} ({type_code})
이 유형의 기본 특징: {type_desc}

사용자의 답변 내역:
{answers_text}

위 내용을 참고해서 이 사람만을 위한 개인화된 분석을 작성해주세요. 아래 구조를 반드시 지켜서 4개 문단으로 작성하고, 각 문단 앞에 표시된 소제목을 그대로 붙여주세요.

[오늘의 한마디]
이 사람의 답변 패턴에서 느껴지는 인상을 2문장으로 다정하게 표현.

[답변에서 보이는 특징]
사용자가 실제로 선택한 답변들을 근거로 들어, 어떤 경향이 두드러지는지 2~3문장으로 구체적으로 설명. 일반적인 유형 설명이 아니라 실제 답변 내용을 언급할 것.

[강점이 빛나는 순간]
이 유형이 특히 잘 해낼 수 있는 상황이나 관계를 2문장으로 설명.

[오늘을 위한 조언]
오늘 하루 실천할 수 있는 짧고 구체적인 조언 1~2문장으로 마무리.

작성 규칙:
- 형식적이지 않고, 친한 친구가 다정하게 얘기해주는 듯한 말투
- 소제목([오늘의 한마디] 등)은 그대로 유지하되 그 외 다른 설명, 따옴표, 마크다운 기호(*, # 등)는 사용하지 말 것
- 전체 250~350자 내외
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
        answers_text = body.get("answersText", "")

        if not type_name or not type_code:
            self._send_json(400, {"error": "typeName과 typeCode는 필수입니다."})
            return

        prompt = build_prompt(type_name, type_code, type_desc, answers_text)
        comment, result = generate_comment(prompt)

        if comment is None:
            self._send_json(result.get("status", 502), {"error": result.get("error", "AI 호출 실패")})
            return

        # result는 성공 시 provider 이름("gemini" 또는 "groq")
        self._send_json(200, {"comment": comment, "provider": result})

    def do_GET(self):
        self._send_json(405, {"error": "POST 요청만 지원합니다."})