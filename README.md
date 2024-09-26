# YTTranscriber

Transcribe YouTube videos using OpenAI's Whisper and ChatGPT-4o

**The code is mostly there, and I'll be updating this readme soon -- here are the absolute essentials for now.**

---

I created this pipeline to summarize YouTube videos. I occasionally watch long lectures and the like and found myself growing tired of sitting through an hour or more of rhetoric and visuals—I want the essence of what I was watching. This pipeline is one step toward obtaining it quickly: it downloads the audio of the video (00); it transcribes it (01); it summarizes the transcription either extractively or abstractively, and either succinctly or verbosely (02).

There are many technical and philosophical nuances involved in designing this pipeline, and I have only put in the time to create a simple approach. Given the token and memory limitations of the summarizing model, for example, I simply chunk the transcription according to word count in a mildly overlapping fashion and then summarize each chunk individually. A more substantive approach would find contiguous chunks based on something like topic modeling. This is an example of the latter nuance—the former would involve considering how to make this pipeline faster and able to parallelize over multiple videos within a more elegant interface. Currently, it simply works through command-line arguments.

Nonetheless, this is a reasonably competent attempt that is primed for your improvement. For example, audio is compressed with a view to what Whisper actually converts it into during its own processing [\[1\]](https://github.com/openai/whisper/discussions/870) (00); chunks and overlaps between chunks are created while ensuring they preserve sentences (02); and so on. Initial trials show that particularly abstractive summarization works well. Still, I will be improving the pipeline as I continue to use it.

---

**Technical Specifics**

As stated within the scripts, you will need an OpenAI API key to run 01 and 02. You will also need to know how to work with Python and what `pip install yt_dlp ffmpeg-python openai==1.48 tqdm` means. If you sufficiently desire, raise an [issue](https://github.com/nurmister/YTTranscriber/issues) and I can probably help you solve technical issues.

If you've found this repository, these are probably trivialities. In case you wish to contribute to this small project, I would appreciate a pull request integrating [a local copy of Whisper](https://github.com/openai/whisper) into 01. While summarization (more correctly, chat completion) API calls are cheap, Whisper isn't really. The API also accepts audio of only 25 MB (which equates to about two hours at 32 kbps) with the efficient Ogg format downloaded by 00.
