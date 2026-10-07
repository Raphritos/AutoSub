# AutoSub

Automatic Subtitle Generator using OpenAI Whisper (100% free, offline).

## Features

- Supports video (.mp4, .mkv, .avi, .mov, .wmv) and audio (.mp3, .wav, .m4a, .flac, .ogg).
- Uses OpenAI Whisper (tiny, base, small) - runs locally on your PC.
- Optional translation to Portuguese (BR) using Google Translate.
- Output in SRT or VTT format.
- Modern interface with dark theme (CustomTkinter).
- Cancel button to stop the process at any time.
- Custom output folder.
- Bilingual interface (PT/EN).

## How to Use

1. Run `AutoSub.exe`.
2. Click "Select Video/Audio" and choose your file.
3. (Optional) Click "Output Folder" to choose where the subtitles will be saved.
4. Choose the audio language (or leave it on auto-detect).
5. Choose the Whisper model (tiny = faster, small = more accurate).
6. Choose the output format (SRT or VTT).
7. (Optional) Check "Translate to Portuguese (BR)" if you want translated subtitles.
8. Click "Generate Subtitles".

## Requirements

- Windows 10 or higher.
- 8 GB of RAM (minimum).
- ~500 MB of free disk space.
- Internet connection only if you use the translation option.

## Installation (from source)

```bash
pip install openai-whisper customtkinter srt googletrans==4.0.0rc1 legacy-cgi
python autosub.py
