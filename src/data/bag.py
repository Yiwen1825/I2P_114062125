import pygame as pg
import json
from src.utils import GameSettings
from src.utils.definition import Monster, Item
from src.sprites import BackgroundSprite, Sprite
from src.interface.components import Button
from src.core.services import input_manager


class Bag:
    _monsters_data: list[Monster]
    _items_data: list[Item]
    bag_panel: Sprite
    monster_banner: Sprite
    close_button: Button
    
    visible: bool
    monster_scroll_offset: int

    def __init__(self, monsters_data: list[Monster] | None = None, items_data: list[Item] | None = None):
        self._monsters_data = monsters_data if monsters_data else []
        self._items_data = items_data if items_data else []
        self.bag_panel = Sprite("UI/raw/UI_Flat_Frame03a.png", (600, 450))
        self.monster_banner = Sprite("UI/raw/UI_Flat_Banner03a.png", (300, 120))
        
        self.visible = False
        self.monster_scroll_offset = 0
        
        self.panel_x = (GameSettings.SCREEN_WIDTH - 600) // 2
        self.panel_y = (GameSettings.SCREEN_HEIGHT - 450) // 2
        
        self.close_button = Button(
            "UI/button_x.png","UI/button_x_hover.png",
            self.panel_x + 540,
            self.panel_y + 20,
            40, 40,
            lambda: self.hide()
        )

    def show(self):
        self.visible = True
        self.monster_scroll_offset = 0

    def hide(self):
        self.visible = False

    def scroll_monsters_up(self):
        self.monster_scroll_offset = max(0, self.monster_scroll_offset - 1)

    def scroll_monsters_down(self):
        max_monsters_visible = 2
        max_offset = max(0, len(self._monsters_data) - max_monsters_visible)
        self.monster_scroll_offset = min(max_offset, self.monster_scroll_offset + 1)

    def update(self, dt: float):
        if not self.visible:
            return
        
        self.close_button.update(dt)
        
        if input_manager.key_pressed(pg.K_ESCAPE):
            self.hide()
        
        if input_manager.key_pressed(pg.K_w) or input_manager.key_pressed(pg.K_UP):
            self.scroll_monsters_up()
        if input_manager.key_pressed(pg.K_s) or input_manager.key_pressed(pg.K_DOWN):
            self.scroll_monsters_down()

    def draw(self, screen: pg.Surface):
        if not self.visible:
            return
        
        # 半透明背景
        dark_overlay = pg.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT))
        dark_overlay.set_alpha(180)
        dark_overlay.fill((0, 0, 0))
        screen.blit(dark_overlay, (0, 0))
        
        # 背包面板
        screen.blit(self.bag_panel.image, (self.panel_x, self.panel_y))
        
        # 字體
        font_title = pg.font.Font("assets/fonts/Minecraft.ttf", 50)
        font_item = pg.font.Font("assets/fonts/Minecraft.ttf", 18)
        font_detail = pg.font.Font("assets/fonts/Minecraft.ttf", 10)
        
        # 標題
        title_text = font_title.render("BAG", True, (0, 0, 0))
        screen.blit(title_text, (self.panel_x + 30, self.panel_y + 25))
        
        # 關閉按鈕
        self.close_button.draw(screen)
        
        # 左側: 怪物列表
        self._draw_monsters(screen, font_item, font_detail)
        
        # 右側: 物品列表
        self._draw_items(screen, font_item)
        
        # 操作提示
        hint_text = font_detail.render("W/S: Scroll | ESC: Close", True, (100, 100, 100))
        screen.blit(hint_text, (self.panel_x + 40, self.panel_y + 410))

    def _draw_monsters(self, screen: pg.Surface, font_item: pg.font.Font, font_detail: pg.font.Font):
        monster_box_x = self.panel_x + 30
        monster_box_y = self.panel_y + 90
        monster_spacing = 130
        max_monsters_visible = 2
        
        if self._monsters_data:
            visible_monsters = self._monsters_data[
                self.monster_scroll_offset : self.monster_scroll_offset + max_monsters_visible
            ]
            
            for i, monster in enumerate(visible_monsters):
                current_y = monster_box_y + i * monster_spacing
                
                # 怪物背景框
                screen.blit(self.monster_banner.image, (monster_box_x, current_y))
                
                # 怪物圖示區域
                icon_size = 70
                icon_x = monster_box_x + 20
                icon_y = current_y + 10
                
                # 嘗試載入怪物圖片
                if isinstance(monster, dict) and 'sprite_path' in monster:
                    sprite_path = monster['sprite_path']
                    monster_sprite = pg.image.load(f"assets/images/{sprite_path}")
                    monster_sprite = pg.transform.scale(monster_sprite, (icon_size, icon_size))
                    screen.blit(monster_sprite, (icon_x, icon_y))
                elif hasattr(monster, 'sprite_path'):
                    sprite_path = monster.sprite_path
                    monster_sprite = pg.image.load(f"assets/images/{sprite_path}")
                    monster_sprite = pg.transform.scale(monster_sprite, (icon_size, icon_size))
                    screen.blit(monster_sprite, (icon_x, icon_y))
                else:
                    # 預設顏色方塊
                    icon_rect = pg.Rect(icon_x, icon_y, icon_size, icon_size)
                    pg.draw.rect(screen, (150, 200, 150), icon_rect, border_radius=5)

                
                # 取得怪物資料 (支援 dict 和物件)
                if isinstance(monster, dict):
                    monster_name = monster.get('name', 'Unknown')
                    current_hp = monster.get('hp', 0)
                    max_hp = monster.get('max_hp', 1)
                    level = monster.get('level', 1)
                else:
                    monster_name = getattr(monster, 'name', str(monster))
                    current_hp = getattr(monster, 'hp', getattr(monster, 'current_hp', 0))
                    max_hp = getattr(monster, 'max_hp', 1)
                    level = getattr(monster, 'level', getattr(monster, 'lv', 1))
                
                # 怪物名稱
                name_text = font_item.render(monster_name, True, (0, 0, 0))
                screen.blit(name_text, (monster_box_x + 100, current_y + 10))
                
                # HP 條
                hp_bar_x = monster_box_x + 100
                hp_bar_y = current_y + 40
                hp_bar_width = 140
                hp_bar_height = 12
                
                # HP 背景
                pg.draw.rect(screen, (200, 50, 50), 
                           pg.Rect(hp_bar_x, hp_bar_y, hp_bar_width, hp_bar_height), 
                           border_radius=3)
                
                # HP 填充
                hp_percent = current_hp / max_hp if max_hp > 0 else 0
                hp_filled_width = int(hp_bar_width * hp_percent)
                if hp_filled_width > 0:
                    pg.draw.rect(screen, (100, 200, 100),
                               pg.Rect(hp_bar_x, hp_bar_y, hp_filled_width, hp_bar_height),
                               border_radius=3)
                
                # HP 文字
                hp_text = font_detail.render(f"{current_hp} / {max_hp}", True, (0, 0, 0))
                screen.blit(hp_text, (hp_bar_x + hp_bar_width + 5, hp_bar_y - 2))
                
                # 等級
                level_text = font_item.render(f"Lv.{level}", True, (0, 0, 0))
                screen.blit(level_text, (monster_box_x + 100, current_y + 65))
            
            # 捲動提示
            if len(self._monsters_data) > max_monsters_visible:
                scroll_hint = font_detail.render(
                    f"{self.monster_scroll_offset + 1}-{min(self.monster_scroll_offset + max_monsters_visible, len(self._monsters_data))} / {len(self._monsters_data)}",
                    True, (100, 100, 100)
                )
                screen.blit(scroll_hint, (monster_box_x + 80, monster_box_y + 270))
        else:
            # 沒有怪物
            screen.blit(self.monster_banner.image, (monster_box_x, monster_box_y))
            empty_text = font_item.render("No Monsters", True, (150, 150, 150))
            empty_x = monster_box_x + 130 - empty_text.get_width() // 2
            empty_y = monster_box_y + 60 - empty_text.get_height() // 2
            screen.blit(empty_text, (empty_x, empty_y))

    def _draw_items(self, screen: pg.Surface, font_item: pg.font.Font):
        """繪製物品列表"""
        items_x = self.panel_x + 320
        items_y = self.panel_y + 90
        item_spacing = 60
        
        if self._items_data:
            for i, item in enumerate(self._items_data[:6]):
                item_y = items_y + i * item_spacing
                
                # 物品圖示
                icon_radius = 20
                icon_center = (items_x + 35, item_y + 25)
                
                # 嘗試載入物品圖片
                try:
                    if isinstance(item, dict) and 'sprite_path' in item:
                        sprite_path = item['sprite_path']
                        item_sprite = pg.image.load(f"assets/images/{sprite_path}")
                        item_sprite = pg.transform.scale(item_sprite, (icon_radius * 2, icon_radius * 2))
                        sprite_rect = item_sprite.get_rect(center=icon_center)
                        screen.blit(item_sprite, sprite_rect)
                    elif hasattr(item, 'sprite_path'):
                        sprite_path = item.sprite_path
                        item_sprite = pg.image.load(f"assets/images/{sprite_path}")
                        item_sprite = pg.transform.scale(item_sprite, (icon_radius * 2, icon_radius * 2))
                        sprite_rect = item_sprite.get_rect(center=icon_center)
                        screen.blit(item_sprite, sprite_rect)
                    else:
                        # 預設圓形
                        pg.draw.circle(screen, (200, 200, 200), icon_center, icon_radius)
                        pg.draw.circle(screen, (0, 0, 0), icon_center, icon_radius, 2)
                except:
                    # 載入失敗時使用預設圓形
                    pg.draw.circle(screen, (200, 200, 200), icon_center, icon_radius)
                    pg.draw.circle(screen, (0, 0, 0), icon_center, icon_radius, 2)
                
                # 取得物品資料 (支援 dict 和物件)
                if isinstance(item, dict):
                    item_name = item.get('name', 'Unknown')
                    count = item.get('count', 1)
                else:
                    item_name = getattr(item, 'name', str(item))
                    count = getattr(item, 'count', getattr(item, 'quantity', 1))
                
                # 物品名稱
                item_text = font_item.render(item_name, True, (0, 0, 0))
                screen.blit(item_text, (items_x + 70, item_y + 15))
                
                # 物品數量
                count_text = font_item.render(f"x{count}", True, (0, 0, 0))
                screen.blit(count_text, (items_x + 200, item_y + 15))
        else:
            # 沒有物品
            empty_text = font_item.render("No Items", True, (150, 150, 150))
            screen.blit(empty_text, (items_x + 80, items_y + 100))

    def to_dict(self) -> dict[str, object]:
        return {
            "monsters": list(self._monsters_data),
            "items": list(self._items_data)
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Bag":
        monsters = data.get("monsters") or []
        items = data.get("items") or []
        bag = cls(monsters, items)
        return bag