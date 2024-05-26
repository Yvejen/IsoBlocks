import pygame as pg
import os
from pygame.math import Vector2 as Vec2
from math import pi, sin, cos, floor
import glob
from dataclasses import dataclass
from effects import DirectedShockwave, CrossWaveAnimation, CircularWaveAnimation
from sprites import SpriteCatalogue

WIDTH = 800
HEIGHT = 600
TAU = 1 / 60

data_path = os.path.join(os.path.dirname(__file__), "data")

# def load_tileset(names, directory):
#    tileset = []
#    for filename in names:
#        tileset.append(SpriteCatalogue.load_image(os.path.join(directory, filename)))
#    return tileset

# def sym_smoothstep(le, re, x):
#    clamp = lambda x: max(le, min(re, x))
#    # Map (le,re) -> (-1,1)
#    x = 2 * (clamp(x) - le) / (re - le) - 1.0
#    return x**4 - 2 * x**2 + 1


class Cycle:
    def __init__(self, start=0, modulus=2, offset=0):
        self.val = start
        self.modulus = modulus
        self.offset = offset

    def cycle_up(self):
        self.val += 1
        if self.val == self.modulus:
            self.val = 0

    def cycle_down(self):
        if self.val == 0:
            self.val = self.modulus
        self.val -= 1

    def get(self):
        return self.val + self.offset


class IsoTiles:
    MAXCNT = 60

    def __init__(self, itiles, jtiles, sprites: SpriteCatalogue):
        self.sprites: SpriteCatalogue = sprites
        self.s_w = self.sprites[0].get_width()
        self.s_h = self.sprites[0].get_height()
        self.tile_offsets = {}
        self.tile_type = {(i, j): 0 for i in range(itiles) for j in range(jtiles)}
        self.animations = pg.sprite.Group()
        self.itiles = itiles
        self.jtiles = jtiles
        self.dynamic_tiles = {}
        self.framecnt = self.MAXCNT
        self.orig: Vec2 = Vec2(0, 0)

    def set_origin(self, orig: Vec2):
        self.orig = orig

    def set_scale(self, scale=1.0):
        self.sprites.scale_catalogue(scale)
        self.s_w = self.sprites[0].get_width()
        self.s_h = self.sprites[0].get_height()

    def draw(self, surf):
        for tileindex in self.tile_type.keys():
            v = self.tile_to_screen(tileindex)
            if sprite := self.get_type_sprite(self.get_tile_type(tileindex)):
                surf.blit(sprite, pg.Rect(v.x, v.y, 0, 0))

    def get_type_sprite(self, type: None | int):
        if type is None:
            return None
        else:
            return self.sprites[type]

    def get_tile_type(self, tileindex) -> None | int:
        return self.tile_type.get(tileindex, None)

    def get_tile_sprite(self, tile) -> None | pg.Surface:
        if not self.is_valid_tile(tile):
            return None
        if tile in self.dynamic_tiles:
            idx = self.dynamic_tiles[tile].get()
        else:
            idx = self.tile_type[tile]
        return self.sprites[idx]

    def tile_to_screen(self, tile):
        return self.iso_to_screen(tile, self.get_tile_offset(tile))

    def iso_to_screen(self, t, offset=0.0):
        i, j = t[0], t[1]
        return Vec2(
            self.orig.x + self.s_w / 2 * (i - j - 1),
            self.orig.y + 0.25 * self.s_h * (i + j + offset),
        )

    def coord_to_tile(self, v: Vec2):
        h1 = (v.x - self.orig.x) * 2 / self.s_w
        h2 = 4 / self.s_h * (v.y - self.orig.y)
        i = floor((h1 + h2) / 2)
        j = floor((h2 - h1) / 2)
        if self.is_valid_tile((i, j)):
            return (i, j)
        else:
            return (-1, -1)

    def is_valid_tile(self, tile):
        return tile in self.tile_type

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

    def set_tile_type(self, tile, ttype=0):
        if self.is_valid_tile(tile):
            self.tile_type[tile] = ttype

    def update(self):
        self.animations.update()
        self.framecnt -= 1
        if self.framecnt == 0:
            for c in self.dynamic_tiles.values():
                c.cycle()
            self.framecnt = self.MAXCNT


