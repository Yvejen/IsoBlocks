import pygame as pg
import os
from pygame.math import Vector2 as Vec2
from math import atan2, degrees, pi, sin, cos, floor
from enum import Enum

WIDTH=800
HEIGHT=600

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

class IsoTiles:
    sprite = None
    sprite_w, sprite_h = None, None
    TOP_OFF = 20
    def __init__(self, itiles, jtiles):
        if IsoTiles.sprite is None:
            IsoTiles.sprite = scale_uniform(load_image("tile1"), 0.4)
            IsoTiles.sprite_w = IsoTiles.sprite.get_width()
            IsoTiles.sprite_h = IsoTiles.sprite.get_height()
        self.tile_offsets = {}
        self.itiles = itiles
        self.jtiles = jtiles
    def draw(self, surf):
        for i in range(self.itiles):
            for j in range(self.jtiles):
                v = self.tile_to_coord((i,j), self.tile_offsets.get((i,j), 0.0))
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

    def get_tile_offset(self, tile):
        if not self.is_valid_tile(tile):
            return 0.0
        else:
            return self.tile_offsets.get(tile, 0.0)
    def set_tile_offset(self, tile, offset):
        if self.is_valid_tile(tile):
            self.tile_offsets[tile] = offset

class Game:
    def __init__(self):
        pg.init()
        print(f"Data Path: {data_path}")
        self.window = pg.display.set_mode((WIDTH,HEIGHT))
        pg.display.set_caption("Isometric")
        self.running = True
        self.clock = pg.time.Clock()
        self.tiles = IsoTiles(10,10)


    def render(self):
        self.window.fill((0,80,180))
        self.tiles.draw(self.window)

    def update(self):
        pass

    def run(self):
        while self.running:
            for e in pg.event.get():
                if e.type == pg.QUIT:
                    self.running = False
                if e.type == pg.MOUSEBUTTONDOWN and e.button == 1:
                    pos = pg.mouse.get_pos()
                    tile = self.tiles.coord_to_tile(Vec2(pos))
                    self.tiles.set_tile_offset(tile, self.tiles.get_tile_offset(tile)+0.2)
                if e.type == pg.MOUSEBUTTONDOWN and e.button == 3:
                    pos = pg.mouse.get_pos()
                    tile = self.tiles.coord_to_tile(Vec2(pos))
                    self.tiles.set_tile_offset(tile, self.tiles.get_tile_offset(tile)-0.2)
            self.update()
            self.render()
            pg.display.update()
            self.clock.tick(60)

Game().run()
