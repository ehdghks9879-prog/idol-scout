"""
idol_scout — Streamlit 웹앱 v4.0
극단값 탐지 패러다임 · 100차원 보컬 벡터 · 쉬운 언어
"""

import streamlit as st
import plotly.graph_objects as go
import json, sys, os
from pathlib import Path
from datetime import datetime
from itertools import combinations

sys.path.insert(0, str(Path(__file__).parent))

st.set_page_config(page_title="idol_scout", page_icon="🎤", layout="wide", initial_sidebar_state="expanded")

# ── CSS ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
* { font-family: 'Noto Sans KR', sans-serif; }

.card {
    background: #1e1e2e;
    border-radius: 16px;
    padding: 1.4rem;
    margin-bottom: 1rem;
    border: 1px solid #2a2a3e;
}
.card-title {
    font-size: 0.85rem;
    color: #888;
    margin-bottom: 0.6rem;
    font-weight: 500;
    letter-spacing: 0.5px;
}
.big-number {
    font-size: 2.4rem;
    font-weight: 700;
    line-height: 1.1;
}
.big-label {
    font-size: 0.9rem;
    color: #aaa;
    margin-top: 0.3rem;
}
.green { color: #00b894; }
.yellow { color: #fdcb6e; }
.red { color: #e17055; }
.gray { color: #636e72; }
.blue { color: #74b9ff; }
.purple { color: #a29bfe; }

.score-bar {
    height: 8px;
    border-radius: 4px;
    background: #2a2a3e;
    margin: 6px 0;
    overflow: hidden;
}
.score-fill {
    height: 100%;
    border-radius: 4px;
}

.indicator-row {
    display: flex;
    align-items: center;
    padding: 0.7rem 0;
    border-bottom: 1px solid #2a2a3e;
}
.indicator-row:last-child { border-bottom: none; }
.indicator-name {
    flex: 1;
    font-size: 0.95rem;
    color: #ddd;
}
.indicator-score {
    font-size: 1.1rem;
    font-weight: 600;
    width: 60px;
    text-align: right;
}
.indicator-bar-wrap {
    flex: 1.2;
    margin: 0 1rem;
}

.tag {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 500;
}
.tag-pass { background: rgba(0,184,148,0.15); color: #00b894; }
.tag-fail { background: rgba(225,112,85,0.15); color: #e17055; }
.tag-warn { background: rgba(253,203,110,0.15); color: #fdcb6e; }
.tag-info { background: rgba(116,185,255,0.15); color: #74b9ff; }
.tag-outlier { background: rgba(162,155,254,0.2); color: #a29bfe; border: 1px solid rgba(162,155,254,0.4); }

.detail-text {
    font-size: 0.85rem;
    color: #999;
    line-height: 1.6;
    margin-top: 0.3rem;
}

.section-title {
    font-size: 1.15rem;
    font-weight: 600;
    color: #eee;
    margin: 1.5rem 0 0.8rem 0;
}

.summary-box {
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    border: 1px solid #0f3460;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin: 0.5rem 0 1rem 0;
    font-size: 0.95rem;
    color: #ddd;
    line-height: 1.8;
}
.multi-person-warning {
    background: linear-gradient(135deg, #2d1b1b, #3a1a1a);
    border: 2px solid #e17055;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin: 0.5rem 0 1rem 0;
    font-size: 1rem;
    color: #fab1a0;
    line-height: 1.8;
}

.explain {
    font-size: 0.8rem;
    color: #777;
    margin-top: 0.2rem;
    font-style: italic;
}

.dim-category {
    background: #16213e;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
    border-left: 4px solid;
}

.paradigm-box {
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    border: 1px solid #0f3460;
    border-radius: 12px;
    padding: 1.2rem;
    margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)

REPORTS_DIR = Path(__file__).parent / "analysis_reports"

# ── 극단값 판정 ──
OUTLIER_THRESHOLD = 0.7
NOTABLE_THRESHOLD = 0.5
OUTLIER_LOW_THRESHOLD = 0.15

# ── 쉬운 한국어 용어 ──
VAR_KR = {
    "SDI": "나만의 스타일", "EDT": "감정 전달력", "CER": "실력 성장 속도",
    "RMC": "리듬감과 몸의 연결", "AAC": "관객과의 소통", "SCA": "자기 객관화 능력",
    "CDR": "가장 잘하는 한 가지의 깊이", "EDI": "감정 표현의 넓이", "NVC": "음악 외 분야 확장력",
    "CCI": "다른 산업에 미치는 영향", "CBP": "다양한 장르 소화력",
}
VAR_EXPLAIN = {
    "SDI": "다른 사람과 비교했을 때 이 사람만의 고유한 스타일이 얼마나 뚜렷한지",
    "EDT": "노래할 때 감정이 얼마나 잘 전달되는지",
    "CER": "시간이 지남에 따라 실력이 얼마나 빠르게 느는지 (여러 영상 필요)",
    "RMC": "음악의 리듬을 몸으로 얼마나 자연스럽게 표현하는지",
    "AAC": "무대에서 관객과 얼마나 잘 교감하는지 (사람이 직접 판단)",
    "SCA": "자기 강점과 약점을 얼마나 잘 파악하는지 (사람이 직접 판단)",
    "CDR": "'이 사람하면 이것'이라고 떠오르는 핵심 능력이 얼마나 깊은지",
    "EDI": "기쁨, 슬픔, 분노 등 다양한 감정을 얼마나 폭넓게 표현하는지",
    "NVC": "예능, 연기, MC 등 음악 외 분야에서도 통하는지 (사람이 직접 판단)",
    "CCI": "패션, 문화 트렌드 등 다른 분야에도 영향을 주는지 (사람이 직접 판단)",
    "CBP": "발라드, 힙합, 댄스 등 다양한 장르를 소화할 수 있는지 (사람이 직접 판단)",
}
LEVEL_KR = {"HIGH": "높음", "MID_HIGH": "중상", "MID": "보통", "MID_LOW": "약간 낮음", "LOW": "낮음"}
LEVEL_EXPLAIN = {
    "HIGH": "이 영역에서 뚜렷한 강점",
    "MID_HIGH": "평균 이상, 잠재력 있음",
    "MID": "아직 판단하기 이른 수준 (기본값일 수 있음)",
    "MID_LOW": "이 영역이 상대적으로 약함",
    "LOW": "이 영역에서 뚜렷한 약점",
}

# ── 6개 핵심 지표 ──
INDICATOR_DETAIL = {
    "1": {"name": "음색 고유성", "icon": "🎵", "category": "vocal",
          "question": "이 사람 목소리를 한 번 들으면 기억에 남는가?",
          "detail": "목소리의 음색 특성(MFCC, 스펙트럼)을 분석합니다. 점수가 높을수록 '아, 이 목소리!' 하고 바로 떠오르는 독특한 음색입니다."},
    "2": {"name": "음색 판별력", "icon": "🔍", "category": "vocal",
          "question": "어떤 노래를 부르든 이 사람인 걸 알아듣겠는가?",
          "detail": "노래의 여러 구간에서 음색이 얼마나 일관되는지 봅니다. 높을수록 어떤 곡이든 '이 사람 목소리'라고 구별이 쉽습니다."},
    "36": {"name": "리듬 인격", "icon": "🥁", "category": "dance",
           "question": "이 사람만의 리듬 해석 방식이 있는가?",
           "detail": "비트보다 살짝 앞서가는지, 뒤에 여유있게 실리는지, 정확히 맞추는지를 봅니다. 거의 바뀌지 않는 타고난 특성입니다."},
    "50": {"name": "동작 식별도", "icon": "💃", "category": "dance",
           "question": "실루엣만 봐도 이 사람인 걸 알겠는가?",
           "detail": "몸 움직임에 고유한 패턴이 있는지 분석합니다. (현재 준비 중)"},
    "64": {"name": "비주얼 잔상", "icon": "👤", "category": "visual",
           "question": "영상을 보고 나서 이 사람 얼굴이 계속 떠오르는가?",
           "detail": "얼굴 구조의 독특함과 기억에 남는 정도를 분석합니다. (현재 준비 중)"},
    "83": {"name": "표정 시그니처", "icon": "😊", "category": "expression",
           "question": "이 사람에게만 있는 고유한 표정이 있는가?",
           "detail": "표정 변화의 범위와 고유 패턴을 분석합니다. (현재 준비 중)"},
}

COMPOSITE_DETAIL = {
    "system_dependency": {
        "name": "기획사 의존도", "icon": "🏢", "reverse": True,
        "question": "이 사람이 소속사/그룹 없이도 혼자 경쟁력이 있는가?",
        "high": "혼자서는 아직 어려움 — 소속사/그룹의 도움이 많이 필요한 상태",
        "low": "독자적 매력이 있음 — 어디에 가든 자기 힘으로 할 수 있는 상태"},
    "transition_readiness": {
        "name": "독립 준비도", "icon": "🔄",
        "question": "그룹 해체나 소속사 이적 시 살아남을 수 있는가?",
        "high": "독립해도 잘 해낼 준비가 되어 있음", "low": "독립하면 어려움이 예상됨"},
    "exposure_conversion": {
        "name": "팬 만드는 효율", "icon": "📈",
        "question": "미디어에 나올 때마다 실제로 팬이 느는가?",
        "high": "노출될 때마다 팬이 효과적으로 늘어남", "low": "많이 알려져도 실제 팬은 잘 안 늘어남"},
    "resource_convergence": {
        "name": "역량 집중도", "icon": "🎯",
        "question": "'이 사람하면 이것'이라는 게 명확한가?",
        "high": "핵심 능력이 명확하게 하나로 모여 있음", "low": "이것저것 하지만 뭐가 핵심인지 불명확"},
    "innate_ratio": {
        "name": "타고난 비율", "icon": "⭐",
        "question": "현재 실력 중 타고난 것과 훈련한 것의 비율은?",
        "high": "타고난 요소가 큰 비중 — 투자 가치 높음", "low": "훈련으로 쌓은 실력 비중이 더 큼"},
    "growth_trajectory": {
        "name": "성장 속도", "icon": "📊",
        "question": "시간이 지나면서 실력이 늘고 있는가?",
        "high": "뚜렷하게 성장하고 있음", "low": "아직 판단 불가 — 다른 시기 영상이 필요"},
}

# ── 100차원 카테고리 ──
DIMENSION_CATEGORIES = {
    "vocal": {"name": "목소리", "icon": "🎵", "color": "#74b9ff", "total": 25,
              "summary": "음색, 음정, 호흡, 비브라토, 감정 표현 등",
              "indicator_ids": ["1", "2"]},
    "dance": {"name": "몸·춤", "icon": "💃", "color": "#fd79a8", "total": 25,
              "summary": "리듬감, 동작 정확도, 즉흥력, 코디네이션 등",
              "indicator_ids": ["36", "50"]},
    "visual": {"name": "외모·카메라", "icon": "👤", "color": "#fdcb6e", "total": 15,
               "summary": "얼굴 식별성, 카메라 적응도, 신체 비율 등",
               "indicator_ids": ["64"]},
    "expression": {"name": "표정·감정", "icon": "😊", "color": "#00b894", "total": 20,
                   "summary": "미세 표정, 감정 전환, 진정성 등",
                   "indicator_ids": ["83"]},
    "aura": {"name": "무대 존재감", "icon": "✨", "color": "#a29bfe", "total": 10,
             "summary": "시선 끌림, 공간 지배력, 에너지 전달 등",
             "indicator_ids": []},
    "growth": {"name": "성장 잠재력", "icon": "📈", "color": "#fab1a0", "total": 5,
               "summary": "실력 변화율, 타고난 비율 등",
               "indicator_ids": []},
}


# ── 색상 헬퍼 ──
def _color(score, reverse=False):
    if reverse:
        if score >= 0.8: return "#e17055"
        if score >= 0.5: return "#fdcb6e"
        return "#00b894"
    if score >= 0.6: return "#00b894"
    if score >= 0.4: return "#fdcb6e"
    if score > 0: return "#e17055"
    return "#636e72"

def _outlier_color(score):
    if score >= OUTLIER_THRESHOLD: return "#a29bfe"
    if 0 < score <= OUTLIER_LOW_THRESHOLD: return "#fd79a8"
    if score >= NOTABLE_THRESHOLD: return "#74b9ff"
    if score > 0: return "#636e72"
    return "#3d3d3d"

def _score_meaning(score, measured=True):
    """점수를 사람이 이해할 수 있는 한 마디로"""
    if not measured: return "아직 측정하지 못했습니다", "gray"
    if score >= OUTLIER_THRESHOLD: return "매우 독특함 — 극단값 영역", "#a29bfe"
    if 0 < score <= OUTLIER_LOW_THRESHOLD: return "매우 특이함 — 기존 틀과 다른 유형", "#fd79a8"
    if score >= 0.6: return "꽤 독특한 편", "#00b894"
    if score >= 0.4: return "평균 범위 안", "#fdcb6e"
    if score > 0: return "약한 편", "#e17055"
    return "미측정", "#636e72"

def _bar_html(score, color, width_pct=100):
    w = max(2, int(score * width_pct))
    return f'<div class="score-bar"><div class="score-fill" style="width:{w}%;background:{color};"></div></div>'

def _metric_card(title, value, subtitle="", color_class="green"):
    return f"""<div class="card">
        <div class="card-title">{title}</div>
        <div class="big-number {color_class}">{value}</div>
        <div class="big-label">{subtitle}</div>
    </div>"""


# ── 리포트 로드 ──
def load_reports():
    if not REPORTS_DIR.exists(): return []
    files = sorted(REPORTS_DIR.glob("analysis_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    reports = []
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            data["_filename"] = f.name
            reports.append(data)
        except: pass
    return reports

# ── 분석 실행 ──
def run_analysis(url, content_type, name, name_en, group, agency):
    from idol_scout.api import screen, build_profile, analyze, screening_to_snapshot
    with st.spinner("🎵 영상 다운로드 및 분석 중... (1~2분 소요)"):
        result = screen(url, content_type=content_type, verbose=False, save=False)
        snapshot = screening_to_snapshot(result)
        profile = build_profile(name=name or "", name_en=name_en or "", group=group or "", agency=agency or "", snapshots=[snapshot])
        profile = analyze(profile)

    report = _build_report(result, profile, url, content_type, name, name_en, group, agency)
    REPORTS_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fp = REPORTS_DIR / f"analysis_{(name or '').replace(' ','_')}_{ts}.json"
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    report["_filename"] = fp.name
    return report

def _build_report(sr, profile, url, ct, name, name_en, group, agency):
    report = {"meta": {"name": name or "", "name_en": name_en or "", "group": group or "", "agency": agency or "",
                        "url": url, "content_type": ct, "analysis_time": datetime.now().isoformat()},
              "screening": {"passed": sr.passed, "max_single_score": round(sr.max_single_score, 4),
                            "outlier_count": sr.outlier_count, "outlier_dimensions": sr.outlier_dimensions,
                            "multi_person_detected": sr.multi_person_detected,
                            "estimated_person_count": sr.estimated_person_count,
                            "multi_person_method": sr.multi_person_method,
                            "multi_person_notes": sr.multi_person_notes,
                            "indicators": {}},
              "interpret_11vars": {}, "composites": {}, "failure_diagnosis": {}}

    for iid, ir in sr.indicators.items():
        report["screening"]["indicators"][str(iid)] = {
            "name": ir.name, "score": round(ir.score, 4) if ir.measured else 0.0,
            "confidence": round(ir.confidence, 4) if ir.measured else 0.0,
            "effective": round(ir.effective_score, 4) if ir.measured else 0.0,
            "measured": ir.measured, "notes": ir.notes or ""}

    if profile.interpret:
        for code in ["sdi","edt","cer","rmc","aac","sca","cdr","edi","nvc","cci","cbp"]:
            v = getattr(profile.interpret, code, None)
            if v:
                report["interpret_11vars"][code.upper()] = {
                    "score": round(v.score, 3), "level": v.level.name if hasattr(v.level, 'name') else str(v.level),
                    "ai_measurable": v.ai_measurable}

    if profile.composites:
        c = profile.composites
        report["composites"] = {k: round(getattr(c, k), 3) for k in
            ["system_dependency","transition_readiness","exposure_conversion","resource_convergence","innate_ratio","growth_trajectory"]}

    if profile.failure_diag:
        fd = profile.failure_diag
        report["failure_diagnosis"] = {
            "failure_type": fd.failure_type.name if hasattr(fd.failure_type, 'name') else str(fd.failure_type),
            "risk_level": fd.risk_level if isinstance(fd.risk_level, str) else str(fd.risk_level),
            "ncps_met": fd.ncps.conditions_met if fd.ncps else 0,
            "rncs_met": fd.rncs.conditions_met if fd.rncs else 0,
            "ncps_detail": {"단일차원 포지션": fd.ncps.cond1_single_dimension, "핵심역량 결핍": fd.ncps.cond2_cdr_deficit,
                            "관객적응 부족": fd.ncps.cond3_aac_low, "시스템 은폐": fd.ncps.cond4_system_concealment,
                            "전환 미준비": fd.ncps.cond5_no_transition_prep} if fd.ncps else {},
            "rncs_detail": {"프로필 분산": fd.rncs.cond1_dispersed_profile, "수렴 엔진 부재": fd.rncs.cond2_convergence_engine,
                            "시스템 공급 부족": fd.rncs.cond3_system_supply, "비음악적 주목": fd.rncs.cond4_non_musical_attention,
                            "윈도우 초과": fd.rncs.cond5_window_missed} if fd.rncs else {}}

    # ── 보컬 프로파일 (v2) ──
    if sr.vocal_profile:
        report["vocal_profile"] = sr.vocal_profile

    return report


# ══════════════════════════════════════
# 렌더링
# ══════════════════════════════════════

def render_radar(indicators):
    cats, vals = [], []
    for iid, ind in indicators.items():
        info = INDICATOR_DETAIL.get(str(iid), {})
        cats.append(info.get("name", ind["name"]))
        vals.append(ind["score"] if ind["measured"] else 0)

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals + [vals[0]], theta=cats + [cats[0]], fill='toself',
        fillcolor='rgba(162,155,254,0.15)', line=dict(color='#a29bfe', width=2),
        marker=dict(size=8, color=[_outlier_color(v) for v in vals])))
    n = len(cats)
    fig.add_trace(go.Scatterpolar(
        r=[OUTLIER_THRESHOLD]*(n+1), theta=cats + [cats[0]],
        line=dict(color='rgba(162,155,254,0.3)', width=1, dash='dot'),
        showlegend=False))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0,1], tickvals=[0.25,0.5,0.75,1.0],
                                   tickfont=dict(size=10, color='#666'), gridcolor='#2a2a3e'),
                   angularaxis=dict(gridcolor='#2a2a3e', tickfont=dict(size=11)),
                   bgcolor='rgba(0,0,0,0)'),
        showlegend=False, margin=dict(l=50,r=50,t=30,b=30), height=320,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    return fig


# ── 톤 4사분면 차트 ──
TONE_QUADRANT_INFO = {
    "bright_light": {"ko": "청량", "color": "#74b9ff", "example": "솔라", "x": 0.75, "y": 0.25},
    "warm_light":   {"ko": "따뜻", "color": "#fdcb6e", "example": "휘인", "x": 0.25, "y": 0.25},
    "dark_heavy":   {"ko": "묵직", "color": "#e17055", "example": "화사", "x": 0.25, "y": 0.75},
    "bright_heavy": {"ko": "건조", "color": "#a29bfe", "example": "문별", "x": 0.75, "y": 0.75},
}

def render_tone_quadrant(vp):
    """톤 4사분면 Plotly 차트"""
    brightness = vp.get("brightness", 0.5)
    weight = vp.get("weight", 0.5)
    quadrant = vp.get("tone_quadrant", "unknown")
    quadrant_ko = vp.get("tone_quadrant_ko", "미분류")

    fig = go.Figure()

    # 4사분면 배경 영역
    for qkey, qinfo in TONE_QUADRANT_INFO.items():
        opacity = 0.25 if qkey == quadrant else 0.08
        fig.add_shape(type="rect",
            x0=qinfo["x"]-0.25, y0=qinfo["y"]-0.25, x1=qinfo["x"]+0.25, y1=qinfo["y"]+0.25,
            fillcolor=qinfo["color"], opacity=opacity, line=dict(width=0))
        # 사분면 라벨
        fig.add_annotation(x=qinfo["x"], y=qinfo["y"],
            text=f"<b>{qinfo['ko']}</b><br><span style='font-size:10px'>{qinfo['example']}</span>",
            showarrow=False, font=dict(size=13, color=qinfo["color"]),
            opacity=0.7 if qkey != quadrant else 1.0)

    # 분석 대상 점
    point_color = TONE_QUADRANT_INFO.get(quadrant, {}).get("color", "#fff")
    fig.add_trace(go.Scatter(
        x=[brightness], y=[weight], mode="markers+text",
        marker=dict(size=18, color=point_color, line=dict(width=2, color="#fff"),
                    symbol="diamond"),
        text=[f" {quadrant_ko}"], textposition="top right",
        textfont=dict(size=13, color=point_color, family="Noto Sans KR"),
        showlegend=False))

    # 축선
    fig.add_hline(y=0.5, line=dict(color="#444", width=1, dash="dot"))
    fig.add_vline(x=0.5, line=dict(color="#444", width=1, dash="dot"))

    fig.update_layout(
        xaxis=dict(range=[0, 1], title="← 어두운 ─── 밝기 ─── 밝은 →",
                   titlefont=dict(size=11, color="#888"), showgrid=False,
                   tickvals=[0, 0.5, 1], ticktext=["어둡", "", "밝음"],
                   tickfont=dict(size=10, color="#666")),
        yaxis=dict(range=[0, 1], title="← 가벼운 ─── 무게 ─── 묵직 →",
                   titlefont=dict(size=11, color="#888"), showgrid=False,
                   tickvals=[0, 0.5, 1], ticktext=["가벼운", "", "묵직"],
                   tickfont=dict(size=10, color="#666")),
        height=340, margin=dict(l=50, r=30, t=20, b=50),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig


def render_vocal_sub_cards(vp):
    """보컬 세부 지표 카드 렌더링"""
    cards_html = []

    # 1. 비브라토 특성
    vib_rate = vp.get("vibrato_rate_hz", 0)
    vib_depth = vp.get("vibrato_depth", 0)
    vib_reg = vp.get("vibrato_regularity", 0)
    vib_pres = vp.get("vibrato_presence", 0)
    if vib_rate > 0:
        vib_desc = "느리고 깊은 비브라토" if vib_rate < 5 else "빠르고 가벼운 비브라토" if vib_rate > 6 else "보통 속도"
        if vib_depth > 0.5: vib_desc += " · 폭이 큼"
        cards_html.append(f"""<div class="card" style="padding:1rem 1.2rem; border-left:3px solid #a29bfe;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-weight:600; color:#eee;">🎼 비브라토 특성</span>
                <span style="color:#a29bfe; font-size:0.85rem;">존재 비율 {vib_pres:.0%}</span>
            </div>
            <div class="detail-text" style="margin-top:0.4rem;">
                속도 <b style="color:#ddd;">{vib_rate:.1f}Hz</b> · 깊이 <b style="color:#ddd;">{vib_depth:.2f}st</b> · 규칙성 <b style="color:#ddd;">{vib_reg:.0%}</b>
            </div>
            <div class="explain">→ {vib_desc}</div>
        </div>""")

    # 2. 다이내믹 레인지
    dyn_db = vp.get("dynamic_range_db", 0)
    dyn_score = vp.get("dynamic_score", 0)
    if dyn_db > 0:
        dyn_color = "#00b894" if dyn_score >= 0.6 else "#fdcb6e" if dyn_score >= 0.3 else "#e17055"
        dyn_desc = "넓은 성량 변화 — 표현력 강함" if dyn_score >= 0.6 else "보통 수준의 성량 변화" if dyn_score >= 0.3 else "성량 변화 적음"
        cards_html.append(f"""<div class="card" style="padding:1rem 1.2rem; border-left:3px solid {dyn_color};">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-weight:600; color:#eee;">📢 다이내믹 레인지</span>
                <span style="color:{dyn_color}; font-weight:600;">{dyn_db:.1f} dB</span>
            </div>
            {_bar_html(dyn_score, dyn_color, 100)}
            <div class="explain">→ {dyn_desc}</div>
        </div>""")

    # 3. 호흡성(기식감)
    breath = vp.get("breathiness", 0)
    if breath > 0:
        br_color = "#74b9ff" if breath >= 0.5 else "#636e72"
        br_desc = "바람 섞인 음색 — 감성적·몽환적 질감" if breath >= 0.5 else "깨끗한 발성 — 선명한 음색"
        cards_html.append(f"""<div class="card" style="padding:1rem 1.2rem; border-left:3px solid {br_color};">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-weight:600; color:#eee;">💨 호흡성 (기식감)</span>
                <span style="color:{br_color}; font-weight:600;">{breath:.2f}</span>
            </div>
            {_bar_html(breath, br_color, 100)}
            <div class="explain">→ {br_desc}</div>
        </div>""")

    # 4. 어택 클린도
    attack = vp.get("attack_sharpness", 0)
    if attack > 0:
        atk_color = "#00b894" if attack >= 0.6 else "#fdcb6e"
        atk_desc = "발성 시작이 선명 — 절도 있는 보컬" if attack >= 0.6 else "부드럽게 시작하는 발성"
        cards_html.append(f"""<div class="card" style="padding:1rem 1.2rem; border-left:3px solid {atk_color};">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-weight:600; color:#eee;">⚡ 어택 클린도</span>
                <span style="color:{atk_color}; font-weight:600;">{attack:.2f}</span>
            </div>
            {_bar_html(attack, atk_color, 100)}
            <div class="explain">→ {atk_desc}</div>
        </div>""")

    # 5. 음역대 폭
    pitch_min = vp.get("pitch_min_hz", 0)
    pitch_max = vp.get("pitch_max_hz", 0)
    pitch_range = vp.get("pitch_range_semitones", 0)
    if pitch_range > 0:
        pr_color = "#00b894" if pitch_range >= 24 else "#fdcb6e" if pitch_range >= 12 else "#e17055"
        pr_desc = f"약 {pitch_range:.0f}반음 ({pitch_min:.0f}Hz ~ {pitch_max:.0f}Hz)"
        if pitch_range >= 24: pr_desc += " — 2옥타브 이상, 넓은 음역"
        elif pitch_range >= 12: pr_desc += " — 1옥타브 이상"
        cards_html.append(f"""<div class="card" style="padding:1rem 1.2rem; border-left:3px solid {pr_color};">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-weight:600; color:#eee;">🎹 음역대 폭</span>
                <span style="color:{pr_color}; font-weight:600;">{pitch_range:.0f} 반음</span>
            </div>
            {_bar_html(min(pitch_range/36, 1.0), pr_color, 100)}
            <div class="explain">→ {pr_desc}</div>
        </div>""")

    # 6. 성역대 구조 (흉성/믹스/두성)
    chest = vp.get("chest_voice_ratio", 0)
    head = vp.get("head_voice_ratio", 0)
    mix = vp.get("mix_voice_ratio", 0)
    if chest + head + mix > 0:
        cards_html.append(f"""<div class="card" style="padding:1rem 1.2rem; border-left:3px solid #fd79a8;">
            <div style="font-weight:600; color:#eee; margin-bottom:0.5rem;">🫁 성역대 구조</div>
            <div style="display:flex; gap:0.5rem; align-items:center; margin-bottom:0.3rem;">
                <span style="color:#e17055; font-size:0.85rem; width:50px;">흉성</span>
                <div style="flex:1;">{_bar_html(chest, '#e17055', 100)}</div>
                <span style="color:#aaa; font-size:0.85rem; width:40px; text-align:right;">{chest:.0%}</span>
            </div>
            <div style="display:flex; gap:0.5rem; align-items:center; margin-bottom:0.3rem;">
                <span style="color:#fdcb6e; font-size:0.85rem; width:50px;">믹스</span>
                <div style="flex:1;">{_bar_html(mix, '#fdcb6e', 100)}</div>
                <span style="color:#aaa; font-size:0.85rem; width:40px; text-align:right;">{mix:.0%}</span>
            </div>
            <div style="display:flex; gap:0.5rem; align-items:center;">
                <span style="color:#74b9ff; font-size:0.85rem; width:50px;">두성</span>
                <div style="flex:1;">{_bar_html(head, '#74b9ff', 100)}</div>
                <span style="color:#aaa; font-size:0.85rem; width:40px; text-align:right;">{head:.0%}</span>
            </div>
        </div>""")

    # 7. 공명 패턴
    f1 = vp.get("formant_1_hz", 0)
    f2 = vp.get("formant_2_hz", 0)
    res_type = vp.get("resonance_type", "unknown")
    res_kr = {"chest_dominant": "가슴 공명 중심", "nasal": "비강 공명 중심",
              "head_dominant": "두성 공명 중심", "mixed": "복합 공명"}.get(res_type, "미분류")
    if f1 > 0:
        cards_html.append(f"""<div class="card" style="padding:1rem 1.2rem; border-left:3px solid #00b894;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-weight:600; color:#eee;">🔊 공명 패턴</span>
                <span style="color:#00b894; font-size:0.85rem;">{res_kr}</span>
            </div>
            <div class="detail-text" style="margin-top:0.4rem;">
                F1: <b style="color:#ddd;">{f1:.0f}Hz</b> · F2: <b style="color:#ddd;">{f2:.0f}Hz</b>
            </div>
            <div class="explain">→ 포먼트 구조로 추정한 공명 패턴</div>
        </div>""")

    return "\n".join(cards_html)


def render_dashboard(report):
    meta = report.get("meta", {})
    scr = report.get("screening", {})
    v11 = report.get("interpret_11vars", {})
    comp = report.get("composites", {})
    diag = report.get("failure_diagnosis", {})
    ct = meta.get("content_type", "auto")
    ct_kr = {"vocal": "보컬 영상", "dance": "댄스 영상", "auto": "자동 감지"}.get(ct, ct)
    indicators = scr.get("indicators", {})

    name_disp = meta.get("name") or "(이름 미입력)"
    if meta.get("name_en"):
        name_disp += f"  ({meta['name_en']})"

    # ── 극단값 분석 ──
    measured_list = []
    outlier_list = []
    for iid, ind in indicators.items():
        if not ind.get("measured"): continue
        score = ind["score"]
        info = INDICATOR_DETAIL.get(str(iid), {})
        name = info.get("name", ind["name"])
        question = info.get("question", "")
        measured_list.append((name, score, iid, question))
        if score >= OUTLIER_THRESHOLD:
            outlier_list.append((name, score, "right", question))
        elif 0 < score <= OUTLIER_LOW_THRESHOLD:
            outlier_list.append((name, score, "left", question))

    measured_count = len(measured_list)
    sd = comp.get("system_dependency", 0)
    ft = diag.get("failure_type", "NONE")

    # ── 헤더 ──
    st.markdown(f"## 🎤 {name_disp}")
    sub_parts = [f"📹 {ct_kr}"]
    if meta.get("group"): sub_parts.append(f"👥 {meta['group']}")
    if meta.get("agency"): sub_parts.append(f"🏢 {meta['agency']}")
    sub_parts.append(f"📅 {meta.get('analysis_time','')[:10]}")
    st.caption("  ·  ".join(sub_parts))

    # ── ★ 다인원 감지 경고 (최우선 표시) ──
    is_multi = scr.get("multi_person_detected", False)
    est_count = scr.get("estimated_person_count", 1)
    mp_method = scr.get("multi_person_method", "")
    mp_notes = scr.get("multi_person_notes", "")

    if is_multi:
        method_kr = "동시 등장" if mp_method == "simultaneous" else "교차 등장"
        st.markdown(f"""<div class='multi-person-warning'>
            <b style='font-size:1.2rem; color:#e17055;'>🚨 다인원 영상 감지 — 분석 결과를 신뢰할 수 없습니다</b><br><br>
            이 영상에서 <b style='color:#ff7675;'>약 {est_count}명</b>의 인물이 <b>{method_kr}</b>하는 것이 감지되었습니다.<br>
            여러 사람의 목소리·얼굴·동작이 섞여서 분석되었기 때문에, 아래 점수는 <b>특정 개인의 특성을 반영하지 않습니다.</b><br><br>
            📌 <b>해결 방법:</b> 분석하려는 연습생 <b>1명만 나오는 영상</b>을 사용해 주세요.<br>
            <span style='font-size:0.85rem; color:#b2bec3;'>감지 상세: {mp_notes}</span>
        </div>""", unsafe_allow_html=True)

    # ── ★ 한 줄 결론 ──
    st.markdown("")
    summary_parts = []

    if is_multi:
        summary_parts.append("🚨 <b>다인원 영상</b>이 감지되어 모든 지표가 무효화되었습니다. 1인 영상으로 재분석해 주세요.")

    if ct == "dance":
        # 음색 지표가 미측정인지 확인 (보컬 미감지)
        ind1 = indicators.get("1", {})
        ind2 = indicators.get("2", {})
        vocal_not_detected = (not ind1.get("measured", False)) and (not ind2.get("measured", False))
        if vocal_not_detected:
            summary_parts.append("📌 <b>댄스 영상</b>에서 사람 목소리가 감지되지 않았습니다. 배경 음악(MR)만 있으므로 <b>음색 분석은 건너뛰고 리듬 분석만 수행</b>했습니다.")
        else:
            summary_parts.append("📌 <b>댄스 영상</b>이지만 사람 목소리가 감지되어 음색도 분석했습니다. 다만 MR이 섞여 있어 참고 수준입니다.")

    if measured_count == 0:
        summary_parts.append("⚠️ 측정된 지표가 없습니다. 영상에서 오디오를 추출하지 못했을 수 있습니다.")
    else:
        summary_parts.append(f"현재 <b>100개 분석 항목 중 {measured_count}개</b>를 측정했습니다 (오디오 기반).")

    if outlier_list:
        names = ", ".join([f"<b style='color:#a29bfe'>{n}</b>" for n, _, _, _ in outlier_list])
        summary_parts.append(f"💎 {names} 에서 극단값이 발견되었습니다 — <b>원석 후보 가능성이 있습니다.</b>")
    else:
        best = max(measured_list, key=lambda x: x[1]) if measured_list else None
        if best and best[1] >= NOTABLE_THRESHOLD:
            summary_parts.append(f"🔍 아직 극단값은 없지만, <b>{best[0]}</b>({best[1]:.2f})이 주목할 만합니다. 보컬 영상으로 교차 검증을 권장합니다.")
        elif best:
            summary_parts.append(f"현재 측정된 항목에서는 뚜렷한 특이점이 보이지 않습니다. 다른 유형의 영상으로 추가 분석해보세요.")

    if sd >= 0.8:
        summary_parts.append(f"🏢 <b>기획사 의존도가 {sd:.0%}</b>로 높습니다 — 혼자서는 아직 경쟁력이 부족한 구조입니다.")

    if ft not in ("NONE", ""):
        ft_kr = {"NCPS": "포지션 정체(그룹에 묻힐 위험)", "RNCS": "역량 분산(핵심이 불분명)", "MIXED": "복합 위험"}.get(ft, ft)
        summary_parts.append(f"⚠️ <b>{ft_kr}</b> 경고가 감지되었습니다.")

    st.markdown(f"<div class='summary-box'>{'<br>'.join(summary_parts)}</div>", unsafe_allow_html=True)

    # ── 측정 결과 카드 ──
    c1, c2, c3 = st.columns(3)
    with c1:
        if outlier_list:
            st.markdown(f"""<div class="card" style="border:1px solid rgba(162,155,254,0.4);">
                <div class="card-title">💎 극단값 발견</div>
                <div class="big-number purple">{len(outlier_list)}개</div>
                <div class="big-label">남다른 특이점이 있음</div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(_metric_card("💎 극단값", "없음", f"측정된 {measured_count}개 중", "gray"), unsafe_allow_html=True)
    with c2:
        sd_color = "red" if sd >= 0.8 else "yellow" if sd >= 0.5 else "green"
        sd_text = "혼자서는 어려움" if sd >= 0.8 else "보통" if sd >= 0.5 else "혼자서도 가능"
        st.markdown(_metric_card("🏢 기획사 의존도", f"{sd:.0%}", sd_text, sd_color), unsafe_allow_html=True)
    with c3:
        diag_kr = {"NONE": "위험 없음", "NCPS": "주의 필요", "RNCS": "주의 필요", "MIXED": "위험"}.get(ft, ft)
        diag_color = "green" if ft == "NONE" else "red"
        st.markdown(_metric_card("🛡️ 실패 위험", diag_kr, f"10개 조건 중 {diag.get('ncps_met',0)+diag.get('rncs_met',0)}개 해당", diag_color), unsafe_allow_html=True)

    st.markdown("")

    # ── 측정 결과 상세 — 질문형 카드 ──
    st.markdown('<div class="section-title">🎯 이 사람의 고유한 점은?</div>', unsafe_allow_html=True)

    for iid, ind in indicators.items():
        info = INDICATOR_DETAIL.get(str(iid), {})
        name = info.get("name", ind["name"])
        question = info.get("question", "")
        score = ind["score"] if ind["measured"] else 0
        meaning, meaning_color = _score_meaning(score, ind["measured"])
        oc = _outlier_color(score)

        if ind["measured"]:
            bar = _bar_html(score, oc, 100)
            is_outlier = score >= OUTLIER_THRESHOLD or (0 < score <= OUTLIER_LOW_THRESHOLD)
            badge = '<span class="tag tag-outlier" style="margin-left:0.5rem;">극단값!</span>' if is_outlier else ''

            st.markdown(f"""<div class="card" style="padding:1rem 1.3rem;{'border:1px solid rgba(162,155,254,0.3);' if is_outlier else ''}">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-weight:600; color:#eee;">{info.get('icon','')} {name}{badge}</span>
                    <span style="font-size:1.3rem; font-weight:700; color:{oc};">{score:.2f}</span>
                </div>
                <div style="color:#74b9ff; font-size:0.85rem; margin:0.3rem 0; font-style:italic;">Q. {question}</div>
                {bar}
                <div style="display:flex; justify-content:space-between; align-items:center; margin-top:0.3rem;">
                    <span style="color:{meaning_color}; font-size:0.85rem; font-weight:500;">→ {meaning}</span>
                    <span style="color:#555; font-size:0.75rem;">0 ← 평범 — 독특 → 1</span>
                </div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""<div class="card" style="padding:1rem 1.3rem; opacity:0.5;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-weight:600; color:#666;">{info.get('icon','')} {name}</span>
                    <span style="font-size:1rem; color:#555;">준비 중</span>
                </div>
                <div style="color:#555; font-size:0.85rem; margin:0.3rem 0; font-style:italic;">Q. {question}</div>
                <div class="detail-text">이 항목은 현재 기술적 제한으로 측정하지 못했습니다.</div>
            </div>""", unsafe_allow_html=True)

    # 측정 근거 (펼치기)
    measured_inds = {k:v for k,v in indicators.items() if v.get("measured")}
    if measured_inds:
        with st.expander("📋 AI가 실제로 측정한 내용 보기"):
            for iid, ind in measured_inds.items():
                info = INDICATOR_DETAIL.get(str(iid), {})
                st.markdown(f"**{info.get('icon','')} {info.get('name', ind['name'])}**")
                st.markdown(f"<div class='detail-text'>{info.get('detail','')}</div>", unsafe_allow_html=True)
                if ind.get("notes"):
                    notes = ind["notes"]
                    notes = notes.replace("유형=ahead", "비트보다 앞서감").replace("유형=behind", "비트보다 뒤처짐").replace("유형=on_beat", "정박")
                    st.code(f"측정 근거: {notes}", language=None)
                st.markdown("")

    st.markdown("")

    # ── ★ 보컬 프로파일 (v2) ──
    vp = report.get("vocal_profile")
    if vp and vp.get("tone_quadrant", "unknown") != "unknown":
        st.markdown('<div class="section-title">🎤 보컬 프로파일 — 톤 4사분면 분류</div>', unsafe_allow_html=True)
        st.markdown("""<div class="detail-text" style="margin-bottom:0.8rem;">
            마마무 4인의 톤 구조를 기준으로, 이 사람의 목소리가 어떤 유형에 해당하는지 자동 분류합니다.
            그룹 조합 시 서로 다른 사분면의 보컬이 모여야 전 주파수 대역을 균형 있게 채울 수 있습니다.
        </div>""", unsafe_allow_html=True)

        col_chart, col_info = st.columns([1.2, 1])
        with col_chart:
            fig = render_tone_quadrant(vp)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        with col_info:
            tq = vp.get("tone_quadrant", "unknown")
            tq_ko = vp.get("tone_quadrant_ko", "미분류")
            tq_info = TONE_QUADRANT_INFO.get(tq, {})
            tq_color = tq_info.get("color", "#888")
            tq_example = tq_info.get("example", "")
            confidence = vp.get("tone_confidence", 0)
            st.markdown(f"""<div class="card" style="border:1px solid {tq_color}; text-align:center; padding:1.5rem;">
                <div style="font-size:0.85rem; color:#888; margin-bottom:0.5rem;">이 사람의 톤 유형</div>
                <div style="font-size:2.2rem; font-weight:700; color:{tq_color};">{tq_ko}</div>
                <div style="font-size:0.9rem; color:#aaa; margin-top:0.3rem;">유사 레퍼런스: {tq_example}</div>
                <div style="margin-top:0.8rem;">
                    <span style="font-size:0.8rem; color:#666;">밝기 {vp.get('brightness',0):.2f}</span>
                    <span style="margin:0 0.5rem; color:#444;">|</span>
                    <span style="font-size:0.8rem; color:#666;">무게 {vp.get('weight',0):.2f}</span>
                </div>
                <div style="margin-top:0.5rem; font-size:0.78rem; color:#555;">분류 신뢰도: {confidence:.0%}</div>
            </div>""", unsafe_allow_html=True)

        # 보컬 세부 지표 카드
        st.markdown('<div class="section-title">🔬 보컬 세부 지표</div>', unsafe_allow_html=True)
        st.markdown("""<div class="detail-text" style="margin-bottom:0.8rem;">
            음색의 세부 특성을 8가지 하위 지표로 분해합니다. 각 지표는 독립적으로 평가되며, 종합 점수로 합산하지 않습니다.
        </div>""", unsafe_allow_html=True)

        sub_cards_html = render_vocal_sub_cards(vp)
        if sub_cards_html:
            st.markdown(sub_cards_html, unsafe_allow_html=True)
        else:
            st.caption("보컬 세부 지표 데이터가 없습니다.")

        st.markdown("")

    # ── 100차원 중 얼마나 봤는가 ──
    st.markdown('<div class="section-title">📐 전체 100개 항목 중 얼마나 측정했나?</div>', unsafe_allow_html=True)
    st.markdown("""<div class="detail-text" style="margin-bottom:0.8rem;">
        이 시스템은 총 100개 항목으로 사람을 분석합니다. 현재는 오디오 기반 항목만 자동 측정 가능하며,
        나머지는 영상 분석 기술 준비 중이거나 사람이 직접 판단해야 하는 영역입니다.
    </div>""", unsafe_allow_html=True)

    cat_cols = st.columns(3)
    for idx, (cat_key, cat_info) in enumerate(DIMENSION_CATEGORIES.items()):
        # 이 카테고리에서 실제 측정된 지표 수
        measured_in_cat = sum(1 for iid in cat_info["indicator_ids"]
                             if iid in indicators and indicators[iid].get("measured"))
        total = cat_info["total"]
        col = cat_cols[idx % 3]
        with col:
            pct = int(measured_in_cat / total * 100) if total > 0 else 0
            st.markdown(f"""<div class="dim-category" style="border-left-color:{cat_info['color']};">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-weight:600; color:#eee;">{cat_info['icon']} {cat_info['name']}</span>
                    <span style="font-size:0.8rem; color:{cat_info['color']};">{measured_in_cat} / {total}개</span>
                </div>
                {_bar_html(measured_in_cat/total if total else 0, cat_info['color'], 100)}
                <div class="detail-text" style="font-size:0.78rem;">{cat_info['summary']}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("")

    # ── 역량 해석 ──
    st.markdown('<div class="section-title">📊 종합 역량은 어떤가?</div>', unsafe_allow_html=True)
    st.markdown("""<div class="detail-text" style="margin-bottom:0.8rem;">
        위의 측정값들을 종합해서 11가지 역량으로 해석합니다.
        6개는 AI가 자동 계산했고, 5개는 사람이 직접 관찰해야 해서 아직 기본값(보통)입니다.
    </div>""", unsafe_allow_html=True)

    # AI 측정 변수
    ai_vars = {k:v for k,v in v11.items() if v.get("ai_measurable")}
    human_vars = {k:v for k,v in v11.items() if not v.get("ai_measurable")}

    if ai_vars:
        st.markdown("**🤖 AI가 계산한 역량:**")
        for code, var in ai_vars.items():
            score = var["score"]
            level = var["level"]
            oc = _outlier_color(score)
            name = VAR_KR.get(code, code)
            explain = VAR_EXPLAIN.get(code, "")
            level_kr = LEVEL_KR.get(level, level)
            level_exp = LEVEL_EXPLAIN.get(level, "")
            meaning, mc = _score_meaning(score)

            st.markdown(f"""<div class="card" style="padding:0.8rem 1.2rem;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-weight:600; color:#eee; font-size:0.95rem;">{name}</span>
                    <span style="color:{oc}; font-weight:600;">{level_kr} ({score:.2f})</span>
                </div>
                {_bar_html(score, oc, 100)}
                <div class="detail-text">{explain}</div>
                <div class="explain">→ {level_exp}</div>
            </div>""", unsafe_allow_html=True)

    if human_vars:
        st.markdown("**👤 사람이 관찰해야 하는 역량** (현재 기본값):")
        for code, var in human_vars.items():
            name = VAR_KR.get(code, code)
            explain = VAR_EXPLAIN.get(code, "")
            st.markdown(f"""<div class="card" style="padding:0.8rem 1.2rem; opacity:0.6;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-weight:500; color:#888;">{name}</span>
                    <span style="color:#555;">미입력</span>
                </div>
                <div class="detail-text">{explain}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("")

    # ── 구조 진단 ──
    st.markdown('<div class="section-title">⚡ 이 사람의 구조적 강점과 약점</div>', unsafe_allow_html=True)
    st.markdown("""<div class="detail-text" style="margin-bottom:0.8rem;">
        아이돌의 커리어를 결정짓는 구조적 요소들입니다. 각 항목의 질문에 답을 보세요.
    </div>""", unsafe_allow_html=True)

    cols = st.columns(2)
    for i, (key, val) in enumerate(comp.items()):
        info = COMPOSITE_DETAIL.get(key, {})
        name = info.get("name", key)
        icon = info.get("icon", "")
        reverse = info.get("reverse", False)
        color = _color(val, reverse=reverse)
        question = info.get("question", "")
        comment = info.get("high" if val >= 0.6 else "low", "")

        with cols[i % 2]:
            st.markdown(f"""<div class="card">
                <div class="card-title">{icon} {name}</div>
                <div style="color:#74b9ff; font-size:0.85rem; margin-bottom:0.4rem; font-style:italic;">Q. {question}</div>
                <div class="big-number" style="color:{color}; font-size:1.8rem;">{val:.2f}</div>
                {_bar_html(val, color, 100)}
                <div style="color:{color}; font-size:0.85rem; font-weight:500; margin-top:0.3rem;">→ {comment}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("")

    # ── 실패 구조 진단 ──
    st.markdown('<div class="section-title">🛡️ 실패 위험 체크</div>', unsafe_allow_html=True)
    st.markdown("""<div class="detail-text" style="margin-bottom:0.8rem;">
        K-POP 30년간 반복된 실패 패턴 2가지를 점검합니다. 5개 조건 중 3개 이상 해당하면 위험 신호입니다.
    </div>""", unsafe_allow_html=True)

    ncps_d = diag.get("ncps_detail", {})
    rncs_d = diag.get("rncs_detail", {})

    col_n, col_r = st.columns(2)
    with col_n:
        n_met = diag.get("ncps_met", 0)
        n_color = "red" if n_met >= 3 else "yellow" if n_met >= 2 else "green"
        st.markdown(f"""<div class="card">
            <div class="card-title">패턴 1: 그룹에 묻히는 구조</div>
            <div style="color:#74b9ff; font-size:0.82rem; margin-bottom:0.4rem; font-style:italic;">
                그룹이 해체되면 혼자 살아남을 수 있는가?
            </div>
            <div class="big-number {n_color}">{n_met}/5</div>
            <div class="big-label">{'⚠️ 3개 이상 — 위험 구조' if n_met >= 3 else '✅ 현재 안전' if n_met < 2 else '⚡ 주시 필요'}</div>
        </div>""", unsafe_allow_html=True)
        for cond, met in ncps_d.items():
            icon = "🔴" if met else "⚪"
            st.markdown(f"&nbsp;&nbsp;{icon} {cond}")
        if not ncps_d:
            st.caption("  조건 데이터 없음")

    with col_r:
        r_met = diag.get("rncs_met", 0)
        r_color = "red" if r_met >= 3 else "yellow" if r_met >= 2 else "green"
        st.markdown(f"""<div class="card">
            <div class="card-title">패턴 2: 핵심이 없는 구조</div>
            <div style="color:#74b9ff; font-size:0.82rem; margin-bottom:0.4rem; font-style:italic;">
                '이 사람하면 이것'이라는 핵심이 있는가?
            </div>
            <div class="big-number {r_color}">{r_met}/5</div>
            <div class="big-label">{'⚠️ 3개 이상 — 위험 구조' if r_met >= 3 else '✅ 현재 안전' if r_met < 2 else '⚡ 주시 필요'}</div>
        </div>""", unsafe_allow_html=True)
        for cond, met in rncs_d.items():
            icon = "🔴" if met else "⚪"
            st.markdown(f"&nbsp;&nbsp;{icon} {cond}")
        if not rncs_d:
            st.caption("  조건 데이터 없음")

    st.markdown("")

    # ── 다음 단계 ──
    st.markdown('<div class="section-title">📌 더 정확한 분석을 위해</div>', unsafe_allow_html=True)
    st.markdown("""<div class="card">
        <div class="detail-text" style="line-height:2;">
            • <b style="color:#ddd;">다른 유형 영상 추가</b> — 보컬 영상 + 댄스 영상을 각각 분석하면 더 많은 항목에서 특이점을 찾을 수 있습니다.<br>
            • <b style="color:#ddd;">다른 시기 영상 추가</b> — 같은 사람의 예전 영상과 최근 영상을 비교하면 성장 속도를 측정할 수 있습니다.<br>
            • <b style="color:#ddd;">사람 관찰 입력</b> — 관객 소통, 자기 객관화 등 5가지를 직접 입력하면 실패 위험 진단이 정확해집니다.
        </div>
    </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════
# 메인 페이지 (온보딩)
# ══════════════════════════════════════
def _render_main_page():
    # ── 히어로 ──
    st.markdown("""
    <div style="text-align:center; padding:2rem 0 1rem 0;">
        <div style="font-size:3rem; margin-bottom:0.5rem;">🎤</div>
        <div style="font-size:1.8rem; font-weight:700; color:#eee;">idol_scout</div>
        <div style="font-size:1rem; color:#a29bfe; margin-top:0.4rem; font-weight:500;">
            AI가 아이돌 원석을 찾아주는 시스템
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 핵심 원리 (쉬운 말) ──
    st.markdown("""
    <div class="paradigm-box" style="text-align:center; padding:1.5rem;">
        <div style="font-size:1.05rem; color:#ddd; margin-bottom:0.8rem; line-height:1.8;">
            이 시스템은 <span style="color:#e17055; font-weight:600;">종합 점수로 줄 세우지 않습니다.</span><br>
            <span style="color:#a29bfe; font-weight:600;">"이 목소리에 남들과 확 다른 점이 있는가?"</span>를 봅니다.
        </div>
        <div class="detail-text" style="max-width:600px; margin:0 auto; text-align:left;">
            마마무가 K-POP 보컬 최강인 이유는 4명의 <b style="color:#ddd;">톤이 서로 다른 사분면</b>을 채우기 때문입니다.
            화사의 묵직함, 솔라의 청량함, 휘인의 따뜻함, 문별의 건조함 — 이 조합이 만드는 시너지가 핵심입니다.
            이 시스템은 <b style="color:#ddd;">보컬 톤의 독특성</b>을 과학적으로 측정하고, 최적의 그룹 조합을 찾습니다.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")

    # ── 사용 방법 ──
    st.markdown('<div class="section-title">📖 이렇게 사용하세요</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="card">
        <div style="display:flex; gap:1.5rem; flex-wrap:wrap;">
            <div style="flex:1; min-width:180px;">
                <div style="font-size:1.6rem; margin-bottom:0.4rem;">①</div>
                <div style="font-weight:600; color:#eee; margin-bottom:0.3rem;">영상 링크 붙여넣기</div>
                <div class="detail-text">좌측에 YouTube 또는 Instagram 영상 주소를 넣으세요.</div>
            </div>
            <div style="flex:1; min-width:180px;">
                <div style="font-size:1.6rem; margin-bottom:0.4rem;">②</div>
                <div style="font-weight:600; color:#eee; margin-bottom:0.3rem;">영상 유형 고르기</div>
                <div class="detail-text"><b style="color:#74b9ff">보컬</b> — 노래 영상<br>
                <b style="color:#74b9ff">댄스</b> — 안무 영상<br>
                <b style="color:#74b9ff">자동</b> — AI가 판단</div>
            </div>
            <div style="flex:1; min-width:180px;">
                <div style="font-size:1.6rem; margin-bottom:0.4rem;">③</div>
                <div style="font-weight:600; color:#eee; margin-bottom:0.3rem;">결과 확인</div>
                <div class="detail-text">AI가 1~2분 안에 분석하고,
                "이 사람만의 독특한 점"이 있는지 알려줍니다.</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")

    # ── AI가 보는 것 ──
    st.markdown('<div class="section-title">🔍 AI는 무엇을 보나요?</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""<div class="card" style="border-top:3px solid #74b9ff;">
            <div class="card-title" style="color:#74b9ff;">🎤 보컬 톤 분석 (핵심)</div>
            <div class="detail-text">
                <b style="color:#ddd;">음색이 얼마나 독특한가?</b><br>
                목소리의 음색 지문(MFCC)을 분석하고,
                톤 4사분면(청량/따뜻/묵직/건조)으로 자동 분류합니다.
                비브라토, 호흡성, 공명 패턴, 음역대 등
                8가지 하위 지표를 세밀하게 측정합니다.<br><br>
                ✅ 현재 자동 측정 가능
            </div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("""<div class="card" style="border-top:3px solid #fd79a8;">
            <div class="card-title" style="color:#fd79a8;">🥁 리듬 분석</div>
            <div class="detail-text">
                <b style="color:#ddd;">비트를 타는 방식이 고유한가?</b><br>
                비트보다 살짝 앞서가는지, 뒤에 여유있게 실리는지,
                정확히 맞추는지를 봅니다.
                이건 거의 바뀌지 않는 타고난 특성입니다.<br><br>
                ✅ 현재 자동 측정 가능
            </div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown("""<div class="card" style="border-top:3px solid #fdcb6e;">
            <div class="card-title" style="color:#fdcb6e;">👤 외모·동작·표정</div>
            <div class="detail-text">
                <b style="color:#ddd;">얼굴, 춤, 표정이 독특한가?</b><br>
                카메라 앞에서의 존재감, 동작의 고유성,
                표정 변화의 개성 등을 분석합니다.<br><br>
                ⏳ 기술 준비 중 (곧 추가 예정)
            </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")

    # ── 실패 구조 ──
    st.markdown('<div class="section-title">🛡️ 실패 위험도 미리 알 수 있나요?</div>', unsafe_allow_html=True)
    fc1, fc2 = st.columns(2)
    with fc1:
        st.markdown("""<div class="card" style="border-top:3px solid #e17055;">
            <div class="card-title" style="color:#e17055;">그룹에 묻히는 구조</div>
            <div class="detail-text">
                그룹 안에서 핵심 역할이 없으면, 그룹이 해체될 때 혼자 살아남기 어렵습니다.
                K-POP에서 반복적으로 나타나는 실패 패턴입니다.
            </div>
        </div>""", unsafe_allow_html=True)
    with fc2:
        st.markdown("""<div class="card" style="border-top:3px solid #fdcb6e;">
            <div class="card-title" style="color:#fdcb6e;">핵심이 없는 구조</div>
            <div class="detail-text">
                인지도는 높은데 "이 사람하면 이것"이라는 핵심이 없으면,
                아무리 많이 알려져도 진짜 팬이 생기지 않는 구조입니다.
            </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")
    st.markdown("""<div style="text-align:center; padding:1.5rem; color:#666; font-size:0.9rem;">
        👈 좌측에서 영상 주소를 넣고 <b style="color:#aaa;">분석 시작</b>을 눌러보세요
    </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════
# 톤 조합 시뮬레이션
# ══════════════════════════════════════

def _get_vocal_reports():
    """보컬 프로파일이 있는 리포트만 필터링"""
    reports = load_reports()
    vocal_reports = []
    for r in reports:
        vp = r.get("vocal_profile")
        if vp and vp.get("tone_quadrant", "unknown") != "unknown":
            vocal_reports.append(r)
    return vocal_reports


def _calc_quadrant_coverage(members_vp):
    """4사분면 커버리지 계산 — 몇 개 사분면을 채우는가"""
    quadrants_hit = set()
    for vp in members_vp:
        quadrants_hit.add(vp.get("tone_quadrant", "unknown"))
    quadrants_hit.discard("unknown")
    return quadrants_hit


def _calc_tone_spread(members_vp):
    """톤 분산도 — 4명이 2D 공간에서 얼마나 넓게 퍼져 있는가 (0~1)"""
    if len(members_vp) < 2:
        return 0.0
    points = [(vp.get("brightness", 0.5), vp.get("weight", 0.5)) for vp in members_vp]
    # 모든 쌍 간의 유클리드 거리 평균
    dists = []
    for i in range(len(points)):
        for j in range(i+1, len(points)):
            d = ((points[i][0] - points[j][0])**2 + (points[i][1] - points[j][1])**2) ** 0.5
            dists.append(d)
    # 최대 거리는 대각선 √2 ≈ 1.414
    avg_dist = sum(dists) / len(dists) if dists else 0
    return min(avg_dist / 0.7, 1.0)  # 0.7 이상이면 매우 넓게 퍼진 것


def _calc_combination_score_components(members_vp):
    """조합 평가 — 종합 점수 없이 각 차원 독립 표시"""
    quadrants = _calc_quadrant_coverage(members_vp)
    spread = _calc_tone_spread(members_vp)
    # 각 사분면에 몇 명이 있는지
    q_counts = {}
    for vp in members_vp:
        q = vp.get("tone_quadrant", "unknown")
        q_counts[q] = q_counts.get(q, 0) + 1
    # 중복 사분면 수 (같은 사분면에 2명 이상)
    overlap_count = sum(1 for c in q_counts.values() if c > 1)
    return {
        "quadrants_covered": len(quadrants),
        "quadrants_list": quadrants,
        "spread": spread,
        "overlap_count": overlap_count,
        "quadrant_distribution": q_counts,
    }


def render_combination_chart(members_data):
    """4명의 톤 위치를 하나의 4사분면 차트에 표시"""
    fig = go.Figure()

    # 4사분면 배경
    for qkey, qinfo in TONE_QUADRANT_INFO.items():
        fig.add_shape(type="rect",
            x0=qinfo["x"]-0.25, y0=qinfo["y"]-0.25, x1=qinfo["x"]+0.25, y1=qinfo["y"]+0.25,
            fillcolor=qinfo["color"], opacity=0.08, line=dict(width=0))
        fig.add_annotation(x=qinfo["x"], y=qinfo["y"],
            text=f"<b>{qinfo['ko']}</b><br><span style='font-size:10px'>{qinfo['example']}</span>",
            showarrow=False, font=dict(size=12, color=qinfo["color"]), opacity=0.5)

    # 각 멤버 점
    member_colors = ["#ff6b6b", "#4ecdc4", "#ffe66d", "#a29bfe"]
    member_symbols = ["diamond", "circle", "square", "star"]
    for i, md in enumerate(members_data):
        vp = md["vocal_profile"]
        name = md["name"]
        tq = vp.get("tone_quadrant", "unknown")
        tq_ko = vp.get("tone_quadrant_ko", "미분류")
        brightness = vp.get("brightness", 0.5)
        weight = vp.get("weight", 0.5)
        color = member_colors[i % len(member_colors)]

        fig.add_trace(go.Scatter(
            x=[brightness], y=[weight], mode="markers+text",
            marker=dict(size=16, color=color, line=dict(width=2, color="#fff"),
                        symbol=member_symbols[i % len(member_symbols)]),
            text=[f" {name}"], textposition="top right",
            textfont=dict(size=12, color=color, family="Noto Sans KR"),
            name=f"{name} ({tq_ko})", showlegend=True))

    # 축선
    fig.add_hline(y=0.5, line=dict(color="#444", width=1, dash="dot"))
    fig.add_vline(x=0.5, line=dict(color="#444", width=1, dash="dot"))

    fig.update_layout(
        xaxis=dict(range=[0, 1], title="← 어두운 ─── 밝기 ─── 밝은 →",
                   titlefont=dict(size=11, color="#888"), showgrid=False,
                   tickvals=[0, 0.5, 1], ticktext=["어둡", "", "밝음"],
                   tickfont=dict(size=10, color="#666")),
        yaxis=dict(range=[0, 1], title="← 가벼운 ─── 무게 ─── 묵직 →",
                   titlefont=dict(size=11, color="#888"), showgrid=False,
                   tickvals=[0, 0.5, 1], ticktext=["가벼운", "", "묵직"],
                   tickfont=dict(size=10, color="#666")),
        height=420, margin=dict(l=50, r=30, t=30, b=50),
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5,
                    font=dict(size=11)),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig


# ══════════════════════════════════════
# 100차원 보컬 벡터 분석 (v2)
# ══════════════════════════════════════

def _render_100dim_intro():
    """100차원 분석 소개 페이지"""
    st.markdown("""
    <div class="card">
        <div class="card-title">🧬 100차원 보컬 벡터 분석</div>
        <p style="color:#aaa; line-height:1.8;">
            영상 URL 하나로 <b>57개 음향 지표</b>를 자동 측정합니다.<br>
            YouTube, Instagram, TikTok 등 링크를 붙여넣으면 오디오를 추출하여 3개 축 × 6개 알고리즘으로 보컬의 모든 차원을 스캔합니다.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="card">
            <div class="card-title">A축: 기술적 안정성</div>
            <p style="color:#aaa;">음정정확도, 음역대, 비브라토,<br>다이내믹, 발성, 회복력</p>
            <div style="font-size:2rem; text-align:center;">🎯</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="card">
            <div class="card-title">B축: 음색 독창성</div>
            <p style="color:#aaa;">스펙트럼 특성, 배음 구조,<br>음색 시간 안정성, 고유성</p>
            <div style="font-size:2rem; text-align:center;">✨</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="card">
            <div class="card-title">C축: 정서 전달력</div>
            <p style="color:#aaa;">표현 도구 활용, 정서 종류,<br>진정성 (Phase 2 ML)</p>
            <div style="font-size:2rem; text-align:center;">💫</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="card" style="border-color:#4a4a6a;">
        <div class="card-title">📌 사용법</div>
        <p style="color:#aaa; line-height:1.8;">
            1. 왼쪽에 <b>영상 URL</b>(YouTube/Instagram/TikTok)을 붙여넣으세요<br>
            2. 가수명을 입력하고 <b>🧬 100차원 분석</b> 버튼을 누르세요<br>
            3. 자동으로 오디오를 추출하고 약 30초 후 57개 지표 측정 결과가 표시됩니다<br><br>
            <span style="color:#f0ad4e;">⚠️ 현재 Phase 1 — tier-1(음향분석) 57개만 측정됩니다.<br>
            tier-2(ML모델) 43개는 Phase 2에서 추가됩니다.</span>
        </p>
    </div>
    """, unsafe_allow_html=True)


def _run_100dim_analysis(url: str, artist_name: str):
    """100차원 분석 실행 (URL → 다운로드 → 측정 → 렌더링)"""
    from idol_scout.screener.downloader import download_video

    # 1) URL에서 오디오 다운로드
    with st.spinner("📥 영상 다운로드 중..."):
        dl = download_video(url)

    if not dl.success:
        st.error(f"❌ 다운로드 실패: {dl.error}")
        return

    # 오디오 경로 결정 (downloader가 추출한 audio 또는 video에서 변환)
    audio_path = dl.audio_path
    if not audio_path or not audio_path.exists():
        # video에서 오디오 추출 시도
        if dl.video_path and dl.video_path.exists():
            with st.spinner("🎵 오디오 추출 중..."):
                from idol_scout.screener.orchestrator import _extract_audio_from_video
                audio_path = _extract_audio_from_video(dl.video_path)

    if not audio_path or not audio_path.exists():
        st.error("❌ 오디오를 추출할 수 없습니다. 다른 URL을 시도해주세요.")
        return

    display_name = artist_name or dl.title or url

    # 2) 100차원 보컬 벡터 측정
    try:
        with st.spinner("🧬 100차원 보컬 벡터 측정 중... (약 30초)"):
            from idol_scout.screener.normalizer import screen_vocal_100
            vector = screen_vocal_100(audio_path, content_type="vocal_audio")

        st.toast(f"✅ 측정 완료! {vector.tier1_measured}개 지표 측정")
        _render_100dim_dashboard(vector, display_name)

    except Exception as e:
        st.error(f"❌ 분석 오류: {e}")
        import traceback
        st.code(traceback.format_exc())
    finally:
        # 임시 다운로드 파일 정리
        try:
            if dl.video_path and dl.video_path.exists():
                dl.video_path.unlink()
            if dl.audio_path and dl.audio_path.exists():
                dl.audio_path.unlink()
            if audio_path and audio_path.exists():
                audio_path.unlink()
        except Exception:
            pass


def _render_100dim_dashboard(vector, artist_name: str):
    """100차원 분석 결과 대시보드"""
    from idol_scout.screener.indicators_100 import INDICATOR_REGISTRY

    # ── 헤더 ──
    st.markdown(f"""
    <div class="card" style="border-color: {'#28a745' if vector.has_any_outlier else '#6c757d'};">
        <div class="card-title">🧬 {artist_name} — 100차원 보컬 벡터</div>
        <p style="color:#aaa;">
            톤: <b>{vector.tone_quadrant_ko}</b> |
            측정: <b>{vector.tier1_measured}</b>개 (tier-1) |
            처리시간: <b>{vector.processing_time_sec:.1f}</b>초
        </p>
        <p style="color: {'#28a745' if vector.has_any_outlier else '#dc3545'}; font-size:1.1rem;">
            {'🔥 ' + vector.outlier_summary if vector.has_any_outlier else '⚪ ' + vector.outlier_summary}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── 축별 극단값 요약 ──
    col_a, col_b, col_c = st.columns(3)
    _render_axis_card(col_a, "A축: 기술적 안정성", "🎯", vector.axis_a_outliers, vector)
    _render_axis_card(col_b, "B축: 음색 독창성", "✨", vector.axis_b_outliers, vector)
    _render_axis_card(col_c, "C축: 정서 전달력", "💫", vector.axis_c_outliers, vector)

    # ── 측정 성공 항목 상세 ──
    st.markdown("---")
    st.markdown("### 📊 지표별 상세 측정 결과")

    # 알고리즘 카테고리별 탭
    algo_tabs = st.tabs(["🎵 Pitch", "⚡ Energy", "🌈 Spectrum", "🎼 Vibrato", "📏 Range", "🔊 Formant"])

    algo_groups = {
        "Pitch_Analysis": 0,
        "Energy_Analysis": 1,
        "Spectrum_Analysis": 2,
        "Vibrato_Analysis": 3,
        "Voice_Range": 4,
        "Formant_Analysis": 5,
    }

    for iid, m in sorted(vector.measurements.items()):
        if not m.measured:
            continue
        spec = INDICATOR_REGISTRY.get(iid)
        if spec is None or spec.algorithm not in algo_groups:
            continue

        tab_idx = algo_groups[spec.algorithm]
        with algo_tabs[tab_idx]:
            pct_str = f"{m.percentile:.0f}%" if m.percentile is not None else "—"
            genius_str = f" | {m.genius_level}" if m.genius_level else ""

            # 백분위 바 색상
            if m.percentile is not None:
                if m.percentile >= 90:
                    bar_color = "#28a745"
                elif m.percentile >= 70:
                    bar_color = "#ffc107"
                elif m.percentile <= 15:
                    bar_color = "#17a2b8"  # 초이질
                else:
                    bar_color = "#6c757d"
                bar_width = min(100, max(2, m.percentile))
            else:
                bar_color = "#6c757d"
                bar_width = 0

            st.markdown(f"""
            <div style="background:#1e1e2e; border-radius:8px; padding:0.6rem 1rem; margin:0.3rem 0; border-left:3px solid {bar_color};">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="color:#ddd; font-size:0.9rem;">
                        <code style="color:#888;">{iid}</code> {m.name}
                    </span>
                    <span style="color:{bar_color}; font-weight:bold;">
                        {pct_str}{genius_str}
                    </span>
                </div>
                <div style="background:#2a2a3e; border-radius:4px; height:6px; margin-top:4px;">
                    <div style="background:{bar_color}; width:{bar_width}%; height:100%; border-radius:4px;"></div>
                </div>
                <div style="color:#666; font-size:0.75rem; margin-top:2px;">
                    raw: {m.raw_value:.4f} | 신뢰도: {m.confidence:.2f}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── 미측정 항목 (tier-2) ──
    with st.expander(f"⏳ 미측정 항목 ({100 - vector.total_measured}개 — Phase 2 ML 모델 필요)"):
        failed = {k: v for k, v in vector.measurements.items() if not v.measured}
        for iid in sorted(failed.keys()):
            m = failed[iid]
            st.caption(f"`{iid}` {m.name} — {m.error}")

    # ── JSON 내보내기 ──
    export_data = {
        "artist": artist_name,
        "tone_quadrant": vector.tone_quadrant_ko,
        "total_measured": vector.total_measured,
        "tier1_measured": vector.tier1_measured,
        "has_outlier": vector.has_any_outlier,
        "outlier_summary": vector.outlier_summary,
        "axis_a_outliers": vector.axis_a_outliers,
        "axis_b_outliers": vector.axis_b_outliers,
        "axis_c_outliers": vector.axis_c_outliers,
        "measurements": {
            iid: {
                "name": m.name,
                "raw_value": m.raw_value,
                "percentile": m.percentile,
                "confidence": m.confidence,
                "genius_level": m.genius_level,
                "measured": m.measured,
            }
            for iid, m in vector.measurements.items()
        }
    }
    st.download_button(
        "📥 100차원 데이터 내려받기",
        json.dumps(export_data, ensure_ascii=False, indent=2),
        file_name=f"vocal_vector_100_{artist_name}.json",
        mime="application/json"
    )


def _render_axis_card(col, title: str, icon: str, outlier_ids: list, vector):
    """축별 카드 렌더링"""
    count = len(outlier_ids)
    color = "#28a745" if count > 0 else "#6c757d"

    details = ""
    for iid in outlier_ids[:5]:
        m = vector.measurements.get(iid)
        if m:
            pct = f"{m.percentile:.0f}%" if m.percentile is not None else "?"
            details += f"<br>• {m.name} ({pct})"
    if count > 5:
        details += f"<br>• ... 외 {count - 5}개"

    with col:
        st.markdown(f"""
        <div class="card" style="border-color:{color}; text-align:center;">
            <div style="font-size:1.8rem;">{icon}</div>
            <div class="card-title">{title}</div>
            <div style="font-size:1.5rem; color:{color}; font-weight:bold;">
                {count}개 극단값
            </div>
            <div style="color:#aaa; font-size:0.8rem; text-align:left;">{details}</div>
        </div>
        """, unsafe_allow_html=True)


def _render_combination_page():
    """톤 조합 시뮬레이션 페이지"""
    st.markdown("## 🎵 걸그룹 톤 조합 시뮬레이션")
    st.markdown("""<div class="detail-text" style="margin-bottom:1rem;">
        분석된 후보들의 톤 4사분면 데이터를 비교합니다.
        마마무처럼 4개 사분면을 고르게 채우는 조합이 최적입니다.
        <b style="color:#ddd;">종합 점수는 산출하지 않으며</b>, 각 차원을 독립적으로 봅니다.
    </div>""", unsafe_allow_html=True)

    vocal_reports = _get_vocal_reports()

    if len(vocal_reports) < 2:
        st.warning(f"톤 조합 시뮬레이션에는 보컬 프로파일이 있는 분석 결과가 2개 이상 필요합니다. (현재 {len(vocal_reports)}개)")
        st.markdown("""<div class="card">
            <div class="detail-text" style="line-height:2;">
                • 보컬 영상으로 <b style="color:#ddd;">새 분석</b>을 실행하세요.<br>
                • 분석 결과에 <b style="color:#ddd;">톤 4사분면 데이터</b>가 포함되어야 합니다.<br>
                • 최소 2명, 최적 4명의 후보가 필요합니다.
            </div>
        </div>""", unsafe_allow_html=True)
        return

    # 후보 선택
    report_labels = []
    for r in vocal_reports:
        m = r.get("meta", {})
        n = m.get("name") or "(이름없음)"
        tq_ko = r.get("vocal_profile", {}).get("tone_quadrant_ko", "?")
        t = m.get("analysis_time", "")[:10]
        report_labels.append(f"{n} · {tq_ko} · {t}")

    st.markdown('<div class="section-title">👤 조합할 멤버를 선택하세요 (2~4명)</div>', unsafe_allow_html=True)
    selected_indices = st.multiselect(
        "후보 선택", range(len(report_labels)),
        format_func=lambda i: report_labels[i],
        max_selections=4,
        label_visibility="collapsed")

    if len(selected_indices) < 2:
        st.info("2명 이상 선택해 주세요.")
        # 전체 후보 톤 맵 미리보기
        if vocal_reports:
            st.markdown('<div class="section-title">📋 분석된 전체 후보 톤 맵</div>', unsafe_allow_html=True)
            all_members = []
            for r in vocal_reports:
                all_members.append({
                    "name": r.get("meta", {}).get("name") or "?",
                    "vocal_profile": r.get("vocal_profile", {})
                })
            fig = render_combination_chart(all_members)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        return

    # 선택된 멤버 데이터 구성
    members_data = []
    for idx in selected_indices:
        r = vocal_reports[idx]
        members_data.append({
            "name": r.get("meta", {}).get("name") or "(이름없음)",
            "vocal_profile": r.get("vocal_profile", {}),
            "report": r,
        })

    members_vp = [md["vocal_profile"] for md in members_data]

    # ── 조합 차트 ──
    st.markdown('<div class="section-title">🎯 톤 조합 시각화</div>', unsafe_allow_html=True)
    fig = render_combination_chart(members_data)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ── 조합 분석 ──
    comp = _calc_combination_score_components(members_vp)
    coverage = comp["quadrants_covered"]
    spread = comp["spread"]
    overlap = comp["overlap_count"]
    q_dist = comp["quadrant_distribution"]

    st.markdown('<div class="section-title">📊 조합 분석 결과</div>', unsafe_allow_html=True)
    st.markdown("""<div class="detail-text" style="margin-bottom:0.8rem;">
        각 차원을 독립적으로 평가합니다. 종합 점수는 없습니다.
    </div>""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        cov_color = "green" if coverage >= 3 else "yellow" if coverage >= 2 else "red"
        cov_text = "우수 — 대부분 커버" if coverage >= 3 else "보통" if coverage >= 2 else "부족"
        st.markdown(_metric_card("🎨 사분면 커버리지", f"{coverage}/4", cov_text, cov_color), unsafe_allow_html=True)
    with c2:
        sp_color = "green" if spread >= 0.6 else "yellow" if spread >= 0.3 else "red"
        sp_text = "넓게 분포 — 다양한 톤" if spread >= 0.6 else "보통 분포" if spread >= 0.3 else "밀집 — 유사한 톤"
        st.markdown(_metric_card("📐 톤 분산도", f"{spread:.0%}", sp_text, sp_color), unsafe_allow_html=True)
    with c3:
        ov_color = "green" if overlap == 0 else "yellow" if overlap == 1 else "red"
        ov_text = "겹침 없음 — 이상적" if overlap == 0 else f"{overlap}개 사분면 겹침"
        st.markdown(_metric_card("⚠️ 사분면 중복", f"{overlap}개", ov_text, ov_color), unsafe_allow_html=True)

    # ── 사분면별 분포 ──
    st.markdown("")
    st.markdown('<div class="section-title">🗂️ 사분면별 배치</div>', unsafe_allow_html=True)

    q_cols = st.columns(4)
    for i, (qkey, qinfo) in enumerate(TONE_QUADRANT_INFO.items()):
        with q_cols[i]:
            members_in_q = [md["name"] for md in members_data
                           if md["vocal_profile"].get("tone_quadrant") == qkey]
            count = len(members_in_q)
            border_style = f"border:1px solid {qinfo['color']};" if count > 0 else "opacity:0.4;"
            names_html = "<br>".join([f"<b style='color:#eee;'>{n}</b>" for n in members_in_q]) if members_in_q else "<span style='color:#555;'>비어 있음</span>"
            warning = ""
            if count > 1:
                warning = f"<div style='color:#e17055; font-size:0.78rem; margin-top:0.3rem;'>⚠️ {count}명 겹침</div>"
            elif count == 0:
                warning = "<div style='color:#fdcb6e; font-size:0.78rem; margin-top:0.3rem;'>빈 사분면</div>"

            st.markdown(f"""<div class="card" style="text-align:center; {border_style}">
                <div style="color:{qinfo['color']}; font-weight:600; margin-bottom:0.5rem;">{qinfo['ko']}</div>
                <div style="font-size:0.8rem; color:#666; margin-bottom:0.4rem;">({qinfo['example']} 유형)</div>
                {names_html}
                {warning}
            </div>""", unsafe_allow_html=True)

    # ── 비어 있는 사분면에 필요한 톤 추천 ──
    all_quadrants = set(TONE_QUADRANT_INFO.keys())
    missing = all_quadrants - comp["quadrants_list"]
    if missing and len(selected_indices) < 4:
        st.markdown("")
        st.markdown('<div class="section-title">💡 추천: 다음 멤버에 필요한 톤</div>', unsafe_allow_html=True)
        for qkey in missing:
            qinfo = TONE_QUADRANT_INFO[qkey]
            st.markdown(f"""<div class="card" style="border-left:3px solid {qinfo['color']}; padding:0.8rem 1.2rem;">
                <span style="color:{qinfo['color']}; font-weight:600;">{qinfo['ko']}</span> 유형 보컬이 필요합니다
                <span class="detail-text"> — {qinfo['example']}처럼 이 사분면을 채울 수 있는 후보를 찾으세요.</span>
            </div>""", unsafe_allow_html=True)

    # ── 멤버별 상세 비교 ──
    st.markdown("")
    st.markdown('<div class="section-title">👥 멤버별 보컬 특성 비교</div>', unsafe_allow_html=True)

    cols = st.columns(len(members_data))
    for i, md in enumerate(members_data):
        vp = md["vocal_profile"]
        tq_ko = vp.get("tone_quadrant_ko", "?")
        tq = vp.get("tone_quadrant", "unknown")
        tq_color = TONE_QUADRANT_INFO.get(tq, {}).get("color", "#888")
        with cols[i]:
            st.markdown(f"""<div class="card" style="border-top:3px solid {tq_color};">
                <div style="text-align:center; margin-bottom:0.5rem;">
                    <div style="font-weight:700; color:#eee; font-size:1.05rem;">{md['name']}</div>
                    <div style="color:{tq_color}; font-weight:600; font-size:0.9rem;">{tq_ko}</div>
                </div>
                <div style="font-size:0.82rem; color:#aaa; line-height:1.8;">
                    밝기: <b style="color:#ddd;">{vp.get('brightness',0):.2f}</b><br>
                    무게: <b style="color:#ddd;">{vp.get('weight',0):.2f}</b><br>
                    음역: <b style="color:#ddd;">{vp.get('pitch_range_semitones',0):.0f}</b>반음<br>
                    비브라토: <b style="color:#ddd;">{vp.get('vibrato_rate_hz',0):.1f}Hz</b><br>
                    호흡성: <b style="color:#ddd;">{vp.get('breathiness',0):.2f}</b><br>
                    다이내믹: <b style="color:#ddd;">{vp.get('dynamic_range_db',0):.1f}dB</b>
                </div>
            </div>""", unsafe_allow_html=True)

    # ── 자동 최적 조합 추천 (4명 이상 후보가 있을 때) ──
    if len(vocal_reports) >= 4 and len(selected_indices) != len(vocal_reports):
        st.markdown("")
        with st.expander("🤖 AI 자동 추천: 전체 후보 중 최적 4인 조합"):
            st.markdown("""<div class="detail-text" style="margin-bottom:0.8rem;">
                모든 후보 중에서 사분면 커버리지가 가장 넓고, 톤 분산도가 높은 4인 조합을 찾습니다.
                <b>종합 점수가 아닌</b>, 사분면 커버리지(더 많은 사분면) → 분산도(더 넓은 분포) 순으로 선별합니다.
            </div>""", unsafe_allow_html=True)

            all_vp = [(i, r.get("vocal_profile", {}), r.get("meta", {}).get("name") or "?")
                      for i, r in enumerate(vocal_reports)]

            best_combos = []
            max_group = min(4, len(all_vp))
            for combo in combinations(range(len(all_vp)), max_group):
                combo_vp = [all_vp[c][1] for c in combo]
                comp_c = _calc_combination_score_components(combo_vp)
                best_combos.append({
                    "indices": combo,
                    "names": [all_vp[c][2] for c in combo],
                    "coverage": comp_c["quadrants_covered"],
                    "spread": comp_c["spread"],
                    "overlap": comp_c["overlap_count"],
                })

            # 정렬: 커버리지 내림차순 → 분산도 내림차순 → 겹침 오름차순
            best_combos.sort(key=lambda x: (-x["coverage"], -x["spread"], x["overlap"]))

            for rank, bc in enumerate(best_combos[:3], 1):
                cov_color = "#00b894" if bc["coverage"] >= 3 else "#fdcb6e"
                st.markdown(f"""<div class="card" style="padding:0.8rem 1.2rem;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-weight:600; color:#eee;">#{rank} {' + '.join(bc['names'])}</span>
                        <span style="color:{cov_color}; font-size:0.9rem;">{bc['coverage']}/4 사분면</span>
                    </div>
                    <div class="detail-text">
                        톤 분산: {bc['spread']:.0%} · 사분면 겹침: {bc['overlap']}개
                    </div>
                </div>""", unsafe_allow_html=True)

            if not best_combos:
                st.caption("조합 가능한 후보가 부족합니다.")


# ══════════════════════════════════════
# 메인
# ══════════════════════════════════════
def main():
    with st.sidebar:
        st.markdown("# 🎤 idol_scout")
        st.caption("AI 아이돌 원석 발굴")
        st.divider()

        mode = st.radio("", ["🔍 새 분석", "📂 지난 분석", "🎵 톤 조합", "🧬 100차원"], label_visibility="collapsed")

        if mode == "🔍 새 분석":
            url = st.text_input("영상 주소", placeholder="YouTube 또는 Instagram URL")
            ct_kr = st.selectbox("영상 유형", ["자동감지", "보컬", "댄스"])
            content_type = {"자동감지": "auto", "보컬": "vocal", "댄스": "dance"}[ct_kr]

            with st.expander("대상 정보 (선택)"):
                name = st.text_input("이름", placeholder="예: 홍길동")
                name_en = st.text_input("영문명", placeholder="")
                group = st.text_input("그룹", placeholder="")
                agency = st.text_input("기획사", placeholder="")

            run_btn = st.button("🚀 분석 시작", type="primary", use_container_width=True)
        elif mode == "🧬 100차원":
            st.markdown("##### 100차원 보컬 벡터 분석")
            st.caption("영상 URL로 57개 음향 지표를 측정합니다")
            v2_url = st.text_input("영상 주소", placeholder="YouTube / Instagram / TikTok URL", key="v2_url")
            v2_name = st.text_input("가수명", placeholder="예: 화사", key="v2_name")
            v2_run = st.button("🧬 100차원 분석", type="primary", use_container_width=True)
            run_btn = False; url = ""
        else:
            run_btn = False; url = ""

    if mode == "🔍 새 분석":
        if run_btn and url:
            try:
                report = run_analysis(url, content_type, name, name_en, group, agency)
                st.toast(f"✅ 분석 완료!")
                render_dashboard(report)
            except Exception as e:
                st.error(f"❌ 오류: {e}")
                import traceback
                st.code(traceback.format_exc())
        elif run_btn:
            st.warning("영상 주소를 입력해주세요.")
        else:
            _render_main_page()
    elif mode == "🧬 100차원":
        if v2_run and v2_url:
            _run_100dim_analysis(v2_url, v2_name)
        elif v2_run:
            st.warning("영상 주소를 입력해주세요.")
        else:
            _render_100dim_intro()
    elif mode == "🎵 톤 조합":
        _render_combination_page()
    else:
        reports = load_reports()
        if not reports:
            st.info("저장된 분석이 없습니다. '새 분석'으로 시작해보세요.")
        else:
            ct_kr_map = {"vocal": "보컬", "dance": "댄스", "auto": "자동"}
            options = []
            for r in reports:
                m = r.get("meta", {})
                n = m.get("name") or "(이름없음)"
                c = ct_kr_map.get(m.get("content_type",""), "?")
                t = m.get("analysis_time","")[:10]
                options.append(f"{n} · {c} · {t}")

            idx = st.selectbox("분석 결과 선택", range(len(options)), format_func=lambda i: options[i])
            if idx is not None:
                render_dashboard(reports[idx])
                st.divider()
                st.download_button("📥 데이터 내려받기",
                    json.dumps(reports[idx], ensure_ascii=False, indent=2, default=str),
                    file_name=reports[idx].get("_filename", "report.json"), mime="application/json")

if __name__ == "__main__":
    main()
