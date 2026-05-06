"""idol_screener/audio_analyzer.py — 오디오 기반 고유성 지표 3개 측정"""
import numpy as np
import subprocess
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Tuple
import librosa
from .config import (AUDIO_SAMPLE_RATE, MFCC_N_COEFFS, MFCC_HOP_LENGTH, MFCC_N_FFT,
    SEGMENT_DURATION, SEGMENT_HOP, CONFIDENCE_CAPS, TONE_QUADRANTS)

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
class VocalProfile:
    """보컬 세부 프로파일 — v2 보컬 해상도 극대화"""
    # 톤 4사분면
    tone_quadrant: str = "unknown"           # bright_light / warm_light / dark_heavy / bright_heavy
    tone_quadrant_ko: str = "미분류"
    brightness: float = 0.0                  # 0~1 (spectral centroid normalized)
    weight: float = 0.0                      # 0~1 (low-freq energy ratio)
    tone_confidence: float = 0.0

    # 성역대 구조
    chest_voice_ratio: float = 0.0           # 흉성 비율
    head_voice_ratio: float = 0.0            # 두성 비율
    mix_voice_ratio: float = 0.0             # 믹스 비율

    # 비브라토 특성
    vibrato_rate_hz: float = 0.0             # 비브라토 속도 (Hz)
    vibrato_depth: float = 0.0               # 비브라토 깊이 (semitones)
    vibrato_regularity: float = 0.0          # 비브라토 규칙성 0~1
    vibrato_presence: float = 0.0            # 비브라토 존재 비율

    # 다이내믹 레인지
    dynamic_range_db: float = 0.0            # dB 범위
    dynamic_score: float = 0.0               # 정규화 점수

    # 어택 클린도
    attack_sharpness: float = 0.0            # onset 선명도 0~1

    # 호흡성(기식감)
    breathiness: float = 0.0                 # 기식 정도 0~1 (HNR 기반)

    # 음역대 폭
    pitch_min_hz: float = 0.0
    pitch_max_hz: float = 0.0
    pitch_range_semitones: float = 0.0

    # 공명 패턴
    formant_1_hz: float = 0.0               # 제1포먼트
    formant_2_hz: float = 0.0               # 제2포먼트
    resonance_type: str = "unknown"          # chest_dominant / nasal / head_dominant / mixed

    # 측정 상태
    measured: bool = False
    notes: str = ""

@dataclass
class AudioAnalysisResult:
    """오디오 분석 통합 결과"""
    timbre: TimbreResult = field(default_factory=TimbreResult)
    rhythm: RhythmResult = field(default_factory=RhythmResult)
    vocal_profile: VocalProfile = field(default_factory=VocalProfile)
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
    # v2: 보컬 세부 프로파일 분석
    if result.has_vocals:
        result.vocal_profile = _analyze_vocal_profile(y, sr, conf_cap)
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

def _analyze_vocal_profile(y: np.ndarray, sr: int, conf_cap: float) -> VocalProfile:
    """보컬 세부 프로파일 분석 (v2 보컬 해상도 극대화)"""
    vp = VocalProfile()
    try:
        # 1. 톤 4사분면 (Tone Quadrant) 분석
        try:
            vp.brightness, vp.weight = _analyze_tone_quadrant(y, sr)
            vp.tone_quadrant, vp.tone_quadrant_ko = _classify_tone_quadrant(vp.brightness, vp.weight)
            vp.tone_confidence = conf_cap * 0.65
        except Exception as e:
            vp.notes += f"톤 분석 실패: {str(e)[:30]}. "

        # 2. 성역대 구조 (Vocal Register) 분석
        try:
            vp.chest_voice_ratio, vp.head_voice_ratio, vp.mix_voice_ratio = _analyze_vocal_register(y, sr)
        except Exception as e:
            vp.notes += f"성역대 분석 실패: {str(e)[:30]}. "

        # 3. 비브라토 특성 (Vibrato Character) 분석
        try:
            vp.vibrato_rate_hz, vp.vibrato_depth, vp.vibrato_regularity, vp.vibrato_presence = _analyze_vibrato(y, sr)
        except Exception as e:
            vp.notes += f"비브라토 분석 실패: {str(e)[:30]}. "

        # 4. 다이내믹 레인지 (Dynamic Range) 분석
        try:
            vp.dynamic_range_db, vp.dynamic_score = _analyze_dynamic_range(y, sr)
        except Exception as e:
            vp.notes += f"다이내믹 분석 실패: {str(e)[:30]}. "

        # 5. 어택 클린도 (Vocal Attack) 분석
        try:
            vp.attack_sharpness = _analyze_attack_sharpness(y, sr)
        except Exception as e:
            vp.notes += f"어택 분석 실패: {str(e)[:30]}. "

        # 6. 호흡성 (Breathiness) 분석
        try:
            vp.breathiness = _analyze_breathiness(y, sr)
        except Exception as e:
            vp.notes += f"호흡성 분석 실패: {str(e)[:30]}. "

        # 7. 음역대 폭 (Pitch Range) 분석
        try:
            vp.pitch_min_hz, vp.pitch_max_hz, vp.pitch_range_semitones = _analyze_pitch_range(y, sr)
        except Exception as e:
            vp.notes += f"음역대 분석 실패: {str(e)[:30]}. "

        # 8. 공명 패턴 (Resonance/Formants) 분석
        try:
            vp.formant_1_hz, vp.formant_2_hz, vp.resonance_type = _analyze_resonance(y, sr)
        except Exception as e:
            vp.notes += f"공명 분석 실패: {str(e)[:30]}. "

        vp.measured = True
        vp.notes += "(v2 보컬 해상도 극대화)"
    except Exception as e:
        vp.notes = f"보컬 프로파일 분석 실패: {str(e)[:50]}"

    return vp

