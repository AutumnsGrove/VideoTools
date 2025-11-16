# Model Setup Guide - VideoTools MCP Server

**Issue Summary from Test Run:**
1. ❌ Parakeet model not loading (returns None)
2. ❌ Pyannote missing AudioDecoder (torchcodec issue)
3. ⚠️  No HuggingFace token in config

This guide provides step-by-step commands to fix these issues.

---

## Step 1: HuggingFace Authentication

### Check Current Status
```bash
huggingface-cli whoami
```

### If Not Authenticated
```bash
# Login interactively
huggingface-cli login
```

You'll need a HuggingFace token from: https://huggingface.co/settings/tokens

### Accept Required Model Licenses

**Required for Pyannote (speaker diarization):**

Visit these URLs while logged in and accept the terms:
1. https://huggingface.co/pyannote/speaker-diarization-3.1
2. https://huggingface.co/pyannote/segmentation-3.0

### Add Token to secrets.json

```bash
# Create/update secrets.json
cat > secrets.json << 'EOF'
{
  "huggingface_token": "hf_YOUR_TOKEN_HERE",
  "anthropic_api_key": "sk-ant-api03-...",
  "openrouter_api_key": "sk-or-v1-..."
}
EOF
```

**Get your token:**
```bash
# Copy token from CLI login
huggingface-cli whoami
```

---

## Step 2: Fix Parakeet Model Loading Issue

The Parakeet model isn't loading because the model files aren't downloaded yet.

### Download Parakeet Model Manually

```bash
# Test Parakeet model loading
uv run python << 'EOF'
from video_tools_mcp.models.parakeet import ParakeetModel

print("Initializing Parakeet model...")
model = ParakeetModel()

print("Loading model (this will download ~600MB on first run)...")
model.load()

if model._model is not None:
    print("✅ SUCCESS: Parakeet model loaded!")
    print(f"Model type: {type(model._model)}")
else:
    print("❌ FAILED: Model is still None")

print(f"Model loaded: {model._loaded}")
EOF
```

**Expected output:**
```
Initializing Parakeet model...
Loading model (this will download ~600MB on first run)...
[Progress bar for model download]
✅ SUCCESS: Parakeet model loaded!
Model type: <class 'parakeet_mlx.model.ParakeetModel'>
Model loaded: True
```

### If Download Fails

Try downloading the model directly:
```bash
# Clone the model repository
mkdir -p ~/.cache/parakeet-mlx
cd ~/.cache/parakeet-mlx

# Download using huggingface-cli
huggingface-cli download nvidia/parakeet-tdt-0.6b --local-dir parakeet-tdt-0.6b
```

---

## Step 3: Fix Pyannote AudioDecoder Issue

The error "NameError: name 'AudioDecoder' is not defined" is caused by missing torchcodec.

### Option A: Install Compatible FFmpeg (Recommended)

```bash
# Install FFmpeg 6 via Homebrew (macOS)
brew install ffmpeg@6

# Link it if not auto-linked
brew link ffmpeg@6
```

### Option B: Reinstall torchcodec

```bash
# Reinstall with proper dependencies
uv pip uninstall torchcodec
uv pip install torchcodec

# Verify installation
uv run python -c "import torchcodec; print(f'torchcodec version: {torchcodec.__version__}')"
```

### Option C: Use Pre-loaded Audio (Workaround)

If torchcodec issues persist, we can modify the code to use our own audio extraction (which works with ffmpeg-python).

**Check if FFmpeg is available:**
```bash
ffmpeg -version
```

---

## Step 4: Download Pyannote Models

