"""idol_screener/audio_analyzer.py — 오디오 기반 고유성 지표 3개 측정"""
import numpy as np
import subprocess
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Tuple
import librosa
from .config import (AUDIO_SAMPLE_RATE, MFCC_N_COEFFS, MFCC_HOP_LENGTH, MFCC_N_FFT,
    SEGMENT_DURATION, SEGMENT_HOP, CONFIDENCE_CAPS)

# imageio-ffmpeg에서 ffmpeg 경로를 가져와서 PATH에 추가
try:
    import imageio_ffmpeg
    _ffmpeg_dir = str(Path(imageio_ffmpeg.get_ffmpeg_exe()).parent)
    if _ffmpeg_dir not in os.environ.get("PATH", ""):
        os.environ["PATH"] = _ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
except ImportError:
    pass

@dataclass
class TimbreResult:
    """음색 분석 결과"""
    mfcc_mean: np.ndarray = field(default_factory=lambda: np.zeros(13))
    mfcc_std: np.ndarray = field(default_factory=lambda: np.zeros(13))
    spectral_centroid_mean: float = 0.0
    spectral_centroid_std: float = 0.0
    spectral_bandwidth_mean: float = 0.0
    spectral_flatness_mean: float = 0.0
    spectral_contrast_mean: float = 0.0
    harmonic_ratio: float = 0.0
    zero_crossing_rate: float = 0.0
    uniqueness_score: float = 0.0
    identifiability_score: float = 0.0
    uniqueness_confidence: float = 0.0
    identifiability_confidence: float = 0.0
    notes: str = ""

@dataclass
class RhythmResult:
    """리듬 인격 분석 결과"""
    tempo: float = 0.0
    mean_onset_offset_ms: float = 0.0
    std_onset_offset_ms: float = 0.0
    onset_count: int = 0
    beat_count: int = 0
    personality: str = "undetermined"
    consistency: float = 0.0
    rhythm_score: float = 0.0
    rhythm_confidence: float = 0.0
    notes: str = ""

@dataclass
class AudioAnalysisResult:
    """오디오 분석 통합 결과"""
    timbre: TimbreResult = field(default_factory=TimbreResult)
    rhythm: RhythmResult = field(default_factory=RhythmResult)
    duration: float = 0.0
    sample_rate: int = AUDIO_SAMPLE_RATE
    has_vocals: bool = False
    error: str = ""

def _convert_to_wav(audio_path: Path) -> Optional[Path]:
    """m4a 등 librosa가 직접 읽지 못하는 포맷을 wav로 변환"""
    wav_path = audio_path.with_suffix(".conv.wav")
    if wav_path.exists():
        return wav_path

    # 방법 1: imageio-ffmpeg 사용
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        cmd = [ffmpeg_exe, "-y", "-i", str(audio_path), "-ar", str(AUDIO_SAMPLE_RATE),
               "-ac", "1", "-f", "wav", str(wav_path)]
        r = subprocess.run(cmd, capture_output=True, timeout=60)
        if r.returncode == 0 and wav_path.exists():
            return wav_path
    except (ImportError, Exception):
        pass

    # 방법 2: 시스템 ffmpeg 사용
    try:
        cmd = ["ffmpeg", "-y", "-i", str(audio_path), "-ar", str(AUDIO_SAMPLE_RATE),
               "-ac", "1", "-f", "wav", str(wav_path)]
        r = subprocess.run(cmd, capture_output=True, timeout=60)
        if r.returncode == 0 and wav_path.exists():
            return wav_path
    except Exception:
        pass

    return None


