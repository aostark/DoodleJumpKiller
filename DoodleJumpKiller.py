import pygame
import random
import os
from pygame import mixer
from SpriteSheet import SpriteSheet
from enemy import Enemy

mixer.init()
pygame.init()

screen_width = 400
screen_height = 600

# define colors
white = (255, 255, 255)
red = (200, 0, 0)
black = (0, 0, 0)
panel_color = (153, 217, 234)

# define fonts
font_small = pygame.font.SysFont("Lucida Sans", 20)
font_large = pygame.font.SysFont("Chiller", 80)

# create game window
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Doodle Jump Killer")

# set frame rate
clock = pygame.time.Clock()
FPS = 60

# load music and sounds
pygame.mixer.music.load("assets/music.mp3")
pygame.mixer.music.set_volume(0.05)
pygame.mixer.music.play(-1, 0.0)

jump_fx = pygame.mixer.Sound("assets/jump.mp3")
jump_fx.set_volume(0.05)

death_fx = pygame.mixer.Sound("assets/death.mp3")
death_fx.set_volume(0.03)

# game variables
gravity = 1  # define how fast the player will be moved down
max_platforms = 10
scroll_threshold = 200
scroll = 0
background_scroll = 0
game_over = False
score = 0
fade_counter = 0
if os.path.exists("score.txt"):
    with open("score.txt", "r") as file:
        high_score = int(file.read())
else:
    high_score = 0

# load images
player_img = pygame.image.load("assets/jump.png").convert_alpha()
background_img = pygame.image.load("assets/bg.png").convert_alpha()
platform_img = pygame.image.load("assets/wood.png").convert_alpha()
# bird sprite sheet
bird_img = pygame.image.load("assets/bird.png").convert_alpha()
bird_sheet = SpriteSheet(bird_img)


# function for outputting text onto the screen
def draw_text(text, font, text_color, x, y):
    img = font.render(text, True, text_color)  # gives you an image instead of the text
    screen.blit(img, (x, y))


# function for drawing info panel
def draw_score():
    pygame.draw.rect(screen, panel_color, (0, 0, screen_width, 30))
    pygame.draw.line(screen, white, (0, 30), (screen_width, 30), 1)
    draw_text("SCORE: " + str(score), font_small, white, 0, 0)


def draw_background(background_scroll):
    screen.blit(background_img, (0, 0 + background_scroll))
    screen.blit(background_img, (0, -600 + background_scroll))


# game classes
class Player:
    def __init__(self, x, y):
        self.image = pygame.transform.scale(player_img, (45, 45))
        self.width = 25
        self.height = 40
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.rect.center = (x, y)
        self.velocity_y = 0
        self.flip = False  # to flip the player 180 degrees when turning left or right

    def move(self):
        # reset variables
        scroll = 0
        delta_x = 0
        delta_y = 0
        # process key presses
        key = pygame.key.get_pressed()
        if key[pygame.K_a]:
            delta_x = -10
            self.flip = True
        if key[pygame.K_d]:
            delta_x = 10
            self.flip = False

        # gravity
        self.velocity_y += gravity  # player will fall down faster at every iteration
        delta_y += self.velocity_y

        # ensure player does not go off the edge of the screen
        if self.rect.left + delta_x < 0:
            delta_x = - self.rect.left  # left side border
        if self.rect.right + delta_x > screen_width:
            delta_x = screen_width - self.rect.right  # right side border

        #  check collision with platforms
        for platform in platform_group:
            # collision in y direction
            if platform.rect.colliderect(self.rect.x, self.rect.y + delta_y, self.width, self.height):
                # check if above th platform
                if self.rect.bottom < platform.rect.centery:
                    if self.velocity_y > 0:
                        self.rect.bottom = platform.rect.top
                        delta_y = 0
                        self.velocity_y = -20  # defines how hard the player bounces off the bottom of the screen
                        jump_fx.play()

        # check if the player has bounced to the top of the screen
        if self.rect.top <= scroll_threshold:
            # if player is jumping
            if self.velocity_y < 0:
                scroll = -delta_y

        # update rectangle position so the player can move
        self.rect.x += delta_x
        self.rect.y += delta_y + scroll

        # update mask
        self.mask = pygame.mask.from_surface(self.image)

        return scroll

    def draw(self):
        screen.blit(pygame.transform.flip(self.image, self.flip, False), (self.rect.x - 12, self.rect.y - 5))


