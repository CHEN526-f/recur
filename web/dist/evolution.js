const clamp=(x,a=0,b=1)=>Math.max(a,Math.min(b,x));
export const formNames=['SERPENT','RIBBON','BLOOM','CRYSTAL','ORBIT','TIDE','IRIS','CORONA','ROSETTE','FACET'];
export class Evolution{
 constructor(){this.auto=true;this.weights=[0,0,1,0,0,0,0,0,0,0];this.targetWeights=this.weights.slice();this.growth=[.4,.25,.4,.1];this.architecture=[.25,.5,.5,.2];this.targets=[...this.growth,...this.architecture];this.pulses=[0,0,0];this.kick=0;this.bands=[0,0,0];this.energy=0;this.expansion=.04;this.charge=0;this.holding=false;this.phase=0;this.travel=0;this.memory=0;this.lastPhrase=-1;this.lastTime=0;this.history=0;this.lastProfile=[0,0,0];this.fx=[.5,.3];this.intensity=.9;this.seed=12345;this.motion=[0,0,0,0];this.motionPhase=[0,0];this.evolution=1;}
 random(){this.seed=(Math.imul(this.seed,1664525)+1013904223)>>>0;return this.seed/4294967296;}
 resetTrack(analysis){this.seed=(Math.floor(analysis.duration*1009+analysis.bpm*919))>>>0;this.lastPhrase=-1;this.memory=0;this.history=0;this.lastTime=0;this.lastFamilyTime=0;this.family=2;this.targetWeights=Array.from({length:10},(_,i)=>+(i===2));this.kick=0;this.pulses=[0,0,0];this.auto=true;}
 manual(form){this.auto=false;this.targetWeights=Array.from({length:10},(_,i)=>+(i===form));}
 note(voice,strength=1){const band=[0,2,1,1,0,2][voice];this.pulses[band]=Math.max(this.pulses[band],strength);if(voice===0)this.kick=Math.max(this.kick,strength);if(voice===4)this.kick=Math.max(this.kick,strength*.4);this.memory+=strength*(voice===0?.4:voice===3?.7:.2);}
 release(){this.holding=false;this.kick=1;this.memory+=3;this.pulses[1]=1;this.targets[0]=Math.min(1,this.targets[0]+.3);}
 update(dt,engine,paused=false,jog=1){if(paused)return this;dt=clamp(dt,0,.12);const levels=engine.sample(),playing=engine.playing,time=engine.position,bpm=engine.analysis?.bpm||108,beat=playing?time*bpm/60:this.phase*bpm/60;
  for(const e of engine.takeEvents())this.note(e.voice,(.45+.55*e.strength)*Math.exp(-(time-e.time)*9));
  for(let i=0;i<3;i++)this.bands[i]+=(Math.max(levels[i],this.pulses[i])-this.bands[i])*(1-Math.exp(-dt*(i===0?13:7)));
  const energy=(this.bands[0]*.3+this.bands[1]*.4+this.bands[2]*.3),contrast=levels.reduce((s,x,i)=>s+Math.abs(x-this.lastProfile[i]),0)/3;
  // Persistent musical memory changes the next mechanism; there is no preset route.
  const phrase=Math.floor(beat/12),newPhrase=phrase!==this.lastPhrase;
  if(this.auto&&playing&&(newPhrase||(contrast>.34&&time-this.lastTime>2.5))){
   this.lastPhrase=phrase;this.lastTime=time;this.lastProfile=levels.slice();this.history+=.5+this.memory*.037;this.memory*=.55;
   const r=()=>this.random(),low=levels[0],mid=levels[1],high=levels[2],long=.5+.5*Math.sin(this.history*.71);
   this.targets=[clamp(.15+low*.45+r()*.32),clamp(.12+mid*.45+r()*.4),clamp(.18+energy*.45+r()*.35),clamp(.05+high*.35+r()*.6),r(),clamp(.2+long*.45+(r()-.5)*.25),r(),clamp(.1+mid*.4+r()*.35)];
   // Keep one structural family legible for a passage, while dimensions keep moving.
   if(time-(this.lastFamilyTime||0)>13||(contrast>.55&&time-(this.lastFamilyTime||0)>6)){
    const choices=low>mid*1.15?[0,4,7,5]:high>mid*1.12?[2,6,8,9]:[1,5,2,3];
    const available=choices.filter(x=>x!==this.family);this.family=available[Math.floor(r()*available.length)];this.lastFamilyTime=time;
    this.targetWeights=Array.from({length:10},(_,i)=>+(i===this.family));
   }
  }
  const follow=1-Math.exp(-dt*(this.auto?.8:5));for(let i=0;i<10;i++)this.weights[i]+=(this.targetWeights[i]-this.weights[i])*follow;
  const followDNA=1-Math.exp(-dt*.85);for(let i=0;i<4;i++){this.growth[i]+=(this.targets[i]-this.growth[i])*followDNA;this.architecture[i]+=(this.targets[i+4]-this.architecture[i])*followDNA;}
  // Slow musical breathing continues within a passage, distinct from drum recoil.
  const brake=this.holding?.15:1;this.phase+=dt*brake*jog;this.travel+=dt*(.35+this.bands[1]*.9+this.kick*.4)*brake*jog;
  this.charge+=(+(this.holding)-this.charge)*(1-Math.exp(-dt*1.8));this.energy+=(energy-this.energy)*(1-Math.exp(-dt*5));
  const breathing=.5-.5*Math.cos(beat*Math.PI/16+this.history*.2),desired=playing?energy*(.20+.48*breathing)+this.charge*.45:Math.max(this.charge*.5,Math.max(...this.pulses)*.18);
  this.expansion+=(clamp(desired,0,.9)-this.expansion)*(1-Math.exp(-dt*(desired>this.expansion?2.5:1.2)));
  const amount=this.intensity;this.motion=[clamp(this.kick*amount,0,1.3),Math.max(this.pulses[1],this.bands[1]*.8)*amount,Math.max(this.pulses[2],this.bands[2]*.65)*amount,Math.max(this.energy,...this.pulses)*amount];this.motionPhase=[beat*Math.PI/2,this.travel];this.evolution=this.auto?1:.15;
  this.kick*=Math.exp(-dt*9);for(let i=0;i<3;i++)this.pulses[i]*=Math.exp(-dt*[6,2.6,12][i]);return this;
 }
}
