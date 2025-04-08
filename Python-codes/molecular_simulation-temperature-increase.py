import pygame
import random
import math
import cv2
import numpy as np

# Initialize Pygame
pygame.init()

# Constants
WIDTH = 1920
HEIGHT = 1080
MIN_DOT_RADIUS = 1
MAX_DOT_RADIUS = 5
NUM_DOTS = 2500
CONTAINER_WIDTH = WIDTH
CONTAINER_HEIGHT = HEIGHT
DOT_COLOR = (0, 0, 255)
COLLISION_COLOR = (255, 0, 0)
BACKGROUND_COLOR = (255, 255, 255)
WALL_COLOR = (0, 0, 0)
FPS = 60 # Frames per second for the video

# --- New Speed Scaling Parameters ---
INITIAL_SPEED_MULTIPLIER = 0.001  # Start at 1% of base speed
FINAL_SPEED_MULTIPLIER = 2.0    # Reach 200% of base speed
TIME_TO_REACH_FINAL_SPEED_MS = 1000000 # Time in milliseconds (e.g., 10 seconds)
# --- End New Parameters ---


# Create the screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Molecular Movement Simulation with Speed Ramp-up")

# Dot class
class Dot:
    def __init__(self, x, y):
        self.radius = random.uniform(MIN_DOT_RADIUS, MAX_DOT_RADIUS)  # Random radius
        self.x = x
        self.y = y
        self.color = DOT_COLOR
        # Store the *base* speed
        self.base_speed_x = random.uniform(-5, 5)
        self.base_speed_y = random.uniform(-5, 5)
        # These will be updated by collisions/bounces
        self.current_speed_x = self.base_speed_x
        self.current_speed_y = self.base_speed_y
        self.colliding = False

    # Modify move to accept a speed multiplier
    def move(self, speed_multiplier):
        # Apply the multiplier only for position update
        self.x += self.current_speed_x * speed_multiplier
        self.y += self.current_speed_y * speed_multiplier

    def bounce_off_walls(self):
        # Check collision based on current position
        hit_wall = False
        if self.x <= self.radius:
            self.x = self.radius # Prevent sticking
            self.current_speed_x *= -1
            hit_wall = True
        elif self.x >= CONTAINER_WIDTH - self.radius:
            self.x = CONTAINER_WIDTH - self.radius # Prevent sticking
            self.current_speed_x *= -1
            hit_wall = True

        if self.y <= self.radius:
            self.y = self.radius # Prevent sticking
            self.current_speed_y *= -1
            hit_wall = True
        elif self.y >= CONTAINER_HEIGHT - self.radius:
            self.y = CONTAINER_HEIGHT - self.radius # Prevent sticking
            self.current_speed_y *= -1
            hit_wall = True

        if hit_wall:
            self.colliding = True


    def bounce_off_dot(self, other):
        dx = self.x - other.x
        dy = self.y - other.y
        # Avoid division by zero if dots overlap perfectly
        distance_sq = dx**2 + dy**2
        min_dist = self.radius + other.radius
        min_dist_sq = min_dist**2

        if distance_sq > 0 and distance_sq < min_dist_sq:
            distance = math.sqrt(distance_sq)

            # --- Collision Response (using current speeds) ---
            nx = dx / distance
            ny = dy / distance

            # Relative velocity
            relative_vx = self.current_speed_x - other.current_speed_x
            relative_vy = self.current_speed_y - other.current_speed_y

            # Dot product of relative velocity and normal vector
            dp = relative_vx * nx + relative_vy * ny

            # If dots are moving towards each other (dp < 0)
            if dp < 0:
                # Calculate impulse (assuming equal mass for simplicity, hence m1=m2=1, factor is 2*dp/(m1+m2) -> dp)
                # More accurate: impulse_magnitude = (2 * dp) / (mass1 + mass2), here mass assumed 1
                impulse_magnitude = dp # Simplified impulse for equal mass

                # Apply impulse to change velocities
                self.current_speed_x -= impulse_magnitude * nx
                self.current_speed_y -= impulse_magnitude * ny
                other.current_speed_x += impulse_magnitude * nx
                other.current_speed_y += impulse_magnitude * ny

                self.colliding = True
                other.colliding = True

                # --- Prevent sticking/overlap ---
                overlap = min_dist - distance
                # Move dots apart along the collision normal, proportionally to their (inverse) mass (here equal)
                move_amount = overlap * 0.5 # Move each dot half the overlap
                self.x += move_amount * nx
                self.y += move_amount * ny
                other.x -= move_amount * nx
                other.y -= move_amount * ny


    def draw(self, surface):
        if self.colliding:
            color = COLLISION_COLOR
        else:
            color = self.color
        # Ensure radius and position are integers for drawing
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), int(self.radius))
        self.colliding = False # Reset collision flag after drawing

