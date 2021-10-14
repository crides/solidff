# monkey patching solidpython to be more pythonic
import solid
from solid.utils import *
import os
import math

__version__ = "0.1.0"

def ff_translate(self, x, y, z=0):
    return solid.translate([x, y, z])(self)

def ff_rotate(self, x, y=None, z=None, v=None):
    if y == None and z == None:
        return solid.rotate(x)(self)
    if v is None:
        return solid.rotate((x, y, z))(self)
    return solid.rotate(a=[x, y, z], v=v)(self)

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

def ff_linear_extrude(obj, height, axis="z", center=False, **kwargs):
    """Note that center only centers the 'axis', not your 2d object"""
    _check_axis(axis)
    o = solid.linear_extrude(height, **kwargs)(obj)
    if center:
        o = o.down(height / 2)
    if axis == "y":
        return o.rotate(90, 0, 0)
    elif axis == "x":
        return o.rotate(0, 90, 0)
    return o

def ff_offset(self, r=None, delta=None, chamfer=False, segments=60):
    return solid.offset(r=r, delta=delta, chamfer=chamfer, segments=segments)(self)

solid.OpenSCADObject.d = solid.OpenSCADObject.debug = lambda self: solid.debug(self)
solid.OpenSCADObject.b = solid.OpenSCADObject.background = lambda self: solid.background(self)
solid.OpenSCADObject.h = solid.OpenSCADObject.hole = lambda self: solid.hole()(self)
solid.OpenSCADObject.t = solid.OpenSCADObject.translate = ff_translate
solid.OpenSCADObject.r = solid.OpenSCADObject.rotate = ff_rotate
solid.OpenSCADObject.s = solid.OpenSCADObject.scale = lambda self, x=1, y=1, z=1: solid.scale([x, y, z])(self)
solid.OpenSCADObject.o = solid.OpenSCADObject.offset = ff_offset

solid.OpenSCADObject.rzx = lambda self: solid.utils.rot_z_to_x(self)
solid.OpenSCADObject.rzy = lambda self: solid.utils.rot_z_to_y(self)
solid.OpenSCADObject.rxy = lambda self: solid.utils.rot_x_to_y(self)
solid.OpenSCADObject.rxz = lambda self: solid.utils.rot_z_to_x(self)
solid.OpenSCADObject.ryx = lambda self: solid.utils.rot_x_to_y(self)
solid.OpenSCADObject.ryz = lambda self: solid.utils.rot_z_to_y(self)

solid.OpenSCADObject.x = solid.OpenSCADObject.right = lambda self, d: solid.utils.right(d)(self)
solid.OpenSCADObject.left = lambda self, d: solid.utils.left(d)(self)  # along y
solid.OpenSCADObject.y = solid.OpenSCADObject.forward = lambda self, d: solid.utils.forward(d)(self)  # along x
solid.OpenSCADObject.back = lambda self, d: solid.utils.back(d)(self)
solid.OpenSCADObject.z = solid.OpenSCADObject.up = lambda self, d: solid.utils.up(d)(self)  # along z
solid.OpenSCADObject.down = lambda self, d: solid.utils.down(d)(self)
solid.OpenSCADObject.c = solid.OpenSCADObject.color = lambda self, c: solid.color(c)(self)
solid.OpenSCADObject.m = solid.OpenSCADObject.mirror = lambda self, a, b, c: solid.mirror([a, b, c])(self)

solid.OpenSCADObject.e = solid.OpenSCADObject.extrude = solid.OpenSCADObject.linear_extrude = ff_linear_extrude

solid.OpenSCADObject.dump = dump

poly = solid.polygon
hull = lambda *args: solid.hull()(*args)

def c(r=None, d=None, segments=60):
    if r == None and d == None:
        raise ValueError("One of `r` and `d` must be specified")
    if r != None:
        return solid.circle(r=r, segments=segments)
    return solid.circle(d=d, segments=segments)

