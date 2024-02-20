"""Functions to handle intersection of Rhino geometries.

These represent geometry computation methods  that are either not supported by
ladybug_geometry or there are much more efficient versions of them in Rhino.
"""
import math
import operator
import array as specializedarray

try:
    import System.Threading.Tasks as tasks
    from System import Array
    import clr
except ImportError as e:
    print('Failed to import Windows/.NET libraries\nParallel processing functionality '
          'will not be available\n{}'.format(e))

try:
    import Rhino.Geometry as rg
except ImportError as e:
    raise ImportError("Failed to import Rhino.\n{}".format(e))

from .config import tolerance, rhino_version


def join_geometry_to_mesh(geometry):
    """Convert an array of Rhino Breps and/or Meshes into a single Rhino Mesh.

    This is a typical pre-step before using the intersect_mesh_rays functions.

    Args:
        geometry: An array of Rhino Breps or Rhino Meshes.
    """
    if len(geometry) == 1 and isinstance(geometry[0], rg.Mesh):
        return geometry[0]
    joined_mesh = rg.Mesh()
    for geo in geometry:
        if isinstance(geo, rg.Mesh):
            joined_mesh.Append(geo)
        elif isinstance(geo, rg.Brep):
            meshes = rg.Mesh.CreateFromBrep(geo, rg.MeshingParameters.Default)
            for mesh in meshes:
                joined_mesh.Append(mesh)
        else:  # it's likely an extrusion object
            try:
                geo = geo.ToBrep()  # extrusion objects must be cast to Brep in Rhino 8
                meshes = rg.Mesh.CreateFromBrep(geo, rg.MeshingParameters.Default)
                for mesh in meshes:
                    joined_mesh.Append(mesh)
            except:
                raise TypeError('Geometry must be either a Brep or a Mesh. '
                                'Not {}.'.format(type(geo)))
    return joined_mesh


def join_geometry_to_gridded_mesh(geometry, grid_size, offset_distance=0):
    """Create a single gridded Ladybug Mesh3D from an array of Rhino geometry.

    Args:
        breps: An array of Rhino Breps and/or Rhino meshes that will be converted
            into a single, joined gridded Ladybug Mesh3D.
        grid_size: A number for the grid size dimension with which to make the mesh.
        offset_distance: A number for the distance at which to offset the points
            from the underlying geometry. The default is 0.
    
    Returns:
         A tuple with three elements

        -   joined_mesh -- A Rhino Mesh from the input geometry.

        -   points -- A list of Rhino Point3ds for the mesh face centers.

        -   normals -- A list of Rhino Point3ds for the mesh face normals.
    """
    # set up the meshing parameters
    meshing_param = rg.MeshingParameters.Default
    meshing_param.MaximumEdgeLength = grid_size
    meshing_param.MinimumEdgeLength = grid_size
    meshing_param.GridAspectRatio = 1
    # loop through the geometry and mesh it
    joined_mesh = rg.Mesh()
    for geo in geometry:
        if isinstance(geo, rg.Mesh):
            joined_mesh.Append(geo)
        else:
            if not isinstance(geo, rg.Brep):  # it's likely an extrusion object
                geo = geo.ToBrep()  # extrusion objects must be cast to Brep in Rhino 8
            mesh_grids = rg.Mesh.CreateFromBrep(geo, meshing_param)
            for m_grid in mesh_grids:
                joined_mesh.Append(m_grid)
    # compute the points at each face center and offset them if necessary
    joined_mesh.FaceNormals.ComputeFaceNormals()
    joined_mesh.FaceNormals.UnitizeFaceNormals()
    normals = [joined_mesh.FaceNormals[i] for i in range(joined_mesh.FaceNormals.Count)]
    points = []
    if offset_distance == 0:
        for i, n in enumerate(normals):
            points.append(joined_mesh.Faces.GetFaceCenter(i))
    else:
        od = offset_distance
        for i, n in enumerate(normals):
            pt = joined_mesh.Faces.GetFaceCenter(i)
            pt = rg.Point3d(pt.X + (n.X * od), pt.Y + (n.Y * od), pt.Z + (n.Z * od))
            points.append(pt)
    return joined_mesh, points, normals


def join_geometry_to_brep(geometry):
    """Convert an array of Rhino Breps and/or Meshes into a single Rhino Brep.

    This is a typical pre-step before using the ray tracing functions.

    Args:
        geometry: An array of Rhino Breps or Rhino Meshes.
    """
    joined_mesh = join_geometry_to_mesh(geometry)
    return rg.Brep.CreateFromMesh(joined_mesh, False)


