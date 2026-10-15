#!/usr/bin/env python3
"""Build a per-case model, quality-listening, and resource comparison page."""
import csv, datetime, html, json, pathlib

HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parent
cases=json.loads((ROOT/"tests.json").read_text())
chatterbox=json.loads((HERE/"results.json").read_text())
omni_rows={r["id"]:r for r in csv.DictReader((ROOT/"results.csv").open())}
omni_manifest=json.loads((ROOT/"model-manifest.json").read_text())
cb_manifest=json.loads((HERE/"model-manifest.json").read_text())
cb_results={r["id"]:r for r in chatterbox}
samples=list(csv.DictReader((HERE/"gpu-samples-fp16-retry.csv").open()))

def mib(n): return f"{n/2**20:,.1f} MiB"
def seconds(n): return f"{float(n):.2f} s"
def metric(label,value): return f"<dt>{html.escape(label)}</dt><dd>{html.escape(str(value))}</dd>"
def cb_telemetry(r):
    start=datetime.datetime.fromisoformat(r["started_utc"]); end=datetime.datetime.fromisoformat(r["finished_utc"])
    rows=[]
    for sample in samples:
        try:
            stamp=datetime.datetime.fromisoformat(sample["timestamp_utc"])
            if start <= stamp <= end: rows.append(sample)
        except (ValueError,KeyError): pass
    if not rows: return {"sample_count":0}
    mem=[int(x["memory_used_mib"]) for x in rows if x["memory_used_mib"]]
    util=[float(x["gpu_util_percent"]) for x in rows if x["gpu_util_percent"]]
    watts=[float(x["power_w"]) for x in rows if x["power_w"]]
    points=[]
    for sample in rows:
        try: points.append((datetime.datetime.fromisoformat(sample["timestamp_utc"]),float(sample["power_w"])))
        except (ValueError,KeyError): pass
    energy_wh=sum((b[0]-a[0]).total_seconds()*(a[1]+b[1])/2/3600 for a,b in zip(points,points[1:]))
    return {"sample_count":len(rows),"sampled_total_gpu_peak_mib":max(mem) if mem else None,
            "mean_gpu_utilization_pct":sum(util)/len(util) if util else None,"peak_board_power_w":max(watts) if watts else None,
            "sampled_board_energy_estimate_wh":energy_wh if len(points)>1 else None}

omni_files=omni_manifest["files"]
omni_base=omni_files["omnivoice-base-Q8_0.gguf"]["bytes"]
omni_tok=omni_files["omnivoice-tokenizer-Q8_0.gguf"]["bytes"]
omni_total=omni_base+omni_tok
cb_files=cb_manifest["files"]
cb_total=cb_manifest["total_model_asset_bytes"]
cb_t3=cb_files["t3_mtl23ls_v3.safetensors"]
cb_s3=cb_files["s3gen.pt"]
cb_support=cb_total-cb_t3-cb_s3

