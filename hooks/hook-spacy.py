# HOOK FILE FOR SPACY
from PyInstaller.utils.hooks import collect_all, collect_data_files

# ----------------------------- SPACY -----------------------------
data = collect_all('spacy')

datas = data[0]
binaries = data[1]
hiddenimports = data[2]

# ----------------------------- THINC -----------------------------
data = collect_all('thinc')

datas += data[0]
binaries += data[1]
hiddenimports += data[2]

# ----------------------------- CYMEM -----------------------------
data = collect_all('cymem')

datas += data[0]
binaries += data[1]
hiddenimports += data[2]

# ----------------------------- PRESHED -----------------------------
data = collect_all('preshed')

datas += data[0]
binaries += data[1]
hiddenimports += data[2]

# ----------------------------- BLIS -----------------------------

data = collect_all('blis')

datas += data[0]
binaries += data[1]
hiddenimports += data[2]

# ----------------------------- OTHER ----------------------------

hiddenimports += ['srsly.msgpack.util']

datas += collect_data_files("en_core_web_sm")