import pygame

from game.game_engine import GameEngine


pygame.init()

WIDTH, HEIGHT = 800, 400

SCREEN = pygame.display.set_mode(
    (WIDTH, HEIGHT)
)

pygame.display.set_caption(
    "Endless Runner - Pygame Version"
)

SKY = (200, 220, 240)

clock = pygame.time.Clock()

FPS = 60

engine = GameEngine(WIDTH, HEIGHT)


def main():
    running = True

    while running:
        SCREEN.fill(SKY)

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

            else:
                engine.handle_event(event)

        if engine.show_menu:
            running = False
        else:
            engine.handle_input()
            engine.update()
            engine.render(SCREEN)

        pygame.display.flip()

        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()