"""
audio_extractor_pro.py — 풍부 통합 오디오 분석 모듈 (v2.3 PoC)
=============================================================

목적:
    엑셀 분석에서 검증된 K-POP 음성 분석용 AI 오픈소스 8종+ 통합.
    각 도구가 측정하는 영역이 달라 종합 시 풍부한 보컬 프로파일 생성.
    PoC 단계라 라이선스 부담 없이 모두 통합.

통합 도구:
    1. librosa (ISC)         — 스펙트럼·다이내믹 (기본)
    2. Parselmouth (GPL 안전) — 포먼트·HNR·Jitter·Shimmer
    3. Resemblyzer (Apache)   — 256-dim 화자 임베딩
    4. CREPE (MIT)            — 정밀 F0 (5센트)
    5. openSMILE (BSD)        — eGeMAPS 88 임상 특징
    6. Essentia (AGPL)        — 음향·리듬·톤 (400+ 특징)
    7. Demucs (MIT)           — 보컬 분리 (선택)
    8. HuBERT (MIT)           — transformers 음색 임베딩
    9. Silero-VAD (MIT)       — 음성 활성 감지
    10. SpeechBrain (Apache)  — 감정 인식 + ECAPA 화자 식별
    11. BasicPitch (Apache)   — 다중 음정 (멜로디 라인)

설계:
    - 각 추출 함수는 graceful fallback (try/except)
    - 한 도구 실패해도 다른 도구 결과로 진행
    - feature dict는 prefix로 도구별 그룹 (예: crepe_*, smile_*)

작성: 2026-05-13
"""
from __future__ import annotations

import warnings
warnings.filterwarnings("ignore")

from io import BytesIO
from pathlib import Path
from typing import Dict, Optional

import numpy as np


# ============================================================
# 캐시된 모델 (한 번만 로드)
# ============================================================
_CACHE = {}


def _safe_call(fn_name, fn, *args, **kwargs) -> dict:
    """모듈 호출 안전 래퍼 — 실패 시 빈 dict 반환."""
    try:
        result = fn(*args, **kwargs)
        return result if isinstance(result, dict) else {}
    except ImportError as e:
        return {f"_error_{fn_name}": f"ImportError: {e.name}"}
    except Exception as e:
        return {f"_error_{fn_name}": f"{type(e).__name__}: {str(e)[:100]}"}


# ============================================================
# 1. librosa — 기본 스펙트럼/다이내믹
# ============================================================

