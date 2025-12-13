import pygame as pg
import random
from src.scenes.scene import Scene
from src.utils import GameSettings
from src.core.services import scene_manager, input_manager, sound_manager
from src.sprites import Sprite, BackgroundSprite
from src.interface.components import Button
from typing import override

class BattleScene(Scene):
    background: BackgroundSprite
    player_info_panel: Sprite
    enemy_info_panel: Sprite
    attack_button: Button
    run_button: Button
    
    player_monster: dict
    enemy_monster: dict
    current_turn: str
    battle_over: bool
    winner: str
    battle_log: str
    enemy_turn_timer: float
    
    player_sprite: pg.Surface | None
    enemy_sprite: pg.Surface | None
    
    def __init__(self):
        super().__init__()
        
        self.background = BackgroundSprite("backgrounds/background1.png")
        self.player_info_panel = Sprite("UI/raw/UI_Flat_Banner03a.png", (300, 100))
        self.enemy_info_panel = Sprite("UI/raw/UI_Flat_Banner03a.png", (300, 100))
        
        button_y = GameSettings.SCREEN_HEIGHT - 80
        self.attack_button = Button(
            "UI/raw/UI_Flat_Banner03a.png",
            "UI/raw/UI_Flat_Banner03a.png",
            250, button_y, 150, 50,
            self._player_attack
        )
        self.run_button = Button(
            "UI/raw/UI_Flat_Banner03a.png",
            "UI/raw/UI_Flat_Banner03a.png",
            450, button_y, 150, 50,
            self._player_run
        )
        
        self.player_monster = None
        self.enemy_monster = None
        self.current_turn = "player"
        self.battle_over = False
        self.winner = ""
        self.battle_log = ""
        self.enemy_turn_timer = 0
        
        self.player_sprite = None
        self.enemy_sprite = None
    
    def _load_sprite(self, sprite_path: str, size: tuple) -> pg.Surface | None:
        if not sprite_path:
            return None

        path = f"assets/images/{sprite_path}"

        try:
            sprite = pg.image.load(path)
            return pg.transform.scale(sprite, size)
        except Exception as e:
            print(f"[Sprite Load Error] Cannot load: {path}, error: {e}")
            return None

    
    def setup_battle(self, player, enemy):
        # 從背包隨機派出一隻
        if hasattr(player, 'game_manager') and player.game_manager.bag._monsters_data:
            monsters = player.game_manager.bag._monsters_data
            if monsters:
                selected_monster = random.choice(monsters)
                
                if isinstance(selected_monster, dict):
                    self.player_monster = selected_monster.copy()
                else:
                    self.player_monster = {
                        "name": getattr(selected_monster, 'name', 'Pokemon'),
                        "hp": getattr(selected_monster, 'hp', 100),
                        "max_hp": getattr(selected_monster, 'max_hp', 100),
                        "level": getattr(selected_monster, 'level', 1),
                        "sprite_path": getattr(selected_monster, 'sprite_path', None)
                    }
            else:
                # 沒怪獸就借一隻來用
                self.player_monster = {
                    "name": "Pikachu",
                    "hp": 100,
                    "max_hp": 100,
                    "level": 25,
                    "sprite_path": "menu_sprites/menusprite1.png"
                }
        else:
            # 沒背包也借啦
            self.player_monster = {
                "name": "Pikachu",
                "hp": 100,
                "max_hp": 100,
                "level": 25,
                "sprite_path": "menu_sprites/menusprite1.png"
            }
        
        # 怪物list
        wild_monsters = [
            {"name": "Rattata", "hp": 400, "max_hp": 400, "level": 25, "sprite_path": "menu_sprites/menusprite1.png"},
            {"name": "Pidgey", "hp": 45, "max_hp": 45, "level": 6, "sprite_path": "menu_sprites/menusprite2.png"},
            {"name": "Caterpie", "hp": 35, "max_hp": 35, "level": 4, "sprite_path": "menu_sprites/menusprite3.png"},
            {"name": "Weedle", "hp": 38, "max_hp": 38, "level": 5, "sprite_path": "menu_sprites/menusprite4.png"},
        ]
        self.enemy_monster = random.choice(wild_monsters).copy()
        
        # 載入怪物圖片
        self.player_sprite = self._load_sprite(
            self.player_monster.get('sprite_path'), 
            (150, 150)
        )
        self.enemy_sprite = self._load_sprite(
            self.enemy_monster.get('sprite_path'), 
            (150, 150)
        )
        
        self.current_turn = "player"
        self.battle_over = False
        self.winner = ""
        self.battle_log = f"What will {self.player_monster['name']} do?"
        self.enemy_turn_timer = 0
    
    @override
    def enter(self) -> None:
        sound_manager.play_bgm("RBY 103 Pallet Town.ogg")
    
    @override
    def exit(self) -> None:
        pass
    
    @override
    def update(self, dt: float) -> None:
        if self.battle_over:
            if input_manager.key_pressed(pg.K_RETURN):
                scene_manager.change_scene("game")
            return
        
        if self.current_turn == "player":
            self.attack_button.update(dt)
            self.run_button.update(dt)
        
        elif self.current_turn == "enemy":
            self.enemy_turn_timer += dt
            if self.enemy_turn_timer >= 1.0:
                self.enemy_turn_timer = 0
                self._enemy_attack()
    
    def _player_attack(self):
        # 玩家攻擊
        if self.current_turn != "player" or self.battle_over:
            return
        
        damage = 20
        self.enemy_monster["hp"] -= damage
        self.battle_log = f"{self.player_monster['name']} attacks! Deals {damage} damage!"
        
        if self.enemy_monster["hp"] <= 0:
            self.enemy_monster["hp"] = 0
            self.battle_over = True
            self.winner = "player"
            self.battle_log = "You Win!"
        else:
            self.current_turn = "enemy"
            self.enemy_turn_timer = 0
    
    def _player_run(self):
        scene_manager.change_scene("game")
    
    def _enemy_attack(self):
        """敵人攻擊"""
        damage = 15
        self.player_monster["hp"] -= damage
        self.battle_log = f"{self.enemy_monster['name']} attacks! Deals {damage} damage!"
        
        if self.player_monster["hp"] <= 0:
            self.player_monster["hp"] = 0
            self.battle_over = True
            self.winner = "enemy"
            self.battle_log = "You Lose!"
        else:
            self.current_turn = "player"
            self.battle_log = f"What will {self.player_monster['name']} do?"
    
    @override
    def draw(self, screen: pg.Surface) -> None:
        self.background.draw(screen)
        
        font_name = pg.font.Font("assets/fonts/Minecraft.ttf", 24)
        font_hp = pg.font.Font("assets/fonts/Minecraft.ttf", 18)
        font_log = pg.font.Font("assets/fonts/Minecraft.ttf", 26)
        font_button = pg.font.Font("assets/fonts/Minecraft.ttf", 28)
        
        # 場上怪物圖片
        if self.enemy_sprite:
            enemy_sprite_x = GameSettings.SCREEN_WIDTH - 450
            enemy_sprite_y = 150
            screen.blit(self.enemy_sprite, (enemy_sprite_x, enemy_sprite_y))
        
        if self.player_sprite:
            player_sprite_x = 400
            player_sprite_y = GameSettings.SCREEN_HEIGHT - 380
            screen.blit(self.player_sprite, (player_sprite_x, player_sprite_y))
        
        # 敵人資訊卡
        enemy_panel_x = GameSettings.SCREEN_WIDTH - 320
        enemy_panel_y = 20
        screen.blit(self.enemy_info_panel.image, (enemy_panel_x, enemy_panel_y))
        
        if self.enemy_sprite:
            small_enemy_sprite = pg.transform.scale(self.enemy_sprite, (60, 60))
            screen.blit(small_enemy_sprite, (enemy_panel_x + 10, enemy_panel_y + 20))
        
        enemy_name = font_name.render(f"{self.enemy_monster['name']}", True, (0, 0, 0))
        screen.blit(enemy_name, (enemy_panel_x + 80, enemy_panel_y + 15))
        
        enemy_level = font_name.render(f"Lv.{self.enemy_monster['level']}", True, (0, 0, 0))
        screen.blit(enemy_level, (enemy_panel_x + 230, enemy_panel_y + 15))
        
        hp_bar_x = enemy_panel_x + 80
        hp_bar_y = enemy_panel_y + 50
        hp_bar_width = 200
        hp_bar_height = 12
        
        pg.draw.rect(screen, (200, 50, 50), pg.Rect(hp_bar_x, hp_bar_y, hp_bar_width, hp_bar_height), border_radius=3)
        hp_percent = self.enemy_monster["hp"] / self.enemy_monster["max_hp"]
        if hp_percent > 0:
            pg.draw.rect(screen, (100, 200, 100), 
                        pg.Rect(hp_bar_x, hp_bar_y, int(hp_bar_width * hp_percent), hp_bar_height),
                        border_radius=3)
        
        enemy_hp_text = font_hp.render(f"{self.enemy_monster['hp']}/{self.enemy_monster['max_hp']}", True, (0, 0, 0))
        screen.blit(enemy_hp_text, (hp_bar_x + 60, hp_bar_y + 20))
        
        # 玩家資訊卡
        player_panel_x = 20
        player_panel_y = GameSettings.SCREEN_HEIGHT - 250
        screen.blit(self.player_info_panel.image, (player_panel_x, player_panel_y))
        
        if self.player_sprite:
            small_player_sprite = pg.transform.scale(self.player_sprite, (60, 60))
            screen.blit(small_player_sprite, (player_panel_x + 10, player_panel_y + 20))
        
        player_name = font_name.render(f"{self.player_monster['name']}", True, (0, 0, 0))
        screen.blit(player_name, (player_panel_x + 80, player_panel_y + 15))
        
        player_level = font_name.render(f"Lv.{self.player_monster['level']}", True, (0, 0, 0))
        screen.blit(player_level, (player_panel_x + 230, player_panel_y + 15))
        
        hp_bar_x = player_panel_x + 80
        hp_bar_y = player_panel_y + 50
        
        pg.draw.rect(screen, (200, 50, 50), pg.Rect(hp_bar_x, hp_bar_y, hp_bar_width, hp_bar_height), border_radius=3)
        hp_percent = self.player_monster["hp"] / self.player_monster["max_hp"]
        if hp_percent > 0:
            pg.draw.rect(screen, (100, 200, 100), 
                        pg.Rect(hp_bar_x, hp_bar_y, int(hp_bar_width * hp_percent), hp_bar_height),
                        border_radius=3)
        
        player_hp_text = font_hp.render(f"{self.player_monster['hp']}/{self.player_monster['max_hp']}", True, (0, 0, 0))
        screen.blit(player_hp_text, (hp_bar_x + 60, hp_bar_y + 20))
        
        # 底部黑色
        action_panel_height = 140
        action_panel_y = GameSettings.SCREEN_HEIGHT - action_panel_height
        pg.draw.rect(screen, (30, 30, 30), 
                    pg.Rect(0, action_panel_y, GameSettings.SCREEN_WIDTH, action_panel_height))
        
        log_text = font_log.render(self.battle_log, True, (255, 255, 255))
        screen.blit(log_text, (30, action_panel_y + 20))
        
        if not self.battle_over and self.current_turn == "player":
            self.attack_button.draw(screen)
            attack_text = font_button.render("Attack", True, (0, 0, 0))
            attack_text_rect = attack_text.get_rect(center=(325, GameSettings.SCREEN_HEIGHT - 55))
            screen.blit(attack_text, attack_text_rect)
            
            self.run_button.draw(screen)
            run_text = font_button.render("Run", True, (0, 0, 0))
            run_text_rect = run_text.get_rect(center=(525, GameSettings.SCREEN_HEIGHT - 55))
            screen.blit(run_text, run_text_rect)
        
        if self.battle_over:
            result_text = font_log.render("Press ENTER to continue", True, (255, 255, 0))
            screen.blit(result_text, (200, GameSettings.SCREEN_HEIGHT - 60))