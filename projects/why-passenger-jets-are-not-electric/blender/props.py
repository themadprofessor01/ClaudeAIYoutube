"""props — environments and props for the film (built on jetlib)."""
import math
import bpy, bmesh
import numpy as np
from mathutils import Vector, Euler
from jetlib import (mat, emissive, obj_from_mesh, empty, lathe, lofted_surface, airfoil, nacelle,
                    image_from_array, textured_mat, xray_mat, TAU)

AMBER = (1.0, 0.42, 0.04)
CYAN = (0.04, 0.55, 1.0)


def box(name, size, loc, material, parent=None, bevel=0.0, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = size
    if bevel:
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        md = o.modifiers.new("bev", "BEVEL")
        md.width = bevel
        md.segments = 3
        md.limit_method = "ANGLE"
        o.data.shade_smooth_by_angle() if hasattr(o.data, "shade_smooth_by_angle") else None
    o.data.materials.append(material)
    if parent:
        o.parent = parent
    return o


def cyl(name, r, h, loc, material, rot=(0, 0, 0), verts=64, parent=None, smooth=True):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, rotation=rot, vertices=verts)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(material)
    if smooth:
        bpy.ops.object.shade_smooth()
    if parent:
        o.parent = parent
    return o


def sphere(name, r, loc, material, scale=(1, 1, 1), parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=48, ring_count=24)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    o.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    if parent:
        o.parent = parent
    return o


# ----------------------------------------------------------------- small aircraft family
def small_plane(name="ev", kind="trainer", xray=False, livery=(0.9, 0.91, 0.92), accent=(0.1, 0.45, 0.75)):
    """Parametric small aircraft. kind: trainer | seaplane | racer | solar | meridian.
    Nose at x=0 pointing −X, +Z up. Returns root empty with ['ground_offset']."""
    root = empty(name)
    paint = mat(f"{name}_paint", livery, 0.28, coat=0.6) if not xray else xray_mat()
    acc = mat(f"{name}_accent", accent, 0.3, coat=0.5) if not xray else paint
    glass = mat("canopy", (0.02, 0.03, 0.04), 0.03, coat=1.0)
    prop_m = mat("prop", (0.05, 0.05, 0.055), 0.4)
    P = dict(trainer=dict(L=6.5, R=0.55, span=10.7, rc=1.2, tc=0.85, wing_z=-0.35, wx=1.9, high=False),
             seaplane=dict(L=9.2, R=0.75, span=14.6, rc=1.6, tc=1.6, wing_z=0.75, wx=2.2, high=True),
             racer=dict(L=7.3, R=0.5, span=7.5, rc=1.3, tc=0.7, wing_z=-0.3, wx=2.2, high=False),
             solar=dict(L=21.0, R=0.6, span=72.0, rc=3.3, tc=2.6, wing_z=1.6, wx=5.5, high=True),
             meridian=dict(L=19.0, R=1.25, span=29.0, rc=2.2, tc=1.3, wing_z=1.25, wx=6.6, high=True))[kind]
    L, R = P["L"], P["R"]
    # fuselage (lathe-ish via loft of circles)
    prof = []
    n = 40
    for i in range(n + 1):
        f = i / n
        x = f * L
        if kind == "solar":
            r = R * (math.sin(min(1, f / 0.25) * math.pi / 2) if f < 0.25 else max(0.08, 1 - (f - 0.25) / 0.75 * 0.85))
        elif kind == "meridian":
            r = R * ((1 - (1 - min(1, f / 0.16)) ** 2.2) ** 0.5 if f < 0.16 else (1 if f < 0.7 else 1 - (f - 0.7) / 0.3 * 0.8))
        else:
            r = R * ((1 - (1 - min(1, f / 0.22)) ** 2) ** 0.5 if f < 0.22 else 1 - (f - 0.22) / 0.78 * 0.82)
        prof.append((x, max(r, 0.03)))
    fus = lathe(f"{name}_fus", prof, paint, 48, root)
    fus.scale = (1, 1, 1.12 if kind != "solar" else 1.0)
    # canopy
    if kind in ("trainer", "racer"):
        c = sphere(f"{name}_canopy", 1, (L * 0.3, 0, R * 0.62), glass, (L * 0.14, R * 0.62, R * 0.55), root)
    elif kind in ("seaplane", "meridian"):
        sphere(f"{name}_wind", 1, (L * 0.12, 0, R * 0.35), glass, (L * 0.05, R * 0.85, R * 0.45), root)
    else:
        sphere(f"{name}_pod", 1, (L * 0.12, 0, -R * 0.1), glass, (1.0, 0.45, 0.5), root)
    # wings
    for sgn in (1, -1):
        secs = []
        for k in range(7):
            f = k / 6
            yy = sgn * (R * 0.6 + f * (P["span"] / 2 - R * 0.6))
            chord = P["rc"] + (P["tc"] - P["rc"]) * f
            sweep = 2.0 if kind != "racer" else 6.0
            secs.append((Vector((P["wx"] + abs(yy) * math.tan(math.radians(sweep)), yy,
                                 P["wing_z"] + abs(yy) * math.tan(math.radians(4 if kind != "solar" else 2)))),
                         chord, 0.13 if kind != "solar" else 0.1, 0, False))
        lofted_surface(f"{name}_w{sgn}", secs, paint, root)
        # tailplane
        hs = [(Vector((L * 0.82, sgn * 0.1, R * 0.15 if kind != "meridian" else R * 0.2 + 2.6)), P["rc"] * 0.6, 0.1, 0, False),
              (Vector((L * 0.86, sgn * (P["span"] * (0.17 if kind != "solar" else 0.08)), R * 0.15 if kind != "meridian" else R * 0.2 + 2.6)), P["rc"] * 0.38, 0.09, 0, False)]
        lofted_surface(f"{name}_h{sgn}", hs, acc, root)
    fh = {"trainer": 1.1, "seaplane": 1.5, "racer": 1.0, "solar": 2.4, "meridian": 2.7}[kind]
    fs = [(Vector((L * 0.8, 0, R * 0.4)), P["rc"] * 0.8, 0.1, 0, True), (Vector((L * 0.8 + fh * 0.7, 0, R * 0.4 + fh)), P["rc"] * 0.42, 0.09, 0, True)]
    lofted_surface(f"{name}_fin", fs, acc, root)
    # propulsion
    def prop(loc, rad, blades=3, parent=root, axis_x=True):
        hub = sphere(f"{name}_spin", 1, loc, mat("spinner_w", (0.85, 0.86, 0.87), 0.25, coat=0.6), (rad * 0.28, rad * 0.16, rad * 0.16), parent)
        for b in range(blades):
            a = TAU * b / blades
            bl = box(f"{name}_pb", (0.06, 0.03, rad), (loc[0] + 0.05, loc[1] + math.sin(a) * rad / 2, loc[2] + math.cos(a) * rad / 2), prop_m, parent,
                     rot=(-a, math.radians(12), 0))
    if kind in ("trainer", "racer", "seaplane"):
        prop((-0.15, 0, 0), {"trainer": 0.8, "racer": 0.75, "seaplane": 1.25}[kind], 3 if kind != "racer" else 3)
    elif kind == "solar":
        for yy in (-22, -11, 11, 22):
            x0 = P["wx"] - 0.6
            z0 = P["wing_z"] + abs(yy) * math.tan(math.radians(2)) - 0.45
            sphere(f"{name}_pod{yy}", 1, (x0 + 0.6, yy, z0), paint, (1.0, 0.22, 0.22), root)
            prop((x0 - 0.45, yy, z0), 1.1, 2)
    elif kind == "meridian":
        for yy in (-12.0, -8.0, -4.0, 4.0, 8.0, 12.0):
            x0 = P["wx"] - 0.9
            z0 = P["wing_z"] + abs(yy) * math.tan(math.radians(4)) - 0.25
            sphere(f"{name}_pod{yy}", 1, (x0 + 0.55, yy, z0), acc, (1.0, 0.24, 0.24), root)
            prop((x0 - 0.5, yy, z0), 0.95, 5)
        # cabin windows strip
        wm = mat("mer_win", (0.015, 0.02, 0.03), 0.04, coat=1.0)
        for side in (1, -1):
            for k in range(9):
                sphere(f"{name}_win", 1, (3.6 + k * 1.05, side * R * 0.985, 0.25), wm, (0.18, 0.02, 0.22), root)
    # gear / floats
    g_off = 0
    if kind == "seaplane":
        fm = mat("float", (0.85, 0.86, 0.87), 0.3, coat=0.5)
        for sgn in (1, -1):
            f = lathe(f"{name}_float{sgn}", [(0, 0.02), (0.8, 0.28), (2.0, 0.36), (6.0, 0.3), (7.6, 0.06)], fm, 32, root)
            f.location = (-0.5, sgn * 1.4, -R - 1.3)
            box(f"{name}_strut", (0.05, 0.05, 1.0), (2.0, sgn * 1.0, -R - 0.7), fm, root, rot=(sgn * 0.4, 0, 0))
        g_off = R + 1.3 + 0.3
    elif kind in ("trainer", "meridian"):
        tire = mat("tire", (0.015, 0.015, 0.016), 0.75)
        gz = -R - (0.55 if kind == "trainer" else 0.9)
        for (x, y) in ((0.6 if kind == "trainer" else 2.0, 0), (P["wx"] + 0.8, 0.9 if kind == "trainer" else 2.0), (P["wx"] + 0.8, -(0.9 if kind == "trainer" else 2.0))):
            bpy.ops.mesh.primitive_torus_add(major_radius=0.17 if kind == "trainer" else 0.3, minor_radius=0.08 if kind == "trainer" else 0.14,
                                             location=(x, y, gz), rotation=(math.pi / 2, 0, 0))
            t = bpy.context.object
            t.data.materials.append(tire)
            t.parent = root
            box(f"{name}_leg", (0.05, 0.05, abs(gz) - R * 0.5), (x, y, (gz - R * 0.5) / 2), mat("strut", (0.75, 0.76, 0.78), 0.2, metal=1), root)
        g_off = -gz + (0.25 if kind == "trainer" else 0.44)
    if kind == "solar":
        # solar-cell texture on the wing top: dark blue glossy overlay strip
        sm = mat("solar_cells", (0.02, 0.04, 0.1), 0.12, metal=0.3, coat=1.0)
        box(f"{name}_cells", (P["rc"] * 0.8, P["span"] * 0.96, 0.01), (P["wx"] + P["rc"] * 0.45, 0, P["wing_z"] + 0.21), sm, root)
    root["ground_offset"] = g_off
    root["length"] = L
    root["span"] = P["span"]
    return root