class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, moving):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.transform.scale(platform_img, (width, 10))
        self.moving = moving
        self.move_counter = random.randint(0, 50)
        self.direction = random.choice([-1, 1])
        self.speed = random.randint(1, 2)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self, scroll):
        # move platforms side to side (for moving platforms only)
        if self.moving:
            self.move_counter += 1
            self.rect.x += self.direction * self.speed
        # change platform direction if it has moved fully or hit the wall
        if self.move_counter >= 100 or self.rect.left < 0 or self.rect.right > screen_width:
            self.direction *= -1
            self.move_counter = 0  # reset it to zero

        # update platform's vertical position
        self.rect.y += scroll

        # check if platform has gone off the screen
        if self.rect.top > screen_height:
            self.kill()


# player instance
jumpy = Player(screen_width // 2, screen_height - 150)

# create sprite groups
platform_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()

# create starting platform
platform = Platform(screen_width // 2 - 40, screen_height - 50, 80, False)
platform_group.add(platform)

# main game loop
run = True
while run:

    clock.tick(FPS)

    if not game_over:
        scroll = jumpy.move()

        # draw background
        background_scroll += scroll
        if background_scroll >= 600:
            background_scroll = 0
        draw_background(background_scroll)

        # generate platforms
        if len(platform_group) < max_platforms:
            platform_width = random.randint(50, 60)
            platform_x = random.randint(0, screen_width - platform_width)
            platform_y = platform.rect.y - random.randint(80, 120)
            platform_type = random.randint(1, 2)
            if platform_type == 1 and score > 500:
                platform_moving = True
            else:
                platform_moving = False
            platform = Platform(platform_x, platform_y, platform_width, platform_moving)
            platform_group.add(platform)

        # update platforms
        platform_group.update(scroll)

        # generate enemies
        if len(enemy_group) == 0 and score > 1500:
            enemy = Enemy(screen_width, 100, bird_sheet, 1)
            enemy_group.add(enemy)

        # update enemies
        enemy_group.update(scroll, screen_width)

        # update score
        if scroll > 0:
            score += scroll

        # draw line at previous high score
        draw_text("HIGH SCORE", font_small, red, screen_width - 130, score - high_score + scroll_threshold)
        pygame.draw.line(screen, red, (0, score - high_score + scroll_threshold),
                         (screen_width, score - high_score + scroll_threshold), 3)

        # draw sprites
        platform_group.draw(screen)
        enemy_group.draw(screen)
        jumpy.draw()

        # draw panel score
        draw_score()

        # check game over
        if jumpy.rect.top > screen_height:
            game_over = True
            death_fx.play()
        # check for collision with enemies
        if pygame.sprite.spritecollide(jumpy, enemy_group, False):
            if pygame.sprite.spritecollide(jumpy, enemy_group, False, pygame.sprite.collide_mask):
                game_over = True
                death_fx.play()
    else:
        if fade_counter < screen_width:
            fade_counter += 5
            for r in range(0, 6, 2):
                pygame.draw.rect(screen, black, (0, r * 100, fade_counter, 100))
                pygame.draw.rect(screen, black, (screen_width - fade_counter, (r + 1) * 100, screen_width, 100))
        else:
            draw_text("GAME OVER", font_large, red, 35, 150)
            draw_text("Score: " + str(score), font_small, white, 150, 300)
            draw_text("Press 'Space' to play again", font_small, white, 80, 350)

            # update high score
            if score > high_score:
                high_score = score
            with open("score.txt", "w") as file:
                file.write(str(high_score))

            key = pygame.key.get_pressed()
            if key[pygame.K_SPACE]:
                # reset variables
                game_over = False
                score = 0
                scroll = 0
                fade_counter = 0
                # reposition the player
                jumpy.rect.center = (screen_width // 2, screen_height - 150)
                # reset enemy
                enemy_group.empty()
                # reset platforms
                platform_group.empty()
                # create starting platform
                platform = Platform(screen_width // 2 - 40, screen_height - 50, 80, False)
                platform_group.add(platform)

    # event handler
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            # updates and saves high score if you close the game window
            if score > high_score:
                high_score = score
            with open("score.txt", "w") as file:
                file.write(str(high_score))
            run = False

    # update display window
    pygame.display.update()

pygame.quit()
