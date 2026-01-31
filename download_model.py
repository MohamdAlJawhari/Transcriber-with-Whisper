from transformers import WhisperProcessor, WhisperForConditionalGeneration

MODEL_NAME = "openai/whisper-small"  # multilingual

print("Downloading model... this may take a few minutes.")

processor = WhisperProcessor.from_pretrained(MODEL_NAME)
model = WhisperForConditionalGeneration.from_pretrained(MODEL_NAME)

processor.save_pretrained("model")
model.save_pretrained("model")

print("Model saved to ./model")
