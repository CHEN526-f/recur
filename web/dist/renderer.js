import {VERTEX,FRAGMENT,MESH} from './geometry.js';
const POST=`#version 300 es
precision highp float;uniform sampler2D scene;uniform vec2 resolution;in vec2 uv;out vec4 frag;
void main(){vec3 c=texture(scene,uv).rgb;vec3 glow=vec3(0.);
 for(int x=-2;x<=2;x++)for(int y=-2;y<=2;y++){vec3 s=texture(scene,uv+vec2(float(x),float(y))*3./resolution).rgb;float k=smoothstep(.65,1.9,max(s.r,max(s.g,s.b)));glow+=s*k/25.;}
 c+=glow*.22+vec3(.002,.0025,.003);
 c=clamp((c*(2.51*c+.03))/(c*(2.43*c+.59)+.14),0.,1.);c=pow(c,vec3(1./2.2));frag=vec4(c,1.);}`;
const QUAD=`#version 300 es
precision highp float;out vec2 uv;void main(){vec2 p=vec2(float((gl_VertexID<<1)&2),float(gl_VertexID&2));uv=p;gl_Position=vec4(p*2.-1.,0,1);}`;
export class Renderer{
 constructor(canvas){
  this.canvas=canvas;this.gl=canvas.getContext('webgl2',{alpha:false,antialias:true,preserveDrawingBuffer:true});
  if(!this.gl)throw Error('Could not start WebGL2. Use a browser that supports WebGL2.');
  const g=this.gl;this.hdr=!!g.getExtension('EXT_color_buffer_float');g.getExtension('OES_texture_float_linear');
  this.program=this.compile(VERTEX,FRAGMENT);this.post=this.compile(QUAD,POST);this.uniforms=new Map();
  this.vao=g.createVertexArray();g.bindVertexArray(this.vao);this.vbo=g.createBuffer();g.bindBuffer(g.ARRAY_BUFFER,this.vbo);g.bufferData(g.ARRAY_BUFFER,new Float32Array(MESH),g.STATIC_DRAW);
  for(const [name,size,offset] of [['in_pos',3,0],['in_normal',3,3],['in_material',1,6],['in_block',3,7],['in_block_normal',3,10]]){const loc=g.getAttribLocation(this.program,name);if(loc>=0){g.enableVertexAttribArray(loc);g.vertexAttribPointer(loc,size,g.FLOAT,false,52,offset*4);}}
  this.count=MESH.length/13;this.quad=g.createVertexArray();this.palette=0;this.orbit=[0,.23];this.zoom=7.3;this.resize();
 }
 compile(v,f){const g=this.gl,p=g.createProgram();for(const [type,src] of [[g.VERTEX_SHADER,v],[g.FRAGMENT_SHADER,f]]){const s=g.createShader(type);g.shaderSource(s,src);g.compileShader(s);if(!g.getShaderParameter(s,g.COMPILE_STATUS))throw Error(g.getShaderInfoLog(s));g.attachShader(p,s);g.deleteShader(s);}g.linkProgram(p);if(!g.getProgramParameter(p,g.LINK_STATUS))throw Error(g.getProgramInfoLog(p));return p;}
 texture(w,h,hdr=false){const g=this.gl,t=g.createTexture();g.bindTexture(g.TEXTURE_2D,t);g.texImage2D(g.TEXTURE_2D,0,hdr?g.RGBA16F:g.RGBA,w,h,0,g.RGBA,hdr?g.HALF_FLOAT:g.UNSIGNED_BYTE,null);g.texParameteri(g.TEXTURE_2D,g.TEXTURE_MIN_FILTER,g.LINEAR);g.texParameteri(g.TEXTURE_2D,g.TEXTURE_MAG_FILTER,g.LINEAR);g.texParameteri(g.TEXTURE_2D,g.TEXTURE_WRAP_S,g.CLAMP_TO_EDGE);g.texParameteri(g.TEXTURE_2D,g.TEXTURE_WRAP_T,g.CLAMP_TO_EDGE);return t;}
 resize(){const g=this.gl,dpr=Math.min(devicePixelRatio||1,1.4),w=Math.max(1,Math.round(innerWidth*dpr)),h=Math.max(1,Math.round(innerHeight*dpr));if(this.width===w&&this.height===h)return;this.width=w;this.height=h;this.canvas.width=w;this.canvas.height=h;if(this.fbo){g.deleteFramebuffer(this.fbo);g.deleteTexture(this.color);g.deleteTexture(this.opaque);g.deleteRenderbuffer(this.depth);}this.color=this.texture(w,h,this.hdr);this.opaque=this.texture(w,h,this.hdr);this.fbo=g.createFramebuffer();g.bindFramebuffer(g.FRAMEBUFFER,this.fbo);g.framebufferTexture2D(g.FRAMEBUFFER,g.COLOR_ATTACHMENT0,g.TEXTURE_2D,this.color,0);this.depth=g.createRenderbuffer();g.bindRenderbuffer(g.RENDERBUFFER,this.depth);g.renderbufferStorage(g.RENDERBUFFER,g.DEPTH_COMPONENT24,w,h);g.framebufferRenderbuffer(g.FRAMEBUFFER,g.DEPTH_ATTACHMENT,g.RENDERBUFFER,this.depth);if(g.checkFramebufferStatus(g.FRAMEBUFFER)!==g.FRAMEBUFFER_COMPLETE)throw Error('Could not create the framebuffer');g.bindFramebuffer(g.FRAMEBUFFER,null);}
 loc(p,name){const key=(p===this.program?'s:':'p:')+name;if(!this.uniforms.has(key))this.uniforms.set(key,this.gl.getUniformLocation(p,name));return this.uniforms.get(key);}
 set(name,v){const g=this.gl,l=this.loc(this.program,name);if(l===null)return;if(typeof v==='number'){if(['palette','surface_pass','opaque_scene'].includes(name))g.uniform1i(l,v);else g.uniform1f(l,v);}else if(v.length===16)g.uniformMatrix4fv(l,false,v);else if(v.length===10)g.uniform1fv(l,v);else g['uniform'+v.length+'fv'](l,v);}
 draw(s){this.resize();const g=this.gl,w=this.width,h=this.height;const f=1/Math.tan(39*Math.PI/360),near=.1,far=100;const projection=new Float32Array([f/(w/h),0,0,0,0,f,0,0,0,0,(far+near)/(near-far),-1,0,0,2*far*near/(near-far),0]);const z=this.zoom*Math.max(1,.95/(w/h))*(1-s.expansion*.045),view=new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,0,0,-z,1]);
  g.bindFramebuffer(g.FRAMEBUFFER,this.fbo);g.viewport(0,0,w,h);g.enable(g.DEPTH_TEST);g.clearColor(0,0,0,1);g.clear(g.COLOR_BUFFER_BIT|g.DEPTH_BUFFER_BIT);g.useProgram(this.program);g.bindVertexArray(this.vao);
  for(const [name,value] of Object.entries({projection,view,phase:s.phase,weights:s.weights,bands:s.bands,energy:s.energy,charge:s.charge,twist:(s.fx[0]-.5)*1.3,orbit:this.orbit,fx:s.fx,expansion:s.expansion,motion:s.motion,motion_phase:s.motionPhase,growth:s.growth,architecture:s.architecture,evolution:s.evolution,palette:this.palette,camera_position:[0,0,z],resolution:[w,h],opaque_scene:3}))this.set(name,value);
  g.activeTexture(g.TEXTURE3);g.bindTexture(g.TEXTURE_2D,this.opaque);this.set('surface_pass',0);g.drawArraysInstanced(g.TRIANGLES,0,this.count,1944);
  g.bindTexture(g.TEXTURE_2D,this.opaque);g.copyTexSubImage2D(g.TEXTURE_2D,0,0,0,0,0,w,h);this.set('surface_pass',1);g.drawArraysInstanced(g.TRIANGLES,0,this.count,1944);
  g.bindFramebuffer(g.FRAMEBUFFER,null);g.disable(g.DEPTH_TEST);g.useProgram(this.post);g.bindVertexArray(this.quad);g.activeTexture(g.TEXTURE0);g.bindTexture(g.TEXTURE_2D,this.color);g.uniform1i(this.loc(this.post,'scene'),0);g.uniform2f(this.loc(this.post,'resolution'),w,h);g.drawArrays(g.TRIANGLES,0,3);
 }
}
