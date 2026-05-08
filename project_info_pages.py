"""
project_info_pages.py — 璞玉문화 프로젝트 정보 페이지 (전문 UI/UX)
==================================================================

설계 원칙:
    - 절제된 색 사용 (휘인 청록 #2a9d8f를 핵심 강조)
    - 명확한 타이포 위계 (4단계)
    - 충분한 화이트 스페이스
    - 일관된 카드 + 그림자 + 미세 보더
    - 데이터 중심 — 메트릭/표/타임라인 적극 활용

작성일: 2026-05-08 (v2 — 전문 UI 재작성)
"""

import streamlit as st


# ============================================================
# 전문 CSS — 정보 페이지 전용 (기존 앱 CSS와 분리)
# ============================================================

_PROFESSIONAL_CSS = """
<style>
/* ===== 색상 시스템 ===== */
:root {
    --bg-deep: #0a0a0f;
    --bg-card: #14141c;
    --bg-elev: #1c1c26;
    --border-subtle: #25252f;
    --border-emphasis: #353545;
    --text-primary: #e8e8ec;
    --text-secondary: #9ca3af;
    --text-tertiary: #6b7280;
    --accent-wheein: #2a9d8f;
    --accent-blue: #5b8def;
    --accent-amber: #d97706;
    --accent-rose: #e11d48;
    --accent-violet: #7c3aed;
}

/* ===== 컨테이너 ===== */
.ip-container {
    padding: 0.5rem 0;
}

/* ===== 페이지 헤더 ===== */
.ip-hero {
    padding: 1.5rem 0 2rem 0;
    border-bottom: 1px solid var(--border-subtle);
    margin-bottom: 2rem;
}
.ip-hero-eyebrow {
    color: var(--accent-wheein);
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 0.6rem;
}
.ip-hero-title {
    font-size: 2rem;
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1.2;
    letter-spacing: -0.02em;
    margin-bottom: 0.5rem;
}
.ip-hero-subtitle {
    font-size: 1rem;
    color: var(--text-secondary);
    line-height: 1.6;
    max-width: 680px;
}

/* ===== 섹션 ===== */
.ip-section {
    margin: 2.5rem 0 1rem 0;
}
.ip-section-label {
    color: var(--text-tertiary);
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin-bottom: 0.8rem;
}
.ip-section-title {
    font-size: 1.35rem;
    font-weight: 600;
    color: var(--text-primary);
    letter-spacing: -0.01em;
    margin-bottom: 1rem;
}

/* ===== 카드 ===== */
.ip-card {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: 10px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 0.8rem;
    transition: border-color 0.2s ease;
}
.ip-card:hover {
    border-color: var(--border-emphasis);
}
.ip-card-accent {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-left: 3px solid var(--accent-wheein);
    border-radius: 8px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 0.6rem;
}

/* ===== 메트릭 카드 ===== */
.ip-metric {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: 10px;
    padding: 1.5rem 1.6rem;
    height: 100%;
}
.ip-metric-label {
    color: var(--text-tertiary);
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 0.6rem;
}
.ip-metric-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1.2;
    margin-bottom: 0.3rem;
    letter-spacing: -0.01em;
}
.ip-metric-value-accent {
    color: var(--accent-wheein);
}
.ip-metric-caption {
    color: var(--text-secondary);
    font-size: 0.82rem;
}

/* ===== 인용 박스 ===== */
.ip-quote {
    background: linear-gradient(180deg, rgba(42,157,143,0.05) 0%, rgba(42,157,143,0.02) 100%);
    border-left: 2px solid var(--accent-wheein);
    border-radius: 4px;
    padding: 1.4rem 1.8rem;
    margin: 1.2rem 0;
}
.ip-quote-label {
    color: var(--accent-wheein);
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 0.6rem;
}
.ip-quote-text {
    color: var(--text-primary);
    font-size: 1.02rem;
    line-height: 1.7;
    font-weight: 400;
}

/* ===== Pill / Badge ===== */
.ip-pill {
    display: inline-block;
    padding: 4px 11px;
    border-radius: 12px;
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 0.02em;
    border: 1px solid var(--border-emphasis);
    background: var(--bg-elev);
    color: var(--text-secondary);
}
.ip-pill-active {
    background: rgba(42,157,143,0.12);
    color: var(--accent-wheein);
    border-color: rgba(42,157,143,0.4);
}
.ip-pill-warn {
    background: rgba(217,119,6,0.10);
    color: var(--accent-amber);
    border-color: rgba(217,119,6,0.3);
}
.ip-pill-info {
    background: rgba(91,141,239,0.10);
    color: var(--accent-blue);
    border-color: rgba(91,141,239,0.3);
}

/* ===== 표 ===== */
.ip-table {
    width: 100%;
    border-collapse: collapse;
    margin: 0.6rem 0;
}
.ip-table th {
    text-align: left;
    padding: 0.7rem 0.9rem;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-tertiary);
    letter-spacing: 0.06em;
    text-transform: uppercase;
    border-bottom: 1px solid var(--border-emphasis);
}
.ip-table td {
    padding: 0.85rem 0.9rem;
    font-size: 0.92rem;
    color: var(--text-primary);
    border-bottom: 1px solid var(--border-subtle);
}
.ip-table tr:last-child td {
    border-bottom: none;
}
.ip-table-cell-muted {
    color: var(--text-secondary);
    font-size: 0.85rem;
}

/* ===== 타임라인 ===== */
.ip-timeline {
    border-left: 2px solid var(--border-subtle);
    padding-left: 1.5rem;
    margin-left: 0.5rem;
}
.ip-timeline-item {
    position: relative;
    padding-bottom: 1.4rem;
}
.ip-timeline-item::before {
    content: "";
    position: absolute;
    left: -1.85rem;
    top: 0.4rem;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: var(--bg-deep);
    border: 2px solid var(--accent-wheein);
}
.ip-timeline-week {
    color: var(--accent-wheein);
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    margin-bottom: 0.3rem;
}
.ip-timeline-task {
    color: var(--text-primary);
    font-size: 1rem;
    font-weight: 500;
    margin-bottom: 0.3rem;
}
.ip-timeline-status {
    color: var(--text-secondary);
    font-size: 0.85rem;
}

/* ===== 진행 상태 리스트 ===== */
.ip-progress-row {
    display: flex;
    align-items: center;
    padding: 0.65rem 0;
    border-bottom: 1px solid var(--border-subtle);
}
.ip-progress-row:last-child {
    border-bottom: none;
}
.ip-progress-icon {
    width: 1.5rem;
    flex-shrink: 0;
    font-size: 0.9rem;
}
.ip-progress-text {
    flex: 1;
    color: var(--text-primary);
    font-size: 0.9rem;
}
.ip-progress-text-done {
    color: var(--text-secondary);
}

/* ===== 본문 텍스트 ===== */
.ip-body {
    color: var(--text-secondary);
    font-size: 0.92rem;
    line-height: 1.7;
}
.ip-body-emphasis {
    color: var(--text-primary);
    font-weight: 500;
}

/* ===== 코드 블록 ===== */
.ip-code-block {
    background: var(--bg-deep);
    border: 1px solid var(--border-subtle);
    border-radius: 6px;
    padding: 1rem 1.2rem;
    margin: 0.8rem 0;
    font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
    font-size: 0.82rem;
    color: var(--text-secondary);
    line-height: 1.6;
    overflow-x: auto;
}

/* ===== 비교 컬럼 ===== */
.ip-compare-col {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: 10px;
    padding: 1.6rem 1.8rem;
    height: 100%;
}
.ip-compare-eyebrow {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}
.ip-compare-title {
    font-size: 1.4rem;
    font-weight: 700;
    margin-bottom: 0.3rem;
    letter-spacing: -0.01em;
}
.ip-compare-subtitle {
    color: var(--text-secondary);
    font-size: 0.85rem;
    margin-bottom: 1rem;
}
.ip-compare-list {
    list-style: none;
    padding: 0;
    margin: 0;
}
.ip-compare-list li {
    color: var(--text-secondary);
    font-size: 0.9rem;
    padding: 0.4rem 0;
    line-height: 1.6;
}
.ip-compare-list li::before {
    content: "—";
    color: var(--text-tertiary);
    margin-right: 0.6rem;
}

/* ===== 디바이더 ===== */
.ip-divider {
    height: 1px;
    background: var(--border-subtle);
    margin: 2rem 0;
    border: none;
}
</style>
"""


