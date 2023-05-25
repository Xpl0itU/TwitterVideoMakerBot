import whisper
import json
import ffmpeg
from datetime import timedelta, datetime

DEBUG = False  # Change it to show debug information


def add_subtitles(video_path, subtitles_path, output_path):
    # Customize subtitles with this filter
    subtitle_filter = (
        f"subtitles='{subtitles_path}':"
        f"force_style='Fontsize=18,"  # Font Size
        f"PrimaryColour=&HFFFFFF&,"  # Font Color in BGR format or ABGR format
        f"Alignment=6,"  # Top Center Alignment
        f"MarginL=0,"  # Offset Left
        f"MarginR=0,"  # Offset Right
        f"MarginV=200'"  # Vertical Offset
    )

    # Codecs configuration
    video_codec = "libx264"
    audio_codec = "aac"

    # Output options
    output_options = {"vf": subtitle_filter, "c:v": video_codec, "c:a": audio_codec}

    # Render the video
    ffmpeg.input(video_path).output(output_path, **output_options).run(
        quiet=True, overwrite_output=True, capture_stdout=False, capture_stderr=False
    )


def generate_srt(subtitles):
    timestamp_format = datetime.strptime(
        "00:00:00,000", "%H:%M:%S,%f"
    )  # Null element of addition to keep the timestamp format
    srt = ""
    for i, subtitle in enumerate(subtitles):
        start_time = (subtitle["start_time"] + timestamp_format).strftime(
            "%H:%M:%S,%f"
        )[:-3]
        end_time = (subtitle["end_time"] + timestamp_format).strftime("%H:%M:%S,%f")[
            :-3
        ]
        words = subtitle["words"]

        srt += f"{i+1}\n"
        srt += f"{start_time} --> {end_time}\n"
        srt += " ".join(words) + "\n\n"

    return srt


def append_segment_to_subtitles(subtitles: list, segment: dict, text: str):
    if DEBUG:
        print(f"{segment[text]} | {segment['start']} | {segment['end']}")
    # Calculate end_time for each word
    start_time = timedelta(seconds=segment["start"])
    end_time = timedelta(seconds=segment["end"])
    # Create subtitle for each word
    subtitle = {
        "start_time": start_time,
        "end_time": end_time,
        "words": [segment[text]],
    }
    subtitles.append(subtitle)
    return subtitles


def transcribe_audio(audio_path: str, srt_path: str, word_by_word: bool = True):
    model = whisper.load_model(
        "base"
    )  # You can choose: [tinu, base, small, medium] to more accurate subtitles
    transcribe = model.transcribe(
        audio=audio_path, fp16=False, word_timestamps=True, verbose=DEBUG
    )
    segments = transcribe["segments"]
    if DEBUG:
        with open("transcribe_dump.txt", "w") as arq:
            arq.writelines(json.dumps(transcribe, indent=2))
    subtitles = []
    for segment in segments:
        # Segment Information
        words = segment["words"]
        if word_by_word:
            for word in words:
                subtitles = append_segment_to_subtitles(subtitles, word, "word")
        else:
            subtitles = append_segment_to_subtitles(subtitles, segment, "text")

    # Gererate the SRT File
    srt_content = generate_srt(subtitles)

    # Write the SRT File
    with open(srt_path, "w", encoding="utf-8") as file:
        file.write(srt_content)

    print("Subtitles was generated with success!")
