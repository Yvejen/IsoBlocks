import pygame as pg
from pygame.math import Vector2 as Vec2
import json
from sprites import SpriteCatalogue
from math import floor
from effects import CircularWaveAnimation


class IsoTiles:
    MAXCNT = 60

    def __init__(self, sprites: SpriteCatalogue):
        self.sprites: SpriteCatalogue = sprites
        # All sprites should have the same dimension, or the isometric effect won't work
        # self.s_w = self.sprites[0].get_width()
        # self.s_h = self.sprites[0].get_height()
        self.tile_offsets = {}
        self.tile_type = {}
        self.animations = pg.sprite.Group()
        self.framecnt = self.MAXCNT
        self.orig: Vec2 = Vec2(0, 0)
        self.flipped = set()

    def to_json(self):
        tile_loc = list(self.tile_type.keys())
        tile_t = list(self.tile_type.values())
        flipped = list(self.flipped)
        s = {"tile_loc": tile_loc, "tile_type": tile_t, "flipped": flipped}
        return json.dumps(s)

    @classmethod
    def from_json(cls, sprites: SpriteCatalogue, json_str: str):
        itiles = cls(sprites)
        d = json.loads(json_str)
        for (
            k,
            v,
        ) in zip(d["tile_loc"], d["tile_type"]):
            ktup = (k[0], k[1])
            itiles.tile_type[ktup] = v
        for f in d["flipped"]:
            itiles.flipped.add((f[0], f[1]))
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
        # Always draw Buildings after the landscape has been drawn
        # for tileindex in sorted(self.buildings):
        #    self.buildings[tileindex].draw(surf, self.iso_to_screen(tileindex, offset=-0.4))

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
        s_w = self.sprites[0].get_width()
        s_h = self.sprites[0].get_height()
        i, j = t[0], t[1]
        return Vec2(
            self.orig.x + s_w / 2 * (i - j - 1),
            self.orig.y + 0.25 * s_h * (i + j + offset),
        )

    def screen_to_iso(self, v: Vec2):
        s_w = self.sprites[0].get_width()
        s_h = self.sprites[0].get_height()
        h1 = (v.x - self.orig.x) * 2 / s_w
        h2 = 4 / s_h * (v.y - self.orig.y)
        i = floor((h1 + h2) / 2)
        j = floor((h2 - h1) / 2)
        return (i, j)

    def is_valid_tile(self, tile):
        return tile in self.tile_type

    def get_tile_offset(self, tile) -> float:
        # if not self.is_valid_tile(tile):
        #     return 0.0
        # else:
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


class Bar:
    def __init__(
        self, dim, ratio=0.0, bg=pg.Color(60, 60, 60), fg=pg.Color(0, 200, 60)
    ):
        # 0 Empty 1 Full
        self.ratio = ratio
        self.dim = dim
        self.bg = bg
        self.fg = fg

    def set_ratio(self, ratio):
        self.ratio = ratio

    def draw(self, surf, at):
        back = pg.Rect(at, self.dim)
        front = pg.Rect(at, (self.dim.x * self.ratio, self.dim.y))
        pg.draw.rect(surf, self.bg, back)
        pg.draw.rect(surf, self.fg, front)


class Building(pg.sprite.Sprite):
    MAX_HP = 100

    def __init__(self, sp_cat, iso_tiles, where=(0, 0)):
        super().__init__()
        self.coord = where
        self.catalogue = sp_cat
        self.iso_tiles = iso_tiles
        self.building_hp = self.MAX_HP
        self.bar = Bar(Vec2(40, 10), ratio=self.building_hp / self.MAX_HP)

    def draw(self, srf, trans=False):
        pos = self.iso_tiles.iso_to_screen(
            self.coord, offset=-0.4 + self.iso_tiles.get_tile_offset(self.coord)
        )
        img = self.catalogue.get(0, trans=trans)
        dst = img.get_rect()
        # Extremely hacky, but places the image at the roughly correct location
        dst.x = int(pos.x + 0.1 * dst.width)
        dst.y = int(pos.y + 0.1 * dst.height)
        srf.blit(img, dst)
        self.bar.draw(srf, pos)

    def damage(self, dmg):
        self.building_hp -= dmg
        self.bar.set_ratio(self.building_hp / self.MAX_HP)
        if self.building_hp <= 0:
            self.explode()

    def explode(self):
        effect = CircularWaveAnimation(
            amplitude=1, ahead=1, trail=1, epicenter=self.coord
        )
        self.iso_tiles.animations.add(effect)
        self.kill()
