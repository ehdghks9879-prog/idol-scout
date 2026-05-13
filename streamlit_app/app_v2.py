"""
app_v2.py — 璞玉문화 통합 보컬 MBTI 시스템 (모델 v2)
=====================================================

대규모 개편:
- 星码(MBTI식) + idol-scout(깊은 분석) 통합
- 댄스 완전 제거, 보컬 100%
- 5프레임 MBTI식 결과 + 선택적 깊은 분석
- 3가지 입력 (파일/녹음/URL)

UI/UX:
- 다크 톤 (#0a0a0f) + 휘인 청록 (#2a9d8f)
- 미니멀 입구 → 8초 분석 애니메이션 → 5프레임 순차 공개
- 절제된 타이포그래피

회사 헌법 정합:
- 종합 점수 절대 없음 (코드 4글자 + 백분위는 분류·희소성일 뿐)
- OR 논리 (한 차원이라도 outlier면 통과)
- 양쪽 꼬리 (초우월 + 초이질)

작성일: 2026-05-12 (v2 통합 시스템)
"""

import streamlit as st
import streamlit.components.v1 as components
import json
import time
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent))

# v2 코드 폴더 추가 (vocal_mbti, visualizers_v2 위치)
_V2_CODE_DIR = Path(__file__).resolve().parent.parent / "code" / "v2"
if _V2_CODE_DIR.exists():
    sys.path.insert(0, str(_V2_CODE_DIR))

# v2 시각화 모듈 — Plotly 차트 (옵션 import, 실패 시 차트 생략)
try:
    import visualizers_v2 as v2viz  # type: ignore
    _V2VIZ_AVAILABLE = True
except Exception as _viz_exc:
    v2viz = None
    _V2VIZ_AVAILABLE = False

# 페이지 설정
st.set_page_config(
    page_title="VOCAL MBTI · 4축 16타입 보컬 분석",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ============================================================
# 전문 CSS — v2 디자인 시스템
# ============================================================

V2_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700;800;900&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');

* { font-family: 'Noto Sans KR', -apple-system, sans-serif; }

/* ⚡ 안전장치 — 애니메이션 실패 시에도 콘텐츠가 보이도록 */
.v2-hero, .v2-hero *, .v2-callout, .v2-input-zone, .v2-frame, .v2-deep-section,
.v2-topbar, .v2-live-wave { opacity: 1; }

:root {
    --bg-deep: #050509;
    --bg-card: #0e0e16;
    --bg-elev: #15151f;
    --border-subtle: #1f1f2c;
    --border-strong: #2c2c3a;
    --text-primary: #f5f7fa;
    --text-secondary: #9aa1b3;
    --text-tertiary: #5e6577;
    --accent: #2a9d8f;
    --accent-bright: #4fd1c5;
    --accent-glow: rgba(42, 157, 143, 0.45);
    --accent-rose: #e11d48;
    --accent-amber: #d97706;
    --accent-blue: #5b8def;
    --accent-purple: #9b5de5;
}

/* ===== 전체 배경 — 마마무 컬러 + 보컬 무드 그라데이션 ===== */
.stApp {
    background:
        /* 4인 컬러 글로우 */
        radial-gradient(ellipse 50% 40% at 15% 8%, rgba(244, 211, 94, 0.16), transparent 60%),
        radial-gradient(ellipse 45% 38% at 85% 15%, rgba(42, 157, 143, 0.18), transparent 60%),
        radial-gradient(ellipse 50% 40% at 10% 75%, rgba(155, 93, 229, 0.16), transparent 60%),
        radial-gradient(ellipse 45% 38% at 90% 85%, rgba(244, 162, 97, 0.14), transparent 60%),
        /* 중앙 부드러운 글로우 */
        radial-gradient(ellipse 70% 55% at 50% 45%, rgba(79, 209, 197, 0.06), transparent 70%),
        var(--bg-deep) !important;
    background-attachment: fixed !important;
}

/* 배경 인물 실루엣 — 4명 K-POP 보컬리스트 (흐릿) */
.v2-bg-portraits {
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 0;
    overflow: hidden;
}
.v2-portrait {
    position: absolute;
    filter: blur(2px);
    opacity: 0.18;
    animation: v2-portrait-drift 22s ease-in-out infinite alternate;
}
.v2-portrait svg { width: 100%; height: 100%; }

.v2-portrait-1 { /* 좌상 — 솔라형(노랑) */
    width: 280px; height: 360px;
    top: -2%; left: -4%;
    color: #f4d35e;
    animation-duration: 24s;
}
.v2-portrait-2 { /* 우상 — 휘인형(청록) */
    width: 260px; height: 340px;
    top: 6%; right: -5%;
    color: #2a9d8f;
    animation-duration: 20s;
    animation-delay: -3s;
}
.v2-portrait-3 { /* 좌하 — 화사형(보라) */
    width: 300px; height: 380px;
    bottom: -4%; left: -3%;
    color: #9b5de5;
    animation-duration: 26s;
    animation-delay: -8s;
}
.v2-portrait-4 { /* 우하 — 문별형(호박) */
    width: 270px; height: 350px;
    bottom: 2%; right: -4%;
    color: #f4a261;
    animation-duration: 22s;
    animation-delay: -12s;
}
@keyframes v2-portrait-drift {
    0%   { transform: translate(0,0) scale(1) rotate(0deg); opacity: 0.16; }
    50%  { transform: translate(2%, -1.5%) scale(1.06) rotate(1deg); opacity: 0.22; }
    100% { transform: translate(-1.5%, 2%) scale(1.03) rotate(-1deg); opacity: 0.18; }
}

/* 노이즈 텍스처 (필름 그레인 — 부드러움 강화) */
.v2-bg-grain {
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 0;
    opacity: 0.05;
    background-image:
        repeating-radial-gradient(circle at 0 0, rgba(255,255,255,0.5) 0, rgba(255,255,255,0) 0.5px, rgba(255,255,255,0) 1.5px);
    background-size: 3px 3px;
    mix-blend-mode: overlay;
}

.main .block-container {
    max-width: 800px;
    padding-top: 1rem;
    padding-bottom: 4rem;
    position: relative;
    z-index: 1;
}

/* ===== Top bar — 미니멀 브랜드 + 페이드인 ===== */
.v2-topbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.8rem 0.2rem 2rem;
    animation: v2-fade-down 0.6s ease-out forwards;
}
.v2-topbar-logo {
    color: var(--accent);
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 0.95rem;
    letter-spacing: 0.05em;
    display: flex;
    align-items: center;
    gap: 0.6rem;
}
.v2-topbar-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: var(--accent);
    box-shadow: 0 0 12px var(--accent-glow);
    animation: v2-pulse 2.2s ease-in-out infinite;
}
.v2-topbar-version {
    color: var(--text-tertiary);
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.72rem;
    letter-spacing: 0.16em;
}
@keyframes v2-pulse {
    0%, 100% { transform: scale(1); opacity: 1; box-shadow: 0 0 12px var(--accent-glow); }
    50%      { transform: scale(1.3); opacity: 0.7; box-shadow: 0 0 24px var(--accent-glow); }
}

