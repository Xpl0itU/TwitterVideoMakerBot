import sys
import pathlib
from typing import Union, List, Tuple


def get_user_data_dir(
    appending_paths: Union[str, List[str], Tuple[str, ...]] = "Fudgify"
) -> pathlib.Path:
    home = pathlib.Path.home()

    system_paths = {
        "win32": home / "AppData/Roaming",
        "linux": home / ".local/share",
        "darwin": home / "Library/Application Support",
    }

    if sys.platform not in system_paths:
        raise SystemError(
            f'Unknown System Platform: {sys.platform}. Only supports {", ".join(list(system_paths.keys()))}'
        )
    data_path = system_paths[sys.platform]

    if appending_paths:
        if isinstance(appending_paths, str):
            appending_paths = [appending_paths]
        for path in appending_paths:
            data_path = data_path / path

    return data_path
