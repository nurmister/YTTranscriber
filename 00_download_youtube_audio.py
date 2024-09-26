#!/usr/bin/env python3
"""
00_download_youtube_audio.py

A script to download the highest-quality FLAC audio from a YouTube video and convert it to Opus format.

Usage:
    python 00_download_youtube_audio.py <YouTube_URL> <Name> [Directory] [--bitrate BITRATE]

Positional Arguments:
    YouTube_URL   The URL of the YouTube video.
    Name          The desired name for the output files (without extension).
    Directory     The directory to save the audio files (optional, defaults to "audio").

Optional Arguments:
    --bitrate BITRATE   The bitrate for the Opus conversion in kbps (default: 32).

Dependencies:
    - yt_dlp
    - ffmpeg-python
    - ffmpeg (must be installed and accessible in the system's PATH)

Example:
    python 00_download_youtube_audio.py "https://www.youtube.com/watch?v=2StKxMKWfbU" ist_means_ist --bitrate 48

Author:
    Nurmister
"""

import argparse
import os
import sys
import subprocess
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    print("Error: yt_dlp is not installed. Install it using 'pip install yt_dlp'.")
    sys.exit(1)

try:
    import ffmpeg
except ImportError:
    print("Error: ffmpeg-python is not installed. Install it using 'pip install ffmpeg-python'.")
    sys.exit(1)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Download highest-quality FLAC audio from a YouTube URL and convert it to Opus format."
    )
    parser.add_argument("youtube_url", help="The URL of the YouTube video.")
    parser.add_argument("name", help="The desired name for the output files (without extension).")
    parser.add_argument(
        "directory",
        nargs="?",
        default="audio",
        help='The directory to save the audio files (default: "audio").',
    )
    parser.add_argument(
        "--bitrate",
        type=int,
        default=32,
        help="The bitrate for the Opus conversion in kbps (default: 32).",
    )
    return parser.parse_args()


def download_audio(youtube_url, output_base_path):
    """
    Download the highest-quality audio from the YouTube URL as FLAC.

    Args:
        youtube_url (str): The YouTube video URL.
        output_base_path (str): The base path (without extension) to save the downloaded FLAC file.

    Raises:
        yt_dlp.DownloadError: If downloading fails.
    """
    ydl_opts = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "outtmpl": output_base_path,  # No extension; FFmpegExtractAudio will append .flac
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "flac",
                "preferredquality": "0",  # Best quality
            }
        ],
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            print(f"Downloading audio from {youtube_url}...")
            ydl.download([youtube_url])
            flac_path = f"{output_base_path}.flac"
            if os.path.exists(flac_path):
                print(f"Audio downloaded successfully and saved to {flac_path}.")
            else:
                print(f"Error: Expected FLAC file was not found at {flac_path}.")
                sys.exit(1)
        except yt_dlp.DownloadError as e:
            print(f"Error downloading audio: {e}")
            sys.exit(1)


def convert_flac_to_opus(flac_path, opus_path, bitrate):
    """
    Convert a FLAC file to Opus format with specified parameters.

    Args:
        flac_path (str): Path to the input FLAC file.
        opus_path (str): Path to save the output Opus file.
        bitrate (int): Bitrate for the Opus conversion in kbps.

    Raises:
        ffmpeg.Error: If conversion fails.
    """
    print(f"Converting {flac_path} to Opus format with bitrate {bitrate} kbps...")
    try:
        (
            ffmpeg
            .input(flac_path)
            .output(
                opus_path,
                audio_bitrate=f'{bitrate}k',
                # Whisper-1 converts audio to Mono 16kHz.
                ar='16000',
                ac=1,
                frame_duration='120',  # Highest frame duration (120 ms)
            )
            .overwrite_output()
            .run(quiet=True)
        )
        print(f"Conversion successful. Opus file saved to {opus_path}.")
    except ffmpeg.Error as e:
        print(f"Error during conversion: {e.stderr.decode()}")
        sys.exit(1)


def check_ffmpeg_installed():
    """Check if ffmpeg is installed and accessible in the system's PATH."""
    try:
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: ffmpeg is not installed or not found in the system's PATH.")
        print("Please install ffmpeg from https://ffmpeg.org/download.html and ensure it's accessible from the command line.")
        sys.exit(1)


def main():
    """Main function to orchestrate downloading and conversion."""
    args = parse_arguments()

    youtube_url = args.youtube_url
    name = args.name
    directory = args.directory
    bitrate = args.bitrate

    # Ensure ffmpeg is installed
    check_ffmpeg_installed()

    # Create the output directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)

    # Define base path (without extension)
    output_base = os.path.join(directory, name)

    # Define file paths
    flac_path = f"{output_base}.flac"
    opus_path = f"{output_base}.opus"

    # Download the audio as FLAC
    download_audio(youtube_url, output_base)

    # Convert FLAC to Opus
    convert_flac_to_opus(flac_path, opus_path, bitrate)

    # Delete the FLAC file after successful conversion
    try:
        os.remove(flac_path)
        print(f"Deleted temporary FLAC file: {flac_path}")
    except OSError as e:
        print(f"Warning: Could not delete FLAC file {flac_path}: {e}")

    print("All tasks completed successfully.")


if __name__ == "__main__":
    main()

