"""Music-led stage direction and shared pose-texture lookup."""
import math
from .vj import VJDirector


class Morphogenesis:
    def __init__(self):
        self.strength=0.
        self.shape=[.42,.45,.65,.35]
        self.detail=[.3,0.,.4,1.]
        self.phases=[0.,0.]
        self.vj=VJDirector()

    def update(self,model,motion,dt,selected=False,running=True):
        if model.paused:return
        dt=max(0.,min(.15,dt))
        self.strength+=(float(selected)-self.strength)*(1-math.exp(-dt*(2. if selected else 4.)))
        if not selected or not running:return
        self.vj.update(model,motion,dt)
        self.phases[:]=[self.vj.time,self.vj.beat]

    def reset(self):self.__init__()


GLSL=r'''
#ifdef ORGANIC_EVOLUTION
void stageProfile(float theta,float band,float assembly,inout vec3 p,inout vec3 n){
 int index=int(floor(theta/(PI*2.)*216.+.5))%216;
 int row=int(band+.5)*4;
 float taper=texelFetch(organism_pose,ivec2(index,row+1),0).w*evolution_strength+assembly*.7*(1.-evolution_strength);
 float rounded=texelFetch(organism_pose,ivec2(index,row+2),0).w*evolution_strength;
 float width=1.-taper*.85*abs(p.x/.44);
 n=vec3(n.x+n.y*p.y*taper*.85*sign(p.x)/(.44*max(width,.05)),n.y/max(width,.05),n.z);
 p.y*=width;
 vec3 shell=normalize(p/vec3(.44,.35,.25))*vec3(.44,.35,.25);
 p=mix(p,shell,rounded);
 n=normalize(mix(n,normalize(p/vec3(.1936,.1225,.0625)),rounded));
}
void remodel(float theta,float band,inout vec3 center,inout mat3 local){
 if(evolution_strength<.00001)return;
 int index=int(floor(theta/(PI*2.)*216.+.5))%216;
 int row=int(band+.5)*4;
 vec3 p=texelFetch(organism_pose,ivec2(index,row),0).xyz;
 mat3 frame=mat3(texelFetch(organism_pose,ivec2(index,row+1),0).xyz,
                 texelFetch(organism_pose,ivec2(index,row+2),0).xyz,
                 texelFetch(organism_pose,ivec2(index,row+3),0).xyz);
 center=mix(center,p,evolution_strength);
 local=local*(1.-evolution_strength)+frame*evolution_strength;
}
#endif
'''
