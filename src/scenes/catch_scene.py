import pygame as pg
import random
from src.scenes.scene import Scene
from src.utils import GameSettings
from src.core.services import scene_manager, input_manager, sound_manager
from src.sprites import Sprite, BackgroundSprite
from src.interface.components import Button
from typing import override

class CatchScene(Scene):
    background: BackgroundSprite
    player_info_panel: Sprite
    wild_info_panel: Sprite
    attack_button: Button
    catch_button: Button
    run_button: Button
    
    player_monster: dict
    wild_monster: dict
    current_turn: str
    battle_over: bool
    catch_success: bool
    result_message: str
    battle_log: str
    enemy_turn_timer: float
    result_timer: float
    game_manager: any
    
    player_sprite: pg.Surface | None
    wild_sprite: pg.Surface | None
    
    def __init__(self):
        super().__init__()
        
        self.background = BackgroundSprite("backgrounds/background1.png")
        self.player_info_panel = Sprite("UI/raw/UI_Flat_Banner03a.png", (300, 100))
        self.wild_info_panel = Sprite("UI/raw/UI_Flat_Banner03a.png", (300, 100))
        
        button_y = GameSettings.SCREEN_HEIGHT - 80
        self.attack_button = Button(
            "UI/raw/UI_Flat_Banner03a.png",
            "UI/raw/UI_Flat_Banner03a.png",
            150, button_y, 130, 50,
            self._player_attack
        )
        self.catch_button = Button(
            "UI/raw/UI_Flat_Banner03a.png",
            "UI/raw/UI_Flat_Banner03a.png",
            800, button_y, 130, 50,
            self._try_catch
        )
        self.run_button = Button(
            "UI/raw/UI_Flat_Banner03a.png",
            "UI/raw/UI_Flat_Banner03a.png",
            450, button_y, 130, 50,
            self._run_away
        )
        
        self.player_monster = None
        self.wild_monster = None
        self.current_turn = "player"
        self.battle_over = False
        self.catch_success = False
        self.result_message = ""
        self.battle_log = ""
        self.enemy_turn_timer = 0
        self.result_timer = 0
        self.game_manager = None
        
        self.player_sprite = None
        self.wild_sprite = None
    
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

    
    def setup_catch(self, game_manager):
        self.game_manager = game_manager
        
        if hasattr(game_manager, 'bag') and game_manager.bag._monsters_data:
            monsters = game_manager.bag._monsters_data
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
                self.player_monster = {
                    "name": "Pikachu",
                    "hp": 100,
                    "max_hp": 100,
                    "level": 25,
                    "sprite_path": "menu_sprites/menusprite1.png"
                }
        else:
            self.player_monster = {
                "name": "Pikachu",
                "hp": 100,
                "max_hp": 100,
                "level": 25,
                "sprite_path": "menu_sprites/menusprite1.png"
            }
        
        # 怪物list
        wild_monsters = [
            {"name": "Rattata", "hp": 40, "max_hp": 40, "level": 5, "sprite_path": "menu_sprites/menusprite1.png"},
            {"name": "Pidgey", "hp": 45, "max_hp": 45, "level": 6, "sprite_path": "menu_sprites/menusprite2.png"},
            {"name": "Caterpie", "hp": 35, "max_hp": 35, "level": 4, "sprite_path": "menu_sprites/menusprite3.png"},
            {"name": "Weedle", "hp": 38, "max_hp": 38, "level": 5, "sprite_path": "menu_sprites/menusprite4.png"},
        ]
        
        self.wild_monster = random.choice(wild_monsters).copy()
        
        # 載入怪物圖片
        self.player_sprite = self._load_sprite(
            self.player_monster.get('sprite_path'), 
            (150, 150)
        )
        self.wild_sprite = self._load_sprite(
            self.wild_monster.get('sprite_path'), 
            (150, 150)
        )
        
        self.current_turn = "player"
        self.battle_over = False
        self.catch_success = False
        self.result_message = ""
        self.battle_log = f"A wild {self.wild_monster['name']} appeared!"
        self.enemy_turn_timer = 0
        self.result_timer = 0
    
    @override
    def enter(self) -> None:
        sound_manager.play_bgm("RBY 103 Pallet Town.ogg")
    
    @override
    def exit(self) -> None:
        pass
    
    @override
    def update(self, dt: float) -> None:
        if self.battle_over:
            if self.catch_success:
                # 捕捉成功後自動返回
                self.result_timer += dt
                if self.result_timer >= 2.5:
                    scene_manager.change_scene("game")
            else:
                # 戰鬥結束要捕捉
                self.catch_button.update(dt)
            return
        
        if self.current_turn == "player":
            self.attack_button.update(dt)
            self.run_button.update(dt)
        
        elif self.current_turn == "enemy":
            self.enemy_turn_timer += dt
            if self.enemy_turn_timer >= 1.5:
                self.enemy_turn_timer = 0
                self._enemy_attack()
    
    def _player_attack(self):
        """玩家攻擊"""
        if self.current_turn != "player" or self.battle_over:
            return
        
        damage = random.randint(15, 25)
        self.wild_monster["hp"] -= damage
        if self.wild_monster["hp"] < 0:
            self.wild_monster["hp"] = 0
            
        self.battle_log = f"{self.player_monster['name']} attacks! Deals {damage} damage!"
        
        if self.wild_monster["hp"] <= 0:
            self.battle_over = True
            self.result_message = f"{self.wild_monster['name']} fainted! Catch it?"
            self.battle_log = self.result_message
        else:
            self.current_turn = "enemy"
            self.enemy_turn_timer = 0
    
    def _try_catch(self):
        """嘗試捕捉（只能在戰鬥勝利後使用）"""
        if not self.battle_over or self.catch_success:
            return
        
        # 贏了就能抓到
        self.catch_success = True
        self.result_message = f"Caught {self.wild_monster['name']}!"
        self.battle_log = self.result_message
        self.result_timer = 0
        
        if self.game_manager:
            # 恢復野生怪獸的HP再加入背包
            self.wild_monster["hp"] = self.wild_monster["max_hp"]
            self.game_manager.bag._monsters_data.append(self.wild_monster)
    
    def _run_away(self):
        scene_manager.change_scene("game")
    
    def _enemy_attack(self):
        """野生怪獸攻擊"""
        damage = random.randint(10, 20)
        self.player_monster["hp"] -= damage
        if self.player_monster["hp"] < 0:
            self.player_monster["hp"] = 0
            
        self.battle_log = f"{self.wild_monster['name']} attacks! Deals {damage} damage!"
        
        if self.player_monster["hp"] <= 0:
            self.battle_over = True
            self.result_message = "You blacked out!"
            self.battle_log = self.result_message
        else:
            self.current_turn = "player"
    
    @override
    def draw(self, screen: pg.Surface) -> None:
        self.background.draw(screen)
        
        font_name = pg.font.Font("assets/fonts/Minecraft.ttf", 24)
        font_hp = pg.font.Font("assets/fonts/Minecraft.ttf", 18)
        font_log = pg.font.Font("assets/fonts/Minecraft.ttf", 26)
        font_button = pg.font.Font("assets/fonts/Minecraft.ttf", 22)
        
        # 場上怪物圖片
        if self.wild_sprite:
            wild_sprite_x = GameSettings.SCREEN_WIDTH - 450
            wild_sprite_y = 150
            screen.blit(self.wild_sprite, (wild_sprite_x, wild_sprite_y))
        
        if self.player_sprite:
            player_sprite_x = 400
            player_sprite_y = GameSettings.SCREEN_HEIGHT - 380
            screen.blit(self.player_sprite, (player_sprite_x, player_sprite_y))
        
        # 怪物資訊卡
        wild_panel_x = GameSettings.SCREEN_WIDTH - 320
        wild_panel_y = 20
        screen.blit(self.wild_info_panel.image, (wild_panel_x, wild_panel_y))
        
        if self.wild_sprite:
            small_wild_sprite = pg.transform.scale(self.wild_sprite, (60, 60))
            screen.blit(small_wild_sprite, (wild_panel_x + 10, wild_panel_y + 20))
        
        wild_name = font_name.render(f"{self.wild_monster['name']}", True, (0, 0, 0))
        screen.blit(wild_name, (wild_panel_x + 80, wild_panel_y + 15))
        
        wild_level = font_name.render(f"Lv.{self.wild_monster['level']}", True, (0, 0, 0))
        screen.blit(wild_level, (wild_panel_x + 230, wild_panel_y + 15))
        
        # HP條
        hp_bar_x = wild_panel_x + 80
        hp_bar_y = wild_panel_y + 50
        hp_bar_width = 200
        hp_bar_height = 12
        
        pg.draw.rect(screen, (200, 50, 50), pg.Rect(hp_bar_x, hp_bar_y, hp_bar_width, hp_bar_height), border_radius=3)
        hp_percent = self.wild_monster["hp"] / self.wild_monster["max_hp"]
        if hp_percent > 0:
            pg.draw.rect(screen, (100, 200, 100), 
                        pg.Rect(hp_bar_x, hp_bar_y, int(hp_bar_width * hp_percent), hp_bar_height),
                        border_radius=3)
        
        wild_hp_text = font_hp.render(f"{self.wild_monster['hp']}/{self.wild_monster['max_hp']}", True, (0, 0, 0))
        screen.blit(wild_hp_text, (hp_bar_x + 60, hp_bar_y + 20))
        
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
        
        # 玩家HP條
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
        
        # 戰鬥訊息
        log_text = font_log.render(self.battle_log, True, (255, 255, 255))
        screen.blit(log_text, (30, action_panel_y + 20))
        
        # 按鈕
        if not self.battle_over and self.current_turn == "player":
            # 戰鬥中 Attack 和 Run
            self.attack_button.draw(screen)
            attack_text = font_button.render("Attack", True, (0, 0, 0))
            attack_text_rect = attack_text.get_rect(center=(215, GameSettings.SCREEN_HEIGHT - 55))
            screen.blit(attack_text, attack_text_rect)
            
            self.run_button.draw(screen)
            run_text = font_button.render("Run", True, (0, 0, 0))
            run_text_rect = run_text.get_rect(center=(515, GameSettings.SCREEN_HEIGHT - 55))
            screen.blit(run_text, run_text_rect)
        
        elif self.battle_over and not self.catch_success:
            # 贏了 Catch
            self.catch_button.draw(screen)
            catch_text = font_button.render("Catch", True, (0, 0, 0))
            catch_text_rect = catch_text.get_rect(center=(865, GameSettings.SCREEN_HEIGHT - 55))
            screen.blit(catch_text, catch_text_rect)
        
        # 結果訊息
        if self.battle_over:
            result_color = (0, 255, 0) if self.catch_success else (255, 100, 100)
            result_text = font_log.render(self.result_message, True, result_color)
            screen.blit(result_text, (200, GameSettings.SCREEN_HEIGHT - 60))