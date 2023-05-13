from moviepy.editor import *
import speech_recognition as sr
import numpy as np

def transcribe_audio_file(file_path: str):
    # Load the audio file
    clip = AudioFileClip(file_path)

    # Extract the audio data as a numpy array
    audio_array = clip.to_soundarray()

    # Transcribe the audio file
    r = sr.Recognizer()
    bytes_per_sample = max(1, int(audio_array.dtype.itemsize / audio_array.shape[1]))
    audio_max = np.abs(audio_array).max()
    if audio_max > 1:
        audio_array = audio_array / audio_max
    audio_source = sr.AudioData(np.int16(audio_array * 32767), clip.fps, bytes_per_sample)
    transcription = r.recognize_sphinx(audio_source, show_all=True)

    # Extract the word timings
    word_timings = list()
    for word in transcription.seg():
        word_timings.append((word.word, word.start_frame / clip.fps, word.end_frame / clip.fps))

    return word_timings, clip

if __name__ == "__main__":
    word_times, audio = transcribe_audio_file('20.mp3')

    subclips = list()
    for word, start_time, end_time in word_times:
        subclip = TextClip(word, fontsize=30, color='white').set_fps(24)
        subclip = subclip.set_start(start_time)
        subclip = subclip.set_end(end_time * 24 * 4)
        subclips.append(subclip)

    final_clip = concatenate_videoclips(subclips, method='compose')
    final_clip = final_clip.set_audio(audio)
    final_clip = final_clip.set_duration(audio.duration)
    final_clip.write_videofile('speech.webm')
