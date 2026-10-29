"""An articulated tree: six parent branches, eighteen child fans, nine rib layers.

Each transform is evaluated once per instance on the CPU and shared with both
render passes through a floating-point pose texture. No mesh/preset carousel.
"""
import math
import numpy as np


def unit(vector):
    return vector/np.maximum(np.linalg.norm(vector,axis=-1,keepdims=True),1e-7)


def rotate(vector,angles):
    """XYZ rotations with broadcasting; axes are local to each parent branch."""
    x,y,z=np.moveaxis(vector,-1,0)
    ax,ay,az=np.moveaxis(angles,-1,0)
    c,s=np.cos(ax),np.sin(ax);y,z=c*y-s*z,s*y+c*z
    c,s=np.cos(ay),np.sin(ay);x,z=c*x+s*z,-s*x+c*z
    c,s=np.cos(az),np.sin(az);x,y=c*x-s*y,s*x+c*y
    return np.stack((x,y,z),axis=-1)


class JointNetwork:
    def __init__(self):
        # Distinct points on the same bounded attractor avoid six near-identical
        # branches starting with the same unfolding phase.
        self.states=np.array([[8.,12.,26.],[-9.,-7.,30.],[2.,-4.,24.],
                              [-2.,5.,16.],[13.,9.,35.],[-12.,-15.,28.]])
        self.roots=np.zeros((6,4));self.root_velocity=np.zeros((6,4))
        self.children=np.zeros((18,4));self.child_velocity=np.zeros((18,4))
        self.excitation=np.zeros(6);self.totals=np.zeros(6)
        self.time=0.
        self.band=np.arange(9,dtype=float)[:,None]
        self.u=np.arange(216,dtype=float)[None,:]/216.
        self.parent=np.arange(216)//36;self.child=np.arange(216)//12
        self.parent_samples=np.arange(6)*36+18
        self.child_samples=np.arange(18)*12+6
        # Fade joint transforms at shared edges so the mechanism remains joined.
        self.root_weight=np.sin((np.arange(216)%36+.5)/36*math.pi)**.8
        self.child_weight=np.sin((np.arange(216)%12+.5)/12*math.pi)**.8
        self.centers=np.zeros((9,216,3),dtype='f4')
        self.frames=np.zeros((9,216,3,3),dtype='f4')
        self.packed=np.zeros((9,4,216,4),dtype='f4')

    def update(self,dt,motion,model,enabled=True):
        if not enabled or model.paused:return
        dt=min(.1,max(0.,dt));activity=min(1.,motion.values[3]*1.6)
        advance=dt*activity*model.brake
        self.time+=advance
        totals=np.asarray(motion.voice_totals)
        changes=np.maximum(0.,totals-self.totals);self.totals=totals.copy()
        # Tonal/percussive events travel through broad overlapping branch fields.
        # This does not select a branch pose; it injects force into existing joints.
        azimuth=float(np.dot(totals,(.31,.47,.23,.41,.19,.37)))
        preferences=np.array([[1.,.3,.1],[.2,1.,.4],[.15,.4,1.],
                              [.8,.6,.2],[.25,.8,.65],[.45,.2,.9]])
        event_bands=np.array([changes[0]+changes[4]*.4,changes[2]+changes[3],changes[1]+changes[5]*.45])
        field=.35+.65*(.5+.5*np.cos(np.arange(6)*math.tau/6-azimuth))
        force=np.minimum(2.,(preferences@event_bands)*field)
        self.excitation=np.minimum(1.5,self.excitation+force*.38)
        self.root_velocity[:,0]+=force*.8
        self.child_velocity[:,1]+=np.repeat(force,3)*np.tile([-.45,.6,-.35],6)
        self.excitation*=math.exp(-dt*1.5)
        spectrum=np.asarray(motion.levels)
        drive=preferences@spectrum/np.maximum(preferences.sum(axis=1),1.)
        duration=advance*.16;steps=max(1,math.ceil(duration/.006));h=duration/steps
        rho=25.5+drive*9.+self.excitation*.8
        def derivative(p):
            x,y,z=p.T
            coupling=(np.roll(x,1)+np.roll(x,-1)-2*x)*.22
            return np.column_stack((10*(y-x)+coupling,
                                    x*(rho-z)-y+self.excitation*1.8,
                                    x*y-z*8/3))
        for _ in range(steps):
            first=derivative(self.states)
            self.states+=derivative(self.states+first*h*.5)*h
        x,y,z=self.states.T
        fx=model.fx
        root_targets=np.column_stack((
            np.tanh((y-x)/10)*1.05+(fx[1]-.3)*.65,
            np.tanh(x/12)*1.25+(fx[0]-.5)*.55,
            np.tanh((z-24)/10)*.85,
            .25+.75*(.5+.5*np.tanh((y+z*.18)/12)),
        ))
        offsets=np.tile(np.array([-1.,0.,1.]),6)
        xx,yy,zz=(np.repeat(v,3) for v in (x,y,z))
        parent_force=np.repeat(self.excitation,3)
        child_targets=np.column_stack((
            .5+.45*np.tanh((xx+offsets*yy*.5)/12),  # child winding
            np.tanh((zz-24+offsets*5)/11)*1.0,     # out-of-plane hinge
            np.tanh((yy-xx)/10)*.8+offsets*.35,    # independent fan roll
            np.clip(.45+.35*np.tanh((zz-24+offsets*xx*.5)/10)+parent_force*.22,0.,1.),
        ))
        # Critically damped joints prevent random-looking shaking or angle snaps.
        for values,velocity,target,omega in ((self.roots,self.root_velocity,root_targets,3.2),
                                               (self.children,self.child_velocity,child_targets,4.0)):
            subdivisions=max(1,math.ceil(dt/.025));step=dt/subdivisions
            for _ in range(subdivisions):
                velocity+=(omega*omega*(target-values)-2*omega*velocity)*step
                values+=velocity*step

    def build(self,state,motion,expansion):
        """Compose parent and child hinges, then pack four texels per rib."""
        k,opening,spacing,depth=state.shape
        split,screw,petals,_=state.detail
        flow,memory=state.phases
        u,b=self.u,self.band;s=(u-.5)*6
        # Integrate a varying tangent field, rather than bending a fixed circle
        # or switching to another outline. Each parent changes local curvature.
        sample=np.arange(216)
        bend=np.interp(sample,self.parent_samples,self.roots[:,1])
        lift=np.interp(sample,self.parent_samples,self.roots[:,0])
        a=s*k+b*screw*.13+bend[None,:]*.95
        a+=split*.28*np.sin(s*(1.3+petals)+flow*.11+b*.24)
        step=6/216*.70*(1+opening*.42)
        px=np.cumsum(np.cos(a)*step,axis=1)
        py=np.cumsum(-np.sin(a)*step,axis=1)
        px-=px.mean(axis=1,keepdims=True);py-=py.mean(axis=1,keepdims=True)
        distance=(b-1)*spacing*.13
        px+=np.sin(a)*distance;py+=np.cos(a)*distance
        pz=(b-1)*depth*.14+depth*.38*np.sin(a*2-flow*.35+b*.65)
        pz+=lift[None,:]*depth*.22
        spine=np.stack(np.broadcast_arrays(px,py,pz),axis=-1)
        tangent=unit(np.gradient(spine,axis=1))
        n=unit(np.cross(tangent,np.broadcast_to([0.,0.,1.],tangent.shape)))
        up=unit(np.cross(n,tangent))
        basis=np.stack((n,tangent,up),axis=-1)
        root_p=spine[:,self.parent_samples,:]
        root_basis=basis[:,self.parent_samples,:,:]
        parent_p=root_p[:,self.parent,:]
        parent_basis=root_basis[:,self.parent,:,:]
        local=np.einsum('...ij,...i->...j',parent_basis,spine-parent_p)
        anchors=local[:,self.child_samples,:][:,self.child,:]
        child_delta=local-anchors
        joints=self.children[self.child][None,:,:]
        growth=joints[...,3:4]*self.child_weight[None,:,None]
        v=(np.arange(216)%12/11.-.5)[None,:]
        phi=v*(.7+3.1*joints[...,0])
        radius=.115+.07*opening+b*.012
        bud=np.stack(np.broadcast_arrays(radius*(1-np.cos(phi)),
                                         radius*np.sin(phi),
                                         .10*np.sin(v*math.pi)*joints[...,1]),axis=-1)
        angles=np.stack(np.broadcast_arrays(joints[...,1]*.55,
                                             joints[...,2]*.6,
                                             joints[...,1]*.15),axis=-1)
        child_delta=rotate(child_delta*(1-growth)+bud*growth,
                           angles*self.child_weight[None,:,None])
        local=anchors+child_delta
        roots=self.roots[self.parent][None,:,:]
        # Parent arms stretch and fold about their own shared anchors.
        local[...,1]*=1+(-.30+roots[...,3]*1.10)*self.root_weight[None,:]
        local[...,1]*=1+motion.values[0]*.25*self.root_weight[None,:]
        root_angles=roots[...,:3]*self.root_weight[None,:,None]
        root_angles=np.broadcast_to(root_angles,(9,216,3)).copy()
        # A transient folds the joints as well as increasing overall reach.
        direction=np.where(self.parent%2==0,1.,-1.)[None,:]
        root_angles[...,1]+=motion.values[0]*(.48+.18*roots[...,3])*direction*self.root_weight[None,:]
        root_angles[...,2]+=(b-2)*screw*.09
        local=rotate(local,root_angles)
        offsets=np.zeros_like(local)
        offsets[...,0]=np.broadcast_to(self.excitation[self.parent][None,:],(9,216))*.12*self.root_weight[None,:]
        centers=parent_p+np.einsum('...ij,...j->...i',parent_basis,local+offsets)
        # The skeleton itself lifts and twists; branches remain attached to it.
        layer_angles=np.stack(np.broadcast_arrays(np.sin(b*.55+flow*.12)*depth*.13,
                                                   np.zeros_like(b),
                                                   (b-2)*screw*.10),axis=-1)
        centers=rotate(centers,layer_angles)
        reach=1+min(.75,expansion)*.45+motion.values[0]*.09
        centers*=reach
        self.centers[:]=centers
        # Derivatives are local to each fan, so gaps between branches cannot
        # create a discontinuous frame for the last rib of another branch.
        tangent=unit(np.gradient(centers.reshape(9,18,12,3),axis=2).reshape(9,216,3))
        parent_up=np.zeros_like(local);parent_up[...,2]=1
        parent_up=rotate(parent_up,root_angles)
        parent_up=np.einsum('...ij,...j->...i',parent_basis,parent_up)
        parent_up=rotate(parent_up,layer_angles)
        normal=unit(np.cross(tangent,parent_up))
        binormal=unit(np.cross(normal,tangent))
        fan=(opening-.5)*1.1+joints[...,2]*.55+motion.values[2]*.18+motion.values[0]*.38
        fan=np.broadcast_to(fan,(9,216))
        nn=normal*np.cos(fan)[...,None]-binormal*np.sin(fan)[...,None]
        bb=normal*np.sin(fan)[...,None]+binormal*np.cos(fan)[...,None]
        size=(.255+.055*opening+b*.0018)*(1-growth[...,0]*.15)
        self.frames[...,0]=nn*size[...,None]
        self.frames[...,1]=tangent*size[...,None]
        self.frames[...,2]=bb*size[...,None]
        self.packed[:,0,:,:3]=centers
        # A few broad plates interleave with curved ribs instead of identical fins.
        plate=np.clip((joints[...,0]-.60)*2.5,0.,.7)
        self.packed[:,0,:,3]=np.broadcast_to(plate,(9,216))
        for column in range(3):self.packed[:,column+1,:,:3]=self.frames[...,column]
        return self.packed.reshape(36,216,4)
