from __future__ import annotations
import pygame as pg
from typing import override
from src.sprites import Animation
from src.utils import Position, PositionCamera, Direction, GameSettings
from src.core import GameManager


class Entity:
    animation: Animation
    direction: Direction
    position: Position
    game_manager: GameManager
    sprite_path: str

    def __init__(self, x: float, y: float, game_manager: GameManager, sprite_path: str = "character/ow1.png") -> None:
        # Sprite is only for debug, need to change into animations
        self.sprite_path = sprite_path
        self.animation = Animation(
            sprite_path, ["down", "left", "right", "up"], 4,
            (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)
        )

        self.position = Position(x, y)
        self.direction = Direction.DOWN
        self.animation.update_pos(self.position)
        self.game_manager = game_manager

        self.animation.switch("down")
        self.game_manager = game_manager
        
    def update(self, dt: float) -> None:
        self.animation.update_pos(self.position)
        self.animation.update(dt)
        
    def draw(self, screen: pg.Surface, camera: PositionCamera) -> None:
        self.animation.draw(screen, camera)
        if GameSettings.DRAW_HITBOXES:
            self.animation.draw_hitbox(screen, camera)
        
    @staticmethod
    def _snap_to_grid(value: float) -> int:
        return round(value / GameSettings.TILE_SIZE) * GameSettings.TILE_SIZE
    
    @property
    def camera(self) -> PositionCamera:
        '''
        [TODO HACKATHON 3]
        Implement the correct algorithm of player camera
        '''
        cam_x = self.position.x - GameSettings.SCREEN_WIDTH // 2
        cam_y = self.position.y - GameSettings.SCREEN_HEIGHT // 2
        
        return PositionCamera(int(cam_x), int(cam_y))
        
    def to_dict(self) -> dict[str, object]:
        return {
            "x": self.position.x / GameSettings.TILE_SIZE,
            "y": self.position.y / GameSettings.TILE_SIZE,
            "sprite_path": self.sprite_path,
        }

    @classmethod
    def from_dict(cls, data: dict[str, float | int], game_manager: GameManager) -> Entity:
        x = float(data["x"])
        y = float(data["y"])
        sprite_path = data.get("sprite_path", "character/ow1.png")
        return cls(x * GameSettings.TILE_SIZE, y * GameSettings.TILE_SIZE, game_manager, sprite_path)
