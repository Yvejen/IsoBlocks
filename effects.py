import pygame as pg
from math import pi, acos
from pygame.math import Vector2 as Vec2

class TileAnimation(pg.sprite.Sprite):
    def __init__(self):
        super().__init__()

    def update(self, deltat=1/60):
        self.kill()

    def get_offset(self, tile) -> float:
        return 0

def smoothstep(le, re, x):
    clamp = lambda x: max(0, min(1, x))
    x = clamp((x - le) / (re - le))
    return x**2 * (3 - 2 * x)

def two_smoothstep(le, re, x):
    if x < 0:
        return smoothstep(le, 0, x)
    else:
        return 1 - smoothstep(0, re, x)

class DirectedShockwave(TileAnimation):
    def __init__(
        self,
        epicenter=(0, 0),
        speed=3,
        max_duration=4,
        trail=2,
        ahead: float =1,
        dampening=0.3,
        amplitude=1,
        width = pi/4,
        dir = Vec2(0,0)
    ):
        super().__init__()
        self.speed = speed
        self.center = Vec2(epicenter)
        self.time = 0
        self.max_duration = max_duration
        self.trail = trail
        self.ahead = ahead
        self.dampening = dampening
        self.amplitude = amplitude
        self.width = width
        self.dir = dir
    def update(self, deltat=1/60):
        self.time += deltat * self.speed
        self.amplitude = max(0, self.amplitude - self.dampening * deltat)
        if self.amplitude <= 1e-14:
            self.kill()

    def diff_angle(self, a: Vec2, b: Vec2):
        if a.length() <= 1e-13 or b.length() <= 1e-13:
            return 0.0
        return acos(a.dot(b)/(a.length()*b.length()))
    def get_offset(self, tile):
        t = Vec2(tile)
        d = (t - self.center).length()
        return -self.amplitude * two_smoothstep(-self.trail, self.ahead, d - self.time) * (1-smoothstep(0, self.width, self.diff_angle(self.dir, t-self.center)))

class CrossWaveAnimation(TileAnimation):
    def __init__(
        self,
        epicenter=(0, 0),
        speed=3,
        max_duration=4,
        trail=2,
        ahead: float =1,
        dampening=0.3,
        amplitude=1,
    ):
        super().__init__()
        self.speed = speed
        self.center = Vec2(epicenter)
        self.time = 0
        self.max_duration = max_duration
        self.trail = trail
        self.ahead = ahead
        self.dampening = dampening
        self.amplitude = amplitude

    def update(self, deltat=1/60):
        self.time += deltat * self.speed
        self.amplitude = max(0, self.amplitude - self.dampening * deltat)
        if self.amplitude <= 1e-14:
            self.kill()

    def is_on_cross(self, tile):
        return tile[0] - self.center[0] == 0 or tile[1] - self.center[1] == 0

    def get_offset(self, tile):
        t = Vec2(tile)
        d = (t - self.center).length()
        if self.is_on_cross(tile):
            return -self.amplitude * two_smoothstep(-self.trail, self.ahead, d - self.time)
        else:
            return 0.0

class CircularWaveAnimation(TileAnimation):
    def __init__(
        self,
        epicenter=(0, 0),
        speed=3,
        max_duration=4,
        trail: float =2,
        ahead: float =1,
        dampening=0.3,
        amplitude=1,
    ):
        super().__init__()
        self.speed = speed
        self.center = Vec2(epicenter)
        self.time = 0
        self.max_duration = max_duration
        self.trail = trail
        self.ahead = ahead
        self.dampening = dampening
        self.amplitude = amplitude

    def update(self, deltat=1/60):
        self.time += deltat * self.speed
        self.amplitude = max(0, self.amplitude - self.dampening * deltat)
        if self.amplitude <= 1e-14:
            self.kill()

    def get_offset(self, tile):
        t = Vec2(tile)
        d = (t - self.center).length()
        val = -self.amplitude * two_smoothstep(-self.trail, self.ahead, d - self.time)
        return val