def _extract_librosa(audio_bytes: bytes, sr: int = 22050) -> dict:
    import librosa
    y, sr_loaded = librosa.load(BytesIO(audio_bytes), sr=sr, mono=True, duration=90.0)
    y, _ = librosa.effects.trim(y, top_db=25)
    if len(y) < sr_loaded:
        raise ValueError("음원이 너무 짧습니다")

    # HPSS 분리
    y_harm, y_perc = librosa.effects.hpss(y, margin=3.0)

    feats = {}
    feats["librosa_spectral_centroid_mean_hz"] = float(np.mean(librosa.feature.spectral_centroid(y=y_harm, sr=sr_loaded)[0]))
    feats["librosa_spectral_centroid_std_hz"] = float(np.std(librosa.feature.spectral_centroid(y=y_harm, sr=sr_loaded)[0]))
    feats["librosa_spectral_rolloff_85_hz"] = float(np.mean(librosa.feature.spectral_rolloff(y=y_harm, sr=sr_loaded, roll_percent=0.85)[0]))
    feats["librosa_spectral_bandwidth_mean"] = float(np.mean(librosa.feature.spectral_bandwidth(y=y_harm, sr=sr_loaded)[0]))
    feats["librosa_spectral_contrast_mean"] = float(np.mean(librosa.feature.spectral_contrast(y=y_harm, sr=sr_loaded)))
    feats["librosa_spectral_flatness_mean"] = float(np.mean(librosa.feature.spectral_flatness(y=y_harm)[0]))
    feats["librosa_zcr_mean"] = float(np.mean(librosa.feature.zero_crossing_rate(y=y_harm)[0]))

    # MFCC 13개
    mfcc = librosa.feature.mfcc(y=y_harm, sr=sr_loaded, n_mfcc=13)
    for i in range(13):
        feats[f"librosa_mfcc_{i+1}_mean"] = float(np.mean(mfcc[i]))
        feats[f"librosa_mfcc_{i+1}_std"] = float(np.std(mfcc[i]))

    # RMS/다이내믹
    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
    rms_db = 20 * np.log10(rms + 1e-8)
    feats["librosa_rms_mean_db"] = float(np.mean(rms_db))
    feats["librosa_rms_std_db"] = float(np.std(rms_db))
    feats["librosa_dynamic_range_db"] = float(np.percentile(rms_db, 95) - np.percentile(rms_db, 5))

    # Onset
    onset = librosa.onset.onset_strength(y=y, sr=sr_loaded)
    feats["librosa_onset_mean"] = float(np.mean(onset))
    feats["librosa_onset_std"] = float(np.std(onset))

    # Tempo & beat
    try:
        tempo, beats = librosa.beat.beat_track(y=y_perc, sr=sr_loaded)
        feats["librosa_tempo_bpm"] = float(tempo) if not np.isnan(tempo) else 0.0
        feats["librosa_beat_count"] = int(len(beats))
    except Exception:
        feats["librosa_tempo_bpm"] = 0.0
        feats["librosa_beat_count"] = 0

    # Tonal features
    try:
        chroma = librosa.feature.chroma_stft(y=y_harm, sr=sr_loaded)
        feats["librosa_chroma_mean"] = float(np.mean(chroma))
        feats["librosa_chroma_std"] = float(np.std(chroma))
        tonnetz = librosa.feature.tonnetz(y=y_harm, sr=sr_loaded)
        feats["librosa_tonnetz_mean"] = float(np.mean(tonnetz))
    except Exception:
        pass

    return feats


# ============================================================
# 2. Parselmouth — 정밀 음성 분석 (포먼트·HNR·Jitter·Shimmer)
# ============================================================

def _extract_parselmouth(audio_bytes: bytes) -> dict:
    import parselmouth
    from parselmouth.praat import call
    import soundfile as sf

    data, sr = sf.read(BytesIO(audio_bytes))
    if data.ndim > 1:
        data = data.mean(axis=1)
    sound = parselmouth.Sound(data.astype(np.float64), sampling_frequency=sr)

    feats = {}

    # 포먼트 F1~F4 정밀 측정
    try:
        formants = sound.to_formant_burg(max_number_of_formants=5, maximum_formant=5500)
        time_points = np.linspace(0.1, sound.duration - 0.1, 30)
        for f_num in [1, 2, 3, 4]:
            vals = []
            for t in time_points:
                v = call(formants, "Get value at time", f_num, t, "Hertz", "Linear")
                if not np.isnan(v):
                    vals.append(v)
            if vals:
                feats[f"praat_formant_{f_num}_mean_hz"] = float(np.median(vals))
                feats[f"praat_formant_{f_num}_std_hz"] = float(np.std(vals))
    except Exception:
        pass

    # HNR
    try:
        harmonicity = sound.to_harmonicity_cc()
        hnr = call(harmonicity, "Get mean", 0, 0)
        if not np.isnan(hnr):
            feats["praat_hnr_db"] = float(np.clip(hnr, 0, 40))
    except Exception:
        pass

    # Jitter / Shimmer
    try:
        pp = call(sound, "To PointProcess (periodic, cc)", 75, 600)
        feats["praat_jitter_local"] = float(call(pp, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3))
        feats["praat_jitter_rap"] = float(call(pp, "Get jitter (rap)", 0, 0, 0.0001, 0.02, 1.3))
        feats["praat_shimmer_local"] = float(call([sound, pp], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6))
        feats["praat_shimmer_apq11"] = float(call([sound, pp], "Get shimmer (apq11)", 0, 0, 0.0001, 0.02, 1.3, 1.6))
    except Exception:
        pass

    # F0 (Pitch)
    try:
        pitch = sound.to_pitch(time_step=0.01, pitch_floor=75, pitch_ceiling=600)
        f0_values = pitch.selected_array['frequency']
        f0_values = f0_values[f0_values > 0]
        if len(f0_values) > 0:
            feats["praat_f0_mean_hz"] = float(np.mean(f0_values))
            feats["praat_f0_std_hz"] = float(np.std(f0_values))
            feats["praat_f0_min_hz"] = float(np.min(f0_values))
            feats["praat_f0_max_hz"] = float(np.max(f0_values))
            feats["praat_f0_range_semitones"] = float(12 * np.log2(np.max(f0_values) / np.min(f0_values)))
    except Exception:
        pass

    return feats


