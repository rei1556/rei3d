"""
REI3D.PY

from-scratch 3d library for people who really like the GPU but also really like python for some reason
"""

import numpy
import moderngl
import pygame
import math
import colors as COLORS

GLOB_RESO = (640, 480)

pygame.init()
w = pygame.display.set_mode(GLOB_RESO, pygame.OPENGL | pygame.DOUBLEBUF)
ctx = moderngl.get_context()

class Mesh:
    def __init__(self, vertices, debugColor, ctx):
        self.vertices = vertices
        self.vertexBuffer = ctx.buffer(vertices.astype('f4').tobytes())
        self.position = numpy.array([0.0, 0.0, 0.0], dtype='f4')
        self.debugColor = debugColor

        with open('meshSetup.glsl', 'r') as f:
            shaderSrc = f.read()
        vertexSrc = "#version 330\n#define VERTEX_SHADER\n" + shaderSrc
        fragmentSrc = "#version 330\n#define FRAGMENT_SHADER\n" + shaderSrc
        self.program = ctx.program(vertex_shader=vertexSrc, fragment_shader=fragmentSrc)

        self.vao = ctx.vertex_array(self.program, [(self.vertexBuffer, '3f', 'position')])

    def draw(self, ctx):
        self.program['u_position'].value = tuple(self.position)
        self.program['u_color'].value = tuple(self.debugColor)
        self.vao.render()

class Camera:
    def __init__(self, position, rotation, clipPlanes:list, fov):
        self.position = numpy.array(position, dtype='f4')
        self.rotation = numpy.array(rotation, dtype='f4')
        self.clipPlanes = clipPlanes
        self.fov = fov
        self.projMatrix = numpy.identity(4, dtype='f4')
        self.viewMatrix = numpy.identity(4, dtype='f4')
    
    def updateMatrix(self):
        a = GLOB_RESO[0] / GLOB_RESO[1]
        n = self.clipPlanes[0]
        f = self.clipPlanes[1]
        theta = math.radians(self.fov)
        tanHalfTheta = math.tan(theta/2) # lol

        self.projMatrix = numpy.array([ # i'm going to be honest and say i have no fucking clue what this means. i just copied something from wikipedia
            [1/ (a * tanHalfTheta), 0,                    0,                0                 ],
            [0,                          1/ tanHalfTheta, 0,                0                 ],
            [0,                          0,               -((f+n) / (f-n)), -((2*f*n) / (f-n))],
            [0,                          0,               -1,               0                 ]
            ], dtype='f4')

        p, y, r = map(math.radians, self.rotation)

        rX = numpy.array([
            [1, 0,        0,               0],
            [0, math.cos(p), -math.sin(p), 0],
            [0, math.sin(p), math.cos(p),  0],
            [0, 0,        0,               1]
            ], dtype='f4')
        rY = numpy.array([
            [math.cos(y),  0, math.sin(y), 0],
            [0,            1, 0,           0],
            [-math.sin(y), 0, math.cos(y), 0],
            [0,            0, 0,           1]
            ], dtype='f4')
        rZ = numpy.array([
            [math.cos(r), -math.sin(r), 0, 0],
            [math.sin(r), math.cos(r),  0, 0],
            [0,           0,            1, 0],
            [0,           0,            0, 1]
            ], dtype='f4')

        rotMatrix = rY @ rX @ rZ # bullshit operator
        
        transMatrix = numpy.array([ # 🏳️‍⚧️
            [1, 0, 0, -self.position[0]],
            [0, 1, 0, -self.position[1]],
            [0, 0, 1, -self.position[2]],
            [0, 0, 0, 1                ],
            ])

        self.viewMatrix = rotMatrix.T @ transMatrix

triangle = Mesh(numpy.array([
    -0.5, -0.5, 0.0,
    0.5, -0.5, 0.0,
    0.0, 0.5, 0.0
], dtype='f4'), numpy.array(COLORS.BGWHITE + (COLORS.OPAQUE,), dtype='f4'), ctx)

running = True
clock = pygame.time.Clock()
while running:
    pygame.display.flip()
    dt = clock.tick()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    now = pygame.time.get_ticks() / 1000.0
    ctx.clear(0,0,0)