# Local voice-cloning experiments on a 4 GB RTX 2050

Run started: 2026-10-15T03:45:17.026418+00:00. Voice: Jivraj. Research status: **generation measured; stress-test listening review pending**.

## Why this experiment

I wanted to find out whether a local voice-cloning model could reproduce my voice, how much hardware it needed, and where it might fail.

My initial comment, made before these stress tests:

> I loved the output of the model. It felt like my voice itself.

That comment applies to the earlier short clone. It is not a rating for the clips below.

## Setup

- App: VoiceStudio v0.5.6 Electron, with the local setup fixes described below.
- Model: k2-fsa/OmniVoice, converted as Serveurperso/OmniVoice-GGUF; Q8_0 language model and tokenizer.
- Runtime: omnivoice.cpp commit 886fc079838ca7400cb2b42b36e2a65aa1daabe8, compiled for CUDA sm_86.
- Hardware: Intel Core i5-12450H, approximately 16 GB system RAM, NVIDIA RTX 2050 with 4,096 MiB VRAM.
- Reference: 10.34 seconds, 24 kHz mono PCM16 WAV, with its exact transcript supplied.
- Reference recording is not included. Generated clips, prompts, seeds, hashes, and reference metadata are included.
- No model training or fine-tuning. All runs use the same saved voice reference.
- One request at a time, with a one-second gap. Different explicit seeds are used for the three consistency takes.
- Model files and app dependencies were already installed. Setup/download/compilation time is excluded.
- The native runtime launches a fresh process and reloads weights for each request. The application and watermark dependency were already warmed.

## Results

**8/8 HTTP requests succeeded.** Total generated audio: **5.64 minutes**. Sum of generation request wall times: **4.15 minutes**. This is one run per prompt, not a statistically stable benchmark.

| Test / audio | Request time | Audio length | RTF | Peak total GPU VRAM | Peak native-process VRAM |
|---|---:|---:|---:|---:|---:|
| [Hindi-English code-switching](audio/01_code_switch.wav) | 9.14 s | 10.76 s | 0.85 | 1596.00 MiB | 1504.00 MiB |
| [Numbers, dates, currency and abbreviations](audio/02_numbers.wav) | 10.28 s | 14.44 s | 0.71 | 1628.00 MiB | 1524.00 MiB |
| [Questions and emotion](audio/03_emotion.wav) | 8.60 s | 10.47 s | 0.82 | 1606.00 MiB | 1490.00 MiB |
| [Names and technical vocabulary](audio/04_names_technical.wav) | 8.48 s | 10.92 s | 0.78 | 1592.00 MiB | 1500.00 MiB |
| [Consistency take 1](audio/05_consistency_take_1.wav) | 25.62 s | 34.93 s | 0.73 | 1618.00 MiB | 1514.00 MiB |
| [Consistency take 2](audio/06_consistency_take_2.wav) | 26.16 s | 35.40 s | 0.74 | 1618.00 MiB | 1514.00 MiB |
| [Consistency take 3](audio/07_consistency_take_3.wav) | 26.14 s | 35.28 s | 0.74 | 1618.00 MiB | 1514.00 MiB |
| [Long narration](audio/08_long_narration.wav) | 134.31 s | 186.06 s | 0.72 | 1632.00 MiB | 1528.00 MiB |

RTF = request wall time / output duration. Below 1 means the complete request finished faster than the duration of its generated audio. It is not time-to-first-audio or proof of conversational latency.

Highest sampled total GPU usage: **1632 MiB (1.59 GiB)**. Highest single native speech process: **1528 MiB (1.49 GiB)**.

## How VRAM and time were measured

- NVIDIA telemetry sampled at a target interval of 200 ms; raw CSV files are included. A shorter allocation spike may be missed.
- Total GPU memory includes every GPU application. Native-process VRAM is separately sampled for the omnivoice-tts process and includes CUDA context, weights and buffers.
- Per-test baseline is the median GPU memory in the preceding 0.8 seconds, with a five-second fallback window. Peak above baseline is available in results.csv.
- Timing begins immediately before the HTTP POST and ends when the full response body reaches the client. It includes server work, loading, postprocessing, watermarking and transfer; output-file writing/analysis is excluded.
- No GPU-memory polling ran inside the synthesis process. An external nvidia-smi process collected the samples.
- WAV decoding, RMS level, peak level and quiet frames were checked. These checks cannot establish intelligibility, likeness, emotion or correct pronunciation.