# ============================================================
# 3. CREPE — 정밀 F0 (딥러닝 기반)
# ============================================================

def _extract_crepe(audio_bytes: bytes) -> dict:
    import crepe
    import soundfile as sf

    data, sr = sf.read(BytesIO(audio_bytes))
    if data.ndim > 1:
        data = data.mean(axis=1)
    if sr != 16000:
        import librosa
        data = librosa.resample(data.astype(np.float32), orig_sr=sr, target_sr=16000)
        sr = 16000

    # CREPE 모델 캐시
    time, frequency, confidence, _ = crepe.predict(
        data, sr,
        model_capacity="tiny",  # tiny=빠름, small/medium/large=정확
        viterbi=True,
        step_size=20,
        verbose=0,
    )

    # 고신뢰 프레임만
    mask = confidence > 0.5
    f0_clean = frequency[mask]
    feats = {}
    if len(f0_clean) > 0:
        feats["crepe_f0_mean_hz"] = float(np.mean(f0_clean))
        feats["crepe_f0_median_hz"] = float(np.median(f0_clean))
        feats["crepe_f0_std_hz"] = float(np.std(f0_clean))
        feats["crepe_f0_min_hz"] = float(np.min(f0_clean))
        feats["crepe_f0_max_hz"] = float(np.max(f0_clean))
        feats["crepe_f0_range_st"] = float(12 * np.log2(np.max(f0_clean) / max(np.min(f0_clean), 1)))
        feats["crepe_confidence_mean"] = float(np.mean(confidence))
        feats["crepe_voiced_ratio"] = float(np.sum(mask) / len(confidence))

        # 비브라토 분석 (F0 변동성)
        f0_diff = np.abs(np.diff(f0_clean))
        feats["crepe_vibrato_extent_hz"] = float(np.std(f0_diff))
    return feats


# ============================================================
# 4. openSMILE — eGeMAPS 88 임상 표준 특징
# ============================================================

def _extract_opensmile(audio_bytes: bytes) -> dict:
    import opensmile
    import soundfile as sf

    if "opensmile_egemaps" not in _CACHE:
        _CACHE["opensmile_egemaps"] = opensmile.Smile(
            feature_set=opensmile.FeatureSet.eGeMAPSv02,
            feature_level=opensmile.FeatureLevel.Functionals,
        )
    smile = _CACHE["opensmile_egemaps"]

    data, sr = sf.read(BytesIO(audio_bytes))
    if data.ndim > 1:
        data = data.mean(axis=1)

    df = smile.process_signal(data.astype(np.float64), sr)
    row = df.iloc[0].to_dict()
    # 키 이름 단순화
    return {f"smile_{k}": float(v) for k, v in row.items() if isinstance(v, (int, float, np.floating))}


# ============================================================
# 5. Essentia — 풍부 음향/리듬/톤 분석
# ============================================================

