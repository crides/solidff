# monkey patching solidpython to be more pythonic
import solid
from solid.utils import *
import os
import math
from typing import Union, List, Tuple, Callable

__version__ = "0.1.0"

def subseteq(x, y):
    return (xset := set(x)) in y and list(xset) == list(x)

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
        fn = fn.replace(".py", "")
    if hasattr(root, "__call__"):
        root = root()
    with open(fn, "wb") as op:
        op.write(prefix.encode("utf-8"))
        op.write(solid.scad_render(root).encode("utf-8"))

def dump_this(root, prefix=""):
    import sys
    file = sys.argv[0]
    if file.endswith(".py"):
        file = file[:-2] + "scad"
    if hasattr(root, "__call__"):
        root = root()
    with open(file, "wb") as op:
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

def patches(l: List[Tuple[List[str], Callable]]):
    for names, val in l:
        for s in names:
            setattr(solid.OpenSCADObject, s, val)

patches([
    (["d", "debug"], lambda self: solid.debug(self)),
    (["b", "background"], lambda self: solid.background(self)),
    (["h", "hole"], lambda self: solid.hole()(self)),
    (["t", "translate"], ff_translate),
    (["r", "rotate"], ff_rotate),
    (["s", "scale"], lambda self, x=1, y=1, z=1: solid.scale([x, y, z])(self)),
    (["o", "offset"], ff_offset),
    (["__pow__"], lambda x, y: hull(x, y)),
    (["__xor__"], lambda x, y: x + y.h()),

    (["rx"], lambda self, x: solid.rotate((x, 0, 0))(self)),
    (["ry"], lambda self, y: solid.rotate((0, y, 0))(self)),
    (["rz"], lambda self, z: solid.rotate((0, 0, z))(self)),

    (["rzx"], solid.utils.rot_z_to_x),
    (["rzy"], solid.utils.rot_z_to_y),
    (["rxy"], solid.utils.rot_x_to_y),
    (["rxz"], solid.utils.rot_z_to_neg_x),
    (["ryx"], solid.utils.rot_x_to_neg_y),
    (["ryz"], solid.utils.rot_z_to_neg_y),

    (["x", "right"], lambda self, d: solid.utils.right(d)(self)),
    (["left"], lambda self, d: solid.utils.left(d)(self)),  # along y
    (["y", "forward"], lambda self, d: solid.utils.forward(d)(self)),  # along x
    (["back"], lambda self, d: solid.utils.back(d)(self)),
    (["z", "up"], lambda self, d: solid.utils.up(d)(self)),  # along z
    (["down"], lambda self, d: solid.utils.down(d)(self)),
    (["c", "color"], lambda self, c: solid.color(c)(self)),
    (["m", "mirror"], lambda self, a, b, c: solid.mirror([a, b, c])(self)),

    (["e", "extrude", "linear_extrude"], ff_linear_extrude),
    (["render"], lambda self, **kw: solid.render(**kw)(self)),

    (["dump"], dump),
    (["dump_this"], dump_this),
])

poly = solid.polygon
hull = lambda *args: solid.hull()(*args)

def center_obj(obj, center: Union[bool, str, None] = None, x=None, y=None, z=None):
    if type(center) == bool:
        return obj(center)
    obj = obj(None)
    if center == None:
        return obj
    center = set(center)
    if 'x' in center:
        obj = obj.x(-x/2)
    if 'y' in center:
        obj = obj.y(-y/2)
    if 'z' in center:
        obj = obj.z(-z/2)
    return obj

def c(d=None, r=None, segments=60):
    return solid.circle(d=d, r=r, segments=segments)

def s(x, y=None, center: Union[bool, str, None] = None):
    if center == None:
        if type(y) in [int, float]:
            return solid.square([x, y])
        obj = lambda c:solid.square(x, center=c)
        return center_obj(obj, y, x, x)
    if y == None:
        obj = lambda c:solid.square(x, center=c)
        return center_obj(obj, center, x, x)
    obj = lambda c:solid.square([x, y], center=c)
    return center_obj(obj, center, x, y)

def cy(d=None, h=2, center=False, axis="z", segments=60, **kw):
    _check_axis(axis)
    cylinder = solid.cylinder(d=d, h=h, center=center, segments=segments, **kw)
    if axis == "z":   return cylinder
    elif axis == "y": return cylinder.rzy()
    elif axis == "x": return cylinder.rzx()

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
    elif o == None:
        o = i + w
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

def q(x, y=None, z=None, center: Union[bool, str, None] = None):
    """A quick cube"""
    if y is None:
        y = x
    if z is None:
        z = x
    obj = lambda c:solid.cube([x, y, z], center=c)
    return center_obj(obj, center, x, y, z)

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
            [0, 0],
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

b = lambda d=None, r=None, segments=60: solid.sphere(d=d, r=r, segments=segments)