def analyze_audio(audio_path: Path, content_type: str = "vocal_video") -> AudioAnalysisResult:
    result = AudioAnalysisResult()

    # 1차 시도: librosa 직접 로드
    y, sr = None, None
    try:
        y, sr = librosa.load(str(audio_path), sr=AUDIO_SAMPLE_RATE, mono=True)
    except Exception:
        pass

    # 2차 시도: ffmpeg로 wav 변환 후 로드
    if y is None:
        wav_path = _convert_to_wav(Path(audio_path))
        if wav_path:
            try:
                y, sr = librosa.load(str(wav_path), sr=AUDIO_SAMPLE_RATE, mono=True)
            except Exception as e2:
                result.error = f"오디오 로드 실패 (변환 후에도): {e2}"
                return result
        else:
            result.error = "오디오 로드 실패: ffmpeg 없음. pip install imageio-ffmpeg 실행 필요"
            return result
    result.duration = librosa.get_duration(y=y, sr=sr)
    result.sample_rate = sr
    if result.duration < 5.0:
        result.error = "오디오 길이 5초 미만 — 분석 불가"
        return result
    result.has_vocals = _check_vocals_present(y, sr)
    conf_cap = CONFIDENCE_CAPS.get(content_type, 0.6)
    result.timbre = _analyze_timbre(y, sr, conf_cap)
    result.rhythm = _analyze_rhythm(y, sr, conf_cap, content_type)
    return result

def _analyze_timbre(y: np.ndarray, sr: int, conf_cap: float) -> TimbreResult:
    tr = TimbreResult()
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=MFCC_N_COEFFS, hop_length=MFCC_HOP_LENGTH, n_fft=MFCC_N_FFT)
    tr.mfcc_mean = np.mean(mfcc, axis=1)
    tr.mfcc_std = np.std(mfcc, axis=1)
    spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    tr.spectral_centroid_mean = float(np.mean(spectral_centroid))
    tr.spectral_centroid_std = float(np.std(spectral_centroid))
    spectral_bw = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
    tr.spectral_bandwidth_mean = float(np.mean(spectral_bw))
    spectral_flat = librosa.feature.spectral_flatness(y=y)[0]
    tr.spectral_flatness_mean = float(np.mean(spectral_flat))
    spectral_contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
    tr.spectral_contrast_mean = float(np.mean(spectral_contrast))
    harmonic, percussive = librosa.effects.hpss(y)
    h_energy = np.sum(harmonic ** 2)
    total_energy = np.sum(y ** 2)
    tr.harmonic_ratio = float(h_energy / (total_energy + 1e-10))
    zcr = librosa.feature.zero_crossing_rate(y)[0]
    tr.zero_crossing_rate = float(np.mean(zcr))
    mfcc_var_score = _normalize(float(np.mean(tr.mfcc_std)), 5.0, 25.0)
    spectral_flat_score = _normalize_extreme(tr.spectral_flatness_mean, 0.01, 0.05, 0.3)
    harmonic_score = _normalize_extreme(tr.harmonic_ratio, 0.3, 0.6, 0.95)
    contrast_score = _normalize(tr.spectral_contrast_mean, 10.0, 30.0)
    centroid_var_score = _normalize(tr.spectral_centroid_std, 200.0, 1500.0)
    raw_uniqueness = _geometric_mean([mfcc_var_score, spectral_flat_score, harmonic_score, contrast_score, centroid_var_score])
    tr.uniqueness_score = min(1.0, raw_uniqueness)
    tr.uniqueness_confidence = conf_cap * _data_quality_factor(tr)
    segment_mfccs = _compute_segment_mfccs(y, sr)
    if len(segment_mfccs) >= 3:
        similarities = []
        for i in range(len(segment_mfccs)):
            for j in range(i + 1, len(segment_mfccs)):
                sim = _cosine_similarity(segment_mfccs[i], segment_mfccs[j])
                similarities.append(sim)
        mean_similarity = float(np.mean(similarities))
        tr.identifiability_score = _normalize(mean_similarity, 0.7, 0.98)
        tr.identifiability_confidence = conf_cap * 0.9
    else:
        tr.identifiability_score = 0.0
        tr.identifiability_confidence = 0.0
        tr.notes += "세그먼트 부족(3개 미만)으로 판별력 미산출. "
    return tr

