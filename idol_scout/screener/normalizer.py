"""
normalizer.py — 백분위 정규화 + 극단값 식별
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
100차원 보컬 벡터의 각 지표를 기준DB 대비 백분위로 변환하고,
OR 논리로 극단값(천재 신호)을 식별합니다.

★ 회사 헌법: 종합점수/합산/가중평균 영구 금지
  - 축 간/지표 간 합산 없음
  - 각 지표 독립 백분위 → 독립 극단값 판정
  - 통과 조건: 어느 한 차원이라도 극단값이면 통과 (OR 논리)
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass, field

from .indicators_100 import (
    INDICATOR_REGISTRY,
    IndicatorMeasurement,
    VocalVector100,
    get_tier1_indicators,
)
from .config import OUTLIER_THRESHOLD, OUTLIER_LOW_THRESHOLD


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 기준 DB 구조
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class IndicatorStats:
    """1개 지표의 기준 통계"""
    indicator_id: str
    count: int = 0            # 측정된 샘플 수
    mean: float = 0.0
    std: float = 0.0
    min_val: float = 0.0
    max_val: float = 0.0
    percentiles: Dict[int, float] = field(default_factory=dict)  # {5: 0.1, 25: 0.3, ...}

    def to_dict(self) -> dict:
        return {
            "id": self.indicator_id,
            "count": self.count,
            "mean": self.mean,
            "std": self.std,
            "min": self.min_val,
            "max": self.max_val,
            "percentiles": self.percentiles,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "IndicatorStats":
        return cls(
            indicator_id=d["id"],
            count=d.get("count", 0),
            mean=d.get("mean", 0.0),
            std=d.get("std", 0.0),
            min_val=d.get("min", 0.0),
            max_val=d.get("max", 0.0),
            percentiles=d.get("percentiles", {}),
        )


@dataclass
class ReferenceDB:
    """기준 데이터베이스 — 지표별 통계"""
    stats: Dict[str, IndicatorStats] = field(default_factory=dict)
    total_artists: int = 0
    version: str = "0.1.0-bootstrap"
    description: str = ""

    def save(self, path: Path):
        data = {
            "version": self.version,
            "total_artists": self.total_artists,
            "description": self.description,
            "stats": {k: v.to_dict() for k, v in self.stats.items()},
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: Path) -> "ReferenceDB":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        db = cls(
            version=data.get("version", "unknown"),
            total_artists=data.get("total_artists", 0),
            description=data.get("description", ""),
        )
        for k, v in data.get("stats", {}).items():
            db.stats[k] = IndicatorStats.from_dict(v)
        return db


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 부트스트랩 기준 DB (Phase 1 — 기준 데이터 없을 때)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def create_bootstrap_db() -> ReferenceDB:
    """
    기준 DB 없이도 동작하는 부트스트랩 통계.

    각 지표에 대해 합리적인 범위를 설정하여
    대략적인 백분위 추정이 가능하도록 합니다.

    ★ Phase 3에서 500명 기준DB로 교체 예정
    """
    db = ReferenceDB(
        version="0.1.0-bootstrap",
        total_artists=0,
        description="부트스트랩 DB — 이론적 범위 기반 추정. 실측 데이터 아님."
    )

    # Pitch 관련 — cent 편차 (낮을수록 좋음)
    pitch_ids = [
        "A-1-1-08", "A-1-1-07", "A-1-2-02", "A-1-2-03",
        "A-1-2-09", "A-1-2-10", "A-1-2-14",
        "A-1-3-05", "A-1-3-09",
    ]
    for iid in pitch_ids:
        db.stats[iid] = IndicatorStats(
            indicator_id=iid, count=0,
            mean=25.0, std=15.0, min_val=2.0, max_val=80.0,
            percentiles={5: 5.0, 25: 15.0, 50: 25.0, 75: 35.0, 95: 60.0}
        )

    # 안정영역 폭 — semitones
    db.stats["A-1-1-10"] = IndicatorStats(
        indicator_id="A-1-1-10", count=0,
        mean=18.0, std=6.0, min_val=5.0, max_val=36.0,
        percentiles={5: 8.0, 25: 14.0, 50: 18.0, 75: 22.0, 95: 30.0}
    )

    # 비율형 (0~1)
    ratio_ids = [
        "A-1-1-15", "A-1-5-05", "A-1-5-07",
        "A-1-4-02", "A-1-4-05", "A-1-4-07",
        "A-5-4-10", "A-5-4-13",
    ]
    for iid in ratio_ids:
        db.stats[iid] = IndicatorStats(
            indicator_id=iid, count=0,
            mean=0.3, std=0.2, min_val=0.0, max_val=1.0,
            percentiles={5: 0.02, 25: 0.15, 50: 0.3, 75: 0.5, 95: 0.8}
        )

    # 음정정확도 cent (낮을수록 좋음 → 역정규화 필요)
    db.stats["A-1-5-06"] = IndicatorStats(
        indicator_id="A-1-5-06", count=0,
        mean=20.0, std=10.0, min_val=2.0, max_val=50.0,
        percentiles={5: 4.0, 25: 12.0, 50: 20.0, 75: 28.0, 95: 40.0}
    )

    # Dynamic range — dB
    for iid in ["A-5-4-07", "A-5-4-02"]:
        db.stats[iid] = IndicatorStats(
            indicator_id=iid, count=0,
            mean=24.0, std=8.0, min_val=6.0, max_val=48.0,
            percentiles={5: 10.0, 25: 18.0, 50: 24.0, 75: 32.0, 95: 42.0}
        )

    # Energy 관련 — 일반적 분포
    energy_generic_ids = [
        "A-5-4-05", "A-5-4-07b", "A-5-4-08", "A-5-4-09",
        "A-5-4-11", "A-5-4-12", "A-5-4-14", "A-5-4-15",
        "A-5-4-16", "A-5-4-17", "A-5-4-18",
    ]
    for iid in energy_generic_ids:
        db.stats[iid] = IndicatorStats(
            indicator_id=iid, count=0,
            mean=0.5, std=0.25, min_val=0.0, max_val=2.0,
            percentiles={5: 0.05, 25: 0.3, 50: 0.5, 75: 0.7, 95: 1.2}
        )

    # Spectrum — entropy, similarity 등
    spectrum_ids = [
        "B-1-1-12", "B-1-1-15", "B-1-1-16",
        "B-1-2-06", "B-1-2-07", "B-1-2-08", "B-1-2-09",
        "B-1-2-11", "B-1-2-12",
        "B-1-4-04", "B-1-4-06", "B-1-4-10",
    ]
    for iid in spectrum_ids:
        db.stats[iid] = IndicatorStats(
            indicator_id=iid, count=0,
            mean=0.5, std=0.2, min_val=0.0, max_val=1.5,
            percentiles={5: 0.1, 25: 0.35, 50: 0.5, 75: 0.65, 95: 0.9}
        )

    # Vibrato
    vibrato_ids = [
        "A-5-1-07", "A-5-1-03", "A-5-1-04", "A-5-1-05",
        "A-5-1-06", "A-5-1-08", "A-5-1-09", "A-5-1-10",
    ]
    for iid in vibrato_ids:
        db.stats[iid] = IndicatorStats(
            indicator_id=iid, count=0,
            mean=0.4, std=0.2, min_val=0.0, max_val=1.0,
            percentiles={5: 0.05, 25: 0.25, 50: 0.4, 75: 0.6, 95: 0.85}
        )

    # Voice Range
    db.stats["A-2-5-01"] = IndicatorStats(
        indicator_id="A-2-5-01", count=0,
        mean=800.0, std=200.0, min_val=300.0, max_val=1500.0,
        percentiles={5: 450.0, 25: 650.0, 50: 800.0, 75: 950.0, 95: 1200.0}
    )
    db.stats["A-2-5-03"] = IndicatorStats(
        indicator_id="A-2-5-03", count=0,
        mean=24.0, std=6.0, min_val=10.0, max_val=48.0,
        percentiles={5: 14.0, 25: 20.0, 50: 24.0, 75: 28.0, 95: 36.0}
    )
    for iid in ["A-2-5-06", "A-2-5-07", "A-2-5-08", "A-2-5-10"]:
        db.stats[iid] = IndicatorStats(
            indicator_id=iid, count=0,
            mean=0.4, std=0.25, min_val=0.0, max_val=1.0,
            percentiles={5: 0.02, 25: 0.2, 50: 0.4, 75: 0.6, 95: 0.9}
        )

    # Formant
    for iid in ["A-2-4-01", "A-2-4-02", "A-2-4-07"]:
        db.stats[iid] = IndicatorStats(
            indicator_id=iid, count=0,
            mean=0.5, std=0.2, min_val=0.0, max_val=1.0,
            percentiles={5: 0.1, 25: 0.3, 50: 0.5, 75: 0.7, 95: 0.9}
        )

    return db


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 정규화기
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 낮을수록 좋은 지표 목록 (역정규화 대상)
_LOWER_IS_BETTER = {
    # 음정편차 (cent) — 낮을수록 정확
    "A-1-1-08", "A-1-1-07", "A-1-2-02", "A-1-2-03",
    "A-1-2-09", "A-1-2-10", "A-1-2-14",
    "A-1-3-05", "A-1-3-09", "A-1-5-06",
    "A-5-1-03",  # 멜리스마 음정편차
    # RMS 분산 — 낮을수록 안정
    "A-5-4-11",
}


class VocalNormalizer:
    """
    백분위 정규화기 — 각 지표를 기준DB 대비 0~100 백분위로 변환

    ★ 종합점수 없음 — 지표 간 합산/가중평균 절대 금지
    """

    def __init__(self, reference_db: Optional[ReferenceDB] = None):
        if reference_db is None:
            self.db = create_bootstrap_db()
            self._is_bootstrap = True
        else:
            self.db = reference_db
            self._is_bootstrap = reference_db.total_artists == 0

    @property
    def is_bootstrap(self) -> bool:
        return self._is_bootstrap

    def normalize(self, vector: VocalVector100) -> VocalVector100:
        """
        각 지표의 raw_value를 백분위로 변환.

        ★ 지표 간 합산 없음 — 각 지표 독립 처리
        """
        for iid, measurement in vector.measurements.items():
            if not measurement.measured:
                continue

            stats = self.db.stats.get(iid)
            if stats is None or stats.count == 0 and not self._is_bootstrap:
                # 기준 통계 없음 → 백분위 미산출
                measurement.percentile = None
                continue

            raw = measurement.raw_value
            is_lower_better = iid in _LOWER_IS_BETTER

            if stats.percentiles:
                # 보간법으로 백분위 추정
                pct = self._interpolate_percentile(raw, stats.percentiles, is_lower_better)
            else:
                # z-score 기반 추정
                pct = self._zscore_percentile(raw, stats.mean, stats.std, is_lower_better)

            measurement.percentile = max(0.0, min(100.0, pct))

        return vector

    def detect_outliers(self, vector: VocalVector100) -> VocalVector100:
        """
        극단값 식별 (OR 논리).

        ★ 종합점수 없음 — 각 지표 독립 판정
        ★ 양쪽 꼬리 모두 검사:
          - 오른쪽 꼬리 (상위): percentile >= OUTLIER_THRESHOLD * 100
          - 왼쪽 꼬리 (초이질): percentile <= OUTLIER_LOW_THRESHOLD * 100
        """
        axis_outliers = {"A": [], "B": [], "C": []}
        high_threshold = OUTLIER_THRESHOLD * 100    # 70
        low_threshold = OUTLIER_LOW_THRESHOLD * 100  # 15

        for iid, measurement in vector.measurements.items():
            if not measurement.measured or measurement.percentile is None:
                continue

            pct = measurement.percentile
            is_outlier = False

            # 오른쪽 꼬리 (상위 극단값)
            if pct >= high_threshold:
                is_outlier = True
                measurement.genius_level = self._classify_genius_level(pct)

            # 왼쪽 꼬리 (초이질 — 극도로 독특)
            if pct <= low_threshold:
                is_outlier = True
                measurement.genius_level = "초이질"

            if is_outlier and measurement.axis in axis_outliers:
                axis_outliers[measurement.axis].append(iid)

        vector.axis_a_outliers = axis_outliers.get("A", [])
        vector.axis_b_outliers = axis_outliers.get("B", [])
        vector.axis_c_outliers = axis_outliers.get("C", [])

        # OR 판정: 어느 한 축이라도 극단값이 있으면 통과
        vector.has_any_outlier = bool(
            vector.axis_a_outliers or
            vector.axis_b_outliers or
            vector.axis_c_outliers
        )

        # 요약 문자열
        parts = []
        if vector.axis_a_outliers:
            parts.append(f"A축(기술적안정성): {len(vector.axis_a_outliers)}개")
        if vector.axis_b_outliers:
            parts.append(f"B축(음색독창성): {len(vector.axis_b_outliers)}개")
        if vector.axis_c_outliers:
            parts.append(f"C축(정서전달력): {len(vector.axis_c_outliers)}개")

        if parts:
            vector.outlier_summary = "극단값 발견 — " + ", ".join(parts)
        else:
            vector.outlier_summary = "극단값 미발견"

        return vector

    def _interpolate_percentile(self, value: float,
                                 percentiles: Dict[int, float],
                                 is_lower_better: bool) -> float:
        """백분위 보간"""
        if is_lower_better:
            # 역전: 값이 낮을수록 높은 백분위
            # percentiles의 값도 역전해서 해석
            sorted_pcts = sorted(percentiles.items())
            for i in range(len(sorted_pcts) - 1):
                p1, v1 = sorted_pcts[i]
                p2, v2 = sorted_pcts[i + 1]
                if v2 >= value >= v1:
                    # 값이 낮을수록 높은 백분위
                    frac = (v2 - value) / (v2 - v1 + 1e-10)
                    return p1 + frac * (p2 - p1)
                elif value >= v2:
                    # 값이 매우 높음 = 낮은 백분위
                    return float(sorted_pcts[0][0])
            # 값이 매우 낮음 = 높은 백분위
            return 100.0 - float(sorted_pcts[0][0])
        else:
            # 정방향: 값이 클수록 높은 백분위
            sorted_pcts = sorted(percentiles.items())
            for i in range(len(sorted_pcts) - 1):
                p1, v1 = sorted_pcts[i]
                p2, v2 = sorted_pcts[i + 1]
                if v1 <= value <= v2:
                    frac = (value - v1) / (v2 - v1 + 1e-10)
                    return p1 + frac * (p2 - p1)
            # 범위 밖
            if value <= sorted_pcts[0][1]:
                return float(sorted_pcts[0][0]) * (value / (sorted_pcts[0][1] + 1e-10))
            else:
                return min(99.9, float(sorted_pcts[-1][0]) +
                          (value - sorted_pcts[-1][1]) / (sorted_pcts[-1][1] + 1e-10) * 5)

    def _zscore_percentile(self, value: float, mean: float,
                           std: float, is_lower_better: bool) -> float:
        """z-score 기반 백분위 추정"""
        if std <= 0:
            return 50.0
        z = (value - mean) / std
        if is_lower_better:
            z = -z  # 역전
        # 간이 CDF: 시그모이드 근사
        pct = 100.0 / (1.0 + np.exp(-0.7 * z))
        return float(pct)

    def _classify_genius_level(self, percentile: float) -> str:
        """천재 신호 수준 분류"""
        if percentile >= 99.9:
            return "매우강함(상위0.1%)"
        elif percentile >= 99.0:
            return "매우강함(상위1%)"
        elif percentile >= 95.0:
            return "강함(상위5%)"
        elif percentile >= 90.0:
            return "중간(상위10%)"
        else:
            return "관심"

    def update_db(self, vectors: List[VocalVector100]):
        """
        측정 결과들로 기준 DB 업데이트.

        Phase 3에서 500명 데이터를 축적할 때 사용.
        """
        # 지표별 raw_value 수집
        all_values: Dict[str, List[float]] = {}
        for vec in vectors:
            for iid, m in vec.measurements.items():
                if m.measured:
                    if iid not in all_values:
                        all_values[iid] = []
                    all_values[iid].append(m.raw_value)

        for iid, values in all_values.items():
            arr = np.array(values)
            self.db.stats[iid] = IndicatorStats(
                indicator_id=iid,
                count=len(arr),
                mean=float(np.mean(arr)),
                std=float(np.std(arr)),
                min_val=float(np.min(arr)),
                max_val=float(np.max(arr)),
                percentiles={
                    int(p): float(np.percentile(arr, p))
                    for p in [1, 5, 10, 25, 50, 75, 90, 95, 99]
                }
            )

        self.db.total_artists += len(vectors)
        self._is_bootstrap = False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 오케스트레이터 v2 (5단계 파이프라인)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def screen_vocal_100(audio_path: Path,
                     content_type: str = "vocal_video",
                     reference_db_path: Optional[Path] = None) -> VocalVector100:
    """
    100차원 보컬 스크리닝 — 5단계 파이프라인

    1단계: 전처리 (~2초)       — 오디오 로드, 포맷 변환
    2단계: 기초특성추출 (~10초) — 공유 특징 (PrecomputedFeatures)
    3단계: 항목별측정 (~15초)   — 6개 알고리즘 × 57+ 지표
    4단계: 백분위정규화 (~3초)  — 기준DB 대비 백분위 변환
    5단계: 이상치식별 (~2초)    — OR 논리 극단값 판정

    ★ 종합점수 없음 — 각 지표 독립 판정

    Parameters
    ----------
    audio_path : Path
        오디오 파일 경로
    content_type : str
        입력 유형
    reference_db_path : Optional[Path]
        기준 DB 파일 경로 (없으면 부트스트랩)

    Returns
    -------
    VocalVector100
        정규화 + 극단값 식별 완료된 100차원 벡터
    """
    from .audio_v2 import measure_tier1

    # 1~3단계: 측정
    vector = measure_tier1(audio_path, content_type)

    # 기준 DB 로드
    ref_db = None
    if reference_db_path and reference_db_path.exists():
        try:
            ref_db = ReferenceDB.load(reference_db_path)
        except Exception:
            ref_db = None

    # 4단계: 백분위 정규화
    normalizer = VocalNormalizer(ref_db)
    vector = normalizer.normalize(vector)

    # 5단계: 극단값 식별 (OR 논리)
    vector = normalizer.detect_outliers(vector)

    return vector
