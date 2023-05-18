from moviepy.editor import *
from TTS.streamlabs_polly import StreamlabsPolly
import tempfile

PARENTHESIS = ["(", ")"]
END_MARKS = [".", "!", "?"]


def add_full_stop(text: str) -> str:
    """
    Adds a full stop to the end of the text if it is missing.
    :return: str, The text with a full stop at the end.
    """
    if not text == "":
        if not text[-1] in END_MARKS:
            text += "."
    return text


def get_sentences_from_story(story: str) -> list:
    """
    Splits a story into sentences.
    :param story: str, The story to split.
    :return: list, The list of sentences.
    """
    preferred_len = 120
    text = add_full_stop(story.strip())

    sentences = list()
    buffer = text
    while buffer:
        last_comma = last_stop = last_space = last_parenthesis = None

        for i, char in enumerate(buffer):
            if char in PARENTHESIS:
                last_parenthesis = i
            elif char in END_MARKS:
                last_stop = i
            elif char == ",":
                last_comma = i
            elif char == " " and not i >= (preferred_len - 1):
                last_space = i

            if i == len(buffer) - 1:
                sentences.append(buffer)
                buffer = str()
                break
            elif i >= (preferred_len - 1) and (
                last_stop or last_parenthesis or last_comma or last_space
            ):
                end_index = -2
                if last_stop:
                    end_index = last_stop
                elif last_parenthesis:
                    if buffer[last_parenthesis] == PARENTHESIS[0]:
                        end_index = max(last_parenthesis - 1, 0)
                    else:
                        end_index = last_parenthesis
                elif last_comma:
                    end_index = last_comma
                elif last_space:
                    end_index = last_space

                sentences.append(buffer[: end_index + 1])
                buffer = buffer[end_index + 1 :]
                break

    return list(map(lambda x: x.strip(), sentences))


def get_tts(text: str, output: str, filename: str) -> None:
    """
    Synthesize text to an mp3 file.
    :param text: str, The text to synthesize.
    :param output: str, The output directory.
    :param filename: str, The filename of the mp3 file.
    :return: None
    """
    engine = StreamlabsPolly()
    engine.run(text, f"{output}/{filename}.mp3")


def get_text_clip_for_tweet(text: str, id: int, audio_path: str) -> VideoClip:
    """
    Creates a video clip from a story.
    :param text: str, The story to create a video clip from.
    :param id: int, The id of the story.
    :return: VideoClip, The video clip.
    """
    os.makedirs(f"{tempfile.gettempdir()}/Fudgify/temp/{id}/tts", exist_ok=True)
    sentences = get_sentences_from_story(text)
    subclips = list()
    for i in range(len(sentences)):
        get_tts(
            sentences[i], f"{tempfile.gettempdir()}/Fudgify/temp/{id}/tts", f"{id}-{i}"
        )
        audio = AudioFileClip(
            f"{tempfile.gettempdir()}/Fudgify/temp/{id}/tts/{id}-{i}.mp3"
        )
        subclip = TextClip(
            sentences[i],
            fontsize=75,
            size=(1080, 1920),
            color="white",
            method="caption",
            align="center",
        ).set_fps(1)
        subclip = subclip.set_duration(audio.duration)
        subclips.append(subclip)

    audio = AudioFileClip(audio_path)
    final_clip = concatenate_videoclips(subclips, method="compose")
    return final_clip.set_audio(audio).set_duration(audio.duration)
