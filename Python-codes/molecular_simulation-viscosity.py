import pygame
import random
import math
import cv2
import numpy as np
import sys # Import sys for exiting gracefully

# Initialize Pygame
pygame.init()

# Constants
WIDTH = 1920
HEIGHT = 1080
MIN_DOT_RADIUS = 2
MAX_DOT_RADIUS = 5
NUM_DOTS = 5000
CONTAINER_WIDTH = WIDTH
CONTAINER_HEIGHT = HEIGHT
DOT_COLOR = (0, 0, 255)
COLLISION_COLOR = (255, 0, 0)
BACKGROUND_COLOR = (255, 255, 255)
WALL_COLOR = (0, 0, 0)
FPS = 60

# Simulation Constants
INITIAL_SPEED_RANGE = 0.5
TOP_WALL_VELOCITY_X = 10.0 # Effective velocity for physics

# --- Visual Wall Movement Constants ---
DRAW_MOVING_WALL_MARKERS = True # Set to False to disable visual markers
NUM_WALL_MARKERS = 20
WALL_MARKER_HEIGHT = 8
WALL_MARKER_COLOR = (100, 100, 100) # Grey color for markers
# Visual speed of markers - can be different from physics speed if desired
VISUAL_WALL_MARKER_SPEED = TOP_WALL_VELOCITY_X # Match physics speed
# --- End Visual Wall Movement Constants ---


# Create the screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Shear Flow Simulation with Visual Moving Wall")

# Dot class (remains the same as previous version)
class Dot:
    def __init__(self, x, y):
        self.radius = random.uniform(MIN_DOT_RADIUS, MAX_DOT_RADIUS)
        self.mass = self.radius**2 # Mass proportional to area
        self.x = x
        self.y = y
        self.color = DOT_COLOR
        self.speed_x = random.uniform(-INITIAL_SPEED_RANGE, INITIAL_SPEED_RANGE)
        self.speed_y = random.uniform(-INITIAL_SPEED_RANGE, INITIAL_SPEED_RANGE)
        self.colliding = False
        self.last_collision_wall = None

    def move(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.colliding = False
        self.last_collision_wall = None

    def bounce_off_walls(self, top_wall_velocity_x):
        collided = False
        # Left wall
        if self.x <= self.radius:
            self.speed_x = abs(self.speed_x)
            self.x = self.radius
            collided = True
            self.last_collision_wall = 'left'
        # Right wall
        elif self.x >= CONTAINER_WIDTH - self.radius:
            self.speed_x = -abs(self.speed_x)
            self.x = CONTAINER_WIDTH - self.radius
            collided = True
            self.last_collision_wall = 'right'

        # Top wall (Moving Boundary Condition)
        if self.y <= self.radius:
            self.speed_y = abs(self.speed_y)
            self.y = self.radius
            self.speed_x = top_wall_velocity_x # Apply wall's velocity
            collided = True
            self.last_collision_wall = 'top'
        # Bottom wall
        elif self.y >= CONTAINER_HEIGHT - self.radius:
            self.speed_y = -abs(self.speed_y)
            self.y = CONTAINER_HEIGHT - self.radius
            # Optional: Simulate no-slip on bottom wall
            # self.speed_x *= 0.9 # Apply some friction/drag
            # self.speed_x = 0 # Full no-slip
            collided = True
            self.last_collision_wall = 'bottom'

        if collided:
            self.colliding = True


    def bounce_off_dot(self, other):
        dx = other.x - self.x
        dy = other.y - self.y
        distance_sq = dx**2 + dy**2
        min_dist = self.radius + other.radius
        min_dist_sq = min_dist**2

        if distance_sq < min_dist_sq and distance_sq > 1e-6:
            distance = math.sqrt(distance_sq)
            overlap = (min_dist - distance) / 2.0
            nx_overlap = dx / distance
            ny_overlap = dy / distance
            self.x -= overlap * nx_overlap
            self.y -= overlap * ny_overlap
            other.x += overlap * nx_overlap
            other.y += overlap * ny_overlap

            # Recalculate after overlap resolution
            dx = other.x - self.x
            dy = other.y - self.y
            distance = math.sqrt(dx**2 + dy**2) if distance_sq > 1e-9 else 1e-5 # Avoid zero distance

            nx = dx / distance
            ny = dy / distance

            dvx = self.speed_x - other.speed_x
            dvy = self.speed_y - other.speed_y
            dot_product = dvx * nx + dvy * ny

            if dot_product < 0: # Only collide if moving towards each other
                m1 = self.mass
                m2 = other.mass
                impulse_scalar = (2 * dot_product) / (m1 + m2)

                self.speed_x -= impulse_scalar * m2 * nx
                self.speed_y -= impulse_scalar * m2 * ny
                other.speed_x += impulse_scalar * m1 * nx
                other.speed_y += impulse_scalar * m1 * ny

                self.colliding = True
                other.colliding = True

    def draw(self, surface):
        color = COLLISION_COLOR if self.colliding else self.color
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), int(self.radius))

