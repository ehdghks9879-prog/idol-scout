"""
streamlit_app.py — 璞玉문화 AI 캐스팅 시스템 v1 대시보드
============================================================

목적:
    1차 모델 결과(개념도·인물 분석·검증 결과)를 인터랙티브하게 탐색.
    무거운 모델(MERT/DDSP/Demucs)은 로컬에서 사전 실행, 본 앱은 결과 표시 전용.

배포:
    GitHub repo에 본 폴더 통째로 push → Streamlit Community Cloud 자동 재배포.

회사 헌법 정합:
    - 종합 점수 표시 절대 없음
    - 차원별 독립 표시 + OR 극단값 강조
    - 양쪽 꼬리 (초우월 + 초이질) 모두 표현

작성일: 2026-05-08
"""

import json
from pathlib import Path

import streamlit as st


# ============================================================
# 설정
# ============================================================

st.set_page_config(
    page_title="璞玉문화 AI 캐스팅 v1",
    page_icon="🎤",
    layout="wide",
)

BASE_DIR = Path(__file__).parent
CONTENT_DIR = BASE_DIR / "content"
IMAGES_DIR = BASE_DIR / "images"
RESULTS_DIR = BASE_DIR / "results"

# 색상 팔레트 (4인 톤 + 휘인 강조)
COLORS = {
    "wheein": "#2a9d8f",
    "hwasa": "#e63946",
    "solar": "#f4a261",
    "moonbyul": "#264653",
}


# ============================================================
# 헬퍼
# ============================================================

def load_md(filename: str) -> str:
    """content 폴더에서 마크다운 파일 로드. 없으면 placeholder."""
    path = CONTENT_DIR / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    return f"⚠ `{filename}` 파일이 아직 준비되지 않았습니다."


def show_image_safe(filename: str, caption: str = "", width: int = None):
    """이미지 안전 표시. 없으면 placeholder 메시지."""
    path = IMAGES_DIR / filename
    if path.exists():
        if width:
            st.image(str(path), caption=caption, width=width)
        else:
            st.image(str(path), caption=caption, use_container_width=True)
    else:
        st.warning(f"이미지 미준비: `{filename}` — `images/` 폴더에 업로드 필요")


def load_json_safe(filename: str) -> dict:
    """results 폴더에서 JSON 안전 로드."""
    path = RESULTS_DIR / filename
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


# ============================================================
# 사이드바
# ============================================================

st.sidebar.title("璞玉문화 AI 캐스팅")
st.sidebar.caption("v1 — 보컬 중심 신인 발굴 시스템")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "페이지",
    [
        "🏠 프로젝트 개요",
        "📜 회사 헌법",
        "🗺 7주 로드맵",
        "📊 휘인 정밀 분석",
        "🎵 마마무 4인 톤 4사분면",
        "📈 5인 11변수 비교",
        "⚖ 화사 vs 휘인 대비",
        "🔬 W1 검증 결과",
        "🛠 1차 모델 구조",
    ],
)

st.sidebar.markdown("---")
st.sidebar.caption("📅 갱신: 2026-05-08")
st.sidebar.caption("⚠ 본 앱은 결과 표시 전용입니다.\n무거운 모델은 로컬 또는 Colab에서 실행 후 결과를 GitHub에 push하면 자동 갱신됩니다.")


# ============================================================
# 페이지 1 — 프로젝트 개요
# ============================================================

