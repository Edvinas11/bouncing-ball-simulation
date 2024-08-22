import pygame
import sys
import math
import random
import pygame.midi
from mido import MidiFile

# Initialize Pygame
pygame.init()
pygame.midi.init()
output_device_id = 0
midi_output = pygame.midi.Output(output_device_id)
midi_output.set_instrument(15)

# Screen dimensions
WIDTH, HEIGHT = 800, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bouncing Balls within a Ball")

# Colors
BLACK = (1, 10, 20)
WHITE = (255, 255, 255)

# Ball properties
big_ball_radius = 250
big_ball_center = (WIDTH // 2, HEIGHT // 2)
gravity = pygame.Vector2(0, 0.25)

# Load MIDI file
midi_file = MidiFile("midi/aloneloop.mid")

# Font initialization
font = pygame.font.Font(None, 36)

class MiniBall:
    def __init__(self, color, initial_position, radius, velocity):
        self.position = pygame.Vector2(initial_position)
        self.prevPos = self.position.copy()
        self.radius = radius
        self.velocity = pygame.Vector2(velocity)
        self.note_iterator = iter(midi_file)  # MIDI note iterator
        self.color = color
        self.image = pygame.Surface((2 * radius, 2 * radius), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (radius, radius), radius)
        self.mask = pygame.mask.from_surface(self.image)

    def move(self):
        self.prevPos = self.position.copy()  # Keep track of previous position
        self.velocity += gravity
        self.position += self.velocity

    def check_collision(self, big_mask, big_ball_rect):
        mini_ball_rect = self.image.get_rect(center=(int(self.position.x), int(self.position.y)))
        offset = (mini_ball_rect.left - big_ball_rect.left, mini_ball_rect.top - big_ball_rect.top)
        if big_mask.overlap(self.mask, offset):
            return True
        return False

    def play_collision_note(self):
        msg = next(self.note_iterator, None)
        while msg and msg.type != "note_on":
            msg = next(self.note_iterator, None)

        if msg is None:
            self.note_iterator = iter(midi_file)
            msg = next(self.note_iterator, None)
            while msg and msg.type != "note_on":
                msg = next(self.note_iterator, None)

        if msg:
            velocity = 100  # Volume (0-127)
            pitch = msg.note + 11  # Transpose up one octave
            midi_output.note_on(pitch, velocity)

    def bounce(self):
        # Use previous position to bounce
        self.position = self.prevPos.copy()

        dir_to_center = self.position - pygame.Vector2(big_ball_center)

        # Calculate new velocity
        speed = self.velocity.length()
        angle_to_collision_point = math.atan2(-dir_to_center.y, dir_to_center.x)
        old_angle = math.atan2(-self.velocity.y, self.velocity.x)
        new_angle = 2 * angle_to_collision_point - old_angle

        # Add randomness to the bounce
        random_angle = random.uniform(-0.1, 0.1)
        new_angle += random_angle

        # Set the new velocity based on the angle
        self.velocity = pygame.Vector2(
            -speed * math.cos(new_angle), speed * math.sin(new_angle)
        )

        # Ensure the ball moves away from the collision point
        self.position += self.velocity * 0.1

    def draw(self, screen):
        screen.blit(self.image, (int(self.position.x) - self.radius, int(self.position.y) - self.radius))

def drawText(text, font, color, surface, x, y, size=36, alpha=255):
    font = pygame.font.Font(None, size)
    textobj = font.render(text, True, color)
    textobj.set_alpha(alpha)
    textrect = textobj.get_rect()
    textrect.center = (x, y)
    surface.blit(textobj, textrect)

# Create the big ball mask with an arc and a customizable gap
def create_big_ball_mask(radius, color, arc_width=10, start_angle=0.5, end_angle=2 * math.pi):
    image = pygame.Surface((2 * radius, 2 * radius), pygame.SRCALPHA)
    rect = image.get_rect()
    pygame.draw.arc(image, color, rect, start_angle, end_angle, arc_width)

    mask = pygame.mask.from_surface(image)

    return mask, image

# Main loop
clock = pygame.time.Clock()

# Color
color = pygame.Color(66, 219, 68)
h = color.hsla[0]
s = color.hsla[1]
l = color.hsla[2]
colorDir = 1

# Start with one mini ball
mini_ball = MiniBall((color.r, color.g, color.b), (WIDTH / 2, HEIGHT / 2), radius=20, velocity=[-4, -4])

running = False

start_angle = 0.5
end_angle = 2 * math.pi
angle_increment = 0.01

while True:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            midi_output.close()
            sys.exit(0)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                running = True

    if running:
        mini_ball.move()

        # Changing color effect
        color.hsla = (h, s, l, 100)
        h += 2 * colorDir
        if h >= 360:
            h = 359  # Keep h in bounds
            colorDir = -1
        elif h <= 0:
            h = 1
            colorDir = 1

        # Update angles to create spinning effect
        start_angle += angle_increment
        end_angle += angle_increment

        big_ball_mask, big_ball_image = create_big_ball_mask(big_ball_radius, (color.r, color.g, color.b), 3, start_angle, end_angle)
        big_ball_rect = big_ball_image.get_rect(center=big_ball_center)

        if mini_ball.check_collision(big_ball_mask, big_ball_rect):
            mini_ball.bounce()
            mini_ball.play_collision_note()

        # Draw everything
        screen.fill(BLACK)
        screen.blit(big_ball_image, big_ball_rect.topleft)
        # pygame.draw.circle(screen, (color.r, color.g, color.b), big_ball_center, big_ball_radius, 6)

        mini_ball.draw(screen)

        # Status text
        # drawText(f"Ball size: {mini_ball.radius}", font, (255, 255, 255), screen, WIDTH / 2, 700, 26, 255)

        pygame.display.flip()
