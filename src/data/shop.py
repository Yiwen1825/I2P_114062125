import pygame as pg
import time
import random
from src.utils import GameSettings
from src.sprites import Sprite
from src.interface.components import Button
from src.core.services import input_manager


class Shop:
    shop_inventory: list[dict]
    last_refresh_time: float
    refresh_interval: float
    
    shop_panel: Sprite
    item_banner: Sprite
    close_button: Button
    buy_buttons: list[Button]
    
    visible: bool
    selected_index: int
    
    def __init__(self):
        self.item_templates = [
            {
                "name": "Potion",
                "price": 50,
                "sprite_path": "ingame_ui/potion.png",
                "description": "Restores 20 HP"
            },
            {
                "name": "Pokeball",
                "price": 200,
                "sprite_path": "ingame_ui/ball.png",
                "description": "Catch monsters"
            }
        ]
        
        self.shop_inventory = []
        self.last_refresh_time = time.time()
        self.refresh_interval = 3600
        
        self.shop_panel = Sprite("UI/raw/UI_Flat_Frame03a.png", (600, 450))
        self.item_banner = Sprite("UI/raw/UI_Flat_Banner03a.png", (500, 80))
        
        self.visible = False
        self.selected_index = 0
        
        self.panel_x = (GameSettings.SCREEN_WIDTH - 600) // 2
        self.panel_y = (GameSettings.SCREEN_HEIGHT - 450) // 2
        
        self.buy_buttons = []
        
        self._refresh_inventory()
        
        self.close_button = Button(
            "UI/button_x.png", "UI/button_x_hover.png",
            self.panel_x + 540,
            self.panel_y + 20,
            40, 40,
            lambda: self.hide()
        )
    
    def _create_buy_buttons(self):
        self.buy_buttons = []
        items_x = self.panel_x + 50
        items_y = self.panel_y + 100
        item_spacing = 70
        
        for i in range(len(self.shop_inventory)):
            current_y = items_y + i * item_spacing
            button = Button(
                "UI/button_shop.png", "UI/button_shop_hover.png",
                items_x + 420,
                current_y + 10,
                40, 40,
                lambda idx=i: self._buy_item(idx)
            )
            self.buy_buttons.append(button)
    
    def _refresh_inventory(self):
        self.shop_inventory = []
        
        num_items = random.randint(3, 5)
        selected_items = random.sample(self.item_templates, min(num_items, len(self.item_templates)))
        
        for item_template in selected_items:
            count = random.randint(1, 3)
            self.shop_inventory.append({
                "name": item_template["name"],
                "price": item_template["price"],
                "count": count,
                "sprite_path": item_template["sprite_path"],
                "description": item_template["description"]
            })
        
        self.last_refresh_time = time.time()
        
        if hasattr(self, 'panel_x'):
            self._create_buy_buttons()
    
    def _check_refresh(self):
        current_time = time.time()
        if current_time - self.last_refresh_time >= self.refresh_interval:
            self._refresh_inventory()
    
    def _get_time_until_refresh(self) -> tuple[int, int, int]:
        current_time = time.time()
        elapsed = current_time - self.last_refresh_time
        remaining = max(0, self.refresh_interval - elapsed)
        
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        seconds = int(remaining % 60)
        
        return hours, minutes, seconds
    
    def show(self, game_manager):
        self.visible = True
        self.selected_index = 0
        self.game_manager = game_manager
        self._check_refresh()
    
    def hide(self):
        self.visible = False
    
    def select_previous(self):
        self.selected_index = max(0, self.selected_index - 1)
    
    def select_next(self):
        self.selected_index = min(len(self.shop_inventory) - 1, self.selected_index + 1)
    
    def _get_player_coins(self) -> int:
        if not hasattr(self, 'game_manager'):
            return 0
        
        for item in self.game_manager.bag._items_data:
            if isinstance(item, dict):
                if item.get('name') == 'Coins':
                    return item.get('count', 0)
        return 0
    
    def _buy_item(self, item_index: int):
        if not hasattr(self, 'game_manager'):
            return
        
        if not (0 <= item_index < len(self.shop_inventory)):
            return
        
        item = self.shop_inventory[item_index]
        
        if item['count'] <= 0:
            return
        
        player_coins = self._get_player_coins()
        if player_coins < item['price']:
            return
        
        for bag_item in self.game_manager.bag._items_data:
            if isinstance(bag_item, dict) and bag_item.get('name') == 'Coins':
                bag_item['count'] -= item['price']
                break
        
        item['count'] -= 1
        
        item_found = False
        for bag_item in self.game_manager.bag._items_data:
            if isinstance(bag_item, dict):
                if bag_item.get('name') == item['name']:
                    bag_item['count'] += 1
                    item_found = True
                    break
        
        if not item_found:
            self.game_manager.bag._items_data.append({
                "name": item['name'],
                "count": 1,
                "sprite_path": item['sprite_path']
            })
    
    def update(self, dt: float):
        if not self.visible:
            return
        
        self.close_button.update(dt)
        
        for button in self.buy_buttons:
            button.update(dt)
        
        self._check_refresh()
        
        if input_manager.key_pressed(pg.K_ESCAPE):
            self.hide()
    
    def draw(self, screen: pg.Surface):
        if not self.visible:
            return
        
        dark_overlay = pg.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT))
        dark_overlay.set_alpha(180)
        dark_overlay.fill((0, 0, 0))
        screen.blit(dark_overlay, (0, 0))
        
        screen.blit(self.shop_panel.image, (self.panel_x, self.panel_y))
        
        font_title = pg.font.Font("assets/fonts/Minecraft.ttf", 50)
        font_item = pg.font.Font("assets/fonts/Minecraft.ttf", 18)
        font_detail = pg.font.Font("assets/fonts/Minecraft.ttf", 14)
        font_small = pg.font.Font("assets/fonts/Minecraft.ttf", 12)
        
        title_text = font_title.render("SHOP", True, (0, 0, 0))
        screen.blit(title_text, (self.panel_x + 30, self.panel_y + 25))
        
        player_coins = self._get_player_coins()
        coins_text = font_item.render(f"Coins: {player_coins}", True, (255, 215, 0))
        screen.blit(coins_text, (self.panel_x + 400, self.panel_y + 30))
        
        hours, minutes, seconds = self._get_time_until_refresh()
        timer_text = font_detail.render(
            f"Next refresh: {hours:02d}:{minutes:02d}:{seconds:02d}",
            True, (100, 100, 100)
        )
        screen.blit(timer_text, (self.panel_x + 360, self.panel_y + 55))
        
        self.close_button.draw(screen)
        
        self._draw_items(screen, font_item, font_detail)
        
        for button in self.buy_buttons:
            button.draw(screen)

        hint_text = font_small.render("Press ESC to close", True, (200, 200, 200))
        screen.blit(hint_text, (self.panel_x + 40, self.panel_y + 410))
    
    def _draw_items(self, screen: pg.Surface, font_item: pg.font.Font, font_detail: pg.font.Font):
        items_x = self.panel_x + 50
        items_y = self.panel_y + 100
        item_spacing = 70
        
        for i, item in enumerate(self.shop_inventory):
            current_y = items_y + i * item_spacing
            
            screen.blit(self.item_banner.image, (items_x, current_y))
            
            icon_size = 40
            icon_x = items_x + 35
            icon_y = current_y + 15
            
            try:
                item_sprite = pg.image.load(f"assets/images/{item['sprite_path']}")
                item_sprite = pg.transform.scale(item_sprite, (icon_size, icon_size))
                screen.blit(item_sprite, (icon_x, icon_y))
            except:
                icon_rect = pg.Rect(icon_x, icon_y, icon_size, icon_size)
                pg.draw.rect(screen, (200, 200, 200), icon_rect, border_radius=5)
            
            name_text = font_item.render(item["name"], True, (0, 0, 0))
            screen.blit(name_text, (items_x + 90, current_y + 15))
            
            desc_text = font_detail.render(item["description"], True, (80, 80, 80))
            screen.blit(desc_text, (items_x + 90, current_y + 38))
            
            stock_color = (0, 150, 0) if item['count'] > 0 else (200, 0, 0)
            stock_text = font_item.render(f"x{item['count']}", True, stock_color)
            screen.blit(stock_text, (items_x + 300, current_y + 25))
            
            price_text = font_item.render(f"{item['price']} G", True, (255, 215, 0))
            screen.blit(price_text, (items_x + 360, current_y + 25))