# ----------------------------------------------------------------- engine cutaway
def engine_cutaway(name="eng", open_frac=1.0, glow=True, scale=1.0):
    """Turbofan on display: half the nacelle removed (open_frac=1) to reveal fan, compressor,
    combustor (glowing amber ring), turbines and nozzle. Axis along +X, inlet at x=0."""
    root = empty(name)
    s = scale
    paint = mat("eng_paint", (0.82, 0.83, 0.85), 0.3, coat=0.6)
    inner = mat("eng_inner", (0.5, 0.51, 0.53), 0.35, metal=1.0)
    ti = mat("titanium", (0.55, 0.53, 0.5), 0.28, metal=1.0)
    dark = mat("eng_dark", (0.05, 0.05, 0.055), 0.5, metal=0.5)
    blade_m = mat("fan_blade", (0.2, 0.21, 0.23), 0.22, metal=1.0)
    hot = mat("hot_metal", (0.18, 0.14, 0.12), 0.4, metal=1.0)
    # half cowl via bmesh bisect
    outer = [(0, 1.02), (0.06, 1.10), (0.25, 1.17), (0.8, 1.21), (2.2, 1.18), (3.3, 1.02), (3.9, 0.86)]
    cowl = lathe(name + "_cowl", [(x * s, r * s) for x, r in outer], paint, 96, root)
    cowl_in = lathe(name + "_cowlin", [(x * s, r * s * 0.97) for x, r in outer[::-1]], inner, 96, root)
    for o in (cowl, cowl_in):
        if open_frac > 0:
            bm = bmesh.new()
            bm.from_mesh(o.data)
            bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(0, 1, 0), clear_inner=True)
            bm.to_mesh(o.data)
            bm.free()
    # core casing (cut too)
    core_prof = [(1.1, 0.62), (1.6, 0.58), (2.4, 0.5), (3.0, 0.48), (3.8, 0.5), (4.3, 0.55)]
    cc = lathe(name + "_casing", [(x * s, r * s) for x, r in core_prof], mat("casing", (0.35, 0.36, 0.38), 0.4, metal=1.0), 96, root)
    bm = bmesh.new()
    bm.from_mesh(cc.data)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(0, 1, 0), clear_inner=True)
    bm.to_mesh(cc.data)
    bm.free()
    # spinner + fan
    lathe(name + "_spinner", [(x * s, r * s) for x, r in [(0.35, 0.0), (0.42, 0.12), (0.6, 0.27), (0.85, 0.34), (0.9, 0.35)]],
          mat("spinner", (0.06, 0.06, 0.07), 0.25, metal=0.6), 48, root)
    for k in range(18):
        a = TAU * k / 18
        b = box(f"{name}_fb{k}", (0.22 * s, 0.025 * s, 0.66 * s), (0.8 * s, -math.sin(a) * 0.66 * s, math.cos(a) * 0.66 * s), blade_m, root,
                rot=(a, math.radians(40), 0))
    # compressor: stages of discs with blades, shrinking radius
    stages = 12
    for i in range(stages):
        x = (1.25 + i * 0.1) * s
        rr = (0.55 - i * 0.022) * s
        cyl(f"{name}_disc{i}", rr * 0.55, 0.03 * s, (x, 0, 0), ti, rot=(0, math.pi / 2, 0), verts=48, parent=root)
        nb = 28 + i * 2
        for k in range(nb):
            a = TAU * k / nb
            box(f"{name}_cb{i}_{k}", (0.05 * s, 0.006 * s, rr * 0.44), (x, -math.sin(a) * rr * 0.78, math.cos(a) * rr * 0.78), ti, root,
                rot=(a, math.radians(35), 0))
    # shaft
    cyl(name + "_shaft", 0.06 * s, 3.6 * s, (2.6 * s, 0, 0), mat("shaft", (0.7, 0.7, 0.72), 0.2, metal=1.0), rot=(0, math.pi / 2, 0), parent=root)
    # combustor ring (glowing)
    comb_m = emissive("flame", (1.0, 0.45, 0.08), 18.0) if glow else hot
    bpy.ops.mesh.primitive_torus_add(major_radius=0.36 * s, minor_radius=0.08 * s, major_segments=64, minor_segments=16,
                                     location=(2.65 * s, 0, 0), rotation=(0, math.pi / 2, 0))
    t = bpy.context.object
    t.name = name + "_combustor"
    t.data.materials.append(comb_m)
    t.parent = root
    for k in range(20):
        a = TAU * k / 20
        cyl(f"{name}_inj{k}", 0.02 * s, 0.25 * s, (2.5 * s, -math.sin(a) * 0.36 * s, math.cos(a) * 0.36 * s), hot, rot=(0, math.pi / 2, 0), verts=12, parent=root)
    # turbines
    for i in range(5):
        x = (3.0 + i * 0.16) * s
        rr = (0.44 + i * 0.03) * s
        cyl(f"{name}_tdisc{i}", rr * 0.5, 0.04 * s, (x, 0, 0), hot, rot=(0, math.pi / 2, 0), verts=48, parent=root)
        nb = 40
        for k in range(nb):
            a = TAU * k / nb
            box(f"{name}_tb{i}_{k}", (0.07 * s, 0.008 * s, rr * 0.48), (x, -math.sin(a) * rr * 0.76, math.cos(a) * rr * 0.76), hot, root,
                rot=(a, math.radians(-40), 0))
    lathe(name + "_plug", [(x * s, r * s) for x, r in [(4.2, 0.36), (4.7, 0.28), (5.1, 0.05), (5.12, 0.0)]], hot, 32, root)
    return root