def _analyze_rhythm(y: np.ndarray, sr: int, conf_cap: float, content_type: str) -> RhythmResult:
    rr = RhythmResult()
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    if isinstance(tempo, np.ndarray):
        tempo = float(tempo[0]) if len(tempo) > 0 else 0.0
    rr.tempo = float(tempo)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    rr.beat_count = len(beat_times)
    if rr.beat_count < 4:
        rr.notes = "비트 감지 부족(4개 미만). 리듬 인격 미산출."
        return rr
    if content_type == "dance_video":
        _, y_perc = librosa.effects.hpss(y)
        onset_frames = librosa.onset.onset_detect(y=y_perc, sr=sr, backtrack=False)
    else:
        onset_frames = librosa.onset.onset_detect(y=y, sr=sr, backtrack=False)
    onset_times = librosa.frames_to_time(onset_frames, sr=sr)
    rr.onset_count = len(onset_times)
    if rr.onset_count < 8:
        rr.notes = "Onset 감지 부족(8개 미만). 리듬 인격 미산출."
        return rr
    offsets_ms = _compute_onset_beat_offsets(onset_times, beat_times)
    if len(offsets_ms) < 5:
        rr.notes = "유효 오프셋 부족. 리듬 인격 미산출."
        return rr
    rr.mean_onset_offset_ms = float(np.mean(offsets_ms))
    rr.std_onset_offset_ms = float(np.std(offsets_ms))
    AHEAD_THRESHOLD = -10.0
    BEHIND_THRESHOLD = 10.0
    if rr.mean_onset_offset_ms < AHEAD_THRESHOLD:
        rr.personality = "ahead"
    elif rr.mean_onset_offset_ms > BEHIND_THRESHOLD:
        rr.personality = "behind"
    else:
        rr.personality = "on_beat"
    rr.consistency = 1.0 - _normalize(rr.std_onset_offset_ms, 5.0, 50.0)
    offset_magnitude = min(abs(rr.mean_onset_offset_ms) / 40.0, 1.0)
    rr.rhythm_score = 0.6 * rr.consistency + 0.4 * offset_magnitude
    rr.rhythm_score = min(1.0, rr.rhythm_score)
    if content_type == "dance_video":
        rr.rhythm_confidence = conf_cap * 0.9
    else:
        rr.rhythm_confidence = conf_cap * 0.6
    return rr

def _compute_onset_beat_offsets(onset_times: np.ndarray, beat_times: np.ndarray) -> np.ndarray:
    offsets = []
    for onset in onset_times:
        diffs = onset - beat_times
        nearest_idx = np.argmin(np.abs(diffs))
        offset_ms = float(diffs[nearest_idx] * 1000)
        if abs(offset_ms) < 300:
            offsets.append(offset_ms)
    return np.array(offsets)

def _compute_segment_mfccs(y: np.ndarray, sr: int) -> list:
    segment_samples = int(SEGMENT_DURATION * sr)
    hop_samples = int(SEGMENT_HOP * sr)
    segments = []
    start = 0
    while start + segment_samples <= len(y):
        seg = y[start:start + segment_samples]
        if np.sqrt(np.mean(seg ** 2)) > 0.01:
            mfcc = librosa.feature.mfcc(y=seg, sr=sr, n_mfcc=MFCC_N_COEFFS, hop_length=MFCC_HOP_LENGTH, n_fft=MFCC_N_FFT)
            segments.append(np.mean(mfcc, axis=1))
        start += hop_samples
    return segments