class Game:
    def __init__(self):
        pg.init()
        print(f"Data Path: {data_path}")
        self.window = pg.display.set_mode((WIDTH, HEIGHT))
        pg.display.set_caption("Isometric")
        self.running = True
        self.clock = pg.time.Clock()
        self.sprite_cat = SpriteCatalogue()
        self.sprite_cat.add_sprites(
            self.create_resource_list(data_path, range(1, 6), pattern="tile{}")
        )
        self.tiles = IsoTiles(10, 10, self.sprite_cat)
        self.pos = Vec2(0, 0)
        self.font_size = 16
        self.font = pg.font.SysFont("DejaVu", size=self.font_size)
        self.mode = 0
        self.selected_effect = Cycle(start=0, modulus=3, offset=0)
        self.effect_types = [
            DirectedShockwave,
            CrossWaveAnimation,
            CircularWaveAnimation,
        ]
        self.zoom = 1.0

    @staticmethod
    def create_resource_list(dir, ran, pattern="sprite{}", ext="png"):
        names = []
        for i in ran:
            filename = os.path.join(dir, pattern.format(i) + "." + ext)
            names.append(filename)
        return names

    def draw_text(self, x, y, text, col=(200, 200, 200)):
        surf = self.font.render(text, True, col)
        dest = surf.get_rect()
        dest.x = x
        dest.y = y
        self.window.blit(surf, dest)

    def draw_ui(self):
        menu_top = 20
        self.draw_text(WIDTH - 60, menu_top, f"FPS: {int(self.clock.get_fps())}")
        match self.mode:
            case 0:
                self.draw_text(20, menu_top, "Effect Mode")
                menu_top += self.font_size
                self.draw_text(20, menu_top, "LMB: Spawn Effect")
                menu_top += self.font_size
                self.draw_text(20, menu_top, "N/P: Next Effect/Previous Effect")
                menu_top += self.font_size
                self.draw_text(
                    20,
                    menu_top,
                    f"Selected Effect {self.effect_types[self.selected_effect.get()]}",
                )

    def render(self):

        self.tiles.set_origin(-self.pos)
        self.window.fill((0, 80, 180))
        self.tiles.draw(self.window)
        self.draw_ui()

    def update(self):
        for e in pg.event.get():
            if e.type == pg.QUIT:
                self.running = False
            match self.mode:
                case 0:
                    if e.type == pg.MOUSEBUTTONDOWN and e.button == 1:
                        pos = pg.mouse.get_pos()
                        tile = self.tiles.coord_to_tile(Vec2(pos))
                        effect = self.effect_types[self.selected_effect.get()](
                            amplitude=1.5,
                            ahead=0.8,
                            trail=2,
                            epicenter=tile,
                            dir=Vec2(1, 0),
                        )
                        self.tiles.animations.add(effect)
                    if e.type == pg.KEYDOWN and e.key == pg.K_n:
                        self.selected_effect.cycle_up()
                    if e.type == pg.KEYDOWN and e.key == pg.K_p:
                        self.selected_effect.cycle_down()
            # if e.type == pg.MOUSEBUTTONDOWN and e.button == 1:
            #    pos = pg.mouse.get_pos()
            #    tile = self.tiles.coord_to_tile(Vec2(pos))
            #    self.tiles.set_tile_offset(tile, self.tiles.get_tile_offset(tile)+0.2)
            # if e.type == pg.MOUSEWHEEL:
            #    pos = pg.mouse.get_pos()
            #    tile = self.tiles.coord_to_tile(Vec2(pos))
            #    self.tiles.set_tile_offset(
            #        tile, self.tiles.get_tile_offset(tile) - 0.2 * e.y
            #    )
            # if e.type == pg.MOUSEWHEEL:
            #    angle += e.y * 0.1
            #    angle %= 2*pi
            # if e.type == pg.MOUSEBUTTONDOWN and e.button == 3:
            #    pos = pg.mouse.get_pos()
            #    tile = self.tiles.coord_to_tile(Vec2(pos))
            #    if self.tiles.is_valid_tile(tile):
            #        self.tiles.tile_type[tile] += 1
            if e.type == pg.MOUSEWHEEL:
                self.zoom += e.y * 0.1
                self.tiles.set_scale(self.zoom)

        # Camera Movement
        pressed = pg.key.get_pressed()
        speed = 3
        if pressed[pg.K_a]:
            self.pos.x -= speed
        if pressed[pg.K_d]:
            self.pos.x += speed
        if pressed[pg.K_w]:
            self.pos.y -= speed
        if pressed[pg.K_s]:
            self.pos.y += speed
        self.tiles.update()

    def run(self):
        while self.running:
            self.update()
            self.render()
            pg.display.update()
            self.clock.tick(60)


Game().run()
