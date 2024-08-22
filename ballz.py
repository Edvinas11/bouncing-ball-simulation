import os
import pygame
import sys
import random
import math
import time


pygame.init()
pygame.mixer.init(frequency=48000)

# ParamÃƒÂ¨tres de l'ÃƒÂ©cran
screen_width = 900
screen_height = 900

# Initialisation de l'ÃƒÂ©cran
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Animation avec Rebond et Nouvelles Balles")

clock = pygame.time.Clock()

animation_started = False

# Rectangle
rect_width = 650
rect_height = 400
rect_x = (screen_width - rect_width) // 2
rect_y = (screen_height - rect_height) // 2

# Classe pour reprÃƒÂ©senter une balle
class Ball:
    def __init__(self, x, y, radius, color, speed_x, speed_y):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.speed_x = speed_x
        self.speed_y = speed_y


# Initialisation de la premiÃƒÂ¨re balle
main_ball = Ball(rect_x + rect_width//2,
                 rect_y + rect_height//2,
                 10,
                 (255,0,0),
                 0.5, 0.5)


# Liste pour stocker les balles
balls = [main_ball]

# Chargement du son de rebond
bounce_sound = pygame.mixer.Sound("bubble.wav")

# Boucle principale
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()

        if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
            animation_started = True

    if animation_started:
        # Mise Ãƒ  jour de la position de chaque balle
        for ball in balls:
            ball.x += ball.speed_x
            ball.y += ball.speed_y

        # Rebondissement sur les bords du rectangle
        for ball in balls:
            if ball.x - ball.radius < rect_x or ball.x + ball.radius > rect_x + rect_width:
                ball.speed_x = -ball.speed_x
                bounce_sound.play()  # Jouer le son de rebond
                speedy = random.uniform(-1, 1)
                speedx = random.uniform(-1, 1)
                new_ball = Ball(random.randint(rect_x + ball.radius, rect_x + rect_width - ball.radius), random.randint(rect_y + ball.radius, rect_y + rect_height - ball.radius), 10,
                                (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), speedx, speedy)
                balls.append(new_ball)

            if ball.y - ball.radius < rect_y or ball.y + ball.radius > rect_y + rect_height:
                ball.speed_y = -ball.speed_y
                bounce_sound.play()  # Jouer le son de rebond
                speedx = random.uniform(-1, 1)
                speedy = random.uniform(-1, 1)
                new_ball = Ball(random.randint(rect_x + ball.radius, rect_x + rect_width - ball.radius), random.randint(rect_y + ball.radius, rect_y + rect_height - ball.radius), 10,
                                (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), speedx, speedy)
                balls.append(new_ball)

        # RafraÃƒÂ®chissement de l'ÃƒÂ©cran
        screen.fill((0, 0, 0))
        pygame.draw.rect(screen, (255, 255, 255), (rect_x, rect_y, rect_width, rect_height), 1)  # Dessiner le rectangle
        pygame.draw.rect(screen, (255, 255, 255), (rect_x - 5, rect_y - 5, rect_width + 10, rect_height + 10), 5)  # Dessiner le rectangle


        # Dessiner chaque balle
        for ball in balls:
            pygame.draw.circle(screen, ball.color, (ball.x, ball.y), ball.radius)

        # Mettre Ãƒ  jour l'affichage
        pygame.display.flip()

        # ContrÃƒÂ´ler la frÃƒÂ©quence de rafraÃƒÂ®chissement de l'ÃƒÂ©cran
        clock.tick(60)