def motor_section(name="motor"):
    """Electric motor cross-section: stator teeth with copper windings + rotor with magnets. Axis +Y."""
    root = empty(name)
    steel = mat("lamination", (0.3, 0.31, 0.33), 0.35, metal=1.0)
    copper = mat("copper", (0.95, 0.45, 0.25), 0.25, metal=1.0)
    mag = mat("magnet", (0.25, 0.25, 0.27), 0.2, metal=1.0)
    bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=0.5, vertices=128, location=(0, 0, 0), rotation=(math.pi / 2, 0, 0))
    ring = bpy.context.object
    ring.data.materials.append(steel)
    hole = bpy.data.objects.new("hole", None)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.82, depth=0.7, vertices=128, location=(0, 0, 0), rotation=(math.pi / 2, 0, 0))
    h = bpy.context.object
    md = ring.modifiers.new("b", "BOOLEAN")
    md.object = h
    md.operation = "DIFFERENCE"
    bpy.context.view_layer.objects.active = ring
    bpy.ops.object.modifier_apply(modifier="b")
    bpy.data.objects.remove(h)
    ring.parent = root
    for k in range(24):
        a = TAU * k / 24
        r0 = 0.68
        box(f"tooth{k}", (0.07, 0.5, 0.22), (math.sin(a) * r0, 0, math.cos(a) * r0), steel, root, rot=(0, a, 0))
        coil = box(f"coil{k}", (0.13, 0.46, 0.15), (math.sin(a) * (r0 + 0.02), 0, math.cos(a) * (r0 + 0.02)), copper, root, rot=(0, a, 0), bevel=0.03)
    cyl("rotor", 0.5, 0.48, (0, 0, 0), steel, rot=(math.pi / 2, 0, 0), verts=96, parent=root)
    for k in range(16):
        a = TAU * k / 16
        box(f"mag{k}", (0.14, 0.47, 0.04), (math.sin(a) * 0.5, 0, math.cos(a) * 0.5), mag, root, rot=(0, a, 0))
    cyl("motor_shaft", 0.09, 1.4, (0, 0, 0), mat("shaft", (0.7, 0.7, 0.72), 0.2, metal=1.0), rot=(math.pi / 2, 0, 0), parent=root)
    return root


# ----------------------------------------------------------------- the Energy Lab
def lab_floor(size=60, rough=0.12):
    m = mat("lab_floor", (0.006, 0.006, 0.007), rough, coat=0.0)
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, 0))
    bpy.context.object.data.materials.append(m)
    return bpy.context.object


