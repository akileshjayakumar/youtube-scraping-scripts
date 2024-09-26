import argparse
import json
import os

import requests
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tqdm import tqdm
from youtube_transcript_api import YouTubeTranscriptApi
from pytube import YouTube
from pydub import AudioSegment


load_dotenv()
api_key = os.getenv("YOUTUBE_API_KEY")
youtube = build("youtube", "v3", developerKey=api_key)


# returns id of given channel
def get_channel_id(channel_name):
    url = "https://www.youtube.com/@" + channel_name
    r = requests.get(url)
    # Retrieve the whole page source
    text = r.text
    # Split the text to get only the section containing the channel id
    id = text.split("youtube.com/channel/")[1].split('">')[0]
    return id


# fetch video ID of videos in channel
def fetch_video_ids(channel_name):
    # Make a request to youtube api
    base_url = "https://www.googleapis.com/youtube/v3/channels"
    channel_id = get_channel_id(channel_name)
    params = {"part": "contentDetails", "id": channel_id, "key": api_key}
    try:
        response = requests.get(base_url, params=params)
        response = json.loads(response.content)
    except HttpError as e:
        print(f"An HTTP error occurred: {e}")
        return []

    if "items" not in response or not response["items"]:
        raise Exception(f"No playlist found for {channel_name}")

    # Retrieve the uploads playlist ID for the given channel
    playlist_id = response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    # Retrieve all videos from uploads playlist
    videos = []
    next_page_token = None

    while True:
        playlist_items_response = (
            youtube.playlistItems()
            .list(
                # part="contentDetails",
                part="snippet",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token,
            )
            .execute()
        )

        videos += playlist_items_response["items"]

        next_page_token = playlist_items_response.get("nextPageToken")

        if not next_page_token:
            break

    # Extract video URLs
    video_urls = []

    for video in videos:
        video_id = video["snippet"]["resourceId"]["videoId"]
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        video_title = video["snippet"]["title"]
        video_urls.append(
            {"ID": video_id, "URL": video_url, "Title": video_title})

    return video_urls


# save transcripts in a file
def fetch_and_save_transcript(video_id, file_name, language):
    def picker_trans(language):
        if language == "english":
            return "en"
        elif language == "chinese":
            return "zh"
        elif language == "malay":
            return "ms"
    try:
        # input language to be transcribed, en==english ms==malay zh==chinese
        transcript = YouTubeTranscriptApi.get_transcript(
            video_id, languages=[picker_trans(language)])
    except Exception as e:
        print(f"An error occurred: {e}")
        return False
    with open(file_name, "w", encoding="utf-8") as file:
        for line in transcript:
            file.write(f"{line['text']}\n")

    # returns true if transcript is saved sucessfully
    return True


# saves audio in a file
def fetch_audio(video_url, result_dir):
    try:
        yt = YouTube(video_url)
        audio = yt.streams.filter(
            only_audio=True, file_extension="mp4").first()
        if audio:
            mp4_path = audio.download(output_path=result_dir)
            # Create the WAV file path
            wav_path = os.path.splitext(mp4_path)[0] + ".wav"
            # Convert MP4 to WAV using pydub
            audio = AudioSegment.from_file(mp4_path, format="mp4")
            audio.export(wav_path, format="wav")
            # Optionally, remove the original MP4 file
            os.remove(mp4_path)

            print(
                f"Audio successfully downloaded and converted to WAV: {wav_path}")
            return True
        else:
            print(f"No audio stream found for video: {video_url}")
            return False
    except Exception as e:
        print(f"Error downloading audio for video {video_url}: {e}")
        return False


if __name__ == "__main__":
    # parses the aurgument in command line
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--channel_name", help="The name of the channel.", type=str)
    parser.add_argument(
        "--results_dir",
        help="The directory to save the transcripts.",
        type=str,
        default="transcripts",
    )
    parser.add_argument(
        "--max_videos",
        help="The max number of transcripts.",
        type=int,
        default=None,
    )
    parser.add_argument(
        "--language",
        help="Language of transcripts.",
        type=str,
        default="english",
    )

    args = parser.parse_args()
    max_videos = args.max_videos
    channel_name = args.channel_name
    results_dir = args.results_dir
    langauge = args.language

    TRANSCRIPTS_DIR = os.path.join(os.getcwd(), results_dir)
    os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)

    print(f"Fetching video IDs for {channel_name}...")
    videos = fetch_video_ids(channel_name)
    if max_videos:
        videos = videos[:max_videos]

    print(f"Fetching transcripts for {channel_name}...")
    cnt = 0
    for i, video in enumerate(tqdm(videos)):
        output_file = os.path.join(TRANSCRIPTS_DIR, f"{video['Title']}.txt")
        json_file = os.path.join(TRANSCRIPTS_DIR, "transcripts.json")

        # save transcript
        success = fetch_and_save_transcript(video["ID"], output_file, language=langauge) and fetch_audio(
            video["URL"], results_dir)

        # save json file with transcript_path, video_url, video_title
        if success:
            with open(json_file, "a", encoding="utf-8", newline="\n") as file:
                json.dump(
                    {
                        "status": "success" if success else "failed",
                        "channel_name": channel_name,
                        "transcript_path": output_file if success else "",
                        "video_url": video["URL"],
                        "video_title": video["Title"],
                    },
                    file,
                    ensure_ascii=False,
                    indent=4,
                )
            cnt += 1

    print(f"Saved {cnt} transcripts for {channel_name}.")
