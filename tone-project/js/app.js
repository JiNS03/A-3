// ==========================================================
// TONE — 성향 컬러 테스트 앱 로직
// ==========================================================

const state = {
  mode: null,          // "quick" | "detailed"
  quizQuestions: [],
  currentIndex: 0,
  answers: {},          // { questionId: value }
  resultType: null
};

const views = {
  home: document.getElementById("view-home"),
  mode: document.getElementById("view-mode"),
  quiz: document.getElementById("view-quiz"),
  result: document.getElementById("view-result")
};

function goToView(name) {
  Object.values(views).forEach(v => v.classList.remove("active"));
  views[name].classList.add("active");
  window.scrollTo({ top: 0, behavior: "instant" in window.scrollTo ? "instant" : "auto" });
  document.getElementById("nav-progress").classList.toggle("show", name === "quiz");
}

function showToast(msg, duration = 3200) {
  const toast = document.getElementById("toast");
  toast.textContent = msg;
  toast.classList.add("show");
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => toast.classList.remove("show"), duration);
}

// ---------- 홈 뷰: 유형 갤러리 렌더 ----------
function renderTypeGallery() {
  const grid = document.getElementById("type-grid");
  grid.innerHTML = TYPE_ORDER.map(code => {
    const t = TYPES[code];
    return `
      <div class="type-card" style="--card-color:${t.color}">
        <div class="emoji">${t.emoji}</div>
        <span class="code-badge">${t.code}</span>
        <h3>${t.name}</h3>
        <p>${t.tagline}</p>
      </div>`;
  }).join("");

  // 스크롤 시 카드 등장 애니메이션
  const cards = grid.querySelectorAll(".type-card");
  const io = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add("reveal");
        io.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15 });
  cards.forEach((c, i) => {
    c.style.transitionDelay = `${(i % 4) * 60}ms`;
    io.observe(c);
  });
}

// ---------- 네비게이션 이벤트 ----------
document.getElementById("logo-home").addEventListener("click", (e) => {
  e.preventDefault();
  goToView("home");
});
document.getElementById("btn-start").addEventListener("click", () => goToView("mode"));
document.getElementById("scroll-hint").addEventListener("click", () => {
  document.getElementById("gallery").scrollIntoView({ behavior: "smooth" });
});
document.getElementById("btn-mode-back").addEventListener("click", () => goToView("home"));
document.getElementById("btn-home").addEventListener("click", () => goToView("home"));

document.querySelectorAll(".mode-card button[data-mode]").forEach(btn => {
  btn.addEventListener("click", () => startQuiz(btn.dataset.mode));
});

// ---------- 퀴즈 진행 ----------
function startQuiz(mode) {
  state.mode = mode;
  state.quizQuestions = mode === "quick"
    ? QUESTIONS.filter(q => q.quick)
    : QUESTIONS.slice();
  state.currentIndex = 0;
  state.answers = {};
  goToView("quiz");
  renderQuestion();
}

function renderQuestion() {
  const q = state.quizQuestions[state.currentIndex];
  const total = state.quizQuestions.length;

  document.getElementById("progress-fill").style.width =
    `${((state.currentIndex) / total) * 100 + (100 / total) * 0.15}%`;
  document.getElementById("progress-label").textContent = `${state.currentIndex + 1} / ${total}`;
  document.getElementById("question-text").textContent = q.text;
  document.getElementById("quiz-warning").textContent = "";

  const list = document.getElementById("option-list");
  list.innerHTML = q.options.map((opt, i) => `
    <button class="option-btn" data-value="${opt.value}" data-index="${i}">${opt.text}</button>
  `).join("");

  const selectedValue = state.answers[q.id];
  list.querySelectorAll(".option-btn").forEach(btn => {
    if (btn.dataset.value === selectedValue) btn.classList.add("selected");
    btn.addEventListener("click", () => {
      list.querySelectorAll(".option-btn").forEach(b => b.classList.remove("selected"));
      btn.classList.add("selected");
      state.answers[q.id] = btn.dataset.value;
      document.getElementById("quiz-warning").textContent = "";
    });
  });

  const prevBtn = document.getElementById("btn-prev");
  prevBtn.disabled = state.currentIndex === 0;
  const nextBtn = document.getElementById("btn-next");
  nextBtn.textContent = state.currentIndex === total - 1 ? "결과 보기" : "다음";
}

document.getElementById("btn-prev").addEventListener("click", () => {
  if (state.currentIndex > 0) {
    state.currentIndex -= 1;
    renderQuestion();
  }
});

