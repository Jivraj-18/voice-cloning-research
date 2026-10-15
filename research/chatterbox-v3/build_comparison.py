#!/usr/bin/env python3
"""Build a local A/B listening page from the pinned test prompts and results."""
import html, json, pathlib

HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parent
cases=json.loads((ROOT/"tests.json").read_text())
results={r["id"]:r for r in json.loads((HERE/"results.json").read_text())}
cards=[]
for case in cases:
    cid=case["id"]; r=results[cid]
    if r["status"]!="success": continue
    title=html.escape(case["title"]); script=html.escape(case["text"]).replace("\n","<br>")
    notes=html.escape(case["listen_for"])
    baseline=f"../audio/{cid}.wav"; candidate=f"audio/{cid}.wav"
    cards.append(f'''<article><h2>{title}</h2><p class="script">{script}</p><p class="notes">Listen for: {notes}</p>
      <div class="players"><section><b>VoiceStudio / OmniVoice baseline</b><audio controls preload="none" src="{baseline}"></audio></section>
      <section><b>Chatterbox Multilingual V3</b><audio controls preload="none" src="{candidate}"></audio></section></div>
      <p class="meta">Chatterbox generation {r['generation_seconds']:.2f}s · output {r['duration_seconds']:.2f}s · peak PyTorch allocation {r['allocated_vram_peak_bytes']/2**20:.0f} MiB · precision {r.get('precision','see README')}</p>
      <label>Your listening notes<textarea rows="3" placeholder="Similarity, pronunciation, pacing, omissions, artifacts…"></textarea></label></article>''')
page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Voice clone A/B: OmniVoice and Chatterbox V3</title>
<style>body{font:16px/1.5 system-ui,sans-serif;max-width:1000px;margin:2rem auto;padding:0 1rem;background:#15121a;color:#eee}h1{line-height:1.15}article{background:#211b27;border:1px solid #54485c;border-radius:12px;padding:1rem;margin:1rem 0}.script{white-space:normal;font-size:1.05rem}.notes,.meta{color:#c9bacd;font-size:.92rem}.players{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin:1rem 0}.players section{background:#19151e;padding:.8rem;border-radius:8px}audio{display:block;width:100%;margin-top:.5rem}textarea{display:block;width:100%;box-sizing:border-box;background:#17131b;color:#fff;border:1px solid #74637b;border-radius:6px;padding:.7rem;margin-top:.3rem}@media(max-width:650px){.players{grid-template-columns:1fr}}</style>
<h1>Voice clone listening comparison</h1><p>Each row uses the same script and the same local reference recording. Play both clips at a matched volume. Your current overall verdict: <strong>Chatterbox was not good overall; OmniVoice did better in several respects.</strong> Per-dimension and per-clip notes are still open. Notes typed here remain in this browser only.</p>'''+''.join(cards)+'''<script>document.querySelectorAll('textarea').forEach((e,i)=>{const k='voice-clone-ab-note-'+i;e.value=localStorage.getItem(k)||'';e.addEventListener('input',()=>localStorage.setItem(k,e.value))})</script></html>'''
(HERE/"index.html").write_text(page)
print(f"Wrote {HERE/'index.html'} with {len(cards)} A/B rows")