def bounding_box(geometry, high_accuracy=False):
    """Get a Rhino bounding box around an input Rhino Mesh or Brep.

    This is a typical pre-step before using intersection functions.

    Args:
        geometry: A Rhino Brep or Mesh.
        high_accuracy: If True, a physically accurate bounding box will be computed.
            If not, a bounding box estimate will be computed. For some geometry
            types, there is no difference between the estimate and the accurate
            bounding box. Estimated bounding boxes can be computed much (much)
            faster than accurate (or "tight") bounding boxes. Estimated bounding
            boxes are always similar to or larger than accurate bounding boxes.
    """
    return geometry.GetBoundingBox(high_accuracy)


def bounding_box_extents(geometry, high_accuracy=False):
    """Get min and max points around an input Rhino Mesh or Brep

    Args:
        geometry: A Rhino Brep or Mesh.
        high_accuracy: If True, a physically accurate bounding box will be computed.
            If not, a bounding box estimate will be computed. For some geometry
            types, there is no difference between the estimate and the accurate
            bounding box. Estimated bounding boxes can be computed much (much)
            faster than accurate (or "tight") bounding boxes. Estimated bounding
            boxes are always similar to or larger than accurate bounding boxes.
    """
    b_box = bounding_box(geometry, high_accuracy)
    return b_box.Max, b_box.Min


def intersect_mesh_rays(
        mesh, points, vectors, normals=None, cpu_count=None, parallel=True):
    """Intersect a group of rays (represented by points and vectors) with a mesh.

    All combinations of rays that are possible between the input points and
    vectors will be intersected. This method exists since most CAD plugins have
    much more efficient mesh/ray intersection functions than ladybug_geometry.
    However, the ladybug_geometry Face3D.intersect_line_ray() method provides
    a workable (albeit very inefficient) alternative to this if it is needed.

    Args:
        mesh: A Rhino mesh that can block the rays.
        points: An array of Rhino points that will be used to generate rays.
        vectors: An array of Rhino vectors that will be used to generate rays.
        normals: An optional array of Rhino vectors that align with the input
            points and denote the direction each point is facing. These will
            be used to eliminate any cases where the vector and the normal differ
            by more than 90 degrees. If None, points are assumed to have no direction.
        cpu_count: An integer for the number of CPUs to be used in the intersection
            calculation. The ladybug_rhino.grasshopper.recommended_processor_count
            function can be used to get a recommendation. If set to None, all
            available processors will be used. (Default: None).
        parallel: Optional boolean to override the cpu_count and use a single CPU
            instead of multiple processors.

    Returns:
        A tuple with two elements

        -   intersection_matrix -- A 2D matrix of 0's and 1's indicating the results
            of the intersection. Each sub-list of the matrix represents one of the
            points and has a length equal to the vectors. 0 indicates a blocked
            ray and 1 indicates a ray that was not blocked.

        -   angle_matrix -- A 2D matrix of angles in radians. Each sub-list of the
            matrix represents one of the normals and has a length equal to the
            supplied vectors. Will be None if no normals are provided.
    """
    intersection_matrix = [0] * len(points)  # matrix to be filled with results
    angle_matrix = [0] * len(normals) if normals is not None else None
    cutoff_angle = math.pi / 2  # constant used in all normal checks
    if not parallel:
        cpu_count = 1

    def intersect_point(i):
        """Intersect all of the vectors of a given point without any normal check."""
        pt = points[i]
        int_list = []
        for vec in vectors:
            ray = rg.Ray3d(pt, vec)
            if rg.Intersect.Intersection.MeshRay(mesh, ray) >= 0:
                is_clear = 0
            else:
                is_clear = 1
            int_list.append(is_clear)
        intersection_matrix[i] = int_list

    def intersect_point_normal_check(i):
        """Intersect all of the vectors of a given point with a normal check."""
        pt, normal_vec = points[i], normals[i]
        int_list = []
        angle_list = []
        for vec in vectors:
            vec_angle = rg.Vector3d.VectorAngle(normal_vec, vec)
            angle_list.append(vec_angle)
            if vec_angle <= cutoff_angle:
                ray = rg.Ray3d(pt, vec)
                if rg.Intersect.Intersection.MeshRay(mesh, ray) >= 0:
                    is_clear = 0
                else:
                    is_clear = 1
                int_list.append(is_clear)
            else:  # the vector is pointing behind the surface
                int_list.append(0)
        intersection_matrix[i] = specializedarray.array('B', int_list)
        angle_matrix[i] = specializedarray.array('d', angle_list)

    def intersect_each_point_group(worker_i):
        """Intersect groups of points so that only the cpu_count is used."""
        start_i, stop_i = pt_groups[worker_i]
        for count in range(start_i, stop_i):
            intersect_point(count)

    def intersect_each_point_group_normal_check(worker_i):
        """Intersect groups of points with distance check so only cpu_count is used."""
        start_i, stop_i = pt_groups[worker_i]
        for count in range(start_i, stop_i):
            intersect_point_normal_check(count)

    if cpu_count is not None and cpu_count > 1:
        # group the points in order to meet the cpu_count
        pt_count = len(points)
        worker_count = min((cpu_count, pt_count))
        i_per_group = int(math.ceil(pt_count / worker_count))
        pt_groups = [[x, x + i_per_group] for x in range(0, pt_count, i_per_group)]
        pt_groups[-1][-1] = pt_count  # ensure the last group ends with point count

    if normals is not None:
        if cpu_count is None:  # use all available CPUs
            tasks.Parallel.ForEach(range(len(points)), intersect_point_normal_check)
        elif cpu_count <= 1:  # run everything on a single processor
            for i in range(len(points)):
                intersect_point_normal_check(i)
        else:  # run the groups in a manner that meets the CPU count
            tasks.Parallel.ForEach(
                range(len(pt_groups)), intersect_each_point_group_normal_check)
    else:
        if cpu_count is None:  # use all available CPUs
            tasks.Parallel.ForEach(range(len(points)), intersect_point)
        elif cpu_count <= 1:  # run everything on a single processor
            for i in range(len(points)):
                intersect_point(i)
        else:  # run the groups in a manner that meets the CPU count
            tasks.Parallel.ForEach(range(len(pt_groups)), intersect_each_point_group)

    return intersection_matrix, angle_matrix


