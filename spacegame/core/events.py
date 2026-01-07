import pygame

# Custom event types for the game. Uses pygame.USEREVENT range.
# Consumers should call `make_save_game_event(owner)` to create an event
# that requests saving the provided owner object.

SAVE_GAME_EVENT = pygame.USEREVENT + 1


def make_save_game_event(owner):
    """Return a pygame Event that asks the main loop to save `owner`.

    The event will carry an `owner` attribute referencing the object
    that should be persisted (typically the `ExpeditionShip`).
    """
    return pygame.event.Event(SAVE_GAME_EVENT, {"owner": owner})