def _analyze_tone_quadrant(y: np.ndarray, sr: int) -> Tuple[float, float]:
    """
    톤 4사분면 분석
    brightness: 0~1 (spectral centroid 정규화)
    weight: 0~1 (저주파 에너지 비율)
    """
    # HPSS로 하모닉 성분만 추출
    y_harmonic, _ = librosa.effects.hpss(y)

    # Spectral Centroid — 밝기 측정
    spectral_centroid = librosa.feature.spectral_centroid(y=y_harmonic, sr=sr)[0]
    mean_centroid = float(np.mean(spectral_centroid))

    # 정규화: 음성 대역 500~4000Hz를 0~1로 매핑
    brightness = _normalize(mean_centroid, 500.0, 4000.0)

    # 저주파 에너지 비율 — 무게감
    S = np.abs(librosa.stft(y_harmonic))
    freqs = librosa.fft_frequencies(sr=sr)
    low_freq_mask = freqs <= 500
    high_freq_energy = np.sum(S[~low_freq_mask] ** 2) + 1e-10
    low_freq_energy = np.sum(S[low_freq_mask] ** 2) + 1e-10
    weight = low_freq_energy / (low_freq_energy + high_freq_energy)

    return float(brightness), float(weight)

def _classify_tone_quadrant(brightness: float, weight: float) -> Tuple[str, str]:
    """톤 4사분면 분류"""
    if brightness > 0.5 and weight < 0.5:
        return "bright_light", "청량"
    elif brightness <= 0.5 and weight < 0.5:
        return "warm_light", "따뜻"
    elif brightness <= 0.5 and weight >= 0.5:
        return "dark_heavy", "묵직"
    else:  # brightness > 0.5 and weight >= 0.5
        return "bright_heavy", "건조"

def _analyze_vocal_register(y: np.ndarray, sr: int) -> Tuple[float, float, float]:
    """
    성역대 구조 분석
    chest_voice_ratio, head_voice_ratio, mix_voice_ratio
    """
    try:
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        chest_frames = np.sum(spectral_centroid < 800)
        mix_frames = np.sum((spectral_centroid >= 800) & (spectral_centroid <= 2500))
        head_frames = np.sum(spectral_centroid > 2500)
        total = len(spectral_centroid)

        chest_ratio = float(chest_frames / total) if total > 0 else 0.0
        mix_ratio = float(mix_frames / total) if total > 0 else 0.0
        head_ratio = float(head_frames / total) if total > 0 else 0.0

        return chest_ratio, head_ratio, mix_ratio
    except Exception:
        return 0.0, 0.0, 0.0

def _analyze_vibrato(y: np.ndarray, sr: int) -> Tuple[float, float, float, float]:
    """
    비브라토 특성 분석
    vibrato_rate_hz, vibrato_depth, vibrato_regularity, vibrato_presence
    """
    try:
        # Pitch tracking with librosa.pyin
        f0, voiced_flag, voiced_probs = librosa.pyin(y, fmin=50, fmax=400, sr=sr)

        # 유성음 부분만 추출
        voiced_f0 = f0[voiced_flag]
        if len(voiced_f0) < 20:
            return 0.0, 0.0, 0.0, 0.0

        # 비브라토는 f0 변조를 따라감
        # 간단한 자기상관을 통해 주기성 감지
        hop_length = 512
        time_step = hop_length / sr
        f0_hz = voiced_f0

        # 변화도 계산 (1차 미분)
        f0_diff = np.abs(np.diff(f0_hz))
        if len(f0_diff) < 10:
            return 0.0, 0.0, 0.0, 0.0

        # 자기상관으로 주기성 감지
        acf = np.correlate(f0_diff - np.mean(f0_diff), f0_diff - np.mean(f0_diff), mode='full')
        acf = acf[len(acf)//2:]
        acf = acf / (np.max(acf) + 1e-10)

        # 비브라토 대역: 3~10 프레임 (typical 4~7Hz)
        vibrato_presence = 0.0
        vibrato_rate_hz = 0.0
        vibrato_depth = 0.0
        vibrato_regularity = 0.0

        if len(acf) > 15:
            vibrato_band = acf[3:15]
            if np.max(vibrato_band) > 0.3:
                vibrato_idx = np.argmax(vibrato_band) + 3
                vibrato_rate_hz = float(sr / (hop_length * vibrato_idx))
                vibrato_presence = float(np.max(vibrato_band))
                vibrato_depth = float(np.std(f0_diff) / np.mean(f0_hz) * 12)  # semitones
                vibrato_regularity = float(np.max(vibrato_band))

        return vibrato_rate_hz, vibrato_depth, vibrato_regularity, vibrato_presence
    except Exception:
        return 0.0, 0.0, 0.0, 0.0

def _analyze_dynamic_range(y: np.ndarray, sr: int) -> Tuple[float, float]:
    """
    다이내믹 레인지 분석
    dynamic_range_db, dynamic_score (0~1 정규화)
    """
    try:
        # RMS 에너지 frame-by-frame
        frame_length = 2048
        hop_length = 512
        rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]

        # 침묵 제거 (threshold: mean RMS * 0.1)
        threshold = np.mean(rms) * 0.1
        rms_active = rms[rms > threshold]

        if len(rms_active) < 2:
            return 0.0, 0.0

        # dB 변환
        rms_db = 20 * np.log10(rms_active + 1e-10)
        dynamic_range = float(np.max(rms_db) - np.min(rms_db))

        # 정규화: 12dB ~ 48dB를 0~1로
        dynamic_score = _normalize(dynamic_range, 12.0, 48.0)

        return dynamic_range, dynamic_score
    except Exception:
        return 0.0, 0.0