def intersect_rays_with_mesh_faces(
        mesh, rays, context=None, normals=None, cpu_count=None):
    """Intersect a matrix of rays with a mesh to get the intersected mesh faces.

    This method is useful when trying to color each face of the mesh with values
    that can be linked to each one of the rays. For example, this method is
    used in all shade benefit calculations.

    Args:
        mesh: A Rhino mesh that will be intersected with the rays.
        rays: A matrix (list of lists) where each sublist contains Rhino Rays to be
            intersected with the mesh.
        context: An optional Rhino mesh that will be used to evaluate if the
            rays are blocked before performing the calculation with the input
            mesh. Rays that intersect this context will be discounted from
            the calculation.
        normals: An optional array of Rhino vectors that align with the input
            rays and denote the direction each ray group is facing. These will
            be used to eliminate any cases where the vector and the normal differ
            by more than 90 degrees. If None, points are assumed to have no direction.
        cpu_count: An integer for the number of CPUs to be used in the intersection
            calculation. The ladybug_rhino.grasshopper.recommended_processor_count
            function can be used to get a recommendation. If set to None, all
            available processors will be used. (Default: None).

    Returns:
        A 2D matrix of integers indicating the results of the intersection.
        Each sub-list of the matrix represents one of the mesh faces and the
        integers within it refer to the indices of the rays in the rays
        list that intersected that face.
    """
    #create a list to populate intersected indices for each face
    face_int = []
    for _ in range(mesh.Faces.Count):
        face_int.append([])  # place holder for result

    # process the input normals if supplied
    if normals is None:
        ang_mtx = [[True] * len(r) for r in rays]
    else:
        cutoff_angle = math.pi / 2  # constant used in all normal checks
        ang_mtx = []
        for ray_list, normal_vec in zip(rays, normals):
            pt_ang = []
            for ray in ray_list:
                vec_angle = rg.Vector3d.VectorAngle(normal_vec, ray.Direction)
                vec_seen = True if vec_angle <= cutoff_angle else False
                pt_ang.append(vec_seen)
            ang_mtx.append(pt_ang)

    def intersect_rays(i):
        for j, ray in enumerate(rays[i]):
            if ang_mtx[i][j]:
                face_ids = clr.StrongBox[Array[int]]()
                ray_p = rg.Intersect.Intersection.MeshRay(mesh, ray, face_ids)
                if ray_p >= 0:
                    for indx in list(face_ids.Value):
                        face_int[indx].append(j)

    def intersect_rays_context(i):
        for j, ray in enumerate(rays[i]):
            if ang_mtx[i][j] and rg.Intersect.Intersection.MeshRay(context, ray) < 0:
                face_ids = clr.StrongBox[Array[int]]()
                ray_p = rg.Intersect.Intersection.MeshRay(mesh, ray, face_ids)
                if ray_p >= 0:
                    for indx in list(face_ids.Value):
                        face_int[indx].append(j)

    def intersect_each_ray_group(worker_i):
        """Intersect groups of rays so that only the cpu_count is used."""
        start_i, stop_i = ray_groups[worker_i]
        for count in range(start_i, stop_i):
            intersect_rays(count)

    def intersect_each_ray_group_context(worker_i):
        """Intersect groups of points with distance check so only cpu_count is used."""
        start_i, stop_i = ray_groups[worker_i]
        for count in range(start_i, stop_i):
            intersect_rays_context(count)

    if cpu_count is not None and cpu_count > 1:
        # group the rays in order to meet the cpu_count
        ray_count = len(rays)
        worker_count = min((cpu_count, ray_count))
        i_per_group = int(math.ceil(ray_count / worker_count))
        ray_groups = [[x, x + i_per_group] for x in range(0, ray_count, i_per_group)]
        ray_groups[-1][-1] = ray_count  # ensure the last group ends with ray count

    if context is not None:
        if cpu_count is None:
            tasks.Parallel.ForEach(range(len(rays)), intersect_rays_context)
        elif cpu_count <= 1:  # run everything on a single processor
            for i in range(len(rays)):
                intersect_rays_context(i)
        else:  # run the groups in a manner that meets the CPU count
            tasks.Parallel.ForEach(
                range(len(ray_groups)), intersect_each_ray_group_context)
    else:
        if cpu_count is None:
            tasks.Parallel.ForEach(range(len(rays)), intersect_rays)
        elif cpu_count <= 1:  # run everything on a single processor
            for i in range(len(rays)):
                intersect_rays(i)
        else:  # run the groups in a manner that meets the CPU count
            tasks.Parallel.ForEach(
                range(len(ray_groups)), intersect_each_ray_group)

    return face_int


