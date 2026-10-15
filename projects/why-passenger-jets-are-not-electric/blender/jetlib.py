"""jetlib — procedural, render-ready assets for "Why Passenger Jets Are Not Electric".

Everything is built from code in Blender (bpy), so the film needs no licensed models:
  airliner()      A320-class narrow-body (≈37.6 m long, 35.8 m span, generic white livery)
  widebody()      777-class twin (scaled-up variant, longer fuselage, bigger engines)
  runway(), apron(), hangar(), lab()   environments
  battery_cell(), battery_module(), battery_pallet(), fuel_cube()   props
  sky(), sun(), camera(), render()     lighting / output helpers

Units are metres. Aircraft nose points to −X… no: nose at x=0, tail at +X, +Z up, left wing +Y.
"""
import math, os
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix, Euler

TAU = 2 * math.pi


# ----------------------------------------------------------------- scene basics
def reset(engine="CYCLES"):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = engine
    sc.cycles.device = "CPU"
    sc.cycles.samples = 64
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = "OPENIMAGEDENOISE"
    sc.cycles.max_bounces = 6
    sc.cycles.glossy_bounces = 3
    sc.cycles.transmission_bounces = 4
    sc.cycles.volume_bounces = 0
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    sc.view_settings.exposure = -0.6
    sc.render.image_settings.file_format = "PNG"
    sc.render.fps = 24
    return sc


def mat(name, color=(0.8, 0.8, 0.8), rough=0.4, metal=0.0, coat=0.0, emit=None, estr=0.0, alpha=1.0, transm=0.0, ior=1.45):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["IOR"].default_value = ior
    if transm:
        b.inputs["Transmission Weight"].default_value = transm
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = estr
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
    return m


def emissive(name, color, strength):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*color, 1)
    e.inputs["Strength"].default_value = strength
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(e.outputs[0], o.inputs[0])
    return m


