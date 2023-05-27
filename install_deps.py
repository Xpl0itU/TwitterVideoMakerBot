import subprocess
import platform
import os
import requests
import sys


def get_python_executable_path() -> str:
    executable_path = sys.executable
    if hasattr(sys, "real_prefix"):
        venv_path = os.path.dirname(sys.real_prefix)
        executable_path = os.path.join(venv_path, executable_path)
    return executable_path


def install_spacy_model(python_executable_path: str) -> None:
    subprocess.run(
        [python_executable_path, "-m", "spacy", "download", "en_core_web_sm"]
    )


def install_pip_deps(python_executable_path: str) -> None:
    subprocess.run([python_executable_path, "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.run(
        [python_executable_path, "-m", "pip", "install", "-r", "requirements.txt"]
    )


def install_playright(python_executable_path: str) -> None:
    subprocess.run([python_executable_path, "-m", "playwright", "install"])
    # This will allow packaging playwright's firefox with pyinstaller
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "0"
    subprocess.run([python_executable_path, "-m", "playwright", "install", "firefox"])


def install_ffmpeg_windows():
    try:
        zip = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
        r = requests.get(zip)
        with open("ffmpeg.zip", "wb") as f:
            f.write(r.content)
        import zipfile

        with zipfile.ZipFile("ffmpeg.zip", "r") as zip_ref:
            zip_ref.extractall()
        os.remove("ffmpeg.zip")
        os.rename("ffmpeg-master-latest-win64-gpl", "ffmpeg")
        # Move the files inside bin to the root
        for file in os.listdir("ffmpeg/bin"):
            os.rename(f"ffmpeg/bin/{file}", f"ffmpeg/{file}")
        os.rmdir("ffmpeg/bin")
        for file in os.listdir("ffmpeg/doc"):
            os.remove(f"ffmpeg/doc/{file}")
        os.rmdir("ffmpeg/doc")
        # Add to the path
        subprocess.run(
            'setx /M PATH "%PATH%;%CD%\\ffmpeg"',
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print(
            "FFmpeg installed successfully! Please restart your computer and then re-run the program."
        )
    except Exception as e:
        print(
            "An error occurred while trying to install FFmpeg. Please try again. Otherwise, please install FFmpeg manually and try again."
        )
        print(e)


if __name__ == "__main__":
    python_executable_path = get_python_executable_path()
    install_pip_deps(python_executable_path)
    install_spacy_model(python_executable_path)
    install_playright(python_executable_path)

    if platform.system() == "Windows":
        install_ffmpeg_windows()
