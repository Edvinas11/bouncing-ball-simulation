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
pygame.display.set_caption("Bouncing Rectangle within a Container")

# Colors
BLACK = (1, 10, 15)
WHITE = (255, 255, 255)

# Container properties
container_width = 600
container_height = 610
container_x = (WIDTH - container_width) // 2
container_y = (HEIGHT - container_height) // 2
container_border_width = 10

# Load MIDI file
midi_file = MidiFile("midi/tokyo.mid")

# Font initialization
font = pygame.font.Font(None, 36)

class MovingRectangle:
    def __init__(self, color, initial_position, size, velocity):
        self.position = pygame.Vector2(initial_position)
        self.size = size
        self.velocity = pygame.Vector2(velocity)
        self.note_iterator = iter(midi_file)  # MIDI note iterator
        self.color = color
        self.image = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.rect(self.image, color, self.image.get_rect())
        self.mask = pygame.mask.from_surface(self.image)
        self.collision_points = []  # List to store collision points
        self.tail = []
        self.age = 957
        self.active = True  # Flag to check if the rectangle is active

    def move(self, color):
        if not self.active:
            return

        self.position += self.velocity
        collision_point = None
        # self.update_tail()
        self.color = color

        # Check for collision with the container boundaries
        if self.position.x <= container_x + container_border_width:
            self.velocity.x *= -1
            self.play_collision_note()
            collision_point = pygame.Vector2(container_x + container_border_width, self.position.y)
            self.position.x = container_x + container_border_width  # Adjust position to prevent sticking
        elif self.position.x + self.size[0] >= container_x + container_width - container_border_width:
            self.velocity.x *= -1
            self.play_collision_note()
            collision_point = pygame.Vector2(container_x + container_width - container_border_width, self.position.y)
            self.position.x = container_x + container_width - container_border_width - self.size[0]  # Adjust position to prevent sticking

        if self.position.y <= container_y + container_border_width:
            self.velocity.y *= -1
            self.play_collision_note()
            collision_point = pygame.Vector2(self.position.x, container_y + container_border_width)
            self.position.y = container_y + container_border_width  # Adjust position to prevent sticking
        elif self.position.y + self.size[1] >= container_y + container_height - container_border_width:
            self.velocity.y *= -1
            self.play_collision_note()
            collision_point = pygame.Vector2(self.position.x, container_y + container_height - container_border_width)
            self.position.y = container_y + container_height - container_border_width - self.size[1]  # Adjust position to prevent sticking

        if collision_point:
            self.collision_points.append(collision_point)

            if self.age > 0 and self.size[0] > 0 and self.size[1] > 0:
                self.size = (self.size[0] - 3, self.size[1] - 3)  # Decrease the size of the rectangle

                if self.size[0] <= 0 or self.size[1] <= 0:
                    self.size = (0, 0)
                    self.active = False  # Deactivate the rectangle

                self.image = pygame.Surface(self.size, pygame.SRCALPHA)
                pygame.draw.rect(self.image, self.color, self.image.get_rect())
                self.mask = pygame.mask.from_surface(self.image)
            else:
                self.size = (0, 0)
                self.active = False  # Deactivate the rectangle

            if self.age > 100:
                self.age -= 9
            elif self.age > 50:
                self.age -= 4
            elif self.age > 30:
                self.age -= 3
            elif self.age > 10:
                self.age -= 2
            elif self.age > 0:
                self.age -= 1
            else:
                self.age = 0

        self.image = pygame.Surface(self.size, pygame.SRCALPHA)
        pygame.draw.rect(self.image, self.color, self.image.get_rect())
        self.mask = pygame.mask.from_surface(self.image)

    def update_tail(self):
        self.tail.append(self.position.copy())
        if len(self.tail) > 15:  # Limit the tail length
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
            pitch = msg.note + 17  # Transpose up one octave
            midi_output.note_on(pitch, velocity)

    def draw_tail(self, screen):
        tail_length = len(self.tail)
        for i in range(tail_length):
            alpha = int(255 * (i / tail_length))  # Fading effect
            tail_color = (*self.color[:3], alpha)
            tail_surface = pygame.Surface(self.size, pygame.SRCALPHA)
            pygame.draw.rect(tail_surface, tail_color, tail_surface.get_rect())
            screen.blit(tail_surface, (self.tail[i].x, self.tail[i].y))

    def draw(self, screen, color):
        if not self.active:
            return

        screen.blit(self.image, (int(self.position.x), int(self.position.y)))
        # pygame.draw.rect(screen, WHITE, (int(self.position.x), int(self.position.y), self.size[0], self.size[1]), 3)

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

# Start with one moving rectangle
moving_rect = MovingRectangle((255, 255, 255), (WIDTH / 2 + 40, HEIGHT / 2 + 20), size=(400, 400), velocity=[-7, -7])

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
        moving_rect.move((255, 255, 255))

        # Changing color effect
        color.hsla = (h, s, l, 100)
        h += 1 * colorDir
        if h >= 360:
            h = 359  # Keep h in bounds
            colorDir = -1
        elif h <= 0:
            h = 1
            colorDir = 1

        # Draw everything
        screen.fill(BLACK)
        pygame.draw.rect(screen, (color.r, color.g, color.b), (container_x, container_y, container_width, container_height), container_border_width)

        moving_rect.draw(screen, (color.r, color.g, color.b))

        # Status text
        drawText(f"Age: {moving_rect.age}", font, (255, 255, 255), screen, WIDTH / 2, 50, 35, 1000)

        pygame.display.flip()