```bash
# Test Pyannote model loading
uv run python << 'EOF'
import os
from video_tools_mcp.models.pyannote import PyannoteModel

# Load token from secrets.json
import json
with open('secrets.json', 'r') as f:
    secrets = json.load(f)
    hf_token = secrets.get('huggingface_token')

if hf_token:
    os.environ['HUGGINGFACE_TOKEN'] = hf_token
    print(f"✅ HuggingFace token loaded: {hf_token[:10]}...")
else:
    print("❌ No HuggingFace token in secrets.json")
    exit(1)

print("\nInitializing Pyannote model...")
model = PyannoteModel()

print("Loading model (this will download ~500MB on first run)...")
model.ensure_loaded()

if model._pipeline is not None:
    print("✅ SUCCESS: Pyannote model loaded!")
    print(f"Pipeline type: {type(model._pipeline)}")
else:
    print("❌ FAILED: Pipeline is still None")

print(f"Model loaded: {model._loaded}")
EOF
```

---

## Step 5: Download Qwen VL Model

```bash
# Test Qwen VL model loading
uv run python << 'EOF'
from video_tools_mcp.models.qwen_vl import QwenVLModel

print("Initializing Qwen VL model...")
model = QwenVLModel()

print("Loading model (this will download ~4-8GB on first run)...")
print("This may take 10-20 minutes...")
model.load()

if model._model is not None:
    print("✅ SUCCESS: Qwen VL model loaded!")
    print(f"Model type: {type(model._model)}")
else:
    print("❌ FAILED: Model is still None")

print(f"Model loaded: {model._loaded}")
EOF
```

---

## Step 6: Verify All Models

```bash
# Run comprehensive model check
uv run python << 'EOF'
import json
import os

# Load HF token
with open('secrets.json', 'r') as f:
    secrets = json.load(f)
    hf_token = secrets.get('huggingface_token')
    if hf_token:
        os.environ['HUGGINGFACE_TOKEN'] = hf_token

print("=" * 60)
print("Model Verification")
print("=" * 60)

# Test 1: Parakeet
print("\n1. Testing Parakeet (Transcription)...")
try:
    from video_tools_mcp.models.parakeet import ParakeetModel
    model = ParakeetModel()
    model.load()
    if model._model is not None:
        print("   ✅ Parakeet: READY")
    else:
        print("   ❌ Parakeet: FAILED TO LOAD")
except Exception as e:
    print(f"   ❌ Parakeet: ERROR - {e}")

# Test 2: Pyannote
print("\n2. Testing Pyannote (Speaker Diarization)...")
try:
    from video_tools_mcp.models.pyannote import PyannoteModel
    model = PyannoteModel()
    model.ensure_loaded()
    if model._pipeline is not None:
        print("   ✅ Pyannote: READY")
    else:
        print("   ❌ Pyannote: FAILED TO LOAD")
except Exception as e:
    print(f"   ❌ Pyannote: ERROR - {e}")

# Test 3: Qwen VL
print("\n3. Testing Qwen VL (Vision Analysis)...")
try:
    from video_tools_mcp.models.qwen_vl import QwenVLModel
    model = QwenVLModel()
    model.load()
    if model._model is not None:
        print("   ✅ Qwen VL: READY")
    else:
        print("   ❌ Qwen VL: FAILED TO LOAD")
except Exception as e:
    print(f"   ❌ Qwen VL: ERROR - {e}")

print("\n" + "=" * 60)
print("Verification Complete")
print("=" * 60)
EOF
```

**Expected output:**
```
============================================================
Model Verification
============================================================

1. Testing Parakeet (Transcription)...
   ✅ Parakeet: READY

2. Testing Pyannote (Speaker Diarization)...
   ✅ Pyannote: READY

3. Testing Qwen VL (Vision Analysis)...
   ✅ Qwen VL: READY

============================================================
Verification Complete
============================================================
```

---

## Step 7: Run Integration Tests

Once all models are ready:

```bash
# Run fast tests (should pass now)
uv run pytest tests/integration/ -v -k "error or invalid or cleanup or range" --tb=short

# Run one full test
uv run pytest tests/integration/test_speaker_diarization_integration.py::TestBasicSpeakerDiarization::test_single_speaker_video_diarization -v -s

# Run all speaker diarization tests
uv run pytest tests/integration/test_speaker_diarization_integration.py -v --tb=short
```

