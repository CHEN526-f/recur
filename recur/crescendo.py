"""Smooth, performed climaxes and original screen-spanning metal architecture."""
import math

import moderngl
import numpy as np


def smoothstep(value):
    value = max(0., min(1., value))
    return value * value * (3. - 2. * value)


class Crescendo:
    """A musical phrase opens the space; isolated notes leave room to breathe."""

    def __init__(self):
        self.excitation = 0.
        self.amount = 0.
        self.sustain = 0.
        self.time = 0.
        self.music_level = 0.
        self.score_target = None

    def note(self, index, gain=1.):
        # Glass has a high sustained partial, bloom a broad chord, noise a short tail.
        strength = {1: .37, 2: .24, 5: .12}.get(index, 0.)
        self.excitation = min(1., self.excitation + strength * max(0., min(1., gain)))

    def drop(self, amount, weights=None):
        if amount <= .1:
            return
        amount=max(0.,min(1.,amount))
        self.excitation=max(self.excitation,.30+.70*amount)
        self.sustain=1.+1.2*amount

    def update(self, model, dt):
        if model.paused:
            return
        dt = max(0., min(.15, dt))
        self.sustain = max(0., self.sustain - dt)
        if not self.sustain:
            self.excitation = max(0., self.excitation - dt * .23)
        desired = max(smoothstep((self.excitation - .25) / .75), model.charge * .55,
                      smoothstep((self.music_level-.40)/.52))
        if self.score_target is not None:
            desired=max(self.score_target,model.charge*.55,self.excitation if self.sustain else 0.)
        rate = 2.3 if desired > self.amount else .95
        self.amount += (desired - self.amount) * (1. - math.exp(-dt * rate))
        self.time += dt * (.16 + self.amount * .22)

    def reset(self):
        self.excitation = self.sustain = 0.


from .structures import GLSL as ARCHITECTURE


VERTEX = r'''
#version 330
#define ORGANIC_EVOLUTION
in vec3 in_pos;in vec3 in_normal;in float in_material;
in vec3 in_tile;in vec3 in_tile_normal;
uniform mat4 projection;uniform mat4 view;
uniform float expansion;uniform float phase;uniform float weights[10];uniform vec3 bands;
uniform vec4 motion;uniform vec2 motion_phase;
uniform float evolution_strength;uniform vec4 evolution_shape;uniform vec4 evolution_detail;uniform vec2 evolution_phase;
uniform sampler2D organism_pose;
uniform vec2 orbit;
out vec3 world;out vec3 normal;out float material;out float instance;
const float PI=3.14159265359;
mat3 rx(float a){float c=cos(a),s=sin(a);return mat3(1,0,0,0,c,s,0,-s,c);}
mat3 ry(float a){float c=cos(a),s=sin(a);return mat3(c,0,-s,0,1,0,s,0,c);}
mat3 rz(float a){float c=cos(a),s=sin(a);return mat3(c,s,0,-s,c,0,0,0,1);}
// ARCHITECTURE
void main(){
 float id=float(gl_InstanceID),band=floor(id/216.)+3.,theta=mod(id,216.)/216.*PI*2.;
 vec3 center;mat3 local;float size;
 structure(theta,band,phase,bands,weights,expansion,center,local,size);
 float emerge=smoothstep(.02,.85,expansion);
 float hierarchy=1.-smoothstep(3.+evolution_detail.w*5.,4.+evolution_detail.w*5.,band);
 emerge=mix(emerge,hierarchy,evolution_strength);
 // The outer rings emerge behind the same mechanism, preserving angular order.
 center.xy*=.86+.14*emerge;
 center.z-=(1.-emerge)*2.8;
 mat3 rotation=rx(orbit.y*.3)*ry(orbit.x*.3);
 float panel=max(evolution_strength,reassembly(weights)*.9);
 vec3 tile=in_tile,tileNormal=in_tile_normal;
 stageProfile(theta,band,reassembly(weights),tile,tileNormal);
 vec3 vertex=mix(in_pos,tile,panel);
 vec3 vertexNormal=normalize(mix(in_normal,tileNormal,panel));
 vec3 p=rotation*(center+local*vertex*size*emerge);
 mat3 cofactors=mat3(cross(local[1],local[2]),cross(local[2],local[0]),cross(local[0],local[1]));
 world=p;normal=rotation*cofactors*vertexNormal;material=in_material;instance=id+648.;
 gl_Position=projection*view*vec4(p,1.);
}
'''
VERTEX=VERTEX.replace('// ARCHITECTURE',ARCHITECTURE)


