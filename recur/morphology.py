"""Continuous musical construction. No preset list, phrase timer or random jumps."""
import math


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

    def update(self,model,motion,dt,selected=False,running=True):
        if model.paused:return
        dt=clamp(dt,0.,.15)
        self.strength+=(float(selected)-self.strength)*(1-math.exp(-dt*(2. if selected else 4.)))
        if not selected or not running:return
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
void organicFrame(float theta,float band,out vec3 p,out mat3 frame,out float moduleSize){
 float u=theta/(PI*2.),s=(u-.5)*6.;
 float curvature=evolution_shape.x,opening=evolution_shape.y;
 float spacing=evolution_shape.z,depth=evolution_shape.w;
 float split=evolution_detail.x,screw=evolution_detail.y,petals=evolution_detail.z;
 float flow=evolution_phase.x,memory=evolution_phase.y;
 float a=s*curvature+band*screw*.13;
 float base=.70/curvature;
 float winding=(u-.5)*.24*smoothstep(.85,1.45,curvature);
 float radius=(base+(band-1.)*spacing*.13+winding)*(1.+opening*.42);
 float harmonic=mix(cos(a*3.+band*.22),cos(a*5.-band*.18),petals);
 radius+=harmonic*.19*split*smoothstep(.25,.8,curvature);
 p=vec3(sin(a)*radius,cos(a)*radius,0.);
 // Mean-centred bend: a continuous ribbon curls into a multi-layer spiral.
 float mean=sin(3.*curvature)/(3.*curvature);
 p.y-=base*mean*(1.+opening*.42);
 float ribbon=(1.-smoothstep(.35,1.,curvature))*(.65+.35*petals);
 float amplitude=.25+.60*split;
 vec2 openPath=vec2(s*.70,amplitude*sin(s*1.25+flow*.17)+(band-1.)*spacing*.12);
 p.xy=mix(p.xy,openPath,ribbon);
 float sector=floor(min(u,.99999)*6.);
 float v=fract(u*6.);
 float anchor=((sector+.5)/6.-.5)*6.*curvature+band*screw*.13;
 vec2 pivot=vec2(sin(anchor),cos(anchor))*radius;
 pivot.y-=base*mean*(1.+opening*.42);
 float anchorS=((sector+.5)/6.-.5)*6.;
 pivot=mix(pivot,vec2(anchorS*.70,amplitude*sin(anchorS*1.25+flow*.17)+(band-1.)*spacing*.12),ribbon);
 float hinge=split*(.35+.6*sin(flow*.39+band*.63))*(v-.5)*2.;
 mat3 sectorFold=rz(hinge);
 p.xy=pivot+(sectorFold*vec3(p.xy-pivot,0.)).xy;
 p.z=(band-1.)*depth*.13+depth*.48*sin(a*2.-flow*.46+band*.65);
 p.z+=split*.42*sin(v*PI)*sin(anchor+flow*.23+memory*.08);
 float layerRoll=screw*(band-2.)*.19+.17*sin(flow*.24+band*.75+memory*.10)*depth;
 mat3 layer=rz(layerRoll)*rx(depth*.18*sin(flow*.17+band*.55));
 p=layer*p;
 // Low-frequency attacks compress the mechanism, instead of shaking its points.
 p*=1.+motion.x*.11+expansion*.70;
 float fan=(opening-.5)*1.55+.62*split*sin(a*3.-flow*.7+band*.4+memory*.06)+motion.x*.26;
 float tangent=mix(-a,atan(amplitude*1.25*cos(s*1.25+flow*.17),.70),ribbon);
 frame=layer*sectorFold*rz(tangent-PI*.5)*ry(fan);
 moduleSize=.31+.07*opening+band*.003;
}
void remodel(float theta,float band,inout vec3 center,inout mat3 local){
 if(evolution_strength<.00001)return;
 vec3 p;mat3 frame;float moduleSize;
 organicFrame(theta,band,p,frame,moduleSize);
 center=mix(center,p,evolution_strength);
 local=local*(1.-evolution_strength)+frame*moduleSize*evolution_strength;
}
#endif
'''


def position(theta,band,shape,detail,phases,kick=0.,expansion=0.):
    """CPU equivalent of the shader's centre path, for geometric verification."""
    u=theta/math.tau;s=(u-.5)*6.
    curvature,opening,spacing,depth=shape
    split,screw,petals,_=detail;flow,memory=phases
    a=s*curvature+band*screw*.13;base=.70/curvature
    x=clamp((curvature-.85)/.60);winding=(u-.5)*.24*x*x*(3-2*x)
    radius=(base+(band-1)*spacing*.13+winding)*(1+opening*.42)
    x=clamp((curvature-.25)/.55)
    harmonic=(1-petals)*math.cos(a*3+band*.22)+petals*math.cos(a*5-band*.18)
    radius+=harmonic*.19*split*x*x*(3-2*x)
    mean=math.sin(3*curvature)/(3*curvature)
    px=math.sin(a)*radius;py=math.cos(a)*radius-base*mean*(1+opening*.42)
    x=clamp((curvature-.35)/.65);ribbon=(1-x*x*(3-2*x))*(.65+.35*petals)
    amplitude=.25+.60*split
    px=px*(1-ribbon)+s*.70*ribbon
    py=py*(1-ribbon)+(amplitude*math.sin(s*1.25+flow*.17)+(band-1)*spacing*.12)*ribbon
    sector=math.floor(min(u,.99999)*6);v=(u*6)%1
    anchor=((sector+.5)/6-.5)*6*curvature+band*screw*.13
    pivotx=math.sin(anchor)*radius;pivoty=math.cos(anchor)*radius-base*mean*(1+opening*.42)
    anchor_s=((sector+.5)/6-.5)*6
    pivotx=pivotx*(1-ribbon)+anchor_s*.70*ribbon
    pivoty=pivoty*(1-ribbon)+(amplitude*math.sin(anchor_s*1.25+flow*.17)+(band-1)*spacing*.12)*ribbon
    hinge=split*(.35+.6*math.sin(flow*.39+band*.63))*(v-.5)*2
    dx,dy=px-pivotx,py-pivoty
    px=pivotx+math.cos(hinge)*dx-math.sin(hinge)*dy
    py=pivoty+math.sin(hinge)*dx+math.cos(hinge)*dy
    pz=(band-1)*depth*.13+depth*.48*math.sin(a*2-flow*.46+band*.65)
    pz+=split*.42*math.sin(v*math.pi)*math.sin(anchor+flow*.23+memory*.08)
    tilt=depth*.18*math.sin(flow*.17+band*.55)
    py,pz=math.cos(tilt)*py-math.sin(tilt)*pz,math.sin(tilt)*py+math.cos(tilt)*pz
    roll=screw*(band-2)*.19+.17*math.sin(flow*.24+band*.75+memory*.10)*depth
    px,py=math.cos(roll)*px-math.sin(roll)*py,math.sin(roll)*px+math.cos(roll)*py
    return tuple(value*(1+kick*.11+expansion*.70) for value in (px,py,pz))