---

## Troubleshooting Common Issues

### Issue 1: Parakeet Model Returns None

**Symptom:** `AttributeError: 'NoneType' object has no attribute 'transcribe'`

**Fix:**
```bash
# Clear cache and reinstall
rm -rf ~/.cache/parakeet-mlx
uv pip uninstall parakeet-mlx
uv pip install parakeet-mlx

# Try loading again
uv run python -c "from video_tools_mcp.models.parakeet import ParakeetModel; m = ParakeetModel(); m.load(); print('Loaded:', m._model is not None)"
```

### Issue 2: AudioDecoder Not Defined

**Symptom:** `NameError: name 'AudioDecoder' is not defined`

**Fix:**
```bash
# Check FFmpeg version
ffmpeg -version | head -1

# Should show version 4, 5, 6, 7, or 8
# If not, install:
brew install ffmpeg

# Reinstall torchcodec
uv pip install --force-reinstall --no-cache-dir torchcodec
```

### Issue 3: HuggingFace 401 Unauthorized

**Symptom:** `401 Client Error` when loading Pyannote

**Fix:**
1. Ensure you've accepted model licenses (see Step 1)
2. Check token is in secrets.json
3. Verify token has read permissions

```bash
# Test token
huggingface-cli whoami

# Ensure environment variable is set when testing
export HUGGINGFACE_TOKEN=$(python -c "import json; print(json.load(open('secrets.json'))['huggingface_token'])")
```

### Issue 4: Out of Memory

**Symptom:** Process killed during model loading

**Fix:**
- Load one model at a time
- Close other applications
- Use smaller test videos
- Consider using 4-bit quantized models

---

## Quick Reference Commands

```bash
# 1. Setup HuggingFace
huggingface-cli login
# Accept licenses at URLs above

# 2. Create secrets.json
cat > secrets.json << 'EOF'
{"huggingface_token": "hf_YOUR_TOKEN"}
EOF

# 3. Download all models
uv run python << 'EOF'
import os, json
with open('secrets.json') as f:
    os.environ['HUGGINGFACE_TOKEN'] = json.load(f)['huggingface_token']

from video_tools_mcp.models.parakeet import ParakeetModel
from video_tools_mcp.models.pyannote import PyannoteModel
from video_tools_mcp.models.qwen_vl import QwenVLModel

print("Loading Parakeet...")
ParakeetModel().load()

print("Loading Pyannote...")
PyannoteModel().ensure_loaded()

print("Loading Qwen VL...")
QwenVLModel().load()

print("✅ All models ready!")
EOF

# 4. Run tests
uv run pytest tests/integration/ -v -k "error or invalid"
```

---

## Disk Space Requirements

| Model | Download Size | Installed Size | Cache Location |
|-------|--------------|----------------|----------------|
| Parakeet TDT | ~600MB | ~1.2GB | ~/.cache/parakeet-mlx |
| Pyannote | ~500MB | ~1GB | ~/.cache/huggingface/hub |
| Qwen VL 8B | ~4GB | ~8GB | ~/.cache/huggingface/hub |
| **Total** | **~5GB** | **~10GB** | |

---

## Expected Timeline

| Task | First Time | Subsequent |
|------|-----------|------------|
| HuggingFace setup | 2-5 min | instant |
| Parakeet download | 5-10 min | instant |
| Pyannote download | 5-10 min | instant |
| Qwen VL download | 10-20 min | instant |
| Test run (all fast) | 15-30 min | 15-30 min |
| **Total first run** | **~40-60 min** | **~15-30 min** |

---

## Next Steps After Models Are Ready

1. Run fast tests to verify everything works
2. Run full integration test suite
3. Document performance benchmarks
4. Run slow tests (long videos) if desired

---

**Last Updated:** 2025-11-15
**Status:** Ready for model installation
