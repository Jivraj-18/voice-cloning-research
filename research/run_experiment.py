#!/usr/bin/env python3
"""Run the published scripts sequentially against an existing local VoiceStudio.
Requires requests, numpy and psutil. GPU telemetry is recorded separately.
An existing authorized profile is required; no voice reference is published.
"""
import argparse,datetime,hashlib,json,pathlib,time,wave
import numpy as np
import psutil
import requests

def utc_now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def audio_stats(path):
 with wave.open(str(path),'rb') as wav:
  sr=wav.getframerate();channels=wav.getnchannels();width=wav.getsampwidth();frames=wav.getnframes();raw=wav.readframes(frames)
 if width!=2:raise ValueError(f'Expected PCM16; got sample width {width}')
 samples=np.frombuffer(raw,dtype='<i2').astype(np.float64)/32768
 mono=samples.reshape(-1,channels).mean(axis=1)
 peak=float(np.max(np.abs(samples))) if samples.size else 0
 rms=float(np.sqrt(np.mean(samples*samples))) if samples.size else 0
 # Frame-level quiet estimates are diagnostics, not a word-accuracy measure.
 n=sr//50;frames_for_rms=mono[:len(mono)//n*n].reshape(-1,n)
 levels=np.sqrt(np.mean(frames_for_rms**2,axis=1)) if len(frames_for_rms) else np.array([])
 active=np.flatnonzero(levels>10**(-50/20))
 return {'duration_seconds':frames/sr,'sample_rate_hz':sr,'channels':channels,'sample_width_bytes':width,'peak_dbfs':20*np.log10(max(peak,1e-12)),'rms_dbfs':20*np.log10(max(rms,1e-12)),'clipped_sample_fraction':float(np.mean(np.abs(samples)>=32767/32768)),'quiet_frame_fraction_below_minus50dbfs':float(np.mean(levels<=10**(-50/20))) if len(levels) else None,'leading_quiet_seconds':float(active[0]*.02) if len(active) else frames/sr,'trailing_quiet_seconds':float((len(levels)-1-active[-1])*.02) if len(active) else frames/sr}
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--base-url',default='http://127.0.0.1:3900');parser.add_argument('--profile-id',default='LOCAL_VOICE_PROFILE');args=parser.parse_args()
 root=pathlib.Path(__file__).resolve().parent;tests=json.loads((root/'tests.json').read_text());base=args.base_url.rstrip('/')
 health=requests.get(base+'/health',timeout=10);health.raise_for_status()
 engines=requests.get(base+'/engines/tts',timeout=10).json();assert engines['active']=='omnivoice-gguf','Select the intended engine before benchmarking'
 metadata={'started_utc':utc_now(),'health':health.json(),'active_engine':engines['active'],'profile_id':args.profile_id,'host':{'cpu':'Intel Core i5-12450H','logical_cpus':psutil.cpu_count(),'ram_total_bytes':psutil.virtual_memory().total},'run_policy':'sequential, one request per case, no automatic retries; one second between requests','timing_boundary':'client wall time from immediately before POST until the full HTTP response body has arrived; excludes writing and analysing the output','native_runtime':'omnivoice.cpp 886fc079838ca7400cb2b42b36e2a65aa1daabe8, CUDA sm_86, native default 32 steps; quantized weights loaded in a new process per generation','gpu_sampling_target_ms':200,'voices_and_models_already_installed':True}
 (root/'run-metadata.json').write_text(json.dumps(metadata,indent=2)+'\n');results=[]
 for case in tests:
  target=root/'audio'/(case['id']+'.wav')
  if target.exists():raise RuntimeError(f'Refusing to overwrite an existing run: {target}')
  payload={'model':'tts-1','voice':args.profile_id,'input':case['text'],'language':case['language'],'response_format':'wav','seed':case['seed']}
  (root/'prompts'/(case['id']+'.request.json')).write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
  time.sleep(1)
  record={k:v for k,v in case.items() if k!='text'};record.update({'characters':len(case['text']),'whitespace_word_count':len(case['text'].split()),'start_utc':utc_now(),'start_epoch':time.time(),'available_ram_before_bytes':psutil.virtual_memory().available,'swap_used_before_bytes':psutil.swap_memory().used,'comments_status':'pending listening review','user_comment':None})
  start=time.perf_counter();print('START',case['id'],case['title'],flush=True)
  try:
   response=requests.post(base+'/v1/audio/speech',json=payload,timeout=(15,900))
   record.update({'wall_seconds':time.perf_counter()-start,'end_epoch':time.time(),'end_utc':utc_now(),'http_status':response.status_code,'response_content_type':response.headers.get('content-type')})
   response.raise_for_status()
   if response.content[:4]!=b'RIFF':raise ValueError('Successful response was not WAV')
   target.write_bytes(response.content);record.update(audio_stats(target));record.update({'status':'success','audio_file':str(target.relative_to(root)),'file_bytes':target.stat().st_size,'sha256':hashlib.sha256(response.content).hexdigest()});record['real_time_factor']=record['wall_seconds']/record['duration_seconds']
   print('DONE',case['id'],f"wall={record['wall_seconds']:.2f}s audio={record['duration_seconds']:.2f}s RTF={record['real_time_factor']:.3f}",flush=True)
  except Exception as exc:
   record.setdefault('wall_seconds',time.perf_counter()-start);record.setdefault('end_epoch',time.time());record.setdefault('end_utc',utc_now());record.update({'status':'failed','error':str(exc)})
   if 'response' in locals() and not response.ok:(root/'audio'/(case['id']+'.error.txt')).write_text(response.text)
   print('FAILED',case['id'],str(exc),flush=True)
  record['available_ram_after_bytes']=psutil.virtual_memory().available;results.append(record);(root/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
 metadata['finished_utc']=utc_now();(root/'run-metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
 print('EXPERIMENT FINISHED',len(results),'cases',flush=True)
if __name__=='__main__':main()
