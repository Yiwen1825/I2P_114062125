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
    potion_button: Button
    switch_button: Button
    
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
    
    # 戰鬥數值
    player_base_atk: int
    player_atk_buff: int
    wild_base_atk: int
    wild_atk_debuff: int
    
    # 選單狀態
    showing_potion_menu: bool
    showing_switch_menu: bool
    menu_selection: int
    
    def __init__(self):
        super().__init__()
        
        self.background = BackgroundSprite("backgrounds/background1.png")
        self.player_info_panel = Sprite("UI/raw/UI_Flat_Banner03a.png", (300, 100))
        self.wild_info_panel = Sprite("UI/raw/UI_Flat_Banner03a.png", (300, 100))
        
        button_y = GameSettings.SCREEN_HEIGHT - 80
        button_width = 120
        button_spacing = 15
        start_x = 50
        
        self.attack_button = Button(
            "UI/raw/UI_Flat_Banner03a.png",
            "UI/raw/UI_Flat_Banner03a.png",
            start_x, button_y, button_width, 50,
            self._player_attack
        )
        self.switch_button = Button(
            "UI/raw/UI_Flat_Banner03a.png",
            "UI/raw/UI_Flat_Banner03a.png",
            start_x + (button_width + button_spacing) * 1, button_y, button_width, 50,
            self._show_switch_menu
        )
        self.potion_button = Button(
            "UI/raw/UI_Flat_Banner03a.png",
            "UI/raw/UI_Flat_Banner03a.png",
            start_x + (button_width + button_spacing) * 2, button_y, button_width, 50,
            self._show_potion_menu
        )
        self.run_button = Button(
            "UI/raw/UI_Flat_Banner03a.png",
            "UI/raw/UI_Flat_Banner03a.png",
            start_x + (button_width + button_spacing) * 3, button_y, button_width, 50,
            self._run_away
        )
        self.catch_button = Button(
            "UI/raw/UI_Flat_Banner03a.png",
            "UI/raw/UI_Flat_Banner03a.png",
            start_x + (button_width + button_spacing) * 4, button_y, button_width, 50,
            self._try_catch
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
        
        # 初始化戰鬥數值
        self.player_base_atk = 20
        self.player_atk_buff = 0
        self.wild_base_atk = 10
        self.wild_atk_debuff = 0
        
        # 初始化選單
        self.showing_potion_menu = False
        self.showing_switch_menu = False
        self.menu_selection = 0
    
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
        
        # 從背包隨機派出一隻
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
                        "atk": getattr(selected_monster, 'atk', 20),
                        "sprite_path": getattr(selected_monster, 'sprite_path', None)
                    }
            else:
                self.player_monster = {
                    "name": "Pikachu",
                    "hp": 100,
                    "max_hp": 100,
                    "level": 25,
                    "atk": 15,
                    "sprite_path": "menu_sprites/menusprite1.png"
                }
        else:
            self.player_monster = {
                "name": "Pikachu",
                "hp": 100,
                "max_hp": 100,
                "level": 25,
                "atk": 15,
                "sprite_path": "menu_sprites/menusprite1.png"
            }
        
        # 野生怪物list
        wild_monsters = [
            {"name": "Rattata", "hp": 40, "max_hp": 40, "level": 5, "atk": 8, "sprite_path": "menu_sprites/menusprite1.png"},
            {"name": "Pidgey", "hp": 45, "max_hp": 45, "level": 6, "atk": 9, "sprite_path": "menu_sprites/menusprite2.png"},
            {"name": "Caterpie", "hp": 35, "max_hp": 35, "level": 4, "atk": 6, "sprite_path": "menu_sprites/menusprite3.png"},
            {"name": "Weedle", "hp": 38, "max_hp": 38, "level": 5, "atk": 7, "sprite_path": "menu_sprites/menusprite4.png"},
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
        
        # 初始化戰鬥數值
        self.player_base_atk = self.player_monster.get('atk', 20)
        self.player_atk_buff = 0
        self.wild_base_atk = self.wild_monster.get('atk', 10)
        self.wild_atk_debuff = 0
        
        # 重置選單
        self.showing_potion_menu = False
        self.showing_switch_menu = False
        self.menu_selection = 0
    
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
        
        # 處理選單
        if self.showing_potion_menu or self.showing_switch_menu:
            self._handle_menu_input()
            return
        
        if self.current_turn == "player":
            self.attack_button.update(dt)
            self.switch_button.update(dt)
            self.potion_button.update(dt)
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
        
        # 使用基礎攻擊力 + buff
        damage = self.player_base_atk + self.player_atk_buff
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
        """嘗試捕捉（需要消耗 Pokeball）"""
        if not self.battle_over or self.catch_success:
            return
        
        # 檢查是否有 Pokeball
        has_pokeball = False
        if self.game_manager and self.game_manager.bag._items_data:
            for item in self.game_manager.bag._items_data:
                if isinstance(item, dict):
                    if item.get('name') == 'Pokeball' and item.get('count', 0) > 0:
                        has_pokeball = True
                        item['count'] -= 1  # 消耗一個 Pokeball
                        break
                else:
                    if getattr(item, 'name', '') == 'Pokeball' and getattr(item, 'count', 0) > 0:
                        has_pokeball = True
                        item.count -= 1  # 消耗一個 Pokeball
                        break
        
        if not has_pokeball:
            self.battle_log = "You don't have any Pokeballs!"
            return
        
        # 捕捉成功
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
    
    def _handle_menu_input(self):
        """處理選單輸入"""
        if self.showing_switch_menu:
            available_monsters = self._get_available_monsters()
            max_selection = len(available_monsters)
        elif self.showing_potion_menu:
            available_potions = self._get_available_potions()
            max_selection = len(available_potions)
        else:
            return
        
        # 上下鍵選擇
        if input_manager.key_pressed(pg.K_UP) or input_manager.key_pressed(pg.K_w):
            self.menu_selection = (self.menu_selection - 1) % max_selection
        elif input_manager.key_pressed(pg.K_DOWN) or input_manager.key_pressed(pg.K_s):
            self.menu_selection = (self.menu_selection + 1) % max_selection
        
        # 確認選擇
        if input_manager.key_pressed(pg.K_RETURN) or input_manager.key_pressed(pg.K_SPACE):
            if self.showing_switch_menu:
                self._switch_monster(self.menu_selection)
            elif self.showing_potion_menu:
                self._use_potion(self.menu_selection)
        
        # 取消
        if input_manager.key_pressed(pg.K_ESCAPE):
            self.showing_switch_menu = False
            self.showing_potion_menu = False
            self.menu_selection = 0
            self.battle_log = f"What will {self.player_monster['name']} do?"
    
    def _show_switch_menu(self):
        """顯示切換怪物選單"""
        if self.current_turn != "player" or self.battle_over:
            return
        
        available_monsters = self._get_available_monsters()
        if not available_monsters:
            self.battle_log = "No other monsters available!"
            return
        
        self.showing_switch_menu = True
        self.menu_selection = 0
        self.battle_log = "Choose a monster to switch in:"
    
    def _show_potion_menu(self):
        """顯示藥水選單"""
        if self.current_turn != "player" or self.battle_over:
            return
        
        available_potions = self._get_available_potions()
        if not available_potions:
            self.battle_log = "No potions available!"
            return
        
        self.showing_potion_menu = True
        self.menu_selection = 0
        self.battle_log = "Choose a potion to use:"
    
    def _get_available_monsters(self) -> list:
        """取得可用的怪物列表 (排除當前怪物和已倒下的)"""
        if not self.game_manager or not self.game_manager.bag._monsters_data:
            return []
        
        available = []
        for monster in self.game_manager.bag._monsters_data:
            if isinstance(monster, dict):
                if (monster.get('name') != self.player_monster['name'] and 
                    monster.get('hp', 0) > 0):
                    available.append(monster)
            else:
                name = getattr(monster, 'name', '')
                hp = getattr(monster, 'hp', 0)
                if name != self.player_monster['name'] and hp > 0:
                    available.append({
                        "name": name,
                        "hp": hp,
                        "max_hp": getattr(monster, 'max_hp', 100),
                        "level": getattr(monster, 'level', 1),
                        "atk": getattr(monster, 'atk', 20),
                        "sprite_path": getattr(monster, 'sprite_path', None)
                    })
        
        return available
    
    def _get_available_potions(self) -> list:
        """取得可用的藥水列表"""
        if not self.game_manager or not self.game_manager.bag._items_data:
            return []
        
        potions = []
        for item in self.game_manager.bag._items_data:
            if isinstance(item, dict):
                name = item.get('name', '')
                count = item.get('count', 0)
                if 'Potion' in name:
                    if count > 0:
                        if name == "Potion":
                            description = "Restores 20 HP"
                            effect_type = "heal"
                            effect_value = 20
                        elif name == "Atk_Potion":
                            description = "+5 Attack"
                            effect_type = "atk_buff"
                            effect_value = 5
                        elif name == "Def_Potion":
                            description = "The opponent loses 1 attack"
                            effect_type = "atk_debuff"
                            effect_value = 1
                        else:
                            continue
                        
                        potions.append({
                            "name": name,
                            "description": description,
                            "count": count,
                            "sprite_path": item.get('sprite_path', ''),
                            "effect_type": effect_type,
                            "effect_value": effect_value
                        })
        
        return potions
    
    def _switch_monster(self, index: int):
        """切換怪物"""
        available_monsters = self._get_available_monsters()
        if index >= len(available_monsters):
            return
        
        selected_monster = available_monsters[index]
        old_name = self.player_monster['name']
        
        if isinstance(selected_monster, dict):
            self.player_monster = selected_monster.copy()
        else:
            self.player_monster = selected_monster
        
        self.player_sprite = self._load_sprite(
            self.player_monster.get('sprite_path'), 
            (150, 150)
        )
        
        # 更新基礎攻擊力和重置 buff
        self.player_base_atk = self.player_monster.get('atk', 20)
        self.player_atk_buff = 0
        
        self.battle_log = f"Come back {old_name}! Go {self.player_monster['name']}!"
        
        self.showing_switch_menu = False
        self.menu_selection = 0
        self.current_turn = "enemy"
        self.enemy_turn_timer = 0
    
    def _use_potion(self, index: int):
        """使用藥水"""
        available_potions = self._get_available_potions()
        if index >= len(available_potions):
            return
        
        potion = available_potions[index]
        name = potion['name']
        effect_type = potion['effect_type']
        effect_value = potion['effect_value']
        
        # 根據藥水類型執行不同效果
        if name == "Potion":
            # 恢復 HP
            old_hp = self.player_monster['hp']
            self.player_monster['hp'] = min(
                self.player_monster['hp'] + effect_value,
                self.player_monster['max_hp']
            )
            actual_heal = self.player_monster['hp'] - old_hp
            self.battle_log = f"Used {name}! {self.player_monster['name']} recovered {actual_heal} HP!"
            next_turn_is_enemy = True
        
        elif name == "Atk_Potion":
            # 增加攻擊力
            self.player_atk_buff += effect_value
            self.battle_log = f"Used {name}! {self.player_monster['name']}'s attack increased by {effect_value}!"
            next_turn_is_enemy = True
        
        elif name == "Def_Potion":
            # 減少敵人攻擊力
            self.wild_atk_debuff += effect_value
            self.battle_log = f"Used {name}! {self.wild_monster['name']}'s attack decreased by {effect_value}!"
            next_turn_is_enemy = False  # Def_Potion 不會失去回合!
        
        else:
            # 預設當作治療藥水
            old_hp = self.player_monster['hp']
            self.player_monster['hp'] = min(
                self.player_monster['hp'] + effect_value,
                self.player_monster['max_hp']
            )
            actual_heal = self.player_monster['hp'] - old_hp
            self.battle_log = f"Used {name}! {self.player_monster['name']} recovered {actual_heal} HP!"
            next_turn_is_enemy = True
        
        # 減少藥水數量
        if self.game_manager and self.game_manager.bag._items_data:
            for item in self.game_manager.bag._items_data:
                if isinstance(item, dict):
                    if item.get('name') == name:
                        item['count'] -= 1
                        break
        
        # 關閉選單
        self.showing_potion_menu = False
        self.menu_selection = 0
        
        # 根據藥水類型決定下一回合
        if next_turn_is_enemy:
            self.current_turn = "enemy"
            self.enemy_turn_timer = 0
        else:
            # Def_Potion: 保持玩家回合
            self.current_turn = "player"
            self.battle_log += " Your turn again!"
    
    def _enemy_attack(self):
        """野生怪獸攻擊"""
        # 使用基礎攻擊力 - debuff (最少 1 點傷害)
        damage = max(1, self.wild_base_atk - self.wild_atk_debuff)
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
        font_menu = pg.font.Font("assets/fonts/Minecraft.ttf", 20)
        
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
        
        # 底部黑色面板
        action_panel_height = 140
        action_panel_y = GameSettings.SCREEN_HEIGHT - action_panel_height
        pg.draw.rect(screen, (30, 30, 30), 
                    pg.Rect(0, action_panel_y, GameSettings.SCREEN_WIDTH, action_panel_height))
        
        # 戰鬥訊息
        log_text = font_log.render(self.battle_log, True, (255, 255, 255))
        screen.blit(log_text, (30, action_panel_y + 20))
        
        # 繪製選單或按鈕
        if self.showing_switch_menu:
            self._draw_switch_menu(screen, font_menu)
        elif self.showing_potion_menu:
            self._draw_potion_menu(screen, font_menu)
        elif not self.battle_over and self.current_turn == "player":
            # 戰鬥中: Attack, Switch, Potion, Run
            self.attack_button.draw(screen)
            attack_text = font_button.render("Attack", True, (0, 0, 0))
            attack_text_rect = attack_text.get_rect(center=(110, GameSettings.SCREEN_HEIGHT - 55))
            screen.blit(attack_text, attack_text_rect)
            
            self.switch_button.draw(screen)
            switch_text = font_button.render("Switch", True, (0, 0, 0))
            switch_text_rect = switch_text.get_rect(center=(245, GameSettings.SCREEN_HEIGHT - 55))
            screen.blit(switch_text, switch_text_rect)
            
            self.potion_button.draw(screen)
            potion_text = font_button.render("Potion", True, (0, 0, 0))
            potion_text_rect = potion_text.get_rect(center=(380, GameSettings.SCREEN_HEIGHT - 55))
            screen.blit(potion_text, potion_text_rect)
            
            self.run_button.draw(screen)
            run_text = font_button.render("Run", True, (0, 0, 0))
            run_text_rect = run_text.get_rect(center=(515, GameSettings.SCREEN_HEIGHT - 55))
            screen.blit(run_text, run_text_rect)
        
        elif self.battle_over and not self.catch_success:
            # 贏了顯示 Catch 按鈕
            self.catch_button.draw(screen)
            catch_text = font_button.render("Catch", True, (0, 0, 0))
            catch_text_rect = catch_text.get_rect(center=(725, GameSettings.SCREEN_HEIGHT - 55))
            screen.blit(catch_text, catch_text_rect)
        
        # 結果訊息
        if self.battle_over:
            result_color = (0, 255, 0) if self.catch_success else (255, 100, 100)
            result_text = font_log.render(self.result_message, True, result_color)
            screen.blit(result_text, (200, GameSettings.SCREEN_HEIGHT - 60))
    
    def _draw_switch_menu(self, screen: pg.Surface, font: pg.font.Font):
        """繪製切換怪物選單"""
        available_monsters = self._get_available_monsters()
        
        # 選單背景
        menu_width = 400
        menu_height = min(300, 60 + len(available_monsters) * 50)
        menu_x = (GameSettings.SCREEN_WIDTH - menu_width) // 2
        menu_y = GameSettings.SCREEN_HEIGHT - 300
        
        # 半透明黑色背景
        menu_bg = pg.Surface((menu_width, menu_height))
        menu_bg.set_alpha(230)
        menu_bg.fill((40, 40, 40))
        screen.blit(menu_bg, (menu_x, menu_y))
        
        # 邊框
        pg.draw.rect(screen, (255, 255, 255), 
                    pg.Rect(menu_x, menu_y, menu_width, menu_height), 3, border_radius=5)
        
        # 繪製怪物選項
        for i, monster in enumerate(available_monsters):
            y = menu_y + 20 + i * 50
            
            # 選中的項目高亮
            if i == self.menu_selection:
                highlight_rect = pg.Rect(menu_x + 10, y, menu_width - 20, 45)
                pg.draw.rect(screen, (100, 100, 150), highlight_rect, border_radius=3)
            
            # 怪物名稱和 HP
            name = monster.get('name', 'Unknown')
            hp = monster.get('hp', 0)
            max_hp = monster.get('max_hp', 100)
            level = monster.get('level', 1)
            
            text = font.render(f"{name} Lv.{level} - HP: {hp}/{max_hp}", True, (255, 255, 255))
            screen.blit(text, (menu_x + 20, y + 10))
        
        # 提示文字
        hint_font = pg.font.Font("assets/fonts/Minecraft.ttf", 16)
        hint = hint_font.render("↑↓: Select  ENTER: Space  ESC: Cancel", True, (200, 200, 200))
        screen.blit(hint, (menu_x + 20, menu_y + menu_height - 25))
    
    def _draw_potion_menu(self, screen: pg.Surface, font: pg.font.Font):
        """繪製藥水選單"""
        available_potions = self._get_available_potions()
        
        # 選單背景
        menu_width = 500
        menu_height = min(300, 60 + len(available_potions) * 50)
        menu_x = (GameSettings.SCREEN_WIDTH - menu_width) // 2
        menu_y = GameSettings.SCREEN_HEIGHT - 300
        
        # 半透明黑色背景
        menu_bg = pg.Surface((menu_width, menu_height))
        menu_bg.set_alpha(230)
        menu_bg.fill((40, 40, 40))
        screen.blit(menu_bg, (menu_x, menu_y))
        
        # 邊框
        pg.draw.rect(screen, (255, 255, 255), 
                    pg.Rect(menu_x, menu_y, menu_width, menu_height), 3, border_radius=5)
        
        # 繪製藥水選項
        for i, potion in enumerate(available_potions):
            y = menu_y + 20 + i * 50
            
            # 選中的項目高亮
            if i == self.menu_selection:
                highlight_rect = pg.Rect(menu_x + 10, y, menu_width - 20, 45)
                pg.draw.rect(screen, (100, 100, 150), highlight_rect, border_radius=3)
            
            # 藥水名稱、描述和數量
            name = potion.get('name', 'Potion')
            description = potion.get('description', '')
            count = potion.get('count', 0)
            
            text = font.render(f"{name} ({description}) x{count}", True, (255, 255, 255))
            screen.blit(text, (menu_x + 20, y + 10))
        
        # 提示文字
        hint_font = pg.font.Font("assets/fonts/Minecraft.ttf", 16)
        hint = hint_font.render("↑↓: Select  ENTER: Space  ESC: Cancel", True, (200, 200, 200))
        screen.blit(hint, (menu_x + 20, menu_y + menu_height - 25))