"""
project_info_pages.py — 璞玉문화 프로젝트 정보 페이지 모듈
=========================================================

기존 app.py에 사이드바 모드 "📚 프로젝트 정보"로 추가되는 모듈.
기존 앱의 다크 테마(#1e1e2e 카드, #a29bfe 강조)와 일관된 디자인.

사용:
    # app.py 상단에 추가
    from project_info_pages import render_project_info_pages

    # 사이드바 mode 라디오에 "📚 프로젝트 정보" 추가
    # main() 함수에 분기 추가:
    elif mode == "📚 프로젝트 정보":
        render_project_info_pages()

작성일: 2026-05-08
"""

import streamlit as st


# ============================================================
# 메인 라우터
# ============================================================

def render_project_info_pages():
    """프로젝트 정보 페이지 — 7개 sub-page 라우터."""
    sub_page = st.sidebar.radio(
        "정보 페이지",
        [
            "🏠 프로젝트 개요",
            "📜 회사 헌법",
            "🗺 7주 로드맵",
            "📊 휘인 정밀 분석",
            "📈 5인 11변수 비교",
            "⚖ 화사 vs 휘인 대비",
            "🛠 1차 모델 구조",
        ],
        key="info_sub_page",
    )

    if sub_page == "🏠 프로젝트 개요":
        _show_overview()
    elif sub_page == "📜 회사 헌법":
        _show_constitution()
    elif sub_page == "🗺 7주 로드맵":
        _show_roadmap()
    elif sub_page == "📊 휘인 정밀 분석":
        _show_wheein_analysis()
    elif sub_page == "📈 5인 11변수 비교":
        _show_radar_comparison()
    elif sub_page == "⚖ 화사 vs 휘인 대비":
        _show_hwasa_vs_wheein()
    elif sub_page == "🛠 1차 모델 구조":
        _show_v1_structure()


# ============================================================
# 페이지 1 — 프로젝트 개요
# ============================================================