def blade_mesh():
    """A swept, rounded metal fin, with continuous normals around its curved edge."""
    vertices = []
    rings = []
    for i in range(21):
        t = i / 20. * math.pi
        center = np.array([.06 + .36 * math.sin(t), 0., .46 * math.cos(t)])
        tangent = np.array([.36 * math.cos(t), 0., -.46 * math.sin(t)])
        tangent /= np.linalg.norm(tangent)
        outward = np.array([-tangent[2], 0., tangent[0]])
        ring = []
        width = .035 + .035 * math.sin(t)
        for k in range(8):
            angle = k / 8. * math.tau
            point = center + outward * math.cos(angle) * width
            point += np.array([0., math.sin(angle) * .019, 0.])
            normal = outward * math.cos(angle) / width
            normal += np.array([0., math.sin(angle) / .019, 0.])
            normal /= np.linalg.norm(normal)
            ring.append([*point, *normal, float(k in (2, 3))])
        rings.append(ring)
    for i in range(20):
        for k in range(8):
            j = (k + 1) % 8
            vertices.extend([rings[i][k], rings[i+1][k], rings[i+1][j],
                             rings[i][k], rings[i+1][j], rings[i][j]])
    return np.asarray(vertices, dtype='f4')


class CrescendoRenderer:
    def __init__(self, ctx, fragment_shader):
        self.program = ctx.program(vertex_shader=VERTEX, fragment_shader=fragment_shader)
        from .materials import beveled_box
        mesh=blade_mesh();tile=beveled_box()
        pad=(-len(mesh))%len(tile)
        if pad:mesh=np.concatenate((mesh,mesh[:pad]))
        combined=np.concatenate((mesh,np.tile(tile,(len(mesh)//len(tile),1))),axis=1)
        vertices,indices=np.unique(combined,axis=0,return_inverse=True)
        self.vbo = ctx.buffer(vertices.astype('f4').tobytes())
        self.ibo = ctx.buffer(indices.astype('u4').tobytes())
        self.vao = ctx.vertex_array(self.program, [
            (self.vbo, '3f 3f 1f 3f 3f', 'in_pos', 'in_normal', 'in_material','in_tile','in_tile_normal')
        ],index_buffer=self.ibo)
        from .materials import panel_mesh
        panel,indices=np.unique(panel_mesh(),axis=0,return_inverse=True)
        self.panel_vbo=ctx.buffer(panel.astype('f4').tobytes())
        self.panel_ibo=ctx.buffer(indices.astype('u4').tobytes())
        self.panel_vao=ctx.vertex_array(self.program,[(self.panel_vbo,'3f 3f 1f 3f 3f','in_pos','in_normal','in_material','in_tile','in_tile_normal')],index_buffer=self.panel_ibo)

    def draw(self, state, projection, view, orbit, palette, energy, aspect, surface_pass=0, resolution=(1280,820), weights=None, bands=None, phase=0., motion=(0.,0.,0.,0.), motion_phase=(0.,0.), evolution=None):
        if state.amount < .008 and (evolution is None or evolution.strength<.008):
            return
        self.program['projection'].write(projection.T.tobytes())
        self.program['view'].write(view.T.tobytes())
        for name, value in (
            ('expansion', state.amount),
            ('orbit', tuple(orbit)), ('palette', palette), ('energy', energy), ('aspect', aspect)
            ,('surface_pass',surface_pass),('resolution',resolution),('opaque_scene',3),
            ('camera_position',(0.,0.,float(-view[2,3]))),('phase',phase),('bands',tuple(bands or [0.,0.,0.])),
            ('motion',tuple(motion)),('motion_phase',tuple(motion_phase))
        ):
            if name in self.program:
                self.program[name].value = value
        self.program['weights'].write(np.asarray(weights or [1.]+[0.]*9,dtype='f4').tobytes())
        self.program['evolution_strength']=evolution.strength if evolution else 0.
        for name,value in (('evolution_shape',tuple(evolution.shape) if evolution else (.42,.45,.65,.35)),
                           ('evolution_detail',tuple(evolution.detail) if evolution else (.3,0.,.4,.5)),
                           ('evolution_phase',tuple(evolution.phases) if evolution else (0.,0.)),('organism_pose',5)):
            if name in self.program:self.program[name].value=value
        (self.panel_vao if evolution and evolution.strength>.9999 else self.vao).render(instances=1296)