def _inject_css():
    st.markdown(_PROFESSIONAL_CSS, unsafe_allow_html=True)


# ============================================================
# 라우터
# ============================================================

def render_project_info_pages():
    _inject_css()

    sub_page = st.sidebar.radio(
        "정보 페이지",
        [
            "Overview",
            "회사 헌법",
            "7주 로드맵",
            "휘인 정밀 분석",
            "5인 11변수 비교",
            "화사 vs 휘인",
            "1차 모델 구조",
        ],
        key="info_sub_page",
    )

    st.markdown('<div class="ip-container">', unsafe_allow_html=True)

    if sub_page == "Overview":
        _show_overview()
    elif sub_page == "회사 헌법":
        _show_constitution()
    elif sub_page == "7주 로드맵":
        _show_roadmap()
    elif sub_page == "휘인 정밀 분석":
        _show_wheein_analysis()
    elif sub_page == "5인 11변수 비교":
        _show_radar_comparison()
    elif sub_page == "화사 vs 휘인":
        _show_hwasa_vs_wheein()
    elif sub_page == "1차 모델 구조":
        _show_v1_structure()

    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# 1. Overview
# ============================================================

def _show_overview():
    st.markdown("""
    <div class="ip-hero">
        <div class="ip-hero-eyebrow">PROJECT — V1 SYSTEM</div>
        <div class="ip-hero-title">璞玉문화 AI 캐스팅 시스템</div>
        <div class="ip-hero-subtitle">
            K-POP 30년의 직관 기반 캐스팅을 AI 기반 outlier 탐지로 전환합니다.
            잘하는 사람이 아닌, 남다르고 타고난 사람을 자동 발굴하는 시스템.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="ip-quote">
        <div class="ip-quote-label">한 줄 정의</div>
        <div class="ip-quote-text">
            AI가 화사 같은 보컬 천재를, 인간 캐스팅이 놓치는 영역에서 자동으로 발견하는 시스템.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="ip-section-label">CORE METRICS</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        <div class="ip-metric">
            <div class="ip-metric-label">CORE TOOLS</div>
            <div class="ip-metric-value">MERT · DDSP · Annoy</div>
            <div class="ip-metric-caption">사용자 결정 우선순위 · 음악 AI 핵심 3종</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="ip-metric">
            <div class="ip-metric-label">GOLD STANDARD</div>
            <div class="ip-metric-value ip-metric-value-accent">휘인 (마마무)</div>
            <div class="ip-metric-caption">2026-05-08 결정 · 시스템 정밀도 시험대</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="ip-metric">
            <div class="ip-metric-label">DEADLINE</div>
            <div class="ip-metric-value">2026 · 08 · 04</div>
            <div class="ip-metric-caption">v1 시스템 정식 가동</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="ip-section-label" style="margin-top:2.5rem;">AI 3대 우위</div>', unsafe_allow_html=True)

    advantages = [
        ("01", "지역 무차별", "1선 도시든 18선 현이든 전수 스캔. 14억 인구의 작은 도시에 숨은 인재까지 도달."),
        ("02", "편견 부재", "옷·배경·화질·기존 성공 사례와의 유사성 같은 무의식적 필터 없이 본질만 측정."),
        ("03", "전수 스크리닝", "매일 수천만 개의 숏폼 영상을 지치지 않고 분석. 단 한 명도 놓치지 않음."),
    ]
    for num, title, desc in advantages:
        st.markdown(f"""
        <div class="ip-card-accent">
            <div style="display:flex; align-items:flex-start; gap:1.2rem;">
                <div style="color:var(--accent-wheein); font-size:0.85rem; font-weight:700; letter-spacing:0.05em; padding-top:2px;">{num}</div>
                <div style="flex:1;">
                    <div style="color:var(--text-primary); font-size:1rem; font-weight:600; margin-bottom:0.3rem;">{title}</div>
                    <div class="ip-body" style="font-size:0.88rem;">{desc}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="ip-section-label" style="margin-top:2.5rem;">진행 상태</div>', unsafe_allow_html=True)

    progress = [
        ("Colab 노트북 + 환경 검증", True),
        ("비교군 후보 + Demucs 모듈", True),
        ("휘인 중심 전환 일괄 수정", True),
        ("휘인 단독 정밀 분석 v1.5", True),
        ("시각화 모듈 + 실측 검증", True),
        ("W2 (DDSP) 사전 조사 + Day 1 환경", True),
        ("1차 모델 통합 파이프라인", True),
        ("RBW 음원 수령", False),
        ("W1 검증 실행", False),
    ]
    rows = []
    for task, done in progress:
        icon = "●" if done else "○"
        color = "var(--accent-wheein)" if done else "var(--text-tertiary)"
        text_class = "ip-progress-text-done" if done else "ip-progress-text"
        rows.append(f"""
        <div class="ip-progress-row">
            <div class="ip-progress-icon" style="color:{color};">{icon}</div>
            <div class="{text_class}">{task}</div>
            <div class="ip-pill {'ip-pill-active' if done else ''}">{'완료' if done else '대기'}</div>
        </div>
        """)
    st.markdown('<div class="ip-card">' + "".join(rows) + '</div>', unsafe_allow_html=True)


# ============================================================
# 2. 회사 헌법
# ============================================================

def _show_constitution():
    st.markdown("""
    <div class="ip-hero">
        <div class="ip-hero-eyebrow">FOUNDATIONAL PRINCIPLES</div>
        <div class="ip-hero-title">회사 헌법</div>
        <div class="ip-hero-subtitle">
            모든 시스템 설계·코드·의사결정의 최상위 원칙. 절대 위반 불가.
        </div>
    </div>
    """, unsafe_allow_html=True)

    principles = [
        {
            "num": "01",
            "title": "종합 점수 영구 금지",
            "desc": "합산·가중평균·단일 숫자 순위는 어떤 시스템에서도 등장하지 않습니다.",
            "detail": "종합 점수의 본질은 평균화입니다. 비평균적 천재성을 측정하는 데 평균화 도구를 쓰는 것은 도구와 목적의 정반대입니다. 모차르트, 반 고흐, 아인슈타인, 잡스, 권지용 — 모두 종합 점수 시스템에서는 \"불량품\"으로 분류됐을 인물들입니다.",
            "color": "var(--accent-rose)",
        },
        {
            "num": "02",
            "title": "OR 논리 (AND 아님)",
            "desc": "후보 통과 조건은 \"하나의 차원에서라도 극단값\" + \"필수 조건 전부 통과\".",
            "detail": "여러 차원에서 동시 outlier일 필요 없습니다. 단 하나면 충분합니다. 권지용은 스타일·음악 감각, 제니는 무대 장악력, 화사는 자기확신, 뷔는 미스터리 매력 — 모두 단일 차원의 극단으로 정점에 도달했습니다.",
            "color": "var(--accent-amber)",
        },
        {
            "num": "03",
            "title": "양쪽 꼬리 — 초우월 + 초이질",
            "desc": "분포의 양쪽 모두에서 outlier를 검출합니다.",
            "detail": "오른쪽(초우월): 너무 잘생김, 너무 잘 춤 — 식별 쉬움. 왼쪽(초이질): 이목구비 특이, 목소리 묘함 — 자주 놓침. 진짜 원석의 다수가 왼쪽에 있습니다. AI 시스템은 양쪽을 모두 잡아야 합니다.",
            "color": "var(--accent-blue)",
        },
        {
            "num": "04",
            "title": "100차원 통계 보정 — 상위 0.05%",
            "desc": "100개 독립 차원에서 단일 차원 임계값은 상위 0.05% (2,000명 중 1명).",
            "detail": "임계값을 0.5%로 두면 위양성이 60% 이상으로 폭증합니다. 따라서 차원 수에 비례해 임계값을 보정해야 하며, 최소 5,000명 이상의 표본으로 베이스라인을 구축해야 합니다.",
            "color": "var(--accent-wheein)",
        },
    ]

    for p in principles:
        st.markdown(f"""
        <div class="ip-card" style="border-left:3px solid {p['color']};">
            <div style="display:flex; align-items:flex-start; gap:1.5rem;">
                <div style="color:{p['color']}; font-size:1rem; font-weight:700; letter-spacing:0.05em; padding-top:2px; min-width:2rem;">{p['num']}</div>
                <div style="flex:1;">
                    <div style="color:var(--text-primary); font-size:1.15rem; font-weight:600; margin-bottom:0.5rem; letter-spacing:-0.01em;">{p['title']}</div>
                    <div style="color:var(--text-primary); font-size:0.95rem; margin-bottom:0.8rem; line-height:1.6;">{p['desc']}</div>
                    <div class="ip-body" style="font-size:0.88rem;">{p['detail']}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# 3. 7주 로드맵
# ============================================================

def _show_roadmap():
    st.markdown("""
    <div class="ip-hero">
        <div class="ip-hero-eyebrow">PHASE 2 — 7-WEEK ROADMAP</div>
        <div class="ip-hero-title">시스템 고도화 로드맵</div>
        <div class="ip-hero-subtitle">
            MERT + DDSP + Annoy 핵심 3종 도입을 통한 v1 시스템 정식 가동까지의 흐름.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="ip-section-label">TIMELINE</div>', unsafe_allow_html=True)

    roadmap = [
        ("W1", "MERT-v1-95M 통합 + 휘인 outlier 검증", "환경 완료, 음원 대기"),
        ("W2 — W3", "DDSP — 휘인 7차원 1·2·3·4번 정량화", "사전 조사 완료, Day 1 환경"),
        ("W4", "Demucs — 더우인/유튜브 보컬 자동 추출", "모듈 완료, 가동 대기"),
        ("W5 — W6", "Annoy — 5,000명 시드 임베딩 인덱스", "사전 설계 단계"),
        ("W7+", "100차원 시스템 재정렬 + 실전 캐스팅 적용", "대기"),
    ]

    timeline_html = '<div class="ip-timeline">'
    for week, task, status in roadmap:
        timeline_html += f"""
        <div class="ip-timeline-item">
            <div class="ip-timeline-week">{week}</div>
            <div class="ip-timeline-task">{task}</div>
            <div class="ip-timeline-status">{status}</div>
        </div>
        """
    timeline_html += '</div>'
    st.markdown(f'<div class="ip-card" style="padding:1.8rem 2rem;">{timeline_html}</div>', unsafe_allow_html=True)

    st.markdown('<div class="ip-section-label" style="margin-top:2.5rem;">W1 검증 가설</div>', unsafe_allow_html=True)

    hypotheses = [
        ("H1", "휘인이 비교군 50명 대비 outlier로 분리되는가",
         "시스템 정밀도의 진짜 시험대. 휘인은 미묘한 정점이라 화사보다 어려운 시험."),
        ("H2", "마마무 4인이 4개 클러스터로 자연 분리되는가",
         "톤 4사분면(청량/따뜻/묵직/건조)이 자동 분리되는지 확인."),
        ("H3", "임베딩 어느 레이어에서 outlier 신호가 강한가",
         "DDSP 추가 도입 필요성 판단. acoustic 레이어 강하면 W2 즉시 진입."),
    ]

    for hid, q, desc in hypotheses:
        st.markdown(f"""
        <div class="ip-card">
            <div style="display:flex; gap:1.3rem; align-items:flex-start;">
                <div style="color:var(--accent-wheein); font-size:1rem; font-weight:700; min-width:2.5rem; padding-top:2px;">{hid}</div>
                <div style="flex:1;">
                    <div style="color:var(--text-primary); font-size:1rem; font-weight:600; margin-bottom:0.4rem;">{q}</div>
                    <div class="ip-body" style="font-size:0.88rem;">{desc}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# 4. 휘인 정밀 분석
# ============================================================

def _show_wheein_analysis():
    st.markdown("""
    <div class="ip-hero">
        <div class="ip-hero-eyebrow">GOLD STANDARD ANALYSIS — V1.5</div>
        <div class="ip-hero-title">휘인 정밀 분석</div>
        <div class="ip-hero-subtitle">
            시스템 정밀도의 진짜 시험대. 화사가 명백한 outlier라면, 휘인은 섬세한 정점.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="ip-quote">
        <div class="ip-quote-label">한 문장 정의</div>
        <div class="ip-quote-text">
            휘인은 화사 같은 명백한 outlier가 아니라, 가벼운 성대 운용·비강 공명·R&B 친화도·절제된 표현이 결합된
            <span style="color:var(--accent-wheein); font-weight:600;">섬세한 정점</span>으로서,
            인간 캐스팅이 가장 놓치기 쉬운 유형이며 따라서 AI 정밀 측정 시스템의 진짜 가치를 증명할 수 있는 정답지다.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="ip-section-label">7차원 OUTLIER 분해 (1차 가설)</div>', unsafe_allow_html=True)

    seven_dim = [
        ("성대 운용", "가벼움", "K-POP 메인보컬 대부분 두꺼운 흉성 추구. 가벼운 운용은 소수.", "DDSP 측정 가능"),
        ("공명 패턴", "가슴+비강 균형", "한국 트레이닝은 흉성/두성 위주. 비강 절제는 드뭄.", "DDSP 측정 가능"),
        ("음색 텍스처", "맑음+허스키", "두 조합 동시 충족 매우 드물다.", "MERT + DDSP"),
        ("다이내믹 처리", "점진적 빌드업", "한국은 \"터트리는\" 폭발 강조. 점진적은 반대 정점.", "DDSP"),
        ("딕션 미학", "흐림의 미학", "K-POP은 명료성 추구. 휘인은 흐림이 정점.", "부분 측정"),
        ("감정 표현", "절제·내향성", "무대 보컬은 외향성. 휘인은 내향성 정점.", "인간 평가"),
        ("R&B 친화도", "한국어 그루브", "일반적으로 어색한 영역. 휘인은 자연 흡수.", "부분 측정"),
    ]

    rows_html = """
    <table class="ip-table">
        <thead>
            <tr>
                <th style="width:24%;">차원</th>
                <th style="width:22%;">휘인의 위치</th>
                <th>희소성 근거</th>
                <th style="width:18%; text-align:right;">측정 도구</th>
            </tr>
        </thead>
        <tbody>
    """
    for dim, position, rarity, measure in seven_dim:
        rows_html += f"""
        <tr>
            <td style="font-weight:500;">{dim}</td>
            <td><span style="color:var(--accent-wheein);">{position}</span></td>
            <td class="ip-table-cell-muted">{rarity}</td>
            <td style="text-align:right;"><span class="ip-pill ip-pill-info">{measure}</span></td>
        </tr>
        """
    rows_html += "</tbody></table>"
    st.markdown(f'<div class="ip-card" style="padding:0.5rem 1.5rem;">{rows_html}</div>', unsafe_allow_html=True)

    st.markdown('<div class="ip-section-label" style="margin-top:2.5rem;">11변수 매핑</div>', unsafe_allow_html=True)

    vars_data = [
        ("SDI", "감각 식별도", "중상", "음색 강함, 비주얼 보통", False),
        ("EDT", "표현 변형", "상", "ad-lib 즉흥 변주 정점", True),
        ("CER", "카메라-에너지", "중상", "자연스러운 활용 (화사 발산형 대비)", False),
        ("RMC", "리듬-동작", "상", "R&B 비트 후행, 여유 그루브", True),
        ("AAC", "자기 미학", "중상~상", "R&B 자기 미학 일관 (추정)", False),
        ("SCA", "자기 교정", "중상", "정밀 정보 부족 (추정)", False),
        ("CDR", "교차 차원", "중상", "수렴형 (보컬 영역)", True),
        ("EDI", "에너지 방향", "+0.5~0.7", "흡인형 — 제니와 같은 카테고리", True),
        ("NVC", "비음악 가치", "중상", "그림·패션 등 (추정)", False),
        ("CCI", "문화 코드", "중상~상", "한국어+R&B 자연 결합", False),
        ("CBP", "카테고리 경계", "중상", "그룹→솔로→다영역", False),
    ]

    vars_html = """
    <table class="ip-table">
        <thead>
            <tr>
                <th style="width:14%;">코드</th>
                <th style="width:24%;">변수명</th>
                <th style="width:14%;">수준</th>
                <th>설명</th>
            </tr>
        </thead>
        <tbody>
    """
    for code, name, level, note, strong in vars_data:
        emphasis = "ip-pill-active" if strong else ""
        code_color = "var(--accent-wheein)" if strong else "var(--text-secondary)"
        vars_html += f"""
        <tr>
            <td><code style="color:{code_color}; font-size:0.85rem;">{code}</code></td>
            <td>{name}</td>
            <td><span class="ip-pill {emphasis}">{level}</span></td>
            <td class="ip-table-cell-muted">{note}</td>
        </tr>
        """
    vars_html += "</tbody></table>"
    st.markdown(f'<div class="ip-card" style="padding:0.5rem 1.5rem;">{vars_html}</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="ip-quote" style="margin-top:2rem;">
        <div class="ip-quote-label">CORE INSIGHT</div>
        <div class="ip-quote-text">
            <span style="color:var(--accent-wheein); font-weight:600;">휘인 = 제니 모델의 보컬 특화 버전.</span>
            제니가 비주얼·라이프스타일 영역 수렴이라면, 휘인은 보컬 영역 수렴.
            산업적 의미: \"vocal-driven 흡인형 보컬리스트\"라는 새로운 카테고리 정립 가능.
        </div>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# 5. 5인 11변수 비교
# ============================================================

def _show_radar_comparison():
    st.markdown("""
    <div class="ip-hero">
        <div class="ip-hero-eyebrow">COMPARATIVE ANALYSIS</div>
        <div class="ip-hero-title">5인 11변수 비교</div>
        <div class="ip-hero-subtitle">
            권지용 · 제니 · 공민지 · 전소미 · 휘인. 식별도 유형으로 카테고리화.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="ip-section-label">식별도 유형 분류</div>', unsafe_allow_html=True)

    types = [
        ("권지용", "이탈형", "기존 DB와의 거리"),
        ("제니", "수렴형", "럭셔리 + 힙합 + 걸크러시 동시 충족"),
        ("휘인", "수렴형 (보컬)", "맑음 + 허스키 + R&B + 절제 동시 충족"),
        ("공민지", "단일 차원", "퍼포먼스 편중"),
        ("전소미", "비돌출 분산", "—"),
    ]

    types_html = """
    <table class="ip-table">
        <thead>
            <tr>
                <th style="width:18%;">인물</th>
                <th style="width:22%;">식별도 유형</th>
                <th>영역 / 조합</th>
            </tr>
        </thead>
        <tbody>
    """
    for name, ttype, area in types:
        is_wheein = name == "휘인"
        emphasis = "color:var(--accent-wheein); font-weight:600;" if is_wheein else "color:var(--text-primary);"
        types_html += f"""
        <tr>
            <td style="{emphasis}">{name}{' ★' if is_wheein else ''}</td>
            <td>{ttype}</td>
            <td class="ip-table-cell-muted">{area}</td>
        </tr>
        """
    types_html += "</tbody></table>"
    st.markdown(f'<div class="ip-card" style="padding:0.5rem 1.5rem;">{types_html}</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="ip-quote" style="margin-top:2rem;">
        <div class="ip-quote-label">KEY FINDING</div>
        <div class="ip-quote-text">
            휘인 = 제니 모델의 보컬 특화 버전. 수렴형 식별도 + 흡인형 에너지 + 중상 NVC/CCI/CBP — 같은 구조적 카테고리.
            차이는 영역: 제니는 비주얼·라이프스타일, 휘인은 보컬.
            마마무 4인 균형 모델의 핵심 위치이자 <span style="color:var(--accent-wheein); font-weight:600;">vocal-driven 흡인형 보컬리스트</span>의 정의 사례.
        </div>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# 6. 화사 vs 휘인
# ============================================================

def _show_hwasa_vs_wheein():
    st.markdown("""
    <div class="ip-hero">
        <div class="ip-hero-eyebrow">CONTRAST STUDY</div>
        <div class="ip-hero-title">화사 vs 휘인</div>
        <div class="ip-hero-subtitle">
            같은 그룹 안 정반대 정점. 강한 정점과 섬세한 정점의 대비축.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="ip-compare-col">
            <div class="ip-compare-eyebrow" style="color:var(--accent-rose);">강한 정점</div>
            <div class="ip-compare-title" style="color:var(--accent-rose);">화사</div>
            <div class="ip-compare-subtitle">명백한 outlier — 캐스팅이 잘 잡는 영역</div>
            <ul class="ip-compare-list">
                <li>7차원 모두 강하게 분리됨</li>
                <li>캐스팅 단계 즉시 식별</li>
                <li>큰 소리·강한 음역에서 빛남</li>
                <li>무대 영상 1개로 충분</li>
                <li>인간 캐스팅이 잘 잡는 영역</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="ip-compare-col" style="border-color:var(--accent-wheein);">
            <div class="ip-compare-eyebrow" style="color:var(--accent-wheein);">섬세한 정점</div>
            <div class="ip-compare-title" style="color:var(--accent-wheein);">휘인</div>
            <div class="ip-compare-subtitle">미묘한 outlier — AI 정밀 측정의 차별화 영역</div>
            <ul class="ip-compare-list">
                <li>단일 차원만 보면 평범</li>
                <li>캐스팅 단계에서 자주 묻힘</li>
                <li>작은 소리·미세 디테일에서 빛남</li>
                <li>다수 영상 + 정밀 분석 필요</li>
                <li>AI 정밀 측정의 차별화 영역</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="ip-quote" style="margin-top:2rem;">
        <div class="ip-quote-label">CORE PROPOSITION</div>
        <div class="ip-quote-text">
            <span style="color:var(--accent-wheein); font-weight:600;">휘인을 잡아낼 수 있는 시스템은 화사형을 자동으로 잡습니다 (역은 성립 안 함).</span>
            따라서 휘인 검증이 시스템의 진짜 정밀도 시험대입니다.
            화사는 누구나 알아보지만, 휘인을 알아보는 시스템이 진짜 천재 발굴기입니다.
        </div>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# 7. 1차 모델 구조
# ============================================================

def _show_v1_structure():
    st.markdown("""
    <div class="ip-hero">
        <div class="ip-hero-eyebrow">SYSTEM ARCHITECTURE</div>
        <div class="ip-hero-title">1차 모델 통합 파이프라인</div>
        <div class="ip-hero-subtitle">
            idol_scout_v1.py — 입력에서 판정·시각화까지 8단계 자동 파이프라인.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="ip-section-label">PIPELINE — 8 STEPS</div>', unsafe_allow_html=True)

    steps = [
        ("01", "입력 처리", "URL 또는 파일 인식 / yt-dlp 자동 다운로드"),
        ("02", "보컬 분리 (선택)", "Demucs를 통한 보컬 단독 트랙 추출"),
        ("03", "MERT 임베딩 추출", "768차원 음색 지문 — 음색 고유성·판별력의 측정 엔진"),
        ("04", "DDSP 5개 파라미터 분해", "F0 / Loudness / Harmonic / Noise / Spectral Envelope"),
        ("05", "100차원 시스템 매핑", "측정 가능한 차원만 자동 산출 (회사 헌법 정합)"),
        ("06", "Reference 비교", "휘인 거리 측정 + 비교군 분포 대비"),
        ("07", "OR 극단값 판정", "양쪽 꼬리: 초우월(상위 1%) + 초이질(하위 1%)"),
        ("08", "JSON 리포트 + 시각화", "차원별 결과 자동 저장"),
    ]

    for num, title, desc in steps:
        st.markdown(f"""
        <div class="ip-card">
            <div style="display:flex; align-items:flex-start; gap:1.3rem;">
                <div style="color:var(--accent-wheein); font-size:0.85rem; font-weight:700; letter-spacing:0.05em; padding-top:3px; min-width:1.8rem;">{num}</div>
                <div style="flex:1;">
                    <div style="color:var(--text-primary); font-size:1rem; font-weight:600; margin-bottom:0.3rem;">{title}</div>
                    <div class="ip-body" style="font-size:0.88rem;">{desc}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="ip-section-label" style="margin-top:2.5rem;">EVOLUTIONARY DESIGN</div>', unsafe_allow_html=True)

    evolution = [
        ("음원 0개 (현재)", "입력 1개 자동 분해 + 100차원 매핑 측정"),
        ("휘인 reference 도착", "휘인 거리 측정 + DDSP 4개 차원 outlier 판정"),
        ("비교군 도착", "양쪽 꼬리 자동 outlier 판정 — 시스템 본격 가동"),
        ("5,000명 시드 적재 (W5–6)", "상위 0.05% 자동 판정 — 회사 헌법 정합 적용"),
    ]

    rows_html = """
    <table class="ip-table">
        <thead>
            <tr>
                <th style="width:35%;">단계</th>
                <th>가능한 측정</th>
            </tr>
        </thead>
        <tbody>
    """
    for stage, capability in evolution:
        rows_html += f"""
        <tr>
            <td style="color:var(--accent-wheein); font-weight:500;">{stage}</td>
            <td class="ip-table-cell-muted">{capability}</td>
        </tr>
        """
    rows_html += "</tbody></table>"
    st.markdown(f'<div class="ip-card" style="padding:0.5rem 1.5rem;">{rows_html}</div>', unsafe_allow_html=True)

    st.markdown('<div class="ip-section-label" style="margin-top:2.5rem;">OUTPUT FORMAT</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="ip-code-block">ScreeningResult — 단일 점수 절대 없음
{
    "measured_dimensions": {
        "dim_01_voice_uniqueness": 0.342,
        "dim_07_chest_voice_quality": 0.71,
        "wheein_3_husky_texture": 0.18,
        ...  # 차원별 독립 출력
    },
    "outlier_dimensions_high": ["wheein_2_nasal_resonance"],
    "outlier_dimensions_low": [],
    "overall_verdict": "OUTLIER_FOUND",
    "notes": ["OR 논리: 어느 한 차원이라도 극단이면 통과"]
}</div>
    """, unsafe_allow_html=True)