document.getElementById("btn-next").addEventListener("click", () => {
  const q = state.quizQuestions[state.currentIndex];
  // 실패 처리: 빈 입력(선택하지 않고 다음으로 넘어가려는 경우)
  if (!state.answers[q.id]) {
    document.getElementById("quiz-warning").textContent = "옵션을 선택해주세요.";
    return;
  }
  if (state.currentIndex < state.quizQuestions.length - 1) {
    state.currentIndex += 1;
    renderQuestion();
  } else {
    finishQuiz();
  }
});

// ---------- 채점 로직 ----------
function computeResultType() {
  const counts = { E: 0, I: 0, L: 0, F: 0, P: 0, S: 0 };
  state.quizQuestions.forEach(q => {
    const v = state.answers[q.id];
    if (v) counts[v] += 1;
  });
  const axis1 = counts.E >= counts.I ? "E" : "I";
  const axis2 = counts.L >= counts.F ? "L" : "F";
  const axis3 = counts.P >= counts.S ? "P" : "S";
  return axis1 + axis2 + axis3;
}

// ---------- 결과 화면 ----------
function finishQuiz() {
  const code = computeResultType();
  state.resultType = TYPES[code];
  goToView("result");
  renderResultCard();
  fetchAIComment();
}

function renderResultCard() {
  const t = state.resultType;
  document.documentElement.style.setProperty("--result-color", t.color);
  document.getElementById("card-front").style.setProperty("--result-color", t.color);
  document.getElementById("result-emoji").textContent = t.emoji;
  document.getElementById("result-code").textContent = t.code;
  document.getElementById("result-name").textContent = t.name;
  document.getElementById("result-tagline").textContent = t.tagline;

  document.getElementById("result-desc").textContent = t.desc;
  document.getElementById("strength-tags").innerHTML =
    t.strengths.map(s => `<span>${s}</span>`).join("");

  const partner = TYPES[t.partner];
  document.getElementById("partner-note").innerHTML =
    `잘 어울리는 상대는 <strong>${partner.emoji} ${partner.name}</strong>이에요.`;

  // 초기 상태 리셋
  const flipCard = document.getElementById("flip-card");
  flipCard.classList.remove("flipped");
  document.getElementById("ai-box").classList.remove("show");
  document.getElementById("desc-box").style.display = "none";
  document.getElementById("partner-note").style.display = "none";
  document.getElementById("result-loading").textContent = "AI가 당신의 카드를 그리는 중...";

  // 카드 뒤집기 연출
  setTimeout(() => flipCard.classList.add("flipped"), 400);
}

async function fetchAIComment() {
  const t = state.resultType;
  const answersText = state.quizQuestions.map(q => {
    const chosen = q.options.find(o => o.value === state.answers[q.id]);
    return `- ${q.text} → ${chosen ? chosen.text : "(무응답)"}`;
  }).join("\n");

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 15000); // 15초 타임아웃

  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        typeName: t.name,
        typeCode: t.code,
        typeDesc: t.desc,
        answersText
      }),
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    if (!res.ok) throw new Error(`API 오류: ${res.status}`);

    const data = await res.json();
    if (!data.comment) throw new Error("빈 응답");

    showAIComment(data.comment);
  } catch (err) {
    clearTimeout(timeoutId);
    // 실패 처리: API 오류 / 타임아웃 시 기본 설명으로 대체
    console.error(err);
    const isAbort = err.name === "AbortError";
    showToast(isAbort
      ? "AI 응답이 지연되어 기본 카드로 보여드려요."
      : "AI 코멘트를 불러오지 못해 기본 카드로 보여드려요.");
    showAIComment(null);
  }
}

function showAIComment(comment) {
  document.getElementById("result-loading").textContent = "";
  const aiBox = document.getElementById("ai-box");
  if (comment) {
    document.getElementById("ai-text").textContent = comment;
    aiBox.classList.add("show");
  } else {
    aiBox.style.display = "none";
  }
  document.getElementById("desc-box").style.display = "block";
  document.getElementById("partner-note").style.display = "block";
}

// ---------- 결과 액션 ----------
document.getElementById("btn-retry").addEventListener("click", () => goToView("mode"));

document.getElementById("btn-download").addEventListener("click", async () => {
  const target = document.querySelector(".result-shell");
  try {
    const canvas = await html2canvas(target, { backgroundColor: "#FFFBF2", scale: 2 });
    const link = document.createElement("a");
    link.download = `tone-${state.resultType.code}.png`;
    link.href = canvas.toDataURL("image/png");
    link.click();
  } catch (err) {
    console.error(err);
    showToast("카드를 저장하지 못했어요. 스크린샷으로 저장해보세요.");
  }
});

// ---------- 초기화 ----------
renderTypeGallery();
goToView("home");
