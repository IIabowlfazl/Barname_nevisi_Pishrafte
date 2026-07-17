# A small pygame shooting game: pull the projectile from the sling and
# hit the targets. Press R to restart.

import math
import random

import pygame

WIDTH, HEIGHT = 1100, 650
FPS = 60
GRAVITY = 0.38
MAX_SHOTS = 6
TARGET_COUNT = 7

SLING_POS = pygame.Vector2(140, HEIGHT - 140)
MAX_PULL = 140
MIN_LAUNCH_SPEED = 6.0
MAX_LAUNCH_SPEED = 20.0

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Abolfazl Sahraie")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Tahoma", 22)
big_font = pygame.font.SysFont("Tahoma", 48)

WHITE = (235, 235, 235)
BLACK = (20, 20, 28)
STEEL = (60, 70, 90)
NAVY = (25, 35, 55)
DARK_RED = (160, 40, 40)
ORANGE = (210, 130, 40)
SILVER = (180, 190, 205)
GREEN = (60, 150, 95)


def spawn_targets():
    targets = []
    for _ in range(TARGET_COUNT):
        x = random.randint(550, WIDTH - 80)
        y = random.randint(120, HEIGHT - 170)
        r = random.randint(22, 35)
        targets.append({"pos": pygame.Vector2(x, y), "r": r, "alive": True})
    return targets


def spawn_particles(pos, color):
    particles = []
    for _ in range(25):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 6)
        particles.append({
            "pos": pygame.Vector2(pos),
            "vel": pygame.Vector2(math.cos(angle) * speed, math.sin(angle) * speed),
            "life": random.randint(20, 45),
            "color": color,
        })
    return particles


def draw_background():
    for i in range(HEIGHT):
        c = (18 + int(30 * i / HEIGHT), 30 + int(40 * i / HEIGHT), 55 + int(60 * i / HEIGHT))
        pygame.draw.line(screen, c, (0, i), (WIDTH, i))
    pygame.draw.rect(screen, (30, 60, 40), (0, HEIGHT - 120, WIDTH, 120))
    pygame.draw.rect(screen, (40, 80, 50), (0, HEIGHT - 80, WIDTH, 80))


def draw_trajectory(start_pos, velocity, steps=40, dt=0.18):
    pos = pygame.Vector2(start_pos)
    vel = pygame.Vector2(velocity)
    for _ in range(steps):
        vel.y += GRAVITY * dt
        pos += vel * dt
        if pos.y > HEIGHT - 120:
            break
        radius = 4 if _ % 2 == 0 else 3
        pygame.draw.circle(screen, (200, 200, 210), (int(pos.x), int(pos.y)), radius)


def main():
    ball_radius = 18
    ball_pos = SLING_POS.copy()
    ball_vel = pygame.Vector2(0, 0)
    ball_launched = False
    dragging = False
    targets = spawn_targets()
    particles = []
    score = 0
    shots_left = MAX_SHOTS
    game_over = False

    while True:
        clock.tick(FPS)
        draw_background()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            if event.type == pygame.MOUSEBUTTONDOWN and not ball_launched and not game_over:
                mx, my = pygame.mouse.get_pos()
                if pygame.Vector2(mx, my).distance_to(ball_pos) <= ball_radius + 10:
                    dragging = True

            if event.type == pygame.MOUSEBUTTONUP and dragging and not game_over:
                dragging = False
                pull_vec = SLING_POS - ball_pos
                pull_len = pull_vec.length()
                if pull_len > 2:
                    pull_ratio = min(pull_len / MAX_PULL, 1.0)
                    speed = MIN_LAUNCH_SPEED + (MAX_LAUNCH_SPEED - MIN_LAUNCH_SPEED) * pull_ratio
                    ball_vel = pull_vec.normalize() * speed
                    ball_launched = True
                    shots_left -= 1
                ball_pos = SLING_POS.copy()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                ball_pos = SLING_POS.copy()
                ball_vel = pygame.Vector2(0, 0)
                ball_launched = False
                shots_left = MAX_SHOTS
                score = 0
                game_over = False
                targets = spawn_targets()
                particles = []

        if dragging:
            mx, my = pygame.mouse.get_pos()
            pull = pygame.Vector2(mx, my) - SLING_POS
            if pull.length() > MAX_PULL:
                pull.scale_to_length(MAX_PULL)
            ball_pos = SLING_POS + pull
            pull_vec = SLING_POS - ball_pos
            pull_len = pull_vec.length()
            if pull_len > 2:
                pull_ratio = min(pull_len / MAX_PULL, 1.0)
                speed = MIN_LAUNCH_SPEED + (MAX_LAUNCH_SPEED - MIN_LAUNCH_SPEED) * pull_ratio
                draw_trajectory(SLING_POS, pull_vec.normalize() * speed)

        if ball_launched:
            ball_vel.y += GRAVITY
            ball_pos += ball_vel
            if ball_pos.y >= HEIGHT - 120 - ball_radius:
                ball_pos.y = HEIGHT - 120 - ball_radius
                ball_vel.y *= -0.5
                ball_vel.x *= 0.7
                if abs(ball_vel.y) < 1.2:
                    ball_vel.y = 0
            if ball_pos.x < ball_radius:
                ball_pos.x = ball_radius
                ball_vel.x *= -0.6
            if ball_pos.x > WIDTH - ball_radius:
                ball_pos.x = WIDTH - ball_radius
                ball_vel.x *= -0.6
            if ball_vel.length() < 0.3:
                ball_launched = False
                ball_vel = pygame.Vector2(0, 0)
                ball_pos = SLING_POS.copy()

        for t in targets:
            if t["alive"] and ball_pos.distance_to(t["pos"]) <= t["r"] + ball_radius:
                t["alive"] = False
                score += 100
                particles += spawn_particles(t["pos"], ORANGE)

        for p in particles[:]:
            p["pos"] += p["vel"]
            p["vel"].y += 0.08
            p["life"] -= 1
            if p["life"] <= 0:
                particles.remove(p)

        for t in targets:
            if t["alive"]:
                pygame.draw.circle(screen, STEEL, (int(t["pos"].x), int(t["pos"].y)), t["r"])
                pygame.draw.circle(screen, SILVER, (int(t["pos"].x) - 8, int(t["pos"].y) - 6), t["r"] // 3)

        for p in particles:
            pygame.draw.circle(screen, p["color"], (int(p["pos"].x), int(p["pos"].y)), 3)

        pygame.draw.circle(screen, DARK_RED, (int(ball_pos.x), int(ball_pos.y)), ball_radius)
        pygame.draw.circle(screen, WHITE, (int(ball_pos.x) - 5, int(ball_pos.y) - 6), 5)
        pygame.draw.line(screen, SILVER, (90, HEIGHT - 140), (150, HEIGHT - 140), 6)
        pygame.draw.circle(screen, SILVER, (int(SLING_POS.x), int(SLING_POS.y)), 15)

        screen.blit(font.render(f"Score: {score}", True, WHITE), (30, 20))
        screen.blit(font.render(f"Shots Left: {shots_left}", True, WHITE), (30, 50))

        if shots_left <= 0 and not ball_launched:
            game_over = True
            msg = big_font.render("GAME OVER", True, ORANGE)
            msg2 = font.render("Press R to restart", True, WHITE)
            screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2 - 60))
            screen.blit(msg2, (WIDTH // 2 - msg2.get_width() // 2, HEIGHT // 2 + 10))

        pygame.display.flip()


if __name__ == "__main__":
    main()
