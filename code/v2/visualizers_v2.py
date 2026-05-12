"""
visualizers_v2.py — 보컬 MBTI 시각화 모듈 (모델 v2)
=========================================================

목적:
    v2 통합 시스템의 시각화 전담 모듈.
    회사 헌법 정합: 종합 점수 차트 X, 차원별 분리 표시 O.

v1 대비 변경:
    [제거]
    - 댄스 영역 차트 (완전 삭제)
    - 비주얼/표정 차트 (영상 분석 옵션화)
    - 종합 점수 막대그래프 (헌법 위반)

    [신규]
    - 4축 레이더 차트 (Brightness/Weight/Direction/Style)
    - 보컬 4사분면 + 사용자 위치 점
    - 셀럽 매칭 분포 (휘인/화사/솔라/문별 거리)
    - 100차원 outlier 분포도 (양쪽 꼬리 강조)
    - 휘인 7차원 정밀 비교 표
    - 신뢰도 검증 5레이어 게이지

디자인 톤:
    - 다크 테마 (#0a0a0f 배경)
    - 휘인 청록 (#2a9d8f) 단일 강조
    - Plotly 기반 (Streamlit 호환)

작성일: 2026-05-12 (v2 통합 시스템 시각화 핵심)
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ============================================================
# 0. 디자인 토큰 (v2 다크 테마)
# ============================================================

COLOR_BG = "#0a0a0f"          # 캔버스 배경
COLOR_PANEL = "#12121a"       # 패널 배경
COLOR_BORDER = "#1f1f2c"      # 경계선
COLOR_TEXT = "#e5e7eb"        # 본문 텍스트
COLOR_MUTED = "#7a7a8c"       # 보조 텍스트
COLOR_ACCENT = "#2a9d8f"      # 휘인 청록 (단일 강조)
COLOR_HIGH = "#f4a261"        # 상위 outlier
COLOR_LOW = "#9b5de5"         # 하위 outlier (양쪽 꼬리)
COLOR_GRID = "rgba(122,122,140,0.18)"

# 4축 색상 (각 축 고유 색)
AXIS_COLORS = {
    "brightness": "#f4d35e",
    "weight": "#f4a261",
    "direction": "#2a9d8f",
    "style": "#9b5de5",
}

# 마마무 4인 색상 (셀럽 매칭 시각화용)
CELEB_COLORS = {
    "휘인": "#2a9d8f",
    "화사": "#9b5de5",
    "솔라": "#f4d35e",
    "문별": "#f4a261",
}


def _base_layout(title: str, height: int = 360) -> dict:
    """Plotly 공통 레이아웃 (다크 테마)."""
    return dict(
        title=dict(text=title, font=dict(color=COLOR_TEXT, size=15),
                   x=0.02, xanchor="left"),
        paper_bgcolor=COLOR_BG,
        plot_bgcolor=COLOR_BG,
        font=dict(color=COLOR_TEXT, family="Inter, Pretendard, sans-serif"),
        margin=dict(l=40, r=20, t=50, b=40),
        height=height,
        showlegend=True,
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=COLOR_MUTED)),
    )


# ============================================================
# 1. 4축 레이더 차트 (보컬 MBTI 코드 시각화)
# ============================================================

def plot_mbti_radar(scores: Dict[str, float],
                    reference_member: Optional[str] = None,
                    reference_scores: Optional[Dict[str, float]] = None) -> go.Figure:
    """4축(Brightness/Weight/Direction/Style) 레이더 차트.

    Args:
        scores: 사용자의 4축 점수 {brightness, weight, direction, style} (0~1)
        reference_member: 비교할 마마무 멤버 이름 ("휘인" 등) - 옵션
        reference_scores: 비교 대상 점수 - 옵션

    Returns:
        Plotly Figure
    """
    axis_labels = ["Brightness<br>(Bright→Dark)",
                   "Weight<br>(Warm→Dry)",
                   "Direction<br>(Outward→Inward)",
                   "Style<br>(Peak→Subtle)"]
    user_values = [scores.get("brightness", 0.5),
                   scores.get("weight", 0.5),
                   scores.get("direction", 0.5),
                   scores.get("style", 0.5)]
    # 레이더는 폐곡선 — 첫 값을 끝에 한 번 더
    user_values.append(user_values[0])
    labels_loop = axis_labels + [axis_labels[0]]

    fig = go.Figure()

    # 비교 대상 (마마무 멤버)
    if reference_scores is not None:
        ref_values = [reference_scores.get("brightness", 0.5),
                      reference_scores.get("weight", 0.5),
                      reference_scores.get("direction", 0.5),
                      reference_scores.get("style", 0.5)]
        ref_values.append(ref_values[0])
        member_color = CELEB_COLORS.get(reference_member, COLOR_MUTED)
        fig.add_trace(go.Scatterpolar(
            r=ref_values, theta=labels_loop,
            fill="toself",
            fillcolor=f"rgba({int(member_color[1:3],16)},{int(member_color[3:5],16)},{int(member_color[5:7],16)},0.15)",
            line=dict(color=member_color, width=2, dash="dot"),
            name=f"{reference_member} (기준)",
        ))

    # 사용자
    fig.add_trace(go.Scatterpolar(
        r=user_values, theta=labels_loop,
        fill="toself",
        fillcolor=f"rgba(42,157,143,0.30)",
        line=dict(color=COLOR_ACCENT, width=3),
        name="당신의 보컬",
    ))

    layout = _base_layout("4축 보컬 MBTI 프로파일", height=420)
    layout["polar"] = dict(
        bgcolor=COLOR_PANEL,
        radialaxis=dict(visible=True, range=[0, 1],
                        tickfont=dict(color=COLOR_MUTED, size=10),
                        gridcolor=COLOR_GRID,
                        tickvals=[0.25, 0.5, 0.75, 1.0]),
        angularaxis=dict(tickfont=dict(color=COLOR_TEXT, size=11),
                         gridcolor=COLOR_GRID),
    )
    fig.update_layout(**layout)
    return fig


# ============================================================
# 2. 보컬 4사분면 + 사용자 위치
# ============================================================

def plot_vocal_quadrant(user_brightness: float, user_weight: float,
                        show_mamamoo: bool = True) -> go.Figure:
    """톤 4사분면 — Brightness × Weight.

    사분면 정의:
        ┌──────────────────────┐
        │ 청량+따뜻 │ 청량+건조 │  (Bright)
        │  솔라형  │  문별형  │
        ├──────────┼──────────┤
        │ 묵직+따뜻 │ 묵직+건조 │  (Dark)
        │  화사형  │         │
        └──────────────────────┘
           (Warm)      (Dry)

    Args:
        user_brightness: 사용자 brightness (0=Dark, 1=Bright)
        user_weight: 사용자 weight (0=Warm, 1=Dry)
        show_mamamoo: 마마무 4인 기준점 표시 여부

    Returns:
        Plotly Figure
    """
    fig = go.Figure()

    # 4분면 배경 (반투명)
    quadrants = [
        # (x_min, x_max, y_min, y_max, label, color, x_label, y_label)
        (0.0, 0.5, 0.5, 1.0, "청량+따뜻<br>(휘인·솔라)", "rgba(42,157,143,0.10)"),
        (0.5, 1.0, 0.5, 1.0, "청량+건조<br>(문별)", "rgba(244,211,94,0.10)"),
        (0.0, 0.5, 0.0, 0.5, "묵직+따뜻<br>(화사)", "rgba(155,93,229,0.10)"),
        (0.5, 1.0, 0.0, 0.5, "묵직+건조", "rgba(244,162,97,0.10)"),
    ]
    for x0, x1, y0, y1, label, color in quadrants:
        fig.add_shape(type="rect", x0=x0, x1=x1, y0=y0, y1=y1,
                      fillcolor=color, line=dict(width=0), layer="below")
        fig.add_annotation(x=(x0+x1)/2, y=(y0+y1)/2, text=label,
                           showarrow=False,
                           font=dict(color=COLOR_MUTED, size=11),
                           opacity=0.7)

    # 마마무 4인
    if show_mamamoo:
        mamamoo_positions = {
            "솔라": (0.30, 0.75, "BWOP"),    # weight=0.30, brightness=0.75
            "휘인": (0.25, 0.55, "BWIS"),
            "화사": (0.30, 0.25, "DWOP"),
            "문별": (0.75, 0.65, "BRIS"),
        }
        for name, (weight, brightness, code) in mamamoo_positions.items():
            color = CELEB_COLORS[name]
            fig.add_trace(go.Scatter(
                x=[weight], y=[brightness],
                mode="markers+text",
                marker=dict(size=14, color=color,
                            line=dict(color="white", width=1.5)),
                text=f"{name}<br>{code}",
                textposition="top center",
                textfont=dict(color=color, size=10),
                name=f"{name} ({code})",
                hovertemplate=f"{name} ({code})<extra></extra>",
            ))

    # 사용자 위치 (강조)
    fig.add_trace(go.Scatter(
        x=[user_weight], y=[user_brightness],
        mode="markers+text",
        marker=dict(size=22, color=COLOR_ACCENT,
                    symbol="star",
                    line=dict(color="white", width=2)),
        text="당신",
        textposition="bottom center",
        textfont=dict(color=COLOR_ACCENT, size=14),
        name="당신의 위치",
        hovertemplate=f"당신<br>weight={user_weight:.2f}<br>brightness={user_brightness:.2f}<extra></extra>",
    ))

    layout = _base_layout("보컬 4사분면 — 톤 좌표", height=480)
    layout["xaxis"] = dict(
        title="Weight (← Warm | Dry →)",
        range=[0, 1], gridcolor=COLOR_GRID,
        zeroline=False, showgrid=True,
        title_font=dict(color=COLOR_MUTED, size=11),
        tickfont=dict(color=COLOR_MUTED),
    )
    layout["yaxis"] = dict(
        title="Brightness (← Dark | Bright →)",
        range=[0, 1], gridcolor=COLOR_GRID,
        zeroline=False, showgrid=True,
        title_font=dict(color=COLOR_MUTED, size=11),
        tickfont=dict(color=COLOR_MUTED),
    )
    layout["showlegend"] = False
    fig.update_layout(**layout)
    return fig


# ============================================================
# 3. 셀럽 매칭 분포 (휘인·화사·솔라·문별 거리)
# ============================================================

def plot_celeb_match(matches: List[Dict]) -> go.Figure:
    """마마무 멤버와의 거리 시각화.

    Args:
        matches: [{"member": "휘인", "similarity": 0.87, "distance": 0.13}, ...]

    Returns:
        Plotly Figure (수평 막대그래프)
    """
    # similarity 기준 정렬 (높은 순)
    matches_sorted = sorted(matches, key=lambda m: m.get("similarity", 0), reverse=True)
    members = [m["member"] for m in matches_sorted]
    sims = [m.get("similarity", 0) * 100 for m in matches_sorted]
    colors = [CELEB_COLORS.get(m, COLOR_MUTED) for m in members]
    codes = [m.get("code", "") for m in matches_sorted]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=members, x=sims,
        orientation="h",
        marker=dict(color=colors, line=dict(color=COLOR_BG, width=1)),
        text=[f"{s:.0f}%  ·  {c}" for s, c in zip(sims, codes)],
        textposition="auto",
        textfont=dict(color=COLOR_BG, size=12, family="Inter"),
        hovertemplate="%{y}<br>유사도 %{x:.1f}%<extra></extra>",
    ))

    layout = _base_layout("셀럽 매칭 — 마마무 4인 거리", height=300)
    layout["xaxis"] = dict(title="유사도 (%)", range=[0, 100],
                           gridcolor=COLOR_GRID, zeroline=False,
                           title_font=dict(color=COLOR_MUTED, size=11),
                           tickfont=dict(color=COLOR_MUTED))
    layout["yaxis"] = dict(autorange="reversed", showgrid=False,
                           tickfont=dict(color=COLOR_TEXT, size=12))
    layout["showlegend"] = False
    fig.update_layout(**layout)
    return fig


# ============================================================
# 4. 100차원 outlier 분포도 (양쪽 꼬리 강조)
# ============================================================

def plot_outlier_distribution(percentiles: Dict[str, float],
                              top_n: int = 12) -> go.Figure:
    """100차원 차원별 백분위 분포 — 양쪽 꼬리 강조.

    회사 헌법:
        - 양쪽 꼬리 모두 outlier (초우월 + 초이질)
        - 상위 0.05% 임계값 (99.95%) 표시

    Args:
        percentiles: {차원명: 백분위(0~100)}
        top_n: 표시할 상위/하위 차원 개수

    Returns:
        Plotly Figure
    """
    # 극단값 정렬
    sorted_items = sorted(percentiles.items(), key=lambda kv: kv[1])
    low_items = sorted_items[:top_n]
    high_items = sorted_items[-top_n:][::-1]  # 높은 순

    names = [k for k, _ in low_items] + [k for k, _ in high_items]
    values = [v for _, v in low_items] + [v for _, v in high_items]
    colors = [COLOR_LOW] * len(low_items) + [COLOR_HIGH] * len(high_items)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=names, y=values,
        marker=dict(color=colors, line=dict(color=COLOR_BG, width=1)),
        hovertemplate="%{x}<br>백분위 %{y:.2f}%<extra></extra>",
        showlegend=False,
    ))

    # 0.05% / 99.95% 라인 (회사 헌법 임계값)
    fig.add_hline(y=99.95, line_dash="dash", line_color=COLOR_HIGH,
                  annotation_text="상위 0.05% 임계값",
                  annotation_position="top right",
                  annotation_font=dict(color=COLOR_HIGH, size=10))
    fig.add_hline(y=0.05, line_dash="dash", line_color=COLOR_LOW,
                  annotation_text="하위 0.05% 임계값",
                  annotation_position="bottom right",
                  annotation_font=dict(color=COLOR_LOW, size=10))

    layout = _base_layout(f"100차원 outlier — 양쪽 꼬리 상위 {top_n}개씩", height=440)
    layout["xaxis"] = dict(tickangle=-45, tickfont=dict(color=COLOR_MUTED, size=9),
                           gridcolor=COLOR_GRID, showgrid=False)
    layout["yaxis"] = dict(title="백분위 (%)", range=[0, 100],
                           gridcolor=COLOR_GRID, zeroline=False,
                           title_font=dict(color=COLOR_MUTED, size=11),
                           tickfont=dict(color=COLOR_MUTED))
    fig.update_layout(**layout)
    return fig


# ============================================================
# 5. 휘인 7차원 정밀 비교
# ============================================================

WHEEIN_7_DIMENSIONS = [
    "가벼운 성대",
    "비강 공명",
    "허스키-청량 텍스처",
    "다이내믹 점진성",
    "흐림 발음 미학",
    "절제된 감정",
    "R&B 친화도",
]


def plot_wheein_7d_comparison(user_scores: Dict[str, float],
                              wheein_scores: Optional[Dict[str, float]] = None) -> go.Figure:
    """휘인 7차원 정밀 비교 레이더.

    Args:
        user_scores: 사용자의 7차원 점수 {차원명: 0~1}
        wheein_scores: 휘인 기준 점수 (None이면 표준 1.0)

    Returns:
        Plotly Figure
    """
    if wheein_scores is None:
        wheein_scores = {dim: 1.0 for dim in WHEEIN_7_DIMENSIONS}

    user_vals = [user_scores.get(dim, 0.5) for dim in WHEEIN_7_DIMENSIONS]
    wheein_vals = [wheein_scores.get(dim, 1.0) for dim in WHEEIN_7_DIMENSIONS]
    user_vals.append(user_vals[0])
    wheein_vals.append(wheein_vals[0])
    labels_loop = WHEEIN_7_DIMENSIONS + [WHEEIN_7_DIMENSIONS[0]]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=wheein_vals, theta=labels_loop,
        fill="toself",
        fillcolor="rgba(42,157,143,0.10)",
        line=dict(color=COLOR_ACCENT, width=2, dash="dot"),
        name="휘인 (기준 1.0)",
    ))
    fig.add_trace(go.Scatterpolar(
        r=user_vals, theta=labels_loop,
        fill="toself",
        fillcolor="rgba(244,162,97,0.30)",
        line=dict(color=COLOR_HIGH, width=3),
        name="당신",
    ))

    layout = _base_layout("휘인 7차원 정밀 비교", height=460)
    layout["polar"] = dict(
        bgcolor=COLOR_PANEL,
        radialaxis=dict(visible=True, range=[0, 1.2],
                        tickfont=dict(color=COLOR_MUTED, size=10),
                        gridcolor=COLOR_GRID),
        angularaxis=dict(tickfont=dict(color=COLOR_TEXT, size=11),
                         gridcolor=COLOR_GRID),
    )
    fig.update_layout(**layout)
    return fig


# ============================================================
# 6. 신뢰도 검증 5레이어 게이지
# ============================================================

RELIABILITY_LAYERS = [
    ("CREPE 정밀 F0", "F0 측정 정확도"),
    ("Parselmouth 발성품질", "Jitter/Shimmer/HNR"),
    ("임상 정상 범위", "병리 가능성 체크"),
    ("저신뢰 프레임 메타", "프레임별 confidence"),
    ("교차검증 (pyin)", "F0 알고리즘 일치도"),
]


def plot_reliability_gauges(reliability_scores: Dict[str, float]) -> go.Figure:
    """5레이어 신뢰도 게이지 (가로 막대).

    Args:
        reliability_scores: {레이어명: 0~1}

    Returns:
        Plotly Figure
    """
    names = [layer[0] for layer in RELIABILITY_LAYERS]
    descriptions = [layer[1] for layer in RELIABILITY_LAYERS]
    scores = [reliability_scores.get(n, 0.85) * 100 for n in names]

    # 점수에 따라 색상 분기
    def score_color(s):
        if s >= 90:
            return COLOR_ACCENT
        elif s >= 70:
            return COLOR_HIGH
        else:
            return COLOR_LOW

    colors = [score_color(s) for s in scores]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=names, x=scores,
        orientation="h",
        marker=dict(color=colors, line=dict(color=COLOR_BG, width=1)),
        text=[f"{s:.0f}%  ·  {d}" for s, d in zip(scores, descriptions)],
        textposition="auto",
        textfont=dict(color=COLOR_BG, size=11),
        hovertemplate="%{y}<br>신뢰도 %{x:.1f}%<extra></extra>",
    ))

    # 90% 기준선 (양호 임계값)
    fig.add_vline(x=90, line_dash="dash", line_color=COLOR_ACCENT,
                  annotation_text="양호 임계값 (90%)",
                  annotation_position="top",
                  annotation_font=dict(color=COLOR_ACCENT, size=10))

    layout = _base_layout("신뢰도 검증 5레이어", height=300)
    layout["xaxis"] = dict(range=[0, 100], gridcolor=COLOR_GRID, zeroline=False,
                           title="신뢰도 (%)", title_font=dict(color=COLOR_MUTED, size=11),
                           tickfont=dict(color=COLOR_MUTED))
    layout["yaxis"] = dict(autorange="reversed", showgrid=False,
                           tickfont=dict(color=COLOR_TEXT, size=11))
    layout["showlegend"] = False
    fig.update_layout(**layout)
    return fig


# ============================================================
# 7. 100차원 카테고리 분포 (보컬 50% 강조)
# ============================================================

V2_CATEGORIES = {
    "보컬": (50, COLOR_ACCENT),
    "비주얼 (영상)": (15, "#5b6f8a"),
    "표정 (영상)": (20, "#7a6f9c"),
    "무대 장악력": (10, "#9c6f7a"),
    "성장 잠재력": (5, "#6f9c8a"),
}


def plot_category_distribution() -> go.Figure:
    """v2 100차원 카테고리 분포 (보컬 50%)."""
    names = list(V2_CATEGORIES.keys())
    values = [v[0] for v in V2_CATEGORIES.values()]
    colors = [v[1] for v in V2_CATEGORIES.values()]

    fig = go.Figure()
    fig.add_trace(go.Pie(
        labels=names, values=values,
        marker=dict(colors=colors, line=dict(color=COLOR_BG, width=2)),
        textinfo="label+percent",
        textfont=dict(color=COLOR_TEXT, size=12),
        hole=0.4,
        hovertemplate="%{label}<br>%{value}개 차원<extra></extra>",
    ))

    fig.add_annotation(
        text="v2<br>100차원",
        x=0.5, y=0.5,
        font=dict(color=COLOR_ACCENT, size=18, family="Inter"),
        showarrow=False,
    )

    layout = _base_layout("v2 100차원 카테고리 분포 (보컬 50%)", height=380)
    layout["showlegend"] = True
    layout["legend"] = dict(bgcolor="rgba(0,0,0,0)",
                            font=dict(color=COLOR_TEXT),
                            orientation="v", x=1.02, y=0.5)
    fig.update_layout(**layout)
    return fig


# ============================================================
# 8. MBTI 코드 분포 16타입 그리드 (현재 위치 강조)
# ============================================================

def plot_16type_grid(user_code: str) -> go.Figure:
    """16타입 그리드 시각화 — 사용자 타입 강조.

    Args:
        user_code: 사용자의 4글자 코드 (예: "BWIS")

    Returns:
        Plotly Figure
    """
    # 4x4 그리드 — 행: BW/BR/DW/DR (밝기·무게), 열: OP/OS/IP/IS (방향·스타일)
    rows = ["BW", "BR", "DW", "DR"]
    cols = ["OP", "OS", "IP", "IS"]
    code_grid = [[r + c for c in cols] for r in rows]

    # 마마무 4인 기준
    member_by_code = {"BWOP": "솔라", "BWIS": "휘인", "DWOP": "화사", "BRIS": "문별"}

    fig = go.Figure()

    for i, row in enumerate(rows):
        for j, col in enumerate(cols):
            code = code_grid[i][j]
            is_user = (code == user_code)
            is_celeb = code in member_by_code

            if is_user:
                fill = COLOR_ACCENT
                border = "white"
                opacity = 1.0
            elif is_celeb:
                fill = CELEB_COLORS.get(member_by_code[code], COLOR_MUTED)
                border = "white"
                opacity = 0.85
            else:
                fill = COLOR_PANEL
                border = COLOR_BORDER
                opacity = 0.7

            fig.add_shape(type="rect",
                          x0=j, x1=j+1, y0=3-i, y1=4-i,
                          fillcolor=fill, opacity=opacity,
                          line=dict(color=border, width=2 if (is_user or is_celeb) else 1))

            label = code
            if is_celeb:
                label += f"<br>({member_by_code[code]})"
            if is_user:
                label += "<br>★ 당신"

            text_color = "white" if (is_user or is_celeb) else COLOR_MUTED
            fig.add_annotation(
                x=j+0.5, y=3-i+0.5, text=label,
                showarrow=False,
                font=dict(color=text_color, size=10, family="Inter"),
            )

    layout = _base_layout(f"16타입 그리드 — 당신은 {user_code}", height=440)
    layout["xaxis"] = dict(range=[0, 4], showticklabels=False, showgrid=False,
                           zeroline=False)
    layout["yaxis"] = dict(range=[0, 4], showticklabels=False, showgrid=False,
                           zeroline=False, scaleanchor="x", scaleratio=1)
    layout["showlegend"] = False
    fig.update_layout(**layout)
    return fig


# ============================================================
# 9. 통합 — 한 번에 모든 v2 차트 생성
# ============================================================

def generate_full_v2_charts(analysis_result: Dict) -> Dict[str, go.Figure]:
    """v2 분석 결과 dict에서 모든 차트를 생성.

    Args:
        analysis_result: vocal_mbti.analyze_vocal_mbti() 결과 + 100차원 측정치

    Returns:
        {chart_name: Figure} 딕셔너리
    """
    charts = {}

    scores = analysis_result.get("axis_scores", {})
    code = analysis_result.get("code", "BWIS")
    matches = analysis_result.get("celeb_matches", [])
    percentiles = analysis_result.get("percentiles_100d", {})
    wheein_7d = analysis_result.get("wheein_7d_scores", {})
    reliability = analysis_result.get("reliability_scores", {})

    # 1. MBTI 4축 레이더
    ref_member = matches[0]["member"] if matches else None
    ref_scores = None
    if ref_member and ref_member in ("솔라", "휘인", "화사", "문별"):
        from vocal_mbti import MAMAMOO_REFERENCE
        ref = MAMAMOO_REFERENCE.get(ref_member, {})
        ref_scores = {k: ref.get(k, 0.5) for k in ("brightness", "weight", "direction", "style")}
    charts["mbti_radar"] = plot_mbti_radar(scores, ref_member, ref_scores)

    # 2. 4사분면
    charts["quadrant"] = plot_vocal_quadrant(
        scores.get("brightness", 0.5),
        scores.get("weight", 0.5),
    )

    # 3. 셀럽 매칭
    if matches:
        charts["celeb_match"] = plot_celeb_match(matches)

    # 4. 100차원 outlier
    if percentiles:
        charts["outliers"] = plot_outlier_distribution(percentiles)

    # 5. 휘인 7차원
    if wheein_7d:
        charts["wheein_7d"] = plot_wheein_7d_comparison(wheein_7d)

    # 6. 신뢰도 5레이어
    if reliability:
        charts["reliability"] = plot_reliability_gauges(reliability)

    # 7. 카테고리 분포 (정적)
    charts["categories"] = plot_category_distribution()

    # 8. 16타입 그리드
    charts["type_grid"] = plot_16type_grid(code)

    return charts


# ============================================================
# 10. 헬퍼 — 더미 데이터 (테스트용)
# ============================================================

def demo_data() -> Dict:
    """테스트용 더미 분석 결과 (휘인형)."""
    return {
        "code": "BWIS",
        "code_with_rank": "BWIS-72",
        "axis_scores": {
            "brightness": 0.58,
            "weight": 0.28,
            "direction": 0.32,
            "style": 0.22,
            "confidence": 0.94,
        },
        "celeb_matches": [
            {"member": "휘인", "similarity": 0.87, "distance": 0.13, "code": "BWIS"},
            {"member": "솔라", "similarity": 0.42, "distance": 0.58, "code": "BWOP"},
            {"member": "화사", "similarity": 0.18, "distance": 0.82, "code": "DWOP"},
            {"member": "문별", "similarity": 0.31, "distance": 0.69, "code": "BRIS"},
        ],
        "percentiles_100d": {
            "성대 두께": 4.6,
            "비강 공명비": 99.7,
            "다이내믹 점진성": 1.4,
            "F0 안정성": 88.2,
            "Jitter": 12.3,
            "Shimmer": 18.5,
            "HNR": 91.4,
            "음역대": 64.0,
            "발음 명료도": 8.1,
            "감정 강도": 22.5,
            "비브라토 주기": 76.3,
            "후렴 폭발력": 14.2,
            "메탈릭 광택": 38.5,
            "허스키-청량 텍스처": 96.8,
            "흐림 발음 미학": 98.2,
            "R&B 친화도": 99.1,
            "절제된 감정": 97.5,
            "흉성 두께": 8.4,
            "두성 사용률": 82.6,
            "고음 안정성": 71.3,
            "저음 깊이": 31.8,
            "리듬 정확도": 79.2,
            "프레이즈 마디 처리": 65.4,
            "공기감": 88.9,
        },
        "wheein_7d_scores": {
            "가벼운 성대": 0.92,
            "비강 공명": 0.88,
            "허스키-청량 텍스처": 0.95,
            "다이내믹 점진성": 0.91,
            "흐림 발음 미학": 0.86,
            "절제된 감정": 0.83,
            "R&B 친화도": 0.94,
        },
        "reliability_scores": {
            "CREPE 정밀 F0": 0.96,
            "Parselmouth 발성품질": 0.94,
            "임상 정상 범위": 0.91,
            "저신뢰 프레임 메타": 0.88,
            "교차검증 (pyin)": 0.92,
        },
    }


if __name__ == "__main__":
    # 자체 테스트 — 8개 차트 모두 생성
    print("[v2 visualizers] 더미 데이터로 차트 생성 테스트")
    data = demo_data()
    charts = generate_full_v2_charts(data)
    print(f"생성된 차트 수: {len(charts)}")
    for name, fig in charts.items():
        print(f"  - {name}: {type(fig).__name__}")
    print("[v2 visualizers] 정상 작동")
