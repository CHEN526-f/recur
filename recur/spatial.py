"""A single ordered 3D construction with independent local motion fields."""
import math
import numpy as np
import moderngl
from .materials import SURFACE_FRAGMENT,polished_rib,beveled_box
from .structures import GLSL


def note_field(note,now,theta):
    p=note.phase(now);env=note.envelope(now)*note.strength
    angle=math.atan2(note.center[1]/.65,note.center[0]/1.25)
    width=.48+note.variant*.35
    travel=(p-.5)*.65*note.direction if note.voice in (1,5) else 0.
    distance=(theta-angle-travel+math.pi)%math.tau-math.pi
    region=np.exp(-.5*(distance/width)**2)
    fields=np.zeros((len(theta),5))
    v=note.voice
    if v==0:
        fields[:,0]=env*region*.22
        fields[:,3]=env*region*.25
    elif v==1:
        fields[:,2]=env*region*.45
        fields[:,3]=-env*region*.70
        fields[:,1]=env*region*np.sin(distance)*.12
    elif v==2:
        petals=3+int(note.variant*4)
        wave=np.cos(theta*petals+angle)
        shape=wave*(.25+.75*region)
        fields[:,0]=env*shape*.12
        fields[:,3]=env*shape*.60
    elif v==3:
        fields[:,3]=env*region*(.65+.2*note.variant)*note.direction
        fields[:,1]=env*region*.10*note.direction
    elif v==4:
        fields[:,4]=env*(.28+.35*region)
        fields[:,2]=env*np.sin(theta-angle)*.15
    else:
        ripple=np.sin(distance*(4+int(note.variant*3))-p*math.tau)
        fields[:,0]=env*region*ripple*.045
        fields[:,3]=env*region*ripple*.46
    return fields


def deformation(stage):
    theta=np.arange(216)/216*math.tau
    summed=np.zeros((216,5))
    for note in stage.notes:summed+=note_field(note,stage.time,theta)
    limits=np.array([.20,.12,.40,.82,.58])
    bounded=limits*np.tanh(summed/limits)
    # Keep the angular map strictly ordered, even under dense, opposing inputs.
    step=math.tau/216
    slope=np.clip((np.roll(bounded[:,1],-1)-bounded[:,1])/step,-.32,.32)
    slope-=slope.mean()
    ordered=np.r_[0.,np.cumsum(slope[:-1])*step]
    ordered-=ordered.mean()
    ordered*=min(1.,.12/max(.12,float(abs(ordered).max())))
    bounded[:,1]=ordered
    packed=np.zeros((9,2,216,4),dtype='f4')
    # The same positional field acts on every depth layer, preserving their order.
    packed[:,0,:,:]=bounded[None,:,:4]
    packed[:,1,:,0]=bounded[None,:,4]
    return packed.reshape(18,216,4)


VERTEX=r'''#version 330
in vec3 in_pos;in vec3 in_normal;in float in_material;
in vec3 in_tile;in vec3 in_tile_normal;
uniform mat4 projection;uniform mat4 view;
uniform vec2 orbit;uniform vec2 fx;uniform float phase;
uniform float weights[10];uniform sampler2D deformation_map;uniform float expansion;
uniform vec4 motion;uniform vec2 motion_phase;
out vec3 world;out vec3 normal;out float material;out float instance;
const float PI=3.14159265359;
mat3 rx(float a){float c=cos(a),s=sin(a);return mat3(1,0,0,0,c,s,0,-s,c);}
mat3 ry(float a){float c=cos(a),s=sin(a);return mat3(c,0,-s,0,1,0,s,0,c);}
mat3 rz(float a){float c=cos(a),s=sin(a);return mat3(c,s,0,-s,c,0,0,0,1);}
// ARCHITECTURE
void main(){
 float id=float(gl_InstanceID),band=floor(id/216.);
 float theta=mod(id,216.)/216.*2.*PI;
 vec3 center;mat3 local;float size;
 structure(theta,band,phase,vec3(0.),weights,0.,center,local,size);
 int row=int(band)*2,index=int(mod(id,216.));
 vec4 field=texelFetch(deformation_map,ivec2(index,row),0);
 float depth=texelFetch(deformation_map,ivec2(index,row+1),0).x;
 center.xy=(rz(field.y)*vec3(center.xy*(1.+field.x),0.)).xy;
 center.z=center.z*(1.+depth)+field.z;
 local=rz(field.y)*local*ry(field.w+(fx.x-.5)*.35);
 float tile=weights[3]+weights[9];
 vec3 pos=mix(in_pos,in_tile,tile);
 vec3 norm=normalize(mix(in_normal,in_tile_normal,tile));
 mat3 camera=rx(orbit.y)*ry(orbit.x);
 vec3 p=camera*(center+local*pos*size)*(1.+(fx.y-.3)*.18)*(1.+expansion*.20);
 world=p;normal=camera*local*norm;material=in_material;instance=id;
 gl_Position=projection*view*vec4(p,1.);
}
'''.replace('// ARCHITECTURE',GLSL)


class SpatialStageRenderer:
    def __init__(self,ctx):
        self.ctx=ctx;self.program=ctx.program(vertex_shader=VERTEX,fragment_shader=SURFACE_FRAGMENT)
        self.resources=[];self.vaos=[]
        rib=polished_rib();tile=beveled_box()
        tile7=np.column_stack((tile,np.zeros(len(tile))))
        pad=(-len(rib))%len(tile)
        mixed=rib if not pad else np.concatenate((rib,rib[:pad]))
        meshes=(np.concatenate((rib,rib[:,:6]),axis=1),
                np.concatenate((tile7,tile),axis=1),
                np.concatenate((mixed,np.tile(tile,(len(mixed)//len(tile),1))),axis=1))
        for mesh in meshes:
            vertices,indices=np.unique(mesh.astype('f4'),axis=0,return_inverse=True)
            vbo=ctx.buffer(vertices.astype('f4').tobytes());ibo=ctx.buffer(indices.astype('u4').tobytes())
            self.resources.extend((vbo,ibo))
            self.vaos.append(ctx.vertex_array(self.program,[(vbo,'3f 3f 1f 3f 3f','in_pos','in_normal','in_material','in_tile','in_tile_normal')],index_buffer=ibo))
        self.texture=ctx.texture((216,18),4,dtype='f4')
        self.texture.filter=(moderngl.NEAREST,moderngl.NEAREST)

    def prepare(self,stage,projection,view,resolution,orbit,fx,palette,zoom,expansion=0.):
        self.texture.write(deformation(stage).tobytes());self.texture.use(5)
        self.program['projection'].write(projection.T.tobytes());self.program['view'].write(view.T.tobytes())
        self.program['weights'].write(stage.weights.astype('f4').tobytes())
        self.program['phase']=stage.time*.12
        tile=stage.weights[3]+stage.weights[9]
        self.mesh=1 if tile>.99999 else 0 if tile<.00001 else 2
        for name,value in (('resolution',resolution),('orbit',tuple(orbit)),('fx',tuple(fx)),
                           ('palette',palette),('camera_position',(0.,0.,zoom)),('opaque_scene',3),
                           ('energy',.1),('evolution_strength',0.),('deformation_map',5),('expansion',expansion),
                           ('motion',(0.,0.,0.,0.)),('motion_phase',(0.,0.))):
            if name in self.program:self.program[name].value=value

    def draw_pass(self,surface_pass):
        self.program['surface_pass']=surface_pass
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.disable(moderngl.BLEND)
        self.ctx.depth_mask=True
        self.vaos[self.mesh].render(instances=216*6)
        self.ctx.disable(moderngl.DEPTH_TEST)
