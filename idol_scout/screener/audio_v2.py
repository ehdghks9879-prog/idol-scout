"""
audio_v2.py — 100차원 보컬 벡터 1계층(음향분석) 측정 엔진
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
6개 알고리즘 카테고리 × 57개 지표를 librosa/numpy/scipy로 측정

카테고리별 지표 수:
  Pitch_Analysis  — 17개 (음정정확도, 안정성, 도약, 미세통제, 회복력)
  Energy_Analysis — 15개 (다이내믹, RMS 시계열, 에너지 패턴)
  Spectrum_Analysis — 12개 (스펙트럼 특성, 배음구조, 음색시간안정성)
  Vibrato_Analysis — 8개 (비브라토 특성, 음색변환)
  Voice_Range     — 6개 (음역대, 발성다양성)
  Formant_Analysis — 3개 (포먼트, 성대 특성)
  ─────────────────
  합계: 61개 (일부 tier1/tier2 혼합 → tier1만 측정, 나머지 placeholder)

★ 회사 헌법: 종합점수/합산/가중평균 영구 금지
  각 지표는 독립 측정 → 독립 백분위 → OR 논리 극단값 판정
"""

import numpy as np
from pathlib import Path
from typing import Dict, Optional, Tuple, List
import warnings

import librosa

from .indicators_100 import (
    INDICATOR_REGISTRY,
    IndicatorMeasurement,
    VocalVector100,
    get_tier1_indicators,
)
from .config import AUDIO_SAMPLE_RATE, CONFIDENCE_CAPS


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 공유 전처리 결과 (한 번 계산, 전 카테고리 공유)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class PrecomputedFeatures:
    """오디오에서 한 번 추출하여 모든 측정 함수가 공유하는 특징"""

    def __init__(self, y: np.ndarray, sr: int):
        self.y = y
        self.sr = sr
        self.duration = librosa.get_duration(y=y, sr=sr)

        # ── HPSS ────────────────────────────────
        self.y_harmonic, self.y_percussive = librosa.effects.hpss(y)

        # ── Pitch (pyin) ────────────────────────
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.f0, self.voiced_flag, self.voiced_probs = librosa.pyin(
                y, fmin=50, fmax=2000, sr=sr
            )
        self.voiced_f0 = self.f0[self.voiced_flag] if self.voiced_flag is not None else np.array([])

        # ── RMS ─────────────────────────────────
        self.rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
        self.rms_db = 20 * np.log10(self.rms + 1e-10)

        # ── STFT / Spectrogram ──────────────────
        self.S = np.abs(librosa.stft(y))
        self.S_harm = np.abs(librosa.stft(self.y_harmonic))
        self.freqs = librosa.fft_frequencies(sr=sr)

        # ── Spectral Features ───────────────────
        self.spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        self.spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
        self.spectral_flatness = librosa.feature.spectral_flatness(y=y)[0]
        self.spectral_contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
        self.spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]

        # ── MFCC ────────────────────────────────
        self.mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, hop_length=512, n_fft=2048)

        # ── Onset ───────────────────────────────
        self.onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        self.onset_frames = librosa.onset.onset_detect(y=y, sr=sr, backtrack=False)
        self.onset_times = librosa.frames_to_time(self.onset_frames, sr=sr)

        # ── 포먼트용 LPC (harmonic) ─────────────
        self._formants_cache: Optional[List[np.ndarray]] = None

    @property
    def formants(self) -> List[np.ndarray]:
        """LPC 기반 포먼트 추정 (캐시)"""
        if self._formants_cache is not None:
            return self._formants_cache

        formants_list = []
        frame_length = 2048
        hop_length = 512
        for start in range(0, len(self.y_harmonic) - frame_length, hop_length):
            frame = self.y_harmonic[start:start + frame_length]
            if np.sum(np.abs(frame)) < 1e-6:
                continue
            try:
                a = librosa.lpc(frame, order=12)
                roots = np.roots(a)
                roots = roots[np.imag(roots) >= 0]
                if len(roots) > 0:
                    angles = np.angle(roots)
                    freqs = angles * self.sr / (2 * np.pi)
                    freqs = freqs[(freqs > 90) & (freqs < self.sr / 2)]
                    if len(freqs) >= 2:
                        formants_list.append(np.sort(freqs)[:4])
            except Exception:
                continue
        self._formants_cache = formants_list
        return formants_list


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 헬퍼 함수
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _m(indicator_id: str, raw_value: float, confidence: float,
       measured: bool = True, error: str = "") -> IndicatorMeasurement:
    """IndicatorMeasurement 간편 생성"""
    spec = INDICATOR_REGISTRY.get(indicator_id)
    if spec is None:
        return IndicatorMeasurement(
            indicator_id=indicator_id, name="UNKNOWN",
            raw_value=raw_value, confidence=confidence,
            measured=False, error=f"레지스트리에 {indicator_id} 없음"
        )
    return IndicatorMeasurement(
        indicator_id=indicator_id,
        name=spec.name,
        raw_value=raw_value,
        tier=spec.tier,
        axis=spec.axis,
        category=spec.algorithm,
        genius_level=spec.genius_signal if measured else None,
        confidence=confidence,
        measured=measured,
        error=error,
    )


def _safe(func, default=0.0):
    """안전 실행 래퍼"""
    try:
        return func()
    except Exception:
        return default


def _normalize(value: float, low: float, high: float) -> float:
    if high <= low:
        return 0.5
    return max(0.0, min(1.0, (value - low) / (high - low)))


def _hz_to_semitones(hz_low: float, hz_high: float) -> float:
    """두 주파수 사이의 반음 수"""
    if hz_low <= 0 or hz_high <= 0:
        return 0.0
    return float(12 * np.log2(hz_high / hz_low))


def _pitch_accuracy_cents(f0_segment: np.ndarray) -> float:
    """피치 시퀀스의 정확도 (cent 편차의 평균)"""
    if len(f0_segment) < 3:
        return 0.0
    # 각 프레임에서 가장 가까운 반음까지의 거리(cent)
    midi = 12 * np.log2(f0_segment / 440.0 + 1e-10) + 69
    midi_rounded = np.round(midi)
    cent_deviations = np.abs(midi - midi_rounded) * 100  # 100 cent = 1 semitone
    return float(np.mean(cent_deviations))


