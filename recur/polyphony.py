"""Independent one-shot visual voices. New notes never retarget older notes."""
from dataclasses import dataclass
import math
import numpy as np

NAMES=('PULSE','ARCS','FAN','RIBBON','PORTAL','SPARKS')
COLORS=((1.,.71,.31),(.86,.92,.98),(.94,.81,.54),(.96,.75,.40),(.75,.84,.93),(1.,.74,.38))
LIFETIMES=(1.65,2.3,2.65,2.1,3.0,1.25)


def ease(value):
    value=np.clip(value,0.,1.)
    return value*value*(3-2*value)


@dataclass
class Note:
    voice:int
    born:float
    strength:float
    serial:int
    center:tuple
    duration:float
    scheduled:bool=False

    def phase(self,now):return max(0.,min(1.,(now-self.born)/self.duration))

    def envelope(self,now):
        age=now-self.born
        return float(ease(age/.09)*(1-ease((age-self.duration*.52)/(self.duration*.48))))


class InputContacts:
    """A key/finger owns only its own contact, independent of animation tails."""
    def __init__(self):self.held={}

    def down(self,token,voice,callback):
        if token in self.held:return False
        self.held[token]=voice;callback(voice);return True

    def up(self,token):return self.held.pop(token,None)
    def clear(self):self.held.clear()

    @property
    def voices(self):return set(self.held.values())

    @staticmethod
    def zone(x,y):
        return min(2,max(0,int(x*3)))+3*min(1,max(0,int(y*2)))