def s(x, y=None, center=None):
    if center == None:
        if type(y) in [int, float]:
            return solid.square([x, y])
        return solid.square(x, center=y)
    if y == None:
        return solid.square(x, center)
    return solid.square([x, y], center)

def cy(d=None, h=2, center=False, d1=None, d2=None, r=None, r1=None, r2=None, axis="z", segments=60):
    _check_axis(axis)
    if (r1 == None) == (r2 == None) and (d1 == None) == (d2 == None) and sum(int(a != None) for a in [r, r1, d, d1]) == 1:
        pass
    else:
        raise ValueError("Specify one and only one of `r`, `d`, both `r1` and `r2`, and both `d1` and `d2`")
    cylinder = solid.cylinder(r=r, r1=r1, r2=r2, d=d, d1=d1, d2=d2, h=h, center=center, segments=segments)
    if axis == "z":
        return cylinder
    elif axis == "y":
        return cylinder.rotate(90, 0, 0)
    elif axis == "x":
        return cylinder.rotate(0, 90, 0)

def sector(radius=20, angles=(45, 135)):
    rect = solid.square([radius * 2, radius]).left(radius)
    return solid.difference()(
        solid.circle(20),
        rect.rotate(angles[0]),
        rect.rotate(angles[1]).mirror(math.cos(math.radians(angles[1])), math.sin(math.radians(angles[1])), 0),
    )

def arc(radius=20, angles=(45, 290), width=1):
    return solid.difference()(
        sector(radius + width, angles),
        sector(radius, angles),
    )

# def ring(o=None, i=None, w=None, od=None, id=None, h=2, hole=False, segments=60):
#     if i != None and id != None:
#         raise ValueError("Use only one of `i` and `id`")
#     if o != None and od != None:
#         raise ValueError("Use only one of `o` and `od`")
#     if sum(int(a != None) for a in [o, i, w, od, id]) != 2:
#         raise ValueError("Specify only 2 of `o`, `i`, `od`, `id`, and `w`")
#     if o == None and od != None:
#         o = od / 2
#     if i == None and id != None:
#         i = id / 2
#     if o == None:
#         o = i + w
#     elif i == None:
#         i = o - w
#     if hole:
#         return cy(r=o, h=h, segments=segments) + cy(r=o, h=h, segments=segments).h()
#     return cy(o, h, segments=segments) - cy(i, h, segments=segments)

def ring(od=None, id=None, h=2, center=False, w=None, o=None, i=None, hole=False, extra=True, segments=60):
    if i != None and id != None:
        raise ValueError("Use only one of `i` and `id`")
    if o != None and od != None:
        raise ValueError("Use only one of `o` and `od`")
    if sum(int(a != None) for a in [o, i, w, od, id]) != 2:
        raise ValueError("Specify only 2 of `o`, `i`, `od`, `id`, and `w`")
    if o == None and od != None:
        o = od / 2
    if i == None and id != None:
        i = id / 2
    if w == None:
        w = o - i
    elif i == None:
        i = o - w
    if hole:
        if extra:
            inner = cy(r=i, h=h + 0.01, segments=segments).z(-0.005)
        else:
            inner = cy(r=i, h=h, segments=segments)
        ring = cy(r=o, h=h, segments=segments) + inner.h()
    else:
        ring = solid.rotate_extrude(segments=segments)(solid.square([w, h]).x(i))
    if center:
        return ring.z(-h / 2)
    return ring

def q(x, y=None, z=None, center=False):
    """A quick cube"""
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


def rq(x, y=None, z=None, r=1, center=False, axis="z", edges=(0, 1, 2, 3)):
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

def triangle90(a, b, height=1, axis="z", center=False):
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
        if center or "z" in center:
            p = p.down(height / 2)
        if center or "x" in center:
            p = p.left(c[0])
        if center or "y" in center:
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

b = lambda d=None, r=None, seg=None: solid.sphere(d=d, r=r, segments=seg)
