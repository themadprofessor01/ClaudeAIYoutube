"""Render every CG plate for the film.

usage: python3 blender/shots.py [--draft] key [key ...]     (or "all")
Writes renders/<key>.png (1920×1080 unless the shot says otherwise).
Conventions: airliner nose at its local origin pointing −X; +Z up; sun azimuth = direction the
sun shines FROM (0 = +X, 90 = +Y).
"""
import sys, os, math, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jetlib import *
from props import *

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "renders")
DRAFT = "--draft" in sys.argv
if DRAFT:
    OUT = OUT + "_draft"
SHOTS = {}


def shot(samples=40, res=(1920, 1080)):
    def deco(fn):
        SHOTS[fn.__name__] = (fn, samples, res)
        return fn
    return deco


def light(elev, az, sky_strength=0.5, sun_energy=3.0, sun_color=(1.0, 0.86, 0.68), haze=None, haze_color=(0.95, 0.85, 0.75), air=1.0, aerosol=1.0):
    sky(elev=elev, rot=90 - az, strength=sky_strength, air=air, aerosol=aerosol)
    sun(elev=elev, rot=az, energy=sun_energy, color=sun_color)
    if haze:
        atmosphere(haze, haze_color)


def golden(az=200, elev=5, haze=0.0004):
    light(elev, az, 0.45, 3.0, (1.0, 0.82, 0.62), haze)


def night_studio(top=(0.012, 0.03, 0.07), strength=1.0):
    """dark blue gradient world for X-ray shots (graphics read clearly)."""
    w = bpy.data.worlds.new("World")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.004, 1)
    ramp.color_ramp.elements[1].position = 0.75
    ramp.color_ramp.elements[1].color = (*top, 1)
    nt.links.new(tc.outputs["Window"], sep.inputs[0])
    nt.links.new(sep.outputs["Y"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength


def jet_on_runway(x=60, name="jet", kind="narrow", xray=False, lights=False):
    j = airliner(name, kind, gear=True, xray=xray)
    j.location = (x, 0, j["ground_offset"])
    if lights:
        landing_lights(j)
    return j


def bat_grid_in(root, x0, x1, y0, y1, z0, z1, mod=(0.9, 0.6, 0.45), lit=1.0, name="bm"):
    """fill a box region of an aircraft (local coords) with battery modules (one merged mesh)."""
    nx = max(1, int((x1 - x0) / (mod[0] + 0.08)))
    ny = max(1, int((y1 - y0) / (mod[1] + 0.06)))
    nz = max(1, int((z1 - z0) / (mod[2] + 0.04)))
    cs = [(x0 + (i + 0.5) * (x1 - x0) / nx, y0 + (j + 0.5) * (y1 - y0) / ny, z0 + l * (z1 - z0) / nz)
          for i in range(nx) for j in range(ny) for l in range(nz)]
    module_field(name, cs, mod, parent=root, lit=lit)
    return len(cs)


# =================================================================== S1 — HOOK
@shot(48)
def a1_tele():
    """600 mm telephoto straight down the runway; jet at the far end facing camera, landing lights on."""
    light(5, 60, 0.4, 3.0, (1.0, 0.8, 0.6), 0.00006, (0.95, 0.85, 0.75))
    runway(length=1600, x0=-40)
    treeline(2200, axis="x")
    j = jet_on_runway(900, lights=True)
    camera((-700, 0.0, 3.2), (900, 0, 3.6), lens=700, dof=1600, fstop=8)


@shot(40)
def a2_pass():
    """Ground level at the runway edge, jet thundering past (blurred in comp)."""
    golden(az=200, elev=6, haze=0.0003)
    runway(length=1200, x0=-300)
    treeline(1500, axis="x")
    j = jet_on_runway(-12)
    camera((6, -78, 1.4), (2, 0, 4.0), lens=55, dof=78, fstop=5.6)


@shot(40)
def a3_rotation():
    """Low side angle, nose lifting at rotation, backlit by the low sun."""
    golden(az=100, elev=5, haze=0.0004)
    runway(length=1200, x0=-400)
    treeline(1300, axis="x")
    j = airliner("jet")
    j.location = (0, 0, 0)
    place_pitched(j, 9)
    camera((20, -70, 1.0), (16, 0, 5), lens=60, dof=70, fstop=5.6)


@shot(48)
def a4_charge():
    """macro: EV charge port glowing cyan, plug inserted (night)."""
    flat_world((0.004, 0.005, 0.008))
    paint = mat("car_paint", (0.03, 0.035, 0.045), 0.18, metal=0.6, coat=1.0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0.6, 0), segments=96, ring_count=48)
    body = bpy.context.object
    body.scale = (3.0, 0.7, 1.2)
    body.data.materials.append(paint)
    bpy.ops.object.shade_smooth()
    ring = emissive("port_ring", CYAN, 25)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.085, minor_radius=0.007, location=(0.0, -0.105, 0.0), rotation=(math.pi / 2, 0, 0))
    bpy.context.object.data.materials.append(ring)
    cyl("port", 0.08, 0.02, (0, -0.1, 0), mat("port_black", (0.01, 0.01, 0.01), 0.5), rot=(math.pi / 2, 0, 0))
    plug = mat("plug", (0.05, 0.05, 0.055), 0.4)
    cyl("plug_head", 0.072, 0.16, (0, -0.2, 0), plug, rot=(math.pi / 2, 0, 0))
    cyl("plug_handle", 0.05, 0.4, (0.0, -0.38, -0.14), plug, rot=(1.1, 0, 0))
    cyl("cable", 0.02, 1.2, (0.0, -0.57, -0.7), mat("cable", (0.02, 0.02, 0.02), 0.6), rot=(0.4, 0, 0))
    area_light("street", (1.5, -2, 2.5), (0.7, 0, 0.6), 2, 500, (1.0, 0.75, 0.5))
    area_light("rim", (-2, 0.2, 1), (0, -1.2, 0), 1, 300, (0.4, 0.6, 1.0))
    softbox_strip("refl", (-0.8, -1.5, 0.8), (0, 0, 0.6), 0.6, 0.05, 8, (1, 0.9, 0.8))
    camera((0.45, -0.9, 0.12), (0, -0.1, 0), lens=85, dof=0.95, fstop=2.8)


