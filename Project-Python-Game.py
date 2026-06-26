import pygame
import sys
import time

# --- CONSTANTS & CONFIGURATION ---
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 600
FPS = 60

COLOR_TEXT = (255, 255, 255)     
COLOR_ALERT = (255, 69, 0)       

LEFT_BANK_X = 250      
RIGHT_BANK_X = 650     
CHASM_START_X = 180   
CHASM_END_X = 780      

# --- 1. GAME ENTITY CLASS ---
class JungleEntity:
    def __init__(self, name, start_side, color, base_y, image_filename):
        self.name = name
        self.side = start_side  
        self.base_y = base_y
        self.x = LEFT_BANK_X if start_side == 'left' else RIGHT_BANK_X
        self.y = base_y
        self.is_on_jeep = False
        self.color = color
        
        try:
            raw_image = pygame.image.load(image_filename).convert_alpha()
            self.image = pygame.transform.scale(raw_image, (120, 120))
            self.has_image = True
        except Exception:
            self.has_image = False
            
    def update_position(self, jeep_side, jeep_x):
        offsets = {"Tiger": -200, "Bananas": -130, "Explorer": -60, "Monkey": 10}
        base_spacing = offsets.get(self.name, 0)

        if self.is_on_jeep:
            if self.name == "Explorer":
                self.x = jeep_x + 110  
                self.y = 445           
            else:
                self.x = jeep_x + 200  
                self.y = 445           
        else:
            if self.side == 'left':
                self.x = LEFT_BANK_X + base_spacing
            else:
                self.x = RIGHT_BANK_X + (base_spacing * -1) - 50
            self.y = 485
            
    def draw(self, screen):
        if self.has_image:
            screen.blit(self.image, (int(self.x - 60), int(self.y - 60)))
        else:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), 25)
            font = pygame.font.SysFont('Arial', 12, bold=True)
            text_surf = font.render(self.name[0:4], True, COLOR_TEXT)
            screen.blit(text_surf, (self.x - 13, self.y - 6))


# --- 2. VEHICLE CLASS ---
class RescueJeep:
    def __init__(self, image_filename=None):
        self.side = 'left'
        self.target_x = CHASM_START_X
        self.x = CHASM_START_X  
        self.y = 390
        self.width = 300       
        self.height = 150      
        self.speed = 8         
        self.passenger = None
        self.has_image = False

        if image_filename:
            try:
                raw_image = pygame.image.load(image_filename).convert_alpha()
                self.image = pygame.transform.scale(raw_image, (self.width, self.height))
                self.has_image = True
            except Exception:
                pass

    def move(self):
        self.target_x = CHASM_START_X if self.side == 'left' else CHASM_END_X - self.width
        if self.x < self.target_x:
            self.x = min(self.x + self.speed, self.target_x)
        elif self.x > self.target_x:
            self.x = max(self.x - self.speed, self.target_x)

    def is_moving(self):
        return self.x != self.target_x

    def draw(self, screen):
        if self.has_image:
            screen.blit(self.image, (int(self.x), int(self.y)))
        else:
            pygame.draw.rect(screen, (34, 139, 34), (self.x, self.y, self.width, self.height), border_radius=10)