def _extract_essentia(audio_bytes: bytes) -> dict:
    import essentia.standard as es
    import tempfile

    # Essentia는 파일에서 로드해야 함
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        import soundfile as sf
        data, sr = sf.read(BytesIO(audio_bytes))
        if data.ndim > 1:
            data = data.mean(axis=1)
        sf.write(tmp.name, data, sr)
        audio_path = tmp.name

    try:
        loader = es.MonoLoader(filename=audio_path, sampleRate=44100)
        audio = loader()

        feats = {}

        # MusicExtractor — 종합 분석
        try:
            extractor = es.MusicExtractor(
                lowlevelStats=['mean', 'stdev'],
                rhythmStats=['mean'],
                tonalStats=['mean'],
            )
            pool = extractor(audio_path)[0]

            # 핵심 특징만 추출
            keys_of_interest = [
                'lowlevel.average_loudness',
                'lowlevel.dynamic_complexity',
                'lowlevel.spectral_complexity.mean',
                'lowlevel.spectral_energy.mean',
                'lowlevel.spectral_entropy.mean',
                'rhythm.bpm',
                'rhythm.beats_count',
                'rhythm.danceability',
                'tonal.key_strength',
                'tonal.tuning_frequency',
            ]
            for k in keys_of_interest:
                try:
                    v = pool[k]
                    if isinstance(v, (int, float, np.floating)):
                        feats[f"essentia_{k.replace('.', '_')}"] = float(v)
                except Exception:
                    pass
        except Exception:
            # MusicExtractor 실패 시 개별 알고리즘 사용
            try:
                rhythm = es.RhythmExtractor2013(method="multifeature")
                bpm, _, _, _, _ = rhythm(audio)
                feats["essentia_rhythm_bpm"] = float(bpm)
            except Exception:
                pass

            try:
                loudness = es.LoudnessEBUR128()
                _, _, integrated, _ = loudness(es.StereoMuxer()(audio, audio))
                feats["essentia_loudness_lufs"] = float(integrated)
            except Exception:
                pass

        return feats
    finally:
        Path(audio_path).unlink(missing_ok=True)


# ============================================================
# 6. Demucs — 보컬 분리 (전처리용)
# ============================================================

def separate_vocal_demucs(audio_bytes: bytes) -> Optional[np.ndarray]:
    """Demucs로 보컬 트랙 분리. CPU 추론으로 30초~1분 소요. 실패 시 None."""
    try:
        import demucs.api
        import soundfile as sf

        if "demucs" not in _CACHE:
            _CACHE["demucs"] = demucs.api.Separator(model="htdemucs", device="cpu")
        separator = _CACHE["demucs"]

        data, sr = sf.read(BytesIO(audio_bytes))
        if data.ndim == 1:
            data = np.stack([data, data])
        import torch
        tensor = torch.from_numpy(data.T.astype(np.float32))

        _, sources = separator.separate_tensor(tensor, sr)
        if "vocals" in sources:
            vocals = sources["vocals"].cpu().numpy().T.mean(axis=1)
            return vocals.astype(np.float32)
    except Exception:
        pass
    return None


# ============================================================
# 7. HuBERT — transformers 음색 임베딩
# ============================================================

def _extract_hubert(audio_bytes: bytes) -> dict:
    from transformers import HubertModel, Wav2Vec2FeatureExtractor
    import torch
    import soundfile as sf

    if "hubert" not in _CACHE:
        model_name = "facebook/hubert-base-ls960"
        _CACHE["hubert_extractor"] = Wav2Vec2FeatureExtractor.from_pretrained(model_name)
        _CACHE["hubert"] = HubertModel.from_pretrained(model_name).eval()
    fe = _CACHE["hubert_extractor"]
    model = _CACHE["hubert"]

    data, sr = sf.read(BytesIO(audio_bytes))
    if data.ndim > 1:
        data = data.mean(axis=1)
    if sr != 16000:
        import librosa
        data = librosa.resample(data.astype(np.float32), orig_sr=sr, target_sr=16000)

    inputs = fe(data, sampling_rate=16000, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)
    # 마지막 hidden state 평균 → 768-dim 임베딩
    embedding = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()

    feats = {}
    feats["hubert_embedding"] = embedding.tolist()  # 768-dim
    feats["hubert_embedding_norm"] = float(np.linalg.norm(embedding))
    feats["hubert_embedding_mean"] = float(np.mean(embedding))
    feats["hubert_embedding_std"] = float(np.std(embedding))
    return feats


# ============================================================
# 8. Silero-VAD — 음성 활성 감지
# ============================================================

