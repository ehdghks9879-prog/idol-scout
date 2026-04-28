"""
idol_scout/models.py — idol_scout_v1/models.py에서 이전
상대 임포트 적용 + 패키지 호환
"""

# 원본 그대로 유지, 변경 사항 없음 (독립 모듈)
# 아래는 원본 코드 전체

from dataclasses import dataclass, field
from typing import Optional, Dict, List
from enum import Enum
import math


NUM_INDICATORS = 100
NUM_INTERPRET_VARS = 11


class Tier(Enum):
    SINGLE_VIDEO = 1
    CROSS_VIDEO = 2
    HUMAN_ONLY = 3


class Category(Enum):
    VOCAL = "vocal"
    DANCE = "dance"
    VISUAL = "visual"
    EXPRESSION = "expression"
    STAGE = "stage"
    GROWTH = "growth"


class Level(Enum):
    LOWEST = 1
    LOW = 2
    MID_LOW = 3
    MID = 4
    MID_HIGH = 5
    HIGH = 6
    HIGHEST = 7

    @property
    def score(self) -> float:
        return (self.value - 1) / 6

    @classmethod
    def from_score(cls, score: float) -> "Level":
        idx = max(1, min(7, round(score * 6 + 1)))
        return cls(idx)


class EnergyDirection(Enum):
    STRONG_RADIATE = -1.0
    RADIATE = -0.5
    WEAK_RADIATE = -0.3
    NEUTRAL = 0.0
    WEAK_ATTRACT = 0.3
    ATTRACT = 0.5
    STRONG_ATTRACT = 1.0


class RhythmPersonality(Enum):
    AHEAD = "ahead"
    ON_BEAT = "on_beat"
    BEHIND = "behind"


class FailureType(Enum):
    NCPS = "NCPS"
    RNCS = "RNCS"
    NONE = "NONE"
    MIXED = "MIXED"


@dataclass
class IndicatorDef:
    id: int
    name: str
    name_en: str
    category: Category
    tier: Tier
    is_uniqueness: bool = False
    is_innate_marker: bool = False
    description: str = ""


@dataclass
class IndicatorScore:
    indicator_id: int
    raw_value: Optional[float] = None
    normalized: Optional[float] = None
    confidence: float = 0.0
    measured: bool = False

    @property
    def effective_score(self) -> float:
        if not self.measured or self.normalized is None:
            return 0.0
        return self.normalized * self.confidence


@dataclass
class Snapshot:
    timestamp: str
    source: str = ""
    scores: Dict[int, IndicatorScore] = field(default_factory=dict)

    def get(self, indicator_id: int) -> IndicatorScore:
        return self.scores.get(indicator_id, IndicatorScore(indicator_id=indicator_id))

    @property
    def measured_count(self) -> int:
        return sum(1 for s in self.scores.values() if s.measured)

    @property
    def uniqueness_scores(self) -> Dict[int, float]:
        ids = {1, 2, 36, 50, 64, 83}
        return {k: v.effective_score for k, v in self.scores.items() if k in ids}


@dataclass
class GrowthSlope:
    indicator_id: int
    slope_per_quarter: float
    r_squared: float = 0.0
    data_points: int = 0
    trend: str = ""


@dataclass
class InterpretVar:
    name: str
    level: Level
    score: float
    source_indicators: List[int] = field(default_factory=list)
    ai_measurable: bool = True
    notes: str = ""


@dataclass
class CDRSubScores:
    cdr_a: Level = Level.MID
    cdr_b: Level = Level.MID
    cdr_c: Level = Level.MID


@dataclass
class InterpretProfile:
    sdi: InterpretVar = None
    edt: InterpretVar = None
    cer: InterpretVar = None
    rmc: InterpretVar = None
    aac: InterpretVar = None
    sca: InterpretVar = None
    cdr: InterpretVar = None
    edi: InterpretVar = None
    nvc: InterpretVar = None
    cci: InterpretVar = None
    cbp: InterpretVar = None
    cdr_sub: CDRSubScores = field(default_factory=CDRSubScores)

    def to_dict(self) -> Dict[str, float]:
        result = {}
        for attr in ['sdi','edt','cer','rmc','aac','sca','cdr','edi','nvc','cci','cbp']:
            var = getattr(self, attr)
            if var:
                result[attr.upper()] = var.score
        return result