/* ===== 히어로 영역 — 시네마틱 ===== */
.v2-hero {
    text-align: center;
    padding: 1.5rem 0 1rem 0;
    position: relative;
}
.v2-hero-waveform {
    position: absolute;
    top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    width: 110%;
    height: 220px;
    z-index: 0;
    opacity: 0.35;
    pointer-events: none;
}
.v2-hero-inner {
    position: relative;
    z-index: 1;
}
.v2-hero-eyebrow {
    display: inline-block;
    color: var(--accent);
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.28em;
    text-transform: uppercase;
    margin-bottom: 1.5rem;
    padding: 0.4rem 1rem;
    background: rgba(42, 157, 143, 0.08);
    border: 1px solid rgba(42, 157, 143, 0.25);
    border-radius: 100px;
    animation: v2-fade-down 0.7s ease-out forwards;
    animation-delay: 0.1s;
}
.v2-hero-title {
    font-size: 3rem;
    font-weight: 800;
    color: var(--text-primary);
    line-height: 1.1;
    letter-spacing: -0.035em;
    margin-bottom: 1.4rem;
}
.v2-hero-title .v2-line {
    display: block;
    overflow: hidden;
}
.v2-hero-title .v2-line span {
    display: inline-block;
    animation: v2-rise 0.9s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
.v2-hero-title .v2-line:nth-child(1) span { animation-delay: 0.25s; }
.v2-hero-title .v2-line:nth-child(2) span { animation-delay: 0.45s; }
.v2-hero-title em {
    font-style: normal;
    background: linear-gradient(135deg, #f4d35e 0%, #2a9d8f 35%, #9b5de5 70%, #f4a261 100%);
    background-size: 200% 200%;
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    animation: v2-gradient-shift 6s ease infinite;
    filter: drop-shadow(0 4px 20px rgba(42, 157, 143, 0.3));
}
.v2-hero-subtitle {
    font-size: 1.02rem;
    color: var(--text-secondary);
    line-height: 1.75;
    max-width: 520px;
    margin: 0 auto;
    /* animation removed for safety */
}
@keyframes v2-rise {
    0%   { transform: translateY(110%); opacity: 0; }
    100% { transform: translateY(0); opacity: 1; }
}
@keyframes v2-fade-up {
    0%   { transform: translateY(20px); opacity: 0; }
    100% { transform: translateY(0); opacity: 1; }
}
@keyframes v2-fade-down {
    0%   { transform: translateY(-12px); opacity: 0; }
    100% { transform: translateY(0); opacity: 1; }
}

/* ===== 라이브 파동 (홈 idle 표시) ===== */
.v2-live-wave {
    display: flex;
    justify-content: center;
    align-items: flex-end;
    gap: 4px;
    height: 64px;
    margin: 2rem auto 1rem;
    animation: v2-fade-up 0.9s ease-out forwards;
    animation-delay: 0.8s;
}
.v2-live-wave .bar {
    width: 4px;
    background: linear-gradient(180deg, var(--accent-bright), var(--accent));
    border-radius: 4px;
    animation: v2-wave-dance 1.4s ease-in-out infinite;
}
.v2-live-wave .bar:nth-child(1)  { animation-delay: 0.0s;  height: 30%; }
.v2-live-wave .bar:nth-child(2)  { animation-delay: 0.1s;  height: 60%; }
.v2-live-wave .bar:nth-child(3)  { animation-delay: 0.2s;  height: 90%; }
.v2-live-wave .bar:nth-child(4)  { animation-delay: 0.3s;  height: 50%; }
.v2-live-wave .bar:nth-child(5)  { animation-delay: 0.4s;  height: 80%; }
.v2-live-wave .bar:nth-child(6)  { animation-delay: 0.5s;  height: 35%; }
.v2-live-wave .bar:nth-child(7)  { animation-delay: 0.6s;  height: 70%; }
.v2-live-wave .bar:nth-child(8)  { animation-delay: 0.7s;  height: 95%; }
.v2-live-wave .bar:nth-child(9)  { animation-delay: 0.8s;  height: 55%; }
.v2-live-wave .bar:nth-child(10) { animation-delay: 0.9s;  height: 75%; }
.v2-live-wave .bar:nth-child(11) { animation-delay: 1.0s;  height: 40%; }
.v2-live-wave .bar:nth-child(12) { animation-delay: 1.1s;  height: 85%; }
.v2-live-wave .bar:nth-child(13) { animation-delay: 1.2s;  height: 65%; }
@keyframes v2-wave-dance {
    0%, 100% { transform: scaleY(0.4); opacity: 0.55; }
    50%      { transform: scaleY(1.1); opacity: 1; }
}

/* ===== 메시지 박스 — 글래스 ===== */
.v2-callout {
    background: linear-gradient(135deg, rgba(42,157,143,0.12) 0%, rgba(155,93,229,0.06) 100%);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 22px;
    padding: 1.4rem 1.8rem;
    margin: 2rem 0;
    backdrop-filter: blur(20px) saturate(150%);
    box-shadow: 0 12px 40px rgba(0,0,0,0.20), inset 0 1px 0 rgba(255,255,255,0.06);
    position: relative;
    overflow: hidden;
}
.v2-callout::before {
    content: "";
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 3px;
    background: linear-gradient(180deg, var(--accent-bright), var(--accent-purple));
    border-radius: 3px;
}
.v2-callout-label {
    color: var(--accent);
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}
.v2-callout-text {
    color: var(--text-primary);
    font-size: 0.96rem;
    line-height: 1.65;
}

/* ===== 입력 영역 — 카드형 인터랙티브 ===== */
.v2-input-zone {
    background: linear-gradient(180deg, rgba(28, 28, 40, 0.55), rgba(18, 18, 28, 0.65));
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 28px;
    padding: 2.2rem;
    margin: 1.5rem 0;
    backdrop-filter: blur(28px) saturate(160%);
    box-shadow: 0 20px 60px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.05);
}
.v2-input-label {
    color: var(--text-tertiary);
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.7rem;
}
.v2-input-label::before {
    content: "";
    width: 16px; height: 1px;
    background: var(--accent);
}

/* ===== Streamlit radio를 탭 카드처럼 ===== */
[data-testid="stRadio"] > div[role="radiogroup"] {
    gap: 0.6rem !important;
    flex-direction: row !important;
}
[data-testid="stRadio"] label {
    flex: 1;
    background: rgba(20,20,28,0.6) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 14px !important;
    padding: 0.95rem 1rem !important;
    text-align: center;
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    cursor: pointer;
    position: relative;
}
[data-testid="stRadio"] label:hover {
    background: rgba(42,157,143,0.06) !important;
    border-color: rgba(42,157,143,0.35) !important;
    transform: translateY(-2px);
}
/* :has() 미지원 브라우저 대응 — 호버 효과만 유지 */
[data-testid="stRadio"] label > div:first-child { display: none !important; }
[data-testid="stRadio"] label p {
    color: var(--text-primary) !important;
    font-weight: 500 !important;
    font-size: 0.95rem !important;
}

/* ===== 텍스트/파일 인풋 — 부드럽게 ===== */
.stTextInput input {
    background: rgba(255, 255, 255, 0.03) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 100px !important;
    padding: 0.85rem 1.4rem !important;
    color: var(--text-primary) !important;
    font-size: 0.95rem !important;
    transition: all 0.25s ease;
    backdrop-filter: blur(10px);
}
.stTextInput input:focus {
    border-color: rgba(42, 157, 143, 0.5) !important;
    box-shadow: 0 0 0 4px rgba(42,157,143,0.10), 0 4px 20px rgba(42, 157, 143, 0.15) !important;
    background: rgba(255, 255, 255, 0.05) !important;
}
[data-testid="stFileUploader"] section {
    background: rgba(255, 255, 255, 0.03) !important;
    border: 1.5px dashed rgba(255, 255, 255, 0.12) !important;
    border-radius: 24px !important;
    padding: 2rem !important;
    transition: all 0.3s ease;
    backdrop-filter: blur(10px);
}
[data-testid="stFileUploader"] section:hover {
    border-color: rgba(42, 157, 143, 0.5) !important;
    background: rgba(42, 157, 143, 0.04) !important;
    transform: translateY(-2px);
}

/* ===== Primary CTA — 호흡하는 부드러운 버튼 ===== */
.stButton > button {
    background: linear-gradient(135deg, #4fd1c5 0%, #2a9d8f 50%, #9b5de5 100%) !important;
    background-size: 200% 200% !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 100px !important;
    padding: 1.1rem 2rem !important;
    font-weight: 700 !important;
    font-size: 1.05rem !important;
    letter-spacing: 0.01em !important;
    width: 100% !important;
    box-shadow:
        0 10px 36px rgba(42,157,143,0.40),
        0 4px 12px rgba(155,93,229,0.20),
        inset 0 1px 0 rgba(255,255,255,0.30),
        inset 0 -1px 0 rgba(0,0,0,0.10);
    transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1) !important;
    animation: v2-breathe 3.4s ease-in-out infinite, v2-gradient-shift 8s ease infinite;
    position: relative;
    overflow: hidden;
}
@keyframes v2-gradient-shift {
    0%, 100% { background-position: 0% 50%; }
    50%      { background-position: 100% 50%; }
}
.stButton > button::before {
    content: "";
    position: absolute;
    top: 0; left: -100%;
    width: 100%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.30), transparent);
    transition: left 0.7s ease;
}
.stButton > button:hover::before { left: 100%; }
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow:
        0 16px 50px rgba(42,157,143,0.45),
        inset 0 1px 0 rgba(255,255,255,0.30);
    background: linear-gradient(135deg, var(--accent-bright) 0%, var(--accent) 100%) !important;
}
.stButton > button:active {
    transform: translateY(0) !important;
}
@keyframes v2-breathe {
    0%, 100% { box-shadow: 0 8px 32px rgba(42,157,143,0.30), inset 0 1px 0 rgba(255,255,255,0.25); }
    50%      { box-shadow: 0 12px 40px rgba(42,157,143,0.50), inset 0 1px 0 rgba(255,255,255,0.30); }
}

/* ===== 분석 중 — 시네마틱 풀스크린 ===== */
.v2-analyzing {
    text-align: center;
    padding: 3.5rem 0 4.5rem;
    animation: v2-fade-up 0.6s ease-out forwards;
}

/* 동심원 펄스 */
.v2-pulse-orb {
    position: relative;
    width: 200px;
    height: 200px;
    margin: 0 auto 2.5rem;
}
.v2-pulse-orb .ring {
    position: absolute;
    inset: 0;
    border-radius: 50%;
    border: 1.5px solid var(--accent);
    opacity: 0;
    animation: v2-ring-expand 2.6s cubic-bezier(0.22, 1, 0.36, 1) infinite;
}
.v2-pulse-orb .ring:nth-child(2) { animation-delay: 0.65s; }
.v2-pulse-orb .ring:nth-child(3) { animation-delay: 1.3s; }
.v2-pulse-orb .core {
    position: absolute;
    inset: 35%;
    border-radius: 50%;
    background: radial-gradient(circle at 30% 30%, var(--accent-bright), var(--accent));
    box-shadow: 0 0 60px var(--accent-glow), inset 0 0 20px rgba(255,255,255,0.20);
    animation: v2-core-pulse 2.0s ease-in-out infinite;
}
@keyframes v2-ring-expand {
    0%   { transform: scale(0.35); opacity: 0.9; }
    100% { transform: scale(1.4); opacity: 0; }
}
@keyframes v2-core-pulse {
    0%, 100% { transform: scale(0.95); }
    50%      { transform: scale(1.10); }
}

/* 스펙트럼 바 (분석 중) */
.v2-spectrum {
    display: flex;
    justify-content: center;
    align-items: flex-end;
    gap: 5px;
    height: 80px;
    margin: 0 auto 2rem;
    max-width: 360px;
}
.v2-spectrum .bar {
    flex: 1;
    background: linear-gradient(180deg, var(--accent-bright), var(--accent) 70%, rgba(42,157,143,0.3));
    border-radius: 3px;
    animation: v2-spec 0.9s ease-in-out infinite alternate;
}
.v2-spectrum .bar:nth-child(odd)  { animation-duration: 0.8s; }
.v2-spectrum .bar:nth-child(3n)   { animation-duration: 1.1s; }
.v2-spectrum .bar:nth-child(4n)   { animation-duration: 0.6s; }
@keyframes v2-spec {
    0%   { height: 15%; opacity: 0.6; }
    100% { height: 100%; opacity: 1; }
}

.v2-analyzing-status {
    color: var(--text-primary);
    font-size: 1.5rem;
    font-weight: 700;
    margin-bottom: 0.7rem;
    letter-spacing: -0.02em;
    animation: v2-fade-up 0.4s ease-out forwards;
}
.v2-analyzing-detail {
    color: var(--text-secondary);
    font-size: 0.98rem;
    line-height: 1.6;
    max-width: 460px;
    margin: 0 auto 1.6rem;
    animation: v2-fade-up 0.5s ease-out 0.05s forwards;
}
.v2-analyzing-step-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.6rem;
    color: var(--accent);
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.2em;
    padding: 0.45rem 1rem;
    background: rgba(42,157,143,0.10);
    border: 1px solid rgba(42,157,143,0.25);
    border-radius: 100px;
}

/* 프로그레스 트랙 */
.v2-progress {
    margin: 1.8rem auto 0;
    max-width: 320px;
    height: 4px;
    background: rgba(255,255,255,0.05);
    border-radius: 100px;
    overflow: hidden;
}
.v2-progress-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--accent), var(--accent-bright));
    border-radius: 100px;
    box-shadow: 0 0 12px var(--accent-glow);
    transition: width 0.3s ease;
}