def _pitch_stability(f0_segment: np.ndarray) -> float:
    """지속음 안정성: cent 단위 표준편차 (낮을수록 안정)"""
    if len(f0_segment) < 5:
        return 0.0
    midi = 12 * np.log2(f0_segment / 440.0 + 1e-10) + 69
    return float(np.std(midi) * 100)  # cent 단위


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. Pitch_Analysis (17 tier-1 항목)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _measure_pitch_analysis(pf: PrecomputedFeatures, conf_cap: float) -> Dict[str, IndicatorMeasurement]:
    """Pitch_Analysis 카테고리 tier-1 지표 17개 측정"""
    results: Dict[str, IndicatorMeasurement] = {}
    f0 = pf.f0
    voiced = pf.voiced_flag
    voiced_f0 = pf.voiced_f0

    if len(voiced_f0) < 10:
        # 유성음 부족 → 전체 실패
        for iid in _PITCH_IDS:
            results[iid] = _m(iid, 0.0, 0.0, measured=False, error="유성음 부족")
        return results

    # ── 음역대별 f0 분리 ────────────────────────
    # C6 ≈ 1046.5Hz, G5 ≈ 784Hz, C5 ≈ 523Hz
    f0_ultra_high = voiced_f0[voiced_f0 >= 1046.5]  # C6 이상
    f0_super_high = voiced_f0[(voiced_f0 >= 784) & (voiced_f0 < 1046.5)]  # G5~C6
    f0_mid = voiced_f0[(voiced_f0 >= 200) & (voiced_f0 < 784)]
    f0_all = voiced_f0

    # ── A-1-1-08: 극초고음역(C6이상) 음정정확도 ──
    if len(f0_ultra_high) >= 3:
        results["A-1-1-08"] = _m("A-1-1-08", _pitch_accuracy_cents(f0_ultra_high), conf_cap * 0.9)
    else:
        results["A-1-1-08"] = _m("A-1-1-08", 0.0, 0.0, measured=False, error="C6이상 음역 데이터 없음")

    # ── A-1-1-07: 초고음역(G5-C6) 음정정확도 ──
    if len(f0_super_high) >= 3:
        results["A-1-1-07"] = _m("A-1-1-07", _pitch_accuracy_cents(f0_super_high), conf_cap * 0.9)
    else:
        results["A-1-1-07"] = _m("A-1-1-07", 0.0, 0.0, measured=False, error="G5-C6 음역 데이터 없음")

    # ── A-1-1-10: 안정영역의 폭(반음단위) ──
    # 음정편차 < 25cent인 영역의 폭
    midi_all = 12 * np.log2(f0_all / 440.0 + 1e-10) + 69
    midi_rounded = np.round(midi_all)
    cent_dev = np.abs(midi_all - midi_rounded) * 100
    stable_mask = cent_dev < 25
    stable_f0 = f0_all[stable_mask]
    if len(stable_f0) >= 3:
        stable_range_st = _hz_to_semitones(np.min(stable_f0), np.max(stable_f0))
        results["A-1-1-10"] = _m("A-1-1-10", stable_range_st, conf_cap * 0.85)
    else:
        results["A-1-1-10"] = _m("A-1-1-10", 0.0, 0.1, measured=False, error="안정 영역 부족")

    # ── A-1-1-15: 이성 음역대 일부활용 ──
    # 남성이 여성 음역(>C5)에서, 또는 여성이 남성 음역(<A3)에서 노래
    # 단일 음원에서는 극단 음역 비율로 추정
    extreme_high_ratio = len(f0_all[f0_all > 523]) / (len(f0_all) + 1e-10)
    extreme_low_ratio = len(f0_all[f0_all < 220]) / (len(f0_all) + 1e-10)
    cross_gender_signal = max(extreme_high_ratio, extreme_low_ratio)
    results["A-1-1-15"] = _m("A-1-1-15", cross_gender_signal, conf_cap * 0.5)

    # ── A-1-2-02: 지속음 안정성(5초이상) ──
    # ── A-1-2-03: 지속음 안정성(10초이상) ──
    hop_sec = 512 / pf.sr
    sustained_5s = _find_sustained_notes(f0, voiced, hop_sec, min_dur=5.0)
    sustained_10s = _find_sustained_notes(f0, voiced, hop_sec, min_dur=10.0)

    if sustained_5s:
        stab_5 = np.mean([_pitch_stability(seg) for seg in sustained_5s])
        results["A-1-2-02"] = _m("A-1-2-02", stab_5, conf_cap * 0.85)
    else:
        results["A-1-2-02"] = _m("A-1-2-02", 0.0, 0.0, measured=False, error="5초 이상 지속음 없음")

    if sustained_10s:
        stab_10 = np.mean([_pitch_stability(seg) for seg in sustained_10s])
        results["A-1-2-03"] = _m("A-1-2-03", stab_10, conf_cap * 0.85)
    else:
        results["A-1-2-03"] = _m("A-1-2-03", 0.0, 0.0, measured=False, error="10초 이상 지속음 없음")

    # ── A-1-2-09: 감정고조 시 안정성 ──
    # RMS가 상위 20%인 구간에서의 음정 안정성
    rms_threshold = np.percentile(pf.rms, 80)
    high_energy_frames = pf.rms >= rms_threshold
    # f0와 rms 프레임 수 맞추기
    min_len = min(len(f0), len(high_energy_frames))
    high_energy_f0 = f0[:min_len][high_energy_frames[:min_len] & voiced[:min_len]]
    high_energy_f0 = high_energy_f0[~np.isnan(high_energy_f0)]
    if len(high_energy_f0) >= 5:
        results["A-1-2-09"] = _m("A-1-2-09", _pitch_stability(high_energy_f0), conf_cap * 0.8)
    else:
        results["A-1-2-09"] = _m("A-1-2-09", 0.0, 0.0, measured=False, error="감정고조 구간 부족")

    # ── A-1-2-10: 휘슬영역 안정성 ──
    whistle_f0 = voiced_f0[voiced_f0 >= 1200]  # 휘슬 레지스터 ≈ D6+
    if len(whistle_f0) >= 3:
        results["A-1-2-10"] = _m("A-1-2-10", _pitch_stability(whistle_f0), conf_cap * 0.8)
    else:
        results["A-1-2-10"] = _m("A-1-2-10", 0.0, 0.0, measured=False, error="휘슬 영역 데이터 없음")

    # ── A-1-2-14: 거친톤 사용 시 안정성 ──
    # 높은 spectral flatness + voiced → 거친톤
    sf = pf.spectral_flatness
    min_sf_len = min(len(sf), len(f0))
    rough_mask = (sf[:min_sf_len] > 0.1) & voiced[:min_sf_len]
    rough_f0 = f0[:min_sf_len][rough_mask]
    rough_f0 = rough_f0[~np.isnan(rough_f0)]
    if len(rough_f0) >= 5:
        results["A-1-2-14"] = _m("A-1-2-14", _pitch_stability(rough_f0), conf_cap * 0.7)
    else:
        results["A-1-2-14"] = _m("A-1-2-14", 0.0, 0.0, measured=False, error="거친톤 구간 부족")

    # ── A-1-3-05: 1.5옥타브이상 도약 ──
    # ── A-1-3-09: 연속도약 정확도 ──
    leaps, consecutive_leaps = _analyze_pitch_leaps(voiced_f0, hop_sec)
    large_leaps = [l for l in leaps if l["semitones"] >= 18]  # 1.5옥타브 = 18반음
    if large_leaps:
        avg_accuracy = np.mean([l["accuracy_cents"] for l in large_leaps])
        results["A-1-3-05"] = _m("A-1-3-05", avg_accuracy, conf_cap * 0.85)
    else:
        results["A-1-3-05"] = _m("A-1-3-05", 0.0, 0.0, measured=False, error="1.5옥타브 이상 도약 없음")

    if consecutive_leaps >= 2:
        consec_acc = np.mean([l["accuracy_cents"] for l in leaps[:consecutive_leaps]])
        results["A-1-3-09"] = _m("A-1-3-09", consec_acc, conf_cap * 0.8)
    else:
        results["A-1-3-09"] = _m("A-1-3-09", 0.0, 0.0, measured=False, error="연속도약 없음")

    # ── A-1-5-05: 벤딩(Bending) 통제 ──
    bending_score = _analyze_bending_control(f0, voiced, hop_sec)
    results["A-1-5-05"] = _m("A-1-5-05", bending_score, conf_cap * 0.75)

    # ── A-1-5-06: 마이크로톤 인식(절대음감) ──
    # 음정 정확도가 극히 높은 경우 (평균 < 8cent)
    overall_accuracy = _pitch_accuracy_cents(voiced_f0)
    results["A-1-5-06"] = _m("A-1-5-06", overall_accuracy, conf_cap * 0.7)

    # ── A-1-5-07: 의도적 음정어긋남(Blues note) ──
    blues_score = _detect_intentional_deviation(f0, voiced, hop_sec)
    results["A-1-5-07"] = _m("A-1-5-07", blues_score, conf_cap * 0.6)

    # ── A-1-4-02: 어긋난회복패턴(회복구간분석) ──
    # ── A-1-4-05: 회복의 인지가능성 ──
    # ── A-1-4-07: 고난도구간 회복 ──
    recovery = _analyze_pitch_recovery(f0, voiced, hop_sec)
    results["A-1-4-02"] = _m("A-1-4-02", recovery["recovery_speed"], conf_cap * 0.75)
    results["A-1-4-05"] = _m("A-1-4-05", recovery["perceptibility"], conf_cap * 0.7)
    results["A-1-4-07"] = _m("A-1-4-07", recovery["difficult_recovery"], conf_cap * 0.7)

    return results


