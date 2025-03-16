import numpy as np

gravitational_constant = 6.6743e-11
earths_mass = 5.972e24
earths_radius = 6371e3
# planet_radius = earths_radius/8
planet_radius = earths_radius
planet_position=(0,0)
# Moon height
initial_height = 384400e3
viewpoint = 1.5 * initial_height
initial_position = np.array([0, initial_height])

