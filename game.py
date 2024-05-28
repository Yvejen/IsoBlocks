import pygame as pg
import os
from pygame.math import Vector2 as Vec2
from math import pi, sin, cos, floor
from dataclasses import dataclass
from enum import Enum
from effects import DirectedShockwave, CrossWaveAnimation, CircularWaveAnimation
from sprites import SpriteCatalogue, Sprite, AnimatedSprite, Cycle
import json

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


class IsoTiles:
    MAXCNT = 60

    def __init__(self, sprites: SpriteCatalogue):
        self.sprites: SpriteCatalogue = sprites
        self.s_w = self.sprites[0].get_width()
        self.s_h = self.sprites[0].get_height()
        self.tile_offsets = {}
        #self.tile_type = {(i, j): 0 for i in range(itiles) for j in range(jtiles)}
        self.tile_type = {}
        self.animations = pg.sprite.Group()
        self.framecnt = self.MAXCNT
        self.orig: Vec2 = Vec2(0, 0)
        self.flipped = set()


    def to_json(self):
        tile_loc = list(self.tile_type.keys())
        tile_t   = list(self.tile_type.values())
        flipped = list(self.flipped)
        s = {"tile_loc" : tile_loc, "tile_type" : tile_t, "flipped" : flipped}
        return json.dumps(s)

    @classmethod
    def from_json(cls, sprites: SpriteCatalogue, json_str: str):
        itiles = cls(sprites)
        d = json.loads(json_str)
        for k,v, in zip(d["tile_loc"], d["tile_type"]):
            ktup = (k[0],k[1])
            itiles.tile_type[ktup] = v
        for f in d["flipped"]:
            itiles.flipped.add((f[0],f[1]))
        return itiles

    def set_origin(self, orig: Vec2):
        self.orig = orig

    def set_scale(self, scale=1.0):
        self.sprites.scale_catalogue(scale)
        self.s_w = self.sprites[0].get_width()
        self.s_h = self.sprites[0].get_height()

    def draw(self, surf):
        for tileindex in sorted(self.tile_type.keys()):
            v = self.tile_to_screen(tileindex)
            if sprite := self.get_tile_sprite(tileindex):
                surf.blit(sprite, pg.Rect(v.x, v.y, 0, 0))

    def draw_block_at(self, surf, pos, block_type, flipped=False, trans=False):
        if sprite := self.sprites.get(block_type, flipped, trans):
            surf.blit(sprite, pg.Rect(pos.x, pos.y, 0, 0))

    def get_type_sprite(self, type: None | int):
        if type is None:
            return None
        else:
            return self.sprites[type]

    def add_tile(self, idx, type, flipped):
        self.tile_type[idx] = type
        if flipped:
            self.flipped.add(idx)
        else:
            try:
                self.flipped.remove(idx)
            except KeyError:
                pass

    def remove_tile(self, idx):
        try:
            del self.tile_type[idx]
        except KeyError:
            pass

    def get_tile_type(self, tileindex) -> None | int:
        return self.tile_type.get(tileindex, None)

    def get_tile_sprite(self, tile) -> None | pg.Surface:
        if not self.is_valid_tile(tile):
            return None
        else:
            idx = self.tile_type[tile]
        return self.sprites.get(idx, tile in self.flipped)

    def tile_to_screen(self, tile):
        return self.iso_to_screen(tile, self.get_tile_offset(tile))

    def iso_to_screen(self, t, offset=0.0):
        i, j = t[0], t[1]
        return Vec2(
            self.orig.x + self.s_w / 2 * (i - j - 1),
            self.orig.y + 0.25 * self.s_h * (i + j + offset),
        )

    def screen_to_iso(self, v: Vec2):
        h1 = (v.x - self.orig.x) * 2 / self.s_w
        h2 = 4 / self.s_h * (v.y - self.orig.y)
        i = floor((h1 + h2) / 2)
        j = floor((h2 - h1) / 2)
        return (i,j)

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

    def flip_tile(self, tile):
        if self.is_valid_tile(tile):
            if tile in self.flipped:
                self.flipped.remove(tile)
            else:
                self.flipped.add(tile)

    def update(self):
        self.animations.update()


