
import math
import random
import sys

import pygame
import numpy as np


G = 9.81
MC = 1.0       
MP = 0.2        
L = 1.0        
DT = 0.02       
FORCE = 30.0    
NOISE = 0.02    

WIN_W = 800
WIN_H = 480
CART_W = 80
CART_H = 24
FPS = 50


class Pendulum:
   
    def __init__(self):
        self.theta = 0.15      
        self.omega = 0.0       

    def step(self, theta_ddot, dt=DT):
        self.omega += theta_ddot * dt
        self.theta += self.omega * dt

    def reset(self):
        self.theta = 0.15
        self.omega = 0.0


class Cart:
    
    def __init__(self):
        self.x = 0.0
        self.v = 0.0

    def step(self, x_ddot, dt=DT):
        self.v += x_ddot * dt
        self.x += self.v * dt

    def reset(self):
        self.x = 0.0
        self.v = 0.0


class Controller:
    
    def __init__(self):
        self.kx = 3.16
        self.kv = 6.69
        self.kth = 65.6
        self.kw = 24.4

    def control(self, theta, omega, x, v):
        # push to bring the pole upright and the cart to center
        u = self.kx * x + self.kv * v + self.kth * theta + self.kw * omega
        return max(-FORCE, min(FORCE, u))


class Simulation:
    # ties cart + pendulum with the cart-pole dynamics
    def __init__(self, auto=False):
        self.cart = Cart()
        self.pend = Pendulum()
        self.auto = auto
        self.controller = Controller()
        self.omega_n = 0.0      # last measured angle (with noise)
        self.alive = True

    def reset(self):
        self.cart.reset()
        self.pend.reset()
        self.controller = Controller()
        self.alive = True

    def _dynamics(self, u):
        # standard cart-pole equations of motion
        th = self.pend.theta
        o = self.pend.omega
        sin = math.sin(th)
        cos = math.cos(th)
        total = MC + MP
        # angular acceleration of the pole
        num = G * sin - (u + MP * L * o * o * sin) * cos / total
        den = L * (4.0 / 3.0 - MP * cos * cos / total)
        theta_ddot = num / den
        # linear acceleration of the cart
        x_ddot = (u + MP * L * (o * o * sin - theta_ddot * cos)) / total
        return theta_ddot, x_ddot

    def step(self, user_u=0.0):
        if not self.alive:
            return
        # choose control: auto controller or user input
        if self.auto:
            u = self.controller.control(self.pend.theta, self.pend.omega,
                                        self.cart.x, self.cart.v)
        else:
            u = user_u
        theta_ddot, x_ddot = self._dynamics(u)
        self.cart.step(x_ddot)
        self.pend.step(theta_ddot)

        # sensor noise on the measured angle
        self.omega_n = self.pend.theta + np.random.normal(0, NOISE)

        # fail conditions: pole fell over or cart left the track
        if abs(self.pend.theta) > math.pi / 2:
            self.alive = False
        if abs(self.cart.x) > 8.0:
            self.alive = False


class GUI:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("Inverted Pendulum")
        self.clock = pygame.time.Clock()
        self.sim = Simulation(auto=False)
        self.font = pygame.font.SysFont("consolas", 16)
        self.auto = False
        self.score = 0
        self.run()

    def run(self):
        running = True
        while running:
            # events
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False
                elif ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_a:
                        self.auto = not self.auto
                        self.sim.auto = self.auto
                    elif ev.key == pygame.K_r:
                        self.sim.reset()
                        self.score = 0

            # user force from arrow keys
            keys = pygame.key.get_pressed()
            u = 0.0
            if not self.auto:
                if keys[pygame.K_LEFT]:
                    u = -FORCE
                elif keys[pygame.K_RIGHT]:
                    u = FORCE

            # step physics at fixed rate
            for _ in range(2):
                self.sim.step(u)

            if self.sim.alive:
                self.score += 1

            self._draw()
            self.clock.tick(FPS)

        pygame.quit()

    def _draw(self):
        self.screen.fill((11, 16, 33))
        # track
        cy = WIN_H - 120
        pygame.draw.line(self.screen, (120, 140, 180),
                         (40, cy), (WIN_W - 40, cy), 3)
        # cart position
        cx = WIN_W // 2 + int(self.sim.cart.x * 60)
        cx = max(60, min(WIN_W - 60, cx))
        pygame.draw.rect(self.screen, (90, 169, 255),
                         (cx - CART_W // 2, cy - CART_H // 2,
                          CART_W, CART_H))
        # pole
        px = cx
        py = cy - CART_H // 2
        ang = self.sim.pend.theta
        ex = px + math.sin(ang) * 140
        ey = py - math.cos(ang) * 140
        col = (57, 217, 138) if self.sim.alive else (255, 91, 91)
        pygame.draw.line(self.screen, col, (px, py), (ex, ey), 8)
        pygame.draw.circle(self.screen, (255, 210, 63), (int(ex), int(ey)), 10)

        # text
        txt = (f"score={self.score}  auto={'ON' if self.auto else 'OFF'}  "
               f"theta={self.sim.pend.theta:.2f}  "
               f"measured={self.sim.omega_n:.2f}")
        self.screen.blit(self.font.render(txt, True, (200, 233, 200)), (12, 12))
        help_txt = "LEFT/RIGHT balance  A toggle auto  R reset"
        self.screen.blit(self.font.render(help_txt, True, (127, 209, 255)),
                         (12, 36))
        if not self.sim.alive:
            msg = self.font.render("FELL! press R to restart", True,
                                   (255, 91, 91))
            self.screen.blit(msg, (WIN_W // 2 - 110, 80))
        pygame.display.flip()


def main():
    GUI()


if __name__ == "__main__":
    main()
