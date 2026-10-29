"""Share the actual original rib mesh and constructions with the WebGL2 client."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import numpy as np
from recur.materials import polished_rib,beveled_box,SURFACE_FRAGMENT
from recur.structures import GLSL

EVOLVE=r'''
void evolve(float theta,float band,float weights[10],inout vec3 p,inout mat3 frame){
 float strength=evolution;
 float aperture=growth.x,curl=growth.y,spacing=growth.z,split=growth.w;
 float petals=architecture.x,elongation=architecture.y,roll=architecture.z,depth=architecture.w;
 float closed=clamp(weights[0]+weights[2]+weights[4]+weights[6]+weights[7]+weights[8]+weights[9],0.,1.);
 float angle=theta,sector=floor(theta/(PI*2.)*6.);
 float sectorAngle=(sector+.5)*PI/3.;
 float v=fract(theta/(PI*2.)*6.);
 float harmonic=mix(cos(theta*3.),cos(theta*6.),petals);
 float ripple=sin(theta*4.-motion_phase.y*1.4+band*.8);
 vec2 radial=vec2(cos(theta),sin(theta));
 // A shared hinge for each sector: connected, ordered parts rather than noise.
 vec2 pivot=vec2(cos(sectorAngle),sin(sectorAngle))*(.32+band*.045);
 float hinge=split*(.45+.40*sin(motion_phase.x*.25+band*.6))*sin((v-.5)*PI);
 mat3 fold=rz(hinge*closed);
 vec3 hinged=fold*vec3(p.xy-pivot,p.z);hinged.xy+=pivot;
 hinged.xy+=vec2(cos(sectorAngle),sin(sectorAngle))*split*.28*closed;
 p=mix(p,hinged,strength);frame=frame*(1.-strength)+(fold*frame)*strength;
 p.xy+=strength*closed*radial*(aperture*.34+harmonic*curl*.22+ripple*.035*motion.y);
 p.x*=1.+strength*(elongation-.5)*.65;
 p.y*=1.-strength*(elongation-.5)*.25;
 p.z+=strength*(band-1.)*spacing*.16;
 p.z+=strength*depth*.45*sin(theta*2.+band*.7-motion_phase.y*.6);
 float openForm=weights[1]+weights[3]+weights[5];
 float curvature=strength*openForm*(curl-.28)*1.65;
 if(abs(curvature)>.001){
   float bend=p.x*curvature;
   p.x=sin(bend)/curvature;p.z+=(1.-cos(bend))/curvature;
   frame=ry(bend)*frame;
 }
 float layerRoll=strength*((roll-.5)*.55*(band-2.5)+curl*.28*sin(motion_phase.x*.125+band*.6));
 mat3 turn=rz(layerRoll+strength*.10*curl*ripple)*rx(strength*depth*.14*sin(band));
 p=turn*p;frame=turn*frame*ry(strength*(curl*.55*sin(theta*3.-motion_phase.y+band*.45)+(aperture-.5)*.6));
}
'''
architecture=GLSL.replace('void structure(',EVOLVE+'\nvoid structure(').replace(' articulate(theta,band,weights,center,local);',' articulate(theta,band,weights,center,local);\n evolve(theta,band,weights,center,local);')
vertex=r'''#version 300 es
precision highp float;
in vec3 in_pos;in vec3 in_normal;in float in_material;in vec3 in_block;in vec3 in_block_normal;
uniform mat4 projection;uniform mat4 view;
uniform float phase;uniform float weights[10];uniform vec3 bands;uniform float energy;
uniform float charge;uniform float twist;uniform vec2 orbit;uniform vec2 fx;uniform float expansion;
uniform vec4 motion;uniform vec2 motion_phase;uniform vec4 growth;uniform vec4 architecture;uniform float evolution;
out vec3 world;out vec3 normal;out float material;out float instance;
const float PI=3.14159265359;
mat3 rx(float a){float c=cos(a),s=sin(a);return mat3(1,0,0,0,c,s,0,-s,c);}
mat3 ry(float a){float c=cos(a),s=sin(a);return mat3(c,0,-s,0,1,0,s,0,c);}
mat3 rz(float a){float c=cos(a),s=sin(a);return mat3(c,s,0,-s,c,0,0,0,1);}
// STRUCTURES
void main(){
 float id=float(gl_InstanceID),band=floor(id/216.),theta=mod(id,216.)/216.*PI*2.;
 vec3 center;mat3 local;float size;
 structure(theta,band,phase,bands,weights,expansion,center,local,size);
 float emergence=1.;
 if(band>=3.){
   emergence=smoothstep(.04,.85,expansion)*(1.-smoothstep(band-.5,band+1.,3.+growth.z*6.));
   center.xy*=.86+.14*emergence;center.z-=(1.-emergence)*2.8;
 }
 local=local*ry(twist*.22+charge*.13);
 float blockMix=weights[3]+weights[9];
 vec3 pos=mix(in_pos,in_block,blockMix),norm=normalize(mix(in_normal,in_block_normal,blockMix)+vec3(.000001));
 mat3 rotation=rx(orbit.y)*ry(orbit.x);
 vec3 p=rotation*(center+local*pos*size*emergence);
 world=p;normal=rotation*local*norm;material=in_material;instance=id;
 gl_Position=projection*view*vec4(p,1.);gl_Position.y+=.10*gl_Position.w;
}
'''.replace('// STRUCTURES',architecture)
fragment=SURFACE_FRAGMENT.lstrip().replace('#version 330','#version 300 es\nprecision highp float;')
mesh=polished_rib();block=beveled_box();pad=(-len(mesh))%len(block)
if pad:mesh=np.concatenate((mesh,mesh[:pad]))
combined=np.concatenate((mesh,np.tile(block,(len(mesh)//len(block),1))),axis=1).astype('f4')
out=ROOT/'web/dist/geometry.js'
out.write_text('export const VERTEX='+json.dumps(vertex)+';\nexport const FRAGMENT='+json.dumps(fragment)+';\nexport const MESH='+json.dumps(np.round(combined,7).reshape(-1).tolist(),separators=(',',':'))+';\n',encoding='utf-8')
print(f'Exported {len(mesh)} vertices; {out}')
