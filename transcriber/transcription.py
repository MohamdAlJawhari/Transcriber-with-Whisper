import librosa
import torch
from flask import current_app
from transformers import WhisperProcessor, WhisperForConditionalGeneration

_processor = None
_model = None
_loaded_model_dir = None
_device = None

# This function determines whether to use GPU or CPU
def _resolve_device() -> str:
    return "cuda" if torch.cuda.is_available() else "cpu"

# Load the model and processor from the specified directory
def _load_model(model_dir: str):
    global _processor, _model, _loaded_model_dir, _device
    if _processor is not None and _model is not None and _loaded_model_dir == model_dir:
        return _processor, _model, _device

    _device = _resolve_device()
    print(f"Loading Whisper model from '{model_dir}' on {_device}...")
    _processor = WhisperProcessor.from_pretrained(model_dir)
    _model = WhisperForConditionalGeneration.from_pretrained(model_dir).to(_device)
    _model.eval()
    _loaded_model_dir = model_dir
    print("Whisper model loaded.")
    return _processor, _model, _device

# Preload model at app startup
def preload_model(app) -> None:
    """Preload Whisper model at startup (optional)."""
    with app.app_context():
        _load_model(app.config["MODEL_DIR"])

# Transcribe an audio file and return the transcribed text
def transcribe_audio_iter(filepath: str):
    """
    Yield (chunk_index, total_chunks, text) for each chunk.

    We chunk the audio into ~30-second segments because Whisper has
    a limited context window.
    """
    processor, model, device = _load_model(current_app.config["MODEL_DIR"])

    # 1. Load full audio and resample to 16kHz
    print(f"Loading audio: {filepath}")
    audio, _ = librosa.load(filepath, sr=16000)
    if audio.ndim > 1:
        # If stereo, convert to mono
        audio = librosa.to_mono(audio)

    # 2. Define chunk size (in samples)
    max_chunk_seconds = current_app.config["MAX_CHUNK_SECONDS"]
    chunk_size = max_chunk_seconds * 16000

    total_samples = len(audio)
    if total_samples == 0:
        print("Audio file has 0 samples after loading.")
        return

    # 3. Split into chunks
    chunks = []
    for start in range(0, total_samples, chunk_size):
        end = min(start + chunk_size, total_samples)
        chunk = audio[start:end]
        if len(chunk) > 0:
            chunks.append(chunk)

    print(f"Transcribing {len(chunks)} chunk(s)...")

    for idx, chunk in enumerate(chunks, start=1):
        try:
            inputs = processor(
                chunk,
                sampling_rate=16000,
                return_tensors="pt",
            )

            input_features = inputs.input_features.to(device)

            with torch.no_grad():
                predicted_ids = model.generate(input_features)

            text = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
            text = text.strip()

            print(f"Chunk {idx}/{len(chunks)}: {len(chunk)} samples -> '{text[:50]}...'")
            yield idx, len(chunks), text
        except Exception as e:
            print(f"Error transcribing chunk {idx}: {e}")
            yield idx, len(chunks), ""

def transcribe_audio(filepath: str) -> str:
    """
    Transcribe an audio file using Whisper and return the full text.
    """
    all_texts = []
    for _idx, _total, text in transcribe_audio_iter(filepath):
        if text:
            all_texts.append(text)

    full_text = " ".join(all_texts)
    return full_text.strip()
