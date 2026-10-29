// Original radix-2 FFT and transient analysis. Runs off the rendering thread.
function fft(re,im){const n=re.length;for(let i=1,j=0;i<n;i++){let bit=n>>1;for(;j&bit;bit>>=1)j^=bit;j^=bit;if(i<j){[re[i],re[j]]=[re[j],re[i]];[im[i],im[j]]=[im[j],im[i]];}}for(let length=2;length<=n;length<<=1){const angle=-2*Math.PI/length,wr=Math.cos(angle),wi=Math.sin(angle);for(let i=0;i<n;i+=length){let r=1,s=0;for(let j=0;j<length/2;j++){const a=i+j,b=a+length/2,tr=r*re[b]-s*im[b],ti=r*im[b]+s*re[b];re[b]=re[a]-tr;im[b]=im[a]-ti;re[a]+=tr;im[a]+=ti;const next=r*wr-s*wi;s=r*wi+s*wr;r=next;}}}}
function percentile(a,p){const v=Array.from(a).sort((x,y)=>x-y);return v[Math.min(v.length-1,Math.floor(v.length*p))]||0;}
self.onmessage=({data:{mono,sampleRate}})=>{try{
 const stride=Math.max(1,Math.round(sampleRate/16000)),rate=sampleRate/stride,n=Math.ceil(mono.length/stride),samples=new Float32Array(n);
 for(let i=0;i<n;i++){let sum=0;for(let j=0;j<stride;j++)sum+=mono[i*stride+j]||0;samples[i]=sum/stride;}
 const size=1024,hop=Math.round(rate/100),fps=rate/hop,frames=Math.ceil(n/hop),levels=new Float32Array(frames*3),flux=new Float32Array(frames*3),re=new Float32Array(size),im=new Float32Array(size),prior=new Float32Array(size/2),win=Float32Array.from({length:size},(_,i)=>.5-.5*Math.cos(i*Math.PI*2/(size-1)));
 const band=Int8Array.from({length:size/2},(_,k)=>{const f=k*rate/size;return f<35?-1:f<190?0:f<2000?1:f<Math.min(10000,rate*.49)?2:-1;}),counts=[0,0,0];for(const b of band)if(b>=0)counts[b]++;
 for(let f=0;f<frames;f++){for(let k=0;k<size;k++){re[k]=(samples[f*hop+k-size/2]||0)*win[k];im[k]=0;}fft(re,im);const power=[0,0,0],rise=[0,0,0];for(let k=0;k<size/2;k++){const mag=Math.hypot(re[k],im[k]),b=band[k];if(b>=0){power[b]+=mag*mag;rise[b]+=Math.max(0,mag-prior[k]);}prior[k]=mag;}for(let b=0;b<3;b++){levels[f*3+b]=Math.sqrt(power[b]/Math.max(1,counts[b]));flux[f*3+b]=rise[b]/Math.max(1,counts[b]);}}
 const refs=[0,1,2].map(b=>Math.max(.002,percentile(Array.from({length:frames},(_,f)=>levels[f*3+b]),.97))),scales=[0,1,2].map(b=>Math.max(.001,Math.max(...refs)*.003,refs[b]*.045,percentile(Array.from({length:frames},(_,f)=>flux[f*3+b]),.95))),novelty=new Float32Array(frames);
 for(let f=0;f<frames;f++){for(let b=0;b<3;b++){flux[f*3+b]=Math.min(4,flux[f*3+b]/scales[b]);levels[f*3+b]=Math.min(1,levels[f*3+b]/refs[b]);}novelty[f]=Math.max(flux[f*3],flux[f*3+1]*.7,flux[f*3+2]*.65);}
 const block=Math.max(1,Math.round(rate/1000)),energy=new Float32Array(Math.ceil(n/block));for(let i=0;i<n;i++)energy[Math.floor(i/block)]+=samples[i]**2/block;const slope=new Float32Array(energy.length);for(let i=3;i<energy.length-3;i++)slope[i]=Math.max(0,(energy[i+2]-energy[i-3])/5);
 const events=[];for(let f=1;f<frames-1;f++){
  const v=novelty[f];if(v<.3||v<novelty[f-1]||v<=novelty[f+1])continue;
  let sum=0,sum2=0,count=0;for(let j=Math.max(0,f-25);j<Math.min(frames,f+26);j++){sum+=novelty[j];sum2+=novelty[j]**2;count++;}const mean=sum/count,sd=Math.sqrt(Math.max(0,sum2/count-mean**2));if(v<mean+sd*.45)continue;
  const t=f/fps,left=Math.max(0,Math.round((t-.030)*rate/block)),right=Math.min(slope.length,Math.round((t+.026)*rate/block));let best=left;for(let j=left+1;j<right;j++)if(slope[j]>slope[best])best=j;
  const time=Math.max(0,best*block/rate-.001),last=events.at(-1);if(last&&time-last.time<.075){if(v<last.raw*1.1)continue;events.pop();}
  const [low,mid,high]=flux.subarray(f*3,f*3+3);events.push({time,voice:low>=Math.max(mid*.75,high*.65)?0:high>mid*.8?5:3,strength:Math.max(.25,Math.min(1,v/1.8)),raw:v});
 }
 let lag=Math.round(fps*.5),score=-Infinity;const mean=novelty.reduce((a,b)=>a+b,0)/frames;
 for(let k=Math.round(fps*60/180);k<=Math.round(fps*60/80);k++){let s=0;for(let f=k;f<frames;f++)s+=(novelty[f]-mean)*(novelty[f-k]-mean);s/=Math.max(1,frames-k);if(s>score){score=s;lag=k;}}
 const bpm=60*fps/lag,period=60/bpm,early=events.filter(e=>e.voice===0&&e.time<8).slice(0,32);let anchor=early[0]?.time||events[0]?.time||0,bestScore=-1;
 for(const candidate of early){let s=0;for(const e of events){const d=Math.abs(((e.time-candidate.time+period/2)%period+period)%period-period/2);s+=e.strength*Math.exp(-((d/(period*.12))**2));}if(s>bestScore){bestScore=s;anchor=candidate.time;}}
 const beats=[];for(let t=anchor%period;t<n/rate;t+=period){let near=null;for(const e of events){if(e.time<t-period*.2)continue;if(e.time>t+period*.2)break;if(!near||Math.abs(e.time-t)<Math.abs(near.time-t))near=e;}beats.push(near?near.time:t);}
 self.postMessage({levels,fps,events,beats,bpm,duration:n/rate},[levels.buffer]);
}catch(error){self.postMessage({error:String(error.message||error)});}};