def intersect_mesh_rays_distance(mesh, point, vectors, max_dist=None):
    """Intersect a group of rays with a mesh to get the distance until intersection.

    Args:
        mesh: A Rhino mesh that can block the rays.
        points: A Rhino point that will be used to generate rays.
        vectors: An array of Rhino vectors that will be used to generate rays.
        max_dist: An optional number to set the maximum distance beyond which context
            blocking the view is no longer considered relevant. If None,
            geometries at all distances will be evaluated for whether they
            block the view and the results may contain negative numbers
            indicating that the view from that ray is never blocked

    Returns:
        A list of values for the distance at which intersection occurs.
    """
    distances = []
    if max_dist is None:
        for vec in vectors:
            ray = rg.Ray3d(point, vec)
            dist = rg.Intersect.Intersection.MeshRay(mesh, ray)
            distances.append(dist)
    else:
        for vec in vectors:
            ray = rg.Ray3d(point, vec)
            dist = rg.Intersect.Intersection.MeshRay(mesh, ray)
            dist = max_dist if dist < 0 or dist > max_dist else dist
            distances.append(dist)
    return distances


def generate_intersection_rays(points, vectors):
    """Generate a series of rays to be used for intersection calculations.

    All combinations of rays between the input points and vectors will be generated.

    Args:
        points: A list of Rhino point objects for the starting point of each ray.
        vectors: A list of Rhino vector objects for the direction of each ray,
            which will be projected from each point.
    """
    int_rays = []
    for pt in points:
        pt_rays = []
        for vec in vectors:
            pt_rays.append(rg.Ray3d(pt, vec))
        int_rays.append(pt_rays)
    return int_rays


