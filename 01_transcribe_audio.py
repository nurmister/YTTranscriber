#!/usr/bin/env python3
"""
01_transcribe_audio.py

A script to transcribe an Ogg audio file using OpenAI's Whisper API and save the transcription as a text file.

Usage:
    python 01_transcribe_audio.py <Audio_Name> <Input_Directory> [Transcript_Directory] [--api_key API_KEY]

Positional Arguments:
    Audio_Name          The name of the Ogg audio file to transcribe (with or without the .ogg extension).
    Input_Directory
                        The directory containing the audio file (optional, defaults to "audio")..
    Transcript_Directory
                        The directory to save the transcription (optional, defaults to "transcripts").

Optional Arguments:
    --api_key API_KEY   Your OpenAI API key. If not provided, the script will look for the OPENAI_API_KEY environment variable.

Dependencies:
    - openai==1.48
    - python-dotenv (optional, for loading environment variables from a .env file)

Environment Variables:
    OPENAI_API_KEY      Your OpenAI API key. Set this if not providing --api_key.

Example:
    python 01_transcribe_audio.py ist_means_ist audio transcripts --api_key your_openai_api_key_here

Author:
    Nurmister
"""

import argparse
import os
import sys
from pathlib import Path

try:
    import openai
except ImportError:
    print("Error: The 'openai' library is not installed. Install it using 'pip install openai==1.48'.")
    sys.exit(1)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Transcribe an Ogg audio file using OpenAI's Whisper API and save the transcription as a text file."
    )
    parser.add_argument(
        "audio_name",
        help="The name of the Ogg audio file to transcribe (with or without the .ogg extension).",
    )
    parser.add_argument(
        "input_directory",
        nargs="?",
        default="audio",
        help='The directory containing the audio file (default: "audio").',
    )
    parser.add_argument(
        "transcript_directory",
        nargs="?",
        default="transcripts",
        help='The directory to save the transcription (default: "transcripts").',
    )
    parser.add_argument(
        "--api_key",
        type=str,
        default=None,
        help="Your OpenAI API key. If not provided, the script will look for the OPENAI_API_KEY environment variable.",
    )
    return parser.parse_args()


def get_api_key(provided_key):
    """
    Retrieve the OpenAI API key.

    Args:
        provided_key (str): API key provided via command-line argument.

    Returns:
        str: The OpenAI API key.

    Raises:
        SystemExit: If the API key is not provided and not found in environment variables.
    """
    if provided_key:
        return provided_key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OpenAI API key not provided. Use the --api_key argument or set the OPENAI_API_KEY environment variable.")
        sys.exit(1)
    return api_key


def construct_audio_path(audio_name, input_directory):
    """
    Construct the full path to the audio file.

    Args:
        audio_name (str): The name of the audio file (with or without .ogg extension).
        input_directory (Path): The directory containing the audio file.

    Returns:
        Path: The full path to the audio file.
    """
    audio_path = Path(input_directory) / audio_name
    if audio_path.suffix != ".ogg":
        audio_path = audio_path.with_suffix(".ogg")
    return audio_path


def check_file_exists(file_path):
    """
    Check if the specified file exists.

    Args:
        file_path (Path): The path to the file.

    Raises:
        SystemExit: If the file does not exist.
    """
    if not file_path.is_file():
        print(f"Error: The audio file '{file_path}' does not exist.")
        sys.exit(1)


def transcribe_audio(api_key, audio_path):
    """
    Transcribe the audio file using OpenAI's Whisper API.

    Args:
        api_key (str): OpenAI API key.
        audio_path (Path): Path to the Ogg audio file.

    Returns:
        str: The transcription text.

    Raises:
        SystemExit: If transcription fails.
    """
    client = openai.OpenAI(api_key=api_key)
    try:
        print(f"Starting transcription for '{audio_path.name}'...")
        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-1",
                language="en",
                response_format="text"
            )
        print("Transcription completed successfully.")
        return transcript
    except openai.AuthenticationError:
        print("Error: Authentication failed. Check your OpenAI API key.")
    except openai.APIConnectionError:
        print("Error: Failed to connect to OpenAI API. Check your internet connection.")
    except openai.OpenAIError as e:
        print(f"An error occurred during transcription: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    sys.exit(1)


def save_transcription(transcript, transcript_path):
    """
    Save the transcription to a text file.

    Args:
        transcript (str): The transcription text.
        transcript_path (Path): Path to save the transcription file.

    Raises:
        SystemExit: If saving the transcription fails.
    """
    try:
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(transcript)
        print(f"Transcription saved to '{transcript_path}'.")
    except IOError as e:
        print(f"Error: Failed to save transcription to '{transcript_path}': {e}")
        sys.exit(1)


def main():
    """Main function to orchestrate transcription."""
    args = parse_arguments()

    audio_name = args.audio_name
    input_directory = Path(args.input_directory)
    transcript_directory = Path(args.transcript_directory)
    provided_api_key = args.api_key

    # Retrieve API key
    api_key = get_api_key(provided_api_key)

    # Construct audio file path
    audio_path = construct_audio_path(audio_name, input_directory)

    # Check if audio file exists
    check_file_exists(audio_path)

    # Create transcript directory if it doesn't exist
    transcript_directory.mkdir(parents=True, exist_ok=True)

    # Define transcript file path
    transcript_filename = audio_path.stem + ".txt"
    transcript_path = transcript_directory / transcript_filename

    # Transcribe the audio
    transcription = transcribe_audio(api_key, audio_path)

    # Save the transcription
    save_transcription(transcription, transcript_path)

    print("All tasks completed successfully.")


if __name__ == "__main__":
    main()

