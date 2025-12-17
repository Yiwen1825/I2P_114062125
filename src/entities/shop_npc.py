from __future__ import annotations
import pygame
from typing import override

from .entity import Entity
from src.sprites import Sprite
from src.core import GameManager
from src.core.services import input_manager
from src.utils import GameSettings, Direction, Position


class ShopNPC(Entity):
    max_tiles: int
    warning_sign: Sprite
    detected: bool
    los_direction: Direction

    @override
    def __init__(
        self,
        x: float,
        y: float,
        game_manager: GameManager,
        max_tiles: int = 2,
        facing: Direction | None = None,
        sprite_path: str = "character/ow1.png",
    ) -> None:
        super().__init__(x, y, game_manager, sprite_path)
        self.max_tiles = max_tiles
        if facing is None:
            facing = Direction.DOWN
        self._set_direction(facing)
        self.warning_sign = Sprite("exclamation.png", (GameSettings.TILE_SIZE // 2, GameSettings.TILE_SIZE // 2))
        self.warning_sign.update_pos(Position(x + GameSettings.TILE_SIZE // 4, y - GameSettings.TILE_SIZE // 2))
        self.detected = False

    @override
    def update(self, dt: float) -> None:
        self._has_los_to_player()
        if self.detected and input_manager.key_pressed(pygame.K_SPACE):
            self.game_manager.shop.show(self.game_manager)
        self.animation.update_pos(self.position)

    @override
    def draw(self, screen: pygame.Surface, camera) -> None:
        super().draw(screen, camera)
        if self.detected:
            self.warning_sign.draw(screen, camera)
        if GameSettings.DRAW_HITBOXES:
            los_rect = self._get_los_rect()
            if los_rect is not None:
                pygame.draw.rect(screen, (255, 255, 0), camera.transform_rect(los_rect), 1)

    def _set_direction(self, direction: Direction) -> None:
        self.direction = direction
        if direction == Direction.RIGHT:
            self.animation.switch("right")
        elif direction == Direction.LEFT:
            self.animation.switch("left")
        elif direction == Direction.DOWN:
            self.animation.switch("down")
        else:
            self.animation.switch("up")
        self.los_direction = self.direction

    def _get_los_rect(self) -> pygame.Rect | None:
        tile_size = GameSettings.TILE_SIZE
        width = tile_size
        height = self.max_tiles * tile_size

        if self.los_direction == Direction.UP:
            return pygame.Rect(self.position.x, self.position.y - height, width, height)
        elif self.los_direction == Direction.DOWN:
            return pygame.Rect(self.position.x, self.position.y + tile_size, width, height)
        elif self.los_direction == Direction.LEFT:
            return pygame.Rect(self.position.x - height, self.position.y, height, width)
        elif self.los_direction == Direction.RIGHT:
            return pygame.Rect(self.position.x + tile_size, self.position.y, height, width)
        return None

    def _has_los_to_player(self) -> None:
        player = self.game_manager.player
        if player is None:
            self.detected = False
            return
        los_rect = self._get_los_rect()
        if los_rect is None:
            self.detected = False
            return
        player_rect = pygame.Rect(player.position.x, player.position.y,
                                  GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)
        self.detected = los_rect.colliderect(player_rect)

    @classmethod
    @override
    def from_dict(cls, data: dict, game_manager: GameManager) -> "ShopNPC":
        max_tiles = data.get("max_tiles", 2)
        facing_val = data.get("facing")
        sprite_path = data.get("sprite_path", "character/ow1.png")
        facing: Direction | None = None
        if facing_val is not None:
            if isinstance(facing_val, str):
                facing = Direction[facing_val]
            elif isinstance(facing_val, Direction):
                facing = facing_val
        if facing is None:
            facing = Direction.DOWN
        return cls(
            data["x"] * GameSettings.TILE_SIZE,
            data["y"] * GameSettings.TILE_SIZE,
            game_manager,
            max_tiles,
            facing,
            sprite_path,
        )

    @override
    def to_dict(self) -> dict[str, object]:
        base: dict[str, object] = super().to_dict()
        base["facing"] = self.direction.name
        base["max_tiles"] = self.max_tiles
        return base