@shot(40)
def a5_window():
    """view from a cabin window: wing + engine, runway blurring below (takeoff)."""
    golden(az=160, elev=7, haze=0.0005)
    runway(length=1200, x0=-500)
    treeline(1300, axis="x")
    j = jet_on_runway(0)
    # camera at a left-side window behind the wing, looking out toward the wing/engine
    camera((24.0, 2.1, j.location.z + 0.35), (11.0, 11.0, j.location.z - 0.9), lens=24, dof=12, fstop=4)


@shot(48)
def a6_exhaust():
    """engine rear close-up: core nozzle + plug, dusk light (heat shimmer added in comp)."""
    golden(az=170, elev=4, haze=0.0005)
    runway(length=800, x0=-400)
    j = jet_on_runway(0)
    camera((19.0, -9.5, j.location.z - 2.2), (12.5, -5.75, j.location.z - 2.4), lens=50, dof=7.5, fstop=2.8)


def _profile_sky(xray=False, batteries=False, sag=False):
    if xray:
        night_studio()
    else:
        light(18, 120, 0.35, 3.5, (1.0, 0.93, 0.85))
    j = airliner("jet", gear=False, xray=xray)
    j.location = (0, 0, 2000)
    if xray and not batteries:
        fuel_tanks(j, "narrow", 1.0, strength=3.5)
    if batteries:
        n = bat_grid_in(j, 5, 31, -1.3, 1.3, -1.7, 1.2, lit=1.0)
        if sag:
            j.location.z -= 0.6
            j.rotation_euler = (0, math.radians(-1.0), 0)
    if xray:
        camera((-8, -46, 2024), (17, 0, 1999), lens=35)
    else:
        camera((19, -90, 2000), (19, 0, 2000), lens=50)


@shot(40)
def a7_profile():
    _profile_sky()


@shot(48)
def a8_xray_fuel():
    _profile_sky(xray=True)


@shot(48)
def a9_xray_batt():
    _profile_sky(xray=True, batteries=True, sag=True)