class PolyphonicStage:
    def __init__(self):
        self.time=0.;self.notes=[];self.serial=0;self.levels=[0.,0.,0.]
        self.contacts=InputContacts();self.last=[-10.]*6;self.counts=[0]*6
        self.fx=[.5,.3]

    def reset(self):
        self.notes.clear();self.contacts.clear();self.last=[-10.]*6

    def update(self,model,motion,dt):
        if model.paused:return
        self.time+=max(0.,min(.15,dt))
        self.levels=list(motion.levels);self.fx=list(model.fx)
        self.notes[:]=[note for note in self.notes if self.time-note.born<note.duration]

    def note(self,voice,strength=1.,source='LIVE'):
        if strength<=.015:return None
        if source=='TRACK':
            if voice==0:
                result=self.spawn(0,strength,.19,True)
                if self.levels[0]>.35:self.spawn(4,strength*.5,2.3,True)
                if self.levels[1]>.55 and strength>.8:self.spawn(2,strength*.65,2.,True)
                return result
            if voice==3:
                role=1 if self.levels[2]>.40 else 3
                result=self.spawn(role,strength,.32,True)
                if strength>.72:self.spawn(2,strength*.6,1.5,True)
                return result
            result=self.spawn(5,strength,.16,True)
            if strength>.8 and self.levels[1]>.45:self.spawn(1,strength*.55,.8,True)
            return result
        scheduled=source not in ('LIVE','TOUCH','GRID')
        return self.spawn(voice,strength,.16 if scheduled else 0.,scheduled)

    def spawn(self,voice,strength,cooldown=0.,scheduled=False):
        if self.time-self.last[voice]<cooldown:return None
        # Bound density by declining additional hits, never by removing a live tail.
        if len(self.notes)>=48 or sum(n.voice==voice for n in self.notes)>=8:return None
        self.last[voice]=self.time;self.serial+=1;self.counts[voice]+=1
        anchors=((- .65,-.05),(.45,.18),(.18,.02),(-.12,.12),(-.08,0.),(.65,-.25))
        duration=(.75,1.45,1.8,1.4,2.0,.8)[voice] if scheduled else LIFETIMES[voice]
        note=Note(voice,self.time,min(1.,max(.05,strength)),self.serial,
                  anchors[voice],duration,scheduled)
        self.notes.append(note)
        return note

    def geometry(self,aspect=1.6):
        pieces=[]
        def strip(points,width,color,alpha,closed=False,glass=False):
            if closed:points=np.vstack((points,points[:1]))
            delta=np.gradient(points,axis=0)
            normal=np.column_stack((-delta[:,1],delta[:,0]))
            normal/=np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-6)
            width=np.broadcast_to(np.asarray(width),len(points))
            left=points-normal*width[:,None]/2;right=points+normal*width[:,None]/2
            count=len(points)-1
            pos=np.stack((left[:-1],right[:-1],right[1:],left[:-1],right[1:],left[1:]),axis=1).reshape(-1,2)
            edge=np.tile((-1.,1.,1.,-1.,1.,-1.),count)
            vertex=np.empty((len(pos),9),dtype='f4');vertex[:,:2]=pos
            vertex[:,2:5]=color;vertex[:,5]=alpha
            angles=np.unwrap(np.arctan2(normal[:,1],normal[:,0]))
            vertex[:,6]=edge
            vertex[:,7]=np.stack((angles[:-1],angles[:-1],angles[1:],angles[:-1],angles[1:],angles[1:]),axis=1).reshape(-1)
            vertex[:,8]=float(glass)
            pieces.append(vertex)
        def polygon(points,color,alpha,glass=False):
            middle=np.mean(points,axis=0)
            pos=np.stack((np.broadcast_to(middle,points.shape),points,np.roll(points,-1,axis=0)),axis=1).reshape(-1,2)
            vertex=np.zeros((len(pos),9),dtype='f4');vertex[:,:2]=pos
            vertex[:,2:5]=color;vertex[:,5]=alpha
            vertex[:,8]=float(glass)
            pieces.append(vertex)
        def arc(center,radius,start,length,width,color,alpha,points=96,glass=False):
            a=np.linspace(start,start+length,points)
            path=np.column_stack((np.cos(a),np.sin(a)))*radius+center
            strip(path,width,color,alpha,glass=glass)
        for note in self.notes:
            p=note.phase(self.time);env=note.envelope(self.time)*(.45+.55*note.strength)
            if env<.001:continue
            v=note.voice;c=np.array(note.center);color=np.array(COLORS[v]);seed=note.serial%7
            move=float(ease(p));out=1-(1-p)**3
            if v==0:
                for ring in range(2 if note.scheduled else 3):
                    radius=.12+out*(.65+note.strength*.3)+ring*.12
                    arc(c,radius,0.,math.tau,.022 if ring else .065,color,env*(.82-ring*.18))
                if not note.scheduled:
                    a=np.linspace(0,math.tau,64,endpoint=False)
                    polygon(c+np.column_stack((np.cos(a),np.sin(a)))*(.07+.1*(1-out)),color,env*.32)
            elif v==1:
                for ring in range(4):
                    start=seed*.35+move*1.7+ring*.7
                    length=math.pi*(.2+1.35*float(ease(min(1.,p*2))))
                    arc(c,.29+ring*.12,start,length,.025+ring*.004,color,env*(.85-ring*.13),glass=ring==3)
            elif v==2:
                opening=float(ease(p/.23));angle=move*.7+seed*.08
                for petal in range(6):
                    a=petal*math.tau/6+angle
                    r=.13+opening*.64
                    local=np.array([[.06,0.],[r*.53,-r*.24*opening],[r,0.],[r*.53,r*.24*opening]])
                    cs,sn=math.cos(a),math.sin(a)
                    points=local@np.array([[cs,sn],[-sn,cs]])+c
                    polygon(points,color,env*.55,glass=petal==4)
                    strip(np.vstack((points,points[:1])),.012,color,env*.85)
            elif v==3:
                t=np.linspace(0,1,120)
                x=(t-.5)*aspect*1.7
                y=.30*np.sin(t*math.pi*1.6+seed*.4)+(.5-move)*.7
                points=np.column_stack((x,y))+c
                # A single continuous sail opens then glides away; no position noise.
                width=(.035+.17*np.sin(t*math.pi)**2)*math.sin(math.pi*min(.999,p*.8+.1))
                strip(points,width,color,env*.72)
                strip(points+np.array([0.,.08]),.022,color,env*.55,glass=True)
            elif v==4:
                corners=(4,6,8)[seed%3]
                layers=4 if note.scheduled else 7
                for layer in range(layers):
                    z=(layer+out*1.8)/(layers+1)
                    radius=.14+z*z*1.35
                    a=np.linspace(0,math.tau,corners,endpoint=False)+math.pi/4+move*.28
                    points=np.column_stack((np.cos(a),np.sin(a)))*radius+c
                    strip(np.vstack((points,points[:1])),.010+.018*z,color,env*(.25+.65*z))
            else:
                for spark in range(12):
                    angle=seed*.12
                    grid=np.array([(spark%4-1.5)*.19,(spark//4-1)*.19])
                    cs,sn=math.cos(angle),math.sin(angle)
                    center=c+(grid@np.array([[cs,sn],[-sn,cs]]))*(.2+out*1.2)
                    size=(.012+.025*(1-p))*float(ease(p/.1))
                    points=np.array([[size,0],[0,size],[-size,0],[0,-size]])+center
                    polygon(points,color,env*.9)
        return np.concatenate(pieces) if pieces else np.empty((0,9),dtype='f4')


VERTEX='''#version 330
in vec2 position;in vec4 ink;in vec3 edge;
uniform float aspect;
out vec4 color;out vec3 local;out vec2 point;
void main(){gl_Position=vec4(position.x/aspect,position.y,0.,1.);color=ink;local=edge;point=position;}
'''
FRAGMENT='''#version 330
in vec4 color;in vec3 local;in vec2 point;out vec4 frag;
uniform int surface_pass;uniform sampler2D opaque_scene;uniform vec2 resolution;
void main(){
 bool glass=local.z>.5;
 if((surface_pass==0 && glass)||(surface_pass==1 && !glass))discard;
 float coverage=1.-smoothstep(.68,1.,abs(local.x));
 float a=color.a*coverage;
 float side=clamp(local.x,-1.,1.);
 vec3 n=normalize(vec3(vec2(cos(local.y),sin(local.y))*side*.83,sqrt(max(.1,1.-side*side*.69))));
 vec3 v=normalize(vec3(-point*.12,1.)),r=reflect(-v,n);
 float nv=max(.01,dot(n,v));
 float card=exp(-pow((r.x+.28)/.18,2.))*1.25;
 float rim=exp(-pow((r.y-.54)/.15,2.))*.65;
 vec3 f0=color.rgb;
 vec3 fresnel=f0+(1.-f0)*pow(1.-nv,5.);
 vec3 metal=fresnel*(.14+card+rim)+f0*.035;
 if(glass){
   vec2 uv=gl_FragCoord.xy/resolution;
   vec3 behind=texture(opaque_scene,clamp(uv+n.xy*.008,.001,.999)).rgb;
   float f=.045+.955*pow(1.-nv,5.);
   metal=behind*vec3(.88,.96,.98)*(1.-f)+vec3(.75,.88,1.)*(card+rim)*f;
 }
 frag=vec4(metal*a,a);
}
'''


class StageRenderer:
    def __init__(self,ctx):
        self.ctx=ctx;self.program=ctx.program(vertex_shader=VERTEX,fragment_shader=FRAGMENT)
        self.buffer=ctx.buffer(reserve=4*1024*1024,dynamic=True)
        self.vao=ctx.vertex_array(self.program,[(self.buffer,'2f 4f 3f','position','ink','edge')])

    def prepare(self,stage,aspect,resolution):
        data=stage.geometry(aspect)
        self.vertices=len(data)
        if not len(data):return
        if data.nbytes>self.buffer.size:self.buffer.orphan(data.nbytes)
        self.buffer.write(data.tobytes());self.program['aspect']=aspect
        self.program['resolution']=resolution;self.program['opaque_scene']=3

    def draw_pass(self,surface_pass):
        import moderngl
        if not self.vertices:return
        self.program['surface_pass']=surface_pass
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func=(moderngl.ONE,moderngl.ONE_MINUS_SRC_ALPHA)
        self.vao.render(vertices=self.vertices)
        self.ctx.disable(moderngl.BLEND)
