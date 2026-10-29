"""Continuous musical construction. No preset list, phrase timer or random jumps."""
import math
from .organism import JointNetwork


def clamp(value,low=0.,high=1.):
    return max(low,min(high,value))


class Morphogenesis:
    def __init__(self):
        self.strength=0.
        self.shape=[.42,.45,.65,.35]  # curvature, opening, layer distance, depth
        self.detail=[.3,0.,.4,.5]     # sector fold, layer screw, petal blend, richness
        self.phases=[0.,0.]
        self.envelope=[0.,0.,0.]
        self.flow=0.;self.memory=0.
        self.latent=[1.7,2.5,22.]
        self.organism=JointNetwork()

    def update(self,model,motion,dt,selected=False,running=True):
        if model.paused:return
        dt=clamp(dt,0.,.15)
        self.strength+=(float(selected)-self.strength)*(1-math.exp(-dt*(2. if selected else 4.)))
        if not selected or not running:return
        self.organism.update(dt,motion,model)
        kick,body,detail,activity=motion.values
        source=(max(motion.levels[0],kick*.6),body,detail)
        for i in range(3):
            self.envelope[i]+=(source[i]-self.envelope[i])*(1-math.exp(-dt*.85))
        low,mid,high=self.envelope
        drive=clamp(activity*1.6)
        advance=dt*drive*model.brake
        # Integrals retain musical history. Identical volume is not an identical pose.
        self.flow+=advance*(.48+mid*1.8+high*.65)
        self.memory+=advance*(kick*1.9+low*.23+high*.11)
        f,m=self.flow,self.memory
        # A smooth coupled system, forced by the spectrum, replaces periodic
        # open/close oscillators. There is no repeat interval or random jump.
        duration=advance*(.14+mid*.08)
        steps=max(1,math.ceil(duration/.008));h=duration/steps
        rho=26.+low*5.+high*3.
        def derivative(p):
            x,y,z=p
            return (10.*(y-x),x*(rho-z)-y+kick*2.,x*y-z*8./3.)
        for _ in range(steps):
            delta=derivative(self.latent)
            middle=[x+d*h*.5 for x,d in zip(self.latent,delta)]
            delta=derivative(middle)
            self.latent=[x+d*h for x,d in zip(self.latent,delta)]
        x,y,z=self.latent
        steer=model.fx[0]-.5;spread=model.fx[1]-.3
        targets=(
            clamp(.12+1.25*(.5+.44*math.tanh(x/9.))+.13*(mid-low)+steer*.35,.12,1.48),
            clamp(.48+low*.22+.32*math.tanh(y/14.)+spread*.25),
            clamp(.72+mid*.35+.48*math.tanh((z-24.)/12.),.25,1.5),
            clamp(.50+mid*.55+.40*math.tanh((y-x)/9.)+spread*.5,.05,1.4),
        )
        details=(
            clamp(.48+.40*math.tanh((z-22.)/10.)+high*.12),
            clamp(.80*math.tanh(x/13.+y/20.)+steer*.6,-1.1,1.1),
            clamp(.50+.44*math.tanh((y-x)/12.)),
            clamp(.50+mid*.25+high*.25+.24*math.tanh((z-23.)/10.)),
        )
        follow=1-math.exp(-dt*1.1)
        for i in range(4):
            self.shape[i]+=(targets[i]-self.shape[i])*follow
            self.detail[i]+=(details[i]-self.detail[i])*follow
        self.phases[:]=[f,m]

    def reset(self):
        self.__init__()


GLSL=r'''
#ifdef ORGANIC_EVOLUTION
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
