"""Instanced 3D metal ribs + HDR lighting and bloom. No reference video textures."""
import math
import numpy as np
import moderngl
from .crescendo import Crescendo, CrescendoRenderer, smoothstep, ARCHITECTURE
from .materials import SURFACE_FRAGMENT, beveled_box, polished_rib,panel_mesh
from .motion import MusicalMotion
from .morphology import Morphogenesis


VERTEX = r'''
#version 330
#define ORGANIC_EVOLUTION
in vec3 in_pos; in vec3 in_normal; in float in_material;
in vec3 in_block; in vec3 in_block_normal;
uniform mat4 projection; uniform mat4 view;
uniform float phase; uniform float weights[10]; uniform vec3 bands;
uniform float energy; uniform float charge; uniform float twist;
uniform vec2 orbit; uniform vec2 fx; uniform float expansion;
uniform vec4 motion; uniform vec2 motion_phase;
uniform float evolution_strength;uniform vec4 evolution_shape;uniform vec4 evolution_detail;uniform vec2 evolution_phase;
uniform sampler2D organism_pose;
out vec3 world; out vec3 normal; out float material; out float instance;
const float PI=3.14159265359;
mat3 rx(float a){float c=cos(a),s=sin(a);return mat3(1,0,0,0,c,s,0,-s,c);}
mat3 ry(float a){float c=cos(a),s=sin(a);return mat3(c,0,-s,0,1,0,s,0,c);}
mat3 rz(float a){float c=cos(a),s=sin(a);return mat3(c,s,0,-s,c,0,0,0,1);}
// ARCHITECTURE
void main(){
 float id=float(gl_InstanceID),band=floor(id/216.),theta=mod(id,216.)/216.*PI*2.;
 vec3 center;mat3 local;float size;
 structure(theta,band,phase,bands,weights,expansion,center,local,size);
 local=local*ry(twist*.22+charge*.13);
 float blockMix=max(weights[3]+weights[9],reassembly(weights)*.9);
 blockMix=mix(blockMix,1.,evolution_strength);
 vec3 block=in_block,blockNormal=in_block_normal;
 stageProfile(theta,band,reassembly(weights),block,blockNormal);
 vec3 pos=mix(in_pos,block,blockMix);
 vec3 norm=normalize(mix(in_normal,blockNormal,blockMix)+vec3(.000001));
 center*=1.+(fx.y-.3)*.12;
 float opening=smoothstep(0.,.8,expansion);
 mat3 rotation=rx(orbit.y*(1.-opening*.7))*ry(orbit.x*(1.-opening*.7));
 vec3 p=rotation*(center+local*pos*size);
 mat3 cofactors=mat3(cross(local[1],local[2]),cross(local[2],local[0]),cross(local[0],local[1]));
 world=p;normal=rotation*cofactors*norm;material=in_material;instance=id;
 gl_Position=projection*view*vec4(p,1.);
}
'''
VERTEX=VERTEX.replace('// ARCHITECTURE',ARCHITECTURE)

SCREEN_VERTEX = r'''
#version 330
in vec2 in_vert;out vec2 uv;
void main(){uv=in_vert*.5+.5;gl_Position=vec4(in_vert,0,1);}
'''

BLUR = r'''
#version 330
uniform sampler2D source;uniform vec2 direction;uniform bool extract;
in vec2 uv;out vec4 frag;
vec3 sampleAt(vec2 p){
 vec3 c=texture(source,p).rgb;
 float l=max(max(c.r,c.g),c.b);
 float knee=clamp((l-.55)/.8,0.,1.);
 return extract?c*knee*knee*.65:c;
}
void main(){
vec3 c=sampleAt(uv)*.227027;
c+=(sampleAt(uv+direction*1.384615)+sampleAt(uv-direction*1.384615))*.316216;
c+=(sampleAt(uv+direction*3.230769)+sampleAt(uv-direction*3.230769))*.070270;
frag=vec4(c,1);}
'''

