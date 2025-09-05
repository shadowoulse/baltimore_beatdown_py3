
import pygame
import random

pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Baltimore Beatdown")


# Always use city.png for background
try:
    city_bg = pygame.image.load("citytileset1/city.png")
    city_bg = pygame.transform.scale(city_bg, (WIDTH, HEIGHT))
except Exception:
    city_bg = None


# Load custom character sprite with aggressive transparency handling
try:
    # Load the original image
    raw_img = pygame.image.load("characters/blue_hoodie_guy.png")
    
    # Create a new surface with per-pixel alpha
    temp_surface = pygame.Surface(raw_img.get_size(), pygame.SRCALPHA, 32)
    temp_surface = temp_surface.convert_alpha()
    
    # Copy pixels, making white/light pixels transparent
    for x in range(raw_img.get_width()):
        for y in range(raw_img.get_height()):
            pixel = raw_img.get_at((x, y))
            r, g, b = pixel[:3]
            
            # If pixel is white or very light, make it transparent
            if r > 200 and g > 200 and b > 200:
                temp_surface.set_at((x, y), (r, g, b, 0))  # Transparent
            else:
                # Keep the original pixel with full opacity
                temp_surface.set_at((x, y), (r, g, b, 255))
    
    # Scale the processed image
    player_img = pygame.transform.smoothscale(temp_surface, (80, 80))
    
except Exception as e:
    print(f"Error loading sprite: {e}")
    player_img = None

# Load enemy cop sprite
try:
    raw_cop = pygame.image.load("characters/cop.png")
    cop_surface = pygame.Surface(raw_cop.get_size(), pygame.SRCALPHA, 32)
    cop_surface = cop_surface.convert_alpha()
    
    for x in range(raw_cop.get_width()):
        for y in range(raw_cop.get_height()):
            pixel = raw_cop.get_at((x, y))
            r, g, b = pixel[:3]
            if r > 200 and g > 200 and b > 200:
                cop_surface.set_at((x, y), (r, g, b, 0))
            else:
                cop_surface.set_at((x, y), (r, g, b, 255))
    
    # Scale with aspect ratio preservation
    original_w, original_h = cop_surface.get_size()
    scale = max(80/original_w, 80/original_h)
    new_w, new_h = int(original_w * scale), int(original_h * scale)
    enemy_img = pygame.transform.smoothscale(cop_surface, (new_w, new_h))
except Exception:
    enemy_img = None

# Load rat sprite
try:
    rat_img = pygame.image.load("animals/rat1.png")
    rat_img = pygame.transform.scale(rat_img, (20, 15))
except Exception:
    rat_img = None