def scale_balance(name="scale", tilt=0.0):
    """Precision balance: base, column, beam, two glass platters at x=±0.55, brass gauge. Returns (root, left_pan_top, right_pan_top)."""
    root = empty(name)
    steel = mat("brushed", (0.62, 0.63, 0.65), 0.22, metal=1.0)
    dark = mat("base_dark", (0.03, 0.03, 0.035), 0.3, coat=0.7)
    brass = mat("brass", (0.85, 0.62, 0.3), 0.25, metal=1.0)
    glassm = mat("platter_glass", (0.9, 0.95, 1.0), 0.02, transm=1.0, ior=1.5)
    box("base", (1.6, 0.5, 0.08), (0, 0, 0.04), dark, root, bevel=0.02)
    cyl("column", 0.035, 0.62, (0, 0, 0.39), steel, parent=root)
    beam = empty("beam", (0, 0, 0.72), root)
    beam.rotation_euler = (0, tilt, 0)
    box("beam_bar", (1.2, 0.04, 0.03), (0, 0, 0), steel, beam, bevel=0.01)
    tops = []
    for sx in (-1, 1):
        x = sx * 0.55
        hang = empty(f"hang{sx}", (x, 0, 0), beam)
        cyl(f"rod{sx}", 0.008, 0.36, (x, 0, -0.18), steel, parent=beam)
        cyl(f"pan{sx}", 0.2, 0.014, (x, 0, -0.37), glassm, verts=96, parent=beam)
        cyl(f"panrim{sx}", 0.205, 0.006, (x, 0, -0.366), steel, verts=96, parent=beam)
        tops.append((x, -0.363 + 0.72))
    # gauge dial at the column
    cyl("gauge", 0.09, 0.03, (0, -0.04, 0.55), brass, rot=(math.pi / 2, 0, 0), parent=root)
    cyl("gauge_face", 0.08, 0.032, (0, -0.042, 0.55), mat("dial", (0.92, 0.9, 0.84), 0.5), rot=(math.pi / 2, 0, 0), parent=root)
    box("needle", (0.004, 0.002, 0.07), (0, -0.06, 0.58), mat("needle", (0.7, 0.05, 0.03), 0.3), root)
    return root, tops


def fuel_cylinder(name, loc, height=0.32, radius=0.045, level=0.85, glow=0.0):
    """Graduated glass cylinder with jet fuel (pale straw)."""
    root = empty(name, loc)
    glassm = mat("lab_glass", (0.95, 0.97, 1.0), 0.01, transm=1.0, ior=1.5)
    fuel = mat("jetfuel" + ("_g" if glow else ""), (1.0, 0.7, 0.28), 0.03, transm=0.75, ior=1.44,
               emit=AMBER if glow else (1.0, 0.6, 0.2), estr=glow if glow else 0.25)
    # glass as thin shell: outer + inner cylinders
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, vertices=64, location=(0, 0, height / 2))
    g = bpy.context.object
    g.data.materials.append(glassm)
    sol = g.modifiers.new("s", "SOLIDIFY")
    sol.thickness = 0.003
    bpy.ops.object.shade_smooth()
    g.parent = root
    cyl(name + "_foot", radius * 1.6, 0.012, (0, 0, 0.006), glassm, verts=64, parent=root)
    cyl(name + "_liq", radius * 0.94, height * level, (0, 0, height * level / 2 + 0.006), fuel, verts=64, parent=root)
    # graduation marks
    mk = mat("grad", (0.95, 0.95, 0.95), 0.4)
    for k in range(9):
        z = 0.04 + k * (height - 0.06) / 8
        box(f"{name}_m{k}", (0.002, 0.012 if k % 2 else 0.02, 0.0015), (0, -radius - 0.001, z), mk, root)
    return root


def cell_21700(name, loc, parent=None, rot=(0, 0, 0)):
    """21700 Li-ion cell: 21 mm × 70 mm, cyan-teal wrap, steel ends."""
    root = empty(name, loc, parent)
    root.rotation_euler = rot
    wrap = mat("cell_wrap", (0.02, 0.32, 0.42), 0.35, coat=0.8)
    steel = mat("cell_steel", (0.78, 0.78, 0.8), 0.18, metal=1.0)
    cyl(name + "_w", 0.0105, 0.066, (0, 0, 0.035), wrap, verts=48, parent=root)
    cyl(name + "_t", 0.0098, 0.004, (0, 0, 0.0685), steel, verts=48, parent=root)
    cyl(name + "_b", 0.0098, 0.004, (0, 0, 0.0015), steel, verts=48, parent=root)
    cyl(name + "_nub", 0.004, 0.0025, (0, 0, 0.0712), steel, verts=24, parent=root)
    return root


def cell_bundle(name, loc, nx=7, ny=2):
    """14 cells (≈1 kg) in a 7×2 hex-ish bundle with nickel strips."""
    root = empty(name, loc)
    nick = mat("nickel", (0.75, 0.74, 0.7), 0.25, metal=1.0)
    for i in range(nx):
        for j in range(ny):
            cell_21700(f"{name}_{i}_{j}", ((i - (nx - 1) / 2) * 0.0215 + (0.0107 if j else 0), (j - 0.5) * 0.0186, 0), root)
    box(name + "_strip", (nx * 0.0215 + 0.01, 0.006, 0.0008), (0.005, 0, 0.0725), nick, root)
    box(name + "_strip2", (nx * 0.0215 + 0.01, 0.006, 0.0008), (0.005, 0, -0.0003), nick, root)
    return root