COMPOSITE = r'''
#version 330
uniform sampler2D scene;uniform sampler2D bloom;uniform sampler2D halo;uniform sampler2D overlay;
uniform vec2 accents;
uniform float clock;uniform bool light_background;uniform bool safe_mode;
in vec2 uv;out vec4 frag;
void main(){
 vec3 c=texture(scene,uv).rgb+texture(bloom,uv).rgb*(safe_mode?.30:.40)
       +texture(halo,uv).rgb*(safe_mode?.16:.24);
 float vignette=smoothstep(.8,.1,length((uv-.5)*vec2(1.1,1)));
 vec3 bg=light_background?vec3(.67,.65,.6):vec3(.002,.0025,.003);
 // Empty HDR pixels stay a subtle charcoal rather than absolute black.
 c+=bg*(.65+.35*vignette);
 c=clamp((c*(2.51*c+.03))/(c*(2.43*c+.59)+.14),0.,1.);
 c=pow(c,vec3(1.0/2.2));
 vec2 p=(uv-.5)*vec2(1.5,1.);
 float ring=exp(-pow((length(p)-accents.x*.7)*140.,2.))*max(0.,1.-accents.x);
 float shutter=exp(-pow((p.x+p.y*.4+1.-accents.y*2.)*48.,2.))*max(0.,1.-accents.y);
 c+=vec3(.23,.19,.12)*(ring+shutter*.6);
 vec4 ui=texture(overlay,vec2(uv.x,1.0-uv.y));
 frag=vec4(mix(c,ui.rgb,ui.a),1);
}
'''