def intersect_mesh_lines(
        mesh, start_points, end_points, max_dist=None, cpu_count=None, parallel=True):
    """Intersect a group of lines (represented by start + end points) with a mesh.

    All combinations of lines that are possible between the input start_points and
    end_points will be intersected. This method exists since most CAD plugins have
    much more efficient mesh/line intersection functions than ladybug_geometry.
    However, the ladybug_geometry Face3D.intersect_line_ray() method provides
    a workable (albeit very inefficient) alternative to this if it is needed.

    Args:
        mesh: A Rhino mesh that can block the lines.
        start_points: An array of Rhino points that will be used to generate lines.
        end_points: An array of Rhino points that will be used to generate lines.
        max_dist: An optional number to set the maximum distance beyond which the
            end_points are no longer considered visible by the start_points.
            If None, points with an unobstructed view to one another will be
            considered visible no matter how far they are from one another.
        cpu_count: An integer for the number of CPUs to be used in the intersection
            calculation. The ladybug_rhino.grasshopper.recommended_processor_count
            function can be used to get a recommendation. If set to None, all
            available processors will be used. (Default: None).
        parallel: Optional boolean to override the cpu_count and use a single CPU
            instead of multiple processors.

    Returns:
        A 2D matrix of 0's and 1's indicating the results of the intersection.
        Each sub-list of the matrix represents one of the points and has a
        length equal to the end_points. 0 indicates a blocked ray and 1 indicates
        a ray that was not blocked.
    """
    int_matrix = [0] * len(start_points)  # matrix to be filled with results
    if not parallel:
        cpu_count = 1

    def intersect_line(i):
        """Intersect a line defined by a start and an end with the mesh."""
        pt = start_points[i]
        int_list = []
        for ept in end_points:
            lin = rg.Line(pt, ept)
            int_obj = rg.Intersect.Intersection.MeshLine(mesh, lin)
            is_clear = 1 if None in int_obj or len(int_obj) == 0 else 0
            int_list.append(is_clear)
        int_matrix[i] = int_list

    def intersect_line_dist_check(i):
        """Intersect a line with the mesh with a distance check."""
        pt = start_points[i]
        int_list = []
        for ept in end_points:
            lin = rg.Line(pt, ept)
            if lin.Length > max_dist:
                int_list.append(0)
            else:
                int_obj = rg.Intersect.Intersection.MeshLine(mesh, lin)
                is_clear = 1 if None in int_obj or len(int_obj) == 0 else 0
                int_list.append(is_clear)
        int_matrix[i] = int_list

    def intersect_each_line_group(worker_i):
        """Intersect groups of lines so that only the cpu_count is used."""
        start_i, stop_i = l_groups[worker_i]
        for count in range(start_i, stop_i):
            intersect_line(count)

    def intersect_each_line_group_dist_check(worker_i):
        """Intersect groups of lines with distance check so only cpu_count is used."""
        start_i, stop_i = l_groups[worker_i]
        for count in range(start_i, stop_i):
            intersect_line_dist_check(count)

    if cpu_count is not None and cpu_count > 1:
        # group the lines in order to meet the cpu_count
        l_count = len(start_points)
        worker_count = min((cpu_count, l_count))
        i_per_group = int(math.ceil(l_count / worker_count))
        l_groups = [[x, x + i_per_group] for x in range(0, l_count, i_per_group)]
        l_groups[-1][-1] = l_count  # ensure the last group ends with line count

    if max_dist is not None:
        if cpu_count is None:  # use all available CPUs
            tasks.Parallel.ForEach(range(len(start_points)), intersect_line_dist_check)
        elif cpu_count <= 1:  # run everything on a single processor
            for i in range(len(start_points)):
                intersect_line_dist_check(i)
        else:  # run the groups in a manner that meets the CPU count
            tasks.Parallel.ForEach(
                range(len(l_groups)), intersect_each_line_group_dist_check)
    else:
        if cpu_count is None:  # use all available CPUs
            tasks.Parallel.ForEach(range(len(start_points)), intersect_line)
        elif cpu_count <= 1:  # run everything on a single processor
            for i in range(len(start_points)):
                intersect_line(i)
        else:  # run the groups in a manner that meets the CPU count
            tasks.Parallel.ForEach(
                range(len(l_groups)), intersect_each_line_group)
    return int_matrix


