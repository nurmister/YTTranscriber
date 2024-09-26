#!/usr/bin/env python3
"""
02_summarize_transcription.py

A script to summarize a transcription text file using OpenAI's text generation
API and save the summary as a text file.

Usage:
    python 02_summarize_transcription.py <Transcription_Name> [Input_Directory]
        [Summary_Directory] [--summarization_type {extractive,abstractive}]
        [--verbosity {verbose,succinct}] [--api_key API_KEY]

Positional Arguments:
    Transcription_Name   The name of the transcription text file to summarize
                         (with or without the .txt extension).
    Input_Directory      The directory containing the transcription file
                         (optional, defaults to "transcripts").
    Summary_Directory    The directory to save the summary text file
                         (optional, defaults to "summaries").

Optional Arguments:
    --summarization_type {extractive,abstractive}
                        The type of summarization to perform
                        (default: abstractive).
    --verbosity {verbose,succinct}
                        The verbosity level of the summary
                        (default: succinct).
    --api_key API_KEY   Your OpenAI API key. If not provided, the script
                        will look for the OPENAI_API_KEY environment variable.

Dependencies:
    - openai==1.48
    - python-dotenv (optional, for loading environment variables from a .env file)

Environment Variables:
    OPENAI_API_KEY      Your OpenAI API key. Set this if not providing --api_key.

Example:
    python 02_summarize_transcription.py ist_means_ist transcripts summaries \
        --summarization_type extractive --verbosity verbose \
        --api_key your_openai_api_key_here

Author:
    Nurmister
"""

import argparse
import os
import sys
import re
from pathlib import Path
from typing import List

try:
    import openai