if page == "🏠 프로젝트 개요":
    st.title("🎤 璞玉문화 AI 캐스팅 시스템 v1")
    st.caption("K-POP 30년 직관 캐스팅의 한계를 AI로 돌파")

    st.markdown("""
    ## 한 줄 정의
    > **"AI가 화사 같은 보컬 천재를, 인간 캐스팅이 놓치는 영역에서 자동으로 발견하는 시스템"**
    """)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("핵심 도구", "MERT + DDSP + Annoy", "사용자 결정 우선순위")
    with col2:
        st.metric("골드 스탠다드", "휘인 (마마무)", "2026-05-08 결정")
    with col3:
        st.metric("데드라인", "2026-08-04", "v1 시스템 가동")

    st.markdown("---")

    st.subheader("AI 3대 우위")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("### 🌍 지역 무차별")
        st.caption("1선 도시든 18선 현이든 전부 훑음")
    with c2:
        st.markdown("### 🚫 편견 부재")
        st.caption("포장 아닌 본질 측정")
    with c3:
        st.markdown("### 📥 전수 스크리닝")
        st.caption("단 한 명도 놓치지 않음")

    st.markdown("---")
    st.subheader("진행 상태")
    progress_data = [
        ("Colab 노트북 + 환경 검증", "완료"),
        ("비교군 후보 + Demucs 모듈", "1차 완료"),
        ("휘인 중심 전환 일괄 수정", "완료"),
        ("휘인 단독 정밀 분석 v1.5", "완료 (검토 대기)"),
        ("시각화 모듈", "완료 (실측 검증)"),
        ("W2 (DDSP) 사전 조사 + Day 1", "완료"),
        ("1차 모델 통합 파이프라인", "완료"),
        ("RBW 음원 수령", "대기 중"),
    ]
    for task, status in progress_data:
        emoji = "✅" if "완료" in status else "⏳"
        st.write(f"{emoji} **{task}** — {status}")


# ============================================================
# 페이지 2 — 회사 헌법
# ============================================================

elif page == "📜 회사 헌법":
    st.title("📜 회사 헌법 — 절대 위반 불가")
    st.caption("모든 시스템 설계·코드·의사결정의 최상위 원칙")

    st.error("**1. 종합 점수 영구 금지**")
    st.markdown("""
    - 합산·가중평균·단일 숫자 순위 — 어떤 시스템에서도 등장 금지
    - 종합 점수 = 평균화 → 비평균적 천재성을 측정 불가능하게 만드는 도구
    - 모차르트·반 고흐·아인슈타인·잡스·권지용 — 모두 종합 점수 시스템에선 "불량품"
    """)

    st.warning("**2. OR 논리 (AND 아님)**")
    st.markdown("""
    - 후보 통과 = (플러스 차원 중 최소 하나 outlier) AND (필수 조건 전부 통과)
    - 여러 차원에서 outlier일 필요 없음 — **단 하나면 충분**
    - 권지용·제니·화사·뷔(BTS) — 모두 단일 차원 극단으로 정점 도달
    """)

    st.info("**3. 양쪽 꼬리 — 초우월 + 초이질**")
    st.markdown("""
    - 오른쪽(초우월): 너무 잘생김, 너무 잘 춤 — 식별 쉬움
    - **왼쪽(초이질)**: 이목구비 특이, 목소리 묘함 — 자주 놓침. **진짜 원석 다수가 여기**
    - AI 시스템은 양쪽 모두 잡아야 함
    """)

    st.success("**4. 100차원 통계 보정 — 상위 0.05%**")
    st.markdown("""
    - 100개 독립 차원에서 단일 차원 임계값 = 상위 0.05% (2,000명 중 1명)
    - 임계값을 0.5%로 두면 위양성 폭증 (60%+)
    - 최소 5,000명 이상 표본으로 베이스라인 구축 필요
    """)


# ============================================================
# 페이지 3 — 7주 로드맵
# ============================================================

elif page == "🗺 7주 로드맵":
    st.title("🗺 Phase 2 — 7주 로드맵")
    st.caption("MERT + DDSP + Annoy 핵심 3종 도입 흐름")

    roadmap = [
        ("W1", "MERT-v1-95M 통합 + 휘인 outlier 검증", "환경 완료, 음원 대기"),
        ("W2-3", "DDSP — 휘인 7차원 1·2·3·4번 정량화", "사전 조사 완료, Day 1 환경"),
        ("W4", "Demucs — 더우인/유튜브 보컬 자동 추출", "모듈 완료, W4 가동 대기"),
        ("W5-6", "Annoy — 5,000명 시드 임베딩 인덱스", "사전 설계 단계"),
        ("W7+", "100차원 시스템 재정렬 + 실전 캐스팅", "대기"),
    ]

    for week, task, status in roadmap:
        with st.expander(f"**{week}** — {task}"):
            st.markdown(f"**상태**: {status}")
            if week == "W1":
                st.markdown("""
                - **3가지 검증 가설**
                  - H1: 휘인이 비교군 50명 대비 outlier 분리 (정밀도 시험대)
                  - H2: 마마무 4인이 4클러스터로 자연 분리 (톤 4사분면)
                  - H3: 임베딩 어느 레이어에서 outlier 신호 강한가
                """)
            elif week == "W2-3":
                st.markdown("""
                - DDSP 5개 파라미터 (F0/Loudness/Harmonic/Noise/SpectralEnvelope)
                - 휘인 7차원 매핑: **4개 정량 측정 가능** + 부분 2개 / 1개 불가
                """)


