import pygame
import random
import math
import cv2 # Make sure OpenCV is installed (pip install opencv-python)
import numpy as np

# Initialize Pygame
pygame.init()

# Constants
WIDTH = 1920
HEIGHT = 1080
MIN_DOT_RADIUS = 1
MAX_DOT_RADIUS = 5
NUM_DOTS = 2500 # Adjust for performance if needed
CONTAINER_WIDTH = WIDTH
CONTAINER_HEIGHT = HEIGHT
DOT_COLOR = (0, 0, 255)
COLLISION_COLOR = (255, 0, 0)
BACKGROUND_COLOR = (255, 255, 255)
WALL_COLOR = (0, 0, 0)
FPS = 60 # Frames per second for the simulation and video

# --- Speed Scaling Parameters ---
INITIAL_SPEED_MULTIPLIER = 1.0  # Start at 10% of base speed
FINAL_SPEED_MULTIPLIER = 1.0    # Reach 100% of base speed
TIME_TO_REACH_FINAL_SPEED_MS = 1000 # Time in milliseconds (e.g., 1 seconds)

# --- Temporary Partition Parameters ---
PARTITION_DURATION_MS = 15000  # How long the partition stays active (e.g., 15 seconds)
PARTITION_X = WIDTH // 2       # Position the partition in the middle
PARTITION_THICKNESS = 4        # How thick the partition line is
PARTITION_COLOR = (0, 255, 0)  # Green color for the partition
# --- End New Parameters ---


# Create the screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Simulation: Speed Ramp + Temp Partition + Video Recording")

# Dot class
class Dot:
    def __init__(self, x, y, partition_active, partition_x, partition_thickness):
        self.radius = random.uniform(MIN_DOT_RADIUS, MAX_DOT_RADIUS)
        # Initial position adjustment to avoid starting inside the active partition
        if partition_active:
            partition_left = partition_x - partition_thickness / 2
            partition_right = partition_x + partition_thickness / 2
            while partition_left - self.radius < x < partition_right + self.radius:
                 # If initial random position overlaps partition, try placing it on one side
                 if random.random() < 0.5: # Place on left
                     x = random.uniform(self.radius + 1, partition_left - self.radius -1)
                 else: # Place on right
                     x = random.uniform(partition_right + self.radius + 1, CONTAINER_WIDTH - self.radius -1)
                 y = random.uniform(self.radius + 1, CONTAINER_HEIGHT - self.radius - 1) # Also re-randomize y maybe

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

    # Modify wall bounce to include partition check
    def bounce_off_walls(self, partition_active, partition_x, partition_thickness):
        hit_boundary = False
        partition_left = partition_x - partition_thickness / 2
        partition_right = partition_x + partition_thickness / 2

        # --- Wall Bouncing ---
        if self.x <= self.radius:
            self.x = self.radius # Prevent sticking
            self.current_speed_x *= -1
            hit_boundary = True
        elif self.x >= CONTAINER_WIDTH - self.radius:
            self.x = CONTAINER_WIDTH - self.radius # Prevent sticking
            self.current_speed_x *= -1
            hit_boundary = True

        if self.y <= self.radius:
            self.y = self.radius # Prevent sticking
            self.current_speed_y *= -1
            hit_boundary = True
        elif self.y >= CONTAINER_HEIGHT - self.radius:
            self.y = CONTAINER_HEIGHT - self.radius # Prevent sticking
            self.current_speed_y *= -1
            hit_boundary = True

        # --- Partition Bouncing (only if active) ---
        if partition_active:
            # Check collision with the partition's effective area
            # Moving right towards partition
            if self.current_speed_x > 0 and self.x + self.radius >= partition_left and self.x < partition_left:
                # Check if previous position was clearly left of the partition
                prev_x = self.x - self.current_speed_x # Estimate previous position (ignoring multiplier for simplicity here)
                if prev_x + self.radius < partition_left:
                    self.x = partition_left - self.radius # Place exactly at boundary
                    self.current_speed_x *= -1
                    hit_boundary = True
            # Moving left towards partition
            elif self.current_speed_x < 0 and self.x - self.radius <= partition_right and self.x > partition_right:
                 # Check if previous position was clearly right of the partition
                prev_x = self.x - self.current_speed_x # Estimate previous position
                if prev_x - self.radius > partition_right:
                    self.x = partition_right + self.radius # Place exactly at boundary
                    self.current_speed_x *= -1
                    hit_boundary = True

        if hit_boundary:
            self.colliding = True


    def bounce_off_dot(self, other):
        dx = self.x - other.x
        dy = self.y - other.y
        # Avoid division by zero if dots overlap perfectly
        distance_sq = dx**2 + dy**2
        min_dist = self.radius + other.radius
        min_dist_sq = min_dist**2

        # Use squared distance for initial check (faster)
        if 0 < distance_sq < min_dist_sq:
            distance = math.sqrt(distance_sq) # Calculate exact distance only if needed

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
                # Calculate impulse (assuming equal mass for simplicity)
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
                # Move dots apart along the collision normal
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
        # Ensure dot coordinates are valid before getting cell
        dot.x = max(dot.radius, min(dot.x, self.width - dot.radius))
        dot.y = max(dot.radius, min(dot.y, self.height - dot.radius))
        cell_x, cell_y = self.get_cell_coordinates(dot.x, dot.y)
        if (cell_x, cell_y) not in self.grid:
            self.grid[(cell_x, cell_y)] = []
        self.grid[(cell_x, cell_y)].append(dot)

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
                        # Avoid adding the dot itself if it's in the center cell's list
                        # The main collision loop already checks `dot is not other_dot`
                        nearby_dots.extend(self.grid[(neighbor_x, neighbor_y)])
        # Remove the dot itself from the list of nearby dots if present
        # While the main loop handles `dot is not other_dot`, this can slightly optimize
        # by reducing list size if the dot is found within its own cell's results.
        # Use list comprehension for potential efficiency / clarity
        return [d for d in nearby_dots if d is not dot]


