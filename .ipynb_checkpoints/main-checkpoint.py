import config
import signal
import numpy as np
import threading
import matplotlib
import datetime
from matplotlib import pyplot as plot
from matplotlib.widgets import Button, Slider

#matplotlib.use('tkagg')

def get_basis_vector(vector):
    normal = np.linalg.norm(vector)
    return vector/normal

def get_distance(displacement):
    return np.sqrt(displacement[0] ** 2 + displacement[1] ** 2)

def get_displacement(point_A, point_B):
    return [point_A[0] - point_B[0], point_A[1] - point_B[1]]

def get_current_time():
    return datetime.datetime.now()

event_loop_pause = 0.5

def draw_projectile(redraw_event, pause_event, config, axis, launch_speed):
    position=np.copy(config.initial_position)
    speed=np.array([launch_speed, 0])

    axis.annotate('', xytext=position, xy=position + speed * 500, arrowprops=dict(arrowstyle="->"))

    i = 0

    # Interpret playback_speed amount of simulation seconds as one playback second
    playback_speed = 48 * 3600
    fps = 40

    # Do a recalculation every dt seconds
    dt = playback_speed/fps

    resolution = launch_speed * 0.1e3
    max_playback_duration = datetime.timedelta(seconds=1)

    start_playback_time = get_current_time()
    last_drawn_position = np.copy(position)

    min_distance = float('inf')
    max_distance = 0

    while not redraw_event.is_set():
        if pause_event.is_set():
            if not printed_pause_message:
                print('Simulation paused, printing important info')
                print('Current time: ', dt * i)
                print('Max distance from center of earth', max_distance)
                print('Min distance from center of earth', min_distance)

                printed_pause_message = True

            plot.pause(event_loop_pause)
            continue

        printed_pause_message = False
        i += 1

        distance = get_distance(get_displacement(last_drawn_position, position))

        distance_to_earth = get_distance(get_displacement(config.planet_position, position))

        if distance_to_earth > max_distance: 
            max_distance = distance_to_earth

        if distance_to_earth < min_distance:
            min_distance = distance_to_earth

        if distance > resolution:
            if np.abs(position[0]) < config.viewpoint and np.abs(position[1]) < config.viewpoint:
                axis.plot([last_drawn_position[0], position[0]], [last_drawn_position[1], position[1]], 'r')

            last_drawn_position = np.copy(position)

        elapsed_time = get_current_time() - start_playback_time
        if elapsed_time > max_playback_duration:
            break

        displacement = get_displacement(config.planet_position, position)
        distance = get_distance(displacement)

        if distance < config.planet_radius:
            break
        
        direction_vector = get_basis_vector(displacement)
        gravitational_acceleration_size = config.gravitational_constant * config.earths_mass / distance ** 2
        gravitational_acceleration = direction_vector * gravitational_acceleration_size
        speed += gravitational_acceleration * dt
        position += speed * dt

        plot.pause(1/playback_speed * dt)

def draw(ax, speed, redraw_event, pause_event):
    try:
        ax.cla() 
        ax.set_aspect('equal')
        ax.set_xlim([-config.viewpoint, config.viewpoint])
        ax.set_ylim([-config.viewpoint, config.viewpoint])
        ax.autoscale(False)

        circle = plot.Circle(config.planet_position, config.planet_radius, color='g')
        ax.add_patch(circle)
        draw_projectile(redraw_event, pause_event, config, ax, speed)
    except Exception as err:
        return err

    return None

def ensure_drawing_stopped():
    global redraw_event
    redraw_event.set()

def playback_toggle_handler(_):
    global pause_event

    if pause_event.is_set(): 
        pause_event.clear()
        return

    pause_event.set()

def speed_change_handler(new_speed):
    global speed
    speed = new_speed
    ensure_drawing_stopped()

def signal_handler(sig, _):
    global stop_app_event
    stop_app_event.set()
    ensure_drawing_stopped()

def figure_close_event(_):
    global stop_app_event
    stop_app_event.set()
    ensure_drawing_stopped()

def start():
    # Need to keep a reference to speed_slider because matplotlib is funky like that
    global speed_slider

    fig = plot.figure(1)
    fig.set_size_inches(6, 8)
    ax = plot.gca()
    pos = ax.get_position()
    ax.set_position([pos.x0, pos.y0 + 0.2, pos.width, pos.height])

    distance = get_distance(get_displacement(config.planet_position, config.initial_position))
    orbital_velocity = np.sqrt(config.gravitational_constant * config.earths_mass / distance)
    escape_velocity = np.sqrt(2) * orbital_velocity

    min_speed = orbital_velocity * 1/2
    initial_speed = 1022.0
    max_speed = escape_velocity * 3/2

    button_axis = fig.add_axes([0.1, 0.1, 0.25, 0.075])
    button = Button(button_axis, 'Toggle playback')
    button.on_clicked(playback_toggle_handler)

    speed_axis = fig.add_axes([0.25, 0, 0.55, 0.03])
    speed_slider = Slider(ax=speed_axis, label='Launch speed', valmin=min_speed, valmax=max_speed, valinit=initial_speed)

    milestones = {
        '50% Orbital': 0.5 * orbital_velocity,
        'Orbital': orbital_velocity,
        'Escape': escape_velocity,
        '150% Escape': 1.5 * escape_velocity
    }

    for label, value in milestones.items():
        norm_val = (value - min_speed) / (max_speed - min_speed)
        speed_axis.text(norm_val, 1.8, label, transform=speed_axis.transAxes,
        ha='center', va='center', fontsize=8)

    speed_slider.on_changed(speed_change_handler)

    global speed, redraw_event, stop_app_event, pause_event
    pause_event = threading.Event()
    redraw_event = threading.Event()
    redraw_event.set()
    stop_app_event = threading.Event()
    speed = initial_speed
    err = None

    signal.signal(signal.SIGINT, signal_handler)
    fig.canvas.mpl_connect('close_event', figure_close_event)

    while True:
        if stop_app_event.is_set():
            break

        if not redraw_event.is_set():
            plot.pause(event_loop_pause)
            continue

        redraw_event.clear()
        err = draw(ax, speed, redraw_event, pause_event)
        print('Simulation complete')

        if err != None:
            break

    if err != None:
        print('Draw failed with error:\n', err)

    print('Main thread exitting')

def main():
    plot.ion()
    plot.clf()
    start()

if __name__ == '__main__':
    main()