# ============================================================
# 페이지 4 — 휘인 정밀 분석
# ============================================================

elif page == "📊 휘인 정밀 분석":
    st.title("📊 휘인 정밀 분석 v1.5")
    st.caption("골드 스탠다드 — 시스템 정밀도의 진짜 시험대")

    st.markdown("""
    > **"휘인은 화사 같은 명백한 outlier가 아니라, 가벼운 성대 운용 · 비강 공명 · R&B 친화도 · 절제된 표현이 결합된 '섬세한 정점'으로서, 인간 캐스팅이 가장 놓치기 쉬운 유형이며 따라서 AI 정밀 측정 시스템의 진짜 가치를 증명할 수 있는 정답지다."**
    """)

    st.markdown("---")
    st.subheader("7차원 Outlier 분해 (1차 가설)")

    seven_dim = [
        ("1. 성대 운용", "가벼움", "K-POP 메인보컬 대부분 두꺼운 흉성 추구. 가벼운 운용은 소수", "DDSP 측정 가능"),
        ("2. 공명 패턴", "가슴+비강 균형", "한국 트레이닝은 흉성/두성 위주. 비강 절제는 드뭄", "DDSP 측정 가능"),
        ("3. 음색 텍스처", "맑음+살짝 허스키", "두 조합 동시 충족 매우 드물다", "MERT+DDSP"),
        ("4. 다이내믹 처리", "점진적 빌드업", "한국은 \"터트리는\" 폭발 강조. 점진적은 반대 정점", "DDSP"),
        ("5. 딕션 미학", "흐림의 미학", "K-POP은 명료성 추구. 휘인은 흐림이 정점", "부분 측정"),
        ("6. 감정 표현", "절제·내향성", "무대 보컬은 외향성. 휘인은 내향성 정점", "인간 평가 필수"),
        ("7. R&B 친화도", "한국어로 자연스러운 그루브", "일반적으로 어색한 영역", "부분 측정"),
    ]

    for dim, position, rarity, measure in seven_dim:
        with st.expander(f"**{dim}** — {position}"):
            st.markdown(f"**희소성**: {rarity}")
            st.markdown(f"**측정 도구**: {measure}")

    st.markdown("---")
    st.subheader("11변수 매핑 — 다른 인물들과 비교")

    st.markdown("""
    | 변수 | 휘인 수준 | 비고 |
    |------|---------|------|
    | SDI (감각 식별도) | 중상 | 음색 강함, 비주얼 보통 |
    | **EDT (표현 변형)** | **상** | ad-lib 즉흥 변주 정점 |
    | CER (카메라-에너지) | 중상 (활용형) | 자연스러운 활용 |
    | **RMC (리듬-동작)** | **상** | R&B 비트 후행 |
    | AAC (자기 미학) | 중상~상 | R&B 자기 미학 일관 |
    | SCA (자기 교정) | 중상 (추정) | 정밀 정보 부족 |
    | **CDR (교차 차원)** | **중상** | 수렴형 (보컬 영역) |
    | **EDI (에너지)** | **+0.5~0.7 (흡인형)** | 제니와 같은 카테고리 |
    | NVC (비음악 가치) | 중상 | 그림·패션 등 |
    | CCI (문화 코드) | 중상~상 | 한국어+R&B 자연 결합 |
    | CBP (카테고리 경계) | 중상 | 그룹→솔로→다영역 |
    """)

    st.success("""
    **핵심 인사이트**: 휘인 = 제니 모델의 보컬 특화 버전.
    수렴형 식별도 + 흡인형 EDI + 중상 NVC/CCI/CBP — 제니와 같은 구조적 카테고리.
    제니가 비주얼·라이프스타일 영역 수렴이라면, **휘인은 보컬 영역 수렴**.
    """)


