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
midi_output.set_instrument(15)

# Screen dimensions
WIDTH, HEIGHT = 800, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bouncing Rectangle within a Rectangle")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Rectangle properties
rect_width = 605
rect_height = 625
rect_x = (WIDTH - rect_width) // 2
rect_y = (HEIGHT - rect_height) // 2
rect_border_width = 10

# Load MIDI file
midi_file = MidiFile("midi/tokyo.mid")

sound = pygame.mixer.Sound("sounds/BABABOI.mp3")

# Font initialization
font = pygame.font.Font(None, 36)

class MiniRect:
    def __init__(self, color, initial_position, size, velocity):
        self.position = pygame.Vector2(initial_position)
        self.size = size
        self.velocity = pygame.Vector2(velocity)
        self.note_iterator = iter(midi_file)  # MIDI note iterator
        self.color = color
        self.image = pygame.Surface((size[0], size[1]), pygame.SRCALPHA)
        pygame.draw.rect(self.image, color, (0, 0, size[0], size[1]))
        self.mask = pygame.mask.from_surface(self.image)
        self.collision_points = []  # List to store collision points
        self.tail = []

    def move(self, color):
        self.position += self.velocity
        collision_point = None
        self.update_tail()
        self.color = color

        # Check for collision with the rectangle boundaries
        if self.position.x <= rect_x + rect_border_width:
            self.velocity.x *= -1
            # self.play_collision_note()
            sound.play()
            collision_point = pygame.Vector2(rect_x + rect_border_width, self.position.y)
            self.position.x = rect_x + rect_border_width  # Adjust position to prevent sticking
        elif self.position.x + self.size[0] >= rect_x + rect_width - rect_border_width:
            self.velocity.x *= -1
            # self.play_collision_note()
            sound.play()
            collision_point = pygame.Vector2(rect_x + rect_width - rect_border_width, self.position.y)
            self.position.x = rect_x + rect_width - rect_border_width - self.size[0]  # Adjust position to prevent sticking

        if self.position.y <= rect_y + rect_border_width:
            self.velocity.y *= -1
            # self.play_collision_note()
            sound.play()
            collision_point = pygame.Vector2(self.position.x, rect_y + rect_border_width)
            self.position.y = rect_y + rect_border_width  # Adjust position to prevent sticking
        elif self.position.y + self.size[1] >= rect_y + rect_height - rect_border_width:
            self.velocity.y *= -1
            # self.play_collision_note()
            sound.play()
            collision_point = pygame.Vector2(self.position.x, rect_y + rect_height - rect_border_width)
            self.position.y = rect_y + rect_height - rect_border_width - self.size[1]  # Adjust position to prevent sticking

        if collision_point:
            self.collision_points.append(collision_point)
            # self.size = (self.size[0] + 2, self.size[1] + 2)  # Increase the size of the rectangle
            self.velocity *= 1.02

        self.image = pygame.Surface((self.size[0], self.size[1]), pygame.SRCALPHA)
        pygame.draw.rect(self.image, self.color, (0, 0, self.size[0], self.size[1]))
        self.mask = pygame.mask.from_surface(self.image)

    def update_tail(self):
        self.tail.append(self.position.copy())
        if len(self.tail) > 20:  # Limit the tail length
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
            pitch = msg.note + 30  # Transpose up one octave
            midi_output.note_on(pitch, velocity)

    def draw_tail(self, screen):
        tail_length = len(self.tail)
        for i in range(tail_length):
            alpha = int(255 * (i / tail_length))  # Fading effect
            tail_color = (*self.color[:3], alpha)
            tail_surface = pygame.Surface((self.size[0], self.size[1]), pygame.SRCALPHA)
            pygame.draw.rect(tail_surface, tail_color, (0, 0, self.size[0], self.size[1]))
            screen.blit(tail_surface, (self.tail[i].x, self.tail[i].y))

    def draw(self, screen, color):
        for point in self.collision_points:
            pygame.draw.line(screen, color, (self.position.x, self.position.y), point, 1)

        self.draw_tail(screen)

        screen.blit(self.image, (int(self.position.x), int(self.position.y)))

        pygame.draw.rect(screen, (0, 0, 0), (self.position.x, self.position.y, self.size[0] - 1, self.size[1] - 1))

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

# Start with one mini rectangle
mini_rect = MiniRect((color.r, color.g, color.b), (WIDTH / 2 + 40, HEIGHT / 2 + 20), size=(20, 20), velocity=[-6, -6])

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
        mini_rect.move((color.r, color.g, color.b))

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
    
        mini_rect.draw(screen, (color.r, color.g, color.b))

        pygame.draw.rect(screen, (color.r, color.g, color.b), (rect_x, rect_y, rect_width, rect_height), rect_border_width)

        pygame.display.flip()