player_rect = pygame.Rect(WIDTH//2-40, HEIGHT-130, 80, 80)
world_offset = 0
player_speed = 5
player_direction = 'right'
player_attacking = False
attack_cooldown = 0

ground_level = HEIGHT-130
jump_velocity = 0
gravity = 0.8
jump_strength = -15
is_jumping = False

enemy_size = 80
enemy_speed = 2
enemies = []
enemy_spawn_delay = 120
enemy_timer = 0

bullets = []
bullet_speed = 8
enemy_bullets = []

paused = False
score = 0
health = 100
strength = 1

items = []
item_spawn_timer = 0
item_spawn_delay = 300
damage_cooldown = 0

# Background rats
rats = [[100, HEIGHT-65], [300, HEIGHT-60]]
font = pygame.font.SysFont(None, 36)
clock = pygame.time.Clock()
running = True

def draw_background():
    if city_bg:
        # Draw repeating background for side scrolling
        bg_x = -(world_offset % WIDTH)
        screen.blit(city_bg, (bg_x, 0))
        screen.blit(city_bg, (bg_x + WIDTH, 0))
    else:
        screen.fill((60, 60, 100))
    
    # Draw grey street at bottom
    pygame.draw.rect(screen, (80, 80, 80), (0, HEIGHT-50, WIDTH, 50))

def draw_player(rect, direction, attacking):
    if player_img:
        # Flip sprite based on direction
        sprite = pygame.transform.flip(player_img, direction == 'left', False)
        # Anchor sprite to bottom of rect
        x_offset = (rect.width - sprite.get_width()) // 2
        y_offset = rect.height - sprite.get_height()
        screen.blit(sprite, (rect.x + x_offset, rect.y + y_offset))
    else:
        # Draw hoodie body
        pygame.draw.rect(screen, (60, 60, 60), rect, border_radius=12)
        pygame.draw.rect(screen, (30, 30, 80), (rect.x, rect.y, rect.width, rect.height//2), border_radius=12)
        # Draw head
        pygame.draw.circle(screen, (255,220,180), (rect.x+rect.width//2, rect.y+rect.height//2-10), 10)

def draw_enemy(rect, player_pos):
    if enemy_img:
        # Flip enemy to face player
        face_left = rect.centerx > player_pos[0]
        sprite = pygame.transform.flip(enemy_img, face_left, False)
        # Anchor sprite to bottom of rect
        x_offset = (rect.width - sprite.get_width()) // 2
        y_offset = rect.height - sprite.get_height()
        screen.blit(sprite, (rect.x + x_offset, rect.y + y_offset))
    else:
        pygame.draw.rect(screen, (180, 80, 80), rect, border_radius=12)
        pygame.draw.circle(screen, (80, 0, 0), (rect.x+rect.width//2, rect.y+rect.height//2-10), 10)

def show_score(score):
    score_font = pygame.font.SysFont(None, 48, bold=True)
    score_text = f"Score: {score}"
    score_surf = score_font.render(score_text, True, (255,255,255))
    screen.blit(score_surf, (10, 10))

def show_stats(health, strength):
    health_text = font.render(f"Health: {health}", True, (255, 0, 0))
    strength_text = font.render(f"Strength: {strength}", True, (0, 255, 0))
    screen.blit(health_text, (10, 60))
    screen.blit(strength_text, (10, 90))

def draw_item(pos, item_type):
    colors = {'weed': (0, 255, 0), 'needle': (200, 200, 200), 'beer': (139, 69, 19)}
    pygame.draw.circle(screen, colors[item_type], pos, 8)

while running:
    # Always redraw background before drawing anything else
    # Clean game loop: always clear screen and redraw background first
    screen.fill((0, 0, 0))
    draw_background()

    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                paused = not paused
            elif event.key == pygame.K_SPACE and attack_cooldown == 0 and not paused:
                bullet_x = player_rect.centerx
                bullet_y = player_rect.centery
                bullet_dir = 1 if player_direction == 'right' else -1
                bullets.append([bullet_x, bullet_y, bullet_dir])
                attack_cooldown = 10

    if not paused:
        # Handle movement and side scrolling
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and player_rect.x > 0:
            player_rect.x -= player_speed
            player_direction = 'left'
        if keys[pygame.K_RIGHT]:
            if player_rect.x < WIDTH - 200:  # Normal movement
                player_rect.x += player_speed
            else:  # Start scrolling when near right edge
                world_offset += player_speed
                # Move all game objects left
                for enemy_data in enemies:
                    enemy_data[0].x -= player_speed
                for item in items:
                    item[0] -= player_speed
                for bullet in bullets:
                    bullet[0] -= player_speed
                for bullet in enemy_bullets:
                    bullet[0] -= player_speed
                # Move rats with world
                for rat in rats:
                    rat[0] -= player_speed
            player_direction = 'right'
        if keys[pygame.K_UP] and not is_jumping:
            jump_velocity = jump_strength
            is_jumping = True
        
        # Handle jumping and gravity
        if is_jumping:
            player_rect.y += jump_velocity
            jump_velocity += gravity
            if player_rect.y >= ground_level:
                player_rect.y = ground_level
                is_jumping = False
                jump_velocity = 0

        # Attack cooldown
        if attack_cooldown > 0:
            attack_cooldown -= 1
        
        # Damage cooldown
        if damage_cooldown > 0:
            damage_cooldown -= 1

        # Update bullets
        for bullet in bullets[:]:
            bullet[0] += bullet[2] * bullet_speed
            if bullet[0] < 0 or bullet[0] > WIDTH:
                bullets.remove(bullet)
        
        # Update enemy bullets
        for bullet in enemy_bullets[:]:
            bullet[0] += bullet[2] * 4
            if bullet[0] < 0 or bullet[0] > WIDTH:
                enemy_bullets.remove(bullet)
            elif player_rect.collidepoint(bullet[0], bullet[1]) and damage_cooldown == 0:
                health -= 5
                damage_cooldown = 30
                enemy_bullets.remove(bullet)
                if health <= 0:
                    running = False
        
        # Spawn items
        item_spawn_timer += 1
        if item_spawn_timer >= item_spawn_delay:
            item_x = WIDTH + random.randint(50, 200)  # Spawn ahead of player
            item_y = random.randint(HEIGHT-230, HEIGHT-150)
            item_type = random.choice(['weed', 'needle', 'beer'])
            items.append([item_x, item_y, item_type])
            item_spawn_timer = 0

        # Enemy spawn
        enemy_timer += 1
        if enemy_timer >= enemy_spawn_delay:
            enemy_y = HEIGHT-130
            enemy_x = random.choice([WIDTH + 50, -enemy_size - 50])  # Spawn off-screen
            enemy_health = 1 + (score // 5)
            can_shoot = random.random() < 0.3
            shoot_timer = random.randint(20, 60)
            enemy_rect = pygame.Rect(enemy_x, enemy_y, enemy_size, enemy_size)
            enemies.append([enemy_rect, enemy_health, can_shoot, shoot_timer])
            enemy_timer = 0

        # Enemy movement and collision
        for enemy_data in enemies[:]:
            enemy_rect, enemy_health, can_shoot, shoot_timer = enemy_data
            if enemy_rect.x < player_rect.x:
                enemy_rect.x += enemy_speed
            elif enemy_rect.x > player_rect.x:
                enemy_rect.x -= enemy_speed
            
            # Enemy shooting
            if can_shoot:
                enemy_data[3] -= 1
                if enemy_data[3] <= 0:
                    bullet_dir = 1 if enemy_rect.centerx < player_rect.centerx else -1
                    enemy_bullets.append([enemy_rect.centerx, enemy_rect.centery, bullet_dir])
                    enemy_data[3] = random.randint(20, 60)
            
            # Enemy damage to player
            if enemy_rect.colliderect(player_rect) and damage_cooldown == 0:
                health -= 10
                damage_cooldown = 60
                if health <= 0:
                    running = False
            
            # Check bullet collisions
            for bullet in bullets[:]:
                if enemy_rect.collidepoint(bullet[0], bullet[1]):
                    enemy_data[1] -= strength
                    bullets.remove(bullet)
                    if enemy_data[1] <= 0:
                        enemies.remove(enemy_data)
                        score += strength
                    break
        
        # Item collection
        for item in items[:]:
            if player_rect.collidepoint(item[0], item[1]):
                if item[2] == 'weed':
                    strength += 1
                elif item[2] == 'needle':
                    strength += 2
                elif item[2] == 'beer':
                    health = min(100, health + 20)
                items.remove(item)

    # Draw everything
    draw_player(player_rect, player_direction, player_attacking)
    for enemy_data in enemies:
        enemy_rect, enemy_health, can_shoot, shoot_timer = enemy_data
        draw_enemy(enemy_rect, player_rect.center)
        # Draw health bar above enemy
        bar_width = 30
        bar_height = 4
        bar_x = enemy_rect.x + (enemy_rect.width - bar_width) // 2
        bar_y = enemy_rect.y - 10
        max_health = 1 + (score // 5)
        health_ratio = enemy_health / max_health
        pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y, bar_width * health_ratio, bar_height))
        # Mark shooting enemies
        if can_shoot:
            pygame.draw.circle(screen, (255, 255, 0), (enemy_rect.centerx, enemy_rect.y - 15), 3)
    
    # Draw bullets
    for bullet in bullets:
        pygame.draw.circle(screen, (255, 255, 0), (int(bullet[0]), int(bullet[1])), 3)
    
    # Draw enemy bullets
    for bullet in enemy_bullets:
        pygame.draw.circle(screen, (255, 0, 0), (int(bullet[0]), int(bullet[1])), 2)
    
    # Draw background rats
    for rat in rats:
        if -50 < rat[0] < WIDTH + 50:  # Only draw if on screen
            if rat_img:
                screen.blit(rat_img, (int(rat[0]), int(rat[1])))
            else:
                # Fallback: draw small brown circles if image fails
                pygame.draw.circle(screen, (139, 69, 19), (int(rat[0]), int(rat[1])), 8)
    
    # Draw items
    for item in items:
        draw_item((int(item[0]), int(item[1])), item[2])
    
    show_score(score)
    show_stats(health, strength)
    
    if paused:
        pause_text = font.render("PAUSED - Press P to continue", True, (255, 255, 255))
        screen.blit(pause_text, (WIDTH//2 - 150, HEIGHT//2))

    # Update display
    pygame.display.flip()
    clock.tick(60)
