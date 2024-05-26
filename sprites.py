import os
import pygame as pg


def load_image(file):
    try:
        image = pg.image.load(file).convert_alpha()
    except FileNotFoundError:
        print(f"Could not load resource from file {file}")
        errsurf = pg.Surface((20, 20))
        errsurf.fill("purple")
        image = errsurf
    return image


def scale_uniform(img, factor=1.0):
    width, height = img.get_width(), img.get_height()
    simg = pg.transform.scale(img, (width * factor, height * factor))
    return simg


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


class Sprite(pg.sprite.Sprite):
    def __init__(self, image, global_scale=1.0, size=1.0):
        super().__init__()
        # Intrinsic size of this object
        self.size = size
        self.raw = image
        self.set_scale(global_scale)

    def set_scale(self, global_scale=1.0):
        # Global scale of the game
        self.global_scale = global_scale
        self.scaled = scale_uniform(self.raw, self.size * self.global_scale)
        self.flipped = pg.transform.flip(self.scaled, flip_x=True, flip_y=False)

    def get(self, flipped=False):
        if flipped:
            return self.flipped
        else:
            return self.scaled

    def update(self):
        pass

    @classmethod
    def from_file(cls, filename, global_scale=1.0, size=1.0):
        return cls(load_image(filename), global_scale, size)


class AnimatedSprite(Sprite):
    def __init__(self, images, global_scale=1.0, size=1.0, updatecnt=60):
        super().__init__(images[0], global_scale, size)
        self.frames = images
        self.updatecnt = updatecnt
        self.count = 0
        self.cycle = Cycle(0, len(images))
        self.paused = False

    def update(self):
        if not self.paused:
            self.count += 1
        if self.count == self.updatecnt:
            self.count = 0
            self.cycle.cycle_up()
            self.raw = self.frames[self.cycle.get()]
            self.set_scale(self.global_scale)

    def pause(self, pause=True):
        self.paused = pause

    @classmethod
    def from_file(cls, filename, global_scale=1.0, size=1.0):
        return cls([load_image(filename)], global_scale, size)

    @classmethod
    def from_files(cls, filenames, global_scale=1.0, size=1.0, updatecnt=60):
        frames = []
        for file in filenames:
            frames.append(load_image(file))
        return cls(frames, global_scale, size, updatecnt)


class SpriteCatalogue:
    def __init__(self):
        self.global_scale = 1.0
        self.sprites: list[Sprite] = []

    def add_sprites(self, *sprites):
        print(sprites)
        num_before = len(self.sprites)
        self.sprites.extend(sprites)
        num_after = len(self.sprites)
        # Update cached sprites
        self.scale_catalogue()
        return range(num_before, num_after)

    def scale_catalogue(self, scale=1.0):
        for s in self.sprites:
            s.set_scale(scale)

    def __getitem__(self, idx):
        return self.get(idx)

    def update(self):
        for s in self.sprites:
            s.update()

    def get(self, idx, flipped=False):
        return self.sprites[idx].get(flipped)


#    def get_width(self):
#        # Assuming all sprites have the same dimension
#        if self.raw_sprites:
#            return self.raw_sprites[0].get_width()
#    def get_height(self):
#        # Assuming all sprites have the same dimension
#        if self.raw_sprites:
#            return self.raw_sprites[0].get_height()
