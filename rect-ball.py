import pygame
import sys
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
pygame.display.set_caption("Bouncing Ball within a Rectangle")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Rectangle properties
rect_width = 605
rect_height = 620
rect_x = (WIDTH - rect_width) // 2
rect_y = (HEIGHT - rect_height) // 2
rect_border_width = 10

# Load MIDI file
midi_file = MidiFile("midi/tokyo.mid")

# Font initialization
font = pygame.font.Font(None, 36)

class MiniBall:
    def __init__(self, color, initial_position, radius, velocity):
        self.position = pygame.Vector2(initial_position)
        self.radius = radius
        self.velocity = pygame.Vector2(velocity)
        self.note_iterator = iter(midi_file)  # MIDI note iterator
        self.color = color
        self.image = pygame.Surface((2 * radius, 2 * radius), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (radius, radius), radius)
        self.mask = pygame.mask.from_surface(self.image)
        self.collision_points = []  # List to store collision points
        self.tail = []

    def move(self, color):
        self.position += self.velocity
        collision_point = None
        self.update_tail()
        self.color = color

        # Check for collision with the rectangle boundaries
        if self.position.x - self.radius <= rect_x + rect_border_width:
            self.velocity.x *= -1
            self.play_collision_note()
            collision_point = pygame.Vector2(rect_x + rect_border_width, self.position.y)
            self.position.x = rect_x + rect_border_width + self.radius  # Adjust position to prevent sticking
        elif self.position.x + self.radius >= rect_x + rect_width - rect_border_width:
            self.velocity.x *= -1
            self.play_collision_note()
            collision_point = pygame.Vector2(rect_x + rect_width - rect_border_width, self.position.y)
            self.position.x = rect_x + rect_width - rect_border_width - self.radius  # Adjust position to prevent sticking

        if self.position.y - self.radius <= rect_y + rect_border_width:
            self.velocity.y *= -1
            self.play_collision_note()
            collision_point = pygame.Vector2(self.position.x, rect_y + rect_border_width)
            self.position.y = rect_y + rect_border_width + self.radius  # Adjust position to prevent sticking
        elif self.position.y + self.radius >= rect_y + rect_height - rect_border_width:
            self.velocity.y *= -1
            self.play_collision_note()
            collision_point = pygame.Vector2(self.position.x, rect_y + rect_height - rect_border_width)
            self.position.y = rect_y + rect_height - rect_border_width - self.radius  # Adjust position to prevent sticking

        if collision_point:
            self.collision_points.append(collision_point)
            self.radius += 2  # Increase the radius of the ball

        self.image = pygame.Surface((2 * self.radius, 2 * self.radius), pygame.SRCALPHA)
        pygame.draw.circle(self.image, self.color, (self.radius, self.radius), self.radius)
        self.mask = pygame.mask.from_surface(self.image)

    def update_tail(self):
        self.tail.append(self.position.copy())
        if len(self.tail) > 10:  # Limit the tail length
            self.tail.pop(0)

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
            pitch = msg.note + 10  # Transpose up one octave
            midi_output.note_on(pitch, velocity)

    def draw_tail(self, screen):
        tail_length = len(self.tail)
        for i in range(tail_length):
            alpha = int(255 * (i / tail_length))  # Fading effect
            tail_color = (*self.color[:3], alpha)
            tail_surface = pygame.Surface((2 * self.radius, 2 * self.radius), pygame.SRCALPHA)
            pygame.draw.circle(tail_surface, tail_color, (self.radius, self.radius), self.radius)
            screen.blit(tail_surface, (self.tail[i].x - self.radius, self.tail[i].y - self.radius))

    def draw(self, screen, color):
        for point in self.collision_points:
            pygame.draw.line(screen, color, (self.position.x, self.position.y), point, 2)

        self.draw_tail(screen)

        screen.blit(self.image, (int(self.position.x) - self.radius, int(self.position.y) - self.radius))

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
mini_ball = MiniBall((color.r, color.g, color.b), (WIDTH / 2 + 0, HEIGHT / 2 - 200), radius=10, velocity=[-6, -6])

running = False

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
        mini_ball.move((color.r, color.g, color.b))

        # Changing color effect
        color.hsla = (h, s, l, 100)
        h += 2 * colorDir
        if h >= 360:
            h = 359  # Keep h in bounds
            colorDir = -1
        elif h <= 0:
            h = 1
            colorDir = 1

        # Draw everything
        screen.fill(BLACK)
        pygame.draw.rect(screen, (255, 255, 255), (rect_x, rect_y, rect_width, rect_height), rect_border_width)

        mini_ball.draw(screen, (color.r, color.g, color.b))
        pygame.draw.circle(screen, BLACK, mini_ball.position, mini_ball.radius)
        pygame.draw.circle(screen, WHITE, mini_ball.position, mini_ball.radius, 5)

        pygame.display.flip()
