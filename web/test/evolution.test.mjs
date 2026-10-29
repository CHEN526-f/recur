import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {Evolution} from '../dist/evolution.js';
test('continuous structure parameters remain bounded and evolve within one family',()=>{
 const e=new Evolution();e.resetTrack({duration:80,bpm:120});const engine={playing:true,position:0,analysis:{bpm:120},sample:()=>[.7,.5,.8],takeEvents:()=>[]},values=[];
 for(let frame=0;frame<720;frame++){engine.position=frame/60;if(frame%30===0)e.note(0,.8);e.update(1/60,engine);values.push([...e.growth,...e.architecture,...e.motion]);}
 assert(values.flat().every(x=>Number.isFinite(x)&&x>=0&&x<=1.4));assert(Math.abs(values[10][0]-values[600][0])>.02);assert(e.weights[2]>.99);assert(e.travel>1);
});
test('manual selection and pause preserve the intended construction',()=>{
 const e=new Evolution(),engine={playing:false,position:0,sample:()=>[0,0,0],takeEvents:()=>[]};e.manual(1);for(let i=0;i<180;i++)e.update(1/60,engine);assert.equal(e.auto,false);assert(e.weights[1]>.999);const before=JSON.stringify(e);e.update(.1,engine,true);assert.equal(JSON.stringify(e),before);
});
test('worker detects actual off-grid pulses and rejects silence',()=>{
 const code=readFileSync(new URL('../dist/analyzer-worker.js',import.meta.url),'utf8');let result;const sandbox={self:{postMessage:r=>{result=r;}},Float32Array,Int8Array,Array,Math};vm.createContext(sandbox);vm.runInContext(code,sandbox);
 const rate=16000,samples=new Float32Array(rate*6),starts=[.3,.81,1.29,1.73,2.28,2.84,3.37,3.86,4.4,4.92,5.4];
 for(const start of starts)for(let j=0;j<rate*.25;j++){const t=j/rate,i=Math.round(start*rate)+j;if(i<samples.length)samples[i]+=.7*Math.sin(Math.PI*2*70*t)*Math.exp(-t*22);}
 sandbox.self.onmessage({data:{mono:samples,sampleRate:rate}});assert(!result.error);for(const start of starts)assert(result.events.some(e=>Math.abs(e.time-start)<.035),`pulse at ${start}`);
 sandbox.self.onmessage({data:{mono:new Float32Array(rate*3),sampleRate:rate}});assert.equal(result.events.length,0);
});
