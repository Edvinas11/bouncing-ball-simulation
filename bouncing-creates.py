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
midi_output.set_instrument(38)

# Screen dimensions
WIDTH, HEIGHT = 800, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bouncing Balls within a Ball")

# Colors
BLACK = (1, 10, 15)
WHITE = (255, 255, 255)

# Ball properties
big_ball_radius = 243
big_ball_center = (WIDTH // 2, HEIGHT // 2)
gravity = pygame.Vector2(0, 0.25)

# Load MIDI file
midi_file = MidiFile("midi/faded.mid")
midi_iterator = iter(midi_file)

# Font initialization
font = pygame.font.Font(None, 36)

class Particle:
    def __init__(self, position, velocity, color, lifespan):
        self.position = pygame.Vector2(position)
        self.velocity = pygame.Vector2(velocity)
        self.color = color
        self.lifespan = lifespan

    def update(self):
        self.position += self.velocity
        self.lifespan -= 2
        if self.lifespan < 0:
            self.lifespan = 0

    def draw(self, screen):
        if self.lifespan > 0:
            alpha = int(255 * (self.lifespan / 50))
            color = self.color + (alpha,)
            pygame.draw.circle(screen, color, (int(self.position.x), int(self.position.y)), 3)

class MiniBall:
    def __init__(self, color, initial_position, radius, velocity):
        self.position = pygame.Vector2(initial_position)
        self.prevPos = self.position.copy()
        self.radius = radius
        self.velocity = pygame.Vector2(velocity)
        self.color = color
        self.image = pygame.Surface((2 * radius, 2 * radius), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (radius, radius), radius)
        self.mask = pygame.mask.from_surface(self.image)
        self.tail = []

    def move(self):
        self.prevPos = self.position.copy()  # Keep track of previous position
        self.velocity += gravity
        self.position += self.velocity
        self.update_tail()

    def update_tail(self):
        self.tail.append(self.position.copy())
        if len(self.tail) > 5:  # Limit the tail length
            self.tail.pop(0)

    def draw_tail(self, screen):
        tail_length = len(self.tail)
        for i in range(tail_length):
            alpha = int(255 * (i / tail_length))  # Fading effect
            tail_color = (*self.color[:3], alpha)
            tail_surface = pygame.Surface((2 * self.radius, 2 * self.radius), pygame.SRCALPHA)
            pygame.draw.circle(tail_surface, tail_color, (self.radius, self.radius), self.radius)
            screen.blit(tail_surface, (self.tail[i].x - self.radius, self.tail[i].y - self.radius))

    def check_collision(self, mask, rect):
        mini_ball_rect = self.image.get_rect(center=(int(self.position.x), int(self.position.y)))
        offset = (mini_ball_rect.left - rect.left, mini_ball_rect.top - rect.top)
        return mask.overlap(self.mask, offset) is not None

    def play_collision_note(self):
        global midi_iterator
        msg = next(midi_iterator, None)
        while msg and msg.type != "note_on":
            msg = next(midi_iterator, None)

        if msg is None:
            midi_iterator = iter(midi_file)
            msg = next(midi_iterator, None)
            while msg and msg.type != "note_on":
                msg = next(midi_iterator, None)

        if msg:
            velocity = 100  # Volume (0-127)
            pitch = msg.note + 14  # Transpose up one octave
            midi_output.note_on(pitch, velocity)

    def bounce(self, normal):
        self.position = self.prevPos.copy()
        speed = self.velocity.length()
        new_velocity = self.velocity.reflect(normal)
        self.velocity = new_velocity.normalize() * speed
        self.position += self.velocity * 0.1
        self.position += normal * 2

    def draw(self, screen):
        self.draw_tail(screen)
        screen.blit(self.image, (int(self.position.x) - self.radius, int(self.position.y) - self.radius))
        pygame.draw.circle(screen, WHITE, (self.position.x, self.position.y), self.radius, 3)

def drawText(text, font, color, surface, x, y, size=36, alpha=255):
    font = pygame.font.Font(None, size)
    textobj = font.render(text, True, color)
    textobj.set_alpha(alpha)
    textrect = textobj.get_rect()
    textrect.center = (x, y)
    surface.blit(textobj, textrect)

# Create the ball mask with an arc and a customizable gap
def create_ball_mask(radius, color, arc_width=10, start_angle=0.5, end_angle=2 * math.pi):
    inner_radius = radius - arc_width // 2
    outer_radius = radius + arc_width // 2

    mask_image = pygame.Surface((2 * outer_radius, 2 * outer_radius), pygame.SRCALPHA)
    rect = mask_image.get_rect()
    pygame.draw.arc(mask_image, color, rect, start_angle, end_angle, arc_width)

    mask = pygame.mask.from_surface(mask_image)

    return mask, mask_image

# Main loop
clock = pygame.time.Clock()

# Color
color = pygame.Color(66, 219, 68)
h = color.hsla[0]
s = color.hsla[1]
l = color.hsla[2]
colorDir = 1

# Start with one mini ball
mini_balls = [MiniBall((color.r, color.g, color.b), (WIDTH / 2 - 10, HEIGHT / 2 - 90), radius=15, velocity=[-4, -4])]
particles = []

running = False

start_angle = 0.4
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
        # Update angles to create spinning effect (consistent speed)
        start_angle += angle_increment
        end_angle += angle_increment

        mask, mask_image = create_ball_mask(big_ball_radius, (color.r, color.g, color.b), 5, start_angle, end_angle)
        mask_rect = mask_image.get_rect(center=big_ball_center)

        # Changing color effect
        color.hsla = (h, s, l, 100)
        h += 2 * colorDir
        if h >= 360:
            h = 359  # Keep h in bounds
            colorDir = -1
        elif h <= 0:
            h = 1
            colorDir = 1

        # Update mini balls
        for mini_ball in mini_balls:
            mini_ball.move()

            if mini_ball.check_collision(mask, mask_rect):
                normal = (mini_ball.position - pygame.Vector2(big_ball_center)).normalize()
                mini_ball.bounce(normal)
                mini_ball.play_collision_note()

        # Check if any ball is out of bounds and handle spawning
        out_of_bounds_balls = [mini_ball for mini_ball in mini_balls if mini_ball.position.x < 0 or mini_ball.position.x > WIDTH or mini_ball.position.y < 0 or mini_ball.position.y > HEIGHT]
        if out_of_bounds_balls:
            for mini_ball in out_of_bounds_balls:
                mini_balls.remove(mini_ball)
                for _ in range(3):
                    ball_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                    mini_balls.append(MiniBall(ball_color, big_ball_center, radius=15, velocity=[random.uniform(-4, 4), random.uniform(-4, 4)]))

        # Draw everything
        screen.fill(BLACK)

        for mini_ball in mini_balls:
            mini_ball.draw(screen)
        
        screen.blit(mask_image, mask_rect.topleft)

        pygame.display.flip()
