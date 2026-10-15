#!/usr/bin/env python3
"""Render the existing VoiceStudio voice-cloning test set with Chatterbox V3."""
import csv, datetime, hashlib, json, os, pathlib, random, subprocess, threading, time, wave

ROOT = pathlib.Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
os.environ.setdefault("HF_HOME", str(PROJECT / "models/chatterbox-v3/hf_home"))
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

import numpy as np
import psutil
import soundfile as sf
import torch
from huggingface_hub import snapshot_download
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

MODEL_REVISION = "e2d6902dd4c1301892935d0a0277325551e8060e"
PACKAGE_REVISION = "5de7a54aa4e5e2baadb0182dde554908b48b85c2"
REFERENCE = pathlib.Path(os.environ["VOICE_REFERENCE"]).expanduser() if os.getenv("VOICE_REFERENCE") else None
SAMPLES = ROOT / "gpu-samples.csv"
stop_event = threading.Event()

def utc(): return datetime.datetime.now(datetime.timezone.utc).isoformat()

def gpu_sampler():
    with SAMPLES.open("w", newline="") as f:
        writer = csv.writer(f); writer.writerow(["timestamp_utc", "memory_used_mib", "memory_free_mib", "gpu_util_percent", "power_w"])
        while not stop_event.is_set():
            try:
                out = subprocess.check_output(["nvidia-smi", "--query-gpu=memory.used,memory.free,utilization.gpu,power.draw", "--format=csv,noheader,nounits"], text=True, stderr=subprocess.DEVNULL, timeout=3).strip()
                writer.writerow([utc(), *[x.strip() for x in out.split(",")]]); f.flush()
            except Exception:
                writer.writerow([utc(), "", "", "", ""]); f.flush()
            stop_event.wait(.25)

def pcm_metrics(path):
    data, sr = sf.read(path, dtype="float32", always_2d=True)
    return {"duration_seconds": len(data)/sr, "sample_rate_hz": sr, "channels": data.shape[1],
            "peak_dbfs": float(20*np.log10(max(float(np.max(np.abs(data))), 1e-12))),
            "rms_dbfs": float(20*np.log10(max(float(np.sqrt(np.mean(data**2))), 1e-12)))}