comparison=[]; cards=[]
for case in cases:
    cid=case["id"]; o=omni_rows[cid]; c=cb_results[cid]; ct=cb_telemetry(c)
    omni={"model":"Serveurperso/OmniVoice-GGUF · Q8_0 (base: k2-fsa/OmniVoice)","asset_bytes":omni_total,
          "generation_seconds":float(o["wall_seconds"]),"audio_seconds":float(o["duration_seconds"]),"real_time_factor":float(o["real_time_factor"]),
          "gpu_total_peak_mib":float(o["gpu_peak_total_used_mib"]),"gpu_process_peak_mib":float(o["gpu_peak_native_process_mib"]),
          "gpu_mean_utilization_pct":float(o["gpu_mean_utilization_pct"]),"gpu_peak_power_w":float(o["gpu_peak_power_w"]),
          "gpu_energy_estimate_wh":float(o["gpu_reported_energy_estimate_wh"]),"precision":"Q8_0 GGUF"}
    cb={"model":"ResembleAI/chatterbox · Multilingual V3","asset_bytes":cb_total,
        "generation_seconds":float(c["generation_seconds"]),"audio_seconds":float(c["duration_seconds"]),"real_time_factor":float(c["real_time_factor"]),
        "pytorch_allocated_peak_mib":c["allocated_vram_peak_bytes"]/2**20,"pytorch_reserved_peak_mib":c["reserved_vram_peak_bytes"]/2**20,
        "precision":c["precision"],**ct}
    comparison.append({"id":cid,"title":case["title"],"script":case["text"],"listen_for":case["listen_for"],"omnivoice":omni,"chatterbox":cb})
    script=html.escape(case["text"]).replace("\n","<br>")
    o_stats="".join([
        metric("Model files on disk",f"{mib(omni_total)} total ({mib(omni_base)} base + {mib(omni_tok)} tokenizer)"),
        metric("Generation / output",f"{seconds(o['wall_seconds'])} / {seconds(o['duration_seconds'])} · RTF {float(o['real_time_factor']):.2f}"),
        metric("Peak GPU VRAM used",f"{float(o['gpu_peak_total_used_mib']):,.0f} MiB total · {float(o['gpu_peak_native_process_mib']):,.0f} MiB OmniVoice process"),
        metric("Mean GPU utilization",f"{float(o['gpu_mean_utilization_pct']):.1f}%"),
        metric("Peak board power / estimated GPU energy",f"{float(o['gpu_peak_power_w']):.1f} W / {float(o['gpu_reported_energy_estimate_wh']):.3f} Wh")])
    cb_total_gpu=(f"{ct['sampled_total_gpu_peak_mib']} MiB total GPU (nvidia-smi sample)" if ct.get("sampled_total_gpu_peak_mib") is not None else "Unavailable: FP32-phase external GPU samples were not retained")
    cb_util=(f"{ct['mean_gpu_utilization_pct']:.1f}%" if ct.get("mean_gpu_utilization_pct") is not None else "Unavailable")
    cb_power=(f"{ct['peak_board_power_w']:.1f} W" if ct.get("peak_board_power_w") is not None else "Unavailable")
    cb_energy=(f"{ct['sampled_board_energy_estimate_wh']:.3f} Wh" if ct.get("sampled_board_energy_estimate_wh") is not None else "Unavailable")
    cb_stats="".join([
        metric("Model files on disk",f"{mib(cb_total)} total (T3 {mib(cb_t3)} + S3Gen {mib(cb_s3)} + support {mib(cb_support)})"),
        metric("Generation / output",f"{seconds(c['generation_seconds'])} / {seconds(c['duration_seconds'])} · RTF {float(c['real_time_factor']):.2f}"),
        metric("Peak PyTorch VRAM",f"{c['allocated_vram_peak_bytes']/2**20:,.0f} MiB allocated · {c['reserved_vram_peak_bytes']/2**20:,.0f} MiB reserved · {c['precision']}"),
        metric("Peak total GPU VRAM",cb_total_gpu),
        metric("GPU telemetry",f"{cb_util} mean utilization · {cb_power} peak power · {cb_energy} sampled board energy · {ct.get('sample_count',0)} samples")])
    omni_language=o["language"]; cb_language=c["language_id"]
    cards.append(f'''<article id="{cid}"><h2>{html.escape(case['title'])}</h2><p class="case-meta">{len(case['text'])} characters · seed {case['seed']} · OmniVoice language setting: {html.escape(omni_language)} · Chatterbox language ID: {html.escape(cb_language)}</p><p class="script">{script}</p><p class="notes">Listen for: {html.escape(case['listen_for'])}</p>
      <div class="players"><section><h3>Serveurperso/OmniVoice-GGUF · Q8_0</h3><p class="source">Base model: <code>k2-fsa/OmniVoice</code></p><audio controls preload="none" src="../audio/{cid}.wav"></audio><dl>{o_stats}</dl></section>
      <section><h3>ResembleAI/chatterbox · Multilingual V3</h3><audio controls preload="none" src="audio/{cid}.wav"></audio><dl>{cb_stats}</dl></section></div>
      <label>Listening notes<textarea rows="3" placeholder="Similarity, pronunciation, pacing, omissions, artifacts…"></textarea></label></article>''')