# =================================================================== S2 — ELECTRIC PLANES EXIST
def grass_field(color=(0.07, 0.13, 0.04)):
    m = bpy.data.materials.new("grassfield")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 40
    n.inputs["Detail"].default_value = 12
    r = nt.nodes.new("ShaderNodeValToRGB")
    r.color_ramp.elements[0].color = (color[0] * 0.6, color[1] * 0.6, color[2] * 0.6, 1)
    r.color_ramp.elements[1].color = (color[0] * 1.6, color[1] * 1.5, color[2] * 1.2, 1)
    nt.links.new(n.outputs["Fac"], r.inputs["Fac"])
    nt.links.new(r.outputs["Color"], b.inputs["Base Color"])
    bm = nt.nodes.new("ShaderNodeBump")
    bm.inputs["Strength"].default_value = 0.8
    nt.links.new(n.outputs["Fac"], bm.inputs["Height"])
    nt.links.new(bm.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = 0.9
    bpy.ops.mesh.primitive_plane_add(size=6000, location=(0, 0, 0))
    bpy.context.object.data.materials.append(m)


@shot(40)
def b1_trainer_field():
    light(9, 60, 0.3, 3.0, (1.0, 0.9, 0.75), 0.0002, (0.9, 0.92, 1.0))
    grass_field()
    treeline(700, axis="x")
    p = small_plane("tr", "trainer")
    p.location = (0, 0, p["ground_offset"])
    p.rotation_euler = (0, 0, math.radians(-28))
    camera((-11, -9, 1.6), (2.0, 0, 0.6), lens=40, dof=14, fstop=2.8)


@shot(40)
def b2_trainer_air():
    light(30, 200, 0.35, 3.5, (1.0, 0.95, 0.88), 0.00004, (0.85, 0.9, 1.0))
    terrain(subdiv=160)
    p = small_plane("tr", "trainer")
    p.location = (0, 0, 450)
    p.rotation_euler = (math.radians(-8), 0, 0)
    camera((-9, -10, 455), (2.5, 0, 450), lens=40)


@shot(48)
def b3_trainer_xray():
    light(30, 200, 0.35, 3.5, (1.0, 0.95, 0.88), 0.00004, (0.85, 0.9, 1.0))
    terrain(subdiv=160)
    p = small_plane("tr", "trainer", xray=True)
    p.location = (0, 0, 450)
    battery_module("bA", (0.5, 0, -0.25), parent=p, w=0.6, d=0.5, h=0.35)
    battery_module("bB", (2.6, 0, -0.3), parent=p, w=0.6, d=0.5, h=0.3)
    cyl("mot", 0.18, 0.4, (0.1, 0, 0), mat("copper", (0.95, 0.45, 0.25), 0.25, metal=1.0), rot=(0, math.pi / 2, 0), parent=p)
    camera((-9, -10, 455), (2.5, 0, 450), lens=40)


@shot(40)
def b4_seaplane():
    light(12, 250, 0.35, 3.0, (1.0, 0.9, 0.75), 0.00015, (0.85, 0.9, 1.0))
    ocean(color=(0.01, 0.05, 0.06), wave_scale=1.5)
    treeline(700, n=300, axis="x", seed=3)
    treeline(760, n=300, axis="x", seed=4)
    p = small_plane("sea", "seaplane", livery=(0.92, 0.9, 0.86), accent=(0.75, 0.12, 0.1))
    p.location = (0, 0, p["ground_offset"] + 1.0)
    p.rotation_euler = (0, math.radians(6), math.radians(-20))
    camera((-26, -30, 0.8), (3, 0, 2.2), lens=45, dof=40, fstop=4)


@shot(40)
def b5_racer():
    light(22, 230, 0.35, 3.5, (1.0, 0.95, 0.9), 0.0001, (0.85, 0.9, 1.0))
    ocean(color=(0.01, 0.05, 0.08), wave_scale=2.0)
    p = small_plane("rc", "racer", livery=(0.03, 0.08, 0.25), accent=(0.9, 0.9, 0.92))
    p.location = (0, 0, 25)
    p.rotation_euler = (math.radians(-10), 0, 0)
    camera((-10, -9, 29), (3.0, 0, 25), lens=40)


@shot(48)
def b6_solar():
    light(2.5, 260, 0.5, 2.5, (1.0, 0.6, 0.35), 0.0002, (1.0, 0.7, 0.5))
    ocean(color=(0.01, 0.03, 0.05), wave_scale=0.8)
    p = small_plane("sol", "solar", livery=(0.92, 0.92, 0.94), accent=(0.9, 0.9, 0.92))
    p.location = (0, 0, 300)
    camera((-45, -62, 322), (8, 0, 300), lens=32)


@shot(48)
def b7_solar_pod():
    light(2.5, 260, 0.5, 2.5, (1.0, 0.6, 0.35), 0.0002, (1.0, 0.7, 0.5))
    ocean(color=(0.01, 0.03, 0.05), wave_scale=0.8)
    p = small_plane("sol", "solar")
    p.location = (0, 0, 300)
    camera((-4, -12, 301.0), (3.0, 0, 300.2), lens=50, dof=12.5, fstop=4)


def _hangar_a320(lights=(1, 1, 1)):
    flat_world((0.01, 0.01, 0.012))
    hangar(lights_on=lights)
    j = airliner("jet")
    j.location = (-15, 0, j["ground_offset"])
    j.rotation_euler = (0, 0, math.radians(180 + 25))
    return j


@shot(40)
def b8_hangar0():
    _hangar_a320((0, 0, 0.0))
    area_light("work", (-20, -10, 6), (0.8, 0, -0.6), 3, 800, (1.0, 0.8, 0.6))
    camera((22, -26, 1.8), (-2, 0, 5), lens=24)


@shot(40)
def b8_hangar1():
    _hangar_a320((0, 1, 0))
    camera((22, -26, 1.8), (-2, 0, 5), lens=24)


@shot(40)
def b8_hangar2():
    _hangar_a320((1, 1, 1))
    camera((22, -26, 1.8), (-2, 0, 5), lens=24)


# =================================================================== S3 — ENERGY
@shot(48)
def c1_xray_runway():
    golden(az=200, elev=2, haze=0.0003)
    runway(length=1200, x0=-500)
    treeline(1300, axis="x")
    j = jet_on_runway(0, xray=True)
    fuel_tanks(j, "narrow", 1.0, strength=3.5)
    camera((19, -62, 3.0), (19, 0, 3.0), lens=45)


@shot(40)
def c2_chase():
    light(8, 230, 0.4, 3.0, (1.0, 0.84, 0.66), 0.00008)
    runway(length=1600, x0=-1200)
    treeline(1500, axis="x")
    j = jet_on_runway(0)
    camera((62, -14, 16), (-30, 0, 2), lens=35)


@shot(64)
def c3_engine_stand():
    flat_world((0.004, 0.004, 0.005))
    lab_floor(80, 0.15)
    e = engine_cutaway("e", open_frac=0.0, glow=False)
    e.location = (0, 0, 1.45)
    box("stand", (3.6, 0.6, 0.25), (2.4, 0, 0.12), mat("stand", (0.06, 0.06, 0.065), 0.4, metal=0.6))
    area_light("key", (3, -5, 5), (0.7, 0, 0.5), 4, 1400)
    area_light("rim", (-3, 3, 3), (-0.9, 0, -2.4), 3, 900, (0.6, 0.75, 1))
    camera((-3.0, -6.2, 2.0), (2.0, 0, 1.35), lens=35, dof=7.2, fstop=5.6)


@shot(64)
def c4_engine_cut():
    flat_world((0.004, 0.004, 0.005))
    lab_floor(80, 0.15)
    e = engine_cutaway("e", open_frac=1.0, glow=True)
    e.location = (0, 0, 1.45)
    box("stand", (3.6, 0.6, 0.25), (2.4, 0, 0.12), mat("stand", (0.06, 0.06, 0.065), 0.4, metal=0.6))
    area_light("key", (3, -5, 5), (0.7, 0, 0.5), 4, 1100)
    area_light("rim", (-3, 3, 3), (-0.9, 0, -2.4), 3, 700, (0.6, 0.75, 1))
    camera((-1.6, -6.6, 2.4), (2.3, 0, 1.3), lens=38, dof=7.4, fstop=5.6)


@shot(64)
def c5_engine_macro():
    flat_world((0.004, 0.004, 0.005))
    lab_floor(80, 0.15)
    e = engine_cutaway("e", open_frac=1.0, glow=True)
    e.location = (0, 0, 1.45)
    area_light("key", (3, -5, 5), (0.7, 0, 0.5), 4, 900)
    camera((2.1, -1.55, 1.75), (2.75, 0, 1.45), lens=40, dof=1.65, fstop=2.8)


@shot(32)
def c6_town_off():
    flat_world((0.002, 0.003, 0.006))
    town_lights(0.0)
    camera((0, -1300, 330), (0, 0, 0), lens=40)


@shot(32)
def c7_town_on():
    flat_world((0.002, 0.003, 0.006))
    town_lights(1.0)
    camera((0, -1300, 330), (0, 0, 0), lens=40)


@shot(48)
def c8_climb():
    light(10, 200, 0.6, 4.0, (1.0, 0.9, 0.75))
    cloud_layer(z=1000, thickness=240, density=0.08)
    terrain(z=0, subdiv=120)
    j = airliner("jet", gear=False)
    j.location = (0, 0, 1220)
    j.rotation_euler = (0, math.radians(12), 0)
    camera((30, -95, 1205), (18, 0, 1222), lens=55)


@shot(40)
def c9_cruise():
    s = sky(elev=35, rot=90 - 150, strength=0.6)
    s.altitude = 11000
    sun(elev=35, rot=150, energy=4.0, color=(1, 0.97, 0.94))
    j = airliner("jet", gear=False)
    j.location = (0, 0, 0)
    camera((-14, -58, 6), (18, 0, 0), lens=45)


@shot(48)
def c10_tanks_xray():
    night_studio()
    j = airliner("jet", gear=False, xray=True)
    j.location = (0, 0, 2000)
    fuel_tanks(j, "narrow", 1.0, strength=3.5)
    camera((-12, -42, 2022), (17, 0, 1999), lens=35)


def _ev_grid(height, lens=35, with_777=False):
    light(35, 130, 0.25, 1.6, (1, 0.96, 0.9), 0.00005)
    apron(8000, color=(0.2, 0.2, 0.2))
    ev_battery_grid(60, 50, origin=(-66, -75))
    if with_777:
        w = airliner("w", "wide")
        w.location = (-10, 10, w["ground_offset"])
        w.rotation_euler = (0, 0, math.radians(30))
    camera((0, -height * 0.35, height), (0, 0, 0), lens=lens)


@shot(32)
def c11_grid_low():
    _ev_grid(70, 35)


@shot(32)
def c12_grid_high():
    _ev_grid(260, 35)


@shot(40)
def c13_grid_777():
    _ev_grid(420, 35, with_777=True)


# =================================================================== S4 — FUEL vs BATTERY (the Energy Lab)
def lab_set(scale_on=True, key=120, strips=True):
    flat_world((0.0, 0.0, 0.0))
    lab_floor(60, 0.1)
    lab_backdrop()
    tops = None
    if scale_on:
        s, tops = scale_balance()
        s.scale = (0.6, 0.6, 0.6)
        tops = [(x * 0.6, z * 0.6) for x, z in tops]
        fuel_cylinder("fc", (tops[0][0], 0, tops[0][1]), height=0.25, radius=0.045, level=0.8)
        cell_bundle("cb", (tops[1][0], 0, tops[1][1]))
    if strips:
        softbox_strip("sbL", (-0.9, 1.2, 0.9), (0, 0, 0.5), 0.08, 1.4, 6, (1, 0.85, 0.7))
        softbox_strip("sbR", (0.9, 1.2, 0.9), (0, 0, -0.5), 0.08, 1.4, 6, (0.75, 0.88, 1))
    area_light("key", (0, -0.6, 2.2), (0.25, 0, 0), 1.5, key)
    area_light("rimL", (-2, 1.5, 1.2), (-1.2, 0, -2.5), 1, 120, (1, 0.6, 0.25))
    area_light("rimR", (2, 1.5, 1.2), (-1.2, 0, 2.5), 1, 120, (0.3, 0.7, 1))
    return tops


@shot(64)
def d1_lab_wide():
    lab_set()
    camera((0.9, -2.4, 0.9), (0, 0, 0.36), lens=35, dof=2.6, fstop=5.6)


@shot(64)
def d2_fuel_macro():
    tops = lab_set()
    x, z = tops[0]
    camera((x - 0.12, -0.38, z + 0.14), (x, 0, z + 0.11), lens=85, dof=0.4, fstop=2.8)


@shot(64)
def d3_cells_macro():
    tops = lab_set()
    x, z = tops[1]
    camera((x + 0.1, -0.3, z + 0.13), (x, 0, z + 0.035), lens=85, dof=0.33, fstop=2.8)


@shot(64)
def d4_balanced():
    lab_set()
    camera((0, -1.6, 0.6), (0, 0, 0.38), lens=50, dof=1.62, fstop=5.6)


@shot(64, (1920, 4320))
def d5_columns_tall():
    """Tall frame for the tilt-up: amber column (12 kWh) vs cyan stub (0.25 kWh), 1 kWh = 0.25 m."""
    tops = lab_set(key=90, strips=False)
    k = 0.25
    energy_column("amber", (tops[0][0], 0, tops[0][1] + 0.26), 12 * k, 0.05, AMBER, 6)
    energy_column("cyan", (tops[1][0], 0, tops[1][1] + 0.08), 0.25 * k, 0.05, CYAN, 6)
    light_ruler(0.62, 0.3, 3.6, k)
    cam = camera((0, -7.0, 1.95), (0, 0, 1.95), lens=60, dof=7.0, fstop=11)
    cam.data.sensor_fit = "VERTICAL"
    cam.data.sensor_height = 36


@shot(64, (1920, 4320))
def d5_nocol_tall():
    """same tall frame without the columns (base layer for the rising-light reveal)."""
    tops = lab_set(key=90, strips=False)
    light_ruler(0.62, 0.3, 3.6, 0.25)
    cam = camera((0, -7.0, 1.95), (0, 0, 1.95), lens=60, dof=7.0, fstop=11)
    cam.data.sensor_fit = "VERTICAL"
    cam.data.sensor_height = 36


@shot(64)
def d6b_columns_heat():
    """useful energy only: amber ≈4.2 kWh, cyan ≈0.23 kWh (same scale as d6)."""
    tops = lab_set(key=90, strips=False)
    k = 0.25
    energy_column("amber", (tops[0][0], 0, tops[0][1] + 0.26), 4.2 * k, 0.05, AMBER, 6)
    energy_column("cyan", (tops[1][0], 0, tops[1][1] + 0.08), 0.225 * k, 0.05, CYAN, 6)
    light_ruler(0.62, 0.3, 3.6, k)
    camera((0, -6.5, 1.6), (0, 0, 1.55), lens=30)


@shot(64)
def d6_columns_wide():
    tops = lab_set(key=90, strips=False)
    k = 0.25
    energy_column("amber", (tops[0][0], 0, tops[0][1] + 0.26), 12 * k, 0.05, AMBER, 6)
    energy_column("cyan", (tops[1][0], 0, tops[1][1] + 0.08), 0.25 * k, 0.05, CYAN, 6)
    light_ruler(0.62, 0.3, 3.6, k)
    camera((0, -6.5, 1.6), (0, 0, 1.55), lens=30)


@shot(64)
def d7_columns_useful():
    """useful energy: amber ≈4 kWh vs cyan ≈0.2 kWh, plus 20 cyan columns stacked to match."""
    tops = lab_set(key=90, strips=False)
    k = 0.25
    energy_column("amber", (tops[0][0], 0, tops[0][1] + 0.26), 4.2 * k, 0.05, AMBER, 6)
    hb = 4.2 * k / 20
    for i in range(20):
        energy_column(f"cy{i}", (tops[1][0], 0, tops[1][1] + 0.08 + i * hb * 1.0 + (0.26 - 0.08) * (i / 19)), hb * 0.9, 0.05, CYAN, 6, core=False)
    light_ruler(0.62, 0.3, 1.6, k)
    camera((0, -3.0, 0.95), (0, 0, 0.85), lens=35, dof=3.0, fstop=8)


@shot(64)
def d8_motor():
    flat_world((0, 0, 0))
    lab_floor(40, 0.1)
    m = motor_section()
    m.location = (0, 0, 1.1)
    m.rotation_euler = (0, 0, math.radians(15))
    area_light("key", (1.5, -3, 3), (0.8, 0, 0.4), 2, 300)
    area_light("rim", (-2, 2, 2), (-0.9, 0, -2.4), 2, 260, (0.3, 0.7, 1))
    camera((0.8, -2.9, 1.6), (0, 0, 1.1), lens=60, dof=3.0, fstop=4)


@shot(64)
def d9_module():
    """battery module: cells + cooling plate + busbars + casing, exploded view."""
    flat_world((0, 0, 0))
    lab_floor(40, 0.1)
    lab_backdrop()
    root = empty("mod", (0, 0, 0.5))
    for i in range(8):
        for j in range(4):
            cell_21700(f"c{i}{j}", ((i - 3.5) * 0.023, (j - 1.5) * 0.023, 0.05), root)
    box("cool", (0.21, 0.11, 0.008), (0, 0, 0.0), mat("alu", (0.75, 0.76, 0.78), 0.25, metal=1.0), root)
    for k in range(4):
        box(f"bus{k}", (0.2, 0.012, 0.002), (0, (k - 1.5) * 0.023, 0.2), mat("busbar", (0.85, 0.5, 0.3), 0.25, metal=1.0), root)
    box("case_lid", (0.23, 0.13, 0.004), (0, 0, 0.29), mat("mod_case", (0.16, 0.17, 0.19), 0.45, metal=0.6), root, bevel=0.002)
    box("case_base", (0.23, 0.13, 0.03), (0, 0, -0.06), mat("mod_case", (0.16, 0.17, 0.19), 0.45, metal=0.6), root, bevel=0.002)
    box("harness", (0.18, 0.004, 0.004), (0, -0.07, 0.24), mat("hv_orange", (1.0, 0.35, 0.02), 0.4), root)
    area_light("key", (0.4, -0.8, 1.4), (0.6, 0, 0.4), 0.8, 60)
    area_light("rim", (-0.6, 0.6, 0.9), (-0.9, 0, -2.4), 0.6, 50, (0.3, 0.7, 1))
    camera((0.3, -0.62, 0.78), (0, 0, 0.6), lens=50, dof=0.75, fstop=5.6)


@shot(48)
def d10_cube():
    flat_world((0.02, 0.02, 0.025))
    hangar(lights_on=(0.6, 1, 0.6))
    fuel_cube("fcube", (0, 0, 0), glow=2.5)
    mannequin("tech", (1.45, -0.35, 0), 2.4)
    camera((-3.4, -5.6, 1.3), (0.2, 0.2, 0.6), lens=40, dof=6.6, fstop=2.8)


def _pallets(n):
    flat_world((0.02, 0.02, 0.025))
    hangar(lights_on=(0.6, 1, 0.6))
    fuel_cube("fcube", (0, 0, 0), glow=2.5)
    mannequin("tech", (-0.9, 0.9, 0), 2.2)
    # wall of 20 pallets behind/right of the cube: 5 wide × 2 deep × 2 high
    pos = []
    for lvl in range(2):
        for d in range(2):
            for i in range(5):
                pos.append((2.0 + i * 1.3, 1.2 + d * 1.1, lvl * 0.95))
    for k in range(n):
        battery_pallet(f"p{k}", pos[k])


for _n in (1, 3, 6, 10, 15, 20):
    def _mk(n=_n):
        def f():
            _pallets(n)
            camera((-3.6, -7.5, 1.6), (3.2, 1.2, 1.0), lens=28, dof=8.5, fstop=5.6)
        f.__name__ = f"d11_pallets{n:02d}"
        return f
    shot(40)(_mk())


@shot(40)
def d12_wall_low():
    _pallets(20)
    camera((1.0, -2.6, 0.25), (3.5, 1.5, 1.6), lens=20, dof=3.0, fstop=4)


def _split_777(fuel_level=None, batt_lit=None, alt=900):
    light(1.5, 140, 0.25, 1.0, (0.7, 0.75, 1.0), 0.00004, (0.6, 0.7, 1.0))
    ocean(color=(0.01, 0.045, 0.07), wave_scale=0.3)
    w = airliner("w", "wide", gear=False, xray=True)
    w.location = (0, 0, alt)
    if fuel_level is not None:
        fuel_tanks(w, "wide", fuel_level, strength=3.5)
    if batt_lit is not None:
        bat_grid_in(w, 10, 60, -2.1, 2.1, -2.8, 1.8, mod=(1.2, 0.8, 0.6), lit=batt_lit)
    camera((28, -64, alt + 30), (37, 0, alt), lens=30)


@shot(40, (960, 1080))
def d13_777_fuel_full():
    _split_777(fuel_level=1.0)


@shot(40, (960, 1080))
def d13_777_fuel_low():
    _split_777(fuel_level=0.3)


@shot(40, (960, 1080))
def d14_777_batt_full():
    _split_777(batt_lit=1.0)


@shot(40, (960, 1080))
def d14_777_batt_empty():
    _split_777(batt_lit=0.05)


@shot(40, (960, 1080))
def d15_land_light():
    golden(az=200, elev=8, haze=0.0003)
    runway(length=1200, x0=-500)
    w = airliner("w", "wide")
    w.location = (0, 0, w["ground_offset"] + 0.4)
    w.rotation_euler = (0, math.radians(4), 0)
    camera((50, -52, 1.6), (34, 0, 5), lens=28)


@shot(40, (960, 1080))
def d15_land_heavy():
    golden(az=200, elev=8, haze=0.0003)
    runway(length=1200, x0=-500)
    w = airliner("w", "wide")
    w.location = (0, 0, w["ground_offset"] - 0.45)
    w.rotation_euler = (0, math.radians(1.5), 0)
    camera((50, -52, 1.6), (34, 0, 5), lens=28)


# =================================================================== S5 — BREAKS DOWN
def _dark_hangar():
    flat_world((0.004, 0.004, 0.005))
    hangar(lights_on=(0.0, 0.25, 0.0))
    for (x, y) in ((-8, -14), (12, 14), (30, -12)):
        d = bpy.data.lights.new("spot", "SPOT")
        d.energy = 60000
        d.spot_size = math.radians(55)
        d.spot_blend = 0.6
        d.color = (1.0, 0.85, 0.65)
        o = bpy.data.objects.new("spot", d)
        bpy.context.scene.collection.objects.link(o)
        o.location = (x, y, 18)
        look(o, (x * 0.5 + 8, 0, 0))


@shot(40)
def e1_hangar_work():
    _dark_hangar()
    j = airliner("jet")
    j.location = (0, 0, j["ground_offset"])
    j.rotation_euler = (0, 0, math.radians(200))
    mannequin("t1", (-14, -4, 0), 1.2)
    mannequin("t2", (-20, 3, 0), -0.5)
    camera((-38, -24, 3.5), (-8, 0, 3), lens=30)


def _hangar_batteries(n):
    _dark_hangar()
    j = airliner("jet")
    j.location = (0, 0, j["ground_offset"])
    j.rotation_euler = (0, 0, math.radians(200))
    import random
    rnd = random.Random(7)
    cs = []
    for lvl in range(3):
        for i in range(-14, 16):
            for side in (-1, 1):
                if len(cs) >= n:
                    break
                x = i * 1.6 + rnd.uniform(-0.1, 0.1)
                y = side * (11 + (abs(i) % 3) * 1.15)
                cs.append((x - 18, y, lvl * 0.95))
    pallet_field("hp", cs)


@shot(40)
def e2_hangar_b40():
    _hangar_batteries(40)
    camera((-40, -34, 9), (-8, 0, 2), lens=28)


@shot(40)
def e3_hangar_b120():
    _hangar_batteries(120)
    camera((-40, -34, 9), (-8, 0, 2), lens=28)


def _xray_fill(stage):
    flat_world((0.003, 0.004, 0.008))
    lab_floor(400, 0.2)
    j = airliner("jet", xray=True)
    j.location = (0, 0, j["ground_offset"] - (0.35 if stage >= 3 else 0))
    if stage >= 1:
        bat_grid_in(j, 6, 30, -1.4, 1.4, -1.85, -0.75, lit=1.0, name="hold")
    if stage >= 2:
        bat_grid_in(j, 5, 30, -1.5, 1.5, -0.55, 1.3, lit=1.0, name="cabin")
    if stage >= 3:
        bat_grid_in(j, 13, 18, 2.5, 14, -1.2, -0.6, mod=(0.9, 0.9, 0.3), lit=1.0, name="wl")
        bat_grid_in(j, 13, 18, -14, -2.5, -1.2, -0.6, mod=(0.9, 0.9, 0.3), lit=1.0, name="wr")
    area_light("top", (19, 0, 25), (0, 0, 0), 30, 4000, (0.6, 0.75, 1.0))
    camera((-14, -40, 2), (17, 0, 1.0), lens=30)


@shot(40)
def e4_xray_hold():
    _xray_fill(1)


@shot(40)
def e5_xray_cabin():
    _xray_fill(2)


@shot(40)
def e6_xray_full():
    _xray_fill(3)


@shot(48)
def e7_gear_strain():
    _dark_hangar()
    j = airliner("jet")
    j.location = (0, 0, j["ground_offset"] - 0.32)
    camera((14.5, -8.5, 0.6), (17.0, -3.8, 0.9), lens=35, dof=5.5, fstop=2.8)


@shot(40)
def e8_hologram():
    flat_world((0, 0, 0))
    j = airliner("jet", gear=False, xray=True)
    j.location = (0, 0, 0)
    bat_grid_in(j, 5, 30, -1.4, 1.4, -1.8, 1.2, lit=1.0)
    camera((19, 0, 75), (19, 0, 0), lens=35)


def _thermal(level):
    flat_world((0, 0, 0))
    lab_floor(40, 0.15)
    hot = [(0.1, 0.3, 1.0), (1.0, 0.75, 0.1), (1.0, 0.25, 0.05)][level]
    for i in range(10):
        for j in range(6):
            c = cell_21700(f"t{i}{j}", ((i - 4.5) * 0.024, (j - 2.5) * 0.024, 0.5))
            heat = max(0, 1 - math.hypot(i - 4.5, j - 2.5) / 6) if level else 0.4
            for ch in c.children:
                ch.data.materials.clear()
                ch.data.materials.append(emissive(f"therm{level}_{int(heat * 10)}", tuple(h * (0.4 + 0.6 * heat) for h in hot), 1.5 + 4 * heat * level))
    area_light("key", (0.4, -0.8, 1.4), (0.6, 0, 0.4), 0.8, 20)
    camera((0.18, -0.38, 0.75), (0, 0, 0.53), lens=50, dof=0.42, fstop=4)


@shot(40)
def e9_thermal0():
    _thermal(0)


@shot(40)
def e9_thermal2():
    _thermal(2)


@shot(48)
def e10_empty_cabin():
    """inside the fuselage: seats removed, floor lined with glowing battery racks."""
    flat_world((0, 0, 0))
    m_in = mat("cabin_wall", (0.78, 0.79, 0.8), 0.6)
    j = fuselage("cab", 37.6, 1.98, m_in)
    # flip normals so we see the inside
    j.data.flip_normals()
    box("floor", (30, 3.4, 0.05), (19, 0, -0.62), mat("cabin_floor", (0.2, 0.21, 0.24), 0.7))
    module_field("racks", [(7 + i * 1.15, side * 0.95, -0.6) for i in range(22) for side in (-1, 1)], (0.9, 0.7, 0.95))
    # dim cabin ceiling strips
    em = emissive("cabin_strip", (0.5, 0.75, 1.0), 2.0)
    for side in (-1, 1):
        box("strip", (26, 0.05, 0.02), (19, side * 1.25, 1.5), em)
    camera((5.5, 0, 0.75), (30, 0, 0.3), lens=22)


@shot(40)
def e11_777_mountain():
    light(12, 150, 0.25, 2.2, (1, 0.9, 0.78), 0.00008)
    apron(6000, color=(0.18, 0.18, 0.18))
    w = airliner("w", "wide")
    w.location = (0, -60, w["ground_offset"])
    # pyramid of pallets (scaled, ~3,000 t ≈ 3,000 units — shown as 1.2×1.0×0.9 m units)
    pm = mat("pal_steel", (0.23, 0.24, 0.26), 0.42, metal=0.8)
    led = emissive("pled_m", CYAN, 10)
    V, F, LV, LF = [], [], [], []
    def add_box(V, F, cx, cy, cz, sx, sy, sz):
        i0 = len(V)
        for dx, dy, dz in ((-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1), (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)):
            V.append((cx + dx * sx / 2, cy + dy * sy / 2, cz + dz * sz / 2))
        F += [(i0, i0 + 1, i0 + 2, i0 + 3), (i0 + 4, i0 + 5, i0 + 6, i0 + 7), (i0, i0 + 1, i0 + 5, i0 + 4),
              (i0 + 1, i0 + 2, i0 + 6, i0 + 5), (i0 + 2, i0 + 3, i0 + 7, i0 + 6), (i0 + 3, i0, i0 + 4, i0 + 7)]
    count = 0
    lvl = 0
    while count < 2900:
        half = 14 - lvl
        if half <= 0:
            break
        for i in range(-half, half + 1):
            for j in range(-half // 2, half // 2 + 1):
                add_box(V, F, 40 + i * 1.25, 20 + j * 1.05, lvl * 0.92 + 0.45, 1.2, 1.0, 0.88)
                if j == -(half // 2):
                    add_box(LV, LF, 40 + i * 1.25, 20 + j * 1.05 - 0.51, lvl * 0.92 + 0.7, 0.4, 0.02, 0.04)
                count += 1
        lvl += 1
    obj_from_mesh("mountain", V, F, pm, smooth=False)
    obj_from_mesh("mleds", LV, LF, led, smooth=False)
    mannequin("tech", (30, -14, 0), 0.4)
    camera((-20, -95, 14), (28, -10, 10), lens=32)


# =================================================================== S6 — FUTURE
@shot(48)
def f1_hangar_night():
    flat_world((0.0, 0.0, 0.0))
    hangar(lights_on=(0, 0, 0))
    em = emissive("cyan_lamp", CYAN, 60)
    box("lamp", (0.2, 3.0, 0.3), (58, 0, 6), em)
    d = bpy.data.lights.new("cy", "AREA")
    d.energy = 3000
    d.color = CYAN
    d.size = 4
    o = bpy.data.objects.new("cy", d)
    bpy.context.scene.collection.objects.link(o)
    o.location = (57, 0, 6)
    o.rotation_euler = (0, -math.pi / 2, 0)
    camera((-40, 0, 2.0), (60, 0, 5), lens=35)


def _meridian_doors(open_frac):
    light(-2.0, 200, 0.35, 0.0, (0.6, 0.7, 1.0))
    hangar(lights_on=(0.3, 0.5, 0.3), door_open=open_frac)
    m = small_plane("mer", "meridian", livery=(0.94, 0.95, 0.96), accent=(0.05, 0.55, 0.85))
    m.location = (-80, 0, m["ground_offset"])
    m.rotation_euler = (0, 0, math.radians(180 - 25))
    apron(4000)
    camera((40, 0, 2.2), (-80, 0, 3.0), lens=35)


@shot(48)
def f2_doors_half():
    _meridian_doors(0.45)


@shot(48)
def f2_doors_open():
    _meridian_doors(1.0)


@shot(48)
def f3_meridian_islands():
    light(3, 80, 0.5, 3.0, (1.0, 0.7, 0.45), 0.00015, (1.0, 0.8, 0.65))
    ocean(color=(0.01, 0.04, 0.06), wave_scale=0.4)
    islands()
    m = small_plane("mer", "meridian", livery=(0.94, 0.95, 0.96), accent=(0.05, 0.55, 0.85))
    m.location = (0, 0, 260)
    m.rotation_euler = (math.radians(-12), math.radians(-1), math.radians(-12))
    camera((-14, -36, 264), (8, 0, 260), lens=40)


@shot(48)
def f4_meridian_xray():
    flat_world((0.003, 0.004, 0.008))
    m = small_plane("mer", "meridian", xray=True)
    m.location = (0, 0, 0)
    for i in range(6):
        battery_module(f"mb{i}", (4 + i * 1.6, 0, -1.05), parent=m, w=1.2, d=1.4, h=0.4)
    tg = mat("turbogen", (1.0, 0.55, 0.12), 0.3, metal=0.5, emit=AMBER, estr=4)
    cyl("tgen", 0.42, 2.0, (15.2, 0, 0.2), tg, rot=(0, math.pi / 2, 0), parent=m)
    camera((-8, -28, 7), (9.5, 0, 0.5), lens=35)


@shot(64)
def f5_cell_history():
    flat_world((0, 0, 0))
    lab_floor(60, 0.1)
    lab_backdrop()
    k = 0.25 / 0.1  # 0.1 kWh/kg → 0.25 m
    xs = (-0.75, -0.25, 0.25, 0.75)
    for i, (x, whkg) in enumerate(zip(xs, (80, 270, 450, 800))):
        cyl(f"ped{i}", 0.09, 0.4, (x, 0, 0.2), mat("pedestal", (0.04, 0.04, 0.045), 0.25, coat=0.8))
        c = cell_21700(f"hc{i}", (x, 0, 0.4))
        if i == 3:
            for ch in c.children:
                ch.data.materials.clear()
                ch.data.materials.append(mat("proto", (0.6, 0.85, 1.0), 0.05, transm=0.8, ior=1.4, emit=CYAN, estr=2))
        energy_column(f"hcol{i}", (x, 0, 0.48), whkg / 1000 * k * 0.5, 0.035, CYAN, 6)
    area_light("key", (0, -1.2, 2.5), (0.4, 0, 0), 2, 120)
    camera((0, -3.4, 0.9), (0, 0, 0.75), lens=35, dof=3.4, fstop=5.6)


@shot(48)
def f6_saf_gate():
    light(4, 70, 0.45, 3.0, (1.0, 0.75, 0.5), 0.0003)
    apron(4000)
    w = airliner("w", "wide")
    w.location = (0, 0, w["ground_offset"])
    tm = mat("truck", (0.85, 0.86, 0.85), 0.35, coat=0.5)
    box("truck_tank", (9, 2.5, 2.6), (24, -14, 2.0), tm, bevel=0.3)
    box("truck_cab", (2.5, 2.5, 2.4), (18.5, -14, 1.6), mat("truck_cab", (0.1, 0.4, 0.25), 0.4, coat=0.5), bevel=0.15)
    cyl("hose", 0.08, 9, (24, -9.5, 0.6), mat("hose", (0.02, 0.02, 0.02), 0.6), rot=(math.pi / 2, 0, 0.2))
    camera((48, -48, 4), (22, 0, 4), lens=35)


@shot(48)
def f7_h2_tank():
    flat_world((0.003, 0.004, 0.008))
    j = airliner("jet", gear=False, xray=True)
    frost = mat("frost", (0.85, 0.92, 1.0), 0.6, emit=(0.6, 0.85, 1.0), estr=0.6)
    cyl("h2", 1.6, 9, (31, 0, 0.1), frost, rot=(0, math.pi / 2, 0))
    sphere("h2c1", 1.6, (26.5, 0, 0.1), frost, (0.5, 1, 1))
    sphere("h2c2", 1.6, (35.5, 0, 0.1), frost, (0.5, 1, 1))
    camera((14, -26, 7), (28, 0, 0.5), lens=35)


# =================================================================== S7
@shot(64)
def g1_future_cell():
    flat_world((0, 0, 0))
    lab_floor(60, 0.08)
    c = cell_21700("fcell", (0, 0, 0.6))
    for ch in c.children:
        ch.data.materials.clear()
        ch.data.materials.append(mat("proto", (0.6, 0.85, 1.0), 0.05, transm=0.8, ior=1.4, emit=CYAN, estr=3))
    energy_column("fcol", (0, 0, 0.68), 0.75, 0.04, CYAN, 6)
    em = emissive("refline", AMBER, 4)
    box("ref", (1.4, 0.004, 0.006), (0, 0.15, 0.68 + 1.05), em)
    camera((0, -2.2, 1.0), (0, 0, 1.05), lens=40, dof=2.2, fstop=4)


# =================================================================== map table (S2, S5, S6)
@shot(48)
def m1_map():
    """dark relief map seen from straight above (graphics drawn on top in comp)."""
    flat_world((0, 0, 0))
    W, H = 2048, 1152
    rs = np.random.RandomState(11)
    # procedural continents: smoothed noise thresholded
    from numpy.fft import fft2, ifft2, fftfreq
    n = rs.standard_normal((H, W))
    fy, fx = np.meshgrid(fftfreq(H), fftfreq(W), indexing="ij")
    f = np.sqrt(fx ** 2 + fy ** 2) + 1e-6
    land = np.real(ifft2(fft2(n) / (f + 0.003) ** 2.1))
    land = (land - land.mean()) / land.std()
    hgt = np.clip(land - 0.55, 0, None)
    col = np.zeros((H, W, 4), np.float32)
    col[..., 3] = 1
    ocean_c = np.array([0.02, 0.05, 0.085])
    land_c = np.array([0.22, 0.25, 0.27])
    mask = (hgt > 0)[..., None]
    shade = (0.7 + 0.6 * np.tanh(hgt * 2))[..., None]
    col[..., :3] = np.where(mask, land_c * shade, ocean_c)
    # coastline glow
    edge = np.abs(np.diff(mask[..., 0].astype(np.float32), axis=1, prepend=0)) + np.abs(np.diff(mask[..., 0].astype(np.float32), axis=0, prepend=0))
    col[..., :3] += edge[..., None] * np.array([0.05, 0.09, 0.12])
    # lat/long grid
    for x in range(0, W, 128):
        col[:, x:x + 1, :3] += 0.018
    for y in range(0, H, 128):
        col[y:y + 1, :, :3] += 0.018
    img = image_from_array("mapimg", col)
    m = textured_mat("map", img, coat=0.0, rough=0.95)
    obj_from_mesh("map", [(-16, -9, 0), (16, -9, 0), (16, 9, 0), (-16, 9, 0)], [(0, 1, 2, 3)], m, uvs=[(0, 0), (1, 0), (1, 1), (0, 1)], smooth=False)
    area_light("top", (6, -14, 16), (0.7, 0, 0.3), 14, 12000, (0.8, 0.88, 1.0))
    area_light("warm", (-18, -10, 8), (0.9, 0, -0.9), 6, 2500, (1.0, 0.7, 0.45))
    cam = camera((0, 0, 30), (0, 0, 0), lens=35)
    cam.rotation_euler = (0, 0, 0)


# ===================================================================
def main():
    keys = [a for a in sys.argv[1:] if not a.startswith("--")]
    if keys == ["all"]:
        keys = list(SHOTS)
    elif keys and keys[0] == "missing":
        keys = [k for k in SHOTS if not os.path.exists(os.path.join(OUT, k + ".png"))]
    for k in keys:
        fn, samples, res = SHOTS[k]
        t = time.time()
        reset()
        try:
            fn()
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"SHOT {k} FAILED {e}", flush=True)
            continue
        if DRAFT:
            samples, res = 12, (res[0] // 3, res[1] // 3)
        render(os.path.join(OUT, k + ".png"), samples=samples, res=res)
        print(f"SHOT {k} {time.time() - t:.0f}s", flush=True)


if __name__ == "__main__":
    main()
