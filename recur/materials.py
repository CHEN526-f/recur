"""Studio-lit conductors and sparse, refractive dielectric fins in linear HDR."""
import math
import numpy as np


SURFACE_FRAGMENT = r'''
#version 330
in vec3 world; in vec3 normal; in float material; in float instance;
uniform float energy; uniform int palette;
uniform vec3 camera_position;
uniform int surface_pass;
uniform sampler2D opaque_scene;
uniform vec2 resolution;
out vec4 frag;
const float PI=3.14159265359;
vec3 fresnel(vec3 f0,float c){return f0+(1.-f0)*pow(1.-clamp(c,0.,1.),5.);}
vec3 studio(vec3 r,float rough){
 float spread=rough*.35;
 // Broad studio cards with dark gaps, reflected by the actual curved normals.
 float key=exp(-pow((r.x+.36)/(.12+spread),2.)-pow((r.y-.34)/(.54+spread),4.));
 float strip=exp(-pow((r.x-.58)/(.065+spread),2.)-pow((r.y+.15)/(.72+spread),4.));
 float ceiling=pow(max(0.,r.y),12.);
 float rim=pow(max(dot(r,normalize(vec3(-.6,-.4,-.7))),0.),20.);
 return vec3(.012,.016,.024)+vec3(1.,.91,.73)*key*1.9
       +vec3(.72,.86,1.)*strip*1.4+vec3(1.,.96,.86)*ceiling*.9
       +vec3(.95,.61,.25)*rim*.7;
}
vec3 light(vec3 n,vec3 v,vec3 l,vec3 radiance,vec3 f0,float rough){
 vec3 h=normalize(v+l);
 float nl=max(dot(n,l),0.),nv=max(dot(n,v),.002),nh=max(dot(n,h),0.);
 float a=rough*rough,a2=a*a;
 float d=a2/(PI*pow(nh*nh*(a2-1.)+1.,2.)+.00001);
 float k=pow(rough+1.,2.)/8.;
 float g=nv/(nv*(1.-k)+k)*nl/(nl*(1.-k)+k);
 return fresnel(f0,max(dot(v,h),0.))*d*g/(4.*nv*max(nl,.002))*radiance*nl;
}
void main(){
 // About eight percent of whole fins are glass; the metal remains dominant.
 bool glass=mod(floor(instance)+4.,13.)<1.;
 if((surface_pass==0 && glass)||(surface_pass==1 && !glass))discard;
 vec3 n=normalize(normal);if(!gl_FrontFacing)n=-n;
 vec3 v=normalize(camera_position-world),r=reflect(-v,n);
 float nv=clamp(dot(n,v),0.,1.);
 vec3 gold=vec3(1.,.72,.30);
 if(palette==1)gold=vec3(.83,.91,.97);
 if(palette==2)gold=vec3(.96,.47,.26);
 float silver=smoothstep(.45,.65,material)*.74;
 vec3 f0=mix(gold,vec3(.91,.94,.98),silver);
 float rough=mix(.23,.16,silver);
 vec3 color=studio(r,rough)*fresnel(f0,nv);
 color+=light(n,v,normalize(vec3(-2.,3.,4.)),vec3(2.2,1.9,1.5),f0,rough);
 color+=light(n,v,normalize(vec3(3.,.7,2.)),vec3(1.,1.3,1.6),f0,rough+.07);
 color+=f0*.028*(.6+.4*max(n.y,0.));
 color*=.78+.22*abs(n.z);
 if(glass){
   vec2 uv=gl_FragCoord.xy/resolution;
   vec2 bend=n.xy*(.009+.012*(1.-nv));
   vec3 behind=vec3(texture(opaque_scene,clamp(uv+bend*1.03,.001,.999)).r,
                    texture(opaque_scene,clamp(uv+bend,.001,.999)).g,
                    texture(opaque_scene,clamp(uv+bend*.97,.001,.999)).b);
   float f=.045+.955*pow(1.-nv,5.);
   vec3 tint=vec3(.87,.96,.98);
   // Composite transmission against the resolved opaque scene, then add Fresnel.
   color=behind*tint*(1.-f)*.96+studio(r,.07)*f;
   color+=vec3(.15,.28,.31)*pow(1.-nv,3.)*.32;
 }
 color+=f0*energy*.025;
 frag=vec4(color,1.);
}
'''


def beveled_box(size=(.88, .7, .50), bevel=.055):
    """Rounded edges have real geometry and smooth normals, not painted outlines."""
    half=np.asarray(size,dtype=float)*.5
    bevel=min(bevel,float(half.min())*.6)
    core=half-bevel
    vertices=[]
    for axis in range(3):
        other=[i for i in range(3) if i!=axis]
        for sign in (-1.,1.):
            grid=[]
            for u in (-1.,-.76,.76,1.):
                row=[]
                for v in (-1.,-.76,.76,1.):
                    p=np.zeros(3);p[axis]=sign*half[axis]
                    p[other[0]]=u*half[other[0]];p[other[1]]=v*half[other[1]]
                    nearest=np.clip(p,-core,core)
                    n=p-nearest;n/=np.linalg.norm(n)
                    row.append([*(nearest+n*bevel),*n])
                grid.append(row)
            for i in range(3):
                for j in range(3):
                    for a,b in ((i,j),(i+1,j),(i+1,j+1),(i,j),(i+1,j+1),(i,j+1)):
                        vertices.append(grid[a][b])
    triangles=np.asarray(vertices,dtype='f4').reshape(-1,3,6)
    face=np.cross(triangles[:,1,:3]-triangles[:,0,:3],triangles[:,2,:3]-triangles[:,0,:3])
    inverted=np.sum(face*triangles[:,:,3:6].mean(axis=1),axis=1)<0
    triangles[inverted]=triangles[inverted][:,[0,2,1],:]
    return triangles.reshape(-1,6)


def polished_rib():
    # A continuously swept curved fin replaces the old stack of flat cuboids.
    from .crescendo import blade_mesh
    fin=blade_mesh().copy()
    fin[:,:3]*=np.array([.90,1.05,.84],dtype='f4')
    rows=fin.tolist()
    for i in range(12):
        a=i/12*math.tau;b=(i+1)/12*math.tau
        for angle,z in ((a,-.41),(b,-.41),(b,.41),(a,-.41),(b,.41),(a,.41)):
            n=np.array([math.cos(angle)/.028,math.sin(angle)/.023,0.])
            n/=np.linalg.norm(n)
            rows.append([.015+.028*math.cos(angle),.023*math.sin(angle),z,*n,1.])
    return np.asarray(rows,dtype='f4')
