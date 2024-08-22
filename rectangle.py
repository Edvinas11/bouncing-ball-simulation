import pygame
import sys
import colorsys

# Initialize Pygame
pygame.init()

# Set up the screen dimensions and create the screen object
screen_width, screen_height = 800, 800
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("DVD Animation with Color Changing Tail")

# Define colors
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
SCREEN_COLOR = (1, 10, 15)

# Define the big rectangle (container)
container_rect = pygame.Rect(150, 151, 489, 512)

# Define the moving rectangle
rect_width, rect_height = 50, 50
moving_rect = pygame.Rect(150, 150, rect_width, rect_height)
rect_speed = [3, 3]  # Speed in x and y directions

# List to store previous positions of the moving rectangle
tail_positions = []

# Hue value for the color changing effect
hue = 0

# Counter to control the recording of tail positions
tail_recording_counter = 0
tail_recording_frequency = 1  # Record a position every .. frames

# Clock to control the frame rate
clock = pygame.time.Clock()

# Load the sound file
bounce_sound = pygame.mixer.Sound('sounds/yeppe.mp3')  # Replace 'bounce.wav' with your sound file

def hsv_to_rgb(h, s, v):
    """Convert HSV to RGB color space."""
    rgb = colorsys.hsv_to_rgb(h, s, v)
    return tuple(int(i * 255) for i in rgb)

# Main loop
running = False
while True:
    # Cap the frame rate
    clock.tick(60)  # Adjusted to 60 frames per second

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                running = True

    if running:
        # Move the rectangle
        moving_rect.x += rect_speed[0]
        moving_rect.y += rect_speed[1]

        # Bounce the rectangle off the edges of the container
        if moving_rect.left <= container_rect.left or moving_rect.right >= container_rect.right:
            rect_speed[0] = -rect_speed[0]
            bounce_sound.play()  # Play sound on bounce
        if moving_rect.top <= container_rect.top or moving_rect.bottom >= container_rect.bottom:
            rect_speed[1] = -rect_speed[1]
            bounce_sound.play()  # Play sound on bounce

        # Increment the tail recording counter
        tail_recording_counter += 1

        # Record the current position to the tail_positions list every `tail_recording_frequency` frames
        if tail_recording_counter >= tail_recording_frequency:
            tail_positions.append((moving_rect.x, moving_rect.y))
            tail_recording_counter = 0

        # Update the hue value
        hue = (hue + 0.005) % 1  # Slower hue increment
        current_color = hsv_to_rgb(hue, 1, 1)  # Convert hue to RGB

        # Fill the background (only draw moving rectangle and tail)
        screen.fill(SCREEN_COLOR)
        
        for pos in tail_positions:
            tail_surface = pygame.Surface((rect_width, rect_height), pygame.SRCALPHA)
            pygame.draw.rect(tail_surface, (*current_color, 100), tail_surface.get_rect(), 2)  # 50% opacity for border
            screen.blit(tail_surface, pos)

        # Draw the moving rectangle
        pygame.draw.rect(screen, WHITE, moving_rect)

        # Draw the container rectangle
        pygame.draw.rect(screen, current_color, container_rect, 10)
        pygame.draw.rect(screen, current_color, pygame.Rect(150, 150, 491, 515), 10)

        # Update the display
        pygame.display.flip()
