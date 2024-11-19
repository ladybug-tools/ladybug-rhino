"""Functions to translate from Honeybee geometries to Rhino geometries."""
from __future__ import division

from .config import tolerance
from .fromgeometry import from_face3d, from_mesh3d, from_face3d_to_wireframe, \
    from_mesh3d_to_wireframe

try:
    import Rhino.Geometry as rg
except ImportError as e:
    raise ImportError('Failed to import Rhino Geometry.\n{}'.format(e))

try:  # import the core honeybee dependencies
    from honeybee.model import Model
    from honeybee.room import Room
    from honeybee.face import Face
    from honeybee.aperture import Aperture
    from honeybee.door import Door
    from honeybee.shade import Shade
    from honeybee.shademesh import ShadeMesh
except ImportError as e:
    print('Failed to import honeybee. Translation from Honeybee objects '
          'is unavailable.\n{}'.format(e))


"""________TRANSLATORS TO BREPS/MESHES________"""


def from_shade(shade):
    """Rhino Brep from a Honeybee Shade."""
    return from_face3d(shade.geometry)


def from_shade_mesh(shade_mesh):
    """Rhino Mesh from a Honeybee ShadeMesh."""
    return from_mesh3d(shade_mesh.geometry)


def from_door(door):
    """Rhino Breps from a Honeybee Door (with shades).

    The first Brep in the returned result is the Door. All following Breps
    are Door-assigned Shades.
    """
    door_breps = [from_face3d(door.geometry)]
    door_breps.extend([from_shade(shd) for shd in door.shades])
    return door_breps


def from_aperture(aperture):
    """Rhino Breps from a Honeybee Aperture (with shades).

    The first Brep in the returned result is the Aperture. All following Breps
    are Aperture-assigned Shades.
    """
    aperture_breps = [from_face3d(aperture.geometry)]
    aperture_breps.extend([from_shade(shd) for shd in aperture.shades])
    return aperture_breps


def from_face(face):
    """Rhino Breps from a Honeybee Face (with shades).

    The first Brep in the returned result is the Face (with Apertures and Doors
    joined into it). All following Breps are assigned Shades.
    """
    face_breps = [from_face3d(face.punched_geometry)]
    shade_breps = [from_shade(shd) for shd in face.shades]
    for ap in face.apertures:
        aperture_breps = from_aperture(ap)
        face_breps.append(aperture_breps[0])
        shade_breps.extend(aperture_breps[1:])
    for dr in face.doors:
        door_breps = from_aperture(dr)
        face_breps.append(door_breps[0])
        shade_breps.extend(door_breps[1:])
    face_breps = list(rg.Brep.JoinBreps(face_breps, tolerance))
    return face_breps + shade_breps


def from_room(room):
    """Rhino Breps from a Honeybee Room (with shades).

    The first Brep in the returned result is a joined Polyface Brep for the Room.
    All following Breps are assigned Shades.
    """
    room_breps = []
    shade_breps = [from_shade(shd) for shd in room.shades]
    for face in room.faces:
        face_breps = from_face(face)
        room_breps.append(face_breps[0])
        shade_breps.extend(face_breps[1:])
    room_breps = list(rg.Brep.JoinBreps(room_breps, tolerance))
    return room_breps + shade_breps


def from_model(model):
    """Rhino Breps and Meshes from a Honeybee Model.

    The first Breps in the returned result will be joined Polyface Breps for each
    Room in the Model. This will be followed by Breps for orphaned objects, which
    will be followed by Breps for Shades assigned to any parent objects. Lastly,
    there will be Meshes for any ShadeMeshes in the Model.
    """
    parent_geo = []
    shade_geo = [from_shade(shd) for shd in model.orphaned_shades]
    for room in model.rooms:
        room_breps = from_room(room)
        parent_geo.append(room_breps[0])
        shade_geo.extend(room_breps[1:])
    for face in model.orphaned_faces:
        face_breps = from_face(face)
        parent_geo.append(face_breps[0])
        shade_geo.extend(face_breps[1:])
    for ap in model.orphaned_apertures:
        ap_breps = from_aperture(ap)
        parent_geo.append(ap_breps[0])
        shade_geo.extend(ap_breps[1:])
    for dr in model.orphaned_doors:
        dr_breps = from_door(dr)
        parent_geo.append(dr_breps[0])
        shade_geo.extend(dr_breps[1:])
    shade_mesh_geo = [from_shade_mesh(sm) for sm in model.shade_meshes]
    return parent_geo + shade_geo + shade_mesh_geo


