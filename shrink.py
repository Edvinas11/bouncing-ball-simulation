import pygame
import sys
import math
import random
import pygame.midi
from mido import MidiFile
import time

# Initialize Pygame
pygame.init()
pygame.midi.init()
output_device_id = 0
midi_output = pygame.midi.Output(output_device_id)
midi_output.set_instrument(38)

# Screen dimensions
WIDTH, HEIGHT = 800, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bouncing Balls within Circles")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Circle properties
initial_big_ball_radius = 290
big_ball_center = (WIDTH // 2, HEIGHT // 2)
shrink_rate = 1.1
arc_width = 10

gravity = pygame.Vector2(0, 0.25)

# Load MIDI file
midi_file = MidiFile("midi/faded.mid")

bounce_sound = pygame.mixer.Sound("sounds/BABABOI.mp3")

# Font initialization
font = pygame.font.Font(None, 36)

class MiniBall:
    def __init__(self, color, initial_position, radius, velocity):
        self.position = pygame.Vector2(initial_position)
        self.prevPos = self.position.copy()
        self.radius = radius
        self.velocity = pygame.Vector2(velocity)
        self.note_iterator = iter(midi_file)  # MIDI note iterator
        self.hue = 0  # Start hue at 0
        self.saturation = 1  # Full saturation
        self.value = 1  # Full value
        self.image = pygame.Surface((2 * radius, 2 * radius), pygame.SRCALPHA)
        self.mask = pygame.mask.from_surface(self.image)
        pygame.draw.circle(self.image, color, (self.radius, self.radius), self.radius)
        self.mask = pygame.mask.from_surface(self.image)
    #     self.update_color()

    # def update_color(self):
    #     color = pygame.Color(0)
    #     color.hsva = (self.hue, self.saturation * 100, self.value * 100, 100)
    #     self.image.fill((0, 0, 0, 0))
    #     pygame.draw.circle(self.image, color, (self.radius, self.radius), self.radius)
    #     self.mask = pygame.mask.from_surface(self.image)

    def move(self):
        self.prevPos = self.position.copy()  # Keep track of previous position
        self.velocity += gravity
        self.position += self.velocity

        # Update hue for the color effect
        # self.hue = (self.hue + 2) % 360  # Increment hue and wrap around at 360
        # self.update_color()

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
            pitch = msg.note + 14  # Transpose up one octave
            midi_output.note_on(pitch, velocity)

    def bounce(self):
        # Calculate the collision point
        dir_to_center = self.position - pygame.Vector2(big_ball_center)
        dir_to_center = dir_to_center.normalize() * initial_big_ball_radius

        # Use previous position to bounce
        self.position = self.prevPos.copy()

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

class BigCircle:
    def __init__(self, radius, color, shrink_rate, arc_width):
        self.radius = radius
        self.color = color
        self.shrink_rate = shrink_rate
        self.arc_width = arc_width
        self.mask, self.image = self.create_mask_and_image()

    def create_mask_and_image(self):
        image = pygame.Surface((2 * self.radius, 2 * self.radius), pygame.SRCALPHA)
        rect = image.get_rect()
        pygame.draw.arc(image, self.color, rect, 0, 2 * math.pi, self.arc_width)
        mask = pygame.mask.from_surface(image)
        return mask, image

    def shrink(self):
        self.radius -= self.shrink_rate
        self.mask, self.image = self.create_mask_and_image()

    def draw(self, screen, center):
        screen.blit(self.image, (center[0] - self.radius, center[1] - self.radius))

def drawText(text, font, color, surface, x, y, size=36, alpha=255):
    font = pygame.font.Font(None, size)
    textobj = font.render(text, True, color)
    textobj.set_alpha(alpha)
    textrect = textobj.get_rect()
    textrect.center = (x, y)
    surface.blit(textobj, textrect)

# Main loop
clock = pygame.time.Clock()

# Color
color = pygame.Color(66, 219, 68)
h = color.hsla[0]
s = color.hsla[1]
l = color.hsla[2]
colorDir = 1

# Start with one mini ball
mini_ball = MiniBall((0, 0, 0), (WIDTH / 2, HEIGHT / 2), radius=20, velocity=[-4, -4])

# Initialize circles
circles = [
    BigCircle(initial_big_ball_radius, (color.r, color.g, color.b), shrink_rate, arc_width),
]

running = False

timer = 0

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
                start_time = time.time()

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

        current_time = time.time()
        if current_time - start_time >= 0.7:
            circle_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            new_circle = BigCircle(initial_big_ball_radius, circle_color, shrink_rate, arc_width)
            circles.append(new_circle)
            start_time = current_time

        circles = [circle for circle in circles if circle.radius > 0]

        big_ball_mask = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        big_ball_rect = big_ball_mask.get_rect(center=big_ball_center)
        big_ball_mask.fill((0, 0, 0, 0))

        for circle in circles:
            circle.shrink()
            pygame.draw.arc(big_ball_mask, (255, 255, 255, 255), (big_ball_center[0] - circle.radius, big_ball_center[1] - circle.radius, 2 * circle.radius, 2 * circle.radius), 0, 2 * math.pi, arc_width)

        big_ball_mask = pygame.mask.from_surface(big_ball_mask)

        if mini_ball.check_collision(big_ball_mask, big_ball_rect):
            mini_ball.bounce()
            bounce_sound.play()
            # mini_ball.play_collision_note()
            circles.pop(0)

        # Draw everything
        screen.fill(BLACK)

        for circle in circles:
            circle.draw(screen, big_ball_center)

        mini_ball.draw(screen)

        pygame.draw.circle(screen, WHITE, mini_ball.position, mini_ball.radius, 5)

        pygame.display.flip()