def _extract_silero_vad(audio_bytes: bytes) -> dict:
    import torch
    import soundfile as sf

    if "silero_vad" not in _CACHE:
        model, utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False,
            trust_repo=True,
            onnx=False,
        )
        _CACHE["silero_vad"] = (model, utils)
    model, utils = _CACHE["silero_vad"]
    (get_speech_timestamps, _, read_audio, _, _) = utils

    data, sr = sf.read(BytesIO(audio_bytes))
    if data.ndim > 1:
        data = data.mean(axis=1)
    if sr != 16000:
        import librosa
        data = librosa.resample(data.astype(np.float32), orig_sr=sr, target_sr=16000)

    tensor = torch.from_numpy(data.astype(np.float32))
    timestamps = get_speech_timestamps(tensor, model, sampling_rate=16000)

    feats = {}
    feats["silero_speech_segments"] = len(timestamps)
    if timestamps:
        total_speech = sum(t['end'] - t['start'] for t in timestamps) / 16000  # 초
        total_audio = len(data) / 16000
        feats["silero_speech_ratio"] = float(total_speech / total_audio)
        feats["silero_speech_duration_sec"] = float(total_speech)
    else:
        feats["silero_speech_ratio"] = 0.0
        feats["silero_speech_duration_sec"] = 0.0
    return feats


# ============================================================
# 9. SpeechBrain — 감정 인식 + ECAPA 화자 임베딩
# ============================================================

def _extract_speechbrain_emotion(audio_bytes: bytes) -> dict:
    from speechbrain.inference.interfaces import foreign_class
    import soundfile as sf
    import torch

    if "sb_emotion" not in _CACHE:
        _CACHE["sb_emotion"] = foreign_class(
            source="speechbrain/emotion-recognition-wav2vec2-IEMOCAP",
            pymodule_file="custom_interface.py",
            classname="CustomEncoderWav2vec2Classifier",
            savedir="~/.cache/sb_emotion",
        )
    classifier = _CACHE["sb_emotion"]

    data, sr = sf.read(BytesIO(audio_bytes))
    if data.ndim > 1:
        data = data.mean(axis=1)
    if sr != 16000:
        import librosa
        data = librosa.resample(data.astype(np.float32), orig_sr=sr, target_sr=16000)

    # 최대 10초만 (메모리 절약)
    if len(data) > 16000 * 10:
        data = data[: 16000 * 10]

    tensor = torch.from_numpy(data.astype(np.float32)).unsqueeze(0)
    out_prob, score, index, text_lab = classifier.classify_batch(tensor)

    feats = {}
    feats["sb_emotion_label"] = str(text_lab[0]) if text_lab else "unknown"
    feats["sb_emotion_score"] = float(score[0]) if hasattr(score, '__len__') else float(score)

    # 4가지 감정 확률 (neutral, happy, sad, angry)
    probs = out_prob[0].detach().cpu().numpy() if hasattr(out_prob, 'detach') else out_prob[0]
    emotion_names = ["neutral", "angry", "happy", "sad"]
    for i, name in enumerate(emotion_names[:len(probs)]):
        feats[f"sb_emotion_{name}_prob"] = float(probs[i])
    return feats


def _extract_speechbrain_ecapa(audio_bytes: bytes) -> dict:
    """ECAPA-TDNN 화자 임베딩 — 192-dim."""
    from speechbrain.inference.speaker import EncoderClassifier
    import soundfile as sf
    import torch

    if "sb_ecapa" not in _CACHE:
        _CACHE["sb_ecapa"] = EncoderClassifier.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb",
            savedir="~/.cache/sb_ecapa",
        )
    classifier = _CACHE["sb_ecapa"]

    data, sr = sf.read(BytesIO(audio_bytes))
    if data.ndim > 1:
        data = data.mean(axis=1)
    if sr != 16000:
        import librosa
        data = librosa.resample(data.astype(np.float32), orig_sr=sr, target_sr=16000)

    tensor = torch.from_numpy(data.astype(np.float32)).unsqueeze(0)
    embedding = classifier.encode_batch(tensor)
    emb = embedding.squeeze().detach().cpu().numpy()

    feats = {}
    feats["ecapa_embedding"] = emb.tolist()  # 192-dim
    feats["ecapa_embedding_norm"] = float(np.linalg.norm(emb))
    feats["ecapa_embedding_mean"] = float(np.mean(emb))
    feats["ecapa_embedding_std"] = float(np.std(emb))
    return feats