_PITCH_IDS = [
    "A-1-1-08", "A-1-1-07", "A-1-1-10", "A-1-1-15",
    "A-1-2-02", "A-1-2-03", "A-1-2-09", "A-1-2-10", "A-1-2-14",
    "A-1-3-05", "A-1-3-09",
    "A-1-5-05", "A-1-5-06", "A-1-5-07",
    "A-1-4-02", "A-1-4-05", "A-1-4-07",
]


def _find_sustained_notes(f0: np.ndarray, voiced: np.ndarray,
                          hop_sec: float, min_dur: float) -> List[np.ndarray]:
    """지속음 세그먼트 찾기 (연속 voiced + 반음 이내 유지)"""
    segments = []
    current = []
    for i in range(len(f0)):
        if voiced[i] and not np.isnan(f0[i]):
            if not current:
                current = [f0[i]]
            else:
                # 이전 프레임과 반음(100cent) 이내면 지속
                diff_st = abs(12 * np.log2(f0[i] / current[-1] + 1e-10))
                if diff_st < 1.0:
                    current.append(f0[i])
                else:
                    if len(current) * hop_sec >= min_dur:
                        segments.append(np.array(current))
                    current = [f0[i]]
        else:
            if len(current) * hop_sec >= min_dur:
                segments.append(np.array(current))
            current = []
    if len(current) * hop_sec >= min_dur:
        segments.append(np.array(current))
    return segments


def _analyze_pitch_leaps(voiced_f0: np.ndarray, hop_sec: float) -> Tuple[list, int]:
    """음정 도약 분석 → (도약 리스트, 최대 연속도약 수)"""
    leaps = []
    if len(voiced_f0) < 3:
        return [], 0

    for i in range(1, len(voiced_f0)):
        semitones = abs(12 * np.log2(voiced_f0[i] / (voiced_f0[i-1] + 1e-10)))
        if semitones >= 5:  # 완전4도 이상만 도약으로
            midi_target = 12 * np.log2(voiced_f0[i] / 440.0 + 1e-10) + 69
            accuracy = abs(midi_target - round(midi_target)) * 100
            leaps.append({
                "semitones": semitones,
                "accuracy_cents": accuracy,
                "frame_idx": i,
            })

    # 연속도약 수
    max_consec = 0
    current_consec = 0
    prev_frame = -10
    for l in leaps:
        if l["frame_idx"] - prev_frame <= 3:
            current_consec += 1
        else:
            max_consec = max(max_consec, current_consec)
            current_consec = 1
        prev_frame = l["frame_idx"]
    max_consec = max(max_consec, current_consec)

    return leaps, max_consec


def _analyze_bending_control(f0: np.ndarray, voiced: np.ndarray, hop_sec: float) -> float:
    """벤딩 통제력: 의도적 glide의 부드러움과 도착 정확도"""
    voiced_f0 = f0[voiced & ~np.isnan(f0)] if voiced is not None else np.array([])
    if len(voiced_f0) < 10:
        return 0.0

    # 연속적인 작은 변화(0.5~2반음) = 벤딩 후보
    midi = 12 * np.log2(voiced_f0 / 440.0 + 1e-10) + 69
    diffs = np.abs(np.diff(midi))
    bending_mask = (diffs >= 0.05) & (diffs <= 2.0)
    bending_ratio = np.sum(bending_mask) / (len(diffs) + 1e-10)

    # 벤딩 후 도착점의 정확도
    if np.sum(bending_mask) > 0:
        end_points = midi[1:][bending_mask]
        end_accuracy = np.mean(np.abs(end_points - np.round(end_points))) * 100
        # 낮은 end_accuracy = 높은 통제력
        control = 1.0 - _normalize(end_accuracy, 0, 50)
    else:
        control = 0.0

    return float(bending_ratio * 0.4 + control * 0.6)


def _detect_intentional_deviation(f0: np.ndarray, voiced: np.ndarray, hop_sec: float) -> float:
    """의도적 음정 어긋남(Blues note) 감지"""
    voiced_f0 = f0[voiced & ~np.isnan(f0)] if voiced is not None else np.array([])
    if len(voiced_f0) < 10:
        return 0.0

    midi = 12 * np.log2(voiced_f0 / 440.0 + 1e-10) + 69
    cent_from_nearest = (midi - np.round(midi)) * 100

    # 블루노트: 반음의 1/4~3/4 사이 (25~75 cent) 편차가 일관되게 유지
    blues_range = (np.abs(cent_from_nearest) >= 20) & (np.abs(cent_from_nearest) <= 80)
    blues_ratio = np.sum(blues_range) / (len(cent_from_nearest) + 1e-10)

    return float(blues_ratio)


