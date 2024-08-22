import pygame
import sys
import math
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
BLACK = (1, 10, 20)
WHITE = (255, 255, 255)

# Ball properties
big_ball_radius = 256
big_ball_center = (WIDTH // 2, HEIGHT // 2)
gravity = pygame.Vector2(0, 0.15)

# Load MIDI file
midi_file = MidiFile("midi/tokyo.mid")

# Font initialization
font = pygame.font.Font(None, 36)

class MiniBall:
    def __init__(self, color, initial_position, radius, velocity):
        self.position = pygame.Vector2(initial_position)
        self.prevPos = self.position.copy()
        self.radius = radius
        self.velocity = pygame.Vector2(velocity)
        self.note_iterator = iter(midi_file)  # MIDI note iterator
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
        if len(self.tail) > 10:  # Limit the tail length
            self.tail.pop(0)

    def draw_tail(self, screen):
        tail_length = len(self.tail)
        for i in range(tail_length):
            alpha = int(200 * (i / tail_length))  # Fading effect
            tail_color = (*self.color[:3], alpha)
            tail_surface = pygame.Surface((2 * self.radius, 2 * self.radius), pygame.SRCALPHA)
            pygame.draw.circle(tail_surface, tail_color, (self.radius, self.radius), self.radius)
            screen.blit(tail_surface, (self.tail[i].x - self.radius, self.tail[i].y - self.radius))

    def check_collision(self, big_mask, big_ball_rect):
        mini_ball_rect = self.image.get_rect(center=(int(self.position.x), int(self.position.y)))
        offset = (mini_ball_rect.left - big_ball_rect.left, mini_ball_rect.top - big_ball_rect.top)
        if big_mask.overlap(self.mask, offset):
            return True
        return False

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
            pitch = msg.note + 10 # Transpose up one octave
            midi_output.note_on(pitch, velocity)

    def bounce(self, normal):
        # Use previous position to bounce
        self.position = self.prevPos.copy()
        speed = self.velocity.length()
        new_velocity = self.velocity.reflect(normal)
        self.velocity = new_velocity.normalize() * speed
        self.position += self.velocity * 0.1
        self.position += normal * 2

    def draw(self, screen):
        self.draw_tail(screen)
        screen.blit(self.image, (int(self.position.x) - self.radius, int(self.position.y) - self.radius))

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
mini_ball = MiniBall((255, 255, 255), (WIDTH / 2, HEIGHT / 2), radius=35, velocity=[-5, -5])

running = False

collision_points = []
# collision_points2 = []
# collision_points3 = []
# collision_points4 = []
angle_increment = 0.02

# Initialize big ball masks and images
big_ball_mask, big_ball_image = create_big_ball_mask(big_ball_radius, (232, 114, 242), 4, collision_points)
big_ball_rect = big_ball_image.get_rect(center=big_ball_center)

# big_ball_mask2, big_ball_image2 = create_big_ball_mask(200, (189, 119, 252), 4, collision_points2)
# big_ball_rect2 = big_ball_image2.get_rect(center=big_ball_center)

# big_ball_mask3, big_ball_image3 = create_big_ball_mask(250, (134, 119, 230), 4, collision_points3)
# big_ball_rect3 = big_ball_image3.get_rect(center=big_ball_center)

# big_ball_mask4, big_ball_image4 = create_big_ball_mask(300, (119, 152, 252), 4, collision_points4)
# big_ball_rect4 = big_ball_image4.get_rect(center=big_ball_center)

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
        mini_ball.move()

        # Changing color effect
        color.hsla = (h, s, l, 100)
        h += 1 * colorDir
        if h >= 360:
            h = 359  # Keep h in bounds
            colorDir = -1
        elif h <= 0:
            h = 1
            colorDir = 1

        if mini_ball.check_collision(big_ball_mask, big_ball_rect):
            normal = (mini_ball.position - pygame.Vector2(big_ball_center)).normalize()
            mini_ball.bounce(normal)
            mini_ball.play_collision_note()
            collision_dir = mini_ball.position - pygame.Vector2(big_ball_center)
            collision_angle = math.atan2(-collision_dir.y, collision_dir.x) % (2 * math.pi)
            gap_start = collision_angle - 0.05
            gap_end = collision_angle + 0.05
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
            big_ball_mask, big_ball_image = create_big_ball_mask(big_ball_radius, (232, 114, 242), 4, collision_points)
            big_ball_rect = big_ball_image.get_rect(center=big_ball_center)

        # if mini_ball.check_collision(big_ball_mask2, big_ball_rect2):
        #     normal = (mini_ball.position - pygame.Vector2(big_ball_center)).normalize()
        #     mini_ball.bounce(normal)
        #     mini_ball.play_collision_note()
        #     collision_dir = mini_ball.position - pygame.Vector2(big_ball_center)
        #     collision_angle = math.atan2(-collision_dir.y, collision_dir.x) % (2 * math.pi)
        #     gap_start = collision_angle - 0.05
        #     gap_end = collision_angle + 0.05
        #     collision_points2.append((gap_start, gap_end))
        #     # Merge overlapping gaps
        #     collision_points2.sort()
        #     merged_gaps = []
        #     current_start, current_end = collision_points2[0]
        #     for start, end in collision_points2[1:]:
        #         if start <= current_end:
        #             current_end = max(current_end, end)
        #         else:
        #             merged_gaps.append((current_start, current_end))
        #             current_start, current_end = start, end
        #     merged_gaps.append((current_start, current_end))
        #     collision_points2 = merged_gaps
        #     big_ball_mask2, big_ball_image2 = create_big_ball_mask(200, (189, 119, 252), 4, collision_points2)
        #     big_ball_rect2 = big_ball_image2.get_rect(center=big_ball_center)

        # if mini_ball.check_collision(big_ball_mask3, big_ball_rect3):
        #     normal = (mini_ball.position - pygame.Vector2(big_ball_center)).normalize()
        #     mini_ball.bounce(normal)
        #     mini_ball.play_collision_note()
        #     collision_dir = mini_ball.position - pygame.Vector2(big_ball_center)
        #     collision_angle = math.atan2(-collision_dir.y, collision_dir.x) % (2 * math.pi)
        #     gap_start = collision_angle - 0.05
        #     gap_end = collision_angle + 0.05
        #     collision_points3.append((gap_start, gap_end))
        #     # Merge overlapping gaps
        #     collision_points3.sort()
        #     merged_gaps = []
        #     current_start, current_end = collision_points3[0]
        #     for start, end in collision_points3[1:]:
        #         if start <= current_end:
        #             current_end = max(current_end, end)
        #         else:
        #             merged_gaps.append((current_start, current_end))
        #             current_start, current_end = start, end
        #     merged_gaps.append((current_start, current_end))
        #     collision_points3 = merged_gaps
        #     big_ball_mask3, big_ball_image3 = create_big_ball_mask(250, (134, 119, 230), 4, collision_points3)
        #     big_ball_rect3 = big_ball_image3.get_rect(center=big_ball_center)

        # if mini_ball.check_collision(big_ball_mask4, big_ball_rect4):
        #     normal = (mini_ball.position - pygame.Vector2(big_ball_center)).normalize()
        #     mini_ball.bounce(normal)
        #     mini_ball.play_collision_note()
        #     collision_dir = mini_ball.position - pygame.Vector2(big_ball_center)
        #     collision_angle = math.atan2(-collision_dir.y, collision_dir.x) % (2 * math.pi)
        #     gap_start = collision_angle - 0.05
        #     gap_end = collision_angle + 0.05
        #     collision_points4.append((gap_start, gap_end))
        #     # Merge overlapping gaps
        #     collision_points4.sort()
        #     merged_gaps = []
        #     current_start, current_end = collision_points4[0]
        #     for start, end in collision_points4[1:]:
        #         if start <= current_end:
        #             current_end = max(current_end, end)
        #         else:
        #             merged_gaps.append((current_start, current_end))
        #             current_start, current_end = start, end
        #     merged_gaps.append((current_start, current_end))
        #     collision_points4 = merged_gaps
        #     big_ball_mask4, big_ball_image4 = create_big_ball_mask(300, (119, 152, 252), 4, collision_points4)
        #     big_ball_rect4 = big_ball_image4.get_rect(center=big_ball_center)

        # Draw everything
        screen.fill(BLACK)
        screen.blit(big_ball_image, big_ball_rect.topleft)
        # screen.blit(big_ball_image2, big_ball_rect2.topleft)
        # screen.blit(big_ball_image3, big_ball_rect3.topleft)
        # screen.blit(big_ball_image4, big_ball_rect4.topleft)
        mini_ball.draw(screen)

        pygame.display.flip()