# ============================================================
# 10. BasicPitch — 다중 음정 검출 (Spotify)
# ============================================================

def _extract_basicpitch(audio_bytes: bytes) -> dict:
    from basic_pitch.inference import predict
    import tempfile
    import soundfile as sf

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        data, sr = sf.read(BytesIO(audio_bytes))
        if data.ndim > 1:
            data = data.mean(axis=1)
        sf.write(tmp.name, data, sr)
        path = tmp.name

    try:
        model_output, midi_data, note_events = predict(path)
        feats = {}
        if note_events:
            durations = [end - start for start, end, _, _, _ in note_events]
            pitches = [pitch for _, _, pitch, _, _ in note_events]
            velocities = [vel for _, _, _, vel, _ in note_events]
            feats["bp_note_count"] = len(note_events)
            feats["bp_pitch_min"] = int(min(pitches))
            feats["bp_pitch_max"] = int(max(pitches))
            feats["bp_pitch_range"] = int(max(pitches) - min(pitches))
            feats["bp_pitch_mean"] = float(np.mean(pitches))
            feats["bp_duration_mean"] = float(np.mean(durations))
            feats["bp_velocity_mean"] = float(np.mean(velocities))
        else:
            feats["bp_note_count"] = 0
        return feats
    finally:
        Path(path).unlink(missing_ok=True)


# ============================================================
# 11. Resemblyzer — 256-dim 화자 임베딩 (기존 통합 그대로)
# ============================================================

def _extract_resemblyzer(audio_bytes: bytes) -> dict:
    from resemblyzer import VoiceEncoder, preprocess_wav
    import librosa

    if "resemblyzer" not in _CACHE:
        _CACHE["resemblyzer"] = VoiceEncoder("cpu", verbose=False)
    encoder = _CACHE["resemblyzer"]

    y, _ = librosa.load(BytesIO(audio_bytes), sr=16000, mono=True, duration=90.0)
    wav = preprocess_wav(y, source_sr=16000)
    if len(wav) < 16000:
        raise ValueError("음원이 너무 짧습니다")
    emb = encoder.embed_utterance(wav)

    feats = {}
    feats["resemblyzer_embedding"] = emb.tolist()  # 256-dim
    feats["resemblyzer_embedding_norm"] = float(np.linalg.norm(emb))
    return feats


# ============================================================
# 통합 진입점
# ============================================================

def extract_all_pro(
    audio_bytes: bytes,
    use_demucs: bool = False,  # 보컬 분리 — 느림 (CPU 30~60s)
    use_heavy_models: bool = True,  # HuBERT/ECAPA/Emotion — 무거움
) -> dict:
    """풍부 통합 분석 — 가능한 모든 도구 호출 (graceful fallback).

    Args:
        audio_bytes: 원본 오디오 바이트
        use_demucs: 보컬 분리 적용 여부 (느림)
        use_heavy_models: 무거운 모델 (HuBERT 등) 사용 여부

    Returns:
        통합 feature dict (실패한 도구는 _error_* 키로 표시)
    """
    # 1) Demucs 보컬 분리 (선택)
    working_bytes = audio_bytes
    if use_demucs:
        vocals = separate_vocal_demucs(audio_bytes)
        if vocals is not None:
            import soundfile as sf
            buf = BytesIO()
            sf.write(buf, vocals, 22050, format="WAV")
            working_bytes = buf.getvalue()

    # 2) 각 도구 호출 — graceful fallback
    all_feats = {}

    extractors = [
        ("librosa", _extract_librosa),
        ("parselmouth", _extract_parselmouth),
        ("crepe", _extract_crepe),
        ("opensmile", _extract_opensmile),
        ("essentia", _extract_essentia),
        ("silero_vad", _extract_silero_vad),
        ("basicpitch", _extract_basicpitch),
        ("resemblyzer", _extract_resemblyzer),
    ]

    if use_heavy_models:
        extractors.extend([
            ("hubert", _extract_hubert),
            ("speechbrain_ecapa", _extract_speechbrain_ecapa),
            ("speechbrain_emotion", _extract_speechbrain_emotion),
        ])

    for name, fn in extractors:
        result = _safe_call(name, fn, working_bytes)
        all_feats.update(result)

    # 3) 메타 정보
    all_feats["_meta_tools_succeeded"] = [
        name for name, _ in extractors
        if not any(k.startswith(f"_error_{name}") for k in all_feats.keys())
    ]
    all_feats["_meta_tools_failed"] = [
        name for name, _ in extractors
        if any(k.startswith(f"_error_{name}") for k in all_feats.keys())
    ]
    all_feats["_meta_feature_count"] = len([k for k in all_feats.keys() if not k.startswith("_")])

    return all_feats


