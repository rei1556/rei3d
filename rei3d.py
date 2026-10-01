"""
REI3D.PY

from-scratch 3d library for people who really like the GPU but also really like python for some reason
"""

import numpy
import moderngl
import pygame
import math
import colors as COLORS
from PIL import Image

GLOB_RESO = (640, 480)

pygame.init()
w = pygame.display.set_mode(GLOB_RESO, pygame.OPENGL | pygame.DOUBLEBUF)
ctx = moderngl.get_context()
ctx.enable(moderngl.DEPTH_TEST)

class Mesh:
    def __init__(self, vertices, position, rotation, debugColor, ctx):
        self.vertices = vertices
        self.vertexBuffer = ctx.buffer(vertices.astype('f4').tobytes())
        self.position = numpy.array(position, dtype='f4')
        self.rotation = numpy.array(rotation, dtype='f4')
        self.debugColor = debugColor

        with open('meshSetup.glsl', 'r') as f:
            shaderSrc = f.read()
        vertexSrc = "#version 330\n#define VERTEX_SHADER\n" + shaderSrc
        fragmentSrc = "#version 330\n#define FRAGMENT_SHADER\n" + shaderSrc
        self.program = ctx.program(vertex_shader=vertexSrc, fragment_shader=fragmentSrc)

        self.vao = ctx.vertex_array(self.program, [(self.vertexBuffer, '3f', 'position')])


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
            [1/ (a * tanHalfTheta),      0,               0,                0                 ],
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

    def render(self, mesh):
        modelTransMatrix = numpy.identity(4, dtype='f4')
        modelTransMatrix[0, 3] = mesh.position[0]
        modelTransMatrix[1, 3] = mesh.position[1]
        modelTransMatrix[2, 3] = mesh.position[2]

        p, y, r = map(math.radians, mesh.rotation)

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

        modelRotMatrix = rY @ rX @ rZ

        modelMatrix = modelTransMatrix @ modelRotMatrix

        mvp = self.projMatrix @ self.viewMatrix @ modelMatrix

        mesh.program['u_mvp'].write(mvp.T.astype('f4').tobytes())
        mesh.program['u_color'].value = tuple(mesh.debugColor)
        mesh.vao.render()


triangle = Mesh(numpy.array([
    -0.5, -0.5, 0.0,
    0.5, -0.5, 0.0,
    0.0, 0.5, 0.0,
    -0.5, -0.5, -1.0,
    0.5, -0.5, -1.0,
    0.0,  0.5, -1.0,

], dtype='f4'), 
                [0, 0, 0],
                [0, 0, 0],
                numpy.array(COLORS.BGWHITE + (COLORS.OPAQUE,), dtype='f4'), ctx)

cam = Camera(
    [0, 0, 2],
    [0, 0, 0],
    (0.01, 128),
    90
    )

running = True
clock = pygame.time.Clock()
spin = 0
while running:
    pygame.display.flip()
    dt = clock.tick()
    cam.updateMatrix()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    now = pygame.time.get_ticks() / 1000.0

    triangle.rotation[1] += 0.2 * dt

    ctx.clear(0,0,0,1,depth=1.0)

    cam.render(triangle)