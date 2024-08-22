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
pygame.display.set_caption("Bouncing Triangles within a Ball")

# Colors
BLACK = (1, 10, 15)
WHITE = (255, 255, 255)

# Ball properties
big_ball_radius = 252
big_ball_center = (WIDTH // 2, HEIGHT // 2)
gravity = pygame.Vector2(0, 0.25)

# Load MIDI file
midi_file = MidiFile("midi/imbluee.mid")
midi_iterator = iter(midi_file)

# Font initialization
font = pygame.font.Font(None, 36)

explode_sound = pygame.mixer.Sound("sounds/bum.wav")

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

class MiniTriangle:
    def __init__(self, color, initial_position, side_length, velocity):
        self.position = pygame.Vector2(initial_position)
        self.prevPos = self.position.copy()
        self.side_length = side_length
        self.velocity = pygame.Vector2(velocity)
        self.color = pygame.Color(*color)
        self.hue = self.color.hsla[0]
        self.saturation = self.color.hsla[1]
        self.lightness = self.color.hsla[2]
        self.image = pygame.Surface((2 * side_length, 2 * side_length), pygame.SRCALPHA)
        self.update_image()
        self.mask = pygame.mask.from_surface(self.image)
        self.is_moving = True
        self.tail = []
        self.elapsed_time = 0

    def update_image(self):
        self.image.fill((0, 0, 0, 0))  # Clear the surface
        pygame.draw.polygon(self.image, self.color, [(self.side_length, 0), (0, 2 * self.side_length), (2 * self.side_length, 2 * self.side_length)])

    def move(self, dt):
        self.prevPos = self.position.copy()  # Keep track of previous position
        self.velocity += gravity
        self.position += self.velocity
        self.update_tail()
        self.elapsed_time += dt

    def update_tail(self):
        self.tail.append(self.position.copy())
        if len(self.tail) > 10:  # Limit the tail length
            self.tail.pop(0)

    def check_collision(self, big_mask, big_ball_rect):
        triangle_rect = self.image.get_rect(center=(int(self.position.x), int(self.position.y)))
        offset = (triangle_rect.left - big_ball_rect.left, triangle_rect.top - big_ball_rect.top)
        if big_mask.overlap(self.mask, offset):
            return True
        return False

    def check_collision_with_stationary(self, stationary_triangles):
        for triangle in stationary_triangles:
            distance = self.position.distance_to(triangle.position)
            if distance <= self.side_length + triangle.side_length:
                return True, triangle
        return False, None

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
            pitch = msg.note + 24  # Transpose up one octave
            midi_output.note_on(pitch, velocity)

    def bounce(self, particles, normal):
        # Calculate the collision point
        dir_to_center = self.position - pygame.Vector2(big_ball_center)
        dir_to_center = dir_to_center.normalize() * big_ball_radius
        collision_point = pygame.Vector2(big_ball_center) + dir_to_center

        self.position = self.prevPos.copy()
        speed = self.velocity.length()
        new_velocity = self.velocity.reflect(normal)
        self.velocity = new_velocity.normalize() * speed
        self.position += self.velocity * 0.1
        self.position += normal * 1

        # Create particles at the collision point
        self.createParticles(collision_point, particles)

    def resolve_collision_with_stationary(self, stationary_triangle):
        direction = self.position - stationary_triangle.position
        distance = direction.length()
        if distance == 0:
            distance = 0.1  # Prevent division by zero
        overlap = self.side_length + stationary_triangle.side_length - distance
        correction = direction.normalize() * overlap

        # Move the triangle out of collision
        self.position += correction

        # Reflect the velocity
        self.velocity = self.velocity.reflect(direction.normalize())

    def draw_tail(self, screen):
        tail_length = len(self.tail)
        for i in range(tail_length):
            alpha = int(200 * (i / tail_length))  # Fading effect
            tail_color = (*self.color[:3], alpha)
            tail_surface = pygame.Surface((2 * self.side_length, 2 * self.side_length), pygame.SRCALPHA)
            pygame.draw.polygon(tail_surface, tail_color, [(self.side_length, 0), (0, 2 * self.side_length), (2 * self.side_length, 2 * self.side_length)])
            screen.blit(tail_surface, (self.tail[i].x - self.side_length, self.tail[i].y - self.side_length))

    def createParticles(self, collision_point, particles):
        num_particles = 10
        for _ in range(num_particles):
            velocity = pygame.Vector2(random.uniform(-3, 3), random.uniform(-3, 3))
            color = (random.randint(200, 255), random.randint(100, 255), random.randint(100, 255))
            lifespan = random.randint(30, 50)
            particles.append(Particle(collision_point, velocity, color, lifespan))

    def createExplosion(self, particles):
        num_particles = 50  # Number of particles in the explosion
        for _ in range(num_particles):
            velocity = pygame.Vector2(random.uniform(-5, 5), random.uniform(-5, 5))
            color = (random.randint(200, 255), random.randint(100, 255), random.randint(100, 255))
            lifespan = random.randint(30, 50)
            particles.append(Particle(self.position, velocity, color, lifespan))

    def update_color(self, h):
        self.color.hsla = (h, self.saturation, self.lightness, 100)
        self.update_image()

    def draw(self, screen, timer=0, isStationary=False):
        self.draw_tail(screen)
        screen.blit(self.image, (int(self.position.x) - self.side_length, int(self.position.y) - self.side_length))
        remaining_time = 7 - self.elapsed_time
        if remaining_time > 4:
            drawText(str(int(remaining_time)), font, WHITE, screen, int(self.position.x), int(self.position.y - 40), 45)
        else:
            drawText(str(int(remaining_time)), font, (255, 0, 0), screen, int(self.position.x), int(self.position.y - 40), 45)
        pygame.draw.polygon(screen, WHITE, [(self.position.x, self.position.y - self.side_length), (self.position.x - self.side_length, self.position.y + self.side_length), (self.position.x + self.side_length, self.position.y + self.side_length)], 4)

def drawText(text, font, color, surface, x, y, size=36, alpha=255):
    textobj = font.render(text, True, color)
    textobj.set_alpha(alpha)
    textrect = textobj.get_rect()
    textrect.center = (x, y)
    surface.blit(textobj, textrect)

# Create the big ball mask with an arc and a customizable gap
def create_big_ball_mask(radius, hue, arc_width=10, start_angle=0.5, end_angle=2 * math.pi):
    color = pygame.Color(0)
    color.hsla = (hue, 100, 50, 100)
    image = pygame.Surface((2 * radius, 2 * radius), pygame.SRCALPHA)
    rect = image.get_rect()
    pygame.draw.arc(image, color, rect, start_angle, end_angle, arc_width)
    mask = pygame.mask.from_surface(image)
    return mask, image

def random_point_in_circle(radius, center):
    angle = random.uniform(0, 2 * math.pi)
    r = radius * math.sqrt(random.uniform(0, 1))
    x = center[0] + r * math.cos(angle)
    y = center[1] + r * math.sin(angle)
    return x, y

# Main loop
clock = pygame.time.Clock()

# Color
color = pygame.Color(66, 219, 68)
h = color.hsla[0]
s = color.hsla[1]
l = color.hsla[2]
colorDir = 1

# Start with one mini triangle
mini_triangles = [MiniTriangle((color.r, color.g, color.b), (WIDTH / 2 -10, HEIGHT / 2 - 90), side_length=20, velocity=[-4, -4])]
stationary_triangles = []
particles = []

running = False

start_angle = 0.4 + 1
end_angle = 2 * math.pi + 1
angle_increment = 0.02

hue1 = 200
hue_increment = 1

while True:
    dt = clock.tick(60) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            midi_output.close()
            sys.exit(0)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                running = True

    if running:
        hue1 = (hue1 + hue_increment) % 360

        # Update angles to create spinning effect
        start_angle += angle_increment
        end_angle += angle_increment

        # Changing color effect
        color.hsla = (h, s, l, 100)
        h += 2 * colorDir
        if h >= 360:
            h = 359  # Keep h in bounds
            colorDir = -1
        elif h <= 0:
            h = 1
            colorDir = 1

        for mini_triangle in mini_triangles:
            mini_triangle.update_color(h)
            mini_triangle.move(dt)   

            big_ball_mask, big_ball_image = create_big_ball_mask(big_ball_radius, hue1, 10, start_angle, end_angle)
            big_ball_rect = big_ball_image.get_rect(center=big_ball_center)

            if mini_triangle.check_collision(big_ball_mask, big_ball_rect):
                normal = (mini_triangle.position - pygame.Vector2(big_ball_center)).normalize()
                mini_triangle.bounce(particles, normal)
                mini_triangle.play_collision_note()

            # Check if the triangle is out of bounds
            if mini_triangle.position.x < 0 or mini_triangle.position.x > WIDTH or mini_triangle.position.y < 0 or mini_triangle.position.y > HEIGHT:
                mini_triangles.remove(mini_triangle)
                break
                
            if mini_triangle.elapsed_time >= 6:
                mini_triangle.createExplosion(particles)  # Create explosion particles
                explode_sound.play()
                mini_triangles.remove(mini_triangle)  # Remove the ball from the list
                break

            # Update and draw particles
            for particle in particles:
                particle.update()
            particles = [particle for particle in particles if particle.lifespan > 0]

            # Draw everything
            screen.fill(BLACK)
            screen.blit(big_ball_image, big_ball_rect.topleft)

            for mini_triangle in mini_triangles:
                mini_triangle.draw(screen)

            for particle in particles:
                particle.draw(screen)

        # Spawn a new triangle if the list is empty
        if not mini_triangles:
            triangle_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            mini_triangles.append(MiniTriangle(triangle_color, random_point_in_circle(big_ball_radius - 150, big_ball_center), side_length=20, velocity=[-4, -4]))
            timer = 0

        pygame.display.flip()