class SculptureRenderer:
    def __init__(self, size):
        self.ctx=moderngl.create_context(require=330)
        self.program=self.ctx.program(vertex_shader=VERTEX,fragment_shader=SURFACE_FRAGMENT)
        mesh=polished_rib()
        block=beveled_box()
        # Repeat complete triangles so both morph endpoints share the same topology.
        pad=(-len(mesh))%len(block)
        if pad:mesh=np.concatenate((mesh,mesh[:pad]))
        blocks=np.tile(block,(len(mesh)//len(block),1))
        combined=np.concatenate((mesh,blocks),axis=1).astype('f4')
        vertices,indices=np.unique(combined,axis=0,return_inverse=True)
        self.vbo=self.ctx.buffer(vertices.astype('f4').tobytes())
        self.ibo=self.ctx.buffer(indices.astype('u4').tobytes())
        self.vao=self.ctx.vertex_array(self.program,[(self.vbo,'3f 3f 1f 3f 3f','in_pos','in_normal','in_material','in_block','in_block_normal')],index_buffer=self.ibo)
        panel,indices=np.unique(panel_mesh(),axis=0,return_inverse=True)
        self.panel_vbo=self.ctx.buffer(panel.astype('f4').tobytes())
        self.panel_ibo=self.ctx.buffer(indices.astype('u4').tobytes())
        self.panel_vao=self.ctx.vertex_array(self.program,[(self.panel_vbo,'3f 3f 1f 3f 3f','in_pos','in_normal','in_material','in_block','in_block_normal')],index_buffer=self.panel_ibo)
        self.climax=Crescendo()
        self.motion=MusicalMotion()
        self.evolution=Morphogenesis()
        self.pose_texture=self.ctx.texture((216,36),4,data=bytes(216*36*16),dtype='f4')
        self.pose_texture.filter=(moderngl.NEAREST,moderngl.NEAREST)
        self.pose_texture.repeat_x=self.pose_texture.repeat_y=False
        self.climax_renderer=CrescendoRenderer(self.ctx,SURFACE_FRAGMENT)
        self.screen=self.ctx.buffer(np.array([-1,-1,1,-1,-1,1,1,1],dtype='f4').tobytes())
        self.blur=self.ctx.program(vertex_shader=SCREEN_VERTEX,fragment_shader=BLUR)
        self.final=self.ctx.program(vertex_shader=SCREEN_VERTEX,fragment_shader=COMPOSITE)
        self.blur_vao=self.ctx.vertex_array(self.blur,[(self.screen,'2f','in_vert')])
        self.final_vao=self.ctx.vertex_array(self.final,[(self.screen,'2f','in_vert')])
        self.light_background=False
        self.palette=0
        self.safe_mode=True
        self.zoom=6.5
        self.instrument_visible=True
        self.orbit=[0.,.35]
        self.orbit_target=[0.,.35]
        self.zoom_target=self.zoom
        self.resize(size)

    def resize(self,size):
        if hasattr(self,'fbo'):
            for resource in (self.fbo,self.color,self.depth,self.msaa_fbo,self.msaa_color,self.msaa_depth,self.bloom_a,self.bloom_b,self.bloom_fbo_a,self.bloom_fbo_b,self.halo_a,self.halo_b,self.halo_fbo_a,self.halo_fbo_b,self.opaque_fbo,self.opaque_color,self.overlay):
                resource.release()
        self.size=tuple(size)
        w,h=self.size
        self.color=self.ctx.texture((w,h),4,dtype='f2')
        self.color.filter=(moderngl.LINEAR,moderngl.LINEAR)
        self.depth=self.ctx.depth_renderbuffer((w,h))
        self.fbo=self.ctx.framebuffer([self.color],self.depth)
        self.opaque_color=self.ctx.texture((w,h),4,dtype='f2')
        self.opaque_color.filter=(moderngl.LINEAR,moderngl.LINEAR)
        self.opaque_fbo=self.ctx.framebuffer([self.opaque_color])
        samples=min(4,self.ctx.max_samples)
        self.msaa_color=self.ctx.renderbuffer((w,h),4,samples=samples,dtype='f2')
        self.msaa_depth=self.ctx.depth_renderbuffer((w,h),samples=samples)
        self.msaa_fbo=self.ctx.framebuffer([self.msaa_color],self.msaa_depth)
        half=(max(1,w//2),max(1,h//2))
        self.bloom_a=self.ctx.texture(half,4,dtype='f2');self.bloom_b=self.ctx.texture(half,4,dtype='f2')
        self.bloom_fbo_a=self.ctx.framebuffer([self.bloom_a]);self.bloom_fbo_b=self.ctx.framebuffer([self.bloom_b])
        quarter=(max(1,w//4),max(1,h//4))
        self.halo_a=self.ctx.texture(quarter,4,dtype='f2');self.halo_b=self.ctx.texture(quarter,4,dtype='f2')
        self.halo_fbo_a=self.ctx.framebuffer([self.halo_a]);self.halo_fbo_b=self.ctx.framebuffer([self.halo_b])
        for texture in (self.color,self.opaque_color,self.bloom_a,self.bloom_b,self.halo_a,self.halo_b):
            texture.filter=(moderngl.LINEAR,moderngl.LINEAR)
            texture.repeat_x=False;texture.repeat_y=False
        self.overlay=self.ctx.texture((w,h),4)
        self.overlay.filter=(moderngl.LINEAR,moderngl.LINEAR)

    def draw(self,model,ui_bytes):
        w,h=self.size
        from .model import ease
        dt=max(0.,min(.1,model.clock-getattr(self,'_last_clock',model.clock)))
        self._last_clock=model.clock
        performance=getattr(self,'performance',None)
        music=getattr(self,'music',None)
        track_playing=music and music.playing
        self.motion.transport_beat=(music.beat_position if track_playing else
                                    performance.position/4. if performance and performance.playing else None)
        self.motion.update(model,dt)
        score_playing=bool(performance and performance.playing)
        selected=bool(performance.auto if score_playing else music and music.auto and (music.path or model.playing))
        self.evolution.update(model,self.motion,dt,selected=selected,
                              running=bool(track_playing or score_playing or model.playing))
        self.climax.score_target=(music.expansion if track_playing else
                                  performance.expansion if performance and performance.playing else None)
        self.climax.update(model,dt)
        if self.evolution.strength>.00001:
            pose=self.evolution.vj.build(self.evolution,self.motion,self.climax.amount)
            self.pose_texture.write(pose.tobytes())
        self.pose_texture.use(5)
        self.zoom=ease(self.zoom,self.zoom_target,6.,dt)
        for i in (0,1):self.orbit[i]=ease(self.orbit[i],self.orbit_target[i],6.,dt)
        # The stage itself opens continuously to the display edges during a climax.
        opening=smoothstep(self.climax.amount)
        stage_h=round(h-245*(1-opening)) if self.instrument_visible else h
        stage_y=round(185*(1-opening)) if self.instrument_visible else 0
        f=1/math.tan(math.radians(39)/2)
        near,far=.1,100.
        proj=np.array([[f/(w/stage_h),0,0,0],[0,f,0,0],[0,0,(far+near)/(near-far),2*far*near/(near-far)],[0,0,-1,0]],dtype='f4')
        view=np.eye(4,dtype='f4');view[2,3]=-self.zoom*(1-opening*.08)
        self.program['projection'].write(proj.T.tobytes());self.program['view'].write(view.T.tobytes())
        self._visual_phase=getattr(self,'_visual_phase',0.)+dt*(model.deck_speeds[0]*(1-model.crossfade)+model.deck_speeds[1]*model.crossfade)
        phase=self._visual_phase
        for name,value in [('phase',phase),('energy',model.energy),('charge',model.charge),('twist',model.twist),('orbit',tuple(self.orbit)),('palette',self.palette),('fx',tuple(model.fx))]:
            if name in self.program:self.program[name].value=value
        self.program['weights'].write(np.array(model.weights,dtype='f4').tobytes())
        self.program['expansion']=self.climax.amount
        self.program['bands']=tuple(model.bands)
        self.program['motion']=self.motion.values
        self.program['motion_phase']=self.motion.phases
        self.program['evolution_strength']=self.evolution.strength
        for name,value in (('evolution_shape',tuple(self.evolution.shape)),
                           ('evolution_detail',tuple(self.evolution.detail)),
                           ('evolution_phase',tuple(self.evolution.phases)),('organism_pose',5)):
            if name in self.program:self.program[name].value=value
        self.program['camera_position']=(0.,0.,float(-view[2,3]))
        self.program['resolution']=(float(w),float(h));self.program['opaque_scene']=3
        self.opaque_color.use(3)
        self.msaa_fbo.use();self.ctx.viewport=(0,0,w,h)
        self.msaa_fbo.clear(0,0,0,1,depth=1)
        self.ctx.viewport=(0,stage_y,w,stage_h)
        self.ctx.enable(moderngl.DEPTH_TEST)
        for surface_pass in (0,1):
            self.program['surface_pass']=surface_pass
            (self.panel_vao if self.evolution.strength>.9999 else self.vao).render(instances=648)
            self.climax_renderer.draw(self.climax,proj,view,self.orbit,self.palette,model.energy,w/stage_h,surface_pass,(float(w),float(h)),model.weights,model.bands,phase,self.motion.values,self.motion.phases,self.evolution)
            if surface_pass==0:
                self.ctx.copy_framebuffer(self.opaque_fbo,self.msaa_fbo)
                self.msaa_fbo.use();self.ctx.viewport=(0,stage_y,w,stage_h)
        self.ctx.disable(moderngl.DEPTH_TEST)
        self.ctx.copy_framebuffer(self.fbo,self.msaa_fbo)
        self.bloom_fbo_a.use();self.ctx.viewport=(0,0,w//2,h//2)
        self.color.use(0);self.blur['source']=0;self.blur['extract']=True;self.blur['direction']=(2./w,0.)
        self.blur_vao.render(moderngl.TRIANGLE_STRIP)
        self.bloom_fbo_b.use();self.bloom_a.use(0);self.blur['extract']=False;self.blur['direction']=(0.,3./h)
        self.blur_vao.render(moderngl.TRIANGLE_STRIP)
        self.halo_fbo_a.use();self.ctx.viewport=(0,0,max(1,w//4),max(1,h//4))
        self.bloom_b.use(0);self.blur['direction']=(12./w,0.)
        self.blur_vao.render(moderngl.TRIANGLE_STRIP)
        self.halo_fbo_b.use();self.halo_a.use(0);self.blur['direction']=(0.,12./h)
        self.blur_vao.render(moderngl.TRIANGLE_STRIP)
        self.ctx.screen.use();self.ctx.viewport=(0,0,w,h)
        self.overlay.write(ui_bytes)
        self.color.use(0);self.bloom_b.use(1);self.overlay.use(2)
        self.halo_b.use(4);self.final['halo']=4
        self.final['scene']=0;self.final['bloom']=1;self.final['overlay']=2
        self.final['accents'].value=tuple(model.accents)
        self.final['light_background']=self.light_background;self.final['safe_mode']=self.safe_mode
        self.final_vao.render(moderngl.TRIANGLE_STRIP)

    def capture(self):
        import pygame
        data=self.ctx.screen.read(components=3,alignment=1)
        return pygame.image.frombytes(data,self.size,'RGB',True)