# ============================================================
# 헬퍼 — 기존 4축 측정값과 호환되는 dict로 변환
# ============================================================

def to_legacy_measurements(pro_feats: dict) -> dict:
    """풍부 feature dict → vocal_mbti.py 호환 12개 측정값."""
    legacy = {}

    # spectral_centroid_hz
    legacy["spectral_centroid_hz"] = pro_feats.get(
        "librosa_spectral_centroid_mean_hz", 1800.0
    )

    # chest_voice_ratio (저주파 에너지 비율 — 근사)
    rolloff = pro_feats.get("librosa_spectral_rolloff_85_hz", 3000.0)
    legacy["chest_voice_ratio"] = float(np.clip((3500 - rolloff) / 2000, 0, 1))

    # formants — Parselmouth 우선, fallback librosa
    legacy["formant_1_hz"] = pro_feats.get("praat_formant_1_mean_hz", 600.0)
    legacy["formant_2_hz"] = pro_feats.get("praat_formant_2_mean_hz", 1500.0)
    if "praat_formant_3_mean_hz" in pro_feats:
        legacy["formant_3_hz"] = pro_feats["praat_formant_3_mean_hz"]

    # nasal_resonance_ratio (근사)
    legacy["nasal_resonance_ratio"] = 0.5  # librosa로 별도 계산 가능

    # breathiness (spectral flatness)
    flat = pro_feats.get("librosa_spectral_flatness_mean", 0.1)
    legacy["breathiness"] = float(np.clip(flat * 10, 0, 1))

    # HNR — Praat 우선
    legacy["hnr_db"] = pro_feats.get("praat_hnr_db", 20.0)

    # dynamic_range_db
    legacy["dynamic_range_db"] = pro_feats.get("librosa_dynamic_range_db", 15.0)

    # attack_sharpness
    onset_mean = pro_feats.get("librosa_onset_mean", 1.5)
    legacy["attack_sharpness"] = float(np.clip(onset_mean / 3, 0, 1))

    # loudness_smoothness
    rms_std = pro_feats.get("librosa_rms_std_db", 5.0)
    rms_mean = abs(pro_feats.get("librosa_rms_mean_db", -20.0))
    legacy["loudness_smoothness"] = float(np.clip(1 - rms_std / max(rms_mean, 1), 0, 1))

    # climax_building / energy_change_rate — Essentia dynamic_complexity로 근사
    dyn_complex = pro_feats.get("essentia_lowlevel_dynamic_complexity", 0.5)
    legacy["climax_building"] = float(np.clip(dyn_complex, 0, 1))
    legacy["energy_change_rate"] = float(np.clip(dyn_complex * 0.8, 0, 1))

    # Jitter/Shimmer 보너스
    if "praat_jitter_local" in pro_feats:
        legacy["jitter_local"] = pro_feats["praat_jitter_local"]
    if "praat_shimmer_local" in pro_feats:
        legacy["shimmer_local"] = pro_feats["praat_shimmer_local"]

    return legacy


if __name__ == "__main__":
    # 자체 테스트용
    print("audio_extractor_pro v2.3 - 11종 AI 도구 통합")
    print("사용: extract_all_pro(audio_bytes)")
