import pygame
import sys
import math
import random
import pygame.midi
from mido import MidiFile

# Initialize Pygame and MIDI
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
big_ball_radius = 150
big_ball2_radius = 200
big_ball3_radius = 250
big_ball4_radius = 300
big_ball_center = (WIDTH // 2, HEIGHT // 2)
gravity = pygame.Vector2(0, 0.15)

# Load MIDI file and pre-process note_on messages
midi_file = MidiFile("midi/levelsfive.mid")
note_on_messages = [msg for msg in midi_file if msg.type == 'note_on']
note_index = 0

# Font initialization
font = pygame.font.Font(None, 36)

# Create the big ball mask with an arc and a customizable gap
def create_big_ball_mask(radius, hue, arc_width=10, start_angle=0.5, end_angle=2 * math.pi):
    color = pygame.Color(0)
    color.hsla = (hue, 100, 50, 100)
    image = pygame.Surface((2 * radius, 2 * radius), pygame.SRCALPHA)
    rect = image.get_rect()
    pygame.draw.arc(image, color, rect, start_angle, end_angle, arc_width)
    mask = pygame.mask.from_surface(image)
    return mask, image

class Particle:
    def __init__(self, position, velocity, color, lifespan):
        self.position = pygame.Vector2(position)
        self.velocity = pygame.Vector2(velocity)
        self.color = pygame.Color(*color[:3], 255)  # Ensure the color has an alpha value
        self.lifespan = lifespan

    def update(self):
        self.position += self.velocity
        self.velocity += gravity  # Apply gravity to particles
        self.lifespan -= 2
        if self.lifespan < 0:
            self.lifespan = 0

    def draw(self, screen):
        if self.lifespan > 0:
            alpha = int(255 * (self.lifespan / 50))
            color = pygame.Color(self.color.r, self.color.g, self.color.b, alpha)
            pygame.draw.circle(screen, color, (int(self.position.x), int(self.position.y)), 3)

class MiniBall:
    def __init__(self, color, initial_position, radius, velocity):
        self.position = pygame.Vector2(initial_position)
        self.prevPos = self.position.copy()
        self.radius = radius
        self.velocity = pygame.Vector2(velocity)
        self.color = pygame.Color(*color)
        self.image = pygame.Surface((2 * radius, 2 * radius), pygame.SRCALPHA)
        pygame.draw.circle(self.image, self.color, (radius, radius), radius)
        self.mask = pygame.mask.from_surface(self.image)
        self.tail = []
        self.bounce_count = 0

    def update_image_and_mask(self):
        self.image = pygame.Surface((2 * self.radius, 2 * self.radius), pygame.SRCALPHA)
        pygame.draw.circle(self.image, self.color, (self.radius, self.radius), self.radius)
        self.mask = pygame.mask.from_surface(self.image)

    def move(self):
        self.prevPos = self.position.copy()  # Keep track of previous position
        self.velocity += gravity
        self.position += self.velocity

        self.update_tail()

    def update_tail(self):
        self.tail.append(self.position.copy())
        if len(self.tail) > 10:  # Limit the tail length
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
    
    def draw_tail(self, screen):
        tail_length = len(self.tail)
        for i in range(tail_length):
            alpha = int(128 * (i / tail_length))  # Fading effect
            tail_color = (*self.color[:3], alpha)
            tail_surface = pygame.Surface((2 * self.radius, 2 * self.radius), pygame.SRCALPHA)
            pygame.draw.circle(tail_surface, tail_color, (self.radius, self.radius), self.radius)
            screen.blit(tail_surface, (self.tail[i].x - self.radius, self.tail[i].y - self.radius))

    @staticmethod
    def play_collision_note():
        global note_index
        if note_index >= len(note_on_messages):
            note_index = 0

        msg = note_on_messages[note_index]
        note_index += 1

        velocity = 100  # Volume (0-127)
        pitch = msg.note + 1  # Transpose up one octave
        midi_output.note_on(pitch, velocity)

    def bounce(self, particles, normal, radius_circle):
        self.position = self.prevPos.copy()
        speed = self.velocity.length()
        new_velocity = self.velocity.reflect(normal)
        self.velocity = new_velocity.normalize() * speed
        self.position += self.velocity * 0.1
        self.position += normal * 1

        # self.update_image_and_mask()
        self.bounce_count += 1

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
        # self.createParticles(self.position, particles)

        self.bounce_count += 1  # Increment bounce count

    def draw(self, screen, isStationary=False):
        screen.blit(self.image, (int(self.position.x) - self.radius, int(self.position.y) - self.radius))
        
        if not isStationary:
            self.draw_tail(screen)
        
        pygame.draw.circle(screen, WHITE, (self.position.x, self.position.y), self.radius, 4)

def drawText(text, font, color, surface, x, y, size=36, alpha=255):
    textobj = font.render(text, True, color)
    textobj.set_alpha(alpha)
    textrect = textobj.get_rect()
    textrect.center = (x, y)
    surface.blit(textobj, textrect)

def create_particles_around_circle(center, radius, particles, hue, num_particles=100):
    for _ in range(num_particles):
        angle = random.uniform(0, 2 * math.pi)
        position = pygame.Vector2(
            center[0] + math.cos(angle) * radius,
            center[1] + math.sin(angle) * radius
        )
        velocity = pygame.Vector2(random.uniform(-2, 2), random.uniform(-2, 2))
        color = pygame.Color(0)
        color.hsla = (hue, 100, 50, 100)
        lifespan = random.randint(30, 50)
        particles.append(Particle(position, velocity, color, lifespan))

# Main loop
clock = pygame.time.Clock()

# Start with two mini balls
mini_balls = [MiniBall((255, 0, 0), (WIDTH / 2 - 10, HEIGHT / 2 - 90), radius=15, velocity=[-2, -2])]
stationary_balls = []
particles = []

running = False

start_angle = 0.5 + 0.5
end_angle = 2 * math.pi + 0.5

start_angle2 = 0.5 + 3.7 + 6
end_angle2 = 2 * math.pi + 3.7 + 6

start_angle3 = 0.5 + 6
end_angle3 = 2 * math.pi + 6

start_angle4 = 0.5 + 8
end_angle4 = 2 * math.pi + 8

angle_increment = 0.02

# Initial hues for big circles
hue1 = 200
hue2 = 180
hue3 = 160
hue4 = 140
hue_increment = 1  # Increment for changing the hue

big_ball_visible = True  # Flag to control visibility of the big ball
big_ball2_visible = True  # Flag to control visibility of the big ball
big_ball3_visible = True  # Flag to control visibility of the big ball
big_ball4_visible = True  # Flag to control visibility of the big ball

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
        # Update hue values for big circles
        hue1 = (hue1 + hue_increment) % 360
        hue2 = (hue2 + hue_increment) % 360
        hue3 = (hue3 + hue_increment) % 360
        hue4 = (hue4 + hue_increment) % 360

        # Update angles to create spinning effect
        start_angle += angle_increment
        end_angle += angle_increment
        start_angle2 -= angle_increment
        end_angle2 -= angle_increment
        start_angle3 += angle_increment
        end_angle3 += angle_increment
        start_angle4 -= angle_increment
        end_angle4 -= angle_increment

        for mini_ball in mini_balls:
            # Move mini balls
            mini_ball.move()

            # ----------------------------------------------------------------------------------------------------------------
            # Check collisions for mini_ball
            if big_ball_visible:
                big_ball_mask, big_ball_image = create_big_ball_mask(big_ball_radius, hue1, 5, start_angle, end_angle)
                big_ball_rect = big_ball_image.get_rect(center=big_ball_center)

                if mini_ball.check_collision(big_ball_mask, big_ball_rect):
                    normal = (mini_ball.position - pygame.Vector2(big_ball_center)).normalize()
                    mini_ball.bounce(particles, normal, big_ball_radius)
                    MiniBall.play_collision_note()

                # Check if the mini ball escapes through the gap
                dir_to_center = mini_ball.position - pygame.Vector2(big_ball_center)
                distance = dir_to_center.length()
                angle = math.atan2(dir_to_center.y, dir_to_center.x) % (2 * math.pi)

                gap_min = start_angle % (2 * math.pi)
                gap_max = end_angle % (2 * math.pi)
                if gap_min < gap_max:
                    in_gap = gap_min <= angle <= gap_max
                else:
                    in_gap = angle >= gap_min or angle <= gap_max

                if in_gap and distance > big_ball_radius:
                    create_particles_around_circle(big_ball_center, big_ball_radius, particles, hue1)
                    big_ball_visible = False
            # ----------------------------------------------------------------------------------------------------------------
            # Check collisions for mini_ball
            if big_ball2_visible:
                big_ball2_mask, big_ball2_image = create_big_ball_mask(big_ball2_radius, hue2, 5, start_angle2, end_angle2)
                big_ball2_rect = big_ball2_image.get_rect(center=big_ball_center)

                if mini_ball.check_collision(big_ball2_mask, big_ball2_rect):
                    normal = (mini_ball.position - pygame.Vector2(big_ball_center)).normalize()
                    mini_ball.bounce(particles, normal, big_ball2_radius)
                    MiniBall.play_collision_note()

                # Check if the mini ball escapes through the gap
                dir_to_center = mini_ball.position - pygame.Vector2(big_ball_center)
                distance = dir_to_center.length()
                angle = math.atan2(dir_to_center.y, dir_to_center.x) % (2 * math.pi)

                gap_min = start_angle2 % (2 * math.pi)
                gap_max = end_angle2 % (2 * math.pi)
                if gap_min < gap_max:
                    in_gap = gap_min <= angle <= gap_max
                else:
                    in_gap = angle >= gap_min or angle <= gap_max

                if in_gap and distance > big_ball2_radius:
                    create_particles_around_circle(big_ball_center, big_ball2_radius, particles, hue2)
                    big_ball2_visible = False
            # ----------------------------------------------------------------------------------------------------------------
            # Check collisions for mini_ball
            if big_ball3_visible:
                big_ball3_mask, big_ball3_image = create_big_ball_mask(big_ball3_radius, hue3, 5, start_angle3, end_angle3)
                big_ball3_rect = big_ball3_image.get_rect(center=big_ball_center)

                if mini_ball.check_collision(big_ball3_mask, big_ball3_rect):
                    normal = (mini_ball.position - pygame.Vector2(big_ball_center)).normalize()
                    mini_ball.bounce(particles, normal, big_ball3_radius)
                    MiniBall.play_collision_note()

                # Check if the mini ball escapes through the gap
                dir_to_center = mini_ball.position - pygame.Vector2(big_ball_center)
                distance = dir_to_center.length()
                angle = math.atan2(dir_to_center.y, dir_to_center.x) % (2 * math.pi)

                gap_min = start_angle3 % (2 * math.pi)
                gap_max = end_angle3 % (2 * math.pi)
                if gap_min < gap_max:
                    in_gap = gap_min <= angle <= gap_max
                else:
                    in_gap = angle >= gap_min or angle <= gap_max

                if in_gap and distance > big_ball3_radius:
                    create_particles_around_circle(big_ball_center, big_ball3_radius, particles, hue3)
                    big_ball3_visible = False
            # ----------------------------------------------------------------------------------------------------------------
            # Check collisions for mini_ball
            if big_ball4_visible:
                big_ball4_mask, big_ball4_image = create_big_ball_mask(big_ball4_radius, hue4, 5, start_angle4, end_angle4)
                big_ball4_rect = big_ball4_image.get_rect(center=big_ball_center)

                if mini_ball.check_collision(big_ball4_mask, big_ball4_rect):
                    normal = (mini_ball.position - pygame.Vector2(big_ball_center)).normalize()
                    mini_ball.bounce(particles, normal, big_ball4_radius)
                    MiniBall.play_collision_note()

                # Check if the mini ball escapes through the gap
                dir_to_center = mini_ball.position - pygame.Vector2(big_ball_center)
                distance = dir_to_center.length()
                angle = math.atan2(dir_to_center.y, dir_to_center.x) % (2 * math.pi)

                gap_min = start_angle4 % (2 * math.pi)
                gap_max = end_angle4 % (2 * math.pi)
                if gap_min < gap_max:
                    in_gap = gap_min <= angle <= gap_max
                else:
                    in_gap = angle >= gap_min or angle <= gap_max

                if in_gap and distance > big_ball4_radius:
                    create_particles_around_circle(big_ball_center, big_ball4_radius, particles, hue4)
                    big_ball4_visible = False

            collision, stationary_ball = mini_ball.check_collision_with_stationary(stationary_balls)
            if collision:
                mini_ball.resolve_collision_with_stationary(stationary_ball, particles)
                MiniBall.play_collision_note()

            # Check if the ball is out of bounds
            # if mini_ball.position.x < 0 or mini_ball.position.x > WIDTH or mini_ball.position.y < 0 or mini_ball.position.y > HEIGHT:
            #     mini_balls.pop()
            #     break

            if mini_ball.bounce_count >= 10:
                stationary_balls.append(mini_balls.pop())
                break

        # Draw everything
        screen.fill(BLACK)

        for mini_ball in mini_balls:
            mini_ball.draw(screen)

        for stationary_ball in stationary_balls:
            stationary_ball.draw(screen, True)

        # Update and draw particles
        for particle in particles:
            particle.update()
        particles = [particle for particle in particles if particle.lifespan > 0]

        if big_ball_visible:
            screen.blit(big_ball_image, big_ball_rect.topleft)
        if big_ball2_visible:
            screen.blit(big_ball2_image, big_ball2_rect.topleft)
        if big_ball3_visible:
            screen.blit(big_ball3_image, big_ball3_rect.topleft)
        if big_ball4_visible:
            screen.blit(big_ball4_image, big_ball4_rect.topleft)

        for particle in particles:
            particle.draw(screen)

        # Spawn a new ball if the list is empty
        if not mini_balls:
            ball_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            mini_balls.append(MiniBall(ball_color, (WIDTH / 2 - 10, HEIGHT / 2 - 90), radius=15, velocity=[-4, -4]))

        pygame.display.flip()

