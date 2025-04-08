import pygame
import random
import math
import cv2
import time
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
PARTITION_COLOR = (0, 0, 0)

FPS=60

# Create the screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Molecular Movement Simulation with Spatial Partitioning and Random Radius")

# Font for timer
font = pygame.font.Font(None, 36)

# Dot class
class Dot:
    def __init__(self, x, y):
        self.radius = random.uniform(MIN_DOT_RADIUS, MAX_DOT_RADIUS)  # Random radius
        self.x = x
        self.y = y
        self.color = DOT_COLOR
        self.speed_x = random.uniform(-5, 5)
        self.speed_y = random.uniform(-5, 5)
        self.colliding = False

    def move(self):
        self.x += self.speed_x
        self.y += self.speed_y

    def bounce_off_walls(self):
        if self.x <= self.radius or self.x >= CONTAINER_WIDTH - self.radius:
            self.speed_x *= -1
            self.colliding = True
        if self.y <= self.radius or self.y >= CONTAINER_HEIGHT - self.radius:
            self.speed_y *= -1
            self.colliding = True

    def bounce_off_dot(self, other):
        dx = self.x - other.x
        dy = self.y - other.y
        distance = math.sqrt(dx**2 + dy**2)

        if distance < self.radius + other.radius:
            nx = dx / distance
            ny = dy / distance
            dp = (self.speed_x - other.speed_x) * nx + (self.speed_y - other.speed_y) * ny
            impulse = (2 * dp) / (1 + 1)
            self.speed_x -= impulse * nx
            self.speed_y -= impulse * ny
            other.speed_x += impulse * nx
            other.speed_y += impulse * ny
            self.colliding = True
            other.colliding = True

    def draw(self, surface):
        if self.colliding:
            color = COLLISION_COLOR
        else:
            color = self.color
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), int(self.radius))  # Draw circle
        self.colliding = False

# Grid class for spatial partitioning
class Grid:
    def __init__(self, width, height, cell_size):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.grid = {}

    def get_cell_coordinates(self, x, y):
        return int(x // self.cell_size), int(y // self.cell_size)

    def add_dot(self, dot):
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
                if (neighbor_x, neighbor_y) in self.grid:
                    nearby_dots.extend(self.grid[(neighbor_x, neighbor_y)])
        return nearby_dots

# Create dots on the right side of the partition
dots = []
for _ in range(NUM_DOTS):
    x = random.uniform(WIDTH // 2 + MAX_DOT_RADIUS, CONTAINER_WIDTH - MAX_DOT_RADIUS)  # Ensure dots stay within bounds on the right side of the partition
    y = random.uniform(MAX_DOT_RADIUS, CONTAINER_HEIGHT - MAX_DOT_RADIUS)  # Ensure dots stay within bounds vertically
    dots.append(Dot(x, y))

# Create the grid
CELL_SIZE = 4 * MAX_DOT_RADIUS  # Adjust cell size based on the maximum radius
grid = Grid(CONTAINER_WIDTH, CONTAINER_HEIGHT, CELL_SIZE)

# Video recording setup using OpenCV
output_filename = "partition.mp4"
fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Codec for .mp4
video = cv2.VideoWriter(output_filename, fourcc, FPS, (WIDTH, HEIGHT))
print(f"Recording video to {output_filename}...")

# Main game loop variables
running = True
clock = pygame.time.Clock()
start_time = pygame.time.get_ticks()
last_displayed_second = -1

timer_surface = None

timer_position = (WIDTH -10, 10)

partition_exists = True

while running:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Game logic
    grid.clear()
    for dot in dots:
        dot.move()
        dot.bounce_off_walls()
        
        # Check for partition collision if it exists
        if partition_exists and dot.x - dot.radius <= WIDTH // 2:
            dot.speed_x *= -1
            dot.colliding = True
        
        grid.add_dot(dot)

    for dot in dots:
        nearby_dots = grid.get_nearby_dots(dot)
        for other_dot in nearby_dots:
            if dot != other_dot:
                dot.bounce_off_dot(other_dot)

    # Remove partition after 10 seconds and allow free movement inside the entire container.
    current_ticks = pygame.time.get_ticks()
    elapsed_time = current_ticks - start_time
    
    elapsed_seconds = elapsed_time // 1000
    
    if elapsed_time > 20000:
        partition_exists = False

    # Drawing
    screen.fill(BACKGROUND_COLOR)
    
    # Draw partition if it exists.
    if partition_exists:
        pygame.draw.line(screen, PARTITION_COLOR, (WIDTH // 2, 0), (WIDTH // 2, HEIGHT), 2)
    
    pygame.draw.rect(screen, WALL_COLOR, (0, 0, CONTAINER_WIDTH, CONTAINER_HEIGHT), 2)
    
    for dot in dots:
        dot.draw(screen)
    
        # --- Video Frame Capture ---
    # Capture the current screen content after all drawing is done
    try:
        frame = pygame.surfarray.array3d(screen)
        # Pygame surface uses (width, height, channels) and RGB format.
        # OpenCV video writer expects (height, width, channels) and BGR format.
        frame = frame.transpose([1, 0, 2]) # Swap width and height axes
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR) # Convert RGB to BGR
        # Write the processed frame to the video file
        video.write(frame)
    except Exception as e:
        print(f"Error capturing/writing video frame: {e}")
        running = False # Optional: stop simulation if video writing fails

    # Update the display.
    pygame.display.flip()
    
    # Update the display.
    pygame.display.flip()

    # Control the frame rate.
    clock.tick(FPS)

print("Simulation finished. Releasing video writer...")
video.release() # Finalize the video file
cv2.destroyAllWindows() # Close any OpenCV windows (usually none)
pygame.quit()
print("Video saved successfully.")