def _check_vocals_present(y: np.ndarray, sr: int) -> bool:
    """
    오디오에 사람 목소리가 실제로 포함되어 있는지 판별.
    HPSS로 하모닉(음성) 성분을 분리한 뒤,
    음성 대역(300~3400Hz) 에너지 비율로 판단.
    배경 음악(MR)만 있는 댄스 영상을 걸러내기 위함.
    """
    rms = np.sqrt(np.mean(y ** 2))
    if rms < 0.005:
        return False

    # HPSS로 하모닉(보컬 포함) vs 퍼커시브(비트) 분리
    y_harmonic, y_percussive = librosa.effects.hpss(y)

    # 하모닉 성분에서 음성 대역(300~3400Hz)의 에너지 비율 측정
    S_harm = np.abs(librosa.stft(y_harmonic))
    freqs = librosa.fft_frequencies(sr=sr)

    # 음성 대역 마스크
    voice_mask = (freqs >= 300) & (freqs <= 3400)
    total_energy = np.sum(S_harm ** 2) + 1e-10
    voice_energy = np.sum(S_harm[voice_mask] ** 2)
    voice_ratio = voice_energy / total_energy

    # 하모닉 대 퍼커시브 에너지 비율
    harm_energy = np.sum(y_harmonic ** 2) + 1e-10
    perc_energy = np.sum(y_percussive ** 2) + 1e-10
    hp_ratio = harm_energy / (harm_energy + perc_energy)

    # 스펙트럼 평탄도 — 사람 목소리는 배음 구조가 있어 평탄도가 낮음
    flatness = librosa.feature.spectral_flatness(y=y_harmonic)[0]
    mean_flatness = float(np.mean(flatness))

    # 판정 기준:
    # 1) 음성 대역 에너지가 전체의 25% 이상
    # 2) 하모닉 비율이 40% 이상 (목소리는 하모닉이 강함)
    # 3) 스펙트럼 평탄도가 0.15 미만 (목소리는 배음 패턴이 뚜렷)
    # 3가지 중 2가지 이상 충족해야 보컬 있음으로 판정
    checks_passed = 0
    if voice_ratio >= 0.25:
        checks_passed += 1
    if hp_ratio >= 0.40:
        checks_passed += 1
    if mean_flatness < 0.15:
        checks_passed += 1

    return checks_passed >= 2

def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    dot = np.dot(a, b)
    norm = np.linalg.norm(a) * np.linalg.norm(b)
    return float(dot / (norm + 1e-10))

def _normalize(value: float, low: float, high: float) -> float:
    if high <= low:
        return 0.5
    return max(0.0, min(1.0, (value - low) / (high - low)))

def _normalize_extreme(value: float, low: float, typical: float, high: float) -> float:
    dist_from_typical = abs(value - typical)
    max_dist = max(abs(typical - low), abs(high - typical))
    return min(1.0, dist_from_typical / (max_dist + 1e-10))

def _geometric_mean(scores: list) -> float:
    valid = [max(0.01, s) for s in scores if s > 0]
    if not valid:
        return 0.0
    product = 1.0
    for s in valid:
        product *= s
    return product ** (1 / len(valid))

def _data_quality_factor(tr: TimbreResult) -> float:
    factors = []
    if np.any(tr.mfcc_mean != 0):
        factors.append(0.9)
    else:
        factors.append(0.1)
    if tr.spectral_centroid_mean > 0:
        factors.append(0.9)
    else:
        factors.append(0.3)
    return float(np.mean(factors))

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
        result = analyze_audio(path, content_type="vocal_video")
        print(f"\n=== 오디오 분석 결과: {path.name} ===")
        print(f"길이: {result.duration:.1f}초")
        print(f"보컬 존재: {result.has_vocals}")
        print(f"\n[음색 고유성]  점수={result.timbre.uniqueness_score:.3f}  신뢰도={result.timbre.uniqueness_confidence:.3f}")
        print(f"[음색 판별력]  점수={result.timbre.identifiability_score:.3f}  신뢰도={result.timbre.identifiability_confidence:.3f}")
        print(f"\n[리듬 인격]    유형={result.rhythm.personality}  점수={result.rhythm.rhythm_score:.3f}  신뢰도={result.rhythm.rhythm_confidence:.3f}")
        print(f"  BPM={result.rhythm.tempo:.1f}  오프셋={result.rhythm.mean_onset_offset_ms:+.1f}ms  σ={result.rhythm.std_onset_offset_ms:.1f}ms")
        if result.error:
            print(f"\n오류: {result.error}")
