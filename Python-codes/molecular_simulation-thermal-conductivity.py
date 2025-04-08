import pygame
import random
import math
import cv2
import numpy as np
import sys

# Initialize Pygame & Font Module
pygame.init()
pygame.font.init() # Initialize the font module

# Constants
WIDTH = 1920
HEIGHT = 1080
MIN_DOT_RADIUS = 2
MAX_DOT_RADIUS = 4
NUM_DOTS = 1000
CONTAINER_WIDTH = WIDTH
CONTAINER_HEIGHT = HEIGHT
BACKGROUND_COLOR = (20, 20, 20)
WALL_COLOR = (150, 150, 150)
FPS = 60

# Thermal Conductivity Constants
HOT_WALL_COLOR = (255, 50, 0)
COLD_WALL_COLOR = (0, 100, 255)
HOT_WALL_TARGET_SPEED = 5.0
COLD_WALL_TARGET_SPEED = 1.0
INITIAL_AVERAGE_SPEED = 0.1 # Low thermal conductivity - 0.1 | High thermal conductivity - (HOT_WALL_TARGET_SPEED + COLD_WALL_TARGET_SPEED) / 2
SPEED_RANDOM_FACTOR = 0.2

# Color Mapping Constants
MIN_SPEED_COLOR = 1.0
MAX_SPEED_COLOR = 5.0

# --- Color Bar Constants ---
COLOR_BAR_X = 50
COLOR_BAR_Y = HEIGHT - 50 # Position near the bottom
COLOR_BAR_WIDTH = WIDTH - 100
COLOR_BAR_HEIGHT = 20
FONT_SIZE = 18
TEXT_COLOR = (230, 230, 230) # Light grey text
try:
    # Try loading a common system font, fall back to default if not found
    GAME_FONT = pygame.font.SysFont("Arial", FONT_SIZE) # Or "Calibri", "Consolas" etc.
except:
    print("Arial font not found, using default pygame font.")
    GAME_FONT = pygame.font.Font(None, FONT_SIZE + 4) # Default font needs slightly larger size
# --- End Color Bar Constants ---


# Create the screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Thermal Conductivity Simulation with Color Bar")

# Helper function for color interpolation (same as before)
def lerp_color(color1, color2, t):
    t = max(0, min(1, t))
    r = int(color1[0] + (color2[0] - color1[0]) * t)
    g = int(color1[1] + (color2[1] - color1[1]) * t)
    b = int(color1[2] + (color2[2] - color1[2]) * t)
    return (r, g, b)

# Helper function to map speed to color (same as before)
def get_color_from_speed(speed, min_speed, max_speed):
    if max_speed <= min_speed: return (0, 255, 0)
    normalized_speed = max(0, min(1, (speed - min_speed) / (max_speed - min_speed)))
    blue, green, yellow, red = (0, 0, 255), (0, 255, 0), (255, 255, 0), (255, 0, 0)
    if normalized_speed < 0.33: return lerp_color(blue, green, normalized_speed / 0.33)
    elif normalized_speed < 0.66: return lerp_color(green, yellow, (normalized_speed - 0.33) / 0.33)
    else: return lerp_color(yellow, red, (normalized_speed - 0.66) / 0.34)

# --- Function to Draw Color Bar ---
def draw_color_bar(surface, font, x, y, width, height, min_val, max_val, label_text="Speed"):
    """Draws a horizontal color bar legend."""
    # Draw the gradient rectangle
    for i in range(width):
        # Calculate the value (speed) corresponding to this horizontal position
        current_val = min_val + (i / width) * (max_val - min_val)
        # Get the color for this value
        color = get_color_from_speed(current_val, min_val, max_val)
        # Draw a thin vertical line
        pygame.draw.line(surface, color, (x + i, y), (x + i, y + height -1))

    # Draw border around the bar (optional)
    pygame.draw.rect(surface, TEXT_COLOR, (x, y, width, height), 1)

    # Create text labels
    min_text = f"{min_val:.1f}"
    max_text = f"{max_val:.1f}"
    label_surf = font.render(label_text, True, TEXT_COLOR)
    min_surf = font.render(min_text, True, TEXT_COLOR)
    max_surf = font.render(max_text, True, TEXT_COLOR)

    # Position and draw labels
    # Label centered above the bar
    label_rect = label_surf.get_rect(midbottom=(x + width / 2, y - 2))
    surface.blit(label_surf, label_rect)

    # Min value label below the left end
    min_rect = min_surf.get_rect(midtop=(x, y + height + 2))
    surface.blit(min_surf, min_rect)

    # Max value label below the right end
    max_rect = max_surf.get_rect(midtop=(x + width, y + height + 2))
    surface.blit(max_surf, max_rect)
# --- End Function to Draw Color Bar ---