def _analyze_attack_sharpness(y: np.ndarray, sr: int) -> float:
    """
    어택 클린도 분석 (onset strength)
    0~1 스케일
    """
    try:
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        attack_sharpness = float(np.mean(onset_env))
        # 정규화
        attack_sharpness = _normalize(attack_sharpness, 0.0, 0.1)
        return attack_sharpness
    except Exception:
        return 0.0

def _analyze_breathiness(y: np.ndarray, sr: int) -> float:
    """
    호흡성(기식감) 분석 (spectral flatness 기반)
    높은 flatness = 더 많은 기식
    0~1 스케일
    """
    try:
        y_harmonic, _ = librosa.effects.hpss(y)
        spectral_flatness = librosa.feature.spectral_flatness(y=y_harmonic)[0]
        mean_flatness = float(np.mean(spectral_flatness))

        # 정규화: 0.01~0.3을 0~1로
        breathiness = _normalize(mean_flatness, 0.01, 0.3)
        return breathiness
    except Exception:
        return 0.0

def _analyze_pitch_range(y: np.ndarray, sr: int) -> Tuple[float, float, float]:
    """
    음역대 폭 분석 (pitch range)
    pitch_min_hz, pitch_max_hz, pitch_range_semitones
    """
    try:
        # Pitch tracking with librosa.pyin
        f0, voiced_flag, _ = librosa.pyin(y, fmin=50, fmax=400, sr=sr)
        voiced_f0 = f0[voiced_flag]

        if len(voiced_f0) < 10:
            return 0.0, 0.0, 0.0

        pitch_min = float(np.min(voiced_f0))
        pitch_max = float(np.max(voiced_f0))

        # semitones = 12 * log2(f_max / f_min)
        if pitch_min > 0:
            pitch_range_semitones = float(12 * np.log2(pitch_max / pitch_min))
        else:
            pitch_range_semitones = 0.0

        return pitch_min, pitch_max, pitch_range_semitones
    except Exception:
        return 0.0, 0.0, 0.0

def _analyze_resonance(y: np.ndarray, sr: int) -> Tuple[float, float, str]:
    """
    공명 패턴 분석 (포먼트 특성)
    formant_1_hz, formant_2_hz, resonance_type
    """
    try:
        y_harmonic, _ = librosa.effects.hpss(y)

        # LPC를 이용한 포먼트 추정 (간단한 구현)
        # windowed frame에서 분석
        frame_length = 2048
        hop_length = 512

        formants_list = []
        for start in range(0, len(y_harmonic) - frame_length, hop_length):
            frame = y_harmonic[start:start + frame_length]
            if np.sum(np.abs(frame)) < 1e-6:
                continue

            try:
                # LPC coefficients (order 12)
                a = librosa.lpc(frame, order=12)
                # roots of LPC polynomial
                roots = np.roots(a)
                roots = roots[np.imag(roots) >= 0]

                if len(roots) > 0:
                    angles = np.angle(roots)
                    freqs = angles * sr / (2 * np.pi)
                    freqs = freqs[freqs > 0]
                    if len(freqs) >= 2:
                        formants_list.append(sorted(freqs)[:2])
            except Exception:
                continue

        if not formants_list:
            return 0.0, 0.0, "unknown"

        # 평균 포먼트
        formants_array = np.array(formants_list)
        formant_1 = float(np.mean(formants_array[:, 0]))
        formant_2 = float(np.mean(formants_array[:, 1]) if formants_array.shape[1] > 1 else 0.0)

        # 공명 타입 분류 (간단한 휴리스틱)
        if formant_1 < 600:
            resonance_type = "chest_dominant"
        elif formant_1 < 800:
            resonance_type = "nasal"
        elif formant_1 < 1000:
            resonance_type = "mixed"
        else:
            resonance_type = "head_dominant"

        return formant_1, formant_2, resonance_type
    except Exception:
        return 0.0, 0.0, "unknown"

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
