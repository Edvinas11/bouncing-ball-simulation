import math
import pygame
import pygame.midi
from mido import MidiFile
import time
import random

width = 900  # Screen width
height = 900  # Screen height

main_circle_width = 760  # Diameter of the main circle

pygame.init()

# Pygame MIDI initialization
pygame.midi.init()
output_device_id = 1
midi_output = pygame.midi.Output(output_device_id)

clock = pygame.time.Clock()

screen = pygame.display.set_mode((width, height))
screen.fill((0, 0, 0))

bounce_sound = pygame.mixer.Sound("bubble.wav")

# Font initialization
font = pygame.font.Font(None, 36)

class Ball:
    def __init__(self, initial_position, initial_velocity):
        self.position = pygame.Vector2(initial_position)
        self.color = (66, 219, 68)
        self.gravity = pygame.Vector2(0, 1.5)
        self.velocity = pygame.Vector2(initial_velocity)
        self.prevPos = pygame.Vector2(self.position.x, self.position.y)
        self.radius = 18
        self.counter = 0
        self.collisions = []
        # Collision flag
        self.collided = False

        # Custom fields
        self.age = 903

    def update(self, color):
        self.prevPos = pygame.Vector2(self.position.x, self.position.y)

        self.color = color

        # Movement
        self.velocity += self.gravity
        self.position += self.velocity

        dirToCenter = pygame.Vector2(
            self.position.x - (width / 2), self.position.y - (height / 2)
        )

        if self.isCollide():
            self.collided = True

            # Play MIDI note upon collision
            # self.playCollisionNote()
            bounce_sound.play()

            self.radius += 1.3

            # Calculate collision point on the main circle's edge
            main_circle_center = pygame.Vector2(width / 2, height / 2)
            main_circle_radius = main_circle_width / 2
            collision_vector = pygame.Vector2(self.position) - main_circle_center
            collision_vector.normalize_ip()
            collision_point = main_circle_center + collision_vector * main_circle_radius

            self.collisions.append(collision_point)

            # Handle collision physics
            self.position = pygame.Vector2(self.prevPos.x, self.prevPos.y)
            v = math.sqrt(self.velocity.x * self.velocity.x + self.velocity.y * self.velocity.y)
            angleToCollisionPoint = math.atan2(-dirToCenter.y, dirToCenter.x)
            oldAngle = math.atan2(-self.velocity.y, self.velocity.x)
            newAngle = 2 * angleToCollisionPoint - oldAngle

            # Add randomness to the bounce
            random_angle = random.uniform(-0.1, 0.1)
            newAngle += random_angle

            self.velocity = pygame.Vector2(
                -v * math.cos(newAngle), v * math.sin(newAngle)
            )

            # Speed up
            self.velocity *= 1.002

            self.counter += 1
        else:
            self.collided = False

    def isCollide(self):
        main_circle_radius = main_circle_width / 2
        if self.distance(self.position.x, self.position.y, (width / 2), (height / 2)) > ((main_circle_radius) - self.radius):
            return True
        return False

    def distance(self, x1, y1, x2, y2):
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    def draw(self, screen):
        pygame.draw.circle(
            screen,
            self.color,
            (int(self.position.x), int(self.position.y)),
            self.radius,
        )

        # Draw lines
        for point in self.collisions:
            pygame.draw.line(screen, color, (self.position.x, self.position.y), point)

def drawText(text, font, color, surface, x, y, size=36, alpha=255):
    font = pygame.font.Font(None, size)
    textobj = font.render(text, True, color)
    textobj.set_alpha(alpha)
    textrect = textobj.get_rect()
    textrect.center = (x, y)
    surface.blit(textobj, textrect)

def drawMainCircle(screen, color, coordinates, radius, width):
    # pygame.draw.circle(screen, color, coordinates, radius + 5, width)
    pygame.draw.circle(screen, color, coordinates, radius, width)

# Color
color = pygame.Color(66, 219, 68)
h = color.hsla[0]
s = color.hsla[1]
l = color.hsla[2]
colorDir = 1

# Create the main ball
main_ball = Ball((width / 2, height / 2), (-9, -9))

running = False

while True:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            midi_output.close()
            exit(0)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                running = True

    if running:
        main_ball.update((color.r, color.g, color.b))

        screen.fill((0, 0, 0))  # Clear the screen

        # The name text of acc
        drawText("@bounce.ballz", font, (255, 255, 255), screen,width / 2, height / 2, 25, 50)

        # Changing color effect
        color.hsla = (h, s, l, 100)
        h += 1 * colorDir
        if h >= 360:
            h = 359  # Keep h in bounds
            colorDir = -1
        elif h <= 0:
            h = 1
            colorDir = 1

        main_ball.draw(screen)

        # Draw the main circle
        main_circle_radius = int(main_circle_width / 2)
        drawMainCircle(screen, (color.r, color.g, color.b), (width / 2, height / 2), main_circle_radius, 10)

        # Status text
        drawText(f"Age: {round(main_ball.age, 0)}", font, (255, 255, 255), screen, width / 2, 860, 26, 1000)

        pygame.display.flip()
