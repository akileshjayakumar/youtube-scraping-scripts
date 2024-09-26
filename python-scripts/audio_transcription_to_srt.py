import torch
from transformers import pipeline
import logging
import os
from pydub import AudioSegment

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

device = "cuda:0" if torch.cuda.is_available() else "cpu"


def get_srt_filename(audio_path):
    base_name = os.path.basename(audio_path)
    name, _ = os.path.splitext(base_name)
    return f"{name}.srt"


def initialize_pipeline():
    try:
        logging.info("Starting the transcription process.")
        transcribe = pipeline(task="automatic-speech-recognition",
                              model="vasista22/whisper-tamil-medium", device=device)
        logging.info(f"Using device: {device}")
        return transcribe
    except Exception as e:
        logging.error(f"Error initializing transcription pipeline: {e}")
        exit()


transcribe = initialize_pipeline()


def format_timestamp(ms):
    seconds, milliseconds = divmod(ms, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"


def transcribe_audio_chunks(audio_path, chunk_length_ms=10000, overlap_length_ms=5000):
    audio = AudioSegment.from_wav(audio_path)
    audio_length_ms = len(audio)
    transcriptions = []

    for start_ms in range(0, audio_length_ms, chunk_length_ms - overlap_length_ms):
        end_ms = min(start_ms + chunk_length_ms, audio_length_ms)
        audio_chunk = audio[start_ms:end_ms]

        chunk_path = "/tmp/audio_chunk.wav"
        audio_chunk.export(chunk_path, format="wav")

        try:
            logging.info(
                f"Transcribing chunk {start_ms // chunk_length_ms + 1}/{audio_length_ms // chunk_length_ms + 1}")
            chunk_transcription = transcribe(chunk_path)["text"]
            transcriptions.append((start_ms, end_ms, chunk_transcription))
        except Exception as e:
            logging.error(
                f"Error during transcription of chunk starting at {start_ms} ms: {e}")

    if os.path.exists(chunk_path):
        os.remove(chunk_path)

    return transcriptions


def save_transcription_to_srt(transcriptions, srt_filepath):
    try:
        with open(srt_filepath, "w", encoding="utf-8") as srt_file:
            for i, (start_ms, end_ms, tamil_text) in enumerate(transcriptions):
                srt_file.write(f"{i + 1}\n")
                srt_file.write(
                    f"{format_timestamp(start_ms)} --> {format_timestamp(end_ms)}\n")
                srt_file.write(f"{tamil_text}\n\n")

        logging.info(f"Transcription saved to {srt_filepath}")
    except Exception as e:
        logging.error(
            f"Error saving to .srt file: {e}")
        exit()


def process_folder(folder_path, output_folder):
    for filename in os.listdir(folder_path):
        if filename.endswith(".wav"):
            audio_path = os.path.join(folder_path, filename)
            srt_filename = get_srt_filename(audio_path)
            srt_filepath = os.path.join(output_folder, srt_filename)

            logging.info(f"Processing file: {audio_path}")
            try:
                transcriptions = transcribe_audio_chunks(audio_path)
                logging.info("Transcription completed.")
                save_transcription_to_srt(transcriptions, srt_filepath)
            except Exception as e:
                logging.error(f"Error processing file {audio_path}: {e}")
                continue


# Main process
folder_path = ""
output_folder = ""

process_folder(folder_path, output_folder)