def obj_from_mesh(name, verts, faces, material=None, uvs=None, smooth=True, parent=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.update()
    if uvs is not None:
        uvl = me.uv_layers.new(name="UVMap")
        for poly in me.polygons:
            for li in poly.loop_indices:
                vi = me.loops[li].vertex_index
                uvl.data[li].uv = uvs[vi]
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    if material:
        me.materials.append(material)
    if parent:
        o.parent = parent
    return o


def empty(name, loc=(0, 0, 0), parent=None):
    o = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    if parent:
        o.parent = parent
    return o


# ----------------------------------------------------------------- textures
def image_from_array(name, arr):
    """arr: HxWx4 float32 0..1 (row 0 = bottom)."""
    h, w = arr.shape[:2]
    img = bpy.data.images.new(name, w, h, alpha=True, float_buffer=False)
    img.pixels.foreach_set(arr.astype(np.float32).ravel())
    img.pack()
    return img


def textured_mat(name, img, rough_img=None, metal=0.0, coat=0.4, rough=0.3, emit_img=None, estr=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tx = nt.nodes.new("ShaderNodeTexImage")
    tx.image = img
    tx.interpolation = "Cubic"
    nt.links.new(tx.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Coat Roughness"].default_value = 0.08
    if rough_img is not None:
        rt = nt.nodes.new("ShaderNodeTexImage")
        rt.image = rough_img
        rt.image.colorspace_settings.name = "Non-Color"
        nt.links.new(rt.outputs["Color"], b.inputs["Roughness"])
    else:
        b.inputs["Roughness"].default_value = rough
    if emit_img is not None:
        et = nt.nodes.new("ShaderNodeTexImage")
        et.image = emit_img
        nt.links.new(et.outputs["Color"], b.inputs["Emission Color"])
        b.inputs["Emission Strength"].default_value = estr
    return m


# ----------------------------------------------------------------- airliner geometry
def _fuselage_profile(L, R, nose=5.2, tail0=0.72):
    """radius(x), centre-z(x) along the fuselage (0 = nose tip)."""
    def r(x):
        if x < nose:
            k = x / nose
            return R * (1 - (1 - k) ** 2.4) ** 0.5
        t0 = L * tail0
        if x > t0:
            k = (x - t0) / (L - t0)
            return R * (1 - k) ** 1.15 * 0.88 + R * 0.12 * (1 - k) + 0.02
        return R

    def zc(x):
        if x < nose:
            return -(R - r(x)) * 0.35
        t0 = L * tail0
        if x > t0:
            return (R - r(x)) * 0.92
        return 0.0
    return r, zc


def fuselage(name, L=37.6, R=1.98, livery=None, parent=None, nseg=64, nring=160):
    r, zc = _fuselage_profile(L, R)
    xs = np.concatenate([np.linspace(0, 6, 50) ** 1.0, np.linspace(6, L, nring - 50)[1:]])
    xs[0] = 0.001
    verts, uvs, faces = [], [], []
    for i, x in enumerate(xs):
        rr, z0 = r(x), zc(x)
        for j in range(nseg + 1):
            th = TAU * j / nseg  # 0 = top, increasing toward +Y (left) side
            y = rr * math.sin(th) * 0.985
            z = z0 + rr * math.cos(th) * 1.04
            verts.append((x, y, z))
            uvs.append((x / L, j / nseg))
    W = nseg + 1
    for i in range(len(xs) - 1):
        for j in range(nseg):
            a = i * W + j
            faces.append((a, a + 1, a + W + 1, a + W))
    # tail cap
    c = len(verts)
    verts.append((L + 0.05, 0, zc(L)))
    uvs.append((1, 0.5))
    base = (len(xs) - 1) * W
    for j in range(nseg):
        faces.append((base + j, base + j + 1, c))
    m = livery or mat("paint_white", (0.86, 0.87, 0.88), 0.3, coat=0.5)
    return obj_from_mesh(name, verts, faces, m, uvs, parent=parent)


def airfoil(n=48, t=0.12, camber=0.02):
    """closed airfoil polyline in chord units, LE at 0, TE at 1 (upper then lower)."""
    xs = (1 - np.cos(np.linspace(0, math.pi, n))) / 2
    yt = 5 * t * (0.2969 * np.sqrt(xs) - 0.126 * xs - 0.3516 * xs ** 2 + 0.2843 * xs ** 3 - 0.1036 * xs ** 4)
    yc = camber * 4 * xs * (1 - xs)
    up = list(zip(xs, yc + yt))
    lo = list(zip(xs[::-1], (yc - yt)[::-1]))
    return up + lo[1:-1]


def lofted_surface(name, sections, material, parent=None, cap=True):
    """sections: list of (origin Vector, chord, t, twist_deg, axis='y'|'z').
    Each section is an airfoil in the X-Z plane (chord along +X) placed at origin."""
    verts, faces = [], []
    npts = None
    for (o, chord, t, twist, vertical) in sections:
        pts = airfoil(40, t, 0.015 if not vertical else 0.0)
        npts = len(pts)
        ct, st = math.cos(math.radians(twist)), math.sin(math.radians(twist))
        for (px, pz) in pts:
            x = px * chord
            zz = pz * chord
            x, zz = x * ct + zz * st, -x * st + zz * ct
            if vertical:  # fin: thickness along Y
                verts.append((o.x + x, o.y + zz, o.z))
            else:
                verts.append((o.x + x, o.y, o.z + zz))
    for s in range(len(sections) - 1):
        for k in range(npts):
            a = s * npts + k
            b = s * npts + (k + 1) % npts
            faces.append((a, b, b + npts, a + npts))
    if cap:
        faces.append(tuple(range(npts))[::-1])
        last = (len(sections) - 1) * npts
        faces.append(tuple(range(last, last + npts)))
    o = obj_from_mesh(name, verts, faces, material, parent=parent)
    o.data.shade_smooth()
    return o


def lathe(name, profile, material, segs=64, parent=None, axis_dir=1):
    """profile: list of (x, radius). Revolved around the X axis."""
    verts, faces = [], []
    for (x, rr) in profile:
        for j in range(segs):
            a = TAU * j / segs
            verts.append((x, rr * math.cos(a), rr * math.sin(a)))
    for i in range(len(profile) - 1):
        for j in range(segs):
            a = i * segs + j
            b = i * segs + (j + 1) % segs
            faces.append((a, b, b + segs, a + segs))
    return obj_from_mesh(name, verts, faces, material, parent=parent)


def nacelle(name, parent, loc, scale=1.0, fan_blades=18, detailed=True):
    """turbofan nacelle with fan, spinner, core nozzle and plug. Inlet faces −X."""
    root = empty(name, loc, parent)
    s = scale
    paint = mat("nacelle_paint", (0.84, 0.85, 0.86), 0.28, coat=0.6)
    lip = mat("nacelle_lip", (0.75, 0.76, 0.78), 0.18, metal=1.0)
    dark = mat("inlet_dark", (0.02, 0.02, 0.025), 0.5)
    core = mat("core_metal", (0.32, 0.31, 0.3), 0.35, metal=1.0)
    hot = mat("hot_metal", (0.18, 0.14, 0.12), 0.4, metal=1.0)
    outer = [(0, 1.02), (0.06, 1.10), (0.25, 1.17), (0.8, 1.21), (2.2, 1.18), (3.3, 1.02), (3.9, 0.86)]
    o = lathe(name + "_cowl", [(x * s, r * s) for x, r in outer], paint, 72, root)
    inner = [(0, 1.02), (0.05, 0.99), (0.3, 0.97), (0.9, 0.98)]
    lathe(name + "_inlet", [(x * s, r * s) for x, r in inner], dark, 72, root)
    lathe(name + "_lip", [(-0.02 * s, 1.035 * s), (0.0, 1.06 * s), (0.08 * s, 1.11 * s), (0.0, 1.0 * s)], lip, 72, root)
    # fan
    spinner = [(0.55, 0.0), (0.6, 0.12), (0.75, 0.26), (0.95, 0.33), (1.0, 0.34)]
    lathe(name + "_spinner", [(x * s, r * s) for x, r in spinner], mat("spinner", (0.06, 0.06, 0.07), 0.25, metal=0.6), 48, root)
    fan = empty(name + "_fan", (0.95 * s, 0, 0), root)
    blade_m = mat("fan_blade", (0.2, 0.21, 0.23), 0.22, metal=1.0)
    for k in range(fan_blades):
        a = TAU * k / fan_blades
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        me = bpy.data.meshes.new(f"{name}_b{k}")
        bm.to_mesh(me)
        bm.free()
        b = bpy.data.objects.new(f"{name}_b{k}", me)
        bpy.context.scene.collection.objects.link(b)
        b.data.materials.append(blade_m)
        b.parent = fan
        b.scale = (0.18 * s, 0.03 * s, 0.33 * s)
        b.location = (0, math.cos(a) * 0.66 * s, math.sin(a) * 0.66 * s)
        b.rotation_euler = (a - math.pi / 2, 0, 0)
        b.rotation_euler.rotate(Euler((0, 0, 0)))
        b.rotation_mode = "XYZ"
        b.rotation_euler = (a, math.radians(38), 0)
        b.location = (0, -math.sin(a) * 0.66 * s, math.cos(a) * 0.66 * s)
    # exhaust: core cowl, nozzle, plug
    lathe(name + "_core", [(3.85 * s, 0.86 * s), (4.3 * s, 0.68 * s), (4.6 * s, 0.6 * s)], core, 48, root)
    lathe(name + "_noz", [(4.6 * s, 0.6 * s), (4.62 * s, 0.5 * s)], hot, 48, root)
    lathe(name + "_plug", [(4.4 * s, 0.42 * s), (4.9 * s, 0.3 * s), (5.3 * s, 0.05 * s), (5.32 * s, 0.0)], hot, 32, root)
    return root


def landing_gear(parent, x, y, z_top, z_ground, wheels=2, tire_r=0.62, name="gear"):
    tire = mat("tire", (0.015, 0.015, 0.016), 0.75)
    hub = mat("hub", (0.22, 0.22, 0.23), 0.35, metal=1.0)
    strut = mat("strut", (0.75, 0.76, 0.78), 0.2, metal=1.0)
    root = empty(name, (x, y, 0), parent)
    h = z_top - (z_ground + tire_r)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.16, depth=h, location=(0, 0, z_ground + tire_r + h / 2))
    st = bpy.context.object
    st.data.materials.append(strut)
    st.parent = root
    st.location = (x, y, z_ground + tire_r + h / 2)
    st.parent = parent
    for k in range(wheels):
        off = (k - (wheels - 1) / 2) * 0.62
        bpy.ops.mesh.primitive_torus_add(major_radius=tire_r * 0.72, minor_radius=tire_r * 0.28, major_segments=48, minor_segments=16,
                                         location=(x, y + off, z_ground + tire_r), rotation=(math.pi / 2, 0, 0))
        t = bpy.context.object
        t.data.materials.append(tire)
        bpy.ops.object.shade_smooth()
        t.parent = parent
        bpy.ops.mesh.primitive_cylinder_add(radius=tire_r * 0.42, depth=tire_r * 0.5, location=(x, y + off, z_ground + tire_r), rotation=(math.pi / 2, 0, 0))
        hb = bpy.context.object
        hb.data.materials.append(hub)
        hb.parent = parent
    return root


def livery_textures(L, kind="narrow", tail_color=(0.07, 0.13, 0.22)):
    """Fuselage colour + roughness maps in (u = x/L, v = angle/2π) space. Generic, logo-free."""
    W, H = 4096, 1024
    col = np.ones((H, W, 4), np.float32)
    col[..., :3] = (0.86, 0.87, 0.88)
    rough = np.full((H, W, 4), 0.3, np.float32)
    rough[..., 3] = 1
    u = (np.arange(W) + 0.5) / W
    v = (np.arange(H) + 0.5) / H
    th = v * 360.0  # degrees, 0 = top
    X = u * L
    R = 1.98 if kind == "narrow" else 3.1
    # grey belly
    belly = (th > 112) & (th < 248)
    col[belly, :, :3] = (0.55, 0.57, 0.6)
    # thin cool-grey cheatline below windows
    for c0 in (101, 259):
        band = np.abs(th - c0) < 1.2
        col[band, :, :3] = (0.2, 0.33, 0.45)
    # windows
    pitch = 0.533
    wx0, wx1 = (6.6, L * 0.78) if kind == "narrow" else (7.5, L * 0.82)
    for side in (78.0, 282.0):
        rows = np.abs(th - side) < (0.30 / R) * 57.3 / 2
        for xw in np.arange(wx0, wx1, pitch):
            if any(abs(xw - d) < 0.9 for d in (L * 0.43, L * 0.46)):  # over-wing exits gap
                continue
            cols = np.abs(X - xw) < 0.12
            m = np.outer(rows, cols)
            col[m, :3] = (0.03, 0.035, 0.045)
            rough[m, :3] = 0.05
    # doors (outlines)
    def door(xc, w=0.9, h=1.85, side=78.0):
        tw = (h / R) * 57.3 / 2
        y0 = np.abs(th - (side + 6)) < tw
        x0 = np.abs(X - xc) < w / 2
        ring = np.outer(y0, x0) & ~np.outer(np.abs(th - (side + 6)) < tw - 0.9, np.abs(X - xc) < w / 2 - 0.03)
        col[ring, :3] = (0.45, 0.47, 0.5)
    for side in (78.0, 282.0):
        door(4.6, side=side)
        door(L * 0.83, side=side)
    # cockpit windows (dark, glossy): windshield + two side panes per side
    for side, sgn in ((50.0, 1), (310.0, -1)):
        for (cx, w, dth, hh) in ((2.05, 0.42, -16, 9.5), (2.62, 0.42, 0, 8.5), (3.15, 0.34, 9, 7.0)):
            c0 = side + sgn * dth
            m = np.outer(np.abs(th - c0) < hh, np.abs(X - cx) < w / 2)
            col[m, :3] = (0.012, 0.016, 0.02)
            rough[m, :3] = 0.03
    # nose radome slightly darker grey
    col[:, X < 1.0, :3] *= 0.92
    return image_from_array("livery_col", col[::1]), image_from_array("livery_rough", rough)


def airliner(name="jet", kind="narrow", gear=True, xray=False):
    """Build a complete airliner. Returns the root empty. Nose at origin, flying toward −X."""
    root = empty(name)
    if kind == "narrow":
        L, R, span, rc, tc, sweep, wx, wz, ey, es = 37.6, 1.98, 17.1, 6.3, 1.55, 27, 13.0, -1.25, 5.75, 0.95
    else:
        L, R, span, rc, tc, sweep, wx, wz, ey, es = 73.9, 3.1, 32.0, 12.5, 2.4, 31, 25.0, -2.0, 9.6, 1.65
    col, rough = livery_textures(L, kind)
    paint = textured_mat("livery_" + name, col, rough, coat=0.6)
    if xray:
        paint = xray_mat()
    fus = fuselage(name + "_fus", L, R, paint, root)
    wing_m = mat("wing_paint", (0.74, 0.75, 0.77), 0.32, coat=0.3) if not xray else paint
    # wings (low-wing, dihedral 5°)
    for sgn in (1, -1):
        secs = []
        n = 8
        for k in range(n + 1):
            f = k / n
            yy = sgn * (R * 0.75 + f * (span - R * 0.75))
            chord = rc + (tc - rc) * f ** 0.9
            if f < 0.3:  # trailing-edge kink (yehudi)
                chord = rc + (rc * 0.62 - rc) * (f / 0.3)
                chord = max(chord, rc * 0.62) + (rc - rc * 0.62) * (1 - f / 0.3) ** 2 * 0
            x = wx + abs(yy - sgn * R * 0.75) * math.tan(math.radians(sweep))
            z = wz + abs(yy) * math.tan(math.radians(5))
            secs.append((Vector((x, yy, z)), chord, 0.14 - 0.04 * f, -1.5 * f, False))
        lofted_surface(f"{name}_wing{sgn}", secs, wing_m, root)
        # sharklet / winglet
        tip = secs[-1][0]
        wl = [(Vector((tip.x + 0.1, tip.y, tip.z)), tc * 0.95, 0.09, 0, True),
              (Vector((tip.x + 1.4, tip.y + sgn * 0.25, tip.z + (2.4 if kind == "narrow" else 0.6))), tc * 0.45, 0.08, 0, True)]
        lofted_surface(f"{name}_winglet{sgn}", wl, wing_m, root)
        # horizontal stabiliser
        hs = []
        hx, hspan, hrc, htc = (L * 0.865, 6.2, 3.6, 1.3) if kind == "narrow" else (L * 0.86, 10.6, 6.4, 2.2)
        for k in range(5):
            f = k / 4
            yy = sgn * (0.3 + f * hspan)
            x = hx + f * hspan * math.tan(math.radians(30))
            hs.append((Vector((x, yy, R * 0.55 + f * 0.5)), hrc + (htc - hrc) * f, 0.1, 0, False))
        lofted_surface(f"{name}_hstab{sgn}", hs, wing_m, root)
        # engine + pylon
        nx = wx - (2.6 if kind == "narrow" else 4.6)
        nz = wz + ey * math.tan(math.radians(5)) - (1.35 if kind == "narrow" else 2.25)
        n_root = nacelle(f"{name}_eng{sgn}", root, (nx, sgn * ey, nz), es)
        pyl = mat("pylon", (0.8, 0.81, 0.82), 0.3, coat=0.4) if not xray else paint
        bpy.ops.mesh.primitive_cube_add(size=1)
        p = bpy.context.object
        p.scale = (3.4 * es, 0.25 * es, 0.9 * es)
        p.location = (nx + 2.6 * es, sgn * ey, nz + 1.15 * es)
        p.data.materials.append(pyl)
        p.parent = root
    # wing-to-body / belly fairing
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=48, ring_count=24)
    bf = bpy.context.object
    bf.scale = (rc * 1.25, R * 0.92, R * 0.55)
    bf.location = (wx + rc * 0.45, 0, -R * 0.62)
    bf.data.materials.append(mat("belly", (0.55, 0.57, 0.6), 0.35, coat=0.4) if not xray else paint)
    bpy.ops.object.shade_smooth()
    bf.parent = root
    # vertical fin
    fx, fh, frc, ftc = (L * 0.79, 5.9, 5.6, 1.9) if kind == "narrow" else (L * 0.8, 9.2, 9.6, 3.2)
    fin_m = mat("fin_" + name, (0.07, 0.13, 0.22), 0.3, coat=0.6) if not xray else paint
    fs = []
    for k in range(5):
        f = k / 4
        fs.append((Vector((fx + f * fh * math.tan(math.radians(36)), 0, R * 0.62 + f * fh)), frc + (ftc - frc) * f, 0.1, 0, True))
    lofted_surface(f"{name}_fin", fs, fin_m, root)
    if gear:
        zg = -R - (2.25 if kind == "narrow" else 3.2)
        landing_gear(root, 5.0 if kind == "narrow" else 8.5, 0, -R * 0.6, zg, 2, 0.4 if kind == "narrow" else 0.6, name + "_ng")
        for sgn in (1, -1):
            landing_gear(root, wx + rc * 0.62, sgn * (3.8 if kind == "narrow" else 5.5), wz + 0.2, zg,
                         2 if kind == "narrow" else 3, 0.62 if kind == "narrow" else 0.68, f"{name}_mg{sgn}")
        root["ground_offset"] = -zg
    root["length"] = L
    root["wing_x"] = wx
    root["radius"] = R
    return root


def xray_mat(color=(0.55, 0.8, 1.0)):
    """Ghost skin: Fresnel rim glow, mostly transparent."""
    m = bpy.data.materials.get("xray")
    if m:
        return m
    m = bpy.data.materials.new("xray")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    fr = nt.nodes.new("ShaderNodeLayerWeight")
    fr.inputs["Blend"].default_value = 0.35
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    em.inputs["Strength"].default_value = 3.0
    mix = nt.nodes.new("ShaderNodeMixShader")
    pw = nt.nodes.new("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = 1.2
    nt.links.new(fr.outputs["Facing"], pw.inputs[0])
    nt.links.new(pw.outputs[0], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    return m


# ----------------------------------------------------------------- environment
def sky(elev=8.0, rot=200.0, strength=1.0, kind="MULTIPLE_SCATTERING", sun_disc=True, air=1.0, aerosol=1.0):
    w = bpy.data.worlds.new("World")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    s = nt.nodes.new("ShaderNodeTexSky")
    s.sky_type = kind
    s.sun_elevation = math.radians(elev)
    s.sun_rotation = math.radians(rot)
    s.sun_disc = sun_disc
    s.air_density = air
    s.aerosol_density = aerosol
    nt.links.new(s.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength
    return s


def flat_world(color=(0.0, 0.0, 0.0), strength=1.0):
    w = bpy.data.worlds.new("World")
    bpy.context.scene.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (*color, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = strength
    return w


def sun(elev=8.0, rot=200.0, energy=4.0, color=(1.0, 0.86, 0.68), angle=0.6):
    d = bpy.data.lights.new("sun", "SUN")
    d.energy = energy
    d.color = color
    d.angle = math.radians(angle)
    o = bpy.data.objects.new("sun", d)
    bpy.context.scene.collection.objects.link(o)
    # sun direction from elevation/azimuth (Blender sky: rotation about Z, 0 = +Y?)
    o.rotation_euler = (math.radians(90 - elev), 0, math.radians(rot + 90))
    return o


def area_light(name, loc, rot, size, energy, color=(1, 1, 1), shape="RECTANGLE", size_y=None):
    d = bpy.data.lights.new(name, "AREA")
    d.energy = energy
    d.color = color
    d.shape = shape
    d.size = size
    if size_y:
        d.size_y = size_y
    o = bpy.data.objects.new(name, d)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = rot
    o.visible_camera = False
    return o


def runway_textures(length=600.0, width=45.0, tex_w=8192, tex_h=1024):
    """asphalt runway colour + roughness maps (u along runway, v across)."""
    rs = np.random.RandomState(3)
    W, H = tex_w, tex_h
    base = 0.11 + 0.025 * rs.standard_normal((H // 8, W // 8)).astype(np.float32)
    base = np.kron(base, np.ones((8, 8), np.float32))
    base += 0.02 * rs.standard_normal((H, W)).astype(np.float32)
    col = np.zeros((H, W, 4), np.float32)
    col[..., 0] = base * 0.98
    col[..., 1] = base * 0.98
    col[..., 2] = base * 1.02
    col[..., 3] = 1
    X = (np.arange(W) + 0.5) / W * length
    Y = ((np.arange(H) + 0.5) / H - 0.5) * width
    paint = np.zeros((H, W), bool)
    # centre-line dashes 30 m / 20 m gap, 0.9 m wide
    paint |= np.outer(np.abs(Y) < 0.45, ((X % 50) < 30) & (X > 80))
    # edge lines
    paint |= np.outer(np.abs(np.abs(Y) - 21.5) < 0.45, np.ones(W, bool))
    # threshold piano keys
    for k in range(8):
        yc = (k - 3.5) * 2.6 + (np.sign(k - 3.5) * 2.0)
        paint |= np.outer(np.abs(Y - yc) < 0.9, (X > 6) & (X < 36))
    # touchdown zone bars
    paint |= np.outer((np.abs(np.abs(Y) - 9) < 1.5), (X > 150) & (X < 172))
    # tyre marks
    marks = np.outer(np.exp(-((np.abs(Y) - 3.8) ** 2) / 1.5), np.clip((X - 140) / 40, 0, 1) * np.clip((400 - X) / 100, 0, 1))
    col[..., :3] *= (1 - 0.55 * marks[..., None])
    col[paint, :3] = (0.78, 0.78, 0.76)
    rough = np.full((H, W, 4), 0.82, np.float32)
    rough[paint, :3] = 0.6
    rough[..., 3] = 1
    return image_from_array("runway_col", col), image_from_array("runway_rough", rough)


def runway(length=600.0, width=45.0, x0=-40.0):
    col, rough = runway_textures(length, width)
    m = textured_mat("runway", col, rough, coat=0.0)
    verts = [(x0, -width / 2, 0), (x0 + length, -width / 2, 0), (x0 + length, width / 2, 0), (x0, width / 2, 0)]
    o = obj_from_mesh("runway", verts, [(0, 1, 2, 3)], m, uvs=[(0, 0), (1, 0), (1, 1), (0, 1)], smooth=False)
    o.location.z = 0.01
    # surrounding grass + shoulders
    g = bpy.data.materials.new("grass")
    g.use_nodes = True
    nt = g.node_tree
    b = nt.nodes["Principled BSDF"]
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 0.08
    noise.inputs["Detail"].default_value = 8
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.08, 0.11, 0.035, 1)
    ramp.color_ramp.elements[1].color = (0.2, 0.22, 0.08, 1)
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.95
    bpy.ops.mesh.primitive_plane_add(size=6000, location=(0, 0, -0.02))
    bpy.context.object.data.materials.append(g)
    # runway edge lights
    lm = emissive("edge_light", (1.0, 0.85, 0.6), 30)
    for x in np.arange(x0, x0 + length, 60):
        for yy in (-width / 2 - 1.5, width / 2 + 1.5):
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.18, location=(x, yy, 0.35), segments=12, ring_count=6)
            bpy.context.object.data.materials.append(lm)
    return o


def camera(loc, look_at, lens=50, name="cam", dof=None, fstop=4.0, sensor=36):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = sensor
    cd.clip_end = 20000
    o = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    d = Vector(look_at) - Vector(loc)
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    if dof:
        cd.dof.use_dof = True
        cd.dof.focus_distance = dof
        cd.dof.aperture_fstop = fstop
    bpy.context.scene.camera = o
    return o


def look(o, target):
    d = Vector(target) - o.location
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def render(path, samples=None, res=None, frame=None):
    sc = bpy.context.scene
    if samples:
        sc.cycles.samples = samples
    if res:
        sc.render.resolution_x, sc.render.resolution_y = res
    if frame is not None:
        sc.frame_set(frame)
    sc.render.filepath = path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.render.render(write_still=True)


def atmosphere(density=0.00025, color=(0.85, 0.9, 1.0), anisotropy=0.6, size=(6000, 6000, 400), center=(0, 0, 0)):
    """Finite haze layer (box volume): aerial perspective + soft sun shafts near the ground."""
    m = bpy.data.materials.new("haze")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    v = nt.nodes.new("ShaderNodeVolumePrincipled")
    v.inputs["Density"].default_value = density
    v.inputs["Color"].default_value = (*color, 1)
    v.inputs["Anisotropy"].default_value = anisotropy
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(v.outputs[0], out.inputs["Volume"])
    bpy.ops.mesh.primitive_cube_add(size=1, location=(center[0], center[1], center[2] + size[2] / 2 - 5))
    o = bpy.context.object
    o.scale = size
    o.data.materials.append(m)
    o.name = "haze"
    o.visible_shadow = False
    bpy.context.scene.cycles.volume_bounces = 0
    bpy.context.scene.cycles.volume_step_rate = 8.0
    return o


def treeline(dist=1400.0, n=420, seed=5, spread=(-3000, 3000), axis="x"):
    """Distant dark treeline / low buildings ring for a horizon."""
    rs = np.random.RandomState(seed)
    m = mat("treeline", (0.035, 0.045, 0.03), 0.9)
    mb = mat("far_bldg", (0.25, 0.26, 0.28), 0.7)
    verts, faces, vb, fb = [], [], [], []
    for k in range(n):
        a = spread[0] + (spread[1] - spread[0]) * k / n + rs.uniform(-4, 4)
        h = rs.uniform(9, 22)
        w = rs.uniform(10, 24)
        d = dist + rs.uniform(-60, 60)
        tgt_v, tgt_f = (vb, fb) if rs.rand() < 0.08 else (verts, faces)
        if tgt_v is vb:
            h = rs.uniform(12, 40)
        i0 = len(tgt_v)
        for (x, y, z) in ((a, d, 0), (a + w, d, 0), (a + w, d, h), (a, d, h), (a, d + 20, 0), (a + w, d + 20, 0), (a + w, d + 20, h), (a, d + 20, h)):
            tgt_v.append((x, y, z) if axis == "x" else (y, x, z))
        tgt_f += [(i0, i0 + 1, i0 + 2, i0 + 3), (i0 + 3, i0 + 2, i0 + 6, i0 + 7), (i0 + 1, i0 + 5, i0 + 6, i0 + 2), (i0, i0 + 3, i0 + 7, i0 + 4)]
    obj_from_mesh("trees", verts, faces, m, smooth=False)
    if vb:
        obj_from_mesh("bldgs", vb, fb, mb, smooth=False)


def place_pitched(root, pitch_deg, gear_x=None, ground=0.0):
    """Pitch an airliner nose-up about its main gear, keeping the main wheels on the ground."""
    import mathutils
    gx = gear_x if gear_x is not None else root["wing_x"] + 3.9
    g = root["ground_offset"]
    th = math.radians(pitch_deg)
    root.rotation_euler = (0, th, 0)
    # main-gear contact point in local space: (gx, 0, -g); world z after rotation about Y
    p = Matrix.Rotation(th, 3, "Y") @ Vector((gx, 0, -g))
    root.location.z = ground - p.z


def landing_lights(root, strength=60.0):
    m = emissive("landing_light", (1.0, 0.95, 0.85), strength)
    pts = [(4.6, 0, -2.6), (13.2, 3.0, -1.6), (13.2, -3.0, -1.6)]
    for k, (x, y, z) in enumerate(pts):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.14, location=(x, y, z), segments=16, ring_count=8)
        o = bpy.context.object
        o.data.materials.append(m)
        o.parent = root
        d = bpy.data.lights.new(f"ll{k}", "SPOT")
        d.energy = 8000
        d.spot_size = math.radians(30)
        d.color = (1.0, 0.95, 0.85)
        lo = bpy.data.objects.new(f"ll{k}", d)
        bpy.context.scene.collection.objects.link(lo)
        lo.location = (x - 0.2, y, z)
        lo.rotation_euler = (0, math.pi / 2 - 0.06, 0)
        lo.parent = root