# --- Simulation Setup ---
start_time = pygame.time.get_ticks() # Record start time for global effects

# Determine initial partition state based on time 0
initial_partition_active = (PARTITION_DURATION_MS > 0)

# Create dots (pass initial partition state for safe placement)
dots = []
for _ in range(NUM_DOTS):
    # Ensure dots start well within bounds
    buffer = MAX_DOT_RADIUS + 1
    x = random.uniform(buffer, CONTAINER_WIDTH - buffer)
    y = random.uniform(buffer, CONTAINER_HEIGHT - buffer)
    dots.append(Dot(x, y, initial_partition_active, PARTITION_X, PARTITION_THICKNESS))

# Create the grid
# Adjust cell size based on max radius and typical movement step
CELL_SIZE = int(MAX_DOT_RADIUS * 2 * FINAL_SPEED_MULTIPLIER * 2) + 1 # A bit larger is safer
grid = Grid(CONTAINER_WIDTH, CONTAINER_HEIGHT, CELL_SIZE)

# Video recording setup using OpenCV
output_filename = "partition.mp4"
fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Codec for .mp4
video = cv2.VideoWriter(output_filename, fourcc, FPS, (WIDTH, HEIGHT))
print(f"Recording video to {output_filename}...")

# Main game loop
running = True
clock = pygame.time.Clock()


while running:
    # --- Time-dependent Calculations ---
    current_time = pygame.time.get_ticks()
    elapsed_time = current_time - start_time

    # 1. Calculate current speed multiplier
    if elapsed_time >= TIME_TO_REACH_FINAL_SPEED_MS:
        current_speed_multiplier = FINAL_SPEED_MULTIPLIER
    elif TIME_TO_REACH_FINAL_SPEED_MS > 0 : # Avoid division by zero
        time_fraction = elapsed_time / TIME_TO_REACH_FINAL_SPEED_MS
        current_speed_multiplier = INITIAL_SPEED_MULTIPLIER + (FINAL_SPEED_MULTIPLIER - INITIAL_SPEED_MULTIPLIER) * time_fraction
    else: # If time to reach is 0, just use the final multiplier
        current_speed_multiplier = FINAL_SPEED_MULTIPLIER

    # 2. Determine if the partition is active
    partition_active = elapsed_time < PARTITION_DURATION_MS

    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # --- Game Logic ---
    grid.clear()
    for dot in dots:
        # Pass the multiplier to the move method
        dot.move(current_speed_multiplier)
        # Pass partition state to bounce logic
        dot.bounce_off_walls(partition_active, PARTITION_X, PARTITION_THICKNESS)
        # Add dot to grid *after* movement and boundary checks
        grid.add_dot(dot)

    # --- Collision Detection and Response (Dot vs Dot) ---
    processed_pairs = set() # To avoid checking collisions twice (A-B and B-A)
    for dot in dots:
        nearby_dots = grid.get_nearby_dots(dot) # get_nearby_dots now excludes self
        for other_dot in nearby_dots:
            # Create a unique identifier for the pair
            pair = tuple(sorted((id(dot), id(other_dot))))
            if pair not in processed_pairs:
                 dot.bounce_off_dot(other_dot)
                 processed_pairs.add(pair) # Mark pair as processed

    # --- Drawing ---
    screen.fill(BACKGROUND_COLOR)

    # Draw the partition if it's active
    if partition_active:
        partition_rect = pygame.Rect(PARTITION_X - PARTITION_THICKNESS // 2, 0, PARTITION_THICKNESS, HEIGHT)
        pygame.draw.rect(screen, PARTITION_COLOR, partition_rect)

    # Draw container walls (outline)
    pygame.draw.rect(screen, WALL_COLOR, (0, 0, CONTAINER_WIDTH, CONTAINER_HEIGHT), 2)

    # Draw all the dots
    for dot in dots:
        dot.draw(screen) # Draws based on current x, y

    # --- Video Frame Capture ---
    # Important: Capture frame *after* all drawing is complete
    try:
        frame = pygame.surfarray.array3d(screen)
        frame = frame.transpose([1, 0, 2])  # Pygame (w,h,c) to OpenCV (h,w,c)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR) # Pygame RGB to OpenCV BGR
        video.write(frame)
    except Exception as e:
        print(f"Error capturing/writing frame: {e}")
        # Optionally decide if you want to stop running on error
        # running = False

    # --- Display Update ---
    pygame.display.flip()

    # --- Frame Rate Control ---
    clock.tick(FPS)

# --- Cleanup ---
print("Simulation finished. Releasing video writer...")
video.release() # Finalize the video file
cv2.destroyAllWindows() # Close any OpenCV windows (usually none)
pygame.quit()
print("Video saved successfully.")