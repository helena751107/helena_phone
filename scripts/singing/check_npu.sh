#!/bin/bash
# check_npu.sh — S21 Exynos NPU / ONNX EP 가용성 진단
# proot-Ubuntu와 Termux native 양쪽에서 실행 가능
# 실행: bash check_npu.sh

set -e
VENV="${HOME}/browser-env"
PYTHON="${VENV}/bin/python3"

echo "========================================"
echo " S21 NPU / ONNX 가용성 진단"
echo " $(date)"
echo "========================================"

echo ""
echo "[1] 환경 확인"
echo "  uname: $(uname -m)"
echo "  OS: $(uname -s)"
echo "  Python: $($PYTHON --version 2>&1 || echo '없음')"

echo ""
echo "[2] onnxruntime Execution Providers"
$PYTHON - <<'PYEOF'
try:
    import onnxruntime as ort
    providers = ort.get_available_providers()
    print(f"  onnxruntime {ort.__version__}")
    print(f"  사용 가능한 EP: {providers}")

    # NNAPI 확인
    if 'NNAPIExecutionProvider' in providers:
        print("  ✅ NNAPI EP 사용 가능 → Exynos NPU 가속 가능!")
    else:
        print("  ⚠️  NNAPI EP 없음 (Linux ARM64 pip 빌드 - 예상된 결과)")

    # XNNPACK 확인
    if 'XNNPACKExecutionProvider' in providers:
        print("  ✅ XNNPACK EP 사용 가능 → ARM NEON 가속")
    else:
        print("  ℹ️  XNNPACK 없음 (CPU만 사용)")

    # fp16 지원 확인
    import numpy as np
    fp16_ok = hasattr(np, 'float16')
    print(f"  {'✅' if fp16_ok else '❌'} fp16 numpy 지원")

except ImportError:
    print("  ❌ onnxruntime 없음 → pip install onnxruntime")
PYEOF

echo ""
echo "[3] Android NNAPI 라이브러리 직접 확인"
NNAPI_LIB="/system/lib64/libnnapi_implementation.so"
if [ -f "$NNAPI_LIB" ]; then
    echo "  ✅ $NNAPI_LIB 존재"
    echo "  → onnxruntime Android 빌드 시 이 라이브러리 사용 가능"
else
    # ARM32 경로도 확인
    NNAPI_LIB32="/system/lib/libnnapi_implementation.so"
    if [ -f "$NNAPI_LIB32" ]; then
        echo "  ✅ $NNAPI_LIB32 존재 (ARM32)"
    else
        echo "  ⚠️  NNAPI 라이브러리를 찾을 수 없음"
        echo "     (proot 격리 환경에서는 /system 접근이 제한될 수 있음)"
    fi
fi

echo ""
echo "[4] Exynos NPU 직접 확인"
for lib in /system/lib64/libeden_model.so /system/lib64/libExynosNNFramework.so \
           /vendor/lib64/libsapu_loc_lib_sec.so /vendor/lib64/libNNSRT.so; do
    if [ -f "$lib" ]; then
        echo "  ✅ $lib"
    fi
done

echo ""
echo "[5] DiffSinger 모델 파일 확인"
$PYTHON - <<'PYEOF'
from pathlib import Path
files = {
    'parksy_ko_v1.onnx': Path.home() / 'DiffSinger/parksy_onnx/parksy_ko_v1.onnx',
    'PARKSY_DS 보이스뱅크': Path.home() / '.local/share/OpenUtau/Singers/PARKSY_DS',
    'helena_rvc.pth': Path.home() / 'rvc_models/helena_rvc/helena_rvc.pth',
    'helena_rvc.index': Path.home() / 'rvc_models/helena_rvc/helena_rvc.index',
    'NSF-HiFiGAN': Path.home() / 'DiffSinger/checkpoints/pc_nsf_hifigan_44.1k_hop512_128bin_2025.02',
}
for name, path in files.items():
    exists = path.exists()
    size = ''
    if exists and path.is_file():
        size = f' ({path.stat().st_size // 1024 // 1024}MB)'
    print(f"  {'✅' if exists else '❌'} {name}{size}: {path}")
PYEOF

echo ""
echo "[6] 성능 벤치마크 (onnxruntime CPU, fp32 vs fp16)"
$PYTHON - <<'PYEOF'
import time, numpy as np
try:
    import onnxruntime as ort

    # 간단한 행렬곱으로 CPU 성능 측정
    N = 512
    a = np.random.randn(N, N).astype(np.float32)
    b = np.random.randn(N, N).astype(np.float32)

    t0 = time.time()
    for _ in range(10):
        c = a @ b
    t_fp32 = (time.time() - t0) / 10 * 1000

    a16 = a.astype(np.float16)
    b16 = b.astype(np.float16)
    t0 = time.time()
    for _ in range(10):
        c = a16 @ b16
    t_fp16 = (time.time() - t0) / 10 * 1000

    print(f"  numpy {N}x{N} GEMM:")
    print(f"    fp32: {t_fp32:.1f}ms")
    print(f"    fp16: {t_fp16:.1f}ms (speedup {t_fp32/t_fp16:.1f}x)")

    # CPU 코어 수
    import multiprocessing
    print(f"  CPU 코어: {multiprocessing.cpu_count()}개")

except Exception as e:
    print(f"  벤치마크 실패: {e}")
PYEOF

echo ""
echo "========================================"
echo " 진단 완료"
echo ""
echo " Exynos NPU 가속 로드맵:"
echo "  즉시: fp16 + steps=10 (CPU, 검증됨)"
echo "  1주:  onnxruntime Android AAR → ctypes (NNAPI)"
echo "  2주:  DiffSingerMiniEngine ARM64 C++ 빌드"
echo "========================================"
