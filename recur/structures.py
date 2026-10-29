# The original six silhouettes, plus four optional radial constructions.
import math

GLSL = r'''
void legacyFrame(float theta,float band,float phase,int shape,out vec3 p,out mat3 frame,out float size){
 float j=floor(theta/(PI*2.)*216.+.0001),u=j/215.,base=u*PI*2.;
 float sector=floor(j/72.),v=mod(j,72.)/71.,t=phase*.22;
 float angle=0.,roll=0.;
 if(shape==0){
   float q=base+t*.18;
   p=vec3(1.62*cos(q),.67*sin(q)+.15*sin(q*2.),.18*sin(q*2.));
   vec2 tangent=vec2(-1.62*sin(q),.67*cos(q)+.3*cos(q*2.));
   angle=atan(tangent.y,tangent.x)-PI*.5;
   p.xy+=vec2(cos(angle),sin(angle))*(band-1.)*.085;
   roll=.15*sin(q);size=.52+.12*sin(u*PI);
 }else if(shape==1){
   float wave=u*PI*2.+t*.35;
   p=vec3((u-.5)*3.85,.38*sin(wave)+(band-1.)*.12,.22*cos(wave));
   angle=atan(.38*PI*2.*cos(wave),3.85)-PI*.5;
   roll=.7*sin(wave*.5);size=.5;
 }else if(shape==2){
   angle=sector*PI*2./3.+v*2.55+band*.17+t*.10;
   float r=.35+v*1.35+band*.09;
   p=vec3(cos(angle)*r,sin(angle)*r,.23*sin(v*PI*1.5+band*.3));
   roll=v*2.1;size=.34+.48*sin(v*PI);
 }else if(shape==3){
   float col=mod(j,18.),row=floor(j/18.);
   p=vec3((col-8.5)*.20,(row-5.5)*.15,(band-1.)*.13+.16*sin(col*.35+row*.3+t*.3));
   angle=.1*sin(t*.2);roll=0.;size=.17;
 }else if(shape==4){
   angle=base+t*.12*(band==1.?-1.:1.);
   float r=1.02+band*.21;
   p=rx((band-1.)*.9)*ry(band*.27)*vec3(cos(angle)*r,sin(angle)*r,0.);
   roll=base*.45+band*.6;size=.40;
 }else{
   p=vec3((u-.5)*3.8,(band-1.)*.42+.20*sin(u*PI*3.+t*.4),.42*sin(u*PI*2.+t*.35+band*.6));
   angle=-PI*.5;roll=.5*cos(u*PI*2.+t*.35);size=.55;
 }
 frame=rz(angle)*ry(roll);
}
void radialFrame(float theta,float band,float t,vec3 music,int shape,out vec3 p,out mat3 frame,out float size){
 float direction=mod(band,2.)<.5?1.:-1.;
 float a=theta+t*.105*direction+band*.085;
 float opening=.5+.5*sin(t*.43+band*.34),base=.51+band*.265;
 float harmonic=shape==6?6.:(shape==8?8.:4.);
 float strength=shape==6?.20*(.25+.75*opening):(shape==8?.19*(.4+.6*opening):.07+.08*opening);
 if(shape==9){base*=.86;strength=(.51+band*.265)*.16;}
 float radius=base+strength*cos(harmonic*a),dr=-strength*harmonic*sin(harmonic*a);
 p=vec3(cos(a)*radius,sin(a)*radius,(band-1.5)*.10+.065*cos(harmonic*a)*(.4+music.y));
 vec2 tangent=vec2(cos(a)*dr-sin(a)*radius,sin(a)*dr+cos(a)*radius);
 float angle=atan(tangent.y,tangent.x)-PI*.5;
 float hinge=(.18+.38*music.y)*sin(a*harmonic+band*.3);
 if(shape==6)hinge=.4+.45*sin(t*.43+band*.34);
 float gate=shape==6?smoothstep(.035,.22,abs(sin(a*3.))):1.;
 if(shape==8)gate=smoothstep(.025,.19,abs(sin(a*2.)));
 size=(.43+band*.012)*(.08+.92*gate);
 frame=rz(angle)*ry(hinge);
 // Facets stay discrete instead of 216 wide boxes overlapping into a gold blob.
 if(shape==9)frame=frame*mat3(1.,0.,0.,0.,.075,0.,0.,0.,.85);
}
void articulate(float theta,float band,float weights[10],inout vec3 p,inout mat3 frame){
 float kick=motion.x,body=motion.y,detail=motion.z,activity=motion.w;
 float beat=motion_phase.x,travel=motion_phase.y;
 float openForm=weights[1]+weights[5],crystal=weights[3];
 float wave=sin(theta*2.-beat*2.+band*.85);
 vec2 outward=p.xy/max(length(p.xy),.001);
 // Recoil on the attack; a travelling fold continues between the notes.
 p*=1.+kick*.20+body*.07*wave;
 p.xy+=outward*(body*.17*wave*(1.-openForm));
 p.y+=openForm*body*.32*sin(theta*2.-beat+band*.65);
 p.z+=body*(.25*sin(theta*2.-beat+band*.9)+(band-1.)*.08*sin(beat));
 p.z+=crystal*detail*.20*cos(theta*6.-beat*3.);
 float direction=mod(band,2.)<.5?1.:-1.;
 float turn=activity*.16*sin(beat*.5+band*.65)+direction*kick*.13;
 p=rz(turn)*rx(body*.16*sin(travel+band*.6))*p;
 // Hinged fins articulate as a connected mechanism rather than scattering.
 frame=rz(detail*.22*sin(theta*6.-beat*4.+band))
       *ry(body*.65*sin(theta*2.-beat+band*.9)+kick*.42)*frame;
}
void structure(float theta,float band,float t,vec3 music,float weights[10],float expansion,
               out vec3 center,out mat3 local,out float size){
 center=vec3(0.);local=mat3(0.);size=1.;
 for(int k=0;k<10;k++){
   if(weights[k]<.00001)continue;
   vec3 p;mat3 frame;float moduleSize;
   if(k<6)legacyFrame(theta,band,t,k,p,frame,moduleSize);
   else radialFrame(theta,band,t,music,k,p,frame,moduleSize);
   center+=p*weights[k];local+=frame*ry(music.y*.20)*moduleSize*weights[k];
 }
 center*=1.+music.x*.035+expansion*(.40+band*.14);
 local*=1.+music.z*.08;
 articulate(theta,band,weights,center,local);
}
'''


