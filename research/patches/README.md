# Local setup changes used for this run

Base application: debpalash/VoiceStudio tag v0.5.6.
These are local setup adaptations; they do not alter trained weights.

1. `01-lightweight-model-catalog.patch` registers the two Q8 GGUF files as
   required for this specific lightweight installation and makes the full
   default PyTorch model optional. It does not claim that absent files exist.
2. `02-saved-quant-preference.patch` connects the application's existing saved
   GGUF quantization preference to the engine constructor. The saved value for
   this run is `omnivoice-base-Q8_0.gguf`.
3. The AppImage did not include the GGUF runtime. It was compiled from the
   upstream runtime commit pinned in `model-manifest.json`; its ggml submodule
   commit is recorded there too.

The exact native build configuration was:

```sh
cmake -S omnivoice-cpp -B omnivoice-cpp/build \
  -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=ON \
  -DCMAKE_CUDA_ARCHITECTURES=86 \
  -DCMAKE_CUDA_HOST_COMPILER=/usr/bin/g++-12 \
  -DCMAKE_C_COMPILER=/usr/bin/gcc-12 \
  -DCMAKE_CXX_COMPILER=/usr/bin/g++-12 \
  -DBUILD_SHARED_LIBS=OFF -DGGML_CUDA_FA_ALL_QUANTS=OFF
cmake --build omnivoice-cpp/build --target omnivoice-tts -j 2
```

Build tools: CUDA toolkit 12.0.140, GCC/G++ 12.4, CMake 4.4.4. The generated
executable and a SHA-256 manifest were installed under the managed project's
`bin/` directory. The large compiled executable is not included in this report.
Runtime source: https://github.com/ServeurpersoCom/omnivoice.cpp

VoiceStudio restages its bundled Python sources on normal startup. Its supported
`OMNIVOICE_BACKEND_CMD` override was used to have Electron supervise the existing
locally adapted runtime, preserving these changes across restarts. The backend
listens on 127.0.0.1:3900. Revalidate these adaptations when changing app versions.

The saved voice is a 24 kHz mono PCM16 WAV with an exact reference transcript.
The UI accepted the original MP3 but the C++ reader rejected it; converting it
to WAV resolved that issue. Reference audio is omitted from this publication.

The patch context comes from VoiceStudio, licensed AGPL-3.0. Application and
model licenses are separate. See the upstream LICENSE and model card.