## Automatic observations

All 8 successful responses decoded as WAV. Maximum observed clipped-sample fraction across clips: 0.000000. These waveform checks do not score content accuracy.

The emotion clip has about 25.4% quiet 20 ms frames below -50 dBFS, versus about 2.4–6.8% for the other clips. Its script contains an explicit hesitation; listening is needed to decide whether the pauses are natural or excessive.

The 3 consistency takes last 34.93–35.40 seconds and took 25.62–26.16 seconds to generate. Duration and speed do not establish identity or pronunciation consistency.

## What to listen for / my comments

Open [the listening worksheet](index.html) in a browser for audio players, ratings and comments. It saves review drafts locally in that browser; use **Export my reviews** to save a JSON file for the repository. Until listening review is complete, ratings remain empty.

### Hindi-English code-switching

[Listen](audio/01_code_switch.wav) · [Exact script](prompts/01_code_switch.txt)

Listen for accent changes, pronunciation of English words inside Hindi, skipped words, and preservation of speaker identity.

**My comment:** pending listening review.

### Numbers, dates, currency and abbreviations

[Listen](audio/02_numbers.wav) · [Exact script](prompts/02_numbers.txt)

Check October twenty-first, nine forty-five A.M., the rupee amount including fifty paise, and G-S-T. Alternate natural readings are acceptable if the value stays correct.

**My comment:** pending listening review.

### Questions and emotion

[Listen](audio/03_emotion.wav) · [Exact script](prompts/03_emotion.txt)

Listen for a questioning first phrase, excitement, a pause, and concern. Punctuation alone is being tested; no emotion tags or style instructions are supplied.

**My comment:** pending listening review.

### Names and technical vocabulary

[Listen](audio/04_names_technical.wav) · [Exact script](prompts/04_names_technical.txt)

Check your name, PostgreSQL, Kubernetes, ElevenLabs, NVIDIA, R-T-X and the model number. Note spelling-out, omissions or odd stress.

**My comment:** pending listening review.

### Consistency take 1

[Listen](audio/05_consistency_take_1.wav) · [Exact script](prompts/05_consistency_take_1.txt)

Compare takes 1–3 for identity, accent, pacing, completeness and noise. Different explicit seeds test variation across sampled takes.

**My comment:** pending listening review.

### Consistency take 2

[Listen](audio/06_consistency_take_2.wav) · [Exact script](prompts/06_consistency_take_2.txt)

Compare against the identical script in takes 1 and 3; seed is the only requested generation setting changed.

**My comment:** pending listening review.

### Consistency take 3

[Listen](audio/07_consistency_take_3.wav) · [Exact script](prompts/07_consistency_take_3.txt)

Compare against takes 1 and 2. Different WAV hashes alone do not establish an audible difference.

**My comment:** pending listening review.

### Long narration

[Listen](audio/08_long_narration.wav) · [Exact script](prompts/08_long_narration.txt)

Listen for voice drift, paragraph joins, missing or repeated sentences, uneven pacing, unnatural pauses, and whether the final paragraph still sounds like you.

**My comment:** pending listening review.

## How much did we pay?

| Item | Amount |
|---|---:|
| VoiceStudio software / Pro subscription | $0 |
| Hosted inference / ElevenLabs API charges | $0 |
| New hardware purchased for this experiment | $0 |
| Electricity cost | Not measured / not allocated |

We used an existing laptop. “$0 paid in software/API fees” does not mean zero electricity, free hardware, or zero setup time.

The integral of sampled GPU-reported power during the request windows is approximately **2.850 Wh**. This is an estimate for the GPU component only, not wall power or total laptop energy. It excludes CPU, display, charger losses, setup, and idle gaps. No electricity tariff was supplied, so no electricity charge is claimed.

For a known tariff: estimated GPU-component cost = energy in Wh / 1,000 × tariff per kWh. This remains only part of the machine’s operating cost.

### Hypothetical ElevenLabs comparison

The scripts total **2,767 Unicode characters**, including repeated takes. At a model rate of one credit per character, that would be **2,767 credits**. Allocating the normal Starter price ($6 / 30,000 credits) gives approximately **$0.55 of monthly allowance**. This is not an actual charge or a pay-as-you-go quote. Rates vary by model, and regeneration rules may differ.

