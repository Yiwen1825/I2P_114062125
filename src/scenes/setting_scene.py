'''
[TODO HACKATHON 5]
Try to mimic the menu_scene.py or game_scene.py to create this new scene
'''
import pygame as pg

from src.utils import GameSettings
from src.sprites import BackgroundSprite, Sprite
from src.scenes.scene import Scene
from src.interface.components import Button
from src.core.services import scene_manager, sound_manager, input_manager
from typing import override
from src.core.managers.game_manager import GameManager

class settingScene(Scene):
    setting_panel: Sprite
    slider_handle: Sprite 
    toggle_off_sprite: Sprite
    toggle_on_sprite: Sprite
    close_button: Button
    back_button: Button
    save_button: Button
    load_button: Button
    volume: int
    slider_dragging: bool
    mute: bool
    return_to: str = "menu"
    
    def __init__(self):
        super().__init__()
        self.setting_panel = Sprite("UI/raw/UI_Flat_Frame03a.png", (500, 400))
        self.slider_handle = Sprite("UI/raw/UI_Flat_Handle03a.png", (24, 24))
        self.toggle_off_sprite = Sprite("UI/raw/UI_Flat_ToggleOff03a.png", (60, 30))
        self.toggle_on_sprite = Sprite("UI/raw/UI_Flat_ToggleOn03a.png", (60, 30))
        
        # 音量
        current_volume = sound_manager.get_bgm_volume()
        self.volume = int(current_volume * 100)
        self.slider_dragging = False
        self.mute = False
        
        # 滑桿
        self.slider_margin = 40  # 左右邊距
        self.slider_y = GameSettings.SCREEN_HEIGHT // 2 - 50
        self.slider_height = 10

        # Toggle 按鈕
        self.toggle_x = 180
        self.toggle_y = GameSettings.SCREEN_HEIGHT // 2 + 50
        self.toggle_width = 60
        self.toggle_height = 30

        px, py = GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT * 3 // 4
        self.back_button = Button(
            "UI/button_back.png", "UI/button_back_hover.png",
            px - 230, py - 82, 80, 80,
            lambda: scene_manager.change_scene("menu")
        )
        self.save_button = Button(
            "UI/button_save.png", "UI/button_save_hover.png",
            px - 130, py - 82, 80, 80,
            self._save_game
        )
        self.load_button = Button(
            "UI/button_load.png", "UI/button_load_hover.png",
            px - 30, py - 82, 80, 80,
            self._load_game
        )
        self.close_button = Button(
            "UI/button_x.png", "UI/button_x_hover.png",
            px + 190 , py - 360, 40, 40,
            lambda: scene_manager.change_scene(self.return_to) 
        )
        
        self.previous_screen = None
    def _save_game(self):
        game_scene = scene_manager._scenes.get("game")
        if game_scene:
            game_scene.game_manager.save("saves/game0.json")
    
    def _load_game(self):
        loaded = GameManager.load("saves/game0.json")
        if loaded:
            game_scene = scene_manager._scenes.get("game")
            if game_scene:
                game_scene.game_manager = loaded
                scene_manager.change_scene("game")
        
    @override
    def enter(self) -> None:
        if self.return_to == "game":
            bgm_file = "RBY 103 Pallet Town.ogg"
        else:
            bgm_file = "RBY 101 Opening (Part 1).ogg"
        sound_manager.play_bgm(bgm_file)
        self.previous_screen = pg.display.get_surface().copy()
        sound_manager.set_bgm_volume(0 if self.mute else self.volume / 100.0)

    @override
    def exit(self) -> None:
        pass

    @override
    def update(self, dt: float) -> None:
        if input_manager.key_pressed(pg.K_ESCAPE):
            scene_manager.change_scene(self.return_to)
            return
        
        self.back_button.update(dt)
        self.close_button.update(dt)
        self.save_button.update(dt)
        self.load_button.update(dt)
        
        mouse_pos = input_manager.mouse_pos

        # 算滑桿位置
        panel_x = (GameSettings.SCREEN_WIDTH - self.setting_panel.image.get_width()) // 2
        slider_full_x = panel_x + self.slider_margin
        slider_full_width = self.setting_panel.image.get_width() - 2 * self.slider_margin
        handle_x = slider_full_x + int((self.volume / 100.0) * slider_full_width)
        handle_y = self.slider_y + self.slider_height // 2
        
        # 滑桿處理
        if input_manager.mouse_pressed(1):
            handle_radius = 12 
            distance = ((mouse_pos[0] - handle_x) ** 2 + (mouse_pos[1] - handle_y) ** 2) ** 0.5
            
            if distance <= handle_radius + 5:
                self.slider_dragging = True
        
        if input_manager.mouse_down(1) and self.slider_dragging:
            relative_x = mouse_pos[0] - slider_full_x
            volume_float = max(0.0, min(1.0, relative_x / slider_full_width))
            self.volume = int(volume_float * 100)
            if not self.mute:
                sound_manager.set_bgm_volume(self.volume / 100.0)
        
        if not input_manager.mouse_down(1):
            self.slider_dragging = False
        
        # Toggle 按鈕處理
        if input_manager.mouse_pressed(1):
            toggle_rect = pg.Rect(panel_x + self.toggle_x, self.toggle_y, self.toggle_width, self.toggle_height)
            if toggle_rect.collidepoint(mouse_pos):
                self.mute = not self.mute
                sound_manager.set_bgm_volume(0 if self.mute else self.volume / 100.0)

    @override
    def draw(self, screen: pg.Surface) -> None:
        # 上一個背景的畫面
        if self.previous_screen:
            screen.blit(self.previous_screen, (0, 0))
        
        # 後面半透明
        dark_overlay = pg.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT))
        dark_overlay.set_alpha(180)
        dark_overlay.fill((0, 0, 0))
        screen.blit(dark_overlay, (0, 0))
        
        # 橘色框框
        panel_x = (GameSettings.SCREEN_WIDTH - self.setting_panel.image.get_width()) // 2
        panel_y = (GameSettings.SCREEN_HEIGHT - self.setting_panel.image.get_height()) // 2
        screen.blit(self.setting_panel.image, (panel_x, panel_y))
        
        # 字體
        font_title = pg.font.Font("assets/fonts/Minecraft.ttf", 40) 
        font_medium = pg.font.Font("assets/fonts/Minecraft.ttf", 26)
        font_small = pg.font.Font("assets/fonts/Minecraft.ttf", 20)

        # 標題
        title_text = font_title.render("SETTINGS", True, (0, 0, 0))
        screen.blit(title_text, (panel_x + 40, panel_y + 30))
        
        # 音量字
        volume_label = font_medium.render(f"Volume: {self.volume}%", True, (0, 0, 0))
        screen.blit(volume_label, (panel_x + 40, self.slider_y - 50))
        
        # 算滑桿位置
        slider_full_x = panel_x + self.slider_margin
        slider_full_width = self.setting_panel.image.get_width() - 2 * self.slider_margin
        
        # 滑桿軌道
        slider_track_height = 20
        slider_rect = pg.Rect(slider_full_x, self.slider_y - (slider_track_height - self.slider_height) // 2, 
                            slider_full_width, slider_track_height) 
        pg.draw.rect(screen, (255, 255, 255), slider_rect, border_radius=3)
        pg.draw.rect(screen, (0, 0, 0), slider_rect, 3, border_radius=3)
        
        # 滑過去灰色
        filled_width = int((self.volume / 100.0) * slider_full_width)
        if filled_width > 0:
            filled_rect = pg.Rect(slider_full_x, self.slider_y - (slider_track_height - self.slider_height) // 2, 
                                filled_width, slider_track_height)
            pg.draw.rect(screen, (200, 200, 200), filled_rect, border_radius=3)
            pg.draw.rect(screen, (0, 0, 0), filled_rect, 3, border_radius=3) 
        
        # 滑桿把手
        handle_x = slider_full_x + filled_width
        handle_y = self.slider_y + self.slider_height // 2
        handle_img_x = handle_x - self.slider_handle.image.get_width() // 2
        handle_img_y = handle_y - self.slider_handle.image.get_height() // 2
        screen.blit(self.slider_handle.image, (handle_img_x, handle_img_y))
        
        # Mute 文字和狀態
        mute_label = font_medium.render("Mute: ", True, (0, 0, 0))
        screen.blit(mute_label, (panel_x + 40, self.toggle_y - 3))
        mute_label_width = mute_label.get_width()
        status_text = "Off" if not self.mute else "On"
        status_label = font_medium.render(status_text, True, (0, 0, 0))
        screen.blit(status_label, (panel_x + 40 + mute_label_width, self.toggle_y - 3))
        # 開關
        toggle_sprite = self.toggle_on_sprite if self.mute else self.toggle_off_sprite
        toggle_img_x = panel_x + self.toggle_x
        screen.blit(toggle_sprite.image, (toggle_img_x, self.toggle_y))
        
        # 底下提示
        hint_text = font_small.render("Press ESC to close", True, (200, 200, 200))
        hint_x = (GameSettings.SCREEN_WIDTH - hint_text.get_width()) // 2
        screen.blit(hint_text, (hint_x, GameSettings.SCREEN_HEIGHT - 60))
        
        # 按鈕們
        self.close_button.draw(screen)
        self.back_button.draw(screen)
        self.save_button.draw(screen)
        self.load_button.draw(screen)