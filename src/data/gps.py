import pygame as pg
from collections import deque
from src.utils import GameSettings, Position
from src.sprites import Sprite
from src.interface.components import Button
from src.core.services import input_manager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core import GameManager


class GPS:
    
    def __init__(self):
        self.visible = False
        self.target_position: Position | None = None
        self.path: list[Position] = []
        
        arrow_size = (20, 20)
        self.arrow_up = Sprite("UI/arrow_up.png", arrow_size)
        self.arrow_down = Sprite("UI/arrow_down.png", arrow_size)
        self.arrow_left = Sprite("UI/arrow_left.png", arrow_size)
        self.arrow_right = Sprite("UI/arrow_right.png", arrow_size)
        
        self.panel_visible = False
        self.panel_x = (GameSettings.SCREEN_WIDTH - 300) // 2
        self.panel_y = (GameSettings.SCREEN_HEIGHT - 400) // 2
        self.panel = Sprite("UI/raw/UI_Flat_Frame01a.png", (300, 400))
        
        # 目的地 list
        self.destinations = [
            {"name": "Gym", "position": (24, 23)},
            {"name": "Shop", "position": (54, 13)},
            {"name": "Delta", "position": (55, 30)},
        ]
        
        self.close_button = Button(
            "UI/button_x.png", "UI/button_x_hover.png",
            self.panel_x + 250, self.panel_y + 10,
            40, 40,
            lambda: self.hide_panel()
        )
        
        # 目的地點擊區域
        self.destination_rects: list[pg.Rect] = []
        self._create_destination_rects()
    
    def _create_destination_rects(self):
        self.destination_rects = []
        
        item_y = self.panel_y + 80
        item_spacing = 60
        item_height = 50
        
        for i in range(len(self.destinations)):
            rect = pg.Rect(
                self.panel_x + 30,
                item_y + i * item_spacing,
                240,
                item_height
            )
            self.destination_rects.append(rect)
    
    def toggle_panel(self):
        self.panel_visible = not self.panel_visible
    
    def show_panel(self):
        self.panel_visible = True
    
    def hide_panel(self):
        self.panel_visible = False
    
    def _navigate_to(self, destination: dict): # 導航到我按的目的地
        self.target_position = Position(
            destination["position"][0] * GameSettings.TILE_SIZE,
            destination["position"][1] * GameSettings.TILE_SIZE
        )
        self.visible = True
        self.hide_panel()
    
    def calculate_path(self, game_manager: "GameManager"):
        if not self.target_position or not game_manager.player:
            return
        
        start = Position(
            int(game_manager.player.position.x // GameSettings.TILE_SIZE),
            int(game_manager.player.position.y // GameSettings.TILE_SIZE)
        )
        end = Position(
            int(self.target_position.x // GameSettings.TILE_SIZE),
            int(self.target_position.y // GameSettings.TILE_SIZE)
        )
        
        self.path = self._bfs_path(start, end, game_manager)
    
    def _bfs_path(self, start: Position, end: Position, game_manager: "GameManager") -> list[Position]:
        queue = deque([(start, [start])])
        visited = {(start.x, start.y)}
        
        while queue:
            current, path = queue.popleft()
            
            # 到了
            if current.x == end.x and current.y == end.y:
                return path
            
            directions = [
                Position(current.x, current.y - 1),  # UP
                Position(current.x, current.y + 1),  # DOWN
                Position(current.x - 1, current.y),  # LEFT
                Position(current.x + 1, current.y),  # RIGHT
            ]
            
            for next_pos in directions:
                if (next_pos.x, next_pos.y) in visited:
                    continue
                
                # 有沒有在地圖範圍內
                if next_pos.x < 0 or next_pos.y < 0:
                    continue
                
                # 能不能走
                tile_rect = pg.Rect(
                    next_pos.x * GameSettings.TILE_SIZE,
                    next_pos.y * GameSettings.TILE_SIZE,
                    GameSettings.TILE_SIZE,
                    GameSettings.TILE_SIZE
                )
                
                if not game_manager.check_collision(tile_rect):
                    visited.add((next_pos.x, next_pos.y))
                    queue.append((next_pos, path + [next_pos]))
        
        return []
    
    def stop_navigation(self):
        self.visible = False
        self.path = []
        self.target_position = None
    
    def update(self, dt: float, game_manager: "GameManager"):
        if self.panel_visible:
            self.close_button.update(dt)
            
            # 檢查目的地點擊
            if input_manager.mouse_pressed(1):
                mouse_pos = input_manager.mouse_pos
                for i, rect in enumerate(self.destination_rects):
                    if rect.collidepoint(mouse_pos):
                        self._navigate_to(self.destinations[i])
                        self.calculate_path(game_manager)
                        break
            
            if input_manager.key_pressed(pg.K_ESCAPE):
                self.hide_panel()
        
        if not self.visible:
            return
        
        # 要不要重算路徑
        if game_manager.player and self.target_position:
            player_tile = Position(
                int(game_manager.player.position.x // GameSettings.TILE_SIZE),
                int(game_manager.player.position.y // GameSettings.TILE_SIZE)
            )
            target_tile = Position(
                int(self.target_position.x // GameSettings.TILE_SIZE),
                int(self.target_position.y // GameSettings.TILE_SIZE)
            )
            
            # 到達目標
            if player_tile.x == target_tile.x and player_tile.y == target_tile.y:
                self.stop_navigation()
                return
            
            # 移動時重算路徑
            if len(self.path) == 0 or (player_tile.x != self.path[0].x or player_tile.y != self.path[0].y):
                self.calculate_path(game_manager)
    
    def draw(self, screen: pg.Surface, camera):
        if self.visible and len(self.path) >= 2:
            # 顯示前 15 步的箭頭
            max_arrows = min(15, len(self.path) - 1)
            
            for i in range(1, max_arrows + 1):
                if i >= len(self.path):
                    break
                    
                from_pos = self.path[i - 1]
                to_pos = self.path[i]
                
                # 使用 to_pos
                arrow_world_x = to_pos.x * GameSettings.TILE_SIZE
                arrow_world_y = to_pos.y * GameSettings.TILE_SIZE
                
                # 轉換到螢幕座標
                arrow_screen_x = arrow_world_x - camera.x
                arrow_screen_y = arrow_world_y - camera.y
                
                # 箭頭方向
                arrow_sprite = self._get_arrow_sprite(from_pos, to_pos)
                
                # 算置中偏移量
                arrow_width = arrow_sprite.image.get_width()
                arrow_height = arrow_sprite.image.get_height()
                
                offset_x = (GameSettings.TILE_SIZE - arrow_width) // 2
                offset_y = (GameSettings.TILE_SIZE - arrow_height) // 2
                
                # 繪製箭頭 (完全置中)
                screen.blit(
                    arrow_sprite.image,
                    (arrow_screen_x + offset_x, arrow_screen_y + offset_y)
                )
            
        # 繪製導航面板
        if self.panel_visible:
            # 半透明背景
            dark_overlay = pg.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT))
            dark_overlay.set_alpha(180)
            dark_overlay.fill((0, 0, 0))
            screen.blit(dark_overlay, (0, 0))
            
            # 面板
            screen.blit(self.panel.image, (self.panel_x, self.panel_y))
            
            # 標題
            font_title = pg.font.Font("assets/fonts/Minecraft.ttf", 36)
            title_text = font_title.render("GPS", True, (0, 0, 0))
            screen.blit(title_text, (self.panel_x + 30, self.panel_y + 20))
            
            # 目的地列表
            font_dest = pg.font.Font("assets/fonts/Minecraft.ttf", 24)
            mouse_pos = input_manager.mouse_pos
            
            for i, (dest, rect) in enumerate(zip(self.destinations, self.destination_rects)):
                # 檢查滑鼠懸停
                is_hovered = rect.collidepoint(mouse_pos)
                
                # 繪製背景
                if is_hovered:
                    pg.draw.rect(screen, (255, 255, 200), rect, border_radius=5)
                else:
                    pg.draw.rect(screen, (220, 220, 220), rect, border_radius=5)
                
                # 邊框
                pg.draw.rect(screen, (100, 100, 100), rect, 2, border_radius=5)
                
                # 目的地名稱
                dest_text = font_dest.render(dest["name"], True, (0, 0, 0))
                text_rect = dest_text.get_rect(center=rect.center)
                screen.blit(dest_text, text_rect)
            
            # 關閉按鈕
            self.close_button.draw(screen)
    
    def _get_arrow_sprite(self, from_pos: Position, to_pos: Position) -> Sprite: # 根據方向選擇箭頭
        dx = to_pos.x - from_pos.x
        dy = to_pos.y - from_pos.y
        
        if dx > 0:
            return self.arrow_right
        elif dx < 0:
            return self.arrow_left
        elif dy > 0:
            return self.arrow_down
        else:
            return self.arrow_up