def main():
    if not torch.cuda.is_available(): raise RuntimeError("CUDA is unavailable; refusing to silently run on CPU")
    if REFERENCE is None: raise RuntimeError("Set VOICE_REFERENCE to your own local reference WAV; source recordings are not part of this bundle")
    if not REFERENCE.is_file(): raise FileNotFoundError(f"Voice reference not found: {REFERENCE}")
    cases = json.loads((PROJECT / "research/tests.json").read_text())
    manifest = {"model": "ResembleAI/chatterbox", "variant": "Chatterbox Multilingual V3", "model_revision": MODEL_REVISION,
                "code_revision": PACKAGE_REVISION, "runtime": {"python": __import__('sys').version, "torch": torch.__version__, "cuda": torch.version.cuda,
                "gpu": torch.cuda.get_device_name(0), "total_vram_bytes": torch.cuda.get_device_properties(0).total_memory},
                "reference_audio": "local user voice reference; not copied to this bundle or uploaded", "started_utc": utc(),
                "run_policy": "sequential; eight existing scripts; per-case seed applied to Python, NumPy and Torch; no retries",
                "timing_boundary": "model download and model load recorded separately; generation time includes reference conditioning and synthesis; WAV writing excluded",
                "language_mapping": {"01_code_switch": "hi (Hindi; script includes English code-switching)", "all other cases": "en"},
                "generation_settings": {"exaggeration": 0.5, "cfg_weight": 0.5, "temperature": 0.8, "repetition_penalty": 1.2, "min_p": 0.05, "top_p": 1.0}}
    (ROOT / "run-metadata.json").write_text(json.dumps(manifest, indent=2)+"\n")
    sampler = threading.Thread(target=gpu_sampler, daemon=True); sampler.start()
    try:
        start = time.perf_counter()
        model_dir = snapshot_download(repo_id="ResembleAI/chatterbox", revision=MODEL_REVISION,
            allow_patterns=["ve.pt", "t3_mtl23ls_v3.safetensors", "s3gen.pt", "grapheme_mtl_merged_expanded_v1.json", "conds.pt", "Cangjie5_TC.json"])
        manifest["model_download_seconds"] = time.perf_counter()-start
        (ROOT / "run-metadata.json").write_text(json.dumps(manifest, indent=2)+"\n")
        print(f"MODEL_FILES_READY download={manifest['model_download_seconds']:.1f}s", flush=True)
        start = time.perf_counter()
        model = ChatterboxMultilingualTTS.from_local(model_dir, "cuda", t3_model="v3")
        torch.cuda.synchronize()
        manifest["model_load_seconds"] = time.perf_counter()-start
        # Convert module-by-module through CPU to avoid transiently duplicating
        # full-precision weights in the 4 GiB address space.
        model.conds = None
        for name in ("t3", "s3gen", "ve"):
            module=getattr(model,name).to("cpu").half().to("cuda").eval()
            setattr(model,name,module)
            torch.cuda.empty_cache()
        torch.cuda.synchronize()
        manifest["model_disk_bytes"] = sum(p.stat().st_size for p in pathlib.Path(model_dir).iterdir() if p.is_file())
        print(f"MODEL_READY load={manifest['model_load_seconds']:.1f}s disk={manifest['model_disk_bytes']} bytes", flush=True)
        results_path=ROOT/"results.json"
        results=json.loads(results_path.read_text()) if results_path.exists() else []
        previous={r["id"]:r for r in results}
        for case in cases:
            target=ROOT/"audio"/(case["id"]+".wav")
            if previous.get(case["id"],{}).get("status")=="success":
                print(f"SKIP {case['id']} already has a successful result", flush=True)
                continue
            if target.exists(): raise FileExistsError(f"Refusing to overwrite {target}")
            seed=int(case["seed"]); random.seed(seed); np.random.seed(seed); torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats(0)
            lang="hi" if case["id"]=="01_code_switch" else "en"
            rec={k:v for k,v in case.items() if k!="text"}; rec.update({"characters":len(case["text"]), "word_count":len(case["text"].split()), "language_id":lang,
                "precision":"FP16 + autocast",
                "seed":seed, "started_utc":utc(), "available_ram_before_bytes":psutil.virtual_memory().available, "swap_used_before_bytes":psutil.swap_memory().used,
                "allocated_vram_before_bytes":torch.cuda.memory_allocated(0), "status":"running"})
            print(f"START {case['id']} chars={len(case['text'])} language={lang}", flush=True)
            start=time.perf_counter()
            try:
                with torch.inference_mode(), torch.autocast(device_type="cuda", dtype=torch.float16):
                    audio=model.generate(case["text"], language_id=lang, audio_prompt_path=str(REFERENCE))
                torch.cuda.synchronize(); rec["generation_seconds"]=time.perf_counter()-start
                audio_np=audio.squeeze().detach().cpu().numpy()
                sf.write(target, audio_np, model.sr, subtype="PCM_16")
                rec.update(pcm_metrics(target)); rec.update({"status":"success", "audio_file":f"audio/{target.name}", "file_bytes":target.stat().st_size,
                    "sha256":hashlib.sha256(target.read_bytes()).hexdigest(), "real_time_factor":rec["generation_seconds"]/rec["duration_seconds"],
                    "allocated_vram_peak_bytes":torch.cuda.max_memory_allocated(0), "reserved_vram_peak_bytes":torch.cuda.max_memory_reserved(0)})
                print(f"DONE {case['id']} generation={rec['generation_seconds']:.2f}s audio={rec['duration_seconds']:.2f}s allocated_peak={rec['allocated_vram_peak_bytes']/2**20:.0f}MiB", flush=True)
            except Exception as e:
                torch.cuda.synchronize() if torch.cuda.is_initialized() else None
                rec.update({"status":"failed", "generation_seconds":time.perf_counter()-start, "error":repr(e),
                    "allocated_vram_peak_bytes":torch.cuda.max_memory_allocated(0), "reserved_vram_peak_bytes":torch.cuda.max_memory_reserved(0)})
                print(f"FAILED {case['id']}: {e!r}", flush=True)
            rec["finished_utc"]=utc(); rec["available_ram_after_bytes"]=psutil.virtual_memory().available
            rec["comments_status"]="pending user listening review"; rec["user_comment"]=None
            if case["id"] in previous:
                old=previous[case["id"]]
                rec["attempt_history"] = old.get("attempt_history", []) + [{k:old.get(k) for k in ("status","generation_seconds","error","allocated_vram_peak_bytes","reserved_vram_peak_bytes")}]
                results=[r for r in results if r["id"]!=case["id"]]
            results.append(rec); previous[case["id"]]=rec
            results.sort(key=lambda r: next(i for i,c in enumerate(cases) if c["id"]==r["id"]))
            results_path.write_text(json.dumps(results,ensure_ascii=False,indent=2)+"\n")
            if rec["status"]!="success": break
        manifest["finished_utc"]=utc(); manifest["completed_cases"]=len(results); manifest["successful_cases"]=sum(x["status"]=="success" for x in results)
        manifest["inference_precision"]="FP16 model weights with CUDA FP16 autocast after initial FP32 out-of-memory failure"
        (ROOT/"run-metadata.json").write_text(json.dumps(manifest,indent=2)+"\n")
    finally:
        stop_event.set(); sampler.join(timeout=5)

if __name__=="__main__": main()
