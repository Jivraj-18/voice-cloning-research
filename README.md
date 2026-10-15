# Voice cloning: local model research

A small, personal comparison of two local voice-cloning setups: **Serveurperso/OmniVoice-GGUF Q8_0** (base model `k2-fsa/OmniVoice`) and **ResembleAI/chatterbox Multilingual V3**. Both used the same eight scripts and the same reference recording, now included at [research/reference-input.wav](research/reference-input.wav) for reproducibility. This is the author's real voice; publishing it makes that recording public.

## Listening results

The author's first short OmniVoice result felt like his own voice. After listening to the matched Chatterbox clips, his overall view was that **Chatterbox was not good and OmniVoice did better at several things**. The exact dimensions and per-clip notes remain to be recorded, so the reports separate measured facts from that subjective verdict.

- [Open the project listening hub](https://jivraj-18.github.io/voice-cloning-research/)
- [Listen to the OmniVoice stress-test set](research/index.html)
- [Compare OmniVoice and Chatterbox side by side](research/chatterbox-v3/index.html)
- [Chatterbox test report, timings, memory and caveats](research/chatterbox-v3/README.md)
- [OmniVoice test report](research/README.md)

## What was run

Eight matched prompts cover Hindi-English code-switching, dates and currency, emotion, technical terms, three identical consistency takes with changed seeds, and a long narration. The Chatterbox run produced 115.8 seconds of audio in 111.5 seconds of synthesis time. Peak PyTorch allocation reached 3,478 MiB on an RTX 2050 with 4 GB VRAM. The first five clips used FP32; the remaining three required FP16 weights with autocast after full precision ran out of memory. Treat this as a practical local test, not a controlled same-precision quality benchmark.

This used the upstream Chatterbox package and model snapshot, not NVIDIA's NIM container. No paid synthesis or cloud evaluator was used. The model reference audio stayed on the local machine.

See each report for source revisions, exact prompts, outputs, hashes, metrics, limitations, and reproducibility details.
