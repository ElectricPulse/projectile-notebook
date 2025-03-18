import time
import numpy as np
import signal
import sys
from matplotlib import pyplot as plot
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button, Slider

import utils
import config

def log(*msg):
    global jupyter, log_out

    if jupyter: 
        with log_out:
            print(*msg)
    else:
        print(*msg)

def clear_log():
    global jupyter, log_out

    if jupyter:
        log_out.clear_output()

class Projectile():
    def __init__(self, ax, dt, speed_bounds, fps):
        self.ax = ax
        self.playback = True
        self.dt = dt
        self.fps = fps

        self.min_distance = float('inf')
        self.max_distance = 0.0
        
        self.arrow = None
        self.graph = None

        self.speed_bounds = speed_bounds

    def update_graph(self):
        trajectory = self.trajectory
        self.graph.set_data([p[0] for p in trajectory], [p[1] for p in trajectory])

    def set_position(self, position):
        self.real_time = 0
        self.simulation_time = 0
        self.position = position.copy()

        if self.graph != None:
            self.graph.remove()

        self.graph, = self.ax.plot([position[0]], [position[1]], 'r')
        self.trajectory = [position.copy()]

    def draw_arrow(self):
        speed_bounds = self.speed_bounds
        # When at min speed the arrow should be min_speed_size
        min_speed_size = 0.1 * config.viewpoint
        max_speed_size = 0.9 * config.viewpoint
        speed_range = speed_bounds[1] - speed_bounds[0]
        speed = utils.get_length(self.speed)
        arrow_size = min_speed_size + (self.speed - speed_bounds[0]) / speed_range * (max_speed_size - min_speed_size)
        end_position = self.position + arrow_size * utils.get_basis_vector(self.speed)
        self.arrow = self.ax.annotate('', xytext=self.position, xy=end_position, arrowprops=dict(arrowstyle="->"))

    def draw_frame(self, frame):
        global animation

        self.real_time += 1/self.fps
        self.simulation_time += self.dt

        max_simulation_time = 15
        if self.real_time > max_simulation_time:
            log('Max simulation time reached')
            self.toggle_playback()

        if not self.playback:
            return self.graph

        distance = utils.get_distance(config.planet_position, self.position)

        if distance < config.planet_radius:
            animation.event_source.stop()
            return self.graph

        if distance > self.max_distance: 
            self.max_distance = distance

        if distance < self.min_distance:
            self.min_distance = distance

        direction_vector = utils.get_direction_to(config.planet_position, self.position)
        gravitational_acceleration_size = config.gravitational_constant * config.earths_mass / distance ** 2
        gravitational_acceleration = direction_vector * gravitational_acceleration_size
        self.speed += gravitational_acceleration * self.dt
        self.position += self.speed * self.dt

        distance_to_last_drawn = utils.get_distance(self.position, self.trajectory[-1])

        if distance_to_last_drawn < config.resolution:
            return self.graph

        self.trajectory.append(self.position.copy())
        self.update_graph()

        return self.graph
       
    def set_speed(self, new_speed):
        self.speed = new_speed.copy()

        if self.arrow != None:
            self.arrow.remove()

        self.draw_arrow()

    def start_playback(self):
        global animation
        self.playback = True
        animation.event_source.start()

    def stop_playback(self):
        global animation
        self.playback = False
        animation.event_source.stop()

    def toggle_playback(self):
        if self.playback:
            self.stop_playback()
            clear_log()
            log('Simulation paused, printing important info:')
            log('   Aktuálny čas: {} dní'.format(self.simulation_time/3600/24))
            log('   Max odchylka {}%'.format(self.max_distance/config.initial_height * 100 - 100))
            log('   Min odchylka {}%'.format(100 - self.min_distance/config.initial_height * 100))
        else:
            self.start_playback()
            
def draw_init(ax):
    circle = plot.Circle(config.planet_position, config.planet_radius, color='g')
    ax.add_patch(circle)

def create_figure_and_graph(plot):
    fig, ax = plot.subplots(figsize=(5,5.5))
    ax.set_aspect('equal')
    ax.set_xlim([-config.viewpoint, config.viewpoint])
    ax.set_ylim([-config.viewpoint, config.viewpoint])
    ax.autoscale(False)

    pos = ax.get_position()
    ax.set_position([pos.x0, pos.y0 + 0.125, pos.width, pos.height])

    return (fig, ax)

def main(_jupyter):
    global jupyter
    jupyter = _jupyter

    if jupyter:
        global log_out
        from ipywidgets.widgets import Output
        log_out = Output(layout={'border': '1px solid black'})
        display(log_out)

        try:
            common_main()
        except Exception as err:
            log(err)
    else:
        common_main()

def common_main():
    (fig, ax) = create_figure_and_graph(plot)
    draw_init(ax)

    distance = utils.get_distance(config.planet_position, config.initial_position)
    orbital_velocity = np.sqrt(config.gravitational_constant * config.earths_mass / distance)
    escape_velocity = np.sqrt(2) * orbital_velocity

    speed_bounds = (0.7 * orbital_velocity, 1.3 * escape_velocity)

    button_axis = fig.add_axes([0.1, 0.1, 0.25, 0.075])
    button = Button(button_axis, 'Toggle playback')

    speed_axis = fig.add_axes([0.25, 0, 0.55, 0.03])
    speed_slider = Slider(ax=speed_axis, label='Launch speed', valmin=speed_bounds[0], valmax=speed_bounds[1], valinit=config.initial_speed[0], initcolor='none')

    milestones = {
        '50% Orbital': 0.7 * orbital_velocity,
        'Orbital': orbital_velocity,
        'Escape': escape_velocity,
        '150% Escape': 1.3 * escape_velocity
    }

    for label, value in milestones.items():
        norm_val = (value - speed_bounds[0]) / (speed_bounds[1] - speed_bounds[0])
        speed_axis.text(norm_val, 1.8, label, transform=speed_axis.transAxes,
        ha='center', va='center', fontsize=8)

    ##############
    # Projectile #
    ##############

    fps = 5
    # Playback speed amount of seconds in simulation is one second during playback
    playback_speed = 3600 * 24 * 3
    dt = playback_speed/fps

    projectile = Projectile(ax, dt, speed_bounds, fps)

    def reset_projectile(speed = config.initial_speed):
        projectile.set_position(config.initial_position)
        projectile.set_speed(speed)

    def playback_toggle_handler(_):
        projectile.toggle_playback()

    def speed_change_handler(new_horizontal_speed):
        reset_projectile([new_horizontal_speed, config.initial_speed[1]])
        projectile.start_playback()

    button.on_clicked(playback_toggle_handler)
    speed_slider.on_changed(speed_change_handler)
    global animation
    animation = FuncAnimation(fig, projectile.draw_frame, interval=1000/fps, cache_frame_data=False, blit=False)

    reset_projectile()
    plot.show()

if __name__ == '__main__':
    main(False)