# Grid class for spatial partitioning (no changes needed)
class Grid:
    def __init__(self, width, height, cell_size):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.grid = {}

    def get_cell_coordinates(self, x, y):
        # Clamp coordinates to be within grid bounds
        cell_x = max(0, min(int(x // self.cell_size), int(self.width // self.cell_size) - 1))
        cell_y = max(0, min(int(y // self.cell_size), int(self.height // self.cell_size) - 1))
        return cell_x, cell_y

    def add_dot(self, dot):
        cell_x, cell_y = self.get_cell_coordinates(dot.x, dot.y)
        if (cell_x, cell_y) not in self.grid:
            self.grid[(cell_x, cell_y)] = []
        self.grid[(cell_x, cell_y)].append(dot) # Corrected append

    def clear(self):
        self.grid = {}

    def get_nearby_dots(self, dot):
        nearby_dots = []
        cell_x, cell_y = self.get_cell_coordinates(dot.x, dot.y)

        for i in range(-1, 2):
            for j in range(-1, 2):
                neighbor_x = cell_x + i
                neighbor_y = cell_y + j
                # Check if the neighbor cell coordinates are valid
                if 0 <= neighbor_x < int(self.width // self.cell_size) and \
                   0 <= neighbor_y < int(self.height // self.cell_size):
                    if (neighbor_x, neighbor_y) in self.grid:
                        nearby_dots.extend(self.grid[(neighbor_x, neighbor_y)])
        return nearby_dots

# Create dots
dots = []
for _ in range(NUM_DOTS):
    # Ensure dots start well within bounds to avoid immediate wall collision issues
    buffer = MAX_DOT_RADIUS + 1
    x = random.uniform(buffer, CONTAINER_WIDTH - buffer)
    y = random.uniform(buffer, CONTAINER_HEIGHT - buffer)
    dots.append(Dot(x, y))

# Create the grid
# Adjust cell size based on max radius and typical movement step
CELL_SIZE = int(MAX_DOT_RADIUS * 2 * FINAL_SPEED_MULTIPLIER * 2) + 1 # A bit larger is safer
grid = Grid(CONTAINER_WIDTH, CONTAINER_HEIGHT, CELL_SIZE)

# Video recording setup
fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Use 'mp4v' for .mp4 (more compatible)
video = cv2.VideoWriter("simulation_speed_ramp.mp4", fourcc, FPS, (WIDTH, HEIGHT)) # Output video file

# Main game loop
running = True
clock = pygame.time.Clock()
start_time = pygame.time.get_ticks() # Record start time

while running:
    # Calculate elapsed time and current speed multiplier
    current_time = pygame.time.get_ticks()
    elapsed_time = current_time - start_time

    if elapsed_time >= TIME_TO_REACH_FINAL_SPEED_MS:
        current_speed_multiplier = FINAL_SPEED_MULTIPLIER
    elif TIME_TO_REACH_FINAL_SPEED_MS > 0 : # Avoid division by zero
        time_fraction = elapsed_time / TIME_TO_REACH_FINAL_SPEED_MS
        # Linear interpolation between initial and final multiplier
        current_speed_multiplier = INITIAL_SPEED_MULTIPLIER + (FINAL_SPEED_MULTIPLIER - INITIAL_SPEED_MULTIPLIER) * time_fraction
    else: # If time to reach is 0, just use the final multiplier
        current_speed_multiplier = FINAL_SPEED_MULTIPLIER

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Game logic
    grid.clear()
    for dot in dots:
        # Pass the multiplier to the move method
        dot.move(current_speed_multiplier)
        dot.bounce_off_walls() # Wall bouncing affects current_speed_x/y directly
        grid.add_dot(dot)

    # Collision detection and response
    for dot in dots:
        nearby_dots = grid.get_nearby_dots(dot)
        for other_dot in nearby_dots:
            # Important: Ensure a dot doesn't collide with itself!
            if dot is not other_dot:
                 dot.bounce_off_dot(other_dot) # Collision affects current_speed_x/y directly

    # Drawing
    screen.fill(BACKGROUND_COLOR)
    pygame.draw.rect(screen, WALL_COLOR, (0, 0, CONTAINER_WIDTH, CONTAINER_HEIGHT), 2)
    for dot in dots:
        dot.draw(screen) # Draws based on current x, y

    # Capture frame
    # Important: Ensure screen capture happens *after* all drawing is complete
    frame = pygame.surfarray.array3d(screen)
    frame = frame.transpose([1, 0, 2])  # Transpose for OpenCV
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)  # Convert RGB to BGR for OpenCV
    video.write(frame)


    # Update the display
    pygame.display.flip()

    # Control the frame rate
    clock.tick(FPS)

# Release video writer and quit
video.release()
cv2.destroyAllWindows()
pygame.quit()