import multiprocessing
import faster_whisper
from datetime import timedelta, datetime


def get_subtitles_style(
    primary_color: str = "&HFFFFFF&",
    font_size: float = 18,
    bold: bool = True,
    desired_style: int = 1,
):
    """
    Get subtitles style.
    :param primary_color: Primary color.
    :param font_size: Font size.
    :param bold: Bold text.
    :param desired_style: Desired style.
    :return: Subtitles style.
    """
    style = {
        # Great format to run with screenshots
        1: f"Fontsize={font_size},"
        f"PrimaryColour={primary_color},"
        f"OutlineColour=&H40000000,"
        f"Bold={bold},"
        f"Alignment=6,"
        f"MarginL=0,"
        f"MarginR=0,"
        f"MarginV=200",
        # Centerd Bold Text
        2: f"Fontsize={font_size},"
        f"PrimaryColour=&HFFFFFF&,"
        f"OutlineColour=&H40000000,"
        f"Bold={bold},"
        f"Alignment=10,"
        f"MarginL=0,"
        f"MarginR=0,"
        f"MarginV=0",
    }
    return style[desired_style]


def generate_srt(subtitles: list) -> str:
    """
    Generate an SRT file from a list of timestamps of words
    :param subtitles: Subtitles list.
    :return: .srt file contents
    """
    timestamp_format = datetime.strptime(
        "00:00:00,000", "%H:%M:%S,%f"
    )  # Null element of addition to keep the timestamp format
    srt = str()
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


def append_segment_to_subtitles(subtitles: list, segment: tuple) -> list:
    """
    Append segment to subtitles.
    :param subtitles: Subtitles list.
    :param segment: Segment to append.
    :return: Subtitles list.
    """
    # Calculate end_time for each word
    start_time = timedelta(seconds=segment.start)
    end_time = timedelta(seconds=segment.end)
    # Create subtitle for each word
    subtitle = {
        "start_time": start_time,
        "end_time": end_time,
        "words": [segment.word],
    }
    subtitles.append(subtitle)
    return subtitles


def transcribe_audio(audio_path: str, srt_path: str, word_by_word: bool = True) -> None:
    """
    Transcribe audio file to SRT file.
    :param audio_path: Path to the audio file.
    :param srt_path: Path to the SRT file.
    :param word_by_word: If True, the subtitles will be generated by each word.
    """
    model = faster_whisper.WhisperModel(
        "base", cpu_threads=multiprocessing.cpu_count()
    )  # You can choose: [tinu, base, small, medium] to more accurate subtitles
    transcribe = model.transcribe(audio=audio_path, word_timestamps=True)
    segments = transcribe[0]
    subtitles = list()
    for segment in segments:
        # Segment Information
        words = segment.words
        if word_by_word:
            for word in words:
                subtitles = append_segment_to_subtitles(subtitles, word)
        else:
            subtitles = append_segment_to_subtitles(subtitles, segment)

    # Gererate the SRT File
    srt_content = generate_srt(subtitles)

    # Write the SRT File
    with open(srt_path, "w", encoding="utf-8") as file:
        file.write(srt_content)