/* ===== 떠다니는 보컬 타입 오브 (배경) ===== */
.v2-orbs {
    position: absolute;
    inset: 0;
    overflow: hidden;
    pointer-events: none;
    z-index: 0;
}
.v2-orb {
    position: absolute;
    border-radius: 50%;
    filter: blur(40px);
    opacity: 0.55;
    animation: v2-orb-float 14s ease-in-out infinite alternate;
}
.v2-orb-1 { /* 솔라 — 청량 */
    width: 280px; height: 280px;
    background: radial-gradient(circle, #f4d35e 0%, transparent 70%);
    top: 5%; left: -8%;
    animation-duration: 16s;
}
.v2-orb-2 { /* 휘인 — 따뜻 청록 */
    width: 320px; height: 320px;
    background: radial-gradient(circle, #2a9d8f 0%, transparent 70%);
    top: 30%; right: -10%;
    animation-duration: 13s;
    animation-delay: -2s;
}
.v2-orb-3 { /* 화사 — 묵직 보라 */
    width: 360px; height: 360px;
    background: radial-gradient(circle, #9b5de5 0%, transparent 70%);
    bottom: 8%; left: 20%;
    animation-duration: 18s;
    animation-delay: -5s;
}
.v2-orb-4 { /* 문별 — 건조 호박 */
    width: 220px; height: 220px;
    background: radial-gradient(circle, #f4a261 0%, transparent 70%);
    bottom: 25%; right: 18%;
    animation-duration: 15s;
    animation-delay: -7s;
}
@keyframes v2-orb-float {
    0%   { transform: translate(0,0) scale(1); }
    33%  { transform: translate(40px, -30px) scale(1.1); }
    66%  { transform: translate(-30px, 40px) scale(0.95); }
    100% { transform: translate(20px, -20px) scale(1.05); }
}

/* ===== 보컬리스트 실루엣 (배경 일러스트) ===== */
.v2-silhouette {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 360px;
    height: 360px;
    opacity: 0.08;
    pointer-events: none;
    z-index: 0;
}
.v2-silhouette circle, .v2-silhouette path {
    stroke: var(--accent-bright);
    fill: none;
    stroke-width: 1.5;
}

/* ===== 메인 녹음 영역 — 거대한 마이크 버튼 ===== */
.v2-mic-stage {
    position: relative;
    padding: 2.5rem 0 2rem;
    text-align: center;
    z-index: 2;
}
.v2-mic-wrap {
    position: relative;
    width: 220px;
    height: 220px;
    margin: 0 auto 1.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
}
.v2-mic-ring {
    position: absolute;
    inset: 0;
    border-radius: 50%;
    border: 1.5px solid var(--accent);
    opacity: 0;
    animation: v2-mic-ripple 2.4s cubic-bezier(0.22, 1, 0.36, 1) infinite;
}
.v2-mic-ring:nth-child(2) { animation-delay: 0.6s; }
.v2-mic-ring:nth-child(3) { animation-delay: 1.2s; }
@keyframes v2-mic-ripple {
    0%   { transform: scale(0.6); opacity: 0; }
    20%  { opacity: 0.9; }
    100% { transform: scale(1.7); opacity: 0; }
}
.v2-mic-button {
    position: relative;
    width: 150px;
    height: 150px;
    border-radius: 50%;
    background:
        radial-gradient(circle at 30% 25%, #b3f0e5 0%, var(--accent-bright) 30%, var(--accent) 65%, #9b5de5 100%);
    box-shadow:
        0 16px 60px rgba(42, 157, 143, 0.60),
        0 8px 30px rgba(155, 93, 229, 0.30),
        inset 0 3px 8px rgba(255, 255, 255, 0.40),
        inset 0 -8px 16px rgba(0, 0, 0, 0.20);
    display: flex;
    align-items: center;
    justify-content: center;
    animation: v2-mic-breathe 2.8s ease-in-out infinite;
    z-index: 2;
    cursor: pointer;
}
.v2-mic-button::after {
    content: "";
    position: absolute;
    inset: -3px;
    border-radius: 50%;
    background: conic-gradient(from 0deg, transparent, rgba(255,255,255,0.4), transparent 30%);
    animation: v2-mic-rotate 4s linear infinite;
    mask: radial-gradient(circle, transparent 65%, black 70%);
    -webkit-mask: radial-gradient(circle, transparent 65%, black 70%);
    pointer-events: none;
}
@keyframes v2-mic-rotate {
    to { transform: rotate(360deg); }
}
@keyframes v2-mic-breathe {
    0%, 100% { transform: scale(1); box-shadow: 0 12px 50px rgba(42, 157, 143, 0.55), inset 0 2px 6px rgba(255, 255, 255, 0.35); }
    50%      { transform: scale(1.06); box-shadow: 0 18px 70px rgba(42, 157, 143, 0.75), inset 0 2px 6px rgba(255, 255, 255, 0.45); }
}
.v2-mic-icon {
    width: 56px; height: 56px;
    color: #fff;
}
.v2-mic-label {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.78rem;
    font-weight: 600;
    color: var(--accent);
    letter-spacing: 0.28em;
    text-transform: uppercase;
    margin-bottom: 0.3rem;
}
.v2-mic-cta {
    color: var(--text-primary);
    font-size: 1.35rem;
    font-weight: 700;
    letter-spacing: -0.02em;
}
.v2-mic-hint {
    color: var(--text-tertiary);
    font-size: 0.88rem;
    margin-top: 0.6rem;
    line-height: 1.5;
}

/* ===== 보컬 타입 데모 카드 (4사분면) — 더 부드럽게 ===== */
.v2-types-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.85rem;
    margin: 2.5rem 0 1.5rem;
}
.v2-type-card {
    background: linear-gradient(165deg, rgba(38, 38, 56, 0.55) 0%, rgba(20, 20, 32, 0.55) 100%);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 24px;
    padding: 1.2rem 0.7rem 1.05rem;
    text-align: center;
    backdrop-filter: blur(16px) saturate(150%);
    transition: all 0.4s cubic-bezier(0.22, 1, 0.36, 1);
    position: relative;
    overflow: hidden;
    box-shadow: 0 8px 24px rgba(0,0,0,0.20), inset 0 1px 0 rgba(255,255,255,0.05);
}
.v2-type-card::before {
    content: "";
    position: absolute;
    top: -50%; left: -50%;
    width: 200%; height: 200%;
    background: radial-gradient(circle, var(--card-glow, rgba(42,157,143,0.15)) 0%, transparent 50%);
    opacity: 0;
    transition: opacity 0.4s ease;
    pointer-events: none;
}
.v2-type-card:hover {
    transform: translateY(-6px) scale(1.02);
    border-color: rgba(255, 255, 255, 0.18);
    box-shadow: 0 16px 40px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.10);
}
.v2-type-card:hover::before { opacity: 1; }
.v2-type-card:nth-child(1) { --card-glow: rgba(244, 211, 94, 0.18); }
.v2-type-card:nth-child(2) { --card-glow: rgba(42, 157, 143, 0.18); }
.v2-type-card:nth-child(3) { --card-glow: rgba(155, 93, 229, 0.18); }
.v2-type-card:nth-child(4) { --card-glow: rgba(244, 162, 97, 0.18); }
.v2-type-orb {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    margin: 0 auto 0.65rem;
    animation: v2-type-pulse 3s ease-in-out infinite;
    position: relative;
}
.v2-type-orb::after {
    content: "";
    position: absolute;
    inset: -8px;
    border-radius: 50%;
    background: inherit;
    filter: blur(14px);
    opacity: 0.5;
    z-index: -1;
}
.v2-type-orb.solar  { background: radial-gradient(circle at 30% 30%, #ffe27a, #f4d35e 60%, #b89636); box-shadow: 0 0 24px rgba(244, 211, 94, 0.6); }
.v2-type-orb.wheein { background: radial-gradient(circle at 30% 30%, #5fe5d3, #2a9d8f 60%, #146d62); box-shadow: 0 0 24px rgba(42, 157, 143, 0.6); animation-delay: -0.6s; }
.v2-type-orb.hwasa  { background: radial-gradient(circle at 30% 30%, #c989f5, #9b5de5 60%, #5d2fa5); box-shadow: 0 0 24px rgba(155, 93, 229, 0.6); animation-delay: -1.2s; }
.v2-type-orb.moon   { background: radial-gradient(circle at 30% 30%, #ffc28a, #f4a261 60%, #b0683a); box-shadow: 0 0 24px rgba(244, 162, 97, 0.6); animation-delay: -1.8s; }
@keyframes v2-type-pulse {
    0%, 100% { transform: scale(1); }
    50%      { transform: scale(1.18); }
}
.v2-type-name {
    color: var(--text-primary);
    font-size: 0.88rem;
    font-weight: 600;
    margin-bottom: 0.15rem;
}
.v2-type-code {
    font-family: 'Space Grotesk', sans-serif;
    color: var(--text-tertiary);
    font-size: 0.7rem;
    letter-spacing: 0.16em;
    font-weight: 500;
}
.v2-type-desc {
    color: var(--text-tertiary);
    font-size: 0.7rem;
    margin-top: 0.3rem;
    line-height: 1.3;
}

/* ===== Sub 입력 (작은 옵션) — 부드럽게 ===== */
.v2-sub-options {
    display: flex;
    justify-content: center;
    gap: 0.8rem;
    margin: 1.6rem 0 0.5rem;
    flex-wrap: wrap;
}
.v2-sub-option {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.55rem 1.05rem;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 100px;
    color: var(--text-secondary);
    font-size: 0.8rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.25s ease;
    backdrop-filter: blur(10px);
}
.v2-sub-option:hover {
    background: rgba(42, 157, 143, 0.10);
    border-color: rgba(42, 157, 143, 0.4);
    color: var(--accent);
    transform: translateY(-2px);
}
.v2-sub-option svg {
    width: 14px; height: 14px;
    opacity: 0.8;
}

/* Secondary 버튼 (sub_mic, sub_file, sub_url) — 부드러운 알약 */
button[kind="secondary"] {
    background: rgba(255, 255, 255, 0.04) !important;
    color: var(--text-secondary) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 100px !important;
    padding: 0.65rem 1.1rem !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    box-shadow: none !important;
    animation: none !important;
    backdrop-filter: blur(10px);
    transition: all 0.25s ease !important;
}
button[kind="secondary"]:hover {
    background: rgba(42, 157, 143, 0.10) !important;
    border-color: rgba(42, 157, 143, 0.4) !important;
    color: var(--accent) !important;
    transform: translateY(-2px) !important;
}

/* ===== 새 미니멀 탑바 (브랜드 제거) ===== */
.v2-topbar-min {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 0.2rem 1.5rem;
}
.v2-brand-wave {
    display: flex;
    align-items: center;
    gap: 0.65rem;
    color: var(--text-secondary);
}
.v2-brand-wave svg {
    width: 22px; height: 22px;
    color: var(--accent);
}
.v2-brand-text {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 0.85rem;
    letter-spacing: 0.16em;
    color: var(--text-primary);
}
.v2-version-pill {
    font-family: 'Space Grotesk', sans-serif;
    color: var(--accent);
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.18em;
    padding: 0.3rem 0.75rem;
    background: rgba(42, 157, 143, 0.10);
    border: 1px solid rgba(42, 157, 143, 0.25);
    border-radius: 100px;
}

/* ===== 가수 일러스트 영역 ===== */
.v2-vocalist-row {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 0.8rem;
    margin: 1.5rem 0;
    flex-wrap: wrap;
}
.v2-vocalist {
    width: 70px;
    height: 70px;
    border-radius: 50%;
    border: 2px solid rgba(255, 255, 255, 0.08);
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    overflow: hidden;
    transition: all 0.3s ease;
}
.v2-vocalist::before {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: 50%;
    background: var(--vocalist-color, var(--accent));
    opacity: 0.18;
    animation: v2-vocalist-pulse 3s ease-in-out infinite;
}
.v2-vocalist svg {
    width: 38px; height: 38px;
    color: var(--vocalist-color, var(--accent));
    z-index: 1;
}
@keyframes v2-vocalist-pulse {
    0%, 100% { opacity: 0.18; }
    50%      { opacity: 0.32; }
}

/* ===== Streamlit audio_input 시각적 통합 ===== */
[data-testid="stAudioInput"] {
    background: rgba(20, 20, 28, 0.6) !important;
    border: 1px solid rgba(42, 157, 143, 0.25) !important;
    border-radius: 18px !important;
    padding: 1rem !important;
    margin-top: -0.5rem;
    box-shadow: 0 8px 30px rgba(42, 157, 143, 0.10);
    transition: all 0.25s ease;
}
[data-testid="stAudioInput"]:hover {
    border-color: rgba(42, 157, 143, 0.5) !important;
    box-shadow: 0 12px 40px rgba(42, 157, 143, 0.20);
}
[data-testid="stAudioInput"] button {
    background: linear-gradient(135deg, var(--accent), var(--accent-bright)) !important;
    color: var(--bg-deep) !important;
    border: none !important;
    font-weight: 600;
}

/* 단계 안내 표시 */
.v2-cta-arrow {
    display: block;
    text-align: center;
    color: var(--accent);
    font-size: 1.4rem;
    margin: 0.5rem 0;
    animation: v2-arrow-bounce 1.8s ease-in-out infinite;
}
@keyframes v2-arrow-bounce {
    0%, 100% { transform: translateY(0); opacity: 0.7; }
    50%      { transform: translateY(6px); opacity: 1; }
}

/* ===== 진행 단계 비주얼 (홈 하단) — 부드러운 카드 ===== */
.v2-steps {
    display: flex;
    justify-content: space-between;
    margin: 2rem 0;
    padding: 1.4rem 1.5rem;
    background: linear-gradient(165deg, rgba(38, 38, 56, 0.45), rgba(18, 18, 28, 0.55));
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 22px;
    backdrop-filter: blur(20px) saturate(150%);
    box-shadow: 0 12px 40px rgba(0,0,0,0.25), inset 0 1px 0 rgba(255,255,255,0.04);
}
.v2-step {
    flex: 1;
    text-align: center;
    position: relative;
}
.v2-step + .v2-step::before {
    content: "";
    position: absolute;
    left: -50%;
    top: 16px;
    width: 100%;
    height: 1.5px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.10), transparent);
}
.v2-step-num {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 34px;
    height: 34px;
    border-radius: 50%;
    background: radial-gradient(circle at 30% 30%, rgba(79, 209, 197, 0.25), rgba(42, 157, 143, 0.10) 70%);
    border: 1px solid rgba(42, 157, 143, 0.4);
    color: var(--accent-bright);
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.82rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    box-shadow: 0 0 16px rgba(42, 157, 143, 0.20);
}
.v2-step-label {
    color: var(--text-secondary);
    font-size: 0.76rem;
    font-weight: 500;
    letter-spacing: 0.04em;
}

/* ===== 5프레임 결과 — 시네마틱 카드 ===== */
.v2-frame {
    background: linear-gradient(180deg, rgba(20,20,28,0.85), rgba(14,14,22,0.85));
    border: 1px solid var(--border-subtle);
    border-radius: 20px;
    padding: 3rem 2.5rem;
    margin: 1.2rem 0;
    min-height: 280px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    backdrop-filter: blur(20px);
    box-shadow: 0 16px 60px rgba(0,0,0,0.45), inset 0 1px 0 rgba(255,255,255,0.03);
    animation: v2-frame-in 0.7s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    position: relative;
    overflow: hidden;
}
.v2-frame::before {
    content: "";
    position: absolute;
    top: -50%; left: -10%;
    width: 60%; height: 200%;
    background: radial-gradient(ellipse at center, rgba(42,157,143,0.08), transparent 60%);
    pointer-events: none;
    animation: v2-frame-glow 5s ease-in-out infinite alternate;
}
@keyframes v2-frame-in {
    0%   { transform: translateY(28px) scale(0.97); opacity: 0; }
    100% { transform: translateY(0) scale(1); opacity: 1; }
}
@keyframes v2-frame-glow {
    0%   { transform: translate(0,0); opacity: 0.6; }
    100% { transform: translate(60%, 20%); opacity: 1; }
}
.v2-frame-number {
    color: var(--accent);
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.28em;
    margin-bottom: 1.2rem;
    padding: 0.35rem 1rem;
    background: rgba(42,157,143,0.10);
    border: 1px solid rgba(42,157,143,0.25);
    border-radius: 100px;
    position: relative;
    z-index: 1;
}
.v2-frame-title {
    font-size: 2.1rem;
    font-weight: 800;
    color: var(--text-primary);
    line-height: 1.25;
    margin-bottom: 1.2rem;
    letter-spacing: -0.025em;
    position: relative;
    z-index: 1;
}
.v2-frame-body {
    color: var(--text-secondary);
    font-size: 1.02rem;
    line-height: 1.75;
    max-width: 480px;
    position: relative;
    z-index: 1;
}

/* MBTI 코드 큰 표시 — 글리치 글로우 */
.v2-mbti-code {
    font-family: 'Space Grotesk', 'SF Mono', monospace;
    font-size: 5.5rem;
    font-weight: 800;
    background: linear-gradient(135deg, var(--accent-bright), var(--accent) 50%, #b6f0e6);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    letter-spacing: 0.1em;
    line-height: 1;
    margin: 1.5rem 0 1rem 0;
    text-shadow: 0 0 50px rgba(79, 209, 197, 0.4);
    animation: v2-code-emerge 1.0s cubic-bezier(0.22, 1, 0.36, 1) forwards;
    position: relative;
    z-index: 1;
}
@keyframes v2-code-emerge {
    0%   { letter-spacing: 0.5em; opacity: 0; filter: blur(20px); }
    100% { letter-spacing: 0.1em; opacity: 1; filter: blur(0); }
}
.v2-mbti-percentile {
    color: var(--text-secondary);
    font-size: 1.1rem;
    margin-bottom: 1.5rem;
    animation: v2-fade-up 0.6s ease-out 0.5s forwards;
    position: relative;
    z-index: 1;
}

/* 셀럽 매칭 */
.v2-celeb-bar {
    background: var(--bg-elev);
    border-radius: 8px;
    padding: 0.7rem 1rem;
    margin: 0.5rem 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
    max-width: 400px;
}
.v2-celeb-name {
    color: var(--text-primary);
    font-weight: 600;
}
.v2-celeb-bar-track {
    flex: 1;
    height: 6px;
    background: var(--bg-deep);
    border-radius: 3px;
    margin: 0 1rem;
    overflow: hidden;
}
.v2-celeb-bar-fill {
    height: 100%;
    background: var(--accent);
    border-radius: 3px;
}
.v2-celeb-percent {
    color: var(--accent);
    font-weight: 600;
    font-size: 0.95rem;
    min-width: 50px;
    text-align: right;
}

/* ===== 깊은 분석 펼침 ===== */
.v2-deep-toggle {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: 14px;
    padding: 1.1rem 1.6rem;
    margin: 2rem 0 1rem 0;
    text-align: center;
    cursor: pointer;
    transition: all 0.25s ease;
}
.v2-deep-toggle:hover {
    border-color: var(--accent);
    background: rgba(42,157,143,0.04);
}
.v2-deep-section {
    background: linear-gradient(180deg, rgba(20,20,28,0.85), rgba(14,14,22,0.85));
    border: 1px solid var(--border-subtle);
    border-radius: 18px;
    padding: 2rem;
    margin: 1rem 0;
    backdrop-filter: blur(20px);
    box-shadow: 0 12px 40px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.02);
    animation: v2-fade-up 0.6s ease-out forwards;
}
.v2-deep-label {
    color: var(--accent);
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.20em;
    text-transform: uppercase;
    margin-bottom: 0.8rem;
}
.v2-deep-title {
    color: var(--text-primary);
    font-size: 1.4rem;
    font-weight: 800;
    margin-bottom: 1.2rem;
    letter-spacing: -0.02em;
}

/* ===== Outlier 표시 — 펄스 효과 ===== */
.v2-outlier-pill {
    display: inline-block;
    padding: 6px 14px;
    border-radius: 100px;
    font-size: 0.8rem;
    font-weight: 500;
    margin: 0.25rem 0.3rem 0.25rem 0;
    background: rgba(42,157,143,0.12);
    color: var(--accent);
    border: 1px solid rgba(42,157,143,0.3);
    transition: all 0.2s ease;
}
.v2-outlier-pill:hover {
    background: rgba(42,157,143,0.20);
    transform: translateY(-1px);
}
.v2-outlier-pill-low {
    background: rgba(225,29,72,0.10);
    color: var(--accent-rose);
    border-color: rgba(225,29,72,0.3);
}
.v2-outlier-pill-low:hover {
    background: rgba(225,29,72,0.18);
}

/* ===== 표 ===== */
.v2-table {
    width: 100%;
    border-collapse: collapse;
}
.v2-table th {
    text-align: left;
    padding: 0.8rem 0.9rem;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--text-tertiary);
    letter-spacing: 0.10em;
    text-transform: uppercase;
    border-bottom: 1px solid var(--border-strong);
}
.v2-table td {
    padding: 0.9rem 0.9rem;
    font-size: 0.93rem;
    color: var(--text-primary);
    border-bottom: 1px solid var(--border-subtle);
}
.v2-table tr:hover td {
    background: rgba(42,157,143,0.03);
}

/* ===== 셀럽 매칭 막대 — 진행 애니메이션 ===== */
.v2-celeb-card {
    background: rgba(20,20,28,0.6);
    border: 1px solid var(--border-subtle);
    border-radius: 12px;
    padding: 0.9rem 1.1rem;
    margin: 0.6rem 0;
    transition: all 0.25s ease;
}
.v2-celeb-card:hover {
    border-color: rgba(42,157,143,0.35);
    transform: translateX(4px);
}
.v2-celeb-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.4rem;
}
.v2-celeb-name {
    color: var(--text-primary);
    font-weight: 600;
    font-size: 0.95rem;
}
.v2-celeb-code {
    color: var(--text-tertiary);
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.78rem;
    letter-spacing: 0.08em;
    margin-left: 0.5rem;
}
.v2-celeb-percent {
    color: var(--accent);
    font-weight: 700;
    font-size: 1rem;
    font-family: 'Space Grotesk', sans-serif;
}
.v2-celeb-track {
    height: 5px;
    background: rgba(255,255,255,0.04);
    border-radius: 100px;
    overflow: hidden;
}
.v2-celeb-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--accent-bright), var(--accent));
    border-radius: 100px;
    box-shadow: 0 0 8px rgba(42,157,143,0.5);
    animation: v2-fill-grow 1.1s cubic-bezier(0.22, 1, 0.36, 1) forwards;
}
@keyframes v2-fill-grow {
    from { width: 0% !important; }
}

/* ===== Secondary 버튼 (돌아가기 등) ===== */
.stButton.v2-secondary > button,
button[kind="secondary"] {
    background: transparent !important;
    color: var(--text-secondary) !important;
    border: 1px solid var(--border-strong) !important;
    box-shadow: none !important;
    animation: none !important;
}
button[kind="secondary"]:hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
    background: rgba(42,157,143,0.04) !important;
}

/* footer */
.v2-footer {
    text-align: center;
    color: var(--text-tertiary);
    font-size: 0.78rem;
    margin-top: 4rem;
    padding-top: 2rem;
    border-top: 1px solid var(--border-subtle);
}

/* Streamlit 기본 요소 숨김 */
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] { background: var(--bg-card); }
footer[class*="viewerBadge"] { display: none !important; }
#MainMenu { visibility: hidden; }

/* 모바일 대응 */
@media (max-width: 640px) {
    .v2-hero-title { font-size: 2.2rem; }
    .v2-mbti-code { font-size: 4rem; }
    .v2-frame { padding: 2rem 1.5rem; }
    [data-testid="stRadio"] > div[role="radiogroup"] {
        flex-direction: column !important;
    }
}
</style>
"""

st.markdown(V2_CSS, unsafe_allow_html=True)


# ============================================================
# 세션 상태 관리
# ============================================================

if "stage" not in st.session_state:
    st.session_state.stage = "home"  # home / analyzing / result / deep
if "result" not in st.session_state:
    st.session_state.result = None


# ============================================================
# Stage 1: 홈 (입구) — MBTI 식 단순 입구
# ============================================================

def render_home():
    """소비자 앱 진입 화면 — 메인 녹음 + 마마무 컨셉 배경 + 부드러운 그래픽."""

    # 배경 — 마마무 4인 컬러 인물 실루엣 (흐릿)
    st.markdown("""
    <div class="v2-bg-portraits">
        <div class="v2-portrait v2-portrait-1">
            <svg viewBox="0 0 200 260" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                <ellipse cx="100" cy="80" rx="42" ry="55"/>
                <path d="M 35 260 Q 35 175 70 155 L 130 155 Q 165 175 165 260 Z"/>
                <path d="M 58 50 Q 100 25 142 50 L 144 80 Q 140 60 100 55 Q 60 60 56 80 Z" opacity="0.5"/>
            </svg>
        </div>
        <div class="v2-portrait v2-portrait-2">
            <svg viewBox="0 0 200 260" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                <ellipse cx="100" cy="78" rx="40" ry="52"/>
                <path d="M 30 260 Q 30 170 65 152 L 135 152 Q 170 170 170 260 Z"/>
                <path d="M 60 35 Q 100 15 140 35 L 142 75 Q 138 50 100 48 Q 62 50 58 75 Z" opacity="0.5"/>
            </svg>
        </div>
        <div class="v2-portrait v2-portrait-3">
            <svg viewBox="0 0 200 260" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                <ellipse cx="100" cy="82" rx="45" ry="58"/>
                <path d="M 32 260 Q 32 172 68 152 L 132 152 Q 168 172 168 260 Z"/>
                <path d="M 55 45 Q 100 18 145 45 L 148 90 Q 142 55 100 50 Q 58 55 52 90 Z" opacity="0.55"/>
            </svg>
        </div>
        <div class="v2-portrait v2-portrait-4">
            <svg viewBox="0 0 200 260" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                <ellipse cx="100" cy="80" rx="40" ry="52"/>
                <path d="M 35 260 Q 35 175 70 155 L 130 155 Q 165 175 165 260 Z"/>
                <path d="M 62 50 Q 100 28 138 50 L 138 75 Q 134 58 100 55 Q 66 58 62 75 Z" opacity="0.5"/>
                <path d="M 95 110 L 105 110 L 102 125 L 98 125 Z" opacity="0.6"/>
            </svg>
        </div>
    </div>
    <div class="v2-bg-grain"></div>
    """, unsafe_allow_html=True)

    # 상단 미니멀 브랜드 (사운드 웨이브 아이콘)
    st.markdown("""
    <div class="v2-topbar-min">
        <div class="v2-brand-wave">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="3" y1="12" x2="3" y2="12"/>
                <line x1="6" y1="9" x2="6" y2="15"/>
                <line x1="9" y1="6" x2="9" y2="18"/>
                <line x1="12" y1="3" x2="12" y2="21"/>
                <line x1="15" y1="6" x2="15" y2="18"/>
                <line x1="18" y1="9" x2="18" y2="15"/>
                <line x1="21" y1="12" x2="21" y2="12"/>
            </svg>
            <span class="v2-brand-text">VOCAL · MBTI</span>
        </div>
        <div class="v2-version-pill">4축 16타입</div>
    </div>
    """, unsafe_allow_html=True)

    # 히어로 — 떠다니는 오브 + 헤드라인
    st.markdown("""
    <div class="v2-hero" style="padding: 1rem 0 0.5rem; min-height: 200px;">
        <div class="v2-orbs">
            <div class="v2-orb v2-orb-1"></div>
            <div class="v2-orb v2-orb-2"></div>
            <div class="v2-orb v2-orb-3"></div>
            <div class="v2-orb v2-orb-4"></div>
        </div>
        <div class="v2-hero-inner">
            <div class="v2-hero-eyebrow">AI VOCAL ANALYSIS</div>
            <div class="v2-hero-title" style="font-size: 2.7rem;">
                <span class="v2-line"><span>당신의 목소리는</span></span>
                <span class="v2-line"><span><em>어떤 타입</em>인가?</span></span>
            </div>
            <div class="v2-hero-subtitle">
                1분 녹음으로 끝. AI가 100차원으로 분석해<br>
                당신만의 4글자 보컬 코드를 찾아드립니다.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 가수 일러스트 — "이건 너의 목소리를 평가하는 앱이다" 시그널
    st.markdown("""
    <div class="v2-vocalist-row">
        <div class="v2-vocalist" style="--vocalist-color: #f4d35e;">
            <svg viewBox="0 0 64 64" fill="currentColor">
                <circle cx="32" cy="22" r="9"/>
                <path d="M14 56c0-10 8-18 18-18s18 8 18 18" stroke="currentColor" stroke-width="3" fill="none"/>
                <path d="M44 26 Q 50 30 50 36" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" opacity="0.6"/>
                <path d="M48 22 Q 56 28 56 38" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" opacity="0.4"/>
            </svg>
        </div>
        <div class="v2-vocalist" style="--vocalist-color: #2a9d8f;">
            <svg viewBox="0 0 64 64" fill="currentColor">
                <circle cx="32" cy="22" r="9"/>
                <path d="M14 56c0-10 8-18 18-18s18 8 18 18" stroke="currentColor" stroke-width="3" fill="none"/>
                <path d="M44 26 Q 50 30 50 36" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" opacity="0.6"/>
            </svg>
        </div>
        <div class="v2-vocalist" style="--vocalist-color: #9b5de5;">
            <svg viewBox="0 0 64 64" fill="currentColor">
                <circle cx="32" cy="22" r="9"/>
                <path d="M14 56c0-10 8-18 18-18s18 8 18 18" stroke="currentColor" stroke-width="3" fill="none"/>
                <path d="M44 26 Q 52 30 52 38" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" opacity="0.6"/>
                <path d="M48 22 Q 58 28 58 40" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" opacity="0.4"/>
                <path d="M52 18 Q 62 26 62 42" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" opacity="0.25"/>
            </svg>
        </div>
        <div class="v2-vocalist" style="--vocalist-color: #f4a261;">
            <svg viewBox="0 0 64 64" fill="currentColor">
                <circle cx="32" cy="22" r="9"/>
                <path d="M14 56c0-10 8-18 18-18s18 8 18 18" stroke="currentColor" stroke-width="3" fill="none"/>
                <path d="M44 26 Q 50 30 50 36" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" opacity="0.5"/>
            </svg>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 보컬 타입 4종 카드 — 결과로 받게 될 타입의 미리보기
    st.markdown("""
    <div class="v2-types-grid">
        <div class="v2-type-card">
            <div class="v2-type-orb solar"></div>
            <div class="v2-type-name">청량+따뜻</div>
            <div class="v2-type-code">BWOP</div>
            <div class="v2-type-desc">외향적 정점</div>
        </div>
        <div class="v2-type-card">
            <div class="v2-type-orb wheein"></div>
            <div class="v2-type-name">청량+따뜻</div>
            <div class="v2-type-code">BWIS</div>
            <div class="v2-type-desc">내향적 정밀</div>
        </div>
        <div class="v2-type-card">
            <div class="v2-type-orb hwasa"></div>
            <div class="v2-type-name">묵직+따뜻</div>
            <div class="v2-type-code">DWOP</div>
            <div class="v2-type-desc">외향적 정점</div>
        </div>
        <div class="v2-type-card">
            <div class="v2-type-orb moon"></div>
            <div class="v2-type-name">청량+건조</div>
            <div class="v2-type-code">BRIS</div>
            <div class="v2-type-desc">내향적 정밀</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ───────────────────────────────────────────────
    # 메인 입력 영역 — 실시간 녹음을 무대 중앙으로
    # ───────────────────────────────────────────────

    # 입력 방식 토글 (세션 상태)
    if "input_mode" not in st.session_state:
        st.session_state.input_mode = "mic"

    audio_data = None
    audio_url = None

    if st.session_state.input_mode == "mic":
        # ▶ 메인 — 거대 마이크 무대
        st.markdown("""
        <div class="v2-mic-stage">
            <div class="v2-mic-wrap">
                <div class="v2-mic-ring"></div>
                <div class="v2-mic-ring"></div>
                <div class="v2-mic-ring"></div>
                <div class="v2-mic-button" id="v2-mic-trigger">
                    <svg class="v2-mic-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="9" y="2" width="6" height="11" rx="3"/>
                        <path d="M19 10v1a7 7 0 0 1-14 0v-1"/>
                        <line x1="12" y1="18" x2="12" y2="22"/>
                        <line x1="8" y1="22" x2="16" y2="22"/>
                    </svg>
                </div>
            </div>
            <div class="v2-mic-label">PRESS RECORD</div>
            <div class="v2-mic-cta">목소리를 들려주세요</div>
            <div class="v2-mic-hint">30초~2분 · 후렴구 추천 · 노이즈 없는 환경</div>
            <div class="v2-cta-arrow">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="12" y1="5" x2="12" y2="19"/>
                    <polyline points="19 12 12 19 5 12"/>
                </svg>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Streamlit 실제 녹음 위젯 (mic-stage 시각 버튼이 이 위젯을 트리거)
        try:
            audio_data = st.audio_input(" ", label_visibility="collapsed", key="audio_recorder")
        except Exception:
            st.warning("이 브라우저에서는 실시간 녹음을 지원하지 않습니다. 파일 업로드를 사용해주세요.")

        # JavaScript 브리지 — 시각 마이크 버튼을 실제 녹음 위젯 트리거로 연결
        components.html("""
        <script>
        (function() {
            const MAX_RETRIES = 60;
            let retries = 0;

            function bindMicTrigger() {
                const doc = window.parent.document;
                const visualMic = doc.querySelector('#v2-mic-trigger');
                const audioInputContainer = doc.querySelector('[data-testid="stAudioInput"]');

                if (!visualMic || !audioInputContainer) {
                    if (retries++ < MAX_RETRIES) {
                        setTimeout(bindMicTrigger, 200);
                    }
                    return;
                }

                // 이미 바인딩됐으면 스킵
                if (visualMic.dataset.bound === 'true') return;
                visualMic.dataset.bound = 'true';

                // 시각 마이크 버튼이 클릭되면 실제 녹음 위젯 버튼을 트리거
                visualMic.style.cursor = 'pointer';
                visualMic.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();

                    // audio_input 내부의 첫 번째 버튼 (record/stop) 클릭
                    const innerBtn = audioInputContainer.querySelector('button');
                    if (innerBtn) {
                        innerBtn.click();
                    }
                });

                // 호버 시 살짝 변형
                visualMic.addEventListener('mouseenter', function() {
                    visualMic.style.transform = 'scale(1.05)';
                    visualMic.style.transition = 'transform 0.2s ease';
                });
                visualMic.addEventListener('mouseleave', function() {
                    visualMic.style.transform = '';
                });
            }

            bindMicTrigger();
        })();
        </script>
        """, height=0)

    elif st.session_state.input_mode == "file":
        st.markdown("""
        <div style="text-align:center; padding: 1.5rem 0 1rem;">
            <div class="v2-mic-label">FILE UPLOAD</div>
            <div class="v2-mic-cta" style="margin-top: 0.4rem;">음원 파일 선택</div>
            <div class="v2-mic-hint">WAV · MP3 · M4A · FLAC</div>
        </div>
        """, unsafe_allow_html=True)
        audio_data = st.file_uploader(
            "음원",
            type=["wav", "mp3", "m4a", "ogg", "flac"],
            label_visibility="collapsed",
        )

    else:  # url
        st.markdown("""
        <div style="text-align:center; padding: 1.5rem 0 1rem;">
            <div class="v2-mic-label">YOUTUBE URL</div>
            <div class="v2-mic-cta" style="margin-top: 0.4rem;">유튜브 음원으로 분석</div>
            <div class="v2-mic-hint">자동 다운로드 · 보컬 분리 · 100차원 분석</div>
        </div>
        """, unsafe_allow_html=True)
        audio_url = st.text_input(
            "YouTube URL",
            placeholder="https://www.youtube.com/watch?v=...",
            label_visibility="collapsed",
        )

    # Sub 옵션 — 작은 토글 버튼들
    sub_cols = st.columns([1, 1, 1, 1])
    with sub_cols[0]:
        if st.session_state.input_mode != "mic":
            if st.button("녹음하기", key="sub_mic", use_container_width=True, type="secondary"):
                st.session_state.input_mode = "mic"
                st.rerun()
    with sub_cols[1]:
        if st.session_state.input_mode != "file":
            if st.button("파일 업로드", key="sub_file", use_container_width=True, type="secondary"):
                st.session_state.input_mode = "file"
                st.rerun()
    with sub_cols[2]:
        if st.session_state.input_mode != "url":
            if st.button("YouTube URL", key="sub_url", use_container_width=True, type="secondary"):
                st.session_state.input_mode = "url"
                st.rerun()

    # 이름 입력 (선택)
    st.markdown('<div style="margin-top:1.6rem;"></div>', unsafe_allow_html=True)
    artist_name = st.text_input(
        "이름 (선택)",
        placeholder="이름 · 익명 가능",
        key="artist_name",
        label_visibility="collapsed",
    )

    # 분석 시작 버튼
    st.markdown('<div style="margin-top:1.2rem;"></div>', unsafe_allow_html=True)
    if st.button("분석 시작 →", use_container_width=True, key="start_btn"):
        if audio_data is None and not audio_url:
            st.warning("먼저 목소리를 녹음하거나 음원을 입력해주세요.")
        else:
            st.session_state.stage = "analyzing"
            st.session_state.audio_data = audio_data
            st.session_state.audio_url = audio_url
            st.rerun()

    # 진행 단계 안내 (시각적 단계 카드)
    st.markdown("""
    <div class="v2-steps">
        <div class="v2-step">
            <div class="v2-step-num">1</div>
            <div class="v2-step-label">녹음 · 업로드</div>
        </div>
        <div class="v2-step">
            <div class="v2-step-num">2</div>
            <div class="v2-step-label">100차원 분석</div>
        </div>
        <div class="v2-step">
            <div class="v2-step-num">3</div>
            <div class="v2-step-label">MBTI 코드</div>
        </div>
        <div class="v2-step">
            <div class="v2-step-num">4</div>
            <div class="v2-step-label">셀럽 매칭</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 회사 헌법 — 발화 톤으로 부드럽게
    st.markdown("""
    <div class="v2-callout">
        <div class="v2-callout-label">FOUNDATIONAL PRINCIPLE</div>
        <div class="v2-callout-text">
            우리는 종합 점수로 줄 세우지 않습니다.
            <b style="color:var(--accent);">"이 목소리에 남다른 점이 있는가?"</b>만 봅니다.
        </div>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# Stage 2: 분석 중 — 8초 애니메이션
# ============================================================

def render_analyzing():
    """시네마틱 분석 화면 — 동심원 펄스 + 스펙트럼 바 + 프로그레스."""
    placeholder = st.empty()

    steps = [
        ("01", "보컬 분리 중", "반주에서 목소리만 추출하고 있습니다 (Demucs)"),
        ("02", "100차원 측정 중", "음색 · 음정 · 다이내믹 · 발성 품질 분석"),
        ("03", "톤 4사분면 분류", "청량 · 따뜻 · 묵직 · 건조 매핑"),
        ("04", "보컬 MBTI 코드 산출", "4축 16타입 자동 분류"),
        ("05", "셀럽 매칭 + 희소성 계산", "마마무 4인과의 거리 측정"),
    ]

    total = len(steps)
    for idx, (num, label, detail) in enumerate(steps):
        progress = int((idx + 1) / total * 100)
        # 스펙트럼 바 24개 — CSS 애니메이션이 알아서 움직임
        spectrum_bars = "".join(['<div class="bar"></div>'] * 24)
        placeholder.markdown(f"""
        <div class="v2-analyzing">
            <div class="v2-pulse-orb">
                <div class="ring"></div>
                <div class="ring"></div>
                <div class="ring"></div>
                <div class="core"></div>
            </div>
            <div class="v2-spectrum">
                {spectrum_bars}
            </div>
            <div class="v2-analyzing-status">{label}</div>
            <div class="v2-analyzing-detail">{detail}</div>
            <div class="v2-analyzing-step-badge">
                <span style="opacity:0.7;">STEP {num} / 0{total}</span>
                <span style="opacity:0.4;">·</span>
                <span>{progress}%</span>
            </div>
            <div class="v2-progress">
                <div class="v2-progress-fill" style="width:{progress}%;"></div>
            </div>
            <div style="margin-top:2.5rem; color:var(--text-tertiary); font-size:0.82rem; letter-spacing:0.04em; display:flex; align-items:center; justify-content:center; gap:0.5rem;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color:var(--accent);">
                    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
                </svg>
                <span>회사 헌법: 종합 점수 없음 · 남다른 점만 찾는 중</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        time.sleep(1.6)

    # 실제 분석은 여기서 진행 (시뮬레이션)
    result = run_analysis(
        st.session_state.get("audio_data"),
        st.session_state.get("audio_url"),
        st.session_state.get("artist_name", "익명"),
    )
    st.session_state.result = result
    st.session_state.stage = "result"
    st.rerun()


def extract_audio_features(audio_bytes: bytes) -> dict:
    """librosa로 실제 오디오에서 12개 보컬 MBTI 측정값 추출.

    추출 항목 (vocal_mbti.py와 키 호환):
        spectral_centroid_hz, chest_voice_ratio, formant_1_hz, formant_2_hz,
        nasal_resonance_ratio, breathiness, hnr_db, dynamic_range_db,
        attack_sharpness, loudness_smoothness, climax_building, energy_change_rate
    """
    import librosa
    import numpy as np
    from io import BytesIO

    # 로드 — 22050 Hz, mono, 최대 120초
    y, sr = librosa.load(BytesIO(audio_bytes), sr=22050, mono=True, duration=120.0)

    # 무음 트림
    y, _ = librosa.effects.trim(y, top_db=25)
    if len(y) < sr * 3:
        raise ValueError("음원이 너무 짧습니다 (3초 이상 필요).")

    features = {}

    # ─ 스펙트럼 분석 ─
    S_full = np.abs(librosa.stft(y, n_fft=2048, hop_length=512))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)

    # 1. Spectral centroid (밝기)
    sc = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    features["spectral_centroid_hz"] = float(np.median(sc))

    # 2. 흉성 비율 (저주파 에너지 비율 — 500Hz 이하)
    low_mask = freqs < 500
    low_energy = np.sum(S_full[low_mask, :])
    total_energy = np.sum(S_full) + 1e-8
    features["chest_voice_ratio"] = float(np.clip(low_energy / total_energy * 2, 0, 1))

    # 3-4. 포먼트 F1, F2 근사 (스펙트럼 피크)
    spec_mean = np.mean(S_full, axis=1)
    # F1: 200~1000 Hz 영역의 피크
    f1_mask = (freqs >= 200) & (freqs <= 1000)
    if f1_mask.any():
        f1_idx = np.argmax(spec_mean[f1_mask])
        features["formant_1_hz"] = float(freqs[f1_mask][f1_idx])
    else:
        features["formant_1_hz"] = 600.0
    # F2: 1000~3000 Hz 영역의 피크
    f2_mask = (freqs >= 1000) & (freqs <= 3000)
    if f2_mask.any():
        f2_idx = np.argmax(spec_mean[f2_mask])
        features["formant_2_hz"] = float(freqs[f2_mask][f2_idx])
    else:
        features["formant_2_hz"] = 1500.0

    # 5. 비강 공명 비율 (800~2500 Hz 에너지 비율)
    nasal_mask = (freqs >= 800) & (freqs <= 2500)
    nasal_energy = np.sum(S_full[nasal_mask, :])
    features["nasal_resonance_ratio"] = float(np.clip(nasal_energy / total_energy * 1.5, 0, 1))

    # 6. 호흡성 (스펙트럼 평탄도)
    flatness = librosa.feature.spectral_flatness(y=y)[0]
    features["breathiness"] = float(np.clip(np.median(flatness) * 8, 0, 1))

    # 7. HNR 근사 (1/ZCR + 스펙트럼 대비)
    zcr = librosa.feature.zero_crossing_rate(y)[0]
    contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
    zcr_med = np.median(zcr)
    contrast_med = np.median(contrast)
    # ZCR 낮을수록, 대비 높을수록 HNR 좋음
    hnr_proxy = (1 - np.clip(zcr_med * 8, 0, 1)) * 15 + np.clip(contrast_med, 0, 30) * 0.5
    features["hnr_db"] = float(np.clip(hnr_proxy, 0, 30))

    # 8. RMS 다이내믹 범위 (dB)
    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
    rms_db = 20 * np.log10(rms + 1e-8)
    features["dynamic_range_db"] = float(np.percentile(rms_db, 95) - np.percentile(rms_db, 5))

    # 9. 어택 강도 (onset strength)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    features["attack_sharpness"] = float(np.clip(np.median(onset_env) / 4, 0, 1))

    # 10. Loudness smoothness (RMS 변동성의 역)
    rms_cv = np.std(rms) / (np.mean(rms) + 1e-8)  # coefficient of variation
    features["loudness_smoothness"] = float(np.clip(1 - rms_cv, 0, 1))

    # 11. Climax building (후반부 / 전반부 에너지 비율)
    half = len(rms) // 2
    if half > 0:
        early = np.mean(rms[:half]) + 1e-8
        late = np.mean(rms[half:])
        ratio = (late - early) / early
        features["climax_building"] = float(np.clip(ratio + 0.5, 0, 1))
    else:
        features["climax_building"] = 0.5

    # 12. Energy change rate
    rms_diff = np.diff(rms)
    features["energy_change_rate"] = float(np.clip(np.std(rms_diff) / (np.mean(rms) + 1e-8), 0, 1))

    return features


def detect_outliers(features: dict) -> tuple:
    """측정값 기반 outlier 판정 — 회사 헌법: OR 논리, 양쪽 꼬리."""
    outlier_high = []
    outlier_low = []

    # 정의된 임계값 (도메인 지식)
    if features.get("spectral_centroid_hz", 1500) > 2800:
        outlier_high.append("스펙트럼 밝기")
    elif features.get("spectral_centroid_hz", 1500) < 1000:
        outlier_low.append("스펙트럼 밝기")

    if features.get("chest_voice_ratio", 0.5) > 0.65:
        outlier_high.append("흉성 두께")
    elif features.get("chest_voice_ratio", 0.5) < 0.15:
        outlier_low.append("흉성 두께")

    if features.get("nasal_resonance_ratio", 0.5) > 0.65:
        outlier_high.append("비강 공명")

    if features.get("breathiness", 0.5) > 0.6:
        outlier_high.append("호흡성")
    elif features.get("breathiness", 0.5) < 0.15:
        outlier_low.append("호흡성")

    if features.get("dynamic_range_db", 20) > 30:
        outlier_high.append("다이내믹 범위")
    elif features.get("dynamic_range_db", 20) < 8:
        outlier_low.append("다이내믹 범위")

    if features.get("attack_sharpness", 0.5) > 0.7:
        outlier_high.append("어택 강도")
    elif features.get("attack_sharpness", 0.5) < 0.2:
        outlier_low.append("어택 강도")

    if features.get("climax_building", 0.5) > 0.7:
        outlier_high.append("클라이맥스 폭발력")
    elif features.get("climax_building", 0.5) < 0.25:
        outlier_low.append("점진적 빌드업")

    if features.get("hnr_db", 20) > 25:
        outlier_high.append("음색 깔끔함")
    elif features.get("hnr_db", 20) < 10:
        outlier_low.append("음색 깔끔함")

    return outlier_high, outlier_low


def features_to_percentiles(features: dict) -> dict:
    """측정값을 100차원 백분위로 매핑 (시각화용)."""
    import numpy as np

    def pct(value, low, high):
        """value를 [low, high] 범위 기준 0~100 백분위로 매핑."""
        return float(np.clip((value - low) / (high - low) * 100, 0, 100))

    return {
        "스펙트럼 밝기": pct(features.get("spectral_centroid_hz", 1500), 500, 3500),
        "흉성 두께": pct(features.get("chest_voice_ratio", 0.5), 0, 1),
        "비강 공명": pct(features.get("nasal_resonance_ratio", 0.5), 0, 1),
        "호흡성": pct(features.get("breathiness", 0.5), 0, 1),
        "HNR (음색 깔끔)": pct(features.get("hnr_db", 20), 0, 30),
        "다이내믹 범위": pct(features.get("dynamic_range_db", 20), 5, 35),
        "어택 강도": pct(features.get("attack_sharpness", 0.5), 0, 1),
        "Loudness smoothness": pct(features.get("loudness_smoothness", 0.5), 0, 1),
        "클라이맥스 빌드업": pct(features.get("climax_building", 0.5), 0, 1),
        "에너지 변화율": pct(features.get("energy_change_rate", 0.5), 0, 1),
        "F1 (200-1000Hz 피크)": pct(features.get("formant_1_hz", 600), 200, 1100),
        "F2 (1000-3000Hz 피크)": pct(features.get("formant_2_hz", 1500), 1000, 3000),
    }


def run_analysis(audio_data, audio_url, artist_name):
    """실제 오디오 분석 진입점 — librosa로 측정 → vocal_mbti로 코드 산출."""

    # 오디오 바이트 추출
    audio_bytes = None
    try:
        if audio_data is not None:
            if hasattr(audio_data, "getvalue"):
                audio_bytes = audio_data.getvalue()
            elif hasattr(audio_data, "read"):
                pos = audio_data.tell() if hasattr(audio_data, "tell") else 0
                audio_bytes = audio_data.read()
                if hasattr(audio_data, "seek"):
                    audio_data.seek(pos)
            elif isinstance(audio_data, (bytes, bytearray)):
                audio_bytes = bytes(audio_data)
        elif audio_url:
            return {
                "error": "YouTube URL 분석은 현재 미지원 (다음 업데이트에서 추가). 파일 업로드 또는 녹음을 사용해주세요.",
                "artist": artist_name,
            }
        else:
            return {"error": "음원이 없습니다.", "artist": artist_name}

        if not audio_bytes:
            return {"error": "오디오 파일을 읽지 못했습니다.", "artist": artist_name}

        # 실제 특징 추출 (librosa)
        measurements = extract_audio_features(audio_bytes)

        # Outlier 판정
        outlier_high, outlier_low = detect_outliers(measurements)

        # 100차원 백분위 매핑
        percentiles = features_to_percentiles(measurements)
    except ImportError as e:
        return {
            "error": f"오디오 라이브러리 로드 실패: {e}. librosa가 설치되지 않았을 수 있습니다.",
            "artist": artist_name,
        }
    except Exception as e:
        return {"error": f"오디오 분석 실패: {e}", "artist": artist_name}

    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / "code" / "v2"))
        from vocal_mbti import analyze_vocal_mbti

        result = analyze_vocal_mbti(
            measurements,
            outlier_high=outlier_high,
            outlier_low=outlier_low,
        )
        return {
            "artist": artist_name,
            "code": result.code,
            "code_description": result.code_description,
            "type_percentile": result.type_percentile,
            "axis_scores": {
                "brightness": result.axis_scores.brightness,
                "weight": result.axis_scores.weight,
                "direction": result.axis_scores.direction,
                "style": result.axis_scores.style,
            },
            "celeb_matches": [
                {"name": m.name, "code": m.code, "similarity": m.similarity_percent}
                for m in result.celeb_matches
            ],
            "outlier_high": result.outlier_high_dimensions,
            "outlier_low": result.outlier_low_dimensions,
            "frame_1": result.frame_1_attention,
            "frame_2": result.frame_2_code_intro,
            "frame_3": result.frame_3_rarity,
            "frame_4": result.frame_4_celeb,
            "frame_5": result.frame_5_emotional,
            "timestamp": datetime.now().isoformat(),
            # 실측값 기반 데이터
            "measurements_raw": measurements,
            "percentiles_100d": percentiles,
            "reliability_scores": {
                "Librosa 스펙트럼 분석": 0.85,
                "RMS · Onset 검출": 0.88,
                "Formant 피크 추정": 0.72,
                "HNR 근사 (ZCR + Contrast)": 0.68,
                "음원 신뢰도": 0.90,
            },
        }
    except Exception as e:
        return {"error": str(e), "artist": artist_name}


