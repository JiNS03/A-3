// 고정 질문 문항 (그때그때 생성하지 않고 미리 정의된 세트를 사용)
// axis: "energy"(E/I), "approach"(L/F), "style"(P/S)
// quick: 빠른진단(5문항)에 포함되는 문항 여부
const QUESTIONS = [
  {
    id: 1,
    axis: "energy",
    quick: true,
    text: "주말에 아무 계획이 없다면 당신은?",
    options: [
      { text: "친구들을 불러 모아 즉흥 모임을 만든다", value: "E" },
      { text: "혼자만의 시간을 보내며 재충전한다", value: "I" }
    ]
  },
  {
    id: 2,
    axis: "approach",
    quick: true,
    text: "친구가 고민 상담을 해왔다. 당신의 반응은?",
    options: [
      { text: "문제의 원인을 분석하고 해결책을 제시한다", value: "L" },
      { text: "먼저 공감하고 마음을 다독여준다", value: "F" }
    ]
  },
  {
    id: 3,
    axis: "style",
    quick: true,
    text: "여행을 떠나기 전 당신은?",
    options: [
      { text: "일정과 동선을 꼼꼼하게 계획한다", value: "P" },
      { text: "일단 떠나서 그때그때 정한다", value: "S" }
    ]
  },
  {
    id: 4,
    axis: "energy",
    quick: true,
    text: "회식이나 모임에서 당신은?",
    options: [
      { text: "분위기를 주도하며 대화를 이끈다", value: "E" },
      { text: "조용히 대화를 듣고 필요할 때 말한다", value: "I" }
    ]
  },
  {
    id: 5,
    axis: "approach",
    quick: true,
    text: "중요한 결정을 내릴 때 당신은?",
    options: [
      { text: "데이터와 근거를 꼼꼼히 따져본다", value: "L" },
      { text: "마음이 끌리는 방향을 따른다", value: "F" }
    ]
  },
  {
    id: 6,
    axis: "style",
    quick: false,
    text: "팀 프로젝트를 시작할 때 당신은?",
    options: [
      { text: "전체 계획표와 역할 분담부터 짠다", value: "P" },
      { text: "일단 시작하면서 방향을 잡아나간다", value: "S" }
    ]
  },
  {
    id: 7,
    axis: "energy",
    quick: false,
    text: "스트레스를 받을 때 당신은?",
    options: [
      { text: "사람들을 만나 이야기하며 푼다", value: "E" },
      { text: "혼자 생각을 정리하며 푼다", value: "I" }
    ]
  },
  {
    id: 8,
    axis: "approach",
    quick: false,
    text: "새로운 정보를 접할 때 당신은?",
    options: [
      { text: "사실 관계와 논리를 먼저 확인한다", value: "L" },
      { text: "그 정보가 주는 느낌과 의미를 먼저 생각한다", value: "F" }
    ]
  },
  {
    id: 9,
    axis: "style",
    quick: false,
    text: "마감이 있는 일을 할 때 당신은?",
    options: [
      { text: "미리미리 나눠서 진행한다", value: "P" },
      { text: "마감 직전 몰아서 집중한다", value: "S" }
    ]
  },
  {
    id: 10,
    axis: "energy",
    quick: false,
    text: "새로운 사람들과의 자리에서 당신은?",
    options: [
      { text: "먼저 다가가 대화를 시작한다", value: "E" },
      { text: "상대가 다가올 때까지 기다린다", value: "I" }
    ]
  }
];
