import os
import pygame as pg

class SpriteCatalogue:
    def __init__(self):
        self.scale = 1.0
        self.orig_sprites = []
        self.scaled_sprites = []
        self.flipped_sprites = []

    def add_sprites(self, dir, ran, pattern="sprite{}", ext="png"):
        for i in ran:
            filename = os.path.join(dir, pattern.format(i) + "." + ext)
            self.orig_sprites.append(self.load_image(filename))
        self.scale_catalogue()

    def scale_catalogue(self, scale=1.0):
        self.scale = scale
        self.scaled_sprites = []
        self.flipped_sprites = []
        for s in self.orig_sprites:
            scaled = self.scale_uniform(s, scale)
            self.scaled_sprites.append(scaled)
            self.flipped_sprites.append(pg.transform.flip(scaled, flip_x=1, flip_y=0))

    @staticmethod
    def load_image(file):
        try:
            image = pg.image.load(file).convert_alpha()
        except FileNotFoundError:
            print(f"Could not load resource from file {file}")
            errsurf = pg.Surface((20, 20))
            errsurf.fill("purple")
            image = errsurf
        return image

    @staticmethod
    def scale_uniform(img, factor=1.0):
        width, height = img.get_width(), img.get_height()
        simg = pg.transform.scale(img, (width * factor, height * factor))
        return simg

    def __getitem__(self, idx):
        return self.get(idx)

    def get(self, idx, flipped=False):
        if flipped:
            return self.flipped_sprites[idx]
        else:
            return self.scaled_sprites[idx]
