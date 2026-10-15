# Chatterbox Multilingual V3 voice-cloning run

Run date: 2026-10-15. All eight prompts in [`../tests.json`](../tests.json) were synthesized from the same local voice reference used for the OmniVoice baseline. The reference file itself was not copied into this folder or uploaded. **Audio quality and voice similarity are awaiting the user's listening review.**

Use [`index.html`](index.html) for side-by-side audio players and the exact scripts, or inspect the [machine-readable results](results.json) and [CSV summary](results.csv).

| Case | Synthesis time | Audio length | Peak PyTorch allocation | Precision |
|---|---:|---:|---:|---|
| Hindi-English code-switching | 18.33 s | 6.04 s | 3,284 MiB | FP32 |
| Numbers, dates and currency | 9.59 s | 8.52 s | 3,332 MiB | FP32 |
| Questions and emotion | 5.03 s | 4.00 s | 3,247 MiB | FP32 |
| Names and technical vocabulary | 8.58 s | 7.76 s | 3,316 MiB | FP32 |
| Consistency take 1 | 17.04 s | 14.52 s | 3,478 MiB | FP32 |
| Consistency take 2 | 12.66 s | 18.72 s | 1,883 MiB | FP16 + autocast |
| Consistency take 3 | 9.26 s | 16.28 s | 1,835 MiB | FP16 + autocast |
| Long narration | 31.03 s | 39.96 s | 2,473 MiB | FP16 + autocast |

Across eight successful outputs, synthesis took **111.53 seconds** and produced **115.80 seconds** of audio. This is one run per script and not a stable performance benchmark. Synthesis timing includes reference-audio conditioning and generation, but excludes writing and analyzing the WAV file. Output is mono PCM16 at 24 kHz.

## Hardware, installation and cost

- GPU: NVIDIA GeForce RTX 2050, 4,096 MiB physical VRAM; PyTorch reports 3.68 GiB available to CUDA. Host: Intel Core i5-12450H, 16 GB RAM.
- The model snapshot occupied **3,208,952,137 bytes** (about 2.99 GiB). Initial public model download took **217.4 seconds**; first FP32 model load took **12.3 seconds**. The FP16 retry loaded the model in 10.5 seconds, then converted model modules; conversion time was not separately timed.
- The highest per-case PyTorch allocated-memory counter was **3,478 MiB** in the FP32 phase. The long narration used **2,473 MiB** after switching to FP16 weights with CUDA FP16 autocast. PyTorch allocation excludes some CUDA context/driver memory. The retained `nvidia-smi` sample CSV covers the FP16 retry phase only; it peaked at 3,252 MiB total GPU usage.
- **Cost for this experiment: $0.** It ran locally; no paid API or NVIDIA NIM endpoint was used. Public model assets were downloaded from Hugging Face. No cloud synthesis or LLM grading was used.
- This is the upstream [Resemble AI Chatterbox implementation](https://github.com/resemble-ai/chatterbox), pinned to code commit `5de7a54aa4e5e2baadb0182dde554908b48b85c2` and model snapshot `e2d6902dd4c1301892935d0a0277325551e8060e`. This is **not** a run of NVIDIA's NIM container. NVIDIA's published TTS NIM support matrix lists 16 GB VRAM as the minimum for the Chatterbox Multilingual NIM, so the 4 GB RTX 2050 is below that requirement: [NVIDIA support matrix](https://docs.nvidia.com/nim/speech/26.10.0/reference/support-matrix/tts.html). NVIDIA's catalog lists the NIM launch in June 2026: [NGC catalog](https://catalog.ngc.nvidia.com/orgs/nim/nvidia/containers/chatterbox-tts-multilingual).

## VRAM limit and precision change

The first five cases completed with FP32 weights. The sixth case failed because the GPU had only 37 MiB free when synthesis requested another 64 MiB. Two more recovery attempts also failed: FP32 autocast still ran out of VRAM, and FP16 weights without autocast hit a float/half tensor mismatch. The successful retry used FP16 weights plus CUDA FP16 autocast; it completed takes 2 and 3 and the long narration. The failed attempts are retained in `attempt_history` for case 6 in `results.json`.

Because precision changed after the first five files, this is a useful local capability check, but it is **not a fully controlled same-precision comparison**. Consider re-running all eight cases in FP16 + autocast on a machine with enough VRAM if strict parity matters. The script records that mixed precision and supports resuming successful cases.

The model returned a full-scale peak in each PCM16 file. Samples at the maximum represent **0.013%–0.146%** of samples per clip, depending on the case. Listen for harshness or crackling; the counts alone do not establish audible clipping.

## Reproduce

The isolated environment and model files live under ignored `setup/` and `models/` folders, not in this research bundle. To rerun locally, set `VOICE_REFERENCE` to your own reference WAV before invoking [`run.py`](run.py); build the A/B player with [`build_comparison.py`](build_comparison.py). Prompts, seeds, generation settings, timing, GPU counters, hashes and run metadata are included here. The listening page stores note drafts in browser local storage only.

## Review status

The user's initial listening verdict: **Chatterbox was not good overall; OmniVoice was better at a number of things.** The specific dimensions and per-clip ratings have not yet been recorded. Compare voice identity, Hindi/English transitions, number reading, pronunciation, emotion, consistency across the repeated script, and drift/omissions in the long narration. Do not treat audio duration, file hashes or waveform statistics as a voice-quality score.
