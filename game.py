import pygame as pg
import os
from pygame.math import Vector2 as Vec2
from math import atan2, degrees, pi, sin, cos, floor
from enum import Enum

WIDTH=800
HEIGHT=600
TAU = 1/60

data_path = os.path.join(os.path.dirname(__file__), "data")
def load_image(name, ext='png'):
    file = os.path.join(data_path, name+'.'+ext)
    try:
        image = pg.image.load(file).convert_alpha()
    except FileNotFoundError:
        print(f"Could not load resource from file {file}")
        errsurf = pg.Surface((20,20))
        errsurf.fill("purple")
        image = errsurf
    return image

def scale_uniform(img, factor=1.0):
    width, height = img.get_width(), img.get_height()
    simg = pg.transform.scale(img, (width*factor, height*factor))
    return simg

class TileAnimation(pg.sprite.Sprite):
    def __init__(self):
        super().__init__()
    def update(self):
        self.kill()
    def get_offset(self, tile) -> float:
        return 0

def sym_smoothstep(le,re,x):
    clamp = lambda x: max(le, min(re,x))
    # Map (le,re) -> (-1,1)
    x = 2*(clamp(x)-le) / (re-le) - 1.0
    return x**4-2*x**2+1

def smoothstep(le,re,x):
    clamp = lambda x: max(0, min(1,x))
    x = clamp((x-le)/(re-le))
    return x**2*(3-2*x)


def two_smoothstep(le,re,x):
    if x < 0:
        return smoothstep(le,0,x)
    else:
        return 1-smoothstep(0,re,x)

    

class CircularWaveAnimation(TileAnimation):
    def __init__(self, epicenter=(0,0), speed=3, max_duration=4, trail=2, ahead=1, dampening=0.3, amplitude = 1):
        super().__init__()
        self.speed = speed
        self.center = Vec2(epicenter)
        self.time = 0
        self.max_duration = max_duration
        self.trail = trail
        self.ahead = ahead
        self.dampening = dampening
        self.amplitude = amplitude
    def update(self):
        self.time += TAU*self.speed
        self.amplitude = max(0, self.amplitude - self.dampening*TAU)
        if self.amplitude <= 1e-14:
            print("DEL")
            self.kill()
    def get_offset(self, tile):
        t = Vec2(tile)
        d = (t-self.center).length()
        val =  -self.amplitude*two_smoothstep(-self.trail, self.ahead, d-self.time)
        return val


class IsoTiles:
    sprite = None
    sprite_w, sprite_h = None, None
    TOP_OFF = 20
    def __init__(self, itiles, jtiles):
        if IsoTiles.sprite is None:
            IsoTiles.sprite = scale_uniform(load_image("tile1"), 0.2)
            IsoTiles.sprite_w = IsoTiles.sprite.get_width()
            IsoTiles.sprite_h = IsoTiles.sprite.get_height()
        self.tile_offsets = {}
        self.animations = pg.sprite.Group()
        self.itiles = itiles
        self.jtiles = jtiles
    def draw(self, surf):
        for i in range(self.itiles):
            for j in range(self.jtiles):
                v = self.tile_to_coord((i,j), self.get_tile_offset((i,j)))
                surf.blit(self.sprite, pg.Rect(v.x,v.y,0,0))
    def tile_to_coord(self, t, offset=0.0):
        i,j = t[0],t[1]
        return Vec2(WIDTH/2 + self.sprite_w/2 * (i-j-1), self.TOP_OFF+0.25*self.sprite_h*(i+j+offset))
    def coord_to_tile(self, v: Vec2):
        h1 = (v.x-WIDTH/2)*2/self.sprite_w
        h2 = 4/self.sprite_h * (v.y-self.TOP_OFF)
        i = floor((h1+h2)/2)
        j = floor((h2-h1)/2)
        if self.is_valid_tile((i,j)):
            return (i,j)
        else:
            return (-1,-1)
    def is_valid_tile(self, tile):
        i,j = tile
        return not (i < 0 or j < 0 or i >= self.itiles or j >= self.jtiles)

    def get_tile_offset(self, tile) -> float:
        if not self.is_valid_tile(tile):
            return 0.0
        else:
            offset = self.tile_offsets.get(tile, 0.0)
            for a in self.animations:
                offset += a.get_offset(tile)
            return offset

    def set_tile_offset(self, tile, offset):
        if self.is_valid_tile(tile):
            self.tile_offsets[tile] = offset
    def update(self):
        self.animations.update()

class Game:
    def __init__(self):
        pg.init()
        print(f"Data Path: {data_path}")
        self.window = pg.display.set_mode((WIDTH,HEIGHT))
        pg.display.set_caption("Isometric")
        self.running = True
        self.clock = pg.time.Clock()
        self.tiles = IsoTiles(20,20)


    def render(self):
        self.window.fill((0,80,180))
        self.tiles.draw(self.window)

    def update(self):
        self.tiles.update()

    def run(self):
        while self.running:
            for e in pg.event.get():
                if e.type == pg.QUIT:
                    self.running = False
                if e.type == pg.MOUSEBUTTONDOWN and e.button == 1:
                    pos = pg.mouse.get_pos()
                    tile = self.tiles.coord_to_tile(Vec2(pos))
                    self.tiles.animations.add(CircularWaveAnimation(tile))
                #if e.type == pg.MOUSEBUTTONDOWN and e.button == 1:
                #    pos = pg.mouse.get_pos()
                #    tile = self.tiles.coord_to_tile(Vec2(pos))
                #    self.tiles.set_tile_offset(tile, self.tiles.get_tile_offset(tile)+0.2)
                #if e.type == pg.MOUSEBUTTONDOWN and e.button == 3:
                #    pos = pg.mouse.get_pos()
                #    tile = self.tiles.coord_to_tile(Vec2(pos))
                #    self.tiles.set_tile_offset(tile, self.tiles.get_tile_offset(tile)-0.2)
            self.update()
            self.render()
            pg.display.update()
            self.clock.tick(60)

Game().run()
