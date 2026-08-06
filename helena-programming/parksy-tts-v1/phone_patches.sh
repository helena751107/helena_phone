#!/bin/bash
# GPT-SoVITS ARM64 phone patches — apply after git pull
# Fixes: numba/llvmlite LLVM crash, torchaudio TorchCodec, librosa.load
# Run: bash phone_patches.sh

set -e

GPT_DIR="${PARKSY_GPT_SOVITS_DIR:-$HOME/GPT-SoVITS}"
TTS_PY="$GPT_DIR/GPT_SoVITS/TTS_infer_pack/TTS.py"
BERT_TTS="$GPT_DIR/GPT_SoVITS/TTS_infer_pack/TTS.py"

echo "Applying ARM64 phone patches to GPT-SoVITS..."

# Patch 1: Replace librosa import with soundfile + scipy (numba-free)
python3 << 'PYEOF'
import sys
TTS_PATH = sys.argv[1]
with open(TTS_PATH) as f:
    content = f.read()

patches = [
    # librosa import → soundfile + scipy
    ("import librosa\n",
     """try:\n    import librosa as _librosa_orig\nexcept Exception:\n    _librosa_orig = None\nimport soundfile as _sf\nfrom scipy.signal import resample_poly as _resample_poly\n"""),
    # torchaudio.load → soundfile
    ("        raw_audio, raw_sr = torchaudio.load(ref_audio_path)\n",
     "        _raw_np, raw_sr = _sf.read(ref_audio_path, always_2d=True)\n        raw_audio = torch.from_numpy(_raw_np.T).float()\n"),
    # librosa.load → soundfile + scipy resample
    ("            wav16k, sr = librosa.load(ref_wav_path, sr=16000)\n",
     "            _wav_np, _wav_sr = _sf.read(ref_wav_path, always_2d=False)\n            if _wav_np.ndim > 1:\n                _wav_np = _wav_np.mean(axis=1)\n            if _wav_sr != 16000:\n                _wav_np = _resample_poly(_wav_np, 16000, _wav_sr).astype('float32')\n            wav16k, sr = _wav_np, 16000\n"),
]

changed = 0
for old, new in patches:
    if old in content:
        content = content.replace(old, new, 1)
        changed += 1

with open(TTS_PATH, "w") as f:
    f.write(content)
print(f"{changed}/3 patches applied to TTS.py")
PYEOF
"$TTS_PY"

# Patch 2: BERT init → skip gracefully for Korean (no 3.7GB roberta needed)
python3 << 'PYEOF'
import sys
TTS_PATH = sys.argv[1]
with open(TTS_PATH) as f:
    content = f.read()

old = """    def init_bert_weights(self, base_path: str):
        print(f"Loading BERT weights from {base_path}")
        self.bert_tokenizer = AutoTokenizer.from_pretrained(base_path)
        self.bert_model = AutoModelForMaskedLM.from_pretrained(base_path)
        self.bert_model = self.bert_model.eval()
        self.bert_model = self.bert_model.to(self.configs.device)
        if self.configs.is_half and str(self.configs.device) != "cpu":
            self.bert_model = self.bert_model.half()"""
new = """    def init_bert_weights(self, base_path: str):
        print(f"Loading BERT weights from {base_path}")
        try:
            self.bert_tokenizer = AutoTokenizer.from_pretrained(base_path)
            self.bert_model = AutoModelForMaskedLM.from_pretrained(base_path)
            self.bert_model = self.bert_model.eval()
            self.bert_model = self.bert_model.to(self.configs.device)
            if self.configs.is_half and str(self.configs.device) != "cpu":
                self.bert_model = self.bert_model.half()
        except Exception as e:
            print(f"BERT load skipped ({e.__class__.__name__}): Korean-only mode, zero-vectors will be used")
            self.bert_tokenizer = None
            self.bert_model = None"""

if old in content:
    content = content.replace(old, new, 1)
    with open(TTS_PATH, "w") as f:
        f.write(content)
    print("BERT patch applied to TTS.py")
else:
    print("BERT patch: already applied or not needed")
PYEOF
"$TTS_PY"

# Patch 3: Install numba no-op stub (prevents llvmlite LLVM ARM64 crash)
NUMBA_DIR="$(python3 -c 'import site; print(site.getsitepackages()[0])')/numba"
if [ ! -f "$NUMBA_DIR/__init__.py" ] || ! grep -q "ARM64" "$NUMBA_DIR/__init__.py" 2>/dev/null; then
    mkdir -p "$NUMBA_DIR"
    cat > "$NUMBA_DIR/__init__.py" << 'STUBEOF'
"""Minimal numba stub for ARM64 proot — avoids llvmlite LLVM machine model crash."""
def jit(func=None, *args, **kwargs):
    if func is not None and callable(func): return func
    return lambda f: f
def njit(func=None, *args, **kwargs): return jit(func, *args, **kwargs)
def stencil(func=None, *args, **kwargs):
    if func is not None and callable(func): return func
    return lambda f: f
def vectorize(*args, **kwargs):
    import numpy as np
    if len(args) == 1 and callable(args[0]): return np.vectorize(args[0])
    return lambda f: np.vectorize(f)
def guvectorize(*args, **kwargs):
    if len(args) == 1 and callable(args[0]): return args[0]
    return lambda f: f
class prange:
    def __new__(cls, *a): return range(*a)
class _T:
    int8=int; int16=int; int32=int; int64=int; float32=float; float64=float
    complex64=complex; complex128=complex; boolean=bool; uint8=int; uint32=int; uint64=int
    void=type(None)
    def __getattr__(self, n): return object
types = _T(); typed = object()
class _M:
    def __getattr__(self, n): return lambda *a, **k: None
core=_M(); cuda=_M(); np=_M()
__version__ = "0.65.1-stub-ARM64"
STUBEOF
    echo "numba stub installed at $NUMBA_DIR"
else
    echo "numba stub: already installed"
fi

echo ""
echo "All patches applied. Test: python3 \$HOME/parksy-tts-v1/say.py '안녕' --out /tmp/test.wav"
