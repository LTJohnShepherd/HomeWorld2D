import sys
import pygame
from spacegame.screens.main_menu import main as main_menu
from spacegame.screens.game_screen import run_game
from spacegame.screens.end_screen import end_screen

STATE_MAIN_MENU = "main_menu"
STATE_GAME      = "game"
STATE_END       = "end"
STATE_EXIT      = "exit"

def run_state_machine():
    pygame.init()
    state = STATE_MAIN_MENU

    while state != STATE_EXIT:
        if state == STATE_MAIN_MENU:
            # main menu: choose play or exit
            result = main_menu()
            if result in (STATE_GAME, STATE_EXIT):
                state = result
            else:
                # default fallback: if None, go to EXIT
                state = STATE_EXIT

        elif state == STATE_GAME:
            # main gameplay
            result = run_game()
            if result in (STATE_MAIN_MENU, STATE_END, STATE_EXIT):
                state = result
            else:
                # ESC fallback: go back to main menu
                state = STATE_MAIN_MENU

        elif state == STATE_END:
            # game over screen
            result = end_screen()
            if result in (STATE_GAME, STATE_MAIN_MENU, STATE_EXIT):
                state = result
            else:
                # default: go back to main menu
                state = STATE_MAIN_MENU

        else:
            # unknown state → exit
            state = STATE_EXIT

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    run_state_machine()