def from_hb_objects(hb_objects):
    """Rhino Breps and Meshes from a list of any Honeybee geometry objects.

    Any Honeybee geometry object may be input to this method (Model, Room, Face,
    Aperture, Door, Shade, ShadeMesh). The returned result will always have
    Breps first and Meshes last (if applicable).
    """
    brep_geo, mesh_geo = [], []
    for hb_obj in hb_objects:
        if isinstance(hb_obj, Room):
            brep_geo.extend(from_room(hb_obj))
        elif isinstance(hb_obj, Shade):
            brep_geo.append(from_shade(hb_obj))
        elif isinstance(hb_obj, Face):
            brep_geo.extend(from_face(hb_obj))
        elif isinstance(hb_obj, Aperture):
            brep_geo.extend(from_aperture(hb_obj))
        elif isinstance(hb_obj, Door):
            brep_geo.extend(from_door(hb_obj))
        elif isinstance(hb_obj, Model):
            model_geo = from_model(hb_obj)
            for geo in reversed(model_geo):
                if isinstance(geo, rg.Mesh):
                    mesh_geo.append(geo)
                else:
                    brep_geo.append(geo)
        elif isinstance(hb_obj, ShadeMesh):
            mesh_geo.append(from_shade_mesh(hb_obj))
        else:
            raise TypeError(
                'Unrecognized honeybee object type: {}'.format(type(hb_obj)))
    return brep_geo + mesh_geo


"""________TRANSLATORS TO WIREFRAMES________"""


def from_shade_to_wireframe(shade):
    """Rhino PolyLineCurves from a Honeybee Shade."""
    return from_face3d_to_wireframe(shade.geometry)


def from_shade_mesh_to_wireframe(shade_mesh):
    """Rhino PolyLineCurves from a Honeybee ShadeMesh."""
    return from_mesh3d_to_wireframe(shade_mesh.geometry)


def from_door_to_wireframe(door):
    """Rhino PolyLineCurves from a Honeybee Door (with shades)."""
    door_wires = from_face3d_to_wireframe(door.geometry)
    for shd in door.shades:
        door_wires.extend(from_shade_to_wireframe(shd))
    return door_wires


def from_aperture_to_wireframe(aperture):
    """Rhino PolyLineCurves from a Honeybee Aperture (with shades)."""
    aperture_wires = from_face3d_to_wireframe(aperture.geometry)
    for shd in aperture.shades:
        aperture_wires.extend(from_shade_to_wireframe(shd))
    return aperture_wires


def from_face_to_wireframe(face):
    """Rhino PolyLineCurves from a Honeybee Face (with shades)."""
    face_wires = from_face3d_to_wireframe(face.punched_geometry)
    for ap in face.apertures:
        face_wires.extend(from_aperture_to_wireframe(ap))
    for dr in face.doors:
        face_wires.extend(from_door_to_wireframe(dr))
    for shd in face.shades:
        face_wires.extend(from_shade_to_wireframe(shd))
    return face_wires


def from_room_to_wireframe(room):
    """Rhino PolyLineCurves from a Honeybee Room (with shades)."""
    room_wires = []
    for face in room.faces:
        room_wires.extend(from_face_to_wireframe(face))
    for shd in room.shades:
        room_wires.extend(from_shade_to_wireframe(shd))
    return room_wires


def from_model_to_wireframe(model):
    """Rhino PolyLineCurves and Meshes from a Honeybee Model."""
    model_wires = []
    for room in model.rooms:
        model_wires.extend(from_room_to_wireframe(room))
    for face in model.orphaned_faces:
        model_wires.extend(from_face_to_wireframe(face))
    for ap in model.orphaned_apertures:
        model_wires.extend(from_aperture_to_wireframe(ap))
    for dr in model.orphaned_doors:
        model_wires.extend(from_door_to_wireframe(dr))
    for shd in model.orphaned_shades:
        model_wires.extend(from_shade_to_wireframe(shd))
    for sm in model.shade_meshes:
        model_wires.extend(from_shade_mesh_to_wireframe(sm))
    return model_wires


def from_hb_objects_to_wireframe(hb_objects):
    """Rhino PolyLineCurves and Meshes from a list of any Honeybee geometry objects."""
    wire_geo = []
    for hb_obj in hb_objects:
        if isinstance(hb_obj, Room):
            wire_geo.extend(from_room_to_wireframe(hb_obj))
        elif isinstance(hb_obj, Shade):
            wire_geo.extend(from_shade_to_wireframe(hb_obj))
        elif isinstance(hb_obj, Face):
            wire_geo.extend(from_face_to_wireframe(hb_obj))
        elif isinstance(hb_obj, Aperture):
            wire_geo.extend(from_aperture_to_wireframe(hb_obj))
        elif isinstance(hb_obj, Door):
            wire_geo.extend(from_door_to_wireframe(hb_obj))
        elif isinstance(hb_obj, ShadeMesh):
            wire_geo.extend(from_shade_mesh_to_wireframe(hb_obj))
        elif isinstance(hb_obj, Model):
            wire_geo.extend(from_model_to_wireframe(hb_obj))
        else:
            raise TypeError(
                'Unrecognized honeybee object type: {}'.format(type(hb_obj)))
    return wire_geo
