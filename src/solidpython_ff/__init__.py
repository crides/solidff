# monkey patching solidpython to be more pythonic
import solid
from solid.utils import *
import os
import json
import math


__version__ = "0.1.0"

def ff_translate(x, y=0, z=0):
    if isinstance(x, (list, tuple)):
        return solid.translate(x)
    else:
        return solid.translate([x, y, z])


def ff_rotate(a=None, b=None, c=None):
    if a is None and b is None and c is None:
        return solid.rotate(0, 0, 0)
    if (
        isinstance(a, (float, int))
        and isinstance(b, (float, int))
        and isinstance(c, (float, int))
    ):
        return solid.rotate([a, b, c])
    else:
        return solid.rotate(a=a, v=b)


def ff_scale(x=1, y=1, z=1):
    if isinstance(x, (list, tuple)):
        return solid.scale(x)
    else:
        return solid.scale([x, y, z])


def dump(root, fn, prefix=""):
    if fn.endswith(".py"):
        fn = __file__.replace(".py", "")
    if hasattr(root, "__call__"):
        root = root()
    with open(fn, "wb") as op:
        op.write(prefix.encode("utf-8"))
        op.write(solid.scad_render(root).encode("utf-8"))


def _check_axis(axis):
    if not axis in ("x", "y", "z"):
        raise ValueError("invalid axis")


def ff_linear_extrude(
    obj, height, axis="z", center=True, **kwargs
):
    """Note that center only centers the 'axis', not your 2d object"""
    _check_axis(axis)
    o = solid.linear_extrude(height, **kwargs)(obj)
    if center:
        o = o.down(height / 2)
    if axis == "y":
        o = o.rotate(90, 0, 0)
    elif axis == "x":
        o = o.rotate(0, 90, 0)
    return o


solid.OpenSCADObject.d = lambda self: solid.debug((self))
solid.OpenSCADObject.debug = solid.OpenSCADObject.d
solid.OpenSCADObject.b = lambda self: solid.background((self))
solid.OpenSCADObject.background = solid.OpenSCADObject.b
solid.OpenSCADObject.h = lambda self: solid.hole()(self)
solid.OpenSCADObject.hole = solid.OpenSCADObject.h
solid.OpenSCADObject.t = lambda self, x=0, y=0, z=0: ff_translate(x, y, z)(self)
solid.OpenSCADObject.translate = solid.OpenSCADObject.t
solid.OpenSCADObject.r = lambda self, a=None, b=None, c=None: ff_rotate(a, b, c)(self)

solid.OpenSCADObject.rzx = lambda self : solid.utils.rot_z_to_x(self)
solid.OpenSCADObject.rzy = lambda self : solid.utils.rot_z_to_y(self)

solid.OpenSCADObject.rxy = lambda self : solid.utils.rot_x_to_y(self)
solid.OpenSCADObject.rxz = lambda self : solid.utils.rot_z_to_x(self)

solid.OpenSCADObject.ryx = lambda self : solid.utils.rot_x_to_y(self)
solid.OpenSCADObject.ryz = lambda self : solid.utils.rot_z_to_y(self)


solid.OpenSCADObject.rotate = solid.OpenSCADObject.r
solid.OpenSCADObject.s = lambda self, x=1, y=1, z=1: ff_scale(
    x,
    y,
    z,
)(self)
solid.OpenSCADObject.scale = solid.OpenSCADObject.s

solid.OpenSCADObject.up = lambda self, d: solid.utils.up(d)(self)  # along z
solid.OpenSCADObject.down = lambda self, d: solid.utils.down(d)(self)
solid.OpenSCADObject.left = lambda self, d: solid.utils.left(d)(self)  # along y
solid.OpenSCADObject.right = lambda self, d: solid.utils.right(d)(self)
solid.OpenSCADObject.forward = lambda self, d: solid.utils.forward(d)(self)  # along x
solid.OpenSCADObject.back = lambda self, d: solid.utils.back(d)(self)
solid.OpenSCADObject.c = lambda self, c: solid.color(c)(self)
solid.OpenSCADObject.color = solid.OpenSCADObject.c
solid.OpenSCADObject.m = lambda self, a, b, c: solid.mirror([a, b, c])(self)
solid.OpenSCADObject.mirror = solid.OpenSCADObject.m

solid.OpenSCADObject.x = lambda self, d: solid.right(d)(self)  # along z
solid.OpenSCADObject.y = lambda self, d: solid.forward(d)(self)  # along y
solid.OpenSCADObject.z = lambda self, d: solid.up(d)(self)  # along z

solid.OpenSCADObject.e = lambda self, height, axis="z", center=True, **kwargs: ff_linear_extrude(
    self, height, axis, **kwargs
)
solid.OpenSCADObject.extrude = solid.OpenSCADObject.e
solid.OpenSCADObject.linear_extrude = solid.OpenSCADObject.e

