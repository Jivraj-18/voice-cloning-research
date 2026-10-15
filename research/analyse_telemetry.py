#!/usr/bin/env python3
"""Join timestamped NVIDIA telemetry to HTTP request windows."""
import csv,datetime,json,pathlib,statistics
root=pathlib.Path(__file__).resolve().parent

def number(value):
 try:return float(value)
 except (TypeError,ValueError):return None

def read_rows(path,expected):
 rows=[]
 with path.open() as f:
  for row in csv.reader(f):
   if len(row)!=expected:continue
   row=[x.strip() for x in row]
   try:ts=datetime.datetime.strptime(row[0],'%Y/%m/%d %H:%M:%S.%f').timestamp()
   except ValueError:continue
   rows.append((ts,row))
 return rows

def main():
 gpu=[]
 for t,row in read_rows(root/'gpu-samples.csv',7):
  gpu.append({'epoch':t,'memory_mib':number(row[4]),'utilization_pct':number(row[5]),'power_w':number(row[6]),'total_memory_mib':number(row[3]),'name':row[2]})
 processes=read_rows(root/'gpu-process-samples.csv',4)
 results=json.loads((root/'results.json').read_text())
 for result in results:
  start=result['start_epoch'];end=result['end_epoch']
  samples=[s for s in gpu if start<=s['epoch']<=end]
  baseline=[s['memory_mib'] for s in gpu if start-0.8<=s['epoch']<start and s['memory_mib'] is not None]
  if not baseline:baseline=[s['memory_mib'] for s in gpu if start-5<=s['epoch']<start and s['memory_mib'] is not None]
  valid=[s['memory_mib'] for s in samples if s['memory_mib'] is not None]
  native=[number(row[3]) for t,row in processes if start<=t<=end and 'omnivoice-tts' in row[2]]
  native=[v for v in native if v is not None]
  powers=[s for s in samples if s['power_w'] is not None]
  # Trapezoids over samples inside the request. End slivers are excluded.
  energy_j=sum((a['power_w']+b['power_w'])/2*(b['epoch']-a['epoch']) for a,b in zip(powers,powers[1:]))
  result.update({'gpu_sample_count':len(samples),'gpu_baseline_mib':statistics.median(baseline) if baseline else None,'gpu_peak_total_used_mib':max(valid) if valid else None,'gpu_peak_native_process_mib':max(native) if native else None,'gpu_mean_utilization_pct':statistics.mean(s['utilization_pct'] for s in samples if s['utilization_pct'] is not None) if samples else None,'gpu_peak_power_w':max(s['power_w'] for s in powers) if powers else None,'gpu_reported_energy_estimate_wh':energy_j/3600 if len(powers)>1 else None})
  result['gpu_peak_above_baseline_mib']=result['gpu_peak_total_used_mib']-result['gpu_baseline_mib'] if valid and baseline else None
 (root/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
 fields=['id','title','status','language','seed','characters','whitespace_word_count','wall_seconds','duration_seconds','real_time_factor','gpu_baseline_mib','gpu_peak_total_used_mib','gpu_peak_above_baseline_mib','gpu_peak_native_process_mib','gpu_sample_count','gpu_mean_utilization_pct','gpu_peak_power_w','gpu_reported_energy_estimate_wh','peak_dbfs','rms_dbfs','clipped_sample_fraction','quiet_frame_fraction_below_minus50dbfs','leading_quiet_seconds','trailing_quiet_seconds','file_bytes','audio_file','sha256','start_utc','end_utc','user_comment','comments_status','listen_for','error']
 with (root/'results.csv').open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(results)
 native=max((x['gpu_peak_native_process_mib'] or 0 for x in results),default=0)
 summary={'test_count':len(results),'successful':sum(x['status']=='success' for x in results),'failed':sum(x['status']!='success' for x in results),'total_request_wall_seconds':sum(x['wall_seconds'] for x in results),'total_audio_seconds':sum(x.get('duration_seconds',0) for x in results),'peak_total_gpu_memory_mib':max((x['gpu_peak_total_used_mib'] or 0 for x in results),default=0),'peak_single_native_process_mib':native,'gpu_reported_energy_estimate_wh':sum(x.get('gpu_reported_energy_estimate_wh') or 0 for x in results),'actual_software_api_paid_usd':0,'electricity_cost_measured':False,'total_requested_characters':sum(x['characters'] for x in results),'hypothetical_elevenlabs_at_1_credit_per_character':{'credits':sum(x['characters'] for x in results),'starter_monthly_usd':6,'monthly_credits':30000,'allocated_allowance_usd':sum(x['characters'] for x in results)*6/30000,'is_actual_charge':False},'gpu_sampling_note':'200 ms target, sampled peaks only; shorter allocation spikes may be missed. Total GPU memory includes other GPU processes. Native process memory includes context/buffers, not just model weights.','energy_note':'Trapezoidal estimate from reported GPU board power during request samples; excludes CPU, screen, charger losses, startup, setup and idle gaps. Not a wall-power or electricity-bill measurement.'}
 (root/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
