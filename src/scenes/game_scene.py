import pygame as pg
import threading
import time

from src.scenes.scene import Scene
from src.core import GameManager, OnlineManager
from src.utils import Logger, PositionCamera, GameSettings, Position
from src.core.services import sound_manager, scene_manager
from src.sprites import Sprite
from typing import override
from src.interface.components.button import Button

class GameScene(Scene):
    game_manager: GameManager
    online_manager: OnlineManager | None
    sprite_online: Sprite
    bag_button: Button
    setting_button: Button
    gps_button: Button
    return_to: str
    
    def __init__(self):
        super().__init__()
        # Game Manager
        manager = GameManager.load("saves/game0.json")
        if manager is None:
            Logger.error("Failed to load game manager")
            exit(1)
        self.game_manager = manager
        
        if self.game_manager.player:
            self.game_manager.current_map_key = "map.tmx"
            self.game_manager.player.position = self.game_manager.maps["map.tmx"].spawn
            self.game_manager.exit_positions.clear()

        # Online Manager
        if GameSettings.IS_ONLINE:
            self.online_manager = OnlineManager()
        else:
            self.online_manager = None
        self.sprite_online = Sprite("ingame_ui/options1.png", (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE))


        screen_width = GameSettings.SCREEN_WIDTH if hasattr(GameSettings, 'SCREEN_WIDTH') else 800
        button_size = 40
        margin = 20
       
        self.bag_button = Button(
            img_path="UI/button_backpack.png",
            img_hovered_path="UI/button_backpack_hover.png",
            x=screen_width - button_size - margin,
            y=margin,
            width=button_size,
            height=button_size,
        )
        self.setting_button = Button(
            img_path="UI/button_setting.png",
            img_hovered_path="UI/button_setting_hover.png",
            x=screen_width - 2 * button_size - 2 * margin,
            y=margin,
            width=button_size,
            height=button_size,
        )
        self.gps_button = Button(
            img_path="UI/raw/UI_Flat_Button02a_4.png",
            img_hovered_path="UI/raw/UI_Flat_Button02a_1.png",
            x=screen_width - 3 * button_size - 3 * margin,  
            y=margin,
            width=button_size,
            height=button_size,
        )

        self.setting_button.on_click = lambda: self._open_settings()
        self.bag_button.on_click = lambda: self._open_bag()
        self.gps_button.on_click = lambda: self._open_gps()
    
    def _open_settings(self):
        setting_scene = scene_manager._scenes["settings"]
        setting_scene.return_to = "game" 
        scene_manager.change_scene("settings")
    def _open_bag(self):
        self.game_manager.bag.show()

    def _open_gps(self):
        self.game_manager.gps.toggle_panel()

    def _draw_minimap(self, screen: pg.Surface):
        if not self.game_manager.player or not self.game_manager.current_map:
            return

        minimap_size = 200
        minimap_x = 10
        minimap_y = 10

        # 看地圖表面
        map_surface = self.game_manager.current_map._surface
        map_width = map_surface.get_width()
        map_height = map_surface.get_height()

        # 縮放比例
        scale_x = minimap_size / map_width
        scale_y = minimap_size / map_height
        scale = min(scale_x, scale_y)

        # minimap
        scaled_map = pg.transform.scale(map_surface, (int(map_width * scale), int(map_height * scale)))
        
        # 畫 minimap
        screen.blit(scaled_map, (minimap_x, minimap_y))

        # player 在 minimap 的位置
        player_x = self.game_manager.player.position.x * scale + minimap_x
        player_y = self.game_manager.player.position.y * scale + minimap_y

        # player: 紅色方塊
        player_size = 4
        player_rect = pg.Rect(player_x - player_size // 2, player_y - player_size // 2, player_size, player_size)
        pg.draw.rect(screen, (255, 0, 0), player_rect)

    @override
    def enter(self) -> None:
        sound_manager.play_bgm("RBY 103 Pallet Town.ogg")
        if self.online_manager:
            self.online_manager.enter()
        
    @override
    def exit(self) -> None:
        if self.online_manager:
            self.online_manager.exit()
        
    @override
    def update(self, dt: float):
        # Check if there is assigned next scene
        self.game_manager.try_switch_map()
        
        # Update player and other data
        if self.game_manager.player:
            self.game_manager.player.update(dt)
        for enemy in self.game_manager.current_enemy_trainers:
            enemy.update(dt)
        for npc in self.game_manager.current_shop_npcs:
            npc.update(dt)
            
        # Update others
        self.game_manager.bag.update(dt)
        self.game_manager.shop.update(dt)
        self.game_manager.gps.update(dt, self.game_manager)
        
        if self.game_manager.player is not None and self.online_manager is not None:
            _ = self.online_manager.update(
                self.game_manager.player.position.x, 
                self.game_manager.player.position.y,
                self.game_manager.current_map.path_name
            )

        # 更新按鈕與狀態
        self.bag_button.update(dt)
        self.setting_button.update(dt)
        self.gps_button.update(dt)
        
    @override
    def draw(self, screen: pg.Surface):        
        if self.game_manager.player:
            '''
            [TODO HACKATHON 3]
            Implement the camera algorithm logic here
            Right now it's hard coded, you need to follow the player's positions
            you may use the below example, but the function still incorrect, you may trace the entity.py
            
            camera = self.game_manager.player.camera
            '''
            #camera = PositionCamera(16 * GameSettings.TILE_SIZE, 30 * GameSettings.TILE_SIZE)
            camera = self.game_manager.player.camera
            self.game_manager.current_map.draw(screen, camera)
            self.game_manager.player.draw(screen, camera)
        else:
            camera = PositionCamera(0, 0)
            self.game_manager.current_map.draw(screen, camera)
        for enemy in self.game_manager.current_enemy_trainers:
            enemy.draw(screen, camera)
        for npc in self.game_manager.current_shop_npcs:
            npc.draw(screen, camera)

        self.game_manager.bag.draw(screen)
        self.game_manager.shop.draw(screen)
        self.game_manager.gps.draw(screen, camera)
        
        if self.online_manager and self.game_manager.player:
            list_online = self.online_manager.get_list_players()
            for player in list_online:
                if player["map"] == self.game_manager.current_map.path_name:
                    cam = self.game_manager.player.camera
                    pos = cam.transform_position_as_position(Position(player["x"], player["y"]))
                    self.sprite_online.update_pos(pos)
                    self.sprite_online.draw(screen)

        # 放包包與設定及GPS按鈕
        self.bag_button.draw(screen)
        self.setting_button.draw(screen)
        self.gps_button.draw(screen)

        # minimap
        self._draw_minimap(screen)