def energy_column(name, loc, height, radius, color, strength=6.0, core=True):
    """Volumetric-looking light column: emissive core + soft translucent glow shell."""
    root = empty(name, loc)
    core_m = emissive(f"{name}_core", color, strength * 0.45)
    shell = bpy.data.materials.new(f"{name}_shell")
    shell.use_nodes = True
    nt = shell.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.5
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    em.inputs["Strength"].default_value = strength * 0.3
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    inv = nt.nodes.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    nt.links.new(lw.outputs["Facing"], inv.inputs[1])
    nt.links.new(inv.outputs[0], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    cyl(name + "_shell", radius, height, (0, 0, height / 2), shell, verts=64, parent=root)
    if core:
        cyl(name + "_core", radius * 0.25, height, (0, 0, height / 2), core_m, verts=32, parent=root)
    # light so it illuminates the set
    d = bpy.data.lights.new(name + "_l", "POINT")
    d.energy = 40 * strength * min(1, height)
    d.color = color
    d.shadow_soft_size = radius
    lo = bpy.data.objects.new(name + "_l", d)
    bpy.context.scene.collection.objects.link(lo)
    lo.location = (loc[0], loc[1], loc[2] + min(height, 1.0) * 0.5)
    lo.parent = None
    return root


def light_ruler(x, y, height, step, color=(0.6, 0.65, 0.7), strength=1.2):
    """vertical row of faint emissive tick marks."""
    m = emissive("ruler", color, strength)
    for k in range(int(height / step) + 1):
        w = 0.25 if k % 5 == 0 else 0.12
        box(f"tick{k}", (w, 0.004, 0.006), (x, y, k * step), m)


# ----------------------------------------------------------------- batteries at scale
def battery_module(name, loc, w=0.4, d=0.3, h=0.12, parent=None, led=True, lit=1.0):
    root = empty(name, loc, parent)
    case = mat("mod_case", (0.16, 0.17, 0.19), 0.45, metal=0.6)
    box(name + "_c", (w, d, h), (0, 0, h / 2), case, root, bevel=0.006)
    box(name + "_lid", (w * 0.92, d * 0.86, 0.004), (0, 0, h + 0.002), mat("mod_lid", (0.24, 0.25, 0.27), 0.35, metal=0.7), root)
    box(name + "_hv", (0.05, 0.02, 0.02), (w * 0.35, -d / 2 - 0.01, h * 0.6), mat("hv_orange", (1.0, 0.35, 0.02), 0.4), root)
    if led:
        box(name + "_led", (0.05, 0.004, 0.008), (-w * 0.3, -d / 2 - 0.002, h * 0.75), emissive(f"led_{lit:.2f}", CYAN, 8 * lit), root)
    return root


def battery_pallet(name, loc, parent=None, lit=1.0, label=True):
    """One-tonne battery unit (~1.2 × 1.0 × 0.9 m, steel enclosure, HV cables, cyan status LEDs)."""
    root = empty(name, loc, parent)
    steel = mat("pal_steel", (0.23, 0.24, 0.26), 0.42, metal=0.8)
    frame = mat("pal_frame", (0.12, 0.12, 0.13), 0.5, metal=0.6)
    box(name + "_body", (1.2, 1.0, 0.82), (0, 0, 0.53), steel, root, bevel=0.02)
    for (sx, sy) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        box(name + "_post", (0.06, 0.06, 0.94), (sx * 0.6, sy * 0.5, 0.47), frame, root)
    box(name + "_skid", (1.24, 1.04, 0.12), (0, 0, 0.06), frame, root)
    for k in range(3):  # fork pockets
        pass
    box(name + "_pocket1", (0.25, 1.06, 0.07), (-0.32, 0, 0.06), mat("void", (0.0, 0.0, 0.0), 1.0), root)
    box(name + "_pocket2", (0.25, 1.06, 0.07), (0.32, 0, 0.06), mat("void", (0.0, 0.0, 0.0), 1.0), root)
    for k in range(4):
        box(f"{name}_led{k}", (0.07, 0.006, 0.02), (-0.42 + k * 0.1, -0.505, 0.8), emissive(f"pled_{lit:.2f}", CYAN, 12 * lit), root)
    box(name + "_warn", (0.22, 0.004, 0.16), (0.36, -0.503, 0.72), mat("warn_yel", (1.0, 0.75, 0.05), 0.5), root)
    box(name + "_cable", (0.06, 0.06, 0.6), (0.62, -0.25, 0.55), mat("hv_orange", (1.0, 0.35, 0.02), 0.4), root)
    for k in range(5):  # vents
        box(f"{name}_vent{k}", (0.9, 0.006, 0.012), (0, -0.503, 0.3 + k * 0.05), frame, root)
    return root


def fuel_cube(name, loc, glow=2.0):
    """1 tonne of jet fuel: 1.25 m³ cube (1.077 m side) in a thin glass tank with a steel frame."""
    root = empty(name, loc)
    a = 1.077
    glassm = mat("tank_glass", (0.95, 0.97, 1.0), 0.02, transm=1.0, ior=1.5)
    fuel = mat("cube_fuel", (1.0, 0.72, 0.3), 0.02, transm=0.9, ior=1.44, emit=AMBER, estr=glow)
    steel = mat("cube_frame", (0.55, 0.56, 0.58), 0.25, metal=1.0)
    box(name + "_glass", (a + 0.02, a + 0.02, a + 0.02), (0, 0, a / 2 + 0.06), glassm, root)
    box(name + "_fuel", (a - 0.01, a - 0.01, a * 0.96), (0, 0, a * 0.48 + 0.06), fuel, root)
    t = 0.035
    for (sx, sy) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        box(name + "_v", (t, t, a + 0.08), (sx * (a / 2 + 0.01), sy * (a / 2 + 0.01), a / 2 + 0.06), steel, root)
    for z in (0.04, a + 0.08):
        for (sx, sy, w, d) in ((0, -1, a + 0.06, t), (0, 1, a + 0.06, t), (-1, 0, t, a + 0.06), (1, 0, t, a + 0.06)):
            box(name + "_h", (w, d, t), (sx * (a / 2 + 0.01), sy * (a / 2 + 0.01), z), steel, root)
    return root


def mannequin(name, loc, rot_z=0.0, coverall=(0.12, 0.2, 0.32), hivis=True):
    """Simple stylised technician figure for scale (1.8 m)."""
    root = empty(name, loc)
    root.rotation_euler = (0, 0, rot_z)
    cm = mat("coverall", coverall, 0.8)
    skin = mat("skin", (0.55, 0.38, 0.28), 0.6)
    hv = mat("hivis", (0.85, 0.95, 0.1), 0.6, emit=(0.6, 0.7, 0.05), estr=0.4) if hivis else cm
    helmet = mat("helmet", (0.95, 0.95, 0.92), 0.35, coat=0.5)
    for sx in (-1, 1):
        cyl(f"{name}_leg{sx}", 0.075, 0.86, (0, sx * 0.1, 0.43), cm, parent=root)
        cyl(f"{name}_arm{sx}", 0.055, 0.62, (0.02, sx * 0.25, 1.17), cm, rot=(sx * 0.08, 0, 0), parent=root)
        sphere(f"{name}_boot{sx}", 0.09, (0.04, sx * 0.1, 0.05), mat("boot", (0.05, 0.04, 0.03), 0.7), (1.4, 0.8, 0.6), root)
    sphere(f"{name}_torso", 1, (0, 0, 1.18), cm, (0.14, 0.23, 0.34), root)
    sphere(f"{name}_vest", 1, (0, 0, 1.2), hv, (0.15, 0.235, 0.24), root)
    cyl(f"{name}_neck", 0.05, 0.1, (0, 0, 1.53), skin, parent=root)
    sphere(f"{name}_head", 0.11, (0, 0, 1.66), skin, (1, 0.9, 1.1), root)
    sphere(f"{name}_helmet", 0.125, (0, 0, 1.72), helmet, (1.05, 0.95, 0.75), root)
    return root


# ----------------------------------------------------------------- big environments
def hangar(length=120, width=90, height=28, floor_rough=0.18, lights_on=(1, 1, 1), door_open=0.0, night=False):
    """Hangar interior: epoxy floor, ribbed walls, roof trusses, 3 banks of high-bay lights.
    Door wall at x = −length/2 (camera usually inside looking +X or −X)."""
    floor = mat("epoxy", (0.33, 0.35, 0.37), floor_rough, coat=0.4)
    wall = mat("hangar_wall", (0.38, 0.4, 0.42), 0.6, metal=0.3)
    truss = mat("truss", (0.25, 0.27, 0.3), 0.5, metal=0.6)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    f = bpy.context.object
    f.scale = (length, width, 1)
    f.data.materials.append(floor)
    # floor markings
    ym = mat("floor_yellow", (0.9, 0.7, 0.05), 0.4)
    for y in (-width / 2 + 6, width / 2 - 6):
        box("fline", (length - 10, 0.15, 0.002), (0, y, 0.001), ym)
    box("cline", (length - 30, 0.12, 0.002), (0, 0, 0.001), ym)
    # walls with ribs
    box("wall_back", (0.3, width, height), (length / 2, 0, height / 2), wall)
    for sy in (-1, 1):
        box("wall_side", (length, 0.3, height), (0, sy * width / 2, height / 2), wall)
        for k in range(int(length / 3)):
            box("rib", (0.12, 0.2, height), (-length / 2 + k * 3, sy * (width / 2 - 0.2), height / 2), truss)
    box("roof", (length, width, 0.4), (0, 0, height + 0.2), wall)
    for k in range(8):
        x = -length / 2 + 8 + k * (length - 16) / 7
        box("truss_b", (0.5, width, 1.4), (x, 0, height - 0.8), truss)
        for j in range(12):
            box("truss_d", (0.12, 0.12, 2.2), (x, -width / 2 + 4 + j * (width - 8) / 11, height - 1.6), truss, rot=(0.5 if j % 2 else -0.5, 0, 0))
    # light banks (3 rows along X), each fixture emissive + area light
    banks = []
    for b, yb in enumerate((-width / 4, 0, width / 4)):
        on = lights_on[b]
        em = emissive(f"bay_{b}_{on:.2f}", (1.0, 0.95, 0.88), 12 * on) if on > 0 else mat("bay_off", (0.2, 0.2, 0.2), 0.4)
        for k in range(6):
            x = -length / 2 + 12 + k * (length - 24) / 5
            box("bay", (1.4, 0.7, 0.12), (x, yb, height - 2.2), em)
        if on > 0:
            d = bpy.data.lights.new(f"bank{b}", "AREA")
            d.shape = "RECTANGLE"
            d.size = length * 0.8
            d.size_y = 3
            d.energy = 9000 * on
            d.color = (1.0, 0.95, 0.88)
            o = bpy.data.objects.new(f"bank{b}", d)
            bpy.context.scene.collection.objects.link(o)
            o.location = (0, yb, height - 2.5)
    # door wall: two panels that slide apart (door_open 0..1)
    door = mat("door", (0.42, 0.44, 0.46), 0.55, metal=0.4)
    gap = width * 0.8 * door_open / 2
    for sy in (-1, 1):
        box("door_p", (0.3, width * 0.4, height * 0.85), (-length / 2, sy * (width * 0.2 + gap), height * 0.425), door)
    box("door_top", (0.3, width, height * 0.15), (-length / 2, 0, height * 0.925), wall)
    return f


def ocean(size=80000, color=(0.01, 0.04, 0.06), rough=0.08, wave_scale=0.6, detail=6):
    m = bpy.data.materials.new("ocean")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["IOR"].default_value = 1.33
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = wave_scale
    n.inputs["Detail"].default_value = detail
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1, 3, 1)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], n.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.35
    nt.links.new(n.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, 0))
    bpy.context.object.data.materials.append(m)
    return bpy.context.object