def _rotate(p,x=0.,y=0.):
    px,py,pz=p
    px,pz=math.cos(y)*px+math.sin(y)*pz,-math.sin(y)*px+math.cos(y)*pz
    return (px,math.cos(x)*py-math.sin(x)*pz,math.sin(x)*py+math.cos(x)*pz)


def form_center(theta,band,phase,music,shape):
    # CPU construction positions used to verify silhouette preservation.
    j=math.floor(theta/math.tau*216+.0001);u=j/215;base=u*math.tau;t=phase*.22
    if shape==0:
        q=base+t*.18
        angle=math.atan2(.67*math.cos(q)+.3*math.cos(q*2),-1.62*math.sin(q))-math.pi*.5
        return (1.62*math.cos(q)+math.cos(angle)*(band-1)*.085,
                .67*math.sin(q)+.15*math.sin(q*2)+math.sin(angle)*(band-1)*.085,.18*math.sin(q*2))
    if shape==1:
        wave=u*math.tau+t*.35
        return ((u-.5)*3.85,.38*math.sin(wave)+(band-1)*.12,.22*math.cos(wave))
    if shape==2:
        sector=j//72;v=(j%72)/71
        a=sector*math.tau/3+v*2.55+band*.17+t*.1;r=.35+v*1.35+band*.09
        return (math.cos(a)*r,math.sin(a)*r,.23*math.sin(v*math.pi*1.5+band*.3))
    if shape==3:
        col=j%18;row=j//18
        return ((col-8.5)*.2,(row-5.5)*.15,(band-1)*.13+.16*math.sin(col*.35+row*.3+t*.3))
    if shape==4:
        a=base+t*.12*(-1 if band==1 else 1);r=1.02+band*.21
        return _rotate((math.cos(a)*r,math.sin(a)*r,0.),(band-1)*.9,band*.27)
    if shape==5:
        return ((u-.5)*3.8,(band-1)*.42+.2*math.sin(u*math.pi*3+t*.4),.42*math.sin(u*math.tau+t*.35+band*.6))
    a=theta+phase*.105*(1 if band%2==0 else -1)+band*.085
    opening=.5+.5*math.sin(phase*.43+band*.34);base=.51+band*.265
    harmonic=6 if shape==6 else 8 if shape==8 else 4
    strength=.20*(.25+.75*opening) if shape==6 else .19*(.4+.6*opening) if shape==8 else .07+.08*opening
    if shape==9:strength=base*.16;base*=.86
    radius=base+strength*math.cos(harmonic*a)
    return (math.cos(a)*radius,math.sin(a)*radius,(band-1.5)*.1+.065*math.cos(harmonic*a)*(.4+music[1]))


def articulate_center(p,theta,band,weights,motion,motion_phase):
    """CPU equivalent of the shared articulation for bounded-motion checks."""
    kick,body,detail,active=motion;beat,travel=motion_phase
    open_form=weights[1]+weights[5];crystal=weights[3]
    wave=math.sin(theta*2-beat*2+band*.85)
    radius=max(math.hypot(p[0],p[1]),.001);outward=(p[0]/radius,p[1]/radius)
    x,y,z=(v*(1+kick*.20+body*.07*wave) for v in p)
    offset=body*.17*wave*(1-open_form)
    x+=outward[0]*offset;y+=outward[1]*offset
    y+=open_form*body*.32*math.sin(theta*2-beat+band*.65)
    z+=body*(.25*math.sin(theta*2-beat+band*.9)+(band-1)*.08*math.sin(beat))
    z+=crystal*detail*.20*math.cos(theta*6-beat*3)
    x,y,z=_rotate((x,y,z),x=body*.16*math.sin(travel+band*.6))
    turn=active*.16*math.sin(beat*.5+band*.65)+(1 if band%2<.5 else -1)*kick*.13
    return (x*math.cos(turn)-y*math.sin(turn),x*math.sin(turn)+y*math.cos(turn),z)


def center(theta,band,phase,music,weights,expansion=0.,motion=(0.,0.,0.,0.),motion_phase=(0.,0.)):
    result=[0.,0.,0.]
    for shape,weight in enumerate(weights):
        if weight:
            p=form_center(theta,band,phase,music,shape)
            for i in range(3):result[i]+=p[i]*weight
    scale=1+music[0]*.035+expansion*(.4+band*.14)
    return articulate_center(tuple(x*scale for x in result),theta,band,weights,motion,motion_phase)