class Game:
    def __init__(self, save="world.json"):
        pg.init()
        self.save = save
        print(f"Data Path: {data_path}")
        self.window = pg.display.set_mode((WIDTH, HEIGHT))
        pg.display.set_caption("Isometric")
        self.running = True
        self.clock = pg.time.Clock()
        self.sprite_cat = SpriteCatalogue()
        self.max_types = (
            max(
                self.sprite_cat.add_sprites(
                    *[
                        Sprite.from_file(fname)
                        for fname in self.create_resource_list(
                            data_path, range(1, 3), pattern="tile{}"
                        )
                    ],
                    AnimatedSprite.from_files(
                        self.create_resource_list(
                            data_path, range(3, 5), pattern="tile{}"
                        )
                    ),
                )
            )
            + 1
        )
        self.tiles = IsoTiles(self.sprite_cat)
        self.pos = Vec2(0, 0)
        self.font_size = 16
        self.font = pg.font.SysFont("DejaVu", size=self.font_size)
        self.mode = Cycle(0, 2, 0)
        self.selected_effect = Cycle(start=0, modulus=3, offset=0)
        self.effect_types = [
            DirectedShockwave,
            CrossWaveAnimation,
            CircularWaveAnimation,
        ]
        self.zoom = 1.0
        self.editor_block_type = Cycle(0, self.max_types, 0)
        self.editor_flipped = False

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

    def draw_block_placer(self, pos):
        snap = self.tiles.iso_to_screen(self.tiles.screen_to_iso(pos))
        self.tiles.draw_block_at(self.window, snap, self.editor_block_type.get(), self.editor_flipped, True)


    def draw_ui(self):
        menu_top = 20
        self.draw_text(WIDTH - 60, menu_top, f"FPS: {int(self.clock.get_fps())}")
        match self.mode.get():
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
                menu_top += self.font_size
                self.draw_text(20, menu_top, "Mode Switch: M")
            case 1:
                self.draw_text(20, menu_top, "Build Mode")
                menu_top += 20
                self.draw_text(20, menu_top, "Scrollwheel: Move Block Up/Down")
                menu_top += 20
                self.draw_text(20, menu_top, "Change Block Type: RMB")
                menu_top += 20
                self.draw_text(20, menu_top, "Rotate Block: R")
                # This should be handled elsewhere
                pos = Vec2(pg.mouse.get_pos())
                self.draw_block_placer(pos)

    def render(self):
        self.tiles.set_origin(-self.pos)
        self.window.fill((0, 80, 180))
        self.tiles.draw(self.window)
        self.draw_ui()

    def update(self):
        self.sprite_cat.update()
        for e in pg.event.get():
            if e.type == pg.QUIT:
                self.running = False
            if e.type == pg.KEYDOWN and e.key == pg.K_m:
                self.mode.cycle_down()

            if e.type == pg.KEYDOWN and e.key == pg.K_o:
                print("Saving")
                jstr = self.tiles.to_json()
                with open(self.save, "w") as sfile:
                    sfile.write(jstr)
            if e.type == pg.KEYDOWN and e.key == pg.K_l:
                print("Loading")
                with open(self.save, "r") as sfile:
                    jstr = sfile.read()
                self.tiles = IsoTiles.from_json(self.sprite_cat, jstr)
            match self.mode.get():
                case 0:
                    if e.type == pg.MOUSEWHEEL:
                        self.zoom += e.y * 0.1
                        self.tiles.set_scale(self.zoom)
                    if e.type == pg.MOUSEBUTTONDOWN and e.button == 1:
                        pos = pg.mouse.get_pos()
                        tile = self.tiles.screen_to_iso(Vec2(pos))
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
                case 1:
                    pos = Vec2(pg.mouse.get_pos())
                   # if e.type == pg.MOUSEWHEEL:
                   #     offset = e.y * 0.1
                   #     tile = self.tiles.screen_to_iso(Vec2(pos))
                   #     self.tiles.set_tile_offset(
                   #         tile, self.tiles.get_tile_offset(tile) + offset
                   #     )
                    if e.type == pg.MOUSEWHEEL and e.y > 0:
                        self.editor_block_type.cycle_up()
                    if e.type == pg.MOUSEWHEEL and e.y < 0:
                        self.editor_block_type.cycle_down()
                        
                    if e.type == pg.MOUSEBUTTONDOWN and e.button == 1:
                        self.tiles.add_tile(self.tiles.screen_to_iso(pos), self.editor_block_type.get(), self.editor_flipped)
                    if e.type == pg.KEYDOWN and e.key == pg.K_r:
                        self.editor_flipped = not self.editor_flipped
                    if e.type == pg.MOUSEBUTTONDOWN and e.button == 3:
                        self.tiles.remove_tile(self.tiles.screen_to_iso(pos))
                    if e.type == pg.KEYDOWN and e.key == pg.K_r:
                        tile = self.tiles.screen_to_iso(pos)
                        if self.tiles.is_valid_tile(tile):
                            self.tiles.flip_tile(tile)
            # if e.type == pg.MOUSEBUTTONDOWN and e.button == 1:
            #    pos = pg.mouse.get_pos()
            #    tile = self.tiles.screen_to_iso(Vec2(pos))
            #    self.tiles.set_tile_offset(tile, self.tiles.get_tile_offset(tile)+0.2)
            # if e.type == pg.MOUSEWHEEL:
            #    pos = pg.mouse.get_pos()
            #    tile = self.tiles.screen_to_iso(Vec2(pos))
            #    self.tiles.set_tile_offset(
            #        tile, self.tiles.get_tile_offset(tile) - 0.2 * e.y
            #    )
            # if e.type == pg.MOUSEWHEEL:
            #    angle += e.y * 0.1
            #    angle %= 2*pi
            # if e.type == pg.MOUSEBUTTONDOWN and e.button == 3:
            #    pos = pg.mouse.get_pos()
            #    tile = self.tiles.screen_to_iso(Vec2(pos))
            #    if self.tiles.is_valid_tile(tile):
            #        self.tiles.tile_type[tile] += 1

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