def intersect_view_factor(
        meshes, points, vectors, vector_weights,
        context=None, normals=None, cpu_count=None):
    """Intersect a list of points with meshes to determine the view factor to each mesh.

    Args:
        meshes: A list of Rhino meshes that will be intersected to determine
            the view factor from each point.
        points: An array of Rhino points that will be used to generate rays.
        vectors: An array of Rhino vectors that will be used to generate rays.
        vector_weights: A list of numbers with the same length as the vectors
            corresponding to the solid angle weight of each vector. The sum of
            this list should be equal to one. These are needed to ensure that
            the resulting view factors are accurate.
        context: An optional Rhino mesh that will be used to evaluate if the
            rays are blocked before performing the calculation with the input
            meshes. Rays that intersect this context will be discounted from
            the result.
        normals: An optional array of Rhino vectors that align with the input
            points and denote the direction each point is facing. These will
            be used to eliminate any cases where the vector and the normal differ
            by more than 90 degrees and will also be used to compute view factors
            within the plane defined by this normal vector. If None, points are
            assumed to have no direction and view factors will be computed
            spherically around the points.
        cpu_count: An integer for the number of CPUs to be used in the intersection
            calculation. The ladybug_rhino.grasshopper.recommended_processor_count
            function can be used to get a recommendation. If set to None, all
            available processors will be used. (Default: None).

    Returns:
        A tuple with two values.

        -   view_factors -- A 2D matrix of fractional values indicating the view
            factor from each point to each mesh. Each sub-list of the matrix
            denotes one of the input points.

        -   mesh_indices -- A 2D matrix of integers indicating the index of each
            mesh struck by each view ray. Each sub-list of the matrix represents
            one of the points and the value in each sub-list is the integer of
            the mesh that was struck by a given ray shot from the point.
    """
    # set up the matrices to be filled
    view_factors = [[] for _ in points]
    mesh_indices = [[] for _ in points]
    vec_count = len(vectors)
    cutoff_angle = math.pi / 2  # constant used in all normal checks

    # combine the context with the meshes if it is specified
    context_index = None
    if context is not None:
        meshes = list(meshes) + [context]
        context_index = len(meshes) - 1

    def intersect_point(i):
        """Intersect all of the vectors of a given point without any normal check."""
        # create the rays to be projected from each point
        rel_pt = points[i]
        point_rays = []
        for vec in vectors:
            point_rays.append(rg.Ray3d(rel_pt, vec))
        
        # perform the intersection of the rays with the mesh
        pt_int_mtx = []
        for ray in point_rays:
            srf_list = []
            for srf in meshes:
                intersect = rg.Intersect.Intersection.MeshRay(srf, ray)
                if intersect < 0:
                    intersect = 'N'
                srf_list.append(intersect)
            pt_int_mtx.append(srf_list)
        
        # find the intersection that was the closest for each ray
        srf_hits = [[] for _ in meshes]
        for ray_count, int_list in enumerate(pt_int_mtx):
            if not all(x == 'N' for x in int_list):
                min_index, _ = min(enumerate(int_list), key=operator.itemgetter(1))
                if min_index == context_index:
                    mesh_indices[i].append(-1)
                else:
                    mesh_indices[i].append(min_index)
                    if normals is None or normals[i] is None:
                        srf_hits[min_index].append(vector_weights[ray_count])
                    else:
                        # get the angle between the surface and the vector
                        vec_angle = rg.Vector3d.VectorAngle(
                            vectors[ray_count], normals[i])
                        if vec_angle > cutoff_angle:
                            srf_hits[min_index].append(0)
                        else:
                            srf_hits[min_index].append(
                                vector_weights[ray_count] * 4 * abs(math.cos(vec_angle)))
            else:
                mesh_indices[i].append(-1)
        
        # sum up the lists and divide by the total rays to get the view factor
        for hit_list in srf_hits:
            view_factors[i].append(sum(hit_list) / vec_count)

    def intersect_each_point_group(worker_i):
        """Intersect groups of points so that only the cpu_count is used."""
        start_i, stop_i = pt_groups[worker_i]
        for count in range(start_i, stop_i):
            intersect_point(count)

    if cpu_count is not None and cpu_count > 1:
        # group the points in order to meet the cpu_count
        pt_count = len(points)
        worker_count = min((cpu_count, pt_count))
        i_per_group = int(math.ceil(pt_count / worker_count))
        pt_groups = [[x, x + i_per_group] for x in range(0, pt_count, i_per_group)]
        pt_groups[-1][-1] = pt_count  # ensure the last group ends with point count

    if cpu_count is None:  # use all available CPUs
        tasks.Parallel.ForEach(range(len(points)), intersect_point)
    elif cpu_count <= 1:  # run everything on a single processor
        for i in range(len(points)):
            intersect_point(i)
    else:  # run the groups in a manner that meets the CPU count
        tasks.Parallel.ForEach(range(len(pt_groups)), intersect_each_point_group)

    return view_factors, mesh_indices