def terrain(size=20000, seed=1, height=60, color_a=(0.08, 0.1, 0.04), color_b=(0.22, 0.2, 0.1), z=0, fields=True, subdiv=200):
    """Rolling farmland: displaced grid with patchwork field colours."""
    rs = np.random.RandomState(seed)
    n = subdiv
    xs = np.linspace(-size / 2, size / 2, n)
    X, Y = np.meshgrid(xs, xs)
    Z = np.zeros_like(X)
    for k in range(6):
        f = (k + 1) * 0.7 / size * 2
        Z += height / (k + 1) * np.sin(X * f * TAU + rs.rand() * 6) * np.cos(Y * f * TAU * 0.8 + rs.rand() * 6)
    verts = [(X[i, j], Y[i, j], Z[i, j] + z) for i in range(n) for j in range(n)]
    faces = [(i * n + j, i * n + j + 1, (i + 1) * n + j + 1, (i + 1) * n + j) for i in range(n - 1) for j in range(n - 1)]
    uvs = [((j / (n - 1)), (i / (n - 1))) for i in range(n) for j in range(n)]
    # patchwork texture
    T = 1024
    tex = np.ones((T, T, 4), np.float32)
    cells = rs.rand(40, 40)
    cols = np.array([color_a, color_b, (0.15, 0.17, 0.06), (0.3, 0.26, 0.14), (0.06, 0.09, 0.04)], np.float32)
    idx = (cells * len(cols)).astype(int)
    big = np.kron(idx, np.ones((T // 40 + 1, T // 40 + 1), int))[:T, :T]
    tex[..., :3] = cols[big]
    tex[..., :3] *= (0.85 + 0.3 * rs.rand(T, T, 1)).astype(np.float32)
    img = image_from_array(f"fields{seed}", tex)
    m = textured_mat(f"terrain{seed}", img, coat=0.0, rough=0.95)
    return obj_from_mesh("terrain", verts, faces, m, uvs)


def islands(seed=4, n=7, color=(0.06, 0.09, 0.04)):
    rs = np.random.RandomState(seed)
    m = mat("island", color, 0.9)
    sand = mat("sand", (0.55, 0.48, 0.34), 0.9)
    for k in range(n):
        x, y = rs.uniform(-3000, 3000), rs.uniform(800, 6000)
        r = rs.uniform(150, 600)
        sphere(f"isl{k}", 1, (x, y, -r * 0.15), m, (r, r * rs.uniform(0.5, 1.2), r * rs.uniform(0.25, 0.45)))
        sphere(f"beach{k}", 1, (x, y, -r * 0.2), sand, (r * 1.04, r * 1.05 * rs.uniform(0.5, 1.2), r * 0.24))


def cloud_layer(z=1200, size=30000, density=0.06, scale=0.0004, thickness=300):
    """Volumetric cloud deck (noise-thresholded volume)."""
    m = bpy.data.materials.new("cloud")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    v = nt.nodes.new("ShaderNodeVolumePrincipled")
    v.inputs["Color"].default_value = (1, 1, 1, 1)
    v.inputs["Anisotropy"].default_value = 0.3
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 3.0
    n.inputs["Detail"].default_value = 6
    n.inputs["Roughness"].default_value = 0.6
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.55
    ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
    ramp.color_ramp.elements[1].position = 0.7
    ramp.color_ramp.elements[1].color = (1, 1, 1, 1)
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = density
    nt.links.new(tc.outputs["Generated"], n.inputs["Vector"])
    nt.links.new(n.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], mul.inputs[0])
    nt.links.new(mul.outputs[0], v.inputs["Density"])
    nt.links.new(v.outputs[0], out.inputs["Volume"])
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, z))
    o = bpy.context.object
    o.scale = (size, size, thickness)
    o.data.materials.append(m)
    return o