# ============================================================
# 페이지 5 — 마마무 4인 톤 4사분면
# ============================================================

elif page == "🎵 마마무 4인 톤 4사분면":
    st.title("🎵 마마무 4인 — 톤 4사분면 균형")

    show_image_safe("concept_4member_tone.png", "톤 4사분면 — 휘인 강조 (점선)")

    st.markdown("---")

    cols = st.columns(4)
    members = [
        ("솔라", "청량", "메탈릭 광택, 후렴 고음 폭발", COLORS["solar"]),
        ("휘인", "따뜻", "허스키, 속삭임, R&B/브릿지 강자", COLORS["wheein"]),
        ("화사", "묵직", "흉성 무게, 캐릭터 보이스", COLORS["hwasa"]),
        ("문별", "건조", "보이쉬, 저음 화음 받침", COLORS["moonbyul"]),
    ]
    for col, (name, tone, desc, color) in zip(cols, members):
        with col:
            st.markdown(f"<h3 style='color:{color}'>{name}</h3>", unsafe_allow_html=True)
            st.caption(f"**{tone}**")
            st.write(desc)


# ============================================================
# 페이지 6 — 5인 11변수 비교
# ============================================================

elif page == "📈 5인 11변수 비교":
    st.title("📈 5인 11변수 레이더")
    st.caption("권지용 · 제니 · 공민지 · 전소미 · 휘인")

    show_image_safe("concept_11var_radar.png", "11변수 비교 — 휘인 강조 (굵은 청록)")

    st.markdown("---")
    st.subheader("식별도 유형 분류")

    st.markdown("""
    | 인물 | 유형 | 영역 |
    |------|------|------|
    | 권지용 | 이탈형 | 기존 DB와의 거리 |
    | 제니 | 수렴형 | 럭셔리+힙합+걸크러시 |
    | **휘인** | **수렴형 (보컬)** | **맑음+허스키+R&B+절제** |
    | 공민지 | 단일 차원 | 퍼포먼스 편중 |
    | 전소미 | 비돌출 분산 | — |
    """)


# ============================================================
# 페이지 7 — 화사 vs 휘인 대비
# ============================================================

elif page == "⚖ 화사 vs 휘인 대비":
    st.title("⚖ 화사 vs 휘인 — 같은 그룹 안 정반대 정점")

    show_image_safe("concept_hwasa_vs_wheein.png", "강한 정점 vs 섬세한 정점")

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"<h3 style='color:{COLORS['hwasa']}'>화사 — 강한 정점</h3>", unsafe_allow_html=True)
        st.markdown("""
        - 7차원 모두 명백한 outlier
        - 캐스팅 단계 즉시 식별 가능
        - 큰 소리·강한 음역에서 빛남
        - 무대 영상 1개로 충분
        - **인간 캐스팅이 잘 잡는 영역**
        """)
    with col2:
        st.markdown(f"<h3 style='color:{COLORS['wheein']}'>휘인 — 섬세한 정점</h3>", unsafe_allow_html=True)
        st.markdown("""
        - 미묘한 정점 (단일 차원만 보면 평범)
        - 캐스팅 단계에서 자주 묻힘
        - 작은 소리·미세 디테일에서 빛남
        - 다수 영상 + 정밀 분석 필요
        - **AI 정밀 측정의 차별화 영역**
        """)

    st.info("""
    **핵심 명제**: 휘인을 잡아낼 수 있는 시스템 = 화사형은 자동으로 잡힙니다 (역은 성립 안 함).
    따라서 휘인 검증이 시스템의 진짜 정밀도 시험대입니다.
    """)


# ============================================================
# 페이지 8 — W1 검증 결과
# ============================================================

