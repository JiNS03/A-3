# TONE — 성향 컬러 테스트

> 몇 가지 질문에 답하면 AI가 당신만의 성향 컬러 카드를 그려주는 웹 서비스

배포 URL: `여기에 Vercel 배포 URL을 적어주세요 (예: https://tone-quiz.vercel.app)`

---

## 1. 서비스 소개

**TONE**은 5문항(빠른 진단) 또는 10문항(정밀 진단) 중 원하는 방식을 골라 답하면, 8가지 성향 컬러 유형 중 하나의 결과 카드를 받아볼 수 있는 성향 테스트 서비스입니다.

- 정해진 질문 세트로 축(에너지 방향 · 판단 방식 · 실행 방식)을 채점해 유형을 결정하고,
- 결정된 유형과 사용자의 답변을 바탕으로 **Gemini API**가 그 사람만을 위한 짧은 개인화 코멘트를 생성합니다.
- 결과 카드는 이미지로 다운로드해 공유할 수 있습니다.

## 2. 기술 스택

| 영역 | 기술 |
|---|---|
| 프론트엔드 | HTML5, CSS3, Vanilla JavaScript (프레임워크 미사용) |
| 백엔드 | Vercel Serverless Functions (Python) |
| AI | Google Gemini API (`gemini-2.0-flash`) |
| 배포 | Vercel + GitHub 연동 |
| 기타 | html2canvas (결과 카드 이미지 다운로드) |

## 3. 프로젝트 구조

```
.
├── index.html            # 메인 페이지 (홈 / 모드선택 / 퀴즈 / 결과 뷰)
├── css/
│   └── style.css
├── js/
│   ├── types.js           # 8가지 성향 유형 데이터
│   ├── questions.js        # 고정 질문 문항 (5/10문항)
│   └── app.js               # 화면 전환·채점·AI 호출 로직
├── api/
│   └── analyze.py           # Gemini API 호출 서버리스 함수
├── requirements.txt
├── .env.example
└── README.md
```

## 4. 로컬에서 실행하기

이 프로젝트는 Vercel Serverless Functions를 사용하므로, 로컬에서는 Vercel CLI로 실행하는 것을 권장합니다.

```bash
# 1. 의존성 설치
npm install -g vercel
pip install -r requirements.txt

# 2. 환경 변수 설정
cp .env.example .env
# .env 파일을 열어 GEMINI_API_KEY 값을 채워 넣기

# 3. 로컬 개발 서버 실행
vercel dev
```

브라우저에서 `http://localhost:3000` 접속.

> 정적 파일(HTML/CSS/JS)만 확인하고 싶다면 `index.html`을 바로 열어도 되지만, 이 경우 AI 기능(`/api/analyze`)은 동작하지 않습니다.

## 5. 배포 방법 (Vercel)

1. 이 저장소를 GitHub에 푸시합니다.
2. [Vercel](https://vercel.com)에 로그인 후 **New Project → GitHub 저장소 import**.
3. 별도 빌드 설정 없이 Vercel이 `api/*.py`를 자동으로 Python 서버리스 함수로 인식합니다.
4. **Settings → Environment Variables**에서 `GEMINI_API_KEY`를 등록합니다.
5. Deploy. 배포가 끝나면 발급된 URL로 접속해 동작을 확인합니다.
6. 이후 코드를 수정하면 GitHub에 push할 때마다 자동으로 재배포됩니다.

## 6. 환경 변수

| 변수명 | 설명 | 예시 |
|---|---|---|
| `GEMINI_API_KEY` | Google AI Studio에서 발급받은 Gemini API 키. [발급 링크](https://aistudio.google.com/apikey) | `AIza...` |

**주의:** API 키는 절대 코드나 README, 스크린샷에 직접 노출하지 마세요. 로컬에서는 `.env`(gitignore 처리됨), 배포 환경에서는 Vercel의 Environment Variables 기능을 사용합니다. 키가 유출된 것으로 의심되면 즉시 Google AI Studio에서 키를 폐기·재발급하고, 만약 커밋 이력에 키가 남아있다면 히스토리에서도 제거하세요.

## 7. AI 기능 동작 방식

1. 사용자가 퀴즈를 마치면 프론트엔드에서 정해진 채점 로직으로 8가지 유형 중 하나를 즉시 결정합니다.
2. 결정된 유형 정보와 사용자의 답변 내역을 `/api/analyze`로 전송합니다.
3. 서버리스 함수가 Gemini API를 호출해 2~3문장의 개인화된 코멘트를 생성해 반환합니다.
4. 실패 처리
   - 응답이 15초 이상 지연되면 요청을 중단하고 안내 토스트를 띄운 뒤 기본 유형 설명으로 대체합니다.
   - API 오류(4xx/5xx) 발생 시에도 동일하게 기본 유형 설명으로 자연스럽게 대체되어 서비스가 끊기지 않습니다.

## 8. 라이선스 / 참고

이 프로젝트는 학습 목적의 미션 결과물입니다.