def town_lights(on=1.0, seed=2, n_blocks=60, spacing=60, origin=(0, 0)):
    """Night town from above: street grid of warm lights + house windows."""
    rs = np.random.RandomState(seed)
    street = emissive(f"street_{on:.2f}", (1.0, 0.7, 0.35), 40 * on) if on else mat("dark_lamp", (0.02, 0.02, 0.02), 0.5)
    win = emissive(f"win_{on:.2f}", (1.0, 0.82, 0.55), 12 * on) if on else mat("dark_win", (0.02, 0.02, 0.02), 0.5)
    house = mat("house", (0.05, 0.05, 0.055), 0.8)
    ground = mat("night_ground", (0.01, 0.012, 0.01), 0.9)
    bpy.ops.mesh.primitive_plane_add(size=12000, location=(0, 0, -0.1))
    bpy.context.object.data.materials.append(ground)
    g = int(math.sqrt(n_blocks))
    lamp_v, lamp_f, win_v, win_f, h_v, h_f = [], [], [], [], [], []

    def add_box(V, F, cx, cy, cz, sx, sy, sz):
        i0 = len(V)
        for dx, dy, dz in ((-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1), (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)):
            V.append((cx + dx * sx / 2, cy + dy * sy / 2, cz + dz * sz / 2))
        F += [(i0, i0 + 1, i0 + 2, i0 + 3), (i0 + 4, i0 + 5, i0 + 6, i0 + 7), (i0, i0 + 1, i0 + 5, i0 + 4),
              (i0 + 1, i0 + 2, i0 + 6, i0 + 5), (i0 + 2, i0 + 3, i0 + 7, i0 + 6), (i0 + 3, i0, i0 + 4, i0 + 7)]
    for i in range(-g, g):
        for j in range(-g, g):
            if math.hypot(i, j) > g * (0.8 + 0.3 * rs.rand()):
                continue
            x0, y0 = origin[0] + i * spacing, origin[1] + j * spacing
            for k in range(6):
                add_box(lamp_v, lamp_f, x0 + k * spacing / 6, y0, 6, 1.6, 1.6, 0.6)
                add_box(lamp_v, lamp_f, x0, y0 + k * spacing / 6, 6, 1.6, 1.6, 0.6)
            for k in range(rs.randint(3, 7)):
                hx, hy = x0 + rs.uniform(8, spacing - 8), y0 + rs.uniform(8, spacing - 8)
                add_box(h_v, h_f, hx, hy, 3, 9, 7, 6)
                if rs.rand() < 0.7:
                    add_box(win_v, win_f, hx, hy, 6.2, 4, 3, 0.2)
    obj_from_mesh("lamps", lamp_v, lamp_f, street, smooth=False)
    obj_from_mesh("houses", h_v, h_f, house, smooth=False)
    obj_from_mesh("wins", win_v, win_f, win, smooth=False)


def apron(size=4000, color=(0.32, 0.32, 0.31)):
    m = bpy.data.materials.new("apron")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 0.6
    n.inputs["Detail"].default_value = 10
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (color[0] * 0.75, color[1] * 0.75, color[2] * 0.75, 1)
    ramp.color_ramp.elements[1].color = (*color, 1)
    nt.links.new(n.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.85
    # concrete slab joints via wave texture
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, 0))
    bpy.context.object.data.materials.append(m)
    return bpy.context.object


def ev_battery_grid(n_x, n_y, pitch_x=2.2, pitch_y=3.0, origin=(0, 0), lit=1.0):
    """Field of EV battery packs (≈2 × 1.5 × 0.15 m) laid on the apron, as one mesh."""
    V, F = [], []
    W, D, H = 1.9, 1.4, 0.15
    for i in range(n_x):
        for j in range(n_y):
            cx, cy = origin[0] + i * pitch_x, origin[1] + j * pitch_y
            i0 = len(V)
            for dx, dy, dz in ((-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0), (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)):
                V.append((cx + dx * W / 2, cy + dy * D / 2, dz * H))
            F += [(i0 + 4, i0 + 5, i0 + 6, i0 + 7), (i0, i0 + 1, i0 + 5, i0 + 4), (i0 + 1, i0 + 2, i0 + 6, i0 + 5),
                  (i0 + 2, i0 + 3, i0 + 7, i0 + 6), (i0 + 3, i0, i0 + 4, i0 + 7)]
    o = obj_from_mesh("evgrid", V, F, mat("ev_pack", (0.1, 0.11, 0.12), 0.45, metal=0.7), smooth=False)
    # LED strip per pack
    LV, LF = [], []
    for i in range(n_x):
        for j in range(n_y):
            cx, cy = origin[0] + i * pitch_x, origin[1] + j * pitch_y
            i0 = len(LV)
            for dx, dy in ((-0.5, -0.03), (0.5, -0.03), (0.5, 0.03), (-0.5, 0.03)):
                LV.append((cx + dx, cy + dy, H + 0.005))
            LF.append((i0, i0 + 1, i0 + 2, i0 + 3))
    obj_from_mesh("evleds", LV, LF, emissive(f"evled{lit:.2f}", CYAN, 6 * lit), smooth=False)
    return o