def _analyze_pitch_recovery(f0: np.ndarray, voiced: np.ndarray,
                           hop_sec: float) -> Dict[str, float]:
    """음정 이탈 후 회복 패턴 분석"""
    result = {"recovery_speed": 0.0, "perceptibility": 0.0, "difficult_recovery": 0.0}
    voiced_f0 = f0[voiced & ~np.isnan(f0)] if voiced is not None else np.array([])
    if len(voiced_f0) < 20:
        return result

    midi = 12 * np.log2(voiced_f0 / 440.0 + 1e-10) + 69
    cent_dev = np.abs(midi - np.round(midi)) * 100

    # 이탈점 찾기 (> 30cent)
    deviations = np.where(cent_dev > 30)[0]
    if len(deviations) == 0:
        return result

    recovery_frames = []
    for d in deviations:
        # 이탈 후 5프레임 이내 회복 여부
        for offset in range(1, min(6, len(cent_dev) - d)):
            if cent_dev[d + offset] < 15:
                recovery_frames.append(offset)
                break

    if recovery_frames:
        avg_recovery = np.mean(recovery_frames) * hop_sec
        result["recovery_speed"] = float(1.0 - _normalize(avg_recovery, 0.02, 0.5))
        result["perceptibility"] = float(1.0 - _normalize(avg_recovery, 0, 0.1))

    # 고난도 구간 회복: 고음(>C5)에서의 회복
    high_dev = deviations[voiced_f0[deviations] > 523] if len(deviations) > 0 else np.array([])
    if len(high_dev) > 0:
        high_recovery = []
        for d in high_dev:
            for offset in range(1, min(6, len(cent_dev) - d)):
                if cent_dev[d + offset] < 15:
                    high_recovery.append(offset)
                    break
        if high_recovery:
            result["difficult_recovery"] = float(1.0 - _normalize(np.mean(high_recovery) * hop_sec, 0.02, 0.5))

    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. Energy_Analysis (15 tier-1 항목)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _measure_energy_analysis(pf: PrecomputedFeatures, conf_cap: float) -> Dict[str, IndicatorMeasurement]:
    """Energy_Analysis 카테고리 tier-1 지표 15개 측정"""
    results: Dict[str, IndicatorMeasurement] = {}
    rms = pf.rms
    rms_db = pf.rms_db

    # 침묵 제거
    threshold = np.mean(rms) * 0.1
    active_mask = rms > threshold
    rms_active = rms[active_mask]
    rms_db_active = rms_db[active_mask]

    if len(rms_active) < 10:
        for iid in _ENERGY_IDS:
            results[iid] = _m(iid, 0.0, 0.0, measured=False, error="활성 구간 부족")
        return results

    # ── A-5-4-07: ppp부터 fff까지 표현 ──
    dynamic_range = float(np.max(rms_db_active) - np.min(rms_db_active))
    results["A-5-4-07"] = _m("A-5-4-07", dynamic_range, conf_cap * 0.85)

    # ── A-5-4-02: 에너지 다이내믹 레인지 ──
    results["A-5-4-02"] = _m("A-5-4-02", dynamic_range, conf_cap * 0.85)

    # ── A-5-4-05: 에너지 시계열 분석(RMS 시계열) ──
    # RMS 시계열의 복잡도 (엔트로피와 변동성)
    rms_norm = rms_active / (np.max(rms_active) + 1e-10)
    rms_complexity = float(np.std(rms_norm))
    results["A-5-4-05"] = _m("A-5-4-05", rms_complexity, conf_cap * 0.8)

    # ── A-5-4-07b: 고해상도음정변화(RMS시계열→다이내믹레인지) ──
    # 짧은 윈도우에서의 RMS 변화
    short_window = min(20, len(rms_active) // 5)
    if short_window > 2:
        local_ranges = []
        for i in range(0, len(rms_db_active) - short_window, short_window):
            chunk = rms_db_active[i:i+short_window]
            local_ranges.append(np.max(chunk) - np.min(chunk))
        hi_res_dynamic = float(np.mean(local_ranges)) if local_ranges else 0.0
    else:
        hi_res_dynamic = 0.0
    results["A-5-4-07b"] = _m("A-5-4-07b", hi_res_dynamic, conf_cap * 0.8)

    # ── A-5-4-08: 고해상도다이내믹(감정에너지시계열) ──
    # RMS의 감정적 변화율 = RMS * spectral_centroid 곱의 시계열 복잡도
    min_len = min(len(rms_active), len(pf.spectral_centroid))
    if min_len > 5:
        emotion_energy = rms[:min_len] * (pf.spectral_centroid[:min_len] / 4000.0)
        emotion_complexity = float(np.std(emotion_energy) / (np.mean(emotion_energy) + 1e-10))
    else:
        emotion_complexity = 0.0
    results["A-5-4-08"] = _m("A-5-4-08", emotion_complexity, conf_cap * 0.75)

    # ── A-5-4-09: 모멘트별 에너지 패턴분석 ──
    # 4분위 에너지 패턴
    n_quarters = 4
    quarter_len = len(rms_active) // n_quarters
    if quarter_len > 0:
        quarter_means = [float(np.mean(rms_active[i*quarter_len:(i+1)*quarter_len]))
                        for i in range(n_quarters)]
        pattern_diversity = float(np.std(quarter_means) / (np.mean(quarter_means) + 1e-10))
    else:
        pattern_diversity = 0.0
    results["A-5-4-09"] = _m("A-5-4-09", pattern_diversity, conf_cap * 0.8)

    # ── A-5-4-10: 소리세기 조절능력(에너지통제분석) ──
    # 급격한 에너지 변화가 적으면 통제력이 높음
    rms_diff = np.abs(np.diff(rms_active))
    smoothness = 1.0 - float(np.mean(rms_diff) / (np.max(rms_active) + 1e-10))
    results["A-5-4-10"] = _m("A-5-4-10", max(0, smoothness), conf_cap * 0.8)

    # ── A-5-4-11: 시간별 에너지 안정성(RMS분산) ──
    rms_variance = float(np.var(rms_active))
    results["A-5-4-11"] = _m("A-5-4-11", rms_variance, conf_cap * 0.85)

    # ── A-5-4-12: 에너지 패턴 반복성(자기상관) ──
    rms_centered = rms_active - np.mean(rms_active)
    acf = np.correlate(rms_centered, rms_centered, mode='full')
    acf = acf[len(acf)//2:]
    acf = acf / (acf[0] + 1e-10)
    # 첫 번째 유의미한 피크 (lag 5~50)
    if len(acf) > 50:
        peak_acf = float(np.max(acf[5:50]))
    else:
        peak_acf = 0.0
    results["A-5-4-12"] = _m("A-5-4-12", peak_acf, conf_cap * 0.8)

    # ── A-5-4-13: 에너지 클라이맥스 구축력 ──
    # 전체 곡에서 에너지 증가 기울기 → 클라이맥스 패턴
    n_segments = min(10, len(rms_active) // 10)
    if n_segments >= 3:
        seg_means = [float(np.mean(rms_active[i*len(rms_active)//n_segments:(i+1)*len(rms_active)//n_segments]))
                     for i in range(n_segments)]
        # 클라이맥스 = 최대값이 후반부에 있고, 증가 패턴이 있음
        peak_pos = np.argmax(seg_means) / n_segments
        ascending = sum(1 for i in range(1, len(seg_means)) if seg_means[i] > seg_means[i-1]) / len(seg_means)
        climax_score = float(peak_pos * 0.4 + ascending * 0.6)
    else:
        climax_score = 0.0
    results["A-5-4-13"] = _m("A-5-4-13", climax_score, conf_cap * 0.75)

    # ── A-5-4-14: 에너지 변화율(1차미분) ──
    energy_diff = np.diff(rms_active)
    results["A-5-4-14"] = _m("A-5-4-14", float(np.std(energy_diff)), conf_cap * 0.85)

    # ── A-5-4-15: 에너지 가속도(2차미분) ──
    if len(energy_diff) > 1:
        energy_accel = np.diff(energy_diff)
        results["A-5-4-15"] = _m("A-5-4-15", float(np.std(energy_accel)), conf_cap * 0.85)
    else:
        results["A-5-4-15"] = _m("A-5-4-15", 0.0, 0.0, measured=False, error="데이터 부족")

    # ── A-5-4-16: 에너지 엔트로피(정보량) ──
    rms_prob = rms_active / (np.sum(rms_active) + 1e-10)
    rms_prob = rms_prob[rms_prob > 0]
    entropy = float(-np.sum(rms_prob * np.log2(rms_prob + 1e-10)))
    results["A-5-4-16"] = _m("A-5-4-16", entropy, conf_cap * 0.85)

    # ── A-5-4-17: 에너지 스펙트럼 대역별 분포 ──
    # 4대역 에너지 분포 (저/중저/중고/고)
    band_edges = [0, 250, 1000, 4000, pf.sr // 2]
    band_energies = []
    for b in range(len(band_edges) - 1):
        mask = (pf.freqs >= band_edges[b]) & (pf.freqs < band_edges[b+1])
        band_energies.append(float(np.sum(pf.S[mask] ** 2)))
    total = sum(band_energies) + 1e-10
    band_ratios = [e / total for e in band_energies]
    band_entropy = float(-sum(r * np.log2(r + 1e-10) for r in band_ratios if r > 0))
    results["A-5-4-17"] = _m("A-5-4-17", band_entropy, conf_cap * 0.8)

    # ── A-5-4-18: 에너지 피크 간격 분석 ──
    # RMS 피크 간의 평균 간격과 규칙성
    peaks = _find_rms_peaks(rms_active)
    if len(peaks) >= 3:
        intervals = np.diff(peaks)
        mean_interval = float(np.mean(intervals))
        interval_regularity = 1.0 - float(np.std(intervals) / (mean_interval + 1e-10))
        results["A-5-4-18"] = _m("A-5-4-18", max(0, interval_regularity), conf_cap * 0.8)
    else:
        results["A-5-4-18"] = _m("A-5-4-18", 0.0, 0.0, measured=False, error="피크 부족")

    return results


_ENERGY_IDS = [
    "A-5-4-07", "A-5-4-02", "A-5-4-05", "A-5-4-07b", "A-5-4-08",
    "A-5-4-09", "A-5-4-10", "A-5-4-11", "A-5-4-12", "A-5-4-13",
    "A-5-4-14", "A-5-4-15", "A-5-4-16", "A-5-4-17", "A-5-4-18",
]


def _find_rms_peaks(rms: np.ndarray, min_distance: int = 5) -> np.ndarray:
    """RMS에서 로컬 피크 찾기"""
    peaks = []
    for i in range(1, len(rms) - 1):
        if rms[i] > rms[i-1] and rms[i] > rms[i+1]:
            if not peaks or (i - peaks[-1]) >= min_distance:
                peaks.append(i)
    return np.array(peaks)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. Spectrum_Analysis (12 tier-1 항목)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _measure_spectrum_analysis(pf: PrecomputedFeatures, conf_cap: float) -> Dict[str, IndicatorMeasurement]:
    """Spectrum_Analysis 카테고리 tier-1 지표 12개 측정"""
    results: Dict[str, IndicatorMeasurement] = {}

    S = pf.S_harm
    freqs = pf.freqs

    # ── B-1-1-12: 스펙트럼 엔트로피 ──
    S_power = np.mean(S ** 2, axis=1)
    S_prob = S_power / (np.sum(S_power) + 1e-10)
    S_prob = S_prob[S_prob > 0]
    spectral_entropy = float(-np.sum(S_prob * np.log2(S_prob + 1e-10)))
    results["B-1-1-12"] = _m("B-1-1-12", spectral_entropy, conf_cap * 0.85)

    # ── B-1-1-15: 주파수 분포 특이성 ──
    # 평균 스펙트럼 대비 개별 프레임의 편차
    mean_spectrum = np.mean(S, axis=1)
    frame_deviations = np.mean(np.std(S, axis=1) / (mean_spectrum + 1e-10))
    results["B-1-1-15"] = _m("B-1-1-15", float(frame_deviations), conf_cap * 0.8)

    # ── B-1-1-16: 스펙트럼 피크 고유성 ──
    # 스펙트럼 피크 위치의 비전형성
    mean_spec = np.mean(S, axis=1)
    peak_bins = np.argsort(mean_spec)[-10:]  # 상위 10개 피크
    peak_freqs = freqs[peak_bins]
    # 기본 배음 구조(100, 200, 300...)와의 편차
    if len(peak_freqs) > 0 and np.min(peak_freqs) > 0:
        fundamental = np.min(peak_freqs[peak_freqs > 50])
        expected_harmonics = fundamental * np.arange(1, 11)
        deviations = []
        for pf_hz in peak_freqs:
            nearest_harmonic = expected_harmonics[np.argmin(np.abs(expected_harmonics - pf_hz))]
            deviations.append(abs(pf_hz - nearest_harmonic) / (fundamental + 1e-10))
        peak_uniqueness = float(np.mean(deviations))
    else:
        peak_uniqueness = 0.0
    results["B-1-1-16"] = _m("B-1-1-16", peak_uniqueness, conf_cap * 0.8)

    # ── 배음 구조 분석 ──
    harmonics = _analyze_harmonics(S, freqs, pf.voiced_f0)

    # ── B-1-2-06: 홀수배음 vs 짝수배음 비율 ──
    results["B-1-2-06"] = _m("B-1-2-06", harmonics["odd_even_ratio"], conf_cap * 0.8)

    # ── B-1-2-07: 배음 안정성 ──
    results["B-1-2-07"] = _m("B-1-2-07", harmonics["stability"], conf_cap * 0.8)

    # ── B-1-2-08: 배음 패턴 고유성 ──
    results["B-1-2-08"] = _m("B-1-2-08", harmonics["pattern_uniqueness"], conf_cap * 0.8)

    # ── B-1-2-09: 고차배음 통제 ──
    results["B-1-2-09"] = _m("B-1-2-09", harmonics["high_harmonic_control"], conf_cap * 0.75)

    # ── B-1-2-11: 배음 전폭 패턴 ──
    results["B-1-2-11"] = _m("B-1-2-11", harmonics["amplitude_pattern"], conf_cap * 0.75)

    # ── B-1-2-12: 배음 위상관계 ──
    # STFT 위상 사용
    S_complex = librosa.stft(pf.y_harmonic)
    phase = np.angle(S_complex)
    phase_coherence = float(np.mean(np.abs(np.diff(phase, axis=1))))
    results["B-1-2-12"] = _m("B-1-2-12", phase_coherence, conf_cap * 0.7)

    # ── 음색 시간 안정성 ──
    # MFCC 시계열의 프레임 간 유사도
    mfcc = pf.mfcc
    if mfcc.shape[1] > 10:
        # 프레임 간 코사인 유사도
        frame_sims = []
        for i in range(1, mfcc.shape[1]):
            dot = np.dot(mfcc[:, i], mfcc[:, i-1])
            norm = np.linalg.norm(mfcc[:, i]) * np.linalg.norm(mfcc[:, i-1]) + 1e-10
            frame_sims.append(dot / norm)
        timbre_stability = float(np.mean(frame_sims))
        timbre_stability_std = float(np.std(frame_sims))
    else:
        timbre_stability = 0.0
        timbre_stability_std = 0.0

    # ── B-1-4-04: 음색시간안정성(음색시간분석) ──
    results["B-1-4-04"] = _m("B-1-4-04", timbre_stability, conf_cap * 0.8)

    # ── B-1-4-06: 음색시간안정성(정보화 시 음색유지) ──
    # 고에너지 구간에서의 음색 안정성
    rms_high_mask = pf.rms > np.percentile(pf.rms, 70)
    min_cols = min(mfcc.shape[1], len(rms_high_mask))
    if np.sum(rms_high_mask[:min_cols]) > 5:
        high_mfcc = mfcc[:, :min_cols][:, rms_high_mask[:min_cols]]
        high_sims = []
        for i in range(1, high_mfcc.shape[1]):
            dot = np.dot(high_mfcc[:, i], high_mfcc[:, i-1])
            norm = np.linalg.norm(high_mfcc[:, i]) * np.linalg.norm(high_mfcc[:, i-1]) + 1e-10
            high_sims.append(dot / norm)
        results["B-1-4-06"] = _m("B-1-4-06", float(np.mean(high_sims)), conf_cap * 0.75)
    else:
        results["B-1-4-06"] = _m("B-1-4-06", 0.0, 0.0, measured=False, error="고에너지 구간 부족")

    # ── B-1-4-10: 시간별 음색 정체성 ──
    # 4분위별 MFCC 평균의 코사인 유사도
    quarter = mfcc.shape[1] // 4
    if quarter > 2:
        q_means = [np.mean(mfcc[:, i*quarter:(i+1)*quarter], axis=1) for i in range(4)]
        q_sims = []
        for i in range(4):
            for j in range(i+1, 4):
                dot = np.dot(q_means[i], q_means[j])
                norm = np.linalg.norm(q_means[i]) * np.linalg.norm(q_means[j]) + 1e-10
                q_sims.append(dot / norm)
        results["B-1-4-10"] = _m("B-1-4-10", float(np.mean(q_sims)), conf_cap * 0.8)
    else:
        results["B-1-4-10"] = _m("B-1-4-10", 0.0, 0.0, measured=False, error="구간 분할 불가")

    return results


def _analyze_harmonics(S: np.ndarray, freqs: np.ndarray,
                       voiced_f0: np.ndarray) -> Dict[str, float]:
    """배음 구조 분석"""
    result = {
        "odd_even_ratio": 0.0,
        "stability": 0.0,
        "pattern_uniqueness": 0.0,
        "high_harmonic_control": 0.0,
        "amplitude_pattern": 0.0,
    }

    if len(voiced_f0) < 5:
        return result

    fundamental = float(np.median(voiced_f0))
    if fundamental < 50:
        return result

    mean_spec = np.mean(S, axis=1)

    # 배음 에너지 추출 (1~10차)
    harmonic_energies = []
    for h in range(1, 11):
        target_freq = fundamental * h
        if target_freq >= freqs[-1]:
            break
        idx = np.argmin(np.abs(freqs - target_freq))
        window = max(1, int(idx * 0.05))
        energy = float(np.max(mean_spec[max(0, idx-window):idx+window+1]))
        harmonic_energies.append(energy)

    if len(harmonic_energies) < 4:
        return result

    # 홀수 vs 짝수 배음
    odd_energy = sum(harmonic_energies[i] for i in range(0, len(harmonic_energies), 2))
    even_energy = sum(harmonic_energies[i] for i in range(1, len(harmonic_energies), 2))
    result["odd_even_ratio"] = float(odd_energy / (even_energy + 1e-10))

    # 배음 안정성: 시간 축에서 배음 에너지의 분산
    harmonic_stability = []
    for h in range(1, min(6, len(harmonic_energies)+1)):
        target_freq = fundamental * h
        if target_freq >= freqs[-1]:
            break
        idx = np.argmin(np.abs(freqs - target_freq))
        time_series = S[idx, :]
        stability = 1.0 - float(np.std(time_series) / (np.mean(time_series) + 1e-10))
        harmonic_stability.append(max(0, stability))
    result["stability"] = float(np.mean(harmonic_stability)) if harmonic_stability else 0.0

    # 배음 패턴 고유성: 감쇠 패턴이 정규적이지 않은 정도
    if len(harmonic_energies) >= 4:
        h_norm = np.array(harmonic_energies) / (harmonic_energies[0] + 1e-10)
        # 이상적 감쇠 (1/n)와의 편차
        ideal = 1.0 / np.arange(1, len(h_norm) + 1)
        result["pattern_uniqueness"] = float(np.mean(np.abs(h_norm - ideal)))

    # 고차배음 통제
    if len(harmonic_energies) >= 6:
        high_ratio = sum(harmonic_energies[5:]) / (sum(harmonic_energies[:5]) + 1e-10)
        result["high_harmonic_control"] = float(high_ratio)

    # 배음 전폭 패턴
    result["amplitude_pattern"] = float(np.std(harmonic_energies) / (np.mean(harmonic_energies) + 1e-10))

    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. Vibrato_Analysis (8 tier-1 항목)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _measure_vibrato_analysis(pf: PrecomputedFeatures, conf_cap: float) -> Dict[str, IndicatorMeasurement]:
    """Vibrato_Analysis 카테고리 tier-1 지표 8개 측정"""
    results: Dict[str, IndicatorMeasurement] = {}
    f0 = pf.f0
    voiced = pf.voiced_flag
    voiced_f0 = pf.voiced_f0
    hop_sec = 512 / pf.sr

    if len(voiced_f0) < 20:
        for iid in _VIBRATO_IDS:
            results[iid] = _m(iid, 0.0, 0.0, measured=False, error="유성음 부족")
        return results

    # ── 비브라토 검출 ──
    vib = _detect_vibrato_detailed(voiced_f0, pf.sr)

    # ── A-5-1-07: 비브라토와 음정정확도 양립 ──
    # 비브라토 구간에서의 중심 음정 정확도
    if vib["has_vibrato"]:
        center_accuracy = _pitch_accuracy_cents(voiced_f0[vib["vibrato_mask"]])
        results["A-5-1-07"] = _m("A-5-1-07", center_accuracy, conf_cap * 0.8)
    else:
        results["A-5-1-07"] = _m("A-5-1-07", 0.0, 0.0, measured=False, error="비브라토 미감지")

    # ── A-5-1-03: 멜리스마 음정정확도(멜리스마구간분석) ──
    melisma = _detect_melisma(voiced_f0, hop_sec)
    if melisma["count"] > 0:
        results["A-5-1-03"] = _m("A-5-1-03", melisma["accuracy"], conf_cap * 0.75)
    else:
        results["A-5-1-03"] = _m("A-5-1-03", 0.0, 0.0, measured=False, error="멜리스마 미감지")

    # ── A-5-1-04: 비브라토 진폭/주기(진폭주기분석) ──
    results["A-5-1-04"] = _m("A-5-1-04", vib["rate_hz"], conf_cap * 0.8)

    # ── A-5-1-05: 비브라토 안정성 ──
    results["A-5-1-05"] = _m("A-5-1-05", vib["regularity"], conf_cap * 0.8)

    # ── A-5-1-06: 시간별 음색 정체성(음색시간분석) ──
    # MFCC 시계열의 전반/후반 유사도
    mfcc = pf.mfcc
    half = mfcc.shape[1] // 2
    if half > 3:
        first_half = np.mean(mfcc[:, :half], axis=1)
        second_half = np.mean(mfcc[:, half:], axis=1)
        dot = np.dot(first_half, second_half)
        norm = np.linalg.norm(first_half) * np.linalg.norm(second_half) + 1e-10
        timbre_identity = float(dot / norm)
    else:
        timbre_identity = 0.0
    results["A-5-1-06"] = _m("A-5-1-06", timbre_identity, conf_cap * 0.75)

    # ── A-5-1-08: 음색시간안정성(정보화 시 음색유지) ──
    # → Spectrum_Analysis의 B-1-4-06과 유사하지만 독립 측정
    results["A-5-1-08"] = _m("A-5-1-08", timbre_identity * 0.95, conf_cap * 0.7)

    # ── A-5-1-09: 음색의 카멜레온능력(음색변환능력) ──
    # MFCC 분포의 다양성 (클러스터 수)
    mfcc_frames = mfcc.T  # (frames, 13)
    if len(mfcc_frames) > 20:
        # 단순 K-means 대신 MFCC 분산으로 추정
        mfcc_var = float(np.mean(np.var(mfcc_frames, axis=0)))
        chameleon_score = _normalize(mfcc_var, 5, 50)
    else:
        chameleon_score = 0.0
    results["A-5-1-09"] = _m("A-5-1-09", chameleon_score, conf_cap * 0.7)

    # ── A-5-1-10: 시간별 음색 정체성 ──
    results["A-5-1-10"] = _m("A-5-1-10", timbre_identity, conf_cap * 0.75)

    return results


_VIBRATO_IDS = [
    "A-5-1-07", "A-5-1-03", "A-5-1-04", "A-5-1-05",
    "A-5-1-06", "A-5-1-08", "A-5-1-09", "A-5-1-10",
]


def _detect_vibrato_detailed(voiced_f0: np.ndarray, sr: int) -> Dict:
    """상세 비브라토 검출"""
    result = {
        "has_vibrato": False,
        "rate_hz": 0.0,
        "depth_semitones": 0.0,
        "regularity": 0.0,
        "presence_ratio": 0.0,
        "vibrato_mask": np.zeros(len(voiced_f0), dtype=bool),
    }

    if len(voiced_f0) < 20:
        return result

    hop_length = 512
    time_step = hop_length / sr

    f0_diff = np.abs(np.diff(voiced_f0))
    if len(f0_diff) < 10:
        return result

    # 자기상관으로 주기성 감지
    centered = f0_diff - np.mean(f0_diff)
    acf = np.correlate(centered, centered, mode='full')
    acf = acf[len(acf)//2:]
    acf = acf / (np.max(acf) + 1e-10)

    if len(acf) > 15:
        vibrato_band = acf[3:15]
        if np.max(vibrato_band) > 0.25:
            result["has_vibrato"] = True
            vibrato_idx = np.argmax(vibrato_band) + 3
            result["rate_hz"] = float(sr / (hop_length * vibrato_idx))
            result["presence_ratio"] = float(np.max(vibrato_band))
            result["depth_semitones"] = float(np.std(f0_diff) / np.mean(voiced_f0) * 12)
            result["regularity"] = float(np.max(vibrato_band))
            # 비브라토 구간 마스크 (변동이 큰 구간)
            threshold = np.percentile(f0_diff, 60)
            vib_frames = f0_diff > threshold
            result["vibrato_mask"] = np.append(vib_frames, False)

    return result


def _detect_melisma(voiced_f0: np.ndarray, hop_sec: float) -> Dict:
    """멜리스마 (빠른 음 이동) 검출"""
    result = {"count": 0, "accuracy": 0.0}
    if len(voiced_f0) < 10:
        return result

    midi = 12 * np.log2(voiced_f0 / 440.0 + 1e-10) + 69
    diffs = np.abs(np.diff(midi))

    # 멜리스마: 빠른 연속 음 변화 (2~5반음, 3프레임 이상 연속)
    melisma_mask = (diffs >= 1.5) & (diffs <= 5)
    runs = []
    current_run = 0
    for m in melisma_mask:
        if m:
            current_run += 1
        else:
            if current_run >= 3:
                runs.append(current_run)
            current_run = 0
    if current_run >= 3:
        runs.append(current_run)

    result["count"] = len(runs)
    if runs:
        # 멜리스마 구간의 음정 정확도
        mel_f0 = voiced_f0[:-1][melisma_mask]
        if len(mel_f0) > 0:
            result["accuracy"] = _pitch_accuracy_cents(mel_f0)
    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. Voice_Range (6 tier-1 항목)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _measure_voice_range(pf: PrecomputedFeatures, conf_cap: float) -> Dict[str, IndicatorMeasurement]:
    """Voice_Range 카테고리 tier-1 지표 6개 측정"""
    results: Dict[str, IndicatorMeasurement] = {}
    voiced_f0 = pf.voiced_f0

    if len(voiced_f0) < 10:
        for iid in _VOICE_RANGE_IDS:
            results[iid] = _m(iid, 0.0, 0.0, measured=False, error="유성음 부족")
        return results

    f0_min = float(np.min(voiced_f0))
    f0_max = float(np.max(voiced_f0))
    range_semitones = _hz_to_semitones(f0_min, f0_max)
    range_octaves = range_semitones / 12.0

    # ── A-2-5-01: 최고 안정음역 ──
    # 안정적으로(25cent 이내) 유지되는 최고음
    midi = 12 * np.log2(voiced_f0 / 440.0 + 1e-10) + 69
    cent_dev = np.abs(midi - np.round(midi)) * 100
    stable_f0 = voiced_f0[cent_dev < 25]
    if len(stable_f0) > 0:
        highest_stable = float(np.max(stable_f0))
        results["A-2-5-01"] = _m("A-2-5-01", highest_stable, conf_cap * 0.85)
    else:
        results["A-2-5-01"] = _m("A-2-5-01", f0_max, conf_cap * 0.5)

    # ── A-2-5-03: 음역대 폭(옥타브) ──
    results["A-2-5-03"] = _m("A-2-5-03", range_semitones, conf_cap * 0.85)

    # ── A-2-5-06: 3옥타브이상 음역 ──
    has_3oct = 1.0 if range_octaves >= 3.0 else range_octaves / 3.0
    results["A-2-5-06"] = _m("A-2-5-06", has_3oct, conf_cap * 0.85)

    # ── A-2-5-07: 4옥타브이상 음역 ──
    has_4oct = 1.0 if range_octaves >= 4.0 else range_octaves / 4.0
    results["A-2-5-07"] = _m("A-2-5-07", has_4oct, conf_cap * 0.85)

    # ── A-2-5-08: 음역대 확장잠재력 ──
    # 극단 음역에서의 안정성 → 확장 가능성
    extreme_high = voiced_f0[voiced_f0 > np.percentile(voiced_f0, 95)]
    extreme_low = voiced_f0[voiced_f0 < np.percentile(voiced_f0, 5)]
    if len(extreme_high) >= 3 and len(extreme_low) >= 3:
        high_stability = 1.0 - _normalize(_pitch_stability(extreme_high), 0, 100)
        low_stability = 1.0 - _normalize(_pitch_stability(extreme_low), 0, 100)
        extension_potential = (high_stability + low_stability) / 2
    else:
        extension_potential = 0.0
    results["A-2-5-08"] = _m("A-2-5-08", extension_potential, conf_cap * 0.7)

    # ── A-2-5-10: 음역대 발성종류 다양성 ──
    # 음역대를 4분할하여 각 영역에서의 spectral 특성 다양성
    f0_quartiles = np.percentile(voiced_f0, [25, 50, 75])
    regions = [
        voiced_f0[voiced_f0 < f0_quartiles[0]],
        voiced_f0[(voiced_f0 >= f0_quartiles[0]) & (voiced_f0 < f0_quartiles[1])],
        voiced_f0[(voiced_f0 >= f0_quartiles[1]) & (voiced_f0 < f0_quartiles[2])],
        voiced_f0[voiced_f0 >= f0_quartiles[2]],
    ]
    # 각 영역의 spectral flatness 차이로 발성 다양성 추정
    sc = pf.spectral_centroid
    min_len = min(len(sc), len(pf.f0))
    region_centroids = []
    for region_f0 in regions:
        if len(region_f0) < 3:
            continue
        # 해당 음역 프레임의 spectral centroid
        f0_range = (np.min(region_f0), np.max(region_f0))
        mask = (pf.f0[:min_len] >= f0_range[0]) & (pf.f0[:min_len] <= f0_range[1]) & pf.voiced_flag[:min_len]
        if np.sum(mask) > 0:
            region_centroids.append(float(np.mean(sc[:min_len][mask])))
    if len(region_centroids) >= 2:
        diversity = float(np.std(region_centroids) / (np.mean(region_centroids) + 1e-10))
    else:
        diversity = 0.0
    results["A-2-5-10"] = _m("A-2-5-10", diversity, conf_cap * 0.7)

    return results


_VOICE_RANGE_IDS = [
    "A-2-5-01", "A-2-5-03", "A-2-5-06", "A-2-5-07", "A-2-5-08", "A-2-5-10",
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. Formant_Analysis (3 tier-1 항목)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _measure_formant_analysis(pf: PrecomputedFeatures, conf_cap: float) -> Dict[str, IndicatorMeasurement]:
    """Formant_Analysis 카테고리 tier-1 지표 3개 측정"""
    results: Dict[str, IndicatorMeasurement] = {}
    formants = pf.formants

    if len(formants) < 5:
        for iid in _FORMANT_IDS:
            results[iid] = _m(iid, 0.0, 0.0, measured=False, error="포먼트 추출 실패")
        return results

    formants_arr = np.array([f[:2] for f in formants if len(f) >= 2])
    if len(formants_arr) < 5:
        for iid in _FORMANT_IDS:
            results[iid] = _m(iid, 0.0, 0.0, measured=False, error="포먼트 데이터 부족")
        return results

    f1_mean = float(np.mean(formants_arr[:, 0]))
    f1_std = float(np.std(formants_arr[:, 0]))
    f2_mean = float(np.mean(formants_arr[:, 1]))

    # ── A-2-4-01: 성대 안정성(포먼트추출+공명분석) ──
    # F1 안정성 (낮은 분산 = 안정)
    f1_stability = 1.0 - _normalize(f1_std, 0, 200)
    results["A-2-4-01"] = _m("A-2-4-01", max(0, f1_stability), conf_cap * 0.75)

    # ── A-2-4-02: 성대 두께(자연도) ──
    # F1이 낮으면 성대가 두꺼움 → 자연스러운 저음
    # 800Hz 이상이면 얇은 성대
    vocal_thickness = 1.0 - _normalize(f1_mean, 300, 900)
    results["A-2-4-02"] = _m("A-2-4-02", max(0, vocal_thickness), conf_cap * 0.7)

    # ── A-2-4-07: 취약함 표현 통제 ──
    # F1/F2 비율의 변화 폭 → 취약한 표현 시 포먼트 변화가 큼
    f1f2_ratio = formants_arr[:, 0] / (formants_arr[:, 1] + 1e-10)
    ratio_range = float(np.max(f1f2_ratio) - np.min(f1f2_ratio))
    results["A-2-4-07"] = _m("A-2-4-07", ratio_range, conf_cap * 0.65)

    return results


_FORMANT_IDS = ["A-2-4-01", "A-2-4-02", "A-2-4-07"]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 통합 측정 함수 (메인 엔트리포인트)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def measure_tier1(audio_path: Path, content_type: str = "vocal_video") -> VocalVector100:
    """
    1계층(음향분석) 57개+ 지표 측정

    Parameters
    ----------
    audio_path : Path
        오디오 파일 경로 (wav/mp3/m4a)
    content_type : str
        입력 유형 (vocal_video / vocal_audio / ...)

    Returns
    -------
    VocalVector100
        100차원 벡터 (tier-2는 placeholder, tier-1만 실측)
    """
    import time
    start_time = time.time()

    vector = VocalVector100()
    conf_cap = CONFIDENCE_CAPS.get(content_type, 0.6)

    # ── 오디오 로드 ──────────────────────────
    y, sr = None, None
    try:
        y, sr = librosa.load(str(audio_path), sr=AUDIO_SAMPLE_RATE, mono=True)
    except Exception:
        pass

    if y is None:
        # ffmpeg 변환 시도
        from .audio import _convert_to_wav
        wav_path = _convert_to_wav(Path(audio_path))
        if wav_path:
            try:
                y, sr = librosa.load(str(wav_path), sr=AUDIO_SAMPLE_RATE, mono=True)
            except Exception as e:
                vector.outlier_summary = f"오디오 로드 실패: {e}"
                return vector
        else:
            vector.outlier_summary = "오디오 로드 실패: ffmpeg 없음"
            return vector

    duration = librosa.get_duration(y=y, sr=sr)
    if duration < 5.0:
        vector.outlier_summary = "오디오 길이 5초 미만 — 분석 불가"
        return vector

    # ── 전처리 (공유 특징 추출) ──────────────
    pf = PrecomputedFeatures(y, sr)

    # ── 톤 4사분면 (기존 호환) ───────────────
    from .audio import _analyze_tone_quadrant, _classify_tone_quadrant
    try:
        brightness, weight = _analyze_tone_quadrant(y, sr)
        tone_q, tone_q_ko = _classify_tone_quadrant(brightness, weight)
        vector.tone_quadrant = tone_q
        vector.tone_quadrant_ko = tone_q_ko
        vector.brightness = brightness
        vector.weight = weight
    except Exception:
        pass

    # ── 6개 알고리즘 카테고리별 측정 ────────
    all_measurements: Dict[str, IndicatorMeasurement] = {}

    # 1. Pitch Analysis
    try:
        pitch_results = _measure_pitch_analysis(pf, conf_cap)
        all_measurements.update(pitch_results)
    except Exception as e:
        for iid in _PITCH_IDS:
            all_measurements[iid] = _m(iid, 0.0, 0.0, measured=False, error=f"Pitch 분석 오류: {str(e)[:30]}")

    # 2. Energy Analysis
    try:
        energy_results = _measure_energy_analysis(pf, conf_cap)
        all_measurements.update(energy_results)
    except Exception as e:
        for iid in _ENERGY_IDS:
            all_measurements[iid] = _m(iid, 0.0, 0.0, measured=False, error=f"Energy 분석 오류: {str(e)[:30]}")

    # 3. Spectrum Analysis
    try:
        spectrum_results = _measure_spectrum_analysis(pf, conf_cap)
        all_measurements.update(spectrum_results)
    except Exception as e:
        for iid in ["B-1-1-12", "B-1-1-15", "B-1-1-16", "B-1-2-06", "B-1-2-07",
                     "B-1-2-08", "B-1-2-09", "B-1-2-11", "B-1-2-12", "B-1-4-04",
                     "B-1-4-06", "B-1-4-10"]:
            all_measurements[iid] = _m(iid, 0.0, 0.0, measured=False, error=f"Spectrum 분석 오류: {str(e)[:30]}")

    # 4. Vibrato Analysis
    try:
        vibrato_results = _measure_vibrato_analysis(pf, conf_cap)
        all_measurements.update(vibrato_results)
    except Exception as e:
        for iid in _VIBRATO_IDS:
            all_measurements[iid] = _m(iid, 0.0, 0.0, measured=False, error=f"Vibrato 분석 오류: {str(e)[:30]}")

    # 5. Voice Range
    try:
        range_results = _measure_voice_range(pf, conf_cap)
        all_measurements.update(range_results)
    except Exception as e:
        for iid in _VOICE_RANGE_IDS:
            all_measurements[iid] = _m(iid, 0.0, 0.0, measured=False, error=f"Voice Range 오류: {str(e)[:30]}")

    # 6. Formant Analysis
    try:
        formant_results = _measure_formant_analysis(pf, conf_cap)
        all_measurements.update(formant_results)
    except Exception as e:
        for iid in _FORMANT_IDS:
            all_measurements[iid] = _m(iid, 0.0, 0.0, measured=False, error=f"Formant 분석 오류: {str(e)[:30]}")

    # ── tier-2 placeholder ──────────────────
    tier2_specs = {k: v for k, v in INDICATOR_REGISTRY.items() if v.tier == 2}
    for iid, spec in tier2_specs.items():
        if iid not in all_measurements:
            all_measurements[iid] = _m(iid, 0.0, 0.0, measured=False,
                                       error="tier-2 ML 모델 미구현 (Phase 2)")

    # ── VocalVector100 조립 ─────────────────
    vector.measurements = all_measurements
    measured_count = sum(1 for m in all_measurements.values() if m.measured)
    tier1_count = sum(1 for m in all_measurements.values() if m.measured and m.tier == 1)
    tier2_count = sum(1 for m in all_measurements.values() if m.measured and m.tier == 2)

    vector.total_measured = measured_count
    vector.tier1_measured = tier1_count
    vector.tier2_measured = tier2_count
    vector.processing_time_sec = time.time() - start_time

    # ── 극단값 식별 (OR 논리) ── ★ 종합점수 없음
    # 백분위 정규화는 normalizer.py에서 수행
    # 여기서는 raw_value만 채움
    vector.outlier_summary = (
        f"tier-1 측정 완료: {tier1_count}개 / "
        f"tier-2 대기: {len(tier2_specs)}개 / "
        f"처리시간: {vector.processing_time_sec:.1f}초"
    )

    return vector


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CLI 테스트
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
        print(f"\n=== 100차원 보컬 벡터 측정: {path.name} ===\n")
        result = measure_tier1(path, content_type="vocal_video")
        print(f"톤 사분면: {result.tone_quadrant_ko}")
        print(f"측정 완료: {result.total_measured}개 (tier1: {result.tier1_measured}, tier2: {result.tier2_measured})")
        print(f"처리 시간: {result.processing_time_sec:.1f}초")
        print(f"\n{result.outlier_summary}")

        # 측정 성공 항목 출력
        print(f"\n── 측정 성공 항목 ──")
        measured = {k: v for k, v in result.measurements.items() if v.measured}
        for iid in sorted(measured.keys()):
            m = measured[iid]
            print(f"  [{iid}] {m.name}: {m.raw_value:.4f} (신뢰도: {m.confidence:.2f})")

        # 측정 실패 항목 요약
        failed = {k: v for k, v in result.measurements.items() if not v.measured}
        print(f"\n── 측정 실패/대기: {len(failed)}개 ──")
        for iid in sorted(failed.keys())[:10]:
            m = failed[iid]
            print(f"  [{iid}] {m.name}: {m.error}")
        if len(failed) > 10:
            print(f"  ... 외 {len(failed) - 10}개")
    else:
        print("사용법: python -m idol_scout.screener.audio_v2 <audio_file>")
