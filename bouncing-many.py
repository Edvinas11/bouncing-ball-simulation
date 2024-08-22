import math
import pygame
import pygame.midi
from mido import MidiFile
import time
import random

width = 800  # Screen width
height = 800  # Screen height

main_circle_width = 760  # Initial diameter of the main circle
main_circle_shrink_rate = 5.3  # Rate at which the circle shrinks per second

screen_color = (255, 255, 255)

pygame.init()

# Pygame MIDI initialization
pygame.midi.init()
midi_output = pygame.midi.Output(pygame.midi.get_default_output_id())

midi_output.set_instrument(38)

clock = pygame.time.Clock()

screen = pygame.display.set_mode((width, height))
screen.fill(screen_color)

# MIDI file
midi_file = MidiFile("midi/kerosene12.mid")

# Font initialization
font = pygame.font.Font(None, 36)

eat_sound = pygame.mixer.Sound("sounds/yeppe.mp3")

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

class VoidBall:
    def __init__(self, radius):
        self.radius = radius
        self.color = (0, 0, 0)
        self.position = (width / 2, height / 2)

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, self.position, self.radius)

    def eats(self, ball):
        return math.hypot(ball.position.x - self.position[0], ball.position.y - self.position[1]) <= self.radius + ball.radius

    def grow(self, amount):
        self.radius += amount

class Ball:
    def __init__(self, initial_position, initial_velocity, color, radius):
        self.position = pygame.Vector2(initial_position)
        self.color = pygame.Color(*color)
        self.gravity = pygame.Vector2(0, 0.12)
        self.velocity = pygame.Vector2(initial_velocity)
        self.prevPos = pygame.Vector2(self.position.x, self.position.y)
        self.radius = radius
        self.counter = 0
        self.collisions = []
        self.previous_positions = []
        self.max_tail_length = 5
        self.fade_rate = 20
        self.note_iterator = iter(midi_file)
        self.collided = False
        self.age = 147.7

    def update(self, main_circle_radius, particles):
        self.prevPos = pygame.Vector2(self.position.x, self.position.y)

        # Movement
        self.velocity += self.gravity
        self.position += self.velocity

        # Add the current position with a full alpha value to the previous positions list
        self.previous_positions.append((self.prevPos, 255))
        if len(self.previous_positions) > self.max_tail_length:
            self.previous_positions.pop(0)
        self.previous_positions = [(pos, max(alpha - self.fade_rate, 0)) for pos, alpha in self.previous_positions]

        dirToCenter = pygame.Vector2(
            self.position.x - (width / 2), self.position.y - (height / 2)
        )

        if self.isCollide(main_circle_radius):
            self.collided = True

            # Play MIDI note upon collision
            self.playCollisionNote()

            # Calculate collision point on the main circle's edge
            main_circle_center = pygame.Vector2(width / 2, height / 2)
            collision_vector = pygame.Vector2(self.position) - main_circle_center
            collision_vector.normalize_ip()
            collision_point = main_circle_center + collision_vector * main_circle_radius

            self.collisions.append((collision_point, self.color))

            # Create particles at the collision point
            self.createParticles(collision_point, particles)

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
            self.velocity *= 1.05

            self.counter += 1
        else:
            self.collided = False

    def createParticles(self, collision_point, particles):
        num_particles = 20
        for _ in range(num_particles):
            velocity = pygame.Vector2(random.uniform(-3, 3), random.uniform(-3, 3))
            color = (random.randint(200, 255), random.randint(100, 255), random.randint(100, 255))
            lifespan = random.randint(30, 50)
            particles.append(Particle(collision_point, velocity, color, lifespan))

    def playCollisionNote(self):
        msg = next(self.note_iterator, None)
        while msg and msg.type != "note_on":
            msg = next(self.note_iterator, None)

        if msg is None:
            self.note_iterator = iter(midi_file)
            msg = next(self.note_iterator, None)
            while msg and msg.type != "note_on":
                msg = next(self.note_iterator, None)

        if msg:
            midi_output.note_on(msg.note + 10, 50)

    def isCollide(self, main_circle_radius):
        return self.distance(self.position.x, self.position.y, width / 2, height / 2) > main_circle_radius - self.radius + 2

    def distance(self, x1, y1, x2, y2):
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    def draw(self, screen):
        pygame.draw.circle(
            screen,
            self.color,
            (int(self.position.x), int(self.position.y)),
            self.radius,
        )

def drawMainCircle(screen, color, coordinates, radius, width):
    pygame.draw.circle(screen, color, coordinates, radius, width)

# Color
color = pygame.Color(66, 219, 68)
h = color.hsla[0]
s = color.hsla[1]
l = color.hsla[2]
colorDir = 1

# Create the main ball
main_ball = Ball((width / 2 + 200, height / 2 + 210), (-6, -6), (color.r, color.g, color.b), 25)
balls = [main_ball]

# Create the void
void = VoidBall(40)

particles = []

running = False

counter_spawn = 3

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
                # Track the initial time
                start_time = time.time()
                last_spawn_time = start_time  # Track the time when the last ball was spawned  
                initial_spawn = True  # Indicate the initial spawn has happened

    if running:     
        main_circle_radius = int(main_circle_width / 2)

        # Changing color effect
        color.hsla = (h, s, l, 100)
        h += 1 * colorDir
        if h >= 360:
            h = 359  # Keep h in bounds
            colorDir = -1
        elif h <= 0:
            h = 1
            colorDir = 1

        # Apply the same hue to all balls
        for ball in balls:
            ball.color.hsla = (h, ball.color.hsla[1], ball.color.hsla[2], 100)

        for ball in balls[:]:  # Iterate over a copy of the list to modify it during iteration
            ball.update(main_circle_radius, particles)
            if void.eats(ball):
                void.grow(1.5)
                balls.remove(ball)
                eat_sound.play()

        screen.fill(screen_color)  # Clear the screen

        for ball in balls:
            ball.draw(screen)

        for particle in particles:
            particle.update()
            particle.draw(screen)

        particles = [particle for particle in particles if particle.lifespan > 0]

        # Draw the main circle
        drawMainCircle(screen, (0, 0, 0), (width / 2, height / 2), main_circle_radius, 15)

        # Draw void
        void.draw(screen)

        # Spawn the second ball 5 seconds after the game starts
        current_time = time.time()

        # Spawn subsequent balls every 5 seconds
        if current_time - last_spawn_time >= 5:
            for i in range(counter_spawn):
                new_ball_color = (color.r, color.g, color.b)
                new_ball_velocity = (random.randint(-6, 6), random.randint(-6, 6))
                new_ball = Ball((width / 2 + 170, height / 2 + 180), new_ball_velocity, new_ball_color, 25)
                balls.append(new_ball)
            last_spawn_time = current_time
            counter_spawn += 3

        pygame.display.flip()
