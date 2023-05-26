function install_spacy_model(){
    python -m spacy download en_core_web_sm
}

function install_pip_deps(){
    python -m pip install --upgrade pip
    pip install -r requirements.txt
}

function install_playright(){
    python -m playwright install
    python -m playwright install-deps
}

function install_ffmpeg_windows(){
    if ! command -v ffmpeg &> /dev/null; then
        curl -sL "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip" -o ffmpeg
        unzip ffmpeg
        rm -rf ffmpeg
        mv ffmpeg-master-latest-win64-gpl/bin C:\\Users\\$(whoami)\\AppData\\Local\\Programs\\Python\\Python311\\Scripts
        rm -rf ffmpeg-master-latest-win64-gpl
        echo "FFMPEG Installed with success, restart your computer to complete installation"
    fi
}

function install_fail(){
    echo "Failed! Try again or restart computer"
    exit 1
}

install_pip_deps || install_fail
install_spacy_model || install_fail
install_playright || install_fail
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
    install_ffmpeg_windows || install_fail
fi