(HERE/"case-comparison.json").write_text(json.dumps(comparison,ensure_ascii=False,indent=2)+"\n")
page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Voice cloning A/B: exact models and resources</title>
<style>
:root{color-scheme:dark;--bg:#15121a;--card:#211b27;--line:#54485c;--ink:#eee;--muted:#c9bacd;--accent:#f092b4}*{box-sizing:border-box}body{font:16px/1.5 system-ui,sans-serif;max-width:1180px;margin:2rem auto;padding:0 1rem;background:var(--bg);color:var(--ink)}h1{line-height:1.15}h2{margin:.3rem 0}h3{font-size:1rem;line-height:1.35;margin:.3rem 0;color:#ffd0df}.intro,.notes,.source,.case-meta{color:var(--muted)}.case-meta{font-size:.9rem}.models{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin:1rem 0}.model,article{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:1rem;margin:1rem 0}.model p{margin:.35rem 0}.players{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin:1rem 0}.players section{background:#19151e;border:1px solid #382e3d;border-radius:8px;padding:.8rem;min-width:0}audio{display:block;width:100%;margin:.5rem 0}dl{display:grid;grid-template-columns:minmax(150px,.7fr) 1.3fr;gap:.25rem .8rem;font-size:.9rem;margin:.6rem 0 0}dt{color:var(--muted)}dd{margin:0;overflow-wrap:anywhere}.script{font-size:1.03rem}.notes{font-size:.92rem}textarea{display:block;width:100%;box-sizing:border-box;background:#17131b;color:#fff;border:1px solid #74637b;border-radius:6px;padding:.7rem;margin-top:.3rem}.warning{border-left:3px solid var(--accent);padding:.6rem .9rem;background:#281e2b;color:var(--muted)}a{color:#ffb4cc}@media(max-width:760px){.players,.models{grid-template-columns:1fr}dl{grid-template-columns:1fr}.players section{overflow:hidden}}
</style>
<h1>Voice cloning: per-case model and resource comparison</h1>
<p class="intro">Same eight scripts and same local reference clip, synthesized on an NVIDIA RTX 2050 with 4,096 MiB physical VRAM. The source reference file is not included.</p>
<div class="models"><section class="model"><h2>Serveurperso/OmniVoice-GGUF · Q8_0</h2><p>Base model: <code>k2-fsa/OmniVoice</code></p><p>Downloaded assets: <code>omnivoice-base-Q8_0.gguf</code> __OMNI_BASE_BYTES__ bytes (__OMNI_BASE_MIB__); <code>omnivoice-tokenizer-Q8_0.gguf</code> __OMNI_TOK_BYTES__ bytes (__OMNI_TOK_MIB__). Total: <strong>__OMNI_TOTAL_MIB__</strong>.</p></section>
<section class="model"><h2>ResembleAI/chatterbox · Multilingual V3</h2><p>Downloaded model assets: <code>t3_mtl23ls_v3.safetensors</code> __CB_T3_BYTES__ bytes (__CB_T3_MIB__); <code>s3gen.pt</code> __CB_S3_BYTES__ bytes (__CB_S3_MIB__); supporting encoder, conditionals and tokenizer files __CB_SUPPORT_BYTES__ bytes (__CB_SUPPORT_MIB__). Total: <strong>__CB_TOTAL_MIB__</strong>.</p></section></div>
<p class="warning">Model file size is disk usage, not VRAM usage. OmniVoice rows report sampled total GPU and native-process peaks. Chatterbox reports per-case PyTorch allocated/reserved peaks; nvidia-smi totals, utilization and power are available only for the final three FP16 cases because the first-phase sample file was overwritten. Chatterbox changed from FP32 to FP16 + autocast after an out-of-memory error.</p>
<p class="warning">Timing boundaries differ: OmniVoice wall time includes the HTTP request and fresh process/model loading; Chatterbox generation time excludes its one-time download/load and includes reference conditioning. Treat timing as setup-specific, not a direct speed ranking. GPU energy is an estimate from sampled board power, not a wall-meter reading.</p>
<p><strong>User's overall listening verdict:</strong> Chatterbox was not good overall; OmniVoice did better in several respects. Per-case quality ratings were not supplied.</p>'''+''.join(cards)+'''<script>document.querySelectorAll('textarea').forEach((e,i)=>{const k='voice-clone-ab-note-'+i;e.value=localStorage.getItem(k)||'';e.addEventListener('input',()=>localStorage.setItem(k,e.value))})</script></html>'''
for token,value in {
    "__OMNI_BASE_BYTES__":f"{omni_base:,}","__OMNI_BASE_MIB__":mib(omni_base),
    "__OMNI_TOK_BYTES__":f"{omni_tok:,}","__OMNI_TOK_MIB__":mib(omni_tok),"__OMNI_TOTAL_MIB__":mib(omni_total),
    "__CB_T3_BYTES__":f"{cb_t3:,}","__CB_T3_MIB__":mib(cb_t3),"__CB_S3_BYTES__":f"{cb_s3:,}",
    "__CB_S3_MIB__":mib(cb_s3),"__CB_SUPPORT_BYTES__":f"{cb_support:,}","__CB_SUPPORT_MIB__":mib(cb_support),
    "__CB_TOTAL_MIB__":mib(cb_total)}.items(): page=page.replace(token,value)
(HERE/"index.html").write_text(page)
print(f"Wrote per-case model/resource comparison for {len(cards)} cases")