def trace_ray(ray, breps, bounce_count=1):
    """Get a list of Rhino points for the path a ray takes bouncing through breps.

    Args:
        ray: A Rhino Ray whose path will be traced through the geometry.
        breps: An array of Rhino breps through with the ray will be traced.
        bounce_count: An positive integer for the number of ray bounces to trace
            the sun rays forward. (Default: 1).
    """
    return rg.Intersect.Intersection.RayShoot(ray, breps, bounce_count)


def normal_at_point(brep, point):
    """Get a Rhino vector for the normal at a specific point that lies on a brep.

    Args:
        breps: A Rhino brep on which the normal direction will be evaluated.
        point: A Rhino point on the input brep where the normal will be evaluated.
    """
    return brep.ClosestPoint(point, tolerance)[5]


def intersect_solids_parallel(solids, bound_boxes, cpu_count=None):
    """Intersect the co-planar faces of an array of solids using parallel processing.

    Args:
        original_solids: An array of closed Rhino breps (polysurfaces) that do
            not have perfectly matching surfaces between adjacent Faces.
        bound_boxes: An array of Rhino bounding boxes that parallels the input
            solids and will be used to check whether two Breps have any potential
            for intersection before the actual intersection is performed.
        cpu_count: An integer for the number of CPUs to be used in the intersection
            calculation. The ladybug_rhino.grasshopper.recommended_processor_count
            function can be used to get a recommendation. If None, all available
            processors will be used. (Default: None).
        parallel: Optional boolean to override the cpu_count and use a single CPU
            instead of multiple processors.

    Returns:
        int_solids -- The input array of solids, which have all been intersected
        with one another.
    """
    int_solids = solids[:]  # copy the input list to avoid editing it

    def intersect_each_solid(i):
        """Intersect a solid with all of the other solids of the list."""
        bb_1 = bound_boxes[i]
        # intersect the solids that come after this one
        for j, bb_2 in enumerate(bound_boxes[i + 1:]):
            if not overlapping_bounding_boxes(bb_1, bb_2):
                continue  # no overlap in bounding box; intersection impossible
            split_brep1, int_exists = \
                intersect_solid(int_solids[i], int_solids[i + j + 1])
            if int_exists:
                int_solids[i] = split_brep1
        # intersect the solids that come before this one
        for j, bb_2 in enumerate(bound_boxes[:i]):
            if not overlapping_bounding_boxes(bb_1, bb_2):
                continue  # no overlap in bounding box; intersection impossible
            split_brep2, int_exists = intersect_solid(int_solids[i], int_solids[j])
            if int_exists:
                int_solids[i] = split_brep2

    def intersect_each_solid_group(worker_i):
        """Intersect groups of solids so that only the cpu_count is used."""
        start_i, stop_i = s_groups[worker_i]
        for count in range(start_i, stop_i):
            intersect_each_solid(count)

    if cpu_count is None or cpu_count <= 1:  # use all available CPUs
        tasks.Parallel.ForEach(range(len(solids)), intersect_each_solid)
    else:  # group the solids in order to meet the cpu_count
        solid_count = len(int_solids)
        worker_count = min((cpu_count, solid_count))
        i_per_group = int(math.ceil(solid_count / worker_count))
        s_groups = [[x, x + i_per_group] for x in range(0, solid_count, i_per_group)]
        s_groups[-1][-1] = solid_count  # ensure the last group ends with solid count
        tasks.Parallel.ForEach(range(len(s_groups)), intersect_each_solid_group)

    return int_solids


def intersect_solids(solids, bound_boxes):
    """Intersect the co-planar faces of an array of solids.

    Args:
        original_solids: An array of closed Rhino breps (polysurfaces) that do
            not have perfectly matching surfaces between adjacent Faces.
        bound_boxes: An array of Rhino bounding boxes that parallels the input
            solids and will be used to check whether two Breps have any potential
            for intersection before the actual intersection is performed.

    Returns:
        int_solids -- The input array of solids, which have all been intersected
        with one another.
    """
    int_solids = solids[:]  # copy the input list to avoid editing it

    for i, bb_1 in enumerate(bound_boxes):
        for j, bb_2 in enumerate(bound_boxes[i + 1:]):
            if not overlapping_bounding_boxes(bb_1, bb_2):
                continue  # no overlap in bounding box; intersection impossible

            # split the first solid with the second one
            split_brep1, int_exists = intersect_solid(
                int_solids[i], int_solids[i + j + 1])
            int_solids[i] = split_brep1

            # split the second solid with the first one if an intersection was found
            if int_exists:
                split_brep2, int_exists = intersect_solid(
                    int_solids[i + j + 1], int_solids[i])
                int_solids[i + j + 1] = split_brep2

    return int_solids


