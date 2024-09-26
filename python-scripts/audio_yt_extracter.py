import argparse
import json
import os
import re
import pandas as pd
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pydub import AudioSegment
from pytube import YouTube
from tqdm import tqdm
from yt_dlp import YoutubeDL
import torch
from transformers import pipeline


def fetch_video_ids_from_csv(csv_file_path):
    try:
        df = pd.read_csv(csv_file_path)
        video_urls = []
        seen_urls = set()  # To avoid duplicates
        ydl_opts = {
            'quiet': True,
            'skip_download': True,
        }

        for index, row in df.iterrows():
            for column in df.columns:
                cell_value = row[column]
                if isinstance(cell_value, str):
                    video_urls_in_cell = re.findall(
                        r"(https?://www\.youtube\.com/watch\?v=[a-zA-Z0-9_-]{11})", cell_value)
                    for video_url in video_urls_in_cell:
                        if video_url not in seen_urls:
                            seen_urls.add(video_url)
                            video_id_match = re.search(
                                r"v=([a-zA-Z0-9_-]{11})", video_url)
                            if video_id_match:
                                video_id = video_id_match.group(1)

                                with YoutubeDL(ydl_opts) as ydl:
                                    info_dict = ydl.extract_info(
                                        video_url, download=False)
                                    video_title = info_dict.get(
                                        'title', 'Unknown Title').replace('/', '_').replace('\\', '_')

                                video_urls.append(
                                    {"ID": video_id, "URL": video_url, "Title": video_title})

        return video_urls
    except Exception as e:
        print(f"An error occurred while reading the CSV file: {e}")
        return []


def print_video_urls(video_urls):
    df = pd.DataFrame(video_urls)
    print(df)


def fetch_audio_for_all_videos(video_urls, result_dir):
    os.makedirs(result_dir, exist_ok=True)

    for video in video_urls:
        video_url = video["URL"]

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(result_dir, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(video_url, download=True)
                title = info_dict.get('title', 'audio').replace(
                    '/', '_').replace('\\', '_')
                wav_path = os.path.join(result_dir, f"{title}.wav")
                print(
                    f"Audio successfully downloaded and converted to WAV: {wav_path}")
        except Exception as e:
            print(f"Error downloading audio for video {video_url}: {e}")


def main():
    csv_file_path = ""
    result_dir = ""

    video_urls = fetch_video_ids_from_csv(csv_file_path)
    print_video_urls(video_urls)
    fetch_audio_for_all_videos(video_urls, result_dir)


if __name__ == "__main__":
    main()
