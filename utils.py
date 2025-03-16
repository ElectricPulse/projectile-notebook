import numpy as np

def get_length(vector):
    return np.sqrt(pow(vector[0], 2) + pow(vector[1], 2))

def get_basis_vector(vector):
    normal = np.linalg.norm(vector)
    return vector/normal

def get_displacement(point_A, point_B):
    return [point_A[0] - point_B[0], point_A[1] - point_B[1]]

def get_displacement_length(displacement):
    return np.sqrt(displacement[0] ** 2 + displacement[1] ** 2)

def get_distance(point_A, point_B):
    return get_displacement_length(get_displacement(point_A, point_B))

def get_direction_to(point_A, point_B):
    return get_basis_vector(get_displacement(point_A, point_B))