elif page == "🔬 W1 검증 결과":
    st.title("🔬 W1 검증 결과")
    st.caption("음원 도착 후 결과 JSON이 results/ 폴더에 들어가면 자동 표시")

    result = load_json_safe("w1_validation_latest.json")

    if not result:
        st.warning("⏳ 아직 검증 결과 없음")
        st.markdown("""
        ### 다음 단계
        1. RBW 음원 수령
        2. Drive `data/` 폴더에 분류 업로드
        3. Colab `colab_validation.ipynb` 실행
        4. 생성된 JSON을 GitHub `streamlit_app/results/w1_validation_latest.json`에 push
        5. 본 페이지 자동 갱신
        """)
    else:
        st.success("✓ 검증 완료")
        st.metric("MERT 모델", result.get("model", "—"))
        st.metric("골드 스탠다드", result.get("gold_standard", "—"))

        h1 = result.get("h1_wheein_outlier", {})
        if h1:
            st.markdown("---")
            st.subheader("H1: 휘인 outlier 분리")
            verdict = h1.get("verdict", "—")
            color = "success" if verdict == "PASS" else "error"
            getattr(st, color)(f"**판정: {verdict}**")
            c1, c2, c3 = st.columns(3)
            c1.metric("휘인 outlier 비율", f"{h1.get('wheein_outlier_rate', 0):.1%}")
            c2.metric("비교군 99분위", f"{h1.get('baseline_dist_99', 0):.2f}")
            c3.metric("휘인 평균 거리", f"{h1.get('wheein_dist_mean', 0):.2f}")

        h2 = result.get("h2_mamamoo_clustering", {})
        if h2:
            st.markdown("---")
            st.subheader("H2: 마마무 4인 톤 분리")
            verdict = h2.get("verdict", "—")
            if verdict == "PASS":
                st.success(f"**판정: {verdict}**")
            elif verdict == "PARTIAL":
                st.warning(f"**판정: {verdict}**")
            else:
                st.error(f"**판정: {verdict}**")
            c1, c2 = st.columns(2)
            c1.metric("Cluster Purity", f"{h2.get('cluster_purity', 0):.2%}")
            c2.metric("Silhouette", f"{h2.get('silhouette_score', 0):.3f}")


# ============================================================
# 페이지 9 — 1차 모델 구조
# ============================================================

elif page == "🛠 1차 모델 구조":
    st.title("🛠 1차 모델 — 통합 파이프라인 구조")
    st.caption("idol_scout_v1.py — 8단계 통합")

    st.code("""
음원 입력 (URL or 파일)
   ↓
[1] 입력 처리
[2] (선택) 보컬 분리 (Demucs)
[3] MERT 임베딩 추출 (768차원)
[4] DDSP 5개 파라미터 분해
[5] 100차원 시스템 매핑 (가능한 차원만)
[6] Reference 비교 (휘인·비교군 있을 때)
[7] OR 극단값 판정 (양쪽 꼬리)
[8] JSON 리포트 + 시각화 자동 저장
   ↓
ScreeningResult 출력
    """, language="text")

    st.markdown("---")
    st.subheader("진화형 설계 — 데이터 누적에 따른 정밀화")

    evolution = [
        ("음원 0개 (지금)", "입력 1개 자동 분해 + 100차원 매핑 측정"),
        ("휘인 reference 도착", "휘인 거리 측정 + DDSP 4개 차원 outlier 판정"),
        ("비교군 도착", "양쪽 꼬리 자동 outlier 판정 (시스템 본격 가동)"),
        ("5,000명 시드 적재 (W5-6)", "상위 0.05% 자동 판정 (회사 헌법 적용)"),
    ]
    for stage, capability in evolution:
        st.markdown(f"- **{stage}** → {capability}")

    st.markdown("---")
    st.subheader("출력 형식 (회사 헌법 정합)")
    st.code("""
ScreeningResult — 단일 점수 절대 없음
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
}
    """, language="json")


# ============================================================
# 푸터
# ============================================================

st.markdown("---")
st.caption("璞玉문화 (PUYU Entertainment) — 본 앱은 회사 헌법(종합점수 금지·OR 논리·양쪽 꼬리·상위 0.05%)에 따라 설계됨")