solid.OpenSCADObject.dump = lambda self, fn, prefix="": dump(self, fn, prefix)


def cy(
    r=None, h=None, center=True, zo="ignored", r1=None, r2=None, segments=64, axis="z"
):
    _check_axis(axis)
    if axis == "z":
        return solid.cylinder(r, h, center=center, segments=segments, r1=r1, r2=r2)
    elif axis == "y":
        return solid.cylinder(
            r, h, center=center, segments=segments, r1=r1, r2=r2
        ).rotate(90, 0, 0)
    elif axis == "x":
        return solid.cylinder(
            r, h, center=center, segments=segments, r1=r1, r2=r2
        ).rotate(0, 90, 0)


degree_to_radians = 0.0174533


def sector(radius=20, angles=(45, 135), segments=24):
    r = radius / math.cos(180 * degree_to_radians / segments)
    step = int(-360 / segments)

    points = [[0, 0]]
    for a in range(int(angles[0]), int(angles[1] - 360), step):
        points.append(
            [r * math.cos(a * degree_to_radians), r * math.sin(a * degree_to_radians)]
        )
    for a in range(int(angles[0]), int(angles[1] - 360), step):
        points.append(
            [
                r * math.cos(angles[1] * degree_to_radians),
                r * math.sin(angles[1] * degree_to_radians),
            ]
        )

    return solid.difference()(
        solid.circle(radius, segments=segments),
        solid.polygon(points),
    )


def arc(radius=20, angles=(45, 290), width=1, segments=24):
    return solid.difference()(
        sector(radius + width, angles, segments),
        sector(radius, angles, segments),
    )


def ring(r1, r2=None, width=None, h=2, *cy_args, **cy_kwargs):
    if width is None and r2 is None:
        width = 1
    if width and r2:
        raise ValueError("Specify either width or r2")
    if width:
        r2 = r1 - width

    return cy(r1, h, *cy_args, **cy_kwargs) - cy(r2, h + 0.1, *cy_args, **cy_kwargs)


def q(x, y=None, z=None, center=True):
    """A quick cube"""
    if isinstance(x, (tuple, list)):
        return solid.cube(x, center=center)
    else:
        if y is None:
            y = x
        if z is None:
            z = x
        return solid.cube([x, y, z], center=center)


def _inner_rq(x, y, z, r, center, edges):
    xr = x / 2 - r
    yr = y / 2 - r
    a = solid.hull()(
        (
            (cy(r, z) if 0 in edges else q(2 * r, 2 * r, z)).left(xr).forward(yr),
            (cy(r, z) if 1 in edges else q(2 * r, 2 * r, z)).left(-xr).forward(yr),
            (cy(r, z) if 2 in edges else q(2 * r, 2 * r, z)).left(xr).forward(-yr),
            (cy(r, z) if 3 in edges else q(2 * r, 2 * r, z)).left(-xr).forward(-yr),
        )
    )
    if not center:
        a = a.right(x / 2).back(y / 2).up(z / 2)
    return a


def rq(x, y=None, z=None, r=1, center=True, axis="z", edges=(0, 1, 2, 3)):
    """A rounded cube with four edges rounded by radius r.
    Use axis='x','y','z' and edges (0,1,2,3) to change
    which edges get rounded"""
    if center not in (True, False):
        raise ValueError("center must be bool")
    if isinstance(x, (tuple, list)):
        x, y, z = x
    else:
        if y is None:
            y = x
        if z is None:
            z = x
    if axis == "z":
        return _inner_rq(x, y, z, r, center, edges)
    elif axis == "y":
        return _inner_rq(z, x, y, r, center, edges).rotate(0, 90, 90)
    elif axis == "x":
        return _inner_rq(y, z, x, r, center, edges).rotate(90, 0, 90)
    else:
        raise ValueError("axis must be x,y,z")


def triangle90(a, b, height=1, axis="z", center=True):
    """A quick 90 degree triangle with sidelengths a,b, extruded to height"""
    p = solid.polygon(
        [
            [
                0,
                0,
            ],
            [a, 0],
            [a, b],
        ]
    ).e(height)
    if center:
        c = ((0 + a + a) / 3, (0 + 0 + b) / 3)
        if center is True or "z" in center:
            p = p.down(height / 2)
        if center is True or "x" in center:
            p = p.left(c[0])
        if center is True or "y" in center:
            p = p.back(c[1])
    if axis == "x":
        p = p.rotate(90, 0, 0)
    elif axis == "y":
        p = p.rotate(
            0,
            90,
            0,
        )
    elif axis == "z":
        pass
    else:
        raise ValueError("invalid axis")
    return p