# --- 3. GAME MANAGEMENT CLASS ---
class GameManager:
    def __init__(self):
        self.state = "MENU"  
        
        self.entities = {
            "Explorer": JungleEntity("Explorer", "left", (0, 128, 255), 485, "images/explorer.png"),
            "Tiger": JungleEntity("Tiger", "left", (255, 140, 0), 485, "images/tiger.png"),
            "Monkey": JungleEntity("Monkey", "left", (205, 133, 63), 485, "images/monkey.png"),
            "Bananas": JungleEntity("Bananas", "left", (255, 215, 0), 485, "images/banana.png")
        }
        self.jeep = RescueJeep("images/jeep.png")
        self.time_limit = 90  
        self.start_time = None  
        self.game_over = False
        self.win = False
        self.lose_reason = ""
        self.is_paused = False

        try:
            bg_image = pygame.image.load("images/background.png").convert()
            self.background = pygame.transform.scale(bg_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
            self.has_bg = True
        except Exception:
            self.has_bg = False

        # --- SAFE AUDIO SETUP ---
        self.has_sound = False
        try:
            pygame.mixer.init()
            self.snd_victory = pygame.mixer.Sound("sounds/victory.wav")
            self.snd_lose = pygame.mixer.Sound("sounds/lose.wav")
            self.has_sound = True
        except Exception as e:
            print(f"Warning: Sound Effects couldn't load (Skipping safely): {e}")

        try:
            pygame.mixer.music.load("sounds/forest.wav")
            pygame.mixer.music.play(-1)  
        except Exception as e:
            print(f"Warning: Background Music couldn't play (Skipping safely): {e}")

    def start_game(self):
        self.state = "PLAYING"
        self.start_time = time.time()

    def handle_click(self, pos):
        if self.state != "PLAYING" or self.is_paused or self.jeep.is_moving():
            return

        for name, ent in self.entities.items():
            dist = ((ent.x - pos[0])**2 + (ent.y - pos[1])**2)**0.5
            if dist <= 55:  
                self.toggle_boarding(ent)
                return

        jeep_rect = pygame.Rect(self.jeep.x, self.jeep.y, self.jeep.width, self.jeep.height)
        if jeep_rect.collidepoint(pos):
            self.cross_canyon()

    def toggle_boarding(self, ent):
        if ent.name == "Explorer":
            ent.is_on_jeep = not ent.is_on_jeep
            return

        if ent.is_on_jeep:
            ent.is_on_jeep = False
            ent.side = self.jeep.side
            self.jeep.passenger = None
        else:
            if ent.side == self.jeep.side and self.jeep.passenger is None and self.entities["Explorer"].side == self.jeep.side:
                ent.is_on_jeep = True
                self.jeep.passenger = ent

    def cross_canyon(self):
        if self.entities["Explorer"].is_on_jeep:
            self.jeep.side = 'right' if self.jeep.side == 'left' else 'left'
            self.entities["Explorer"].side = self.jeep.side

    def verify_rules(self):
        if self.state != "PLAYING":
            return

        elapsed = time.time() - self.start_time
        if self.time_limit - elapsed <= 0:
            self.state = "GAMEOVER"
            self.game_over = True
            self.lose_reason = "Time Ran Out! Night fell over the safari."
            try: pygame.mixer.music.stop()
            except: pass
            if self.has_sound: self.snd_lose.play()
            return

        pos_map = {}
        for name, ent in self.entities.items():
            pos_map[name] = "jeep" if ent.is_on_jeep else ent.side

        exp_loc = pos_map["Explorer"]

        if pos_map["Tiger"] == pos_map["Monkey"] and pos_map["Tiger"] != exp_loc and pos_map["Tiger"] != "jeep":
            self.state = "GAMEOVER"
            self.game_over = True
            self.lose_reason = "The Tiger attacked the Monkey!"
            try: pygame.mixer.music.stop()
            except: pass
            if self.has_sound: self.snd_lose.play()
        elif pos_map["Monkey"] == pos_map["Bananas"] and pos_map["Monkey"] != exp_loc and pos_map["Monkey"] != "jeep":
            self.state = "GAMEOVER"
            self.game_over = True
            self.lose_reason = "The Monkey ate all the Bananas!"
            try: pygame.mixer.music.stop()
            except: pass
            if self.has_sound: self.snd_lose.play()

        if all(ent.side == 'right' and not ent.is_on_jeep for ent in self.entities.values()):
            self.state = "GAMEOVER"
            self.game_over = True
            self.win = True
            try: pygame.mixer.music.stop()
            except: pass
            if self.has_sound: self.snd_victory.play()

    def update(self):
        if self.state == "PLAYING" and not self.is_paused:
            self.jeep.move()
            for ent in self.entities.values():
                ent.update_position(self.jeep.side, self.jeep.x)
            self.verify_rules()

    def draw(self, screen):
        if self.has_bg:
            screen.blit(self.background, (0, 0))
        else:
            screen.fill((30, 50, 30)) 
        
        self.jeep.draw(screen)
        for ent in self.entities.values():
            ent.draw(screen)

        font = pygame.font.SysFont('Arial', 24, bold=True)
        menu_font = pygame.font.SysFont('Arial', 20, bold=False)

        if self.state == "MENU":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            
            title = font.render("PIXEL SAFARI ADVENTURE", True, (255, 215, 0))
            rule1 = menu_font.render("1. Help the Explorer move everyone across the mud bank.", True, COLOR_TEXT)
            rule2 = menu_font.render("2. The jeep can only take the Explorer and ONE passenger.", True, COLOR_TEXT)
            rule3 = menu_font.render("3. Left unsupervised: Tiger attacks Monkey, Monkey eats Bananas!", True, COLOR_ALERT)
            prompt = font.render("Press 'SPACEBAR' to Start Rescue Mission", True, (0, 255, 128))
            exit_prompt = menu_font.render("Press 'ESC' to Exit Game", True, (200, 200, 200))

            screen.blit(title, (SCREEN_WIDTH // 2 - 140, 130))
            screen.blit(rule1, (SCREEN_WIDTH // 2 - 240, 210))
            screen.blit(rule2, (SCREEN_WIDTH // 2 - 240, 250))
            screen.blit(rule3, (SCREEN_WIDTH // 2 - 240, 290))
            screen.blit(prompt, (SCREEN_WIDTH // 2 - 210, 400))
            screen.blit(exit_prompt, (SCREEN_WIDTH // 2 - 100, 460))

        elif self.state == "PLAYING":
            elapsed = time.time() - self.start_time
            rem_time = max(0, int(self.time_limit - elapsed))
            
            timer_text = font.render(f"Safari Time Left: {rem_time}s", True, COLOR_TEXT)
            screen.blit(timer_text, (20, 20))

            if self.is_paused:
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 160))
                screen.blit(overlay, (0, 0))
                screen.blit(font.render("GAME PAUSED - Press 'P' to Resume", True, COLOR_TEXT), (SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT // 2))

        elif self.state == "GAMEOVER":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 210))
            screen.blit(overlay, (0, 0))
            
            if self.win:
                res_text = font.render("SUCCESS! Safe evacuation completed!", True, (0, 255, 128))
            else:
                res_text = font.render(f"MISSION FAILED: {self.lose_reason}", True, COLOR_ALERT)
                
            retry_text = font.render("Press 'R' to Restart  |  Press 'ESC' to Exit", True, COLOR_TEXT)
            screen.blit(res_text, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 20))
            screen.blit(retry_text, (SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT // 2 + 20))


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Pixel Safari Adventure")
    clock = pygame.time.Clock()
    manager = GameManager()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                manager.handle_click(event.pos)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:  
                    pygame.quit()
                    sys.exit()
                elif event.key == pygame.K_SPACE and manager.state == "MENU":
                    manager.start_game()
                elif event.key == pygame.K_r:
                    manager = GameManager()
                elif event.key == pygame.K_p and manager.state == "PLAYING":
                    manager.is_paused = not manager.is_paused

        manager.update()
        manager.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()