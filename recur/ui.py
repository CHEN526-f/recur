"""Minimal performance surface. Detailed instructions appear only in the guide."""
import math
import os
from pathlib import Path
import pygame
from .model import NAMES, KEYS
from .music import DEMO_PATH

INK=(230,227,215)
MUTED=(111,116,117)
GOLD=(210,173,104)
PANEL=(17,19,21,246)


class Interface:
    def __init__(self):
        self.fonts={};self.buttons={};self.cells=[];self.pad_rects=[]
        self.show_help=False;self.show_camera=False;self.show_grid=False;self.hide=False
        self.jogs=[];self.fader=None;self.fx_rect=None

    def font(self,size,serif=False,cjk=False):
        key=(size,serif,cjk)
        if key not in self.fonts:
            root=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'
            p=root/('msyh.ttc' if cjk else 'georgia.ttf' if serif else 'consola.ttf')
            self.fonts[key]=pygame.font.Font(str(p) if p.is_file() else None,size)
        return self.fonts[key]

    def text(self,surf,string,x,y,size=12,color=INK,serif=False):
        surf.blit(self.font(size,serif,any(ord(c)>127 for c in string)).render(string,True,color),(x,y))

    def button(self,surf,key,label,rect,active=False):
        rect=pygame.Rect(rect);self.buttons[key]=rect
        pygame.draw.rect(surf,(36,32,25,245) if active else PANEL,rect,border_radius=5)
        pygame.draw.rect(surf,GOLD if active else (49,51,51),rect,1,border_radius=5)
        img=self.font(12,cjk=any(ord(c)>127 for c in label)).render(label,True,GOLD if active else INK)
        surf.blit(img,img.get_rect(center=rect.center))

    def render(self,size,model,synth,renderer,camera,fps,toast,demo):
        w,h=size;surf=pygame.Surface(size,pygame.SRCALPHA)
        self.buttons={};self.cells=[];self.pad_rects=[];self.jogs=[]
        self.fader=None;self.fx_rect=None
        if self.hide:return pygame.image.tobytes(surf,'RGBA')
        self.text(surf,'RECUR',28,20,22,INK,True)
        self.button(surf,'import_music','IMPORT',(143,20,94,28))
        music=getattr(renderer,'music',None)
        performance=getattr(renderer,'performance',None)
        self.button(surf,'visual_mode','PLAY / F2' if renderer.play_mode else 'SCULPT / F2',(247,20,100,28),renderer.play_mode)
        if music:
            auto=performance.auto if demo and performance else music.auto
            self.button(surf,'auto_music','FOLLOW' if auto else 'LIVE ONLY',(357,20,82,28),auto)
        if music and music.path:
            stem=music.path.stem
            name=stem[:21] if stem.isascii() else 'Imported track'
            if not demo:self.text(surf,name,450,27,11,MUTED)
            if not demo and music.analysis:
                self.text(surf,f'{music.bpm:.0f} BPM',600,27,11,GOLD)
            self.button(surf,'music','|| MUSIC' if music.playing else '> MUSIC',(w-248,20,92,28),music.playing)
        self.button(surf,'help','?',(w-146,20,32,28),self.show_help)
        self.button(surf,'camera','C',(w-106,20,32,28),self.show_camera)
        self.button(surf,'mute','M',(w-66,20,38,28),synth.muted)
        if demo and performance:
            self.text(surf,f'{performance.label} / {performance.chord_name} / {performance.bar+1:02}/32',450,27,12,GOLD)
        base=h-205
        # The stage stays almost text-free; the controls resemble an instrument.
        pygame.draw.line(surf,(42,43,40),(28,base),(w-28,base))
        for deck,cx in [(0,120),(1,w-120)]:
            cy=h-108;radius=65;active=model.selected_deck==deck
            self.jogs.append(((cx,cy),radius))
            self.text(surf,'A' if deck==0 else 'B',cx-5,base+13,13,GOLD if active else MUTED)
            pygame.draw.circle(surf,(21,23,24,248),(cx,cy),radius)
            pygame.draw.circle(surf,GOLD if active else (75,77,72),(cx,cy),radius,1)
            for r in (26,33,40,47,54):pygame.draw.circle(surf,(43,45,44),(cx,cy),r,1)
            angle=model.deck_phases[deck]*5
            p=(cx+math.cos(angle)*50,cy+math.sin(angle)*50)
            pygame.draw.line(surf,GOLD,(cx,cy),p,2)
            pygame.draw.circle(surf,(51,44,31),(cx,cy),17)
            pygame.draw.circle(surf,GOLD,(cx,cy),3)
        available=w-560;pad_w=(available-5*8)//6;pad_x=(w-(pad_w*6+5*8))//2
        for i in range(6):
            r=pygame.Rect(pad_x+i*(pad_w+8),base+20,pad_w,34)
            self.pad_rects.append(r);on=(i in renderer.stage.contacts.voices or model.flashes[i]>.1) if renderer.play_mode else model.active_target==i
            pygame.draw.rect(surf,(30+int(model.flashes[i]*15),29,25,245),r,border_radius=4)
            pygame.draw.rect(surf,GOLD if on else (54,55,51),r,1,border_radius=4)
            label=self.font(11).render(KEYS[i]+' '+('PULSE','ARCS','FAN','RIBBON','PORTAL','SPARKS')[i] if renderer.play_mode else KEYS[i],True,GOLD if on else INK)
            surf.blit(label,label.get_rect(center=(r.centerx,r.y+10)))
            role=self.font(9).render(('KICK','MELODY','CHORD','PLUCK','BASS','PERC')[i],True,MUTED)
            surf.blit(role,role.get_rect(center=(r.centerx,r.y+25)))
        for i,name in enumerate(NAMES[6:] if not renderer.play_mode else ()):
            self.button(surf,f'form_{6+i}',f'{4+i} {name}',(w//2-174+i*88,base-32,82,23),model.active_target==6+i)
        if renderer.play_mode:
            self.text(surf,'INDEPENDENT VOICES / COMBINE KEYS OR TOUCHES',w//2-166,base-26,11,MUTED)
            if not renderer.stage.notes and not self.show_grid and not self.show_help:
                self.text(surf,'PLAY  A  S  D  J  K  L',w//2-167,int(h*.40),24,INK)
                self.text(surf,'Tap the canvas or pads. Each voice keeps its own tail.',w//2-201,int(h*.40)+38,12,MUTED)
        y=base+70;bx=w//2-177
        for i,(key,label,on) in enumerate([
            ('play','||' if model.playing else '>',model.playing),
            ('record','REC',model.recording),
            ('demo','DEMO',bool(music and music.playing and music.path==DEMO_PATH)),('score','LOCAL',demo),
            ('grid','LOOP',self.show_grid),('export','SAVE',False),('load','LOAD',False)]):
            self.button(surf,key,label,(bx+i*52,y,45,28),on)
        # A crossfader changes both audio gain and the sculpture mixture.
        self.fader=pygame.Rect(w//2-155,h-55,310,20)
        pygame.draw.line(surf,(61,62,56),(self.fader.left,self.fader.centery),(self.fader.right,self.fader.centery),2)
        for i in range(9):
            xx=self.fader.left+i*self.fader.w//8
            pygame.draw.line(surf,(55,56,52),(xx,self.fader.centery-4),(xx,self.fader.centery+4))
        xx=int(self.fader.left+self.fader.w*model.crossfade)
        pygame.draw.rect(surf,GOLD,(xx-6,self.fader.top-2,12,24),border_radius=2)
        self.text(surf,'A',self.fader.left-20,self.fader.top+3,10,MUTED)
        self.text(surf,'B',self.fader.right+13,self.fader.top+3,10,MUTED)
        self.fx_rect=pygame.Rect(w-300,h-128,88,84)
        pygame.draw.rect(surf,(20,23,24,230),self.fx_rect,border_radius=4)
        pygame.draw.rect(surf,(59,61,56),self.fx_rect,1,border_radius=4)
        pygame.draw.line(surf,(36,39,39),(self.fx_rect.centerx,self.fx_rect.top),(self.fx_rect.centerx,self.fx_rect.bottom))
        pygame.draw.line(surf,(36,39,39),(self.fx_rect.left,self.fx_rect.centery),(self.fx_rect.right,self.fx_rect.centery))
        fxp=(int(self.fx_rect.left+model.fx[0]*88),int(self.fx_rect.bottom-model.fx[1]*84))
        pygame.draw.circle(surf,GOLD,fxp,4)
        self.text(surf,'FX',self.fx_rect.x,self.fx_rect.y-19,10,MUTED)
        self.text(surf,str(model.bpm),232,h-123,22)
        self.button(surf,'bpm_down','-',(225,h-88,30,24))
        self.button(surf,'bpm_up','+',(263,h-88,30,24))
        self.text(surf,'BPM',234,h-52,9,MUTED)
        if self.show_grid:
            p=pygame.Rect(w//2-370,base-238,740,202)
            pygame.draw.rect(surf,PANEL,p,border_radius=6)
            self.button(surf,'deck_a','A',(p.x+12,p.y+8,34,22),model.selected_deck==0)
            self.button(surf,'deck_b','B',(p.x+52,p.y+8,34,22),model.selected_deck==1)
            self.button(surf,'grid_play','PAUSE' if model.playing else 'PLAY',(p.right-168,p.y+8,88,24),model.playing)
            self.button(surf,'clear','CLEAR',(p.right-72,p.y+8,60,24))
            self.text(surf,'16 STEPS / Click a cell to audition and start',p.x+104,p.y+12,12,INK)
            step=model.step if model.selected_deck==0 else model.step_b
            for col in range(16):
                self.text(surf,str(col+1),p.x+102+col*39,p.y+42,10,GOLD if col%4==0 else MUTED)
            for row in range(6):
                self.text(surf,KEYS[row]+' '+('KICK','MELODY','CHORD','PLUCK','BASS','PERC')[row],p.x+14,p.y+64+row*19,11,MUTED)
                for col in range(16):
                    r=pygame.Rect(p.x+98+col*39,p.y+63+row*19,34,14)
                    on=model.active_loop[row][col]
                    pygame.draw.rect(surf,GOLD if on else (37,40,39),r,border_radius=2)
                    if col==step:pygame.draw.rect(surf,INK,r,1,border_radius=2)
                    self.cells.append((r,row,col))
            gain=math.cos(model.crossfade*math.pi/2) if model.selected_deck==0 else math.sin(model.crossfade*math.pi/2)
            status='MUTED / Press M' if synth.muted else 'LOOP PLAYING' if model.playing else 'STOPPED'
            self.text(surf,f'{status}  /  DECK GAIN {gain*100:.0f}%',p.x+14,p.y+184,11,GOLD)
            if demo or (music and music.playing):
                self.text(surf,'Editing pauses the track and plays your loop',p.x+320,p.y+184,11,MUTED)
        if self.show_camera:
            p=pygame.Rect(w-288,65,260,186)
            pygame.draw.rect(surf,PANEL,p,border_radius=6)
            self.button(surf,'cam_start','STOP' if camera.active else 'CONNECT',(p.x+12,p.y+12,106,26),camera.active)
            self.button(surf,'cam_device',f'DEVICE {camera.index}',(p.x+128,p.y+12,120,26))
            for i,val in enumerate(camera.sample()):
                r=pygame.Rect(p.x+12+(i%2)*121,p.y+52+(i//2)*33,114,26)
                pygame.draw.rect(surf,(34,37,38),r)
                pygame.draw.rect(surf,GOLD,(r.x,r.y,int(r.w*min(1,val/.25)),r.h))
            self.button(surf,'sensitivity_down','-',(p.x+12,p.y+125,30,23))
            self.button(surf,'sensitivity_up','+',(p.x+50,p.y+125,30,23))
            for i in range(0,min(len(camera.status),74),37):
                self.text(surf,camera.status[i:i+37],p.x+12,p.y+155+i//37*12,9,MUTED)
        if toast:
            img=self.font(11,cjk=any(ord(c)>127 for c in toast)).render(toast[:115],True,INK)
            surf.blit(img,(w//2-img.get_width()//2,66))
        if self.show_help:
            shade=pygame.Surface(size,pygame.SRCALPHA);shade.fill((5,7,9,235));surf.blit(shade,(0,0))
            x=w//2-350;y=85
            pygame.draw.rect(surf,PANEL,(x,y,700,550),border_radius=9)
            self.text(surf,'RECUR / controls',x+28,y+26,24,INK,True)
            lines=[
                'A S D J K L   Independent visual voices + pitched/percussive sound.',
                'F2 / 4 5 6 7  Sculpture mode / original extra sculpture forms.',
                'TAB           Select deck A or B. Each keeps its own form/loop.',
                'TOUCH         Multiple fingers play independent voices together.',
                'TURNTABLES    Drag around either disc to scratch forward/back.',
                'FX PAD        X: tone + torsion. Y: echo + spatial spread.',
                'SPACE         Hold to brake both decks; release to recover.',
                'R / >         Overdub into selected loop / play or stop loops.',
                'LOOP / I      Click cells to audition and start your loop. A/B: deck.',
                'T / DEMO      Play the CC0 demo; measured drums drive the motion.',
                'G / LOCAL     32-bar score with continuous unfolding and reassembly.',
                'S / J / Z X   Melodic notes / warm plucks / shift melody octave.',
                'Q / W         Temporary ring / shutter visual accents.',
                'ARROWS/WHEEL  Orbit / zoom. 1,2,3 change metal. B: background.',
                'H / F         Artwork-only view / fullscreen.',
                'IMPORT / U    Choose music; drag-and-drop also works. Auto starts on.',
                'V / Y         Pause the track / toggle imported-music visuals.',
                'P / M         Pause / mute. E saves PNG + session; O restores.',
                'C             Optional local camera input. Device 0..3.',
                'BACKSPACE     Reset controls, preserving your loops.',
                'ESC           Close guide, or exit. Moderate your volume.',
            ]
            for i,line in enumerate(lines):self.text(surf,line,x+28,y+77+i*19,12,INK)
            self.button(surf,'close_help','CLOSE',(x+28,y+496,644,28),True)
        return pygame.image.tobytes(surf,'RGBA')
