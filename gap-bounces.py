import pygame
import sys
import math
import random
import pygame.midi
from mido import MidiFile, MidiTrack, Message

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
RED = (255, 0, 0)

# Ball properties
big_ball_radius = 250
big_ball_center = (WIDTH // 2, HEIGHT // 2)
gravity = pygame.Vector2(0, 0.25)

# Load MIDI file
midi_file = MidiFile("midi/alonewalker.mid")
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
        self.color = pygame.Color(*color)
        self.hue = self.color.hsla[0]
        self.saturation = self.color.hsla[1]
        self.lightness = self.color.hsla[2]
        self.image = pygame.Surface((2 * radius, 2 * radius), pygame.SRCALPHA)
        pygame.draw.circle(self.image, self.color, (radius, radius), radius)
        self.mask = pygame.mask.from_surface(self.image)
        self.is_moving = True
        self.tail = []
        self.bounce_count = 0  # Initialize bounce count

    def move(self):
        self.prevPos = self.position.copy()  # Keep track of previous position
        self.velocity += gravity
        self.position += self.velocity
        self.update_tail()

    def update_tail(self):
        self.tail.append(self.position.copy())
        if len(self.tail) > 20:  # Limit the tail length
            self.tail.pop(0)

    def check_collision(self, big_mask, big_ball_rect):
        mini_ball_rect = self.image.get_rect(center=(int(self.position.x), int(self.position.y)))
        offset = (mini_ball_rect.left - big_ball_rect.left, mini_ball_rect.top - big_ball_rect.top)
        if big_mask.overlap(self.mask, offset):
            return True
        return False

    def check_collision_with_stationary(self, stationary_balls):
        for ball in stationary_balls:
            distance = self.position.distance_to(ball.position)
            if distance <= self.radius + ball.radius:
                return True, ball
        return False, None

    def play_collision_note():
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
            pitch = msg.note + 2  # Transpose up one octave
            midi_output.note_on(pitch, velocity)

    def bounce(self, particles):
        # Calculate the collision point
        dir_to_center = self.position - pygame.Vector2(big_ball_center)
        dir_to_center = dir_to_center.normalize() * big_ball_radius
        collision_point = pygame.Vector2(big_ball_center) + dir_to_center

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

        # Create particles at the collision point
        self.createParticles(collision_point, particles)

        change_gap_position()

        self.bounce_count += 1  # Increment bounce count

    def resolve_collision_with_stationary(self, stationary_ball, particles):
        direction = self.position - stationary_ball.position
        distance = direction.length()
        if distance == 0:
            distance = 0.1  # Prevent division by zero
        overlap = self.radius + stationary_ball.radius - distance
        correction = direction.normalize() * overlap

        # Move the ball out of collision
        self.position += correction

        # Reflect the velocity
        self.velocity = self.velocity.reflect(direction.normalize())

        # Create particles at the collision point
        self.createParticles(self.position, particles)

        self.bounce_count += 1  # Increment bounce count

    def draw_tail(self, screen):
        tail_length = len(self.tail)
        for i in range(tail_length):
            alpha = int(255 * (i / tail_length))  # Fading effect
            tail_color = (*self.color[:3], alpha)
            tail_surface = pygame.Surface((2 * self.radius, 2 * self.radius), pygame.SRCALPHA)
            pygame.draw.circle(tail_surface, tail_color, (self.radius, self.radius), self.radius, 3)
            screen.blit(tail_surface, (self.tail[i].x - self.radius, self.tail[i].y - self.radius))

    def createParticles(self, collision_point, particles):
        num_particles = 10
        for _ in range(num_particles):
            velocity = pygame.Vector2(random.uniform(-3, 3), random.uniform(-3, 3))
            color = (random.randint(200, 255), random.randint(100, 255), random.randint(100, 255))
            lifespan = random.randint(30, 50)
            particles.append(Particle(collision_point, velocity, color, lifespan))

    def update_color(self, h):
        self.color.hsla = (h, self.saturation, self.lightness, 100)
        self.image.fill((0, 0, 0, 0))  # Clear the surface
        pygame.draw.circle(self.image, self.color, (self.radius, self.radius), self.radius)

    def draw(self, screen, timer=0, isStationary=False):
        screen.blit(self.image, (int(self.position.x) - self.radius, int(self.position.y) - self.radius))
        
        if not isStationary:
            self.draw_tail(screen)
            # if abs(int(timer) - 10) > 3:
            #     drawText(str(abs(int(timer) - 10)), font, WHITE, screen, int(self.position.x), int(self.position.y - 40), 45)
            # else:
            #     drawText(str(abs(int(timer) - 10)), font, RED, screen, int(self.position.x), int(self.position.y - 40), 45)

        pygame.draw.circle(screen, WHITE, (self.position.x, self.position.y), self.radius, 3)

def drawText(text, font, color, surface, x, y, size=36, alpha=255):
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

def change_gap_position():
    global start_angle, end_angle
    gap_size = end_angle - start_angle
    new_start_angle = random.uniform(0, 2 * math.pi)
    new_end_angle = new_start_angle + gap_size
    start_angle = new_start_angle
    end_angle = new_end_angle

# Main loop
clock = pygame.time.Clock()

# Color
color = pygame.Color(66, 219, 68)
h = color.hsla[0]
s = color.hsla[1]
l = color.hsla[2]
colorDir = 1

# Start with one mini ball
mini_balls = [MiniBall((color.r, color.g, color.b), (WIDTH / 2 -10, HEIGHT / 2 - 90), radius=15, velocity=[-4, -4])]
stationary_balls = []
particles = []

running = False

start_angle = 0.4
end_angle = 2 * math.pi
angle_increment = 0.018

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

    if running:
        for mini_ball in mini_balls:
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
            # start_angle += angle_increment
            # end_angle += angle_increment

            big_ball_mask, big_ball_image = create_big_ball_mask(big_ball_radius, (color.r, color.g, color.b), 10, start_angle, end_angle)
            big_ball_rect = big_ball_image.get_rect(center=big_ball_center)

            if mini_ball.check_collision(big_ball_mask, big_ball_rect):
                mini_ball.bounce(particles)
                MiniBall.play_collision_note()

            collision, stationary_ball = mini_ball.check_collision_with_stationary(stationary_balls)
            if collision:
                mini_ball.resolve_collision_with_stationary(stationary_ball, particles)
                MiniBall.play_collision_note()

            # Check if the ball is out of bounds
            if mini_ball.position.x < 0 or mini_ball.position.x > WIDTH or mini_ball.position.y < 0 or mini_ball.position.y > HEIGHT:
                mini_balls.pop()
                break

            if mini_ball.bounce_count >= 10:
                stationary_balls.append(mini_balls.pop())
                break

            # Update and draw particles
            for particle in particles:
                particle.update()
            particles = [particle for particle in particles if particle.lifespan > 0]

            # Draw everything
            screen.fill(BLACK)
            screen.blit(big_ball_image, big_ball_rect.topleft)

            for stationary_ball in stationary_balls:
                stationary_ball.draw(screen, mini_ball.bounce_count, True)

            for mini_ball in mini_balls:
                mini_ball.draw(screen, mini_ball.bounce_count)

            for particle in particles:
                particle.draw(screen)

        # Spawn a new ball if the list is empty
        if not mini_balls:
            ball_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            mini_balls.append(MiniBall(ball_color, (WIDTH / 2 - 10, HEIGHT / 2 - 90), radius=15, velocity=[-4, -4]))

        pygame.display.flip()
