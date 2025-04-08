import pygame
import random
import math

# Initialize Pygame
pygame.init()

# Constants
WIDTH = 1600  # Increased width for better visualization
HEIGHT = 800 # Increased height for better visualization
DOT_RADIUS = 5
NUM_DOTS = 250
CONTAINER_WIDTH = 40 * 40 # Scaled up for better visualization
CONTAINER_HEIGHT = 20 * 40 # Scaled up for better visualization
DOT_COLOR = (0, 0, 255)  # Blue
COLLISION_COLOR = (255, 0, 0)  # Red
BACKGROUND_COLOR = (255, 255, 255)  # White
WALL_COLOR = (0, 0, 0) # Black

# Create the screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Molecular Movement Simulation")

# Dot class
class Dot:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = DOT_RADIUS
        self.color = DOT_COLOR
        self.speed_x = random.uniform(-5, 5)
        self.speed_y = random.uniform(-5, 5)
        self.colliding = False  # Flag to indicate collision with wall

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
        # Calculate the angle between the two dots
        dx = self.x - other.x
        dy = self.y - other.y
        distance = math.sqrt(dx**2 + dy**2)

        # Check for collision
        if distance < self.radius + other.radius:
            # Normalize the vector between the dots
            nx = dx / distance
            ny = dy / distance

            # Calculate the dot product of the relative velocity and the normal vector
            dp = (self.speed_x - other.speed_x) * nx + (self.speed_y - other.speed_y) * ny

            # Calculate the impulse scalar
            impulse = (2 * dp) / (1 + 1)  # Assuming equal mass

            # Update the velocities
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
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), self.radius)
        self.colliding = False  # Reset collision flag after drawing


# Create dots
dots = []
for _ in range(NUM_DOTS):
    x = random.uniform(DOT_RADIUS, CONTAINER_WIDTH - DOT_RADIUS)
    y = random.uniform(DOT_RADIUS, CONTAINER_HEIGHT - DOT_RADIUS)
    dots.append(Dot(x, y))

# Main game loop
running = True
clock = pygame.time.Clock()

while running:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Game logic
    for dot in dots:
        dot.move()
        dot.bounce_off_walls()

        # Check for collisions with other dots
        for other_dot in dots:
            if dot != other_dot:
                dot.bounce_off_dot(other_dot)

    # Drawing
    screen.fill(BACKGROUND_COLOR)
    pygame.draw.rect(screen, WALL_COLOR, (0, 0, CONTAINER_WIDTH, CONTAINER_HEIGHT), 2)  # Draw container
    for dot in dots:
        dot.draw(screen)

    # Update the display
    pygame.display.flip()

    # Control the frame rate
    clock.tick(60)

# Quit Pygame
pygame.quit()