def _show_overview():
    st.markdown("## 🎤 璞玉문화 AI 캐스팅 시스템 v1")
    st.caption("K-POP 30년 직관 캐스팅의 한계를 AI로 돌파")

    st.markdown("""
    <div class="paradigm-box">
        <div style="font-size:1.05rem; color:#ddd; margin-bottom:0.6rem;">
            <b style="color:#a29bfe;">한 줄 정의</b>
        </div>
        <div style="font-size:1rem; color:#ddd; line-height:1.8;">
            "AI가 화사 같은 보컬 천재를, 인간 캐스팅이 놓치는 영역에서 자동으로 발견하는 시스템"
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""<div class="card">
            <div class="card-title">🛠 핵심 도구</div>
            <div style="font-size:1.2rem; font-weight:600; color:#74b9ff;">MERT + DDSP + Annoy</div>
            <div class="detail-text">사용자 결정 우선순위</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""<div class="card">
            <div class="card-title">⭐ 골드 스탠다드</div>
            <div style="font-size:1.2rem; font-weight:600; color:#a29bfe;">휘인 (마마무)</div>
            <div class="detail-text">2026-05-08 결정</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown("""<div class="card">
            <div class="card-title">📅 데드라인</div>
            <div style="font-size:1.2rem; font-weight:600; color:#fdcb6e;">2026-08-04</div>
            <div class="detail-text">v1 시스템 가동</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")
    st.markdown('<div class="section-title">🌟 AI 3대 우위</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""<div class="card" style="border-top:3px solid #74b9ff;">
            <div style="font-size:1.5rem; margin-bottom:0.4rem;">🌍</div>
            <div style="font-weight:600; color:#eee;">지역 무차별</div>
            <div class="detail-text">1선 도시든 18선 현이든 전부 훑음</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("""<div class="card" style="border-top:3px solid #00b894;">
            <div style="font-size:1.5rem; margin-bottom:0.4rem;">🚫</div>
            <div style="font-weight:600; color:#eee;">편견 부재</div>
            <div class="detail-text">포장 아닌 본질 측정</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown("""<div class="card" style="border-top:3px solid #fd79a8;">
            <div style="font-size:1.5rem; margin-bottom:0.4rem;">📥</div>
            <div style="font-weight:600; color:#eee;">전수 스크리닝</div>
            <div class="detail-text">단 한 명도 놓치지 않음</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")
    st.markdown('<div class="section-title">📊 진행 상태</div>', unsafe_allow_html=True)
    progress = [
        ("Colab 노트북 + 환경 검증", True),
        ("비교군 후보 + Demucs 모듈", True),
        ("휘인 중심 전환 일괄 수정", True),
        ("휘인 단독 정밀 분석 v1.5", True),
        ("시각화 모듈", True),
        ("W2 (DDSP) 사전 조사 + Day 1", True),
        ("1차 모델 통합 파이프라인", True),
        ("RBW 음원 수령", False),
        ("W1 검증 실행", False),
    ]
    for task, done in progress:
        icon = "✅" if done else "⏳"
        color = "#00b894" if done else "#fdcb6e"
        st.markdown(f"<div style='padding:0.4rem 0;'>{icon} <span style='color:{color};'>{task}</span></div>", unsafe_allow_html=True)


# ============================================================
# 페이지 2 — 회사 헌법
# ============================================================

def _show_constitution():
    st.markdown("## 📜 회사 헌법 — 절대 위반 불가")
    st.caption("모든 시스템 설계·코드·의사결정의 최상위 원칙")

    st.markdown("""<div class="card" style="border:1px solid #e17055;">
        <div class="card-title" style="color:#e17055;">1. 종합 점수 영구 금지</div>
        <div class="detail-text" style="line-height:1.8;">
            • 합산·가중평균·단일 숫자 순위 — 어떤 시스템에서도 등장 금지<br>
            • 종합 점수 = 평균화 → 비평균적 천재성을 측정 불가능하게 만드는 도구<br>
            • 모차르트·반 고흐·아인슈타인·잡스·권지용 — 모두 종합 점수 시스템에선 "불량품"
        </div>
    </div>""", unsafe_allow_html=True)

    st.markdown("""<div class="card" style="border:1px solid #fdcb6e;">
        <div class="card-title" style="color:#fdcb6e;">2. OR 논리 (AND 아님)</div>
        <div class="detail-text" style="line-height:1.8;">
            • 후보 통과 = (플러스 차원 중 최소 하나 outlier) AND (필수 조건 전부 통과)<br>
            • 여러 차원에서 outlier일 필요 없음 — <b style="color:#ddd;">단 하나면 충분</b><br>
            • 권지용·제니·화사·뷔(BTS) — 모두 단일 차원 극단으로 정점 도달
        </div>
    </div>""", unsafe_allow_html=True)

    st.markdown("""<div class="card" style="border:1px solid #74b9ff;">
        <div class="card-title" style="color:#74b9ff;">3. 양쪽 꼬리 — 초우월 + 초이질</div>
        <div class="detail-text" style="line-height:1.8;">
            • <b style="color:#ddd;">오른쪽(초우월)</b>: 너무 잘생김, 너무 잘 춤 — 식별 쉬움<br>
            • <b style="color:#ddd;">왼쪽(초이질)</b>: 이목구비 특이, 목소리 묘함 — 자주 놓침. <span style="color:#a29bfe;">진짜 원석 다수가 여기</span><br>
            • AI 시스템은 양쪽 모두 잡아야 함
        </div>
    </div>""", unsafe_allow_html=True)

    st.markdown("""<div class="card" style="border:1px solid #00b894;">
        <div class="card-title" style="color:#00b894;">4. 100차원 통계 보정 — 상위 0.05%</div>
        <div class="detail-text" style="line-height:1.8;">
            • 100개 독립 차원에서 단일 차원 임계값 = <b style="color:#ddd;">상위 0.05%</b> (2,000명 중 1명)<br>
            • 임계값을 0.5%로 두면 위양성 폭증 (60%+)<br>
            • 최소 5,000명 이상 표본으로 베이스라인 구축 필요
        </div>
    </div>""", unsafe_allow_html=True)


# ============================================================
# 페이지 3 — 7주 로드맵
# ============================================================

def _show_roadmap():
    st.markdown("## 🗺 Phase 2 — 7주 로드맵")
    st.caption("MERT + DDSP + Annoy 핵심 3종 도입 흐름")

    roadmap = [
        ("W1", "MERT-v1-95M 통합 + 휘인 outlier 검증", "환경 완료, 음원 대기", "#00b894"),
        ("W2-3", "DDSP — 휘인 7차원 1·2·3·4번 정량화", "사전 조사 완료, Day 1 환경", "#fdcb6e"),
        ("W4", "Demucs — 더우인/유튜브 보컬 자동 추출", "모듈 완료, W4 가동 대기", "#74b9ff"),
        ("W5-6", "Annoy — 5,000명 시드 임베딩 인덱스", "사전 설계 단계", "#a29bfe"),
        ("W7+", "100차원 시스템 재정렬 + 실전 캐스팅", "대기", "#fd79a8"),
    ]

    for week, task, status, color in roadmap:
        st.markdown(f"""<div class="card" style="border-left:4px solid {color};">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-weight:700; color:{color}; font-size:1.05rem;">{week}</span>
                <span style="color:#aaa; font-size:0.85rem;">{status}</span>
            </div>
            <div style="color:#eee; margin-top:0.4rem;">{task}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")
    st.markdown('<div class="section-title">🎯 W1 검증 가설 3가지</div>', unsafe_allow_html=True)
    hypotheses = [
        ("H1", "휘인이 비교군 50명 대비 outlier 분리", "정밀도 시험대 — 휘인은 미묘한 정점이라 화사보다 어려운 시험"),
        ("H2", "마마무 4인이 4클러스터로 자연 분리", "톤 4사분면 자동 검증"),
        ("H3", "임베딩 어느 레이어에서 outlier 신호 강한가", "DDSP 필요성 판단"),
    ]
    for hid, q, desc in hypotheses:
        st.markdown(f"""<div class="card" style="padding:0.8rem 1.2rem;">
            <span style="color:#a29bfe; font-weight:600;">{hid}</span>:
            <span style="color:#eee;">{q}</span>
            <div class="detail-text" style="margin-top:0.3rem;">→ {desc}</div>
        </div>""", unsafe_allow_html=True)


# ============================================================
# 페이지 4 — 휘인 정밀 분석
# ============================================================

def _show_wheein_analysis():
    st.markdown("## 📊 휘인 정밀 분석 v1.5")
    st.caption("골드 스탠다드 — 시스템 정밀도의 진짜 시험대")

    st.markdown("""<div class="summary-box">
        <b style="color:#a29bfe;">한 문장 정의</b><br><br>
        "휘인은 화사 같은 명백한 outlier가 아니라, 가벼운 성대 운용 · 비강 공명 · R&B 친화도 · 절제된 표현이
        결합된 <b style="color:#ddd;">'섬세한 정점'</b>으로서, 인간 캐스팅이 가장 놓치기 쉬운 유형이며 따라서
        AI 정밀 측정 시스템의 진짜 가치를 증명할 수 있는 정답지다."
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-title">🎯 7차원 Outlier 분해 (1차 가설)</div>', unsafe_allow_html=True)

    seven_dim = [
        ("1. 성대 운용", "가벼움", "K-POP 메인보컬 대부분 두꺼운 흉성 추구. 가벼운 운용은 소수", "DDSP 측정 가능", "#00b894"),
        ("2. 공명 패턴", "가슴+비강 균형", "한국 트레이닝은 흉성/두성 위주. 비강 절제는 드뭄", "DDSP 측정 가능", "#00b894"),
        ("3. 음색 텍스처", "맑음+살짝 허스키", "두 조합 동시 충족 매우 드물다", "MERT+DDSP", "#74b9ff"),
        ("4. 다이내믹 처리", "점진적 빌드업", "한국은 \"터트리는\" 폭발 강조. 점진적은 반대 정점", "DDSP", "#74b9ff"),
        ("5. 딕션 미학", "흐림의 미학", "K-POP은 명료성 추구. 휘인은 흐림이 정점", "부분 측정", "#fdcb6e"),
        ("6. 감정 표현", "절제·내향성", "무대 보컬은 외향성. 휘인은 내향성 정점", "인간 평가 필수", "#e17055"),
        ("7. R&B 친화도", "한국어로 자연스러운 그루브", "일반적으로 어색한 영역", "부분 측정", "#fdcb6e"),
    ]

    for dim, position, rarity, measure, color in seven_dim:
        st.markdown(f"""<div class="card" style="padding:0.8rem 1.2rem; border-left:3px solid {color};">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-weight:600; color:#eee;">{dim}</span>
                <span style="color:{color}; font-size:0.85rem;">{measure}</span>
            </div>
            <div style="color:#a29bfe; font-size:0.9rem; margin:0.3rem 0;">→ {position}</div>
            <div class="detail-text">{rarity}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")
    st.markdown('<div class="section-title">📐 11변수 매핑 — 휘인 = 제니 보컬 버전</div>', unsafe_allow_html=True)

    st.markdown("""<div class="card">
        <div class="card-title">핵심 인사이트</div>
        <div style="color:#eee; line-height:1.8;">
            수렴형 식별도 + 흡인형 EDI + 중상 NVC/CCI/CBP — <b style="color:#a29bfe;">제니와 같은 구조적 카테고리</b>.<br>
            제니가 비주얼·라이프스타일 영역 수렴이라면, <b style="color:#ddd;">휘인은 보컬 영역 수렴</b>.<br><br>
            산업적 의미: <b style="color:#a29bfe;">"vocal-driven 흡인형 보컬리스트"</b>라는 새로운 카테고리 정립 가능.
        </div>
    </div>""", unsafe_allow_html=True)

    st.markdown("**11변수 수준 (1차 가설)**:")
    var_data = [
        ("SDI (감각 식별도)", "중상", "음색 강함, 비주얼 보통", "#74b9ff"),
        ("EDT (표현 변형)", "상 ⭐", "ad-lib 즉흥 변주 정점", "#a29bfe"),
        ("CER (카메라-에너지)", "중상 (활용형)", "자연스러운 활용", "#74b9ff"),
        ("RMC (리듬-동작)", "상 ⭐", "R&B 비트 후행", "#a29bfe"),
        ("AAC (자기 미학)", "중상~상", "R&B 자기 미학 일관", "#74b9ff"),
        ("SCA (자기 교정)", "중상 (추정)", "정밀 정보 부족", "#fdcb6e"),
        ("CDR (교차 차원)", "중상 ⭐", "수렴형 (보컬 영역)", "#a29bfe"),
        ("EDI (에너지)", "+0.5~0.7 흡인형 ⭐", "제니와 같은 카테고리", "#a29bfe"),
        ("NVC (비음악 가치)", "중상", "그림·패션 등", "#74b9ff"),
        ("CCI (문화 코드)", "중상~상", "한국어+R&B 자연 결합", "#74b9ff"),
        ("CBP (카테고리 경계)", "중상", "그룹→솔로→다영역", "#74b9ff"),
    ]
    for var, level, note, color in var_data:
        st.markdown(f"""<div style="padding:0.5rem 0; border-bottom:1px solid #2a2a3e;">
            <span style="color:#eee;">{var}</span>
            <span style="color:{color}; float:right; font-weight:500;">{level}</span>
            <div class="detail-text">{note}</div>
        </div>""", unsafe_allow_html=True)


# ============================================================
# 페이지 5 — 5인 11변수 비교
# ============================================================

def _show_radar_comparison():
    st.markdown("## 📈 5인 11변수 비교")
    st.caption("권지용 · 제니 · 공민지 · 전소미 · 휘인")

    st.markdown('<div class="section-title">🎭 식별도 유형 분류</div>', unsafe_allow_html=True)

    types = [
        ("권지용", "이탈형", "기존 DB와의 거리", "#74b9ff"),
        ("제니", "수렴형", "럭셔리+힙합+걸크러시 동시 충족", "#fd79a8"),
        ("휘인 ⭐", "수렴형 (보컬)", "맑음+허스키+R&B+절제 동시 충족", "#a29bfe"),
        ("공민지", "단일 차원", "퍼포먼스 편중", "#636e72"),
        ("전소미", "비돌출 분산", "—", "#636e72"),
    ]
    for name, ttype, area, color in types:
        st.markdown(f"""<div class="card" style="padding:0.7rem 1.2rem; border-left:3px solid {color};">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="color:{color}; font-weight:600;">{name}</span>
                <span style="color:#eee;">{ttype}</span>
            </div>
            <div class="detail-text">{area}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")
    st.markdown('<div class="section-title">🔍 핵심 인사이트</div>', unsafe_allow_html=True)
    st.markdown("""<div class="paradigm-box">
        <div style="color:#ddd; line-height:1.8;">
            <b style="color:#a29bfe;">"휘인 = 제니 모델의 보컬 특화 버전"</b><br><br>
            • 공통점: 수렴형 식별도 + 흡인형 에너지 + 중상 NVC/CCI/CBP<br>
            • 차이점: 제니는 <b style="color:#fd79a8;">비주얼·라이프스타일 영역</b> 수렴, 휘인은 <b style="color:#a29bfe;">보컬 영역</b> 수렴<br>
            • 마마무 4인 균형 모델의 핵심 위치 = 그룹 안의 흡인형 R&B 정점
        </div>
    </div>""", unsafe_allow_html=True)


# ============================================================
# 페이지 6 — 화사 vs 휘인 대비
# ============================================================

def _show_hwasa_vs_wheein():
    st.markdown("## ⚖ 화사 vs 휘인 — 같은 그룹 안 정반대 정점")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""<div class="card" style="border-top:3px solid #e17055;">
            <div style="text-align:center; margin-bottom:0.8rem;">
                <div style="font-size:1.4rem; color:#e17055; font-weight:700;">화사</div>
                <div style="color:#aaa;">강한 정점</div>
            </div>
            <div class="detail-text" style="line-height:2;">
                • 7차원 모두 <b style="color:#ddd;">명백한 outlier</b><br>
                • 캐스팅 단계 즉시 식별 가능<br>
                • 큰 소리·강한 음역에서 빛남<br>
                • 무대 영상 1개로 충분<br>
                • <span style="color:#fdcb6e;">인간 캐스팅이 잘 잡는 영역</span>
            </div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""<div class="card" style="border-top:3px solid #2a9d8f;">
            <div style="text-align:center; margin-bottom:0.8rem;">
                <div style="font-size:1.4rem; color:#2a9d8f; font-weight:700;">휘인 ⭐</div>
                <div style="color:#aaa;">섬세한 정점</div>
            </div>
            <div class="detail-text" style="line-height:2;">
                • <b style="color:#ddd;">미묘한 정점</b> (단일 차원만 보면 평범)<br>
                • 캐스팅 단계에서 자주 묻힘<br>
                • 작은 소리·미세 디테일에서 빛남<br>
                • 다수 영상 + 정밀 분석 필요<br>
                • <span style="color:#a29bfe;">AI 정밀 측정의 차별화 영역</span>
            </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")
    st.markdown('<div class="section-title">💡 핵심 명제</div>', unsafe_allow_html=True)
    st.markdown("""<div class="paradigm-box">
        <div style="color:#ddd; line-height:1.8; font-size:1rem;">
            <b style="color:#a29bfe;">휘인을 잡아낼 수 있는 시스템 = 화사형은 자동으로 잡힙니다</b> (역은 성립 안 함).<br><br>
            따라서 <b style="color:#ddd;">휘인 검증이 시스템의 진짜 정밀도 시험대</b>입니다.<br>
            화사는 누구나 알아보지만, 휘인을 알아보는 시스템은 진짜 천재 발굴기입니다.
        </div>
    </div>""", unsafe_allow_html=True)


# ============================================================
# 페이지 7 — 1차 모델 구조
# ============================================================

def _show_v1_structure():
    st.markdown("## 🛠 1차 모델 — 통합 파이프라인")
    st.caption("idol_scout_v1.py — 8단계 통합")

    st.markdown('<div class="section-title">🔄 8단계 파이프라인</div>', unsafe_allow_html=True)

    steps = [
        ("1", "입력 처리", "URL 또는 파일 인식"),
        ("2", "보컬 분리 (선택)", "Demucs로 보컬만 추출"),
        ("3", "MERT 임베딩 추출", "768차원 음색 지문"),
        ("4", "DDSP 5개 파라미터 분해", "F0 / Loudness / Harmonic / Noise / Envelope"),
        ("5", "100차원 시스템 매핑", "측정 가능한 차원만"),
        ("6", "Reference 비교", "휘인·비교군 있을 때"),
        ("7", "OR 극단값 판정", "양쪽 꼬리: 초우월 + 초이질"),
        ("8", "JSON 리포트 + 시각화", "자동 저장"),
    ]
    for num, title, desc in steps:
        st.markdown(f"""<div class="card" style="padding:0.7rem 1.2rem; display:flex; align-items:center; gap:1rem;">
            <span style="color:#a29bfe; font-weight:700; font-size:1.2rem;">{num}</span>
            <div style="flex:1;">
                <div style="color:#eee; font-weight:600;">{title}</div>
                <div class="detail-text">{desc}</div>
            </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")
    st.markdown('<div class="section-title">📈 진화형 설계</div>', unsafe_allow_html=True)

    evolution = [
        ("음원 0개 (지금)", "입력 1개 자동 분해 + 100차원 매핑 측정", "#636e72"),
        ("휘인 reference 도착", "휘인 거리 측정 + DDSP 4개 차원 outlier 판정", "#74b9ff"),
        ("비교군 도착", "양쪽 꼬리 자동 outlier 판정 (시스템 본격 가동)", "#00b894"),
        ("5,000명 시드 적재 (W5-6)", "상위 0.05% 자동 판정 (회사 헌법 적용)", "#a29bfe"),
    ]
    for stage, capability, color in evolution:
        st.markdown(f"""<div class="card" style="padding:0.7rem 1.2rem; border-left:3px solid {color};">
            <span style="color:{color}; font-weight:600;">{stage}</span>
            <div style="color:#eee; margin-top:0.3rem;">→ {capability}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")
    st.markdown('<div class="section-title">📋 출력 형식 (회사 헌법 정합)</div>', unsafe_allow_html=True)
    st.code("""ScreeningResult — 단일 점수 절대 없음
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
}""", language="json")