The normal minimum monthly purchase for Instant Voice Cloning is Starter at $6 before taxes; offers or annual billing may change the purchase price. We bought no plan, sent no clips to ElevenLabs, and did not test its output. No quality-equivalence or demonstrated savings claim is made.

[ElevenLabs pricing, checked 15 October 2026](https://elevenlabs.io/pricing).

## Known setup friction and limitations

- The shipped Linux AppImage omitted its native GGUF executable. It was built from the exact pinned source commit with CUDA support.
- The setup gate required the full default model. A local catalog patch registers the downloaded quantized model instead.
- A local constructor patch connects the saved quantization preference. Both patches are in patches/. They are setup changes, not a new trained model.
- An MP3 reference was accepted by the UI but rejected by the native WAV reader. Converting the recording to WAV resolved that failure. The earlier failure and setup work are not included in the eight timed tests.
- System memory was already under pressure and swap was nearly full. This is a real laptop session, not an otherwise-idle laboratory benchmark.
- HTTP success and audio duration do not establish spoken-content correctness. Transcript accuracy, voice drift, and expressiveness remain pending listening review.
- No statistical repetitions except the three consistency takes, whose seeds intentionally differ. They do not measure fixed-seed reproducibility.
- No other models, quantization levels, GPUs or hosted providers were benchmarked.
- Upstream OmniVoice weights carry non-commercial terms. A GGUF conversion or the app’s AGPL license does not remove upstream restrictions.

## Reproduce

1. Use VoiceStudio v0.5.6 with the pinned runtime and Q8 files listed in model-manifest.json; review patches/README.md.
2. Create an authorized saved voice with a short PCM WAV and its exact transcript. The original reference is omitted, so exact replication of this speaker requires separately providing that recording.
3. Copy run_experiment.py, analyse_telemetry.py, build_report.py, tests.json and reference-metadata.json to a fresh run folder with empty audio/ and prompts/ subfolders; install requests, numpy and psutil in your chosen Python environment.
4. Save each test text under prompts/<id>.txt. Run the two telemetry commands below in separate terminals, then run the experiment. Stop telemetry after the last case.

```sh
nvidia-smi --query-gpu=timestamp,index,name,memory.total,memory.used,utilization.gpu,power.draw --format=csv,noheader,nounits --loop-ms=200 --filename=gpu-samples.csv
nvidia-smi --query-compute-apps=timestamp,pid,process_name,used_gpu_memory --format=csv,noheader,nounits --loop-ms=200 --filename=gpu-process-samples.csv
python3 run_experiment.py --base-url http://127.0.0.1:3900 --profile-id YOUR_PROFILE_ID
python3 analyse_telemetry.py
python3 build_report.py
```

Keep NVIDIA timestamps and Python request times in the same system timezone. The telemetry analyser interprets NVIDIA timestamps in the host’s local timezone.

## Files

- audio/: eight generated WAV clips.
- prompts/: exact UTF-8 scripts and request bodies.
- results.csv / results.json: per-test measurements and listening prompts.
- summary.json / run-metadata.json / model-manifest.json: totals, environment and checksums.
- gpu-samples.csv / gpu-process-samples.csv: raw GPU telemetry.
- index.html: offline listening and review worksheet.
- reviews-template.json: empty fields for per-clip human review.
- patches/: local app setup patches and build notes.

## Sources

- [Original OmniVoice model and model terms](https://huggingface.co/k2-fsa/OmniVoice)
- [GGUF conversion](https://huggingface.co/Serveurperso/OmniVoice-GGUF)
- [Native runtime](https://github.com/ServeurpersoCom/omnivoice.cpp)
- [VoiceStudio release v0.5.6](https://github.com/debpalash/VoiceStudio/releases/tag/v0.5.6)
- [ElevenLabs pricing](https://elevenlabs.io/pricing)

## Second model: Chatterbox Multilingual V3

The same eight scripts and local voice reference were also tested with upstream Chatterbox V3. The user's overall listening verdict is that Chatterbox was not good and OmniVoice did better in several respects; the specific dimensions have not yet been recorded. All outputs, timings, VRAM measurements, retries, limitations, and a side-by-side listening page are in [`chatterbox-v3/README.md`](chatterbox-v3/README.md) and [`chatterbox-v3/index.html`](chatterbox-v3/index.html).