# Grid class (remains the same)
class Grid:
    def __init__(self, width, height, cell_size):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.cols = int(math.ceil(width / cell_size))
        self.rows = int(math.ceil(height / cell_size))
        self.grid = {}

    def get_cell_coordinates(self, x, y):
        col = max(0, min(self.cols - 1, int(x // self.cell_size)))
        row = max(0, min(self.rows - 1, int(y // self.cell_size)))
        return col, row

    def add_dot(self, dot):
        cell_coords = self.get_cell_coordinates(dot.x, dot.y)
        if cell_coords not in self.grid:
            self.grid[cell_coords] = []
        self.grid[cell_coords].append(dot)

    def clear(self):
        self.grid = {}

    def get_nearby_dots(self, dot):
        nearby_dots = []
        center_col, center_row = self.get_cell_coordinates(dot.x, dot.y)
        for i in range(-1, 2):
            for j in range(-1, 2):
                check_col = center_col + i
                check_row = center_row + j
                if 0 <= check_col < self.cols and 0 <= check_row < self.rows:
                    cell_coords = (check_col, check_row)
                    if cell_coords in self.grid:
                        nearby_dots.extend(self.grid[cell_coords])
        return nearby_dots

# --- Dot Creation --- (remains the same)
dots = []
attempts = 0
max_attempts = NUM_DOTS * 10
while len(dots) < NUM_DOTS and attempts < max_attempts:
    radius = random.uniform(MIN_DOT_RADIUS, MAX_DOT_RADIUS)
    x = random.uniform(radius, CONTAINER_WIDTH - radius)
    y = random.uniform(radius, CONTAINER_HEIGHT - radius)
    # Optional overlap check can be added here if needed, but might slow down init
    dots.append(Dot(x, y))
    attempts += 1

if len(dots) < NUM_DOTS:
    print(f"Warning: Placed {len(dots)} out of {NUM_DOTS} dots.")

# Create the grid
CELL_SIZE = 2.1 * MAX_DOT_RADIUS
grid = Grid(CONTAINER_WIDTH, CONTAINER_HEIGHT, CELL_SIZE)

# --- Initialize Wall Markers ---
wall_marker_positions = []
if DRAW_MOVING_WALL_MARKERS and NUM_WALL_MARKERS > 0:
    spacing = CONTAINER_WIDTH / NUM_WALL_MARKERS
    for i in range(NUM_WALL_MARKERS):
        wall_marker_positions.append(i * spacing)
# --- End Initialize Wall Markers ---

# Video recording setup (Optional)
RECORD_VIDEO = True # Set to True to enable recording
video = None
if RECORD_VIDEO:
    try:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_filename = "shear_flow_simulation_moving_wall.mp4"
        video = cv2.VideoWriter(video_filename, fourcc, FPS, (WIDTH, HEIGHT))
        print(f"Recording video to {video_filename}")
    
    except Exception as e:
        print(f"Error initializing video writer: {e}")
        RECORD_VIDEO = False

# Main game loop
running = True
clock = pygame.time.Clock()

while running:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

    # --- Update Wall Markers ---
    if DRAW_MOVING_WALL_MARKERS:
        for i in range(len(wall_marker_positions)):
            # Move marker to the right based on visual speed
            wall_marker_positions[i] += VISUAL_WALL_MARKER_SPEED
            # Wrap marker around if it goes past the right edge
            if wall_marker_positions[i] > CONTAINER_WIDTH:
                wall_marker_positions[i] -= CONTAINER_WIDTH # Wrap back to the left
    # --- End Update Wall Markers ---


    # --- Game logic ---
    grid.clear()
    for dot in dots:
        dot.move()
        dot.bounce_off_walls(TOP_WALL_VELOCITY_X)
        grid.add_dot(dot)

    processed_pairs = set()
    for dot in dots:
        nearby_dots = grid.get_nearby_dots(dot)
        for other_dot in nearby_dots:
            if dot is not other_dot:
                pair_key = tuple(sorted((id(dot), id(other_dot))))
                if pair_key not in processed_pairs:
                    dot.bounce_off_dot(other_dot)
                    processed_pairs.add(pair_key)

    # --- Drawing ---
    screen.fill(BACKGROUND_COLOR)

    # Draw the container walls (static box)
    pygame.draw.rect(screen, WALL_COLOR, (0, 0, CONTAINER_WIDTH, CONTAINER_HEIGHT), 2)

    # --- Draw Moving Wall Markers ---
    if DRAW_MOVING_WALL_MARKERS:
        for marker_x in wall_marker_positions:
            # Draw a small vertical line at the top edge
            start_pos = (int(marker_x), 0)
            end_pos = (int(marker_x), WALL_MARKER_HEIGHT)
            pygame.draw.line(screen, WALL_MARKER_COLOR, start_pos, end_pos, 2) # Line thickness 2
    # --- End Draw Moving Wall Markers ---

    # Draw the dots
    for dot in dots:
        dot.draw(screen)

    # --- Video Frame Capture (Optional) ---
    if RECORD_VIDEO and video is not None:
        try:
            frame = pygame.surfarray.array3d(screen)
            frame = frame.transpose([1, 0, 2])
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            video.write(frame)
        except Exception as e:
            print(f"Error writing video frame: {e}")
            RECORD_VIDEO = False


    # Update the display
    pygame.display.flip()

    # Control the frame rate
    dt = clock.tick(FPS) / 1000.0 # Get time delta in seconds (optional, not used here yet but good practice)

# --- Cleanup ---
if RECORD_VIDEO and video is not None:
    print("Releasing video writer...")
    video.release()

print("Quitting Pygame...")
pygame.quit()
sys.exit()