def intersect_solid(solid, other_solid):
    """Intersect the co-planar faces of one solid Brep using another.

    Args:
        solid: The solid Brep which will be split with intersections.
        other_solid: The other Brep, which will be used to split.

    Returns:
        A tuple with two elements

        -   solid -- The input solid, which has been split.

        -   intersection_exists -- Boolean to note whether an intersection was found
            between the solid and the other_solid. If False, there's no need to
            split the other_solid with the input solid.
    """
    # variables to track the splitting process
    intersection_exists = False  # boolean to note whether an intersection exists
    temp_brep = solid.Split(other_solid, tolerance)
    if len(temp_brep) != 0:
        solid = rg.Brep.JoinBreps(temp_brep, tolerance)[0]
        solid.Faces.ShrinkFaces()
        intersection_exists = True
    return solid, intersection_exists


def overlapping_bounding_boxes(bound_box1, bound_box2):
    """Check if two Rhino bounding boxes overlap within the tolerance.

    This is particularly useful as a check before performing computationally
    intense intersection processes between two bounding boxes. Checking the
    overlap of the bounding boxes is extremely quick given this method's use
    of the Separating Axis Theorem. This method is built into the intersect_solids
    functions in order to improve its calculation time.

    Args:
        bound_box1: The first bound_box to check.
        bound_box2: The second bound_box to check.
    """
    # Bounding box check using the Separating Axis Theorem
    bb1_width = bound_box1.Max.X - bound_box1.Min.X
    bb2_width = bound_box2.Max.X - bound_box2.Min.X
    dist_btwn_x = abs(bound_box1.Center.X - bound_box2.Center.X)
    x_gap_btwn_box = dist_btwn_x - (0.5 * bb1_width) - (0.5 * bb2_width)

    bb1_depth = bound_box1.Max.Y - bound_box1.Min.Y
    bb2_depth = bound_box2.Max.Y - bound_box2.Min.Y
    dist_btwn_y = abs(bound_box1.Center.Y - bound_box2.Center.Y)
    y_gap_btwn_box = dist_btwn_y - (0.5 * bb1_depth) - (0.5 * bb2_depth)

    bb1_height = bound_box1.Max.Z - bound_box1.Min.Z
    bb2_height = bound_box2.Max.Z - bound_box2.Min.Z
    dist_btwn_z = abs(bound_box1.Center.Z - bound_box2.Center.Z)
    z_gap_btwn_box = dist_btwn_z - (0.5 * bb1_height) - (0.5 * bb2_height)

    if x_gap_btwn_box > tolerance or y_gap_btwn_box > tolerance or \
            z_gap_btwn_box > tolerance:
        return False  # no overlap
    return True  # overlap exists


def split_solid_to_floors(building_solid, floor_heights):
    """Extract a series of planar floor surfaces from solid building massing.

    Args:
        building_solid: A closed brep representing a building massing.
        floor_heights: An array of float values for the floor heights, which
            will be used to generate planes that subdivide the building solid.

    Returns:
        floor_breps -- A list of planar, horizontal breps representing the floors
        of the building.
    """
    # get the floor brep at each of the floor heights.
    floor_breps = []
    for hgt in floor_heights:
        story_breps = []
        floor_base_pt = rg.Point3d(0, 0, hgt)
        section_plane = rg.Plane(floor_base_pt, rg.Vector3d.ZAxis)
        floor_crvs = rg.Brep.CreateContourCurves(building_solid, section_plane)
        try:  # Assume a single contour curve has been found
            floor_brep = rg.Brep.CreatePlanarBreps(floor_crvs, tolerance)
        except TypeError:  # An array of contour curves has been found
            floor_brep = rg.Brep.CreatePlanarBreps(floor_crvs)
        if floor_brep is not None:
            story_breps.extend(floor_brep)
        floor_breps.append(story_breps)

    return floor_breps


def geo_min_max_height(geometry):
    """Get the min and max Z values of any input object.

    This is useful as a pre-step before the split_solid_to_floors method.
    """
    # intersection functions changed in Rhino 7.15 such that we now need 2* tolerance
    add_val = tolerance * 2 if (7, 15) <= rhino_version < (7, 17) else 0
    bound_box = geometry.GetBoundingBox(rg.Plane.WorldXY)
    return bound_box.Min.Z + add_val, bound_box.Max.Z
