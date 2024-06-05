import pygame as pg
import os
from pygame.math import Vector2 as Vec2
from enum import Enum
from effects import DirectedShockwave, CrossWaveAnimation, CircularWaveAnimation
from sprites import SpriteCatalogue, Sprite, AnimatedSprite, Cycle
from isotiles import IsoTiles, Building

WIDTH = 800
HEIGHT = 600
TAU = 1 / 60
FONT_SIZE = 16

data_path = os.path.join(os.path.dirname(__file__), "data")


class GameState(Enum):
    EFFECT_MODE = 0
    BUILD_MODE = 1
    CITY_MODE = 2
    PLAY_MODE = 3
    LAST_MODE = 4


class Game:
    def __init__(self, save="world.json"):
        pg.init()
        self.savefile: str = save
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
        self.building_cat = SpriteCatalogue()
        self.building_cat.add_sprites(
            Sprite.from_file(os.path.join(data_path, "city.png"), size=0.8)
        )
        self.tiles = IsoTiles(self.sprite_cat)
        self.cities = pg.sprite.Group()
        self.pos = Vec2(0, 0)
        self.font = pg.font.SysFont("DejaVu", size=FONT_SIZE)
        self.mode = Cycle(0, GameState.LAST_MODE.value, 0)
        self.selected_effect = Cycle(start=0, modulus=3, offset=0)
        self.effect_types = [
            DirectedShockwave,
            CrossWaveAnimation,
            CircularWaveAnimation,
        ]
        self.zoom = 1.0
        self.editor_block_type = Cycle(0, self.max_types, 0)
        self.editor_flipped = False
        self.editor_city = Building(self.building_cat, self.tiles, (0, 0))

        # self.player = Robot()

    @staticmethod
    def create_resource_list(dir, ran, pattern="sprite{}", ext="png"):
        names = []
        for i in ran:
            filename = os.path.join(dir, pattern.format(i) + "." + ext)
            names.append(filename)
        return names

    def draw_str(self, x, y, text, col=(200, 200, 200)):
        surf = self.font.render(text, True, col)
        dest = surf.get_rect()
        dest.x = x
        dest.y = y
        self.window.blit(surf, dest)

    def draw_block_placer(self, pos):
        snap = self.tiles.iso_to_screen(self.tiles.screen_to_iso(pos))
        self.tiles.draw_block_at(
            self.window, snap, self.editor_block_type.get(), self.editor_flipped, True
        )

    def draw_city_placer(self, pos):
        iso_snap = self.tiles.screen_to_iso(pos)
        self.editor_city.coord = iso_snap
        self.editor_city.draw(self.window, trans=True)

    def draw_text(self, x, y, text, sep=FONT_SIZE):
        for line in text.splitlines():
            self.draw_str(x, y, line)
            y = y + sep

    def draw_ui(self, pos):
        menu_top = 20
        self.draw_text(WIDTH - 60, menu_top, f"FPS: {int(self.clock.get_fps())}")
        match self.mode.get():
            case 0:
                self.draw_text(
                    20,
                    10,
                    "Effect Mode\n"
                    "LMB: Spawn Effect\n"
                    "N/P: Next Effect/Previous Effect\n"
                    f"Selected Effect {self.effect_types[self.selected_effect.get()]}"
                    "Mode Switch: M",
                )
            case 1:
                self.draw_text(
                    20,
                    10,
                    "Build Mode\n"
                    "Scrollwheel: Move Block Up/Down\n"
                    "Change Block Type: RMB\n"
                    "Rotate Block: R\n",
                )
                self.draw_block_placer(pos)
            case 2:
                self.draw_text(20, 10, "City Place Mode\n" "LMB: Place City\n")
                self.draw_city_placer(pos)

    def render(self):
        # Update relative position
        self.tiles.set_origin(-self.pos)
        self.window.fill((0, 80, 180))
        self.tiles.draw(self.window)
        for c in self.cities:
            c.draw(self.window)
        self.draw_ui(Vec2(pg.mouse.get_pos()))

    # Save the current game state to a file that can be loaded with the load method
    def save(self, filename):
        print("Saving")
        jstr = self.tiles.to_json()
        with open(filename, "w") as sfile:
            sfile.write(jstr)

    def load(self, filename):
        print("Loading")
        with open(filename, "r") as sfile:
            jstr = sfile.read()
        self.tiles = IsoTiles.from_json(self.sprite_cat, jstr)

    def mode_effect_controls(self, e):
        if e.type == pg.MOUSEWHEEL:
            self.zoom += e.y * 0.1
            self.sprite_cat.scale_catalogue(self.zoom)
            self.building_cat.scale_catalogue(self.zoom)
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

    def mode_build_controls(self, e):
        if e.type == pg.KEYDOWN and e.key == pg.K_o:
            self.save(self.savefile)
        if e.type == pg.KEYDOWN and e.key == pg.K_l:
            self.load(self.savefile)
        pos = Vec2(pg.mouse.get_pos())
        if e.type == pg.MOUSEWHEEL and e.y > 0:
            self.editor_block_type.cycle_up()
        if e.type == pg.MOUSEWHEEL and e.y < 0:
            self.editor_block_type.cycle_down()
        if e.type == pg.MOUSEBUTTONDOWN and e.button == 1:
            self.tiles.add_tile(
                self.tiles.screen_to_iso(pos),
                self.editor_block_type.get(),
                self.editor_flipped,
            )
        if e.type == pg.KEYDOWN and e.key == pg.K_r:
            self.editor_flipped = not self.editor_flipped
        if e.type == pg.MOUSEBUTTONDOWN and e.button == 3:
            self.tiles.remove_tile(self.tiles.screen_to_iso(pos))
        if e.type == pg.KEYDOWN and e.key == pg.K_r:
            tile = self.tiles.screen_to_iso(pos)
            if self.tiles.is_valid_tile(tile):
                self.tiles.flip_tile(tile)

    def mode_city_build_controls(self, e):
        if e.type == pg.MOUSEBUTTONDOWN and e.button == 1:
            # Editor item location gets updated every frame
            self.cities.add(self.editor_city)
            self.editor_city = Building(
                self.building_cat, self.tiles, self.editor_city.coord
            )

    def camera_control(self):
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

    def update(self):
        self.sprite_cat.update()
        for e in pg.event.get():
            if e.type == pg.QUIT:
                self.running = False
            if e.type == pg.KEYDOWN and e.key == pg.K_m:
                self.mode.cycle_down()
            match self.mode.get():
                case GameState.EFFECT_MODE.value:
                    self.mode_effect_controls(e)
                case GameState.BUILD_MODE.value:
                    self.mode_build_controls(e)
                case GameState.CITY_MODE.value:
                    self.mode_city_build_controls(e)
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
        if self.mode.get() in {0, 2}:
            self.camera_control()
        self.tiles.update()

    def run(self):
        while self.running:
            self.update()
            self.render()
            pg.display.update()
            self.clock.tick(60)


class Robot(pg.sprite.Sprite):
    def __init__(self, idle, walking, cmnd):
        super().__init__()
        self.idle_animation: AnimatedSprite = idle
        self.walking_animation: AnimatedSprite = walking
        self.active_animation = self.idle_animation
        self.cmnd = cmnd
        self.walking = 0
        self.updatecnt = 60
        self.cnt = 0
        self.pos = Vec2(0, 0)
        self.orig = Vec2(0, 0)

    def set_origin(self, origin: Vec2):
        self.orig = origin

    def set_scale(self, global_scale=1.0):
        self.idle_animation.set_scale(global_scale)
        self.walking_animation.set_scale(global_scale)

    def update(self, *args):
        # We need a better meachnism for handling sprite timings
        if self.cnt >= self.updatecnt:
            self.cnt = 0
            self.active_animation.update()
        self.cmnd(self, *args)
        self.cnt += 1

    def draw(self, srf):
        img = self.active_animation.get()
        dst = img.get_rect()
        dpos = self.orig + self.pos
        dst.x = int(dpos.x)
        dst.y = int(dpos.y)
        srf.blit(img, dst)


Game().run()
