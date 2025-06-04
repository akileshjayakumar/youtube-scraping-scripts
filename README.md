# YouTube Audio Scraper

This repository provides Python scripts to extract both audio and video transcripts from a YouTube channel using the YouTube API.

## Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set up your API key:

Create a `.env` file inside the `youtube-scraper` directory and add:

```env
YOUTUBE_API_KEY=your-api-key
```

Replace `your-api-key` with your actual YouTube API key.  
For help generating an API key, follow this [guide](https://developers.google.com/youtube/registering_an_application).

## Structure

- `python-scripts/` – Core Python scripts for transcript extraction.
- `notebooks/` – Jupyter notebooks for analysis or experimentation.

## Notes

Ensure your API quota is sufficient, especially when processing larger channels.
