import subprocess, sys, numpy as np, json
def frames(f, fps=10, w=108, h=192):
    p = subprocess.run(["ffmpeg","-v","error","-i",f,"-vf",f"fps={fps},scale={w}:{h},format=gray","-f","rawvideo","-"],capture_output=True)
    a = np.frombuffer(p.stdout,np.uint8).reshape(-1,h,w).astype(np.float32); return a
out={}
for n in sys.argv[1:]:
    a = frames(f"{n}.mp4"); fps=10
    cap = a[:, 20:44, :]          # caption band (~10-23%)
    stage = a[:, 44:140, :]       # stage band
    # caption "reset" = caption text mostly disappears/changes: big drop in caption brightness
    cb = cap.mean((1,2)); sd = np.abs(np.diff(cap,axis=0)).mean((1,2)); st = np.abs(np.diff(stage,axis=0)).mean((1,2))
    # caption beats: local minima of brightness (text fades out between sentences)
    th = cb.max()*0.45 if cb.max()>0 else 0
    beats=[]; i=1
    while i < len(cb)-1:
        if cb[i] < th*0.0 + np.percentile(cb,12) and cb[i]<=cb[i-1] and cb[i]<=cb[i+1] and (not beats or i/fps-beats[-1]>1.0): beats.append(round(i/fps,1))
        i+=1
    out[n]={"dur":round(len(a)/fps,1),"caption_beats":len(beats),"median_beat_s":round(float(np.median(np.diff(beats))),2) if len(beats)>2 else None,
            "stage_motion_mean":round(float(st.mean()),2),"stage_motion_p90":round(float(np.percentile(st,90)),2),"still_frac":round(float((st<0.25).mean()),2),
            "mean_luma":round(float(a.mean()),1)}
    print(n,out[n],flush=True)
json.dump(out,open("beats.json","w"),indent=1)