# Dot class (remains the same as previous thermal conductivity version)
class Dot:
    def __init__(self, x, y):
        self.radius = random.uniform(MIN_DOT_RADIUS, MAX_DOT_RADIUS)
        self.mass = self.radius**2
        self.x = x
        self.y = y
        angle = random.uniform(0, 2 * math.pi)
        initial_speed = random.uniform(INITIAL_AVERAGE_SPEED * 0.8, INITIAL_AVERAGE_SPEED * 1.2)
        self.speed_x = initial_speed * math.cos(angle)
        self.speed_y = initial_speed * math.sin(angle)
        self.colliding = False

    def get_speed(self):
        return math.sqrt(self.speed_x**2 + self.speed_y**2)

    def set_speed(self, new_speed):
        current_speed = self.get_speed()
        if current_speed > 1e-6:
            factor = new_speed / current_speed
            self.speed_x *= factor
            self.speed_y *= factor
        else:
            angle = random.uniform(0, 2 * math.pi)
            self.speed_x = new_speed * math.cos(angle)
            self.speed_y = new_speed * math.sin(angle)

    def move(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.colliding = False

    def bounce_off_walls(self):
        # Hot Left Wall
        if self.x <= self.radius:
            self.speed_x = abs(self.speed_x)
            target_speed = random.uniform(HOT_WALL_TARGET_SPEED * (1-SPEED_RANDOM_FACTOR),
                                         HOT_WALL_TARGET_SPEED * (1+SPEED_RANDOM_FACTOR))
            self.set_speed(max(target_speed, 0.1))
            self.x = self.radius
        # Cold Right Wall
        elif self.x >= CONTAINER_WIDTH - self.radius:
            self.speed_x = -abs(self.speed_x)
            target_speed = random.uniform(COLD_WALL_TARGET_SPEED * (1-SPEED_RANDOM_FACTOR),
                                         COLD_WALL_TARGET_SPEED * (1+SPEED_RANDOM_FACTOR))
            self.set_speed(max(target_speed, 0.1))
            self.x = CONTAINER_WIDTH - self.radius
        # Insulating Top/Bottom Walls
        if self.y <= self.radius:
            self.speed_y = abs(self.speed_y)
            self.y = self.radius
        elif self.y >= CONTAINER_HEIGHT - self.radius:
            self.speed_y = -abs(self.speed_y)
            self.y = CONTAINER_HEIGHT - self.radius

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

            dx = other.x - self.x
            dy = other.y - self.y
            distance = math.sqrt(dx**2 + dy**2) if distance_sq > 1e-9 else 1e-5
            nx = dx / distance
            ny = dy / distance
            dvx = self.speed_x - other.speed_x
            dvy = self.speed_y - other.speed_y
            dot_product = dvx * nx + dvy * ny

            if dot_product < 0:
                m1 = self.mass
                m2 = other.mass
                impulse_scalar = (2 * dot_product) / (m1 + m2)
                self.speed_x -= impulse_scalar * m2 * nx
                self.speed_y -= impulse_scalar * m2 * ny
                other.speed_x += impulse_scalar * m1 * nx
                other.speed_y += impulse_scalar * m1 * ny

    def draw(self, surface):
        current_speed = self.get_speed()
        color = get_color_from_speed(current_speed, MIN_SPEED_COLOR, MAX_SPEED_COLOR)
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
        # Efficiently remove self from nearby list if present
        # Create a new list excluding 'dot'
        return [d for d in nearby_dots if d is not dot]


# --- Dot Creation --- (remains the same)
dots = []
attempts = 0
max_attempts = NUM_DOTS * 20
while len(dots) < NUM_DOTS and attempts < max_attempts:
    radius = random.uniform(MIN_DOT_RADIUS, MAX_DOT_RADIUS)
    x = random.uniform(radius, CONTAINER_WIDTH - radius)
    y = random.uniform(radius, CONTAINER_HEIGHT - radius)
    # Simple overlap check if needed...
    dots.append(Dot(x, y))
    attempts += 1
if len(dots) < NUM_DOTS: print(f"Warning: Placed {len(dots)} out of {NUM_DOTS} dots.")

# Create the grid
CELL_SIZE = 2.1 * MAX_DOT_RADIUS
grid = Grid(CONTAINER_WIDTH, CONTAINER_HEIGHT, CELL_SIZE)

# Video recording setup (Optional - remains the same)
RECORD_VIDEO = True
video = None
# ... (video setup code) ...

if RECORD_VIDEO:
    try:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_filename = "thermal_conductivity-low.mp4"
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

    # --- Game logic --- (remains the same)
    grid.clear()
    for dot in dots:
        dot.move()
        dot.bounce_off_walls()
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

    # Draw the container walls
    wall_thickness = 5
    pygame.draw.line(screen, HOT_WALL_COLOR, (0, 0), (0, HEIGHT), wall_thickness) # Left Hot
    pygame.draw.line(screen, COLD_WALL_COLOR, (WIDTH-1, 0), (WIDTH-1, HEIGHT), wall_thickness) # Right Cold
    pygame.draw.line(screen, WALL_COLOR, (0, 0), (WIDTH, 0), wall_thickness) # Top
    pygame.draw.line(screen, WALL_COLOR, (0, HEIGHT-1), (WIDTH, HEIGHT-1), wall_thickness) # Bottom

    # Draw the dots
    for dot in dots:
        dot.draw(screen)

    # --- Draw the Color Bar ---
    draw_color_bar(screen, GAME_FONT,
                   COLOR_BAR_X, COLOR_BAR_Y,
                   COLOR_BAR_WIDTH, COLOR_BAR_HEIGHT,
                   MIN_SPEED_COLOR, MAX_SPEED_COLOR,
                   label_text="Particle Speed")
    # --- End Draw the Color Bar ---


    # --- Video Frame Capture (Optional) --- (remains the same)
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
    clock.tick(FPS)

# --- Cleanup ---
# ... (video release code) ...
pygame.font.quit() # Uninitialize font module
pygame.quit()
sys.exit()