@dataclass
class CompositeMetrics:
    system_dependency: float = 0.0
    transition_readiness: float = 0.0
    exposure_conversion: float = 0.0
    resource_convergence: float = 0.0
    innate_ratio: float = 0.0
    growth_trajectory: float = 0.0


@dataclass
class NCPSDiagnosis:
    cond1_single_dimension: bool = False
    cond2_cdr_deficit: bool = False
    cond3_aac_low: bool = False
    cond4_system_concealment: bool = False
    cond5_no_transition_prep: bool = False

    @property
    def conditions_met(self) -> int:
        return sum([self.cond1_single_dimension, self.cond2_cdr_deficit,
                    self.cond3_aac_low, self.cond4_system_concealment,
                    self.cond5_no_transition_prep])

    @property
    def is_ncps(self) -> bool:
        return self.conditions_met >= 4


@dataclass
class RNCSDiagnosis:
    cond1_dispersed_profile: bool = False
    cond2_convergence_engine: bool = False
    cond3_system_supply: bool = False
    cond4_non_musical_attention: bool = False
    cond5_window_missed: bool = False

    @property
    def conditions_met(self) -> int:
        return sum([self.cond1_dispersed_profile, self.cond2_convergence_engine,
                    self.cond3_system_supply, self.cond4_non_musical_attention,
                    self.cond5_window_missed])

    @property
    def is_rncs(self) -> bool:
        return self.conditions_met >= 4


@dataclass
class FailureDiagnosis:
    ncps: NCPSDiagnosis = field(default_factory=NCPSDiagnosis)
    rncs: RNCSDiagnosis = field(default_factory=RNCSDiagnosis)

    @property
    def failure_type(self) -> FailureType:
        if self.ncps.is_ncps and self.rncs.is_rncs:
            return FailureType.MIXED
        elif self.ncps.is_ncps:
            return FailureType.NCPS
        elif self.rncs.is_rncs:
            return FailureType.RNCS
        return FailureType.NONE

    @property
    def risk_level(self) -> str:
        total = self.ncps.conditions_met + self.rncs.conditions_met
        if total >= 7: return "CRITICAL"
        elif total >= 5: return "HIGH"
        elif total >= 3: return "MODERATE"
        return "LOW"


@dataclass
class EnvironmentFactors:
    market_timing: float = 1.0
    system_fit: float = 1.0
    group_composition: float = 1.0
    initial_narrative: float = 1.0
    global_infra: float = 1.0
    system_content_capacity: float = 1.0
    competition_density: float = 1.0
    initial_position_path: float = 1.0

    @property
    def composite(self) -> float:
        vals = [self.market_timing, self.system_fit, self.group_composition,
                self.initial_narrative, self.global_infra, self.system_content_capacity,
                self.competition_density, self.initial_position_path]
        product = 1.0
        for v in vals:
            product *= max(0.2, min(1.5, v))
        return product ** (1 / len(vals))


@dataclass
class IdolProfile:
    name: str
    name_en: str = ""
    birth_year: int = 0
    debut_year: int = 0
    group: str = ""
    agency: str = ""
    snapshots: List[Snapshot] = field(default_factory=list)
    growth_slopes: Dict[int, GrowthSlope] = field(default_factory=dict)
    interpret: InterpretProfile = field(default_factory=InterpretProfile)
    composites: CompositeMetrics = field(default_factory=CompositeMetrics)
    failure_diag: FailureDiagnosis = field(default_factory=FailureDiagnosis)
    environment: EnvironmentFactors = field(default_factory=EnvironmentFactors)
    rhythm_personality: Optional[RhythmPersonality] = None
    energy_direction: Optional[EnergyDirection] = None
    talent_type: str = ""
    analysis_notes: str = ""
    one_sentence: str = ""

    @property
    def latest_snapshot(self) -> Optional[Snapshot]:
        return self.snapshots[-1] if self.snapshots else None

    @property
    def career_years(self) -> int:
        if self.debut_year > 0:
            return 2026 - self.debut_year
        return 0
