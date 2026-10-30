"""Audio-led stage compositions, with facet meshes and spatial reassembly.

The director edits on measured musical attacks and phrases, never on a wall-clock
preset playlist. Each composition keeps developing between edits.
"""
import math
import numpy as np
from .organism import rotate

NAMES=('PORTAL','KALEIDOSCOPE','FOLD','ORBIT','RIBBON','PRISM')


def smooth(value):
    value=np.clip(value,0.,1.)
    return value*value*(3-2*value)


class VJDirector:
    def __init__(self):
        self.source=self.target=0
        self.source_variant=self.variant=0
        self.blend=1.;self.edit_beat=0.;self.edits=0
        self.time=0.;self.beat=0.;self.duration=2.
        self.fx=[.5,.3]
        self.totals=np.zeros(6);self.mean=np.zeros(3);self.previous=np.zeros(3)
        self.last_used=np.full(6,-24.);self.last_used[0]=0.
        self.history=[]
        self.arc_delta=None;self.angle_delta=None
        self.j=np.broadcast_to(np.arange(216)[None,:],(9,216))
        self.b=np.broadcast_to(np.arange(9)[:,None],(9,216))
        self.centers=np.zeros((9,216,3),dtype='f4')
        self.frames=np.zeros((9,216,3,3),dtype='f4')
        self.packed=np.zeros((9,4,216,4),dtype='f4')

    @property
    def label(self):return NAMES[self.target]

    def update(self,model,motion,dt):
        if model.paused:return
        dt=max(0.,min(.1,dt))
        self.fx=list(model.fx)
        activity=motion.values[3]
        self.time+=dt*min(1.,activity*1.7)*model.brake
        self.beat=motion.beat
        levels=np.asarray(motion.levels)
        self.mean+=(levels-self.mean)*(1-math.exp(-dt*.9))
        totals=np.asarray(motion.voice_totals)
        change=np.maximum(0.,totals-self.totals);self.totals=totals.copy()
        age=max(0.,self.beat-self.edit_beat)
        self.blend=min(1.,age/self.duration) if self.edits else 1.
        novelty=float(np.linalg.norm(levels-self.mean))
        attack=bool(change.max()>.22)
        near_phrase=self.beat%4<.45 or self.beat%4>3.85
        # Quiet passages hold their composition. Musical changes can edit early;
        # sustained sections get phrase edits, only when an actual attack arrives.
        edit=attack and self.blend>=1. and activity>.12 and (
            (age>=4. and novelty>.32) or (age>=8. and near_phrase) or age>=18.)
        if not edit:return
        low,mid,high=self.mean
        scores=np.array([.5+low*.9,.4+high*.8+mid*.3,
                         .5+mid*.8+(1-low)*.3,.4+(1-activity)*.7+mid*.6,
                         .35+(1-low)*.5+mid*.4,.4+low*.5+high*.7])
        signature=float(np.dot(totals,[.19,.47,.31,.29,.23,.37]))
        scores+=np.minimum(8.,(self.beat-self.last_used)/4)*.12
        scores+=np.sin(signature+np.arange(6)*2.4)*.22
        scores[self.target]-=4.
        if len(self.history)>1:scores[self.history[-2][1]]-=.8
        self.source,self.source_variant=self.target,self.variant
        self.target=int(np.argmax(scores));self.variant=int(signature*3.7+self.edits)%12
        self.duration=max(.6,round(self.beat)+2.-self.beat)
        self.edit_beat=self.beat;self.blend=0.;self.edits+=1
        self.arc_delta=None;self.angle_delta=None
        self.last_used[self.target]=self.beat
        self.history.append((self.beat,self.target))
        self.previous=levels.copy()

    def layout(self,family,variant,motion):
        """Return positions, Euler articulation and anisotropic panel scales."""
        j,b=self.j,self.b;t=self.time
        kick,body,detail,activity=motion.values
        low,mid,high=motion.levels
        phase=t*(.6+mid*.6)
        if family==0:
            a=(j%72)/72*math.tau+t*.13
            depth=((b*3+j//72)/27+t*.14)%1.
            z=-5.+depth*8.2
            sides=(6,8,12)[variant%3]
            r=(1.48+low*.18+kick*.12)/np.cos((a+math.pi/sides)%(math.tau/sides)-math.pi/sides)
            r+=.13*np.sin(a*3-phase+depth*2)
            r*=.88+.20*np.sin(depth*math.tau-phase*.35)
            x,y=r*np.cos(a),r*np.sin(a)
            angles=(np.full_like(a,math.pi/2),np.zeros_like(a),a+math.pi/2)
            fade=smooth(depth/.08)*smooth((1-depth)/.08)
            sizes=((.14+mid*.035)*fade,.42*fade,.035*fade)
        elif family==1:
            order=(4,6,8)[variant%3];sector=j%order
            q=(j//order+.5)/(216/order)
            a=sector/order*math.tau+(b-4)*.055
            a+=(q-.5)*(.5+.8*np.sin(phase*.45))+t*.15
            r=.22+q*(2.+low*.5)+kick*q*.24
            x,y=r*np.cos(a),r*np.sin(a)
            z=(b-4)*.14+np.sin(q*math.pi)*np.sin(phase+sector*math.pi)*.45
            angles=(.4*np.sin(q*math.pi+phase+b*.2),
                    .8*np.sin(q*math.tau-phase)+kick*.5,a)
            sizes=(.14+q*.12,.16+q*.25,.035)
        elif family==2:
            u=(j%18-8.5)*.28;v=(j//18-5.5)*.25
            bend=.65*np.sin(phase*.21+variant*.4)
            x=u*np.sinc(u*bend/math.pi);y=v
            z=.9*np.sin(u*1.4+phase+b*.35)+.45*np.sin(v*1.7-phase*.7)+(b-4)*.17
            z+=u*u*bend*.3
            angles=(np.arctan(.765*np.cos(v*1.7-phase*.7)),
                    -np.arctan(1.26*np.cos(u*1.4+phase+b*.35)),
                    np.full_like(u,.15*np.sin(phase*.25)))
            visible=np.where(b%3==variant%3,1.,.001)
            sizes=(.30*visible,.33*visible,.04*visible)
        elif family==3:
            yy=1-2*(j//18+.5)/12.;rr=np.sqrt(1-yy*yy)
            a=(j%18+(j//18%2)*.5)/18*math.tau+t*.3+b*.11
            r=1.17+b*.09+kick*.18*(1+.3*np.cos(a*3))
            x,y,z=r*np.cos(a)*rr,r*yy,r*np.sin(a)*rr
            torus=float(smooth((.5+.5*np.sin(phase*.24+variant))*.95))
            ring=1.3+.38*np.cos(yy*math.pi)
            x=x*(1-torus)+ring*np.cos(a)*torus
            z=z*(1-torus)+ring*np.sin(a)*torus
            y=y*(1-torus)+.48*np.sin(yy*math.pi)*torus
            angles=(-np.arcsin(yy),math.pi/2-a,a*.08+phase*.15)
            visible=np.where(b%3==variant%3,1.,.001)
            sizes=((.16+mid*.06)*visible,(.20+high*.06)*visible,.24*visible)
        elif family==4:
            u=(j%18-8.5)*.31;v=(j//18-5.5)*.13
            x=u;y=.75*np.sin(u*1.2+phase+b*.35)+v+(b-4)*.10
            z=.8*np.cos(u*.9-phase)+(b-4)*.24+v*.45*np.sin(phase*.6)
            angles=(np.full_like(u,.2*np.sin(phase*.6)),
                    np.arctan(.72*np.sin(u*.9-phase)),
                    np.arctan(.9*np.cos(u*1.2+phase+b*.35)))
            visible=np.where(b%3==variant%3,1.,.001)
            sizes=(.35*visible,.18*visible,.04*visible)
        else:
            face=j//36;u=(j%6-2.5)/3;v=((j%36)//6-2.5)/3
            r=1.1+b*.13+kick*.28
            x=np.where(face<2,np.where(face==0,r,-r),u*r)
            y=np.where((face>=2)&(face<4),np.where(face==2,r,-r),v*r)
            z=np.where(face>=4,np.where(face==4,r,-r),np.where(face<2,u*r,v*r))
            x,y,z=np.broadcast_arrays(x,y,z)
            y=np.where(face>=4,v*r,y)
            z=np.where((face>=2)&(face<4),v*r,z)
            angles=(np.where(face==2,-math.pi/2,np.where(face==3,math.pi/2,0.)),
                    np.where(face==0,math.pi/2,np.where(face==1,-math.pi/2,np.where(face==5,math.pi,0.))),
                    np.zeros_like(u))
            visible=np.where(b%3==variant%3,1.,.001)
            sizes=((.36+b*.043)*visible,(.45+b*.055)*visible,.045*visible)
        centers=np.stack(np.broadcast_arrays(x,y,z),axis=-1)
        angles=np.stack(np.broadcast_arrays(*angles),axis=-1)
        sizes=np.stack(np.broadcast_arrays(*sizes,np.zeros_like(x)),axis=-1)[...,:3]
        # Compositions have their own framing, including asymmetric wide sheets.
        if family in (2,4,5):
            global_angles=np.array([.20*np.sin(t*.19),.24*np.sin(t*.13),.2*np.sin(t*.17)])
            centers=rotate(centers,global_angles)
            angles+=global_angles
        return centers,angles,np.maximum(sizes,.0001)

    def build(self,state,motion,expansion):
        destination,angles,scales=self.layout(self.target,self.variant,motion)
        if self.blend<1.:
            source,old_angles,old_scales=self.layout(self.source,self.source_variant,motion)
            p=smooth(self.blend)
            # Polar transport, with a shared folded bridge, avoids a ring ripping
            # straight into a Cartesian line. Every cell retains angular order.
            start=np.arctan2(source[...,1],source[...,0])
            end=np.arctan2(destination[...,1],destination[...,0])
            delta=(end-start+math.pi)%math.tau-math.pi
            if self.arc_delta is not None:
                delta=self.arc_delta+(delta-self.arc_delta+math.pi)%math.tau-math.pi
            self.arc_delta=delta.copy()
            radius=np.linalg.norm(source[...,:2],axis=-1)*(1-p)+np.linalg.norm(destination[...,:2],axis=-1)*p
            arc=start+delta*p+np.sin(math.pi*p)*.65
            centers=np.stack((radius*np.cos(arc),radius*np.sin(arc),
                              source[...,2]*(1-p)+destination[...,2]*p),axis=-1)
            centers[...,2]+=.35*np.sin(math.pi*p)*np.sin(self.j/216*math.tau*3)
            turn=(angles-old_angles+math.pi)%math.tau-math.pi
            if self.angle_delta is not None:
                turn=self.angle_delta+(turn-self.angle_delta+math.pi)%math.tau-math.pi
            self.angle_delta=turn.copy()
            angles=old_angles+turn*p
            angles[...,1]+=np.sin(math.pi*p)*np.sin(self.j/216*math.tau*6)*.7
            scales=old_scales*(1-p)+scales*p
            # The middle of an edit is an ordered assembly, rather than an
            # arbitrary cloud made by mixing unrelated point correspondences.
            bridge=4 if self.source in (2,4) or self.target in (2,4) else 1
            folded,fold_angles,fold_scales=self.layout(bridge,(self.source+self.target+self.variant)%12,motion)
            amount=math.sin(math.pi*p)**2
            centers=centers*(1-amount)+folded*amount
            angles=angles*(1-amount)+fold_angles*amount
            scales=scales*(1-amount)+fold_scales*amount
        else:centers=destination
        steer=self.fx[0]-.5;spread=self.fx[1]-.3
        torsion=steer*(centers[...,2]*.45+np.linalg.norm(centers[...,:2],axis=-1)*.18)
        x,y=centers[...,0].copy(),centers[...,1].copy()
        centers[...,0]=(x*np.cos(torsion)-y*np.sin(torsion))*(1+spread*.7)
        centers[...,1]=(x*np.sin(torsion)+y*np.cos(torsion))*(1+spread*.7)
        centers[...,2]*=1+spread*.6
        angles[...,2]+=torsion
        angles[...,1]+=steer*np.sin(self.j/216*math.tau)*.7
        centers*=1+expansion*.10
        self.centers[:]=centers
        axes=np.broadcast_to(np.eye(3),(9,216,3,3))
        for column in range(3):self.frames[...,column]=rotate(axes[...,column],angles)*scales[...,column,None]
        self.packed[:,0,:,:3]=centers;self.packed[:,0,:,3]=1.
        for column in range(3):self.packed[:,column+1,:,:3]=self.frames[...,column]
        profiles=((0.,.05),(1.,.15),(.15,.1),(.15,1.),(.7,.05),(.0,.0))
        profile=np.array(profiles[self.target])
        if self.blend<1.:profile=np.array(profiles[self.source])*(1-smooth(self.blend))+profile*smooth(self.blend)
        self.packed[:,1,:,3]=profile[0];self.packed[:,2,:,3]=profile[1]
        return self.packed.reshape(36,216,4)