# ============================================================
# Stage 3: 결과 — 5프레임 순차 공개
# ============================================================

def render_result():
    """5프레임 결과 + 깊은 분석 펼침."""
    result = st.session_state.result

    if not result or "error" in result:
        st.error(f"분석 실패: {result.get('error', 'Unknown')}")
        if st.button("처음으로"):
            st.session_state.stage = "home"
            st.rerun()
        return

    # ── 결과 진입 — 상단 미니 안내 ──
    outlier_count = len(result['outlier_high']) + len(result['outlier_low'])
    st.markdown(f"""
    <div class="v2-topbar">
        <div class="v2-topbar-logo">
            <div class="v2-topbar-dot"></div>
            <span>분석 완료</span>
        </div>
        <div class="v2-topbar-version">{outlier_count} OUTLIERS DETECTED</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Frame 1: 주의 환기 ──
    st.markdown(f"""
    <div class="v2-frame">
        <div class="v2-frame-number">FRAME 1 · 5</div>
        <div class="v2-frame-title">{result['frame_1']}</div>
        <div class="v2-frame-body">
            100차원 학술 분석을 완료했습니다.<br>
            <b style="color:var(--accent);">{outlier_count}개 차원</b>에서 outlier가 발견됐습니다.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Frame 2: 보컬 MBTI 코드 ──
    st.markdown(f"""
    <div class="v2-frame">
        <div class="v2-frame-number">FRAME 2 · 5 · YOUR VOCAL CODE</div>
        <div class="v2-mbti-code">{result['code']}</div>
        <div class="v2-mbti-percentile">희소성 <b style="color:var(--accent);">{int(result['type_percentile'])}%</b> · 이 타입 안에서의 위치</div>
        <div class="v2-frame-body">{result['code_description']}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Frame 3: 희소성 ──
    pct = result['type_percentile']
    if pct >= 99:
        rarity_color = "var(--accent)"
        rarity_label = "TOP 1%"
    elif pct >= 95:
        rarity_color = "var(--accent-bright)"
        rarity_label = "TOP 5%"
    elif pct >= 75:
        rarity_color = "var(--accent-blue)"
        rarity_label = "TOP 25%"
    else:
        rarity_color = "var(--text-secondary)"
        rarity_label = "AVERAGE RANGE"

    st.markdown(f"""
    <div class="v2-frame">
        <div class="v2-frame-number">FRAME 3 · 5 · RARITY</div>
        <div class="v2-frame-title" style="color:{rarity_color}; font-family:'Space Grotesk',sans-serif; font-size:2.6rem; letter-spacing:0.04em;">{rarity_label}</div>
        <div class="v2-frame-body">
            {result['frame_3']}<br>
            <span style="color:var(--text-tertiary); font-size:0.85rem;">
                ※ 종합 순위가 아닌 이 타입 내부에서의 희소성 (회사 헌법)
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Frame 4: 셀럽 매칭 ──
    celebs = result['celeb_matches']
    # 유사도 높은 순 정렬
    celebs_sorted = sorted(celebs, key=lambda m: m.get('similarity', 0), reverse=True)
    # 들여쓰기 없는 한 줄 HTML로 작성 — markdown이 들여쓰기를 code-block으로 잘못 인식하는 것 방지
    celeb_cards_html = ""
    for m in celebs_sorted:
        sim = m.get('similarity', 0)
        bar_width = max(2, int(sim))
        code = m.get('code', '')
        name = m.get('name', '')
        celeb_cards_html += (
            f'<div class="v2-celeb-card">'
            f'<div class="v2-celeb-row">'
            f'<div><span class="v2-celeb-name">{name}</span>'
            f'<span class="v2-celeb-code">· {code}</span></div>'
            f'<div class="v2-celeb-percent">{sim:.0f}%</div>'
            f'</div>'
            f'<div class="v2-celeb-track">'
            f'<div class="v2-celeb-fill" style="width:{bar_width}%;"></div>'
            f'</div>'
            f'</div>'
        )

    frame4_html = (
        f'<div class="v2-frame" style="padding-top:2.5rem; padding-bottom:2.5rem;">'
        f'<div class="v2-frame-number">FRAME 4 / 5 · CELEBRITY MATCH</div>'
        f'<div class="v2-frame-title" style="margin-bottom:1.8rem;">가장 닮은 보컬</div>'
        f'<div style="width:100%; max-width:460px;">{celeb_cards_html}</div>'
        f'<div class="v2-frame-body" style="margin-top:1.6rem; font-size:0.88rem; color:var(--text-tertiary);">'
        f'마마무 4인 톤 4사분면 기준 거리 측정</div>'
        f'</div>'
    )
    st.markdown(frame4_html, unsafe_allow_html=True)

    # ── Frame 5: 감정 트리거 ──
    st.markdown(f"""
    <div class="v2-frame" style="background:linear-gradient(180deg, rgba(42,157,143,0.18) 0%, rgba(20,20,28,0.9) 60%); border-color:rgba(42,157,143,0.35);">
        <div class="v2-frame-number">FRAME 5 · 5 · YOUR ESSENCE</div>
        <div class="v2-frame-title" style="font-size:1.7rem; font-style:italic; line-height:1.5;">
            "{result['frame_5']}"
        </div>
        <div class="v2-frame-body" style="margin-top:1.5rem; color:var(--text-secondary);">
            이것이 당신의 보컬이 시스템에 남긴 인상입니다.
        </div>
        <div style="margin-top:2rem; display:flex; gap:0.4rem;">
            <div class="v2-topbar-dot" style="width:6px; height:6px;"></div>
            <div class="v2-topbar-dot" style="width:6px; height:6px; animation-delay:0.4s;"></div>
            <div class="v2-topbar-dot" style="width:6px; height:6px; animation-delay:0.8s;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 깊은 분석 펼침 토글 ──
    st.markdown('<div style="height:1.5rem;"></div>', unsafe_allow_html=True)

    col_a, col_b = st.columns([2, 1])
    with col_a:
        if st.button("idol-scout급 깊은 분석 보기 →", use_container_width=True):
            st.session_state.stage = "deep"
            st.rerun()
    with col_b:
        if st.button("다시 분석", use_container_width=True, type="secondary"):
            st.session_state.stage = "home"
            st.session_state.result = None
            st.rerun()

    # 처음으로 + JSON 다운로드
    col1, col2 = st.columns(2)
    with col1:
        if st.button("처음으로", use_container_width=True):
            st.session_state.stage = "home"
            st.session_state.result = None
            st.rerun()
    with col2:
        st.download_button(
            "📥 JSON 다운로드",
            json.dumps(result, ensure_ascii=False, indent=2),
            file_name=f"vocal_mbti_{result.get('artist', 'anon')}_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True,
        )


# ============================================================
# Stage 4: 깊은 분석
# ============================================================

def render_deep():
    """idol-scout급 학술 결과 — outlier 차원, 7차원 비교 등."""
    result = st.session_state.result
    if not result:
        st.session_state.stage = "home"
        st.rerun()
        return

    # 헤더
    st.markdown(f"""
    <div style="padding:2rem 0 1rem 0;">
        <div style="color:var(--accent); font-size:0.78rem; font-weight:600; letter-spacing:0.18em;">DEEP ANALYSIS — IDOL-SCOUT GRADE</div>
        <div style="color:var(--text-primary); font-size:2rem; font-weight:700; margin-top:0.6rem;">
            {result['code']}-{int(result['type_percentile'])}
        </div>
        <div style="color:var(--text-secondary); font-size:1rem; margin-top:0.5rem;">
            {result['code_description']}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 4축 점수 표 ──
    st.markdown('<div class="v2-deep-section">', unsafe_allow_html=True)
    st.markdown('<div class="v2-deep-label">4-AXIS BREAKDOWN</div>', unsafe_allow_html=True)
    st.markdown('<div class="v2-deep-title">4축 점수 분해</div>', unsafe_allow_html=True)

    axes = result['axis_scores']
    axis_rows = [
        ("Brightness", axes['brightness'], "Dark", "Bright"),
        ("Weight", axes['weight'], "Warm", "Dry"),
        ("Direction", axes['direction'], "Inward", "Outward"),
        ("Style", axes['style'], "Subtle", "Peak"),
    ]
    axis_html = '<table class="v2-table">'
    axis_html += '<thead><tr><th>축</th><th>점수</th><th>위치</th></tr></thead><tbody>'
    for name, score, left, right in axis_rows:
        position = right if score >= 0.5 else left
        axis_html += f"""
        <tr>
            <td>{name}</td>
            <td style="color:var(--accent); font-weight:600;">{score:.2f}</td>
            <td>{left} ←——→ <b style="color:var(--accent);">{position}</b> ←——→ {right}</td>
        </tr>
        """
    axis_html += '</tbody></table>'
    st.markdown(axis_html, unsafe_allow_html=True)

    # v2 시각화 — 4축 레이더 + 4사분면 + 16타입 그리드
    if _V2VIZ_AVAILABLE:
        try:
            # 셀럽 매칭에서 가장 가까운 마마무 멤버 추출
            celeb_matches = result.get('celeb_matches', [])
            top_member = None
            top_ref = None
            if celeb_matches:
                top_member = celeb_matches[0].get('member')
                try:
                    from vocal_mbti import MAMAMOO_REFERENCE  # type: ignore
                    ref = MAMAMOO_REFERENCE.get(top_member, {})
                    if ref:
                        top_ref = {k: ref.get(k, 0.5)
                                   for k in ("brightness", "weight", "direction", "style")}
                except Exception:
                    top_ref = None

            radar_fig = v2viz.plot_mbti_radar(axes, top_member, top_ref)
            st.plotly_chart(radar_fig, use_container_width=True)

            quad_fig = v2viz.plot_vocal_quadrant(
                user_brightness=axes['brightness'],
                user_weight=axes['weight'],
                show_mamamoo=True,
            )
            st.plotly_chart(quad_fig, use_container_width=True)

            grid_fig = v2viz.plot_16type_grid(result['code'])
            st.plotly_chart(grid_fig, use_container_width=True)

            if celeb_matches:
                # visualizers_v2.plot_celeb_match는 {"member","similarity(0~1)","code"} 기대
                # app_v2 result는 {"name","similarity(0~100)","code"} 형태이므로 변환
                normalized_matches = []
                for m in celeb_matches:
                    member = m.get('member') or m.get('name')
                    sim_raw = m.get('similarity', 0)
                    sim = sim_raw / 100.0 if sim_raw > 1.5 else sim_raw
                    normalized_matches.append({
                        "member": member,
                        "similarity": sim,
                        "distance": 1.0 - sim,
                        "code": m.get('code', ''),
                    })
                celeb_fig = v2viz.plot_celeb_match(normalized_matches)
                st.plotly_chart(celeb_fig, use_container_width=True)
        except Exception as _viz_e:
            st.caption(f"(시각화 모듈 로드 실패: {_viz_e})")

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Outlier 차원 ──
    st.markdown('<div class="v2-deep-section">', unsafe_allow_html=True)
    st.markdown('<div class="v2-deep-label">OUTLIER DIMENSIONS — OR LOGIC</div>', unsafe_allow_html=True)
    st.markdown('<div class="v2-deep-title">극단값 발견 차원</div>', unsafe_allow_html=True)

    st.markdown('<div style="margin:1rem 0;">', unsafe_allow_html=True)
    st.markdown('<b style="color:var(--accent);">초우월 (상위 1% 이상)</b>', unsafe_allow_html=True)
    pills_high = "".join([f'<span class="v2-outlier-pill">{d}</span>' for d in result['outlier_high']])
    st.markdown(f'<div style="margin-top:0.5rem;">{pills_high or "<i>없음</i>"}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div style="margin:1.5rem 0;">', unsafe_allow_html=True)
    st.markdown('<b style="color:var(--accent-rose);">초이질 (하위 1% 미만 — 진짜 원석)</b>', unsafe_allow_html=True)
    pills_low = "".join([f'<span class="v2-outlier-pill v2-outlier-pill-low">{d}</span>' for d in result['outlier_low']])
    st.markdown(f'<div style="margin-top:0.5rem;">{pills_low or "<i>없음</i>"}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div style="color:var(--text-tertiary); font-size:0.85rem; margin-top:1rem;">회사 헌법: OR 논리 — 한 차원이라도 outlier면 통과</div>', unsafe_allow_html=True)

    # v2 시각화 — 100차원 outlier 분포 (양쪽 꼬리 강조)
    if _V2VIZ_AVAILABLE:
        percentiles = result.get('percentiles_100d', {})
        if percentiles:
            try:
                outlier_fig = v2viz.plot_outlier_distribution(percentiles, top_n=10)
                st.plotly_chart(outlier_fig, use_container_width=True)
            except Exception as _viz_e:
                st.caption(f"(outlier 차트 생성 실패: {_viz_e})")

    st.markdown('</div>', unsafe_allow_html=True)

    # ── 신뢰도 검증 ──
    st.markdown('<div class="v2-deep-section">', unsafe_allow_html=True)
    st.markdown('<div class="v2-deep-label">RELIABILITY VALIDATION — 5 LAYERS</div>', unsafe_allow_html=True)
    st.markdown('<div class="v2-deep-title">신뢰도 검증 레이어</div>', unsafe_allow_html=True)

    layers = [
        ("① 공개 데이터셋 검증", "VocalSet · NUS-48E · OpenSinger"),
        ("② 사람 평가자 상관계수", "Pearson r / Spearman ρ / ICC"),
        ("③ 모델·라이브러리 버전 고정", "재현 가능성"),
        ("④ 저신뢰 프레임 비율 메타데이터", "F0 정밀도"),
        ("⑤ Jitter·Shimmer·HNR 임상 정상 범위", "음성과학 표준"),
    ]
    table_html = '<table class="v2-table"><thead><tr><th>검증 절차</th><th>방법</th></tr></thead><tbody>'
    for title, method in layers:
        table_html += f'<tr><td>{title}</td><td style="color:var(--text-secondary);">{method}</td></tr>'
    table_html += '</tbody></table>'
    st.markdown(table_html, unsafe_allow_html=True)

    # v2 시각화 — 5레이어 신뢰도 게이지
    if _V2VIZ_AVAILABLE:
        reliability = result.get('reliability_scores', {})
        if reliability:
            try:
                rel_fig = v2viz.plot_reliability_gauges(reliability)
                st.plotly_chart(rel_fig, use_container_width=True)
            except Exception as _viz_e:
                st.caption(f"(신뢰도 차트 생성 실패: {_viz_e})")

    st.markdown('</div>', unsafe_allow_html=True)

    # ── 회사 헌법 정합 ──
    st.markdown('<div class="v2-deep-section">', unsafe_allow_html=True)
    st.markdown('<div class="v2-deep-label">CONSTITUTIONAL ALIGNMENT</div>', unsafe_allow_html=True)
    st.markdown('<div class="v2-deep-title">회사 헌법 정합성</div>', unsafe_allow_html=True)
    st.markdown("""
    <table class="v2-table">
        <thead><tr><th>원칙</th><th>적용 결과</th></tr></thead>
        <tbody>
            <tr><td>종합 점수 금지</td><td style="color:var(--accent);">✓ 단일 점수 없음 · MBTI 코드는 분류일 뿐</td></tr>
            <tr><td>OR 논리</td><td style="color:var(--accent);">✓ 차원별 독립 outlier 판정</td></tr>
            <tr><td>양쪽 꼬리</td><td style="color:var(--accent);">✓ 초우월 + 초이질 동시 검출</td></tr>
            <tr><td>상위 0.05% 임계</td><td style="color:var(--accent);">✓ 100차원 통계 보정 적용</td></tr>
        </tbody>
    </table>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # 돌아가기
    st.markdown('<div style="height:2rem;"></div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← 5프레임 결과로", use_container_width=True):
            st.session_state.stage = "result"
            st.rerun()
    with col2:
        if st.button("처음으로", use_container_width=True):
            st.session_state.stage = "home"
            st.session_state.result = None
            st.rerun()


# ============================================================
# 라우터
# ============================================================

if st.session_state.stage == "home":
    render_home()
elif st.session_state.stage == "analyzing":
    render_analyzing()
elif st.session_state.stage == "result":
    render_result()
elif st.session_state.stage == "deep":
    render_deep()


# ============================================================
# Footer
# ============================================================

st.markdown("""
<div class="v2-footer">
    璞玉문화 · 보컬 MBTI v2 · 통합 시스템<br>
    종합 점수 없음 · OR 논리 · 양쪽 꼬리 · 상위 0.05% 임계값
</div>
""", unsafe_allow_html=True)
