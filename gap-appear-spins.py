import pygame
import sys
import math
import pygame.midi
from mido import MidiFile
import random

# Initialize Pygame
pygame.init()
pygame.midi.init()
# output_device_id = 0
midi_output = pygame.midi.Output(pygame.midi.get_default_output_id())
midi_output.set_instrument(15)

# Screen dimensions
WIDTH, HEIGHT = 800, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bouncing Balls within a Ball")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Ball properties
big_ball_radius = 260
big_ball_center = (WIDTH // 2, HEIGHT // 2)
gravity = pygame.Vector2(0, 0.18)

# Load MIDI file
midi_file = MidiFile("midi/levelll.mid")
note_on_messages = [msg for msg in midi_file if msg.type == 'note_on']
note_index = 0

# Font initialization
font = pygame.font.Font(None, 36)

baba_sound = pygame.mixer.Sound("sounds/BABABOI.mp3")

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
        self.tail_color_phase = 0  # Phase for the rainbow wave effect

    def move(self):
        self.prevPos = self.position.copy()  # Keep track of previous position
        self.velocity += gravity
        self.position += self.velocity
        self.update_tail()

    def update_tail(self):
        self.tail.append(self.position.copy())
        if len(self.tail) > 10:  # Limit the tail length
            self.tail.pop(0)

    def draw_tail(self, screen):
        tail_length = len(self.tail)
        self.tail_color_phase += 0.01  # Update the phase to animate the wave more slowly
        for i in range(tail_length):
            alpha = int(255 * (i / tail_length))  # Fading effect
            hue = (self.tail_color_phase + i * 0.08) % 1.0  # Calculate hue for the wave effect, adjust step for slower change
            tail_color = pygame.Color(0)
            tail_color.hsva = (hue * 360, 100, 100)  # Convert HSV to RGB
            tail_color.a = alpha  # Set the alpha value separately
            tail_surface = pygame.Surface((2 * self.radius, 2 * self.radius), pygame.SRCALPHA)
            pygame.draw.circle(tail_surface, tail_color, (self.radius, self.radius), self.radius)
            screen.blit(tail_surface, (self.tail[i].x - self.radius, self.tail[i].y - self.radius))

    def check_collision(self, big_mask, big_ball_rect):
        mini_ball_rect = self.image.get_rect(center=(int(self.position.x), int(self.position.y)))
        offset = (mini_ball_rect.left - big_ball_rect.left, mini_ball_rect.top - big_ball_rect.top)
        if big_mask.overlap(self.mask, offset):
            return True
        return False

    @staticmethod
    def play_collision_note():
        global note_index
        if note_index >= len(note_on_messages):
            note_index = 0

        msg = note_on_messages[note_index]
        note_index += 1

        velocity = 100  # Volume (0-127)
        pitch = msg.note + 2  # Transpose up one octave
        midi_output.note_on(pitch, velocity)

    def bounce(self, normal, particles):
        # Calculate the collision point
        dir_to_center = self.position - pygame.Vector2(big_ball_center)
        dir_to_center = dir_to_center.normalize() * big_ball_radius
        collision_point = pygame.Vector2(big_ball_center) + dir_to_center

        # Use previous position to bounce
        self.position = self.prevPos.copy()
        speed = self.velocity.length()
        new_velocity = self.velocity.reflect(normal)
        self.velocity = new_velocity.normalize() * speed
        self.position += self.velocity * 0.1
        self.position += normal * 2

        # Create particles at the collision point
        self.createParticles(collision_point, particles)

    def createParticles(self, collision_point, particles, num_particles=10):
        for _ in range(num_particles):
            velocity = pygame.Vector2(random.uniform(-3, 3), random.uniform(-3, 3))
            color = (255, 255, 255)
            lifespan = random.randint(30, 50)
            particles.append(Particle(collision_point, velocity, color, lifespan))

    def explode(self, particles):
        collision_point = self.position
        self.createParticles(collision_point, particles, num_particles=50)
        self.radius = 0  # Hide the ball

    def draw(self, screen, bounce_count):
        if self.radius > 0:  # Only draw if the ball is not exploded
            self.draw_tail(screen)
            screen.blit(self.image, (int(self.position.x) - self.radius, int(self.position.y) - self.radius))
            drawText(str(abs(60 - bounce_count)), font, WHITE, screen, int(self.position.x), int(self.position.y), 35)
            pygame.draw.circle(screen, WHITE, (self.position.x, self.position.y), self.radius, 10)

def drawText(text, font, color, surface, x, y, size=36, alpha=255):
    font = pygame.font.Font(None, size)
    textobj = font.render(text, True, color)
    textobj.set_alpha(alpha)
    textrect = textobj.get_rect()
    textrect.center = (x, y)
    surface.blit(textobj, textrect)

# Create the big ball mask with gaps at specified angles
def create_big_ball_mask(radius, color, arc_width=10, gaps=[]):
    image = pygame.Surface((2 * radius, 2 * radius), pygame.SRCALPHA)
    rect = image.get_rect()
    full_circle = 2 * math.pi

    if not gaps:
        pygame.draw.circle(image, color, (radius, radius), radius, arc_width + 1)
    else:
        gaps = sorted(gaps)
        start_angle = 0
        for gap_start, gap_end in gaps:
            if start_angle < gap_start:
                pygame.draw.arc(image, color, rect, start_angle, gap_start, arc_width)
            start_angle = gap_end
        if start_angle < full_circle:
            pygame.draw.arc(image, color, rect, start_angle, full_circle, arc_width)

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
mini_ball = MiniBall((0, 0, 0), (WIDTH / 2, HEIGHT / 2), radius=55, velocity=[-6, -6])
particles = []

running = False

collision_points = []
rotation_angle = 0  # Initialize rotation angle
rotation_speed = 0.6  # Rotation speed

# Initialize big ball masks and images
big_ball_mask, big_ball_image = create_big_ball_mask(big_ball_radius, (color.r, color.g, color.b), 9, collision_points)
big_ball_rect = big_ball_image.get_rect(center=big_ball_center)

bounce_count = 0  # Initialize bounce counter

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
        if mini_ball.radius > 0:
            mini_ball.move()

        if mini_ball.radius > 0 and mini_ball.check_collision(big_ball_mask, big_ball_rect):
            normal = (mini_ball.position - pygame.Vector2(big_ball_center)).normalize()
            mini_ball.bounce(normal, particles)
            mini_ball.play_collision_note()
            bounce_count += 1
            collision_dir = mini_ball.position - pygame.Vector2(big_ball_center)
            collision_angle = math.atan2(-collision_dir.y, collision_dir.x) % (2 * math.pi)
            adjusted_angle = (collision_angle - math.radians(rotation_angle)) % (2 * math.pi)
            gap_start = adjusted_angle - 0.05
            gap_end = adjusted_angle + 0.05
            collision_points.append((gap_start, gap_end))
            # Merge overlapping gaps
            collision_points.sort()
            merged_gaps = []
            current_start, current_end = collision_points[0]
            for start, end in collision_points[1:]:
                if start <= current_end:
                    current_end = max(current_end, end)
                else:
                    merged_gaps.append((current_start, current_end))
                    current_start, current_end = start, end
            merged_gaps.append((current_start, current_end))
            collision_points = merged_gaps
            big_ball_mask, big_ball_image = create_big_ball_mask(big_ball_radius, (color.r, color.g, color.b), 9, collision_points)
            big_ball_rect = big_ball_image.get_rect(center=big_ball_center)

        # Trigger explosion after 60 bounces
        if bounce_count >= 60 and mini_ball.radius > 0:
            baba_sound.play()
            mini_ball.explode(particles)

        # Changing color effect
        color.hsla = (h, s, l, 100)
        h += 3 * colorDir
        if h >= 360:
            h = 359  # Keep h in bounds
            colorDir = -1
        elif h <= 0:
            h = 1
            colorDir = 1

        # Update and draw particles
        for particle in particles:
            particle.update()
        particles = [particle for particle in particles if particle.lifespan > 0]

        # Draw everything
        screen.fill(BLACK)

        # Rotate the big ball image
        rotation_angle += rotation_speed  # Adjust the rotation speed as needed
        rotated_big_ball_image = pygame.transform.rotate(big_ball_image, rotation_angle)
        rotated_rect = rotated_big_ball_image.get_rect(center=big_ball_center)
        screen.blit(rotated_big_ball_image, rotated_rect.topleft)
        
        mini_ball.draw(screen, bounce_count)

        for particle in particles:
            particle.draw(screen)

        pygame.display.flip()