def fuel_tanks(root, kind="narrow", level=1.0, color=AMBER, strength=4.0, name="tanks"):
    """Glowing fuel volumes inside an x-ray airliner (wing tanks + centre tank), filled to `level`."""
    m = emissive(f"{name}_{level:.2f}", color, strength)
    if kind == "narrow":
        wx, span, rc, wz, R = 13.0, 17.1, 6.3, -1.25, 1.98
    else:
        wx, span, rc, wz, R = 25.0, 32.0, 12.5, -2.0, 3.1
    if level <= 0:
        return
    for sgn in (1, -1):
        secs = []
        y_end = R + (span - R) * 0.85
        for k in range(5):
            f = k / 4
            yy = sgn * (R * 0.8 + f * (y_end - R * 0.8))
            chord = (rc + (rc * 0.3 - rc) * f) * 0.55
            x = wx + rc * 0.15 + abs(yy - sgn * R * 0.75) * math.tan(math.radians(27 if kind == "narrow" else 31))
            z = wz + abs(yy) * math.tan(math.radians(5))
            secs.append((Vector((x, yy, z - 0.05)), chord, 0.09 * level + 0.01, 0, False))
        lofted_surface(f"{name}_w{sgn}", secs, m, root)
    box(f"{name}_ctr", (rc * 0.6, R * 1.3, R * 0.5 * level), (wx + rc * 0.45, 0, -R * 0.55 + R * 0.25 * level - R * 0.25), m, root)
    # fuel lines to engines
    lm = emissive(f"{name}_line", color, strength * 0.6)
    ey = 5.75 if kind == "narrow" else 9.6
    for sgn in (1, -1):
        cyl(f"{name}_ln{sgn}", 0.06, ey - 1, (wx + 1.0, sgn * (ey / 2 + 0.5), wz + 0.2), lm, rot=(math.pi / 2, 0, 0), verts=12, parent=root)


def lab_backdrop(color=(0.012, 0.012, 0.014), dist=4.0):
    """curved cyclorama behind the set so glass and metal have something to reflect."""
    m = mat("cyc", color, 0.5)
    verts, faces = [], []
    n = 24
    for i in range(n + 1):
        a = (i / n) * math.pi / 2
        y = dist + math.sin(a) * 1.5 - 1.5
        z = (1 - math.cos(a)) * 1.5
        if i == n:
            pass
        verts += [(-12, y, z), (12, y, z)]
    verts += [(-12, dist, 8), (12, dist, 8)]
    for i in range(n + 1):
        faces.append((2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2))
    return obj_from_mesh("cyc", verts, faces, m)


def softbox_strip(name, loc, rot, w, h, strength, color=(1, 1, 1)):
    """visible emissive strip (shows up as reflections in glass/metal) + matching area light."""
    m = emissive(name + "_m", color, strength)
    box(name, (w, 0.01, h), loc, m, rot=rot)


def _box_mesh(V, F, cx, cy, cz, sx, sy, sz):
    i0 = len(V)
    for dx, dy, dz in ((-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1), (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)):
        V.append((cx + dx * sx / 2, cy + dy * sy / 2, cz + dz * sz / 2))
    F += [(i0, i0 + 3, i0 + 2, i0 + 1), (i0 + 4, i0 + 5, i0 + 6, i0 + 7), (i0, i0 + 1, i0 + 5, i0 + 4),
          (i0 + 1, i0 + 2, i0 + 6, i0 + 5), (i0 + 2, i0 + 3, i0 + 7, i0 + 6), (i0 + 3, i0, i0 + 4, i0 + 7)]


def module_field(name, centers, size, parent=None, lit=1.0, led=True):
    """Many battery modules as two meshes (cases + cyan LED strips). centers: list of (x, y, z_bottom)."""
    V, F, LV, LF = [], [], [], []
    w, d, h = size
    for (x, y, z) in centers:
        _box_mesh(V, F, x, y, z + h / 2, w * 0.97, d * 0.97, h * 0.97)
        if led:
            _box_mesh(LV, LF, x - w * 0.25, y - d / 2 - 0.005, z + h * 0.72, w * 0.3, 0.012, h * 0.08)
            _box_mesh(LV, LF, x + w * 0.25, y + d / 2 + 0.005, z + h * 0.72, w * 0.3, 0.012, h * 0.08)
    o = obj_from_mesh(name, V, F, mat("mod_case", (0.16, 0.17, 0.19), 0.45, metal=0.6), smooth=False, parent=parent)
    if led:
        obj_from_mesh(name + "_led", LV, LF, emissive(f"led_{lit:.2f}", CYAN, 10 * lit), smooth=False, parent=parent)
    return o


def pallet_field(name, centers, lit=1.0):
    """Many one-tonne battery units as a few merged meshes (fast for 100+ units)."""
    S, Fr, L, Y, O = ([], []), ([], []), ([], []), ([], []), ([], [])
    for (x, y, z) in centers:
        _box_mesh(*S, x, y, z + 0.53, 1.2, 1.0, 0.82)
        _box_mesh(*Fr, x, y, z + 0.06, 1.24, 1.04, 0.12)
        for sx in (-1, 1):
            for sy in (-1, 1):
                _box_mesh(*Fr, x + sx * 0.6, y + sy * 0.5, z + 0.47, 0.06, 0.06, 0.94)
        for k in range(4):
            _box_mesh(*L, x - 0.42 + k * 0.1, y - 0.505, z + 0.8, 0.07, 0.008, 0.02)
        _box_mesh(*Y, x + 0.36, y - 0.504, z + 0.72, 0.22, 0.006, 0.16)
        _box_mesh(*O, x + 0.62, y - 0.25, z + 0.55, 0.06, 0.06, 0.6)
    obj_from_mesh(name + "_body", *S, mat("pal_steel", (0.23, 0.24, 0.26), 0.42, metal=0.8), smooth=False)
    obj_from_mesh(name + "_frame", *Fr, mat("pal_frame", (0.12, 0.12, 0.13), 0.5, metal=0.6), smooth=False)
    obj_from_mesh(name + "_led", *L, emissive(f"pled_{lit:.2f}", CYAN, 12 * lit), smooth=False)
    obj_from_mesh(name + "_warn", *Y, mat("warn_yel", (1.0, 0.75, 0.05), 0.5), smooth=False)
    obj_from_mesh(name + "_hv", *O, mat("hv_orange", (1.0, 0.35, 0.02), 0.4), smooth=False)