except ImportError:
    print("Error: The 'openai' library is not installed. Install it using "
          "'pip install openai==1.48'.")
    sys.exit(1)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=("Summarize a transcription text file using OpenAI's chat "
                     "completion API and save the summary as a text file.")
    )
    parser.add_argument(
        "transcription_name",
        help=("The name of the transcription text file to summarize "
              "(with or without the .txt extension)."),
    )
    parser.add_argument(
        "input_directory",
        nargs="?",
        default="transcripts",
        help=('The directory containing the transcription file '
              '(optional, defaults to "transcripts").'),
    )
    parser.add_argument(
        "summary_directory",
        nargs="?",
        default="summaries",
        help=('The directory to save the summary text file '
              '(optional, defaults to "summaries").'),
    )
    parser.add_argument(
        "--summarization_type",
        choices=["extractive", "abstractive"],
        default="abstractive",
        help=('The type of summarization to perform: "extractive" or '
              '"abstractive" (default: "abstractive").'),
    )
    parser.add_argument(
        "--verbosity",
        choices=["verbose", "succinct"],
        default="succinct",
        help=('The verbosity level of the summary: "verbose" or "succinct" '
              '(default: "succinct").'),
    )
    parser.add_argument(
        "--api_key",
        type=str,
        default=None,
        help=("Your OpenAI API key. If not provided, the script will look for "
              "the OPENAI_API_KEY environment variable."),
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
        SystemExit: If the API key is not provided and not found in environment
                    variables.
    """
    if provided_key:
        return provided_key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OpenAI API key not provided. Use the --api_key argument "
              "or set the OPENAI_API_KEY environment variable.")
        sys.exit(1)
    return api_key


def construct_transcription_path(transcription_name, input_directory):
    """
    Construct the full path to the transcription file.

    Args:
        transcription_name (str): The name of the transcription file
                                   (with or without .txt extension).
        input_directory (Path): The directory containing the transcription file.

    Returns:
        Path: The full path to the transcription file.
    """
    transcription_path = Path(input_directory) / transcription_name
    if transcription_path.suffix != ".txt":
        transcription_path = transcription_path.with_suffix(".txt")
    return transcription_path


def check_file_exists(file_path):
    """
    Check if the specified file exists.

    Args:
        file_path (Path): The path to the file.

    Raises:
        SystemExit: If the file does not exist.
    """
    if not file_path.is_file():
        print(f"Error: The transcription file '{file_path}' does not exist.")
        sys.exit(1)


def read_transcription(file_path):
    """
    Read the content of the transcription file.

    Args:
        file_path (Path): The path to the transcription file.

    Returns:
        str: The content of the transcription file.

    Raises:
        SystemExit: If reading the file fails.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        print(f"Successfully read transcription from '{file_path}'.")
        return content
    except IOError as e:
        print(f"Error: Failed to read transcription file '{file_path}': {e}")
        sys.exit(1)


def split_into_sentences(text):
    """
    Split text into sentences using regular expressions.

    Args:
        text (str): The input text.

    Returns:
        List[str]: A list of sentences.
    """
    # This regex handles most sentence endings.
    sentence_endings = re.compile(r'(?<=[.!?]) +')
    sentences = sentence_endings.split(text)
    return sentences


def create_chunks(sentences, max_words=750, overlap_words=75):
    """
    Split sentences into chunks with specified maximum words and overlapping words.

    Args:
        sentences (List[str]): List of sentences.
        max_words (int): Maximum number of words per chunk.
        overlap_words (int): Number of overlapping words between chunks.

    Returns:
        List[str]: List of text chunks.
    """
    chunks = []
    current_chunk = []
    current_word_count = 0
    overlap = []

    for sentence in sentences:
        sentence_word_count = len(sentence.split())
        if current_word_count + sentence_word_count > max_words:
            # Add the current chunk to chunks
            chunk_text = ' '.join(current_chunk)
            chunks.append(chunk_text)

            # Prepare the overlap for the next chunk
            words = ' '.join(current_chunk).split()
            if len(words) >= overlap_words:
                overlap = words[-overlap_words:]
            else:
                overlap = words[:]

            # Start new chunk with overlap
            overlap_text = ' '.join(overlap)
            current_chunk = [overlap_text]
            current_word_count = len(overlap)

        # Add the sentence to the current chunk
        current_chunk.append(sentence)
        current_word_count += sentence_word_count

    # Add the last chunk
    if current_chunk:
        chunk_text = ' '.join(current_chunk)
        chunks.append(chunk_text)

    return chunks


def generate_summary_for_chunk(api_key,
                               chunk_text,
                               summarization_type,
                               verbosity):
    """
    Generate a summary for a single chunk using OpenAI's ChatCompletion API.

    Args:
        api_key (str): OpenAI API key.
        chunk_text (str): The text chunk to summarize.
        summarization_type (str): 'extractive' or 'abstractive'.
        verbosity (str): 'verbose' or 'succinct'.

    Returns:
        str: The summary of the chunk.

    Raises:
        SystemExit: If summary generation fails.
    """
    client = openai.OpenAI(api_key=api_key)
    try:
        print("Generating chunk summary...")
        # Define system message based on summarization type and verbosity
        system_content = (
            "You are a precise AI assistant that summarizes transcriptions of spoken content. "
            "The transcription may involve multiple speakers. "
            "Don't waste words with filler like "
            "\"in this transcription...\", \"the speaker says...\"."
        )
        if summarization_type == "extractive":
            system_content += (
                "Provide an extractive summary, focusing on the key points and main "
                "ideas directly from the text. "
            )
        else:
            system_content += (
                "Provide an abstractive summary, paraphrasing and revealing the main "
                "ideas in your own words. "
            )

        if verbosity == "verbose":
            system_content += (
                "Ensure that the summary is detailed with minimal compression, "
                "covering all essential aspects comprehensively."
            )
        else:
            system_content += (
                "Ensure that the summary is concise and succinct, capturing the main "
                "points effectively with minimal words."
            )

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": f"Please summarize the following transcription:\n\n{chunk_text}"},
            ],
            max_tokens=500,  # Adjust based on desired summary length per chunk
            temperature=0.5,
        )
        summary = response.to_dict()["choices"][0]["message"]["content"].strip()
        print("Summary for chunk generated successfully.")
        return summary
    except openai.AuthenticationError:
        print("Error: Authentication failed. Check your OpenAI API key.")
    except openai.APIConnectionError:
        print("Error: Failed to connect to OpenAI API. Check your internet connection.")
    except openai.OpenAIError as e:
        print(f"An error occurred during summary generation: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    sys.exit(1)


def generate_full_summary(api_key,
                          transcription_text,
                          summarization_type,
                          verbosity):
    """
    Generate a full summary by splitting the transcription into chunks and
    summarizing each.

    Args:
        api_key (str): OpenAI API key.
        transcription_text (str): The full transcription text.
        summarization_type (str): 'extractive' or 'abstractive'.
        verbosity (str): 'verbose' or 'succinct'.

    Returns:
        str: The combined summary.
    """
    sentences = split_into_sentences(transcription_text)
    chunks = create_chunks(sentences)
    print(f"Transcription split into {len(chunks)} chunks.")

    chunk_summaries = []
    for idx, chunk in enumerate(chunks, 1):
        print(f"Processing chunk {idx}/{len(chunks)}...")
        summary = generate_summary_for_chunk(
            api_key, chunk, summarization_type, verbosity
        )
        chunk_summaries.append(summary)

    # Combine chunk summaries into a full summary
    print("Combining chunk summaries into a full summary...")
    full_summary_text = "\n".join(chunk_summaries)
    return full_summary_text


def save_summary(summary, summary_path):
    """
    Save the summary to a text file.

    Args:
        summary (str): The summary text.
        summary_path (Path): Path to save the summary file.

    Raises:
        SystemExit: If saving the summary fails.
    """
    try:
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(summary)
        print(f"Summary saved to '{summary_path}'.")
    except IOError as e:
        print(f"Error: Failed to save summary to '{summary_path}': {e}")
        sys.exit(1)


def main():
    """Main function to orchestrate summarization."""
    args = parse_arguments()

    transcription_name = args.transcription_name
    input_directory = Path(args.input_directory)
    summary_directory = Path(args.summary_directory)
    summarization_type = args.summarization_type
    verbosity = args.verbosity
    provided_api_key = args.api_key

    # Retrieve API key
    api_key = get_api_key(provided_api_key)

    # Construct transcription file path
    transcription_path = construct_transcription_path(
        transcription_name, input_directory
    )

    # Check if transcription file exists
    check_file_exists(transcription_path)

    # Read transcription content
    transcription_text = read_transcription(transcription_path)

    # Generate full summary
    full_summary = generate_full_summary(
        api_key, transcription_text, summarization_type, verbosity
    )

    # Create summary directory if it doesn't exist
    summary_directory.mkdir(parents=True, exist_ok=True)

    # Define summary file path
    summary_filename = transcription_path.stem + ".txt"
    summary_path = summary_directory / summary_filename

    # Save the summary
    save_summary(full_summary, summary_path)

    print("All tasks completed successfully.")


if __name__ == "__main__":
    main()

