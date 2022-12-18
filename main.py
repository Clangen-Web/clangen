#!/usr/bin/env python3
import sys
import os
from scripts.game_structure.load_cat import *
from scripts.cat.sprites import sprites
from scripts.clan import clan_class
import pygame_gui
import pygame
# from scripts.world import load_map

pygame.init()

directory = os.path.dirname(__file__)
if directory:
    os.chdir(directory)

# initialize pygame_gui manager, and load themes
manager = pygame_gui.UIManager((800, 700), 'resources/defaults.json')
manager.get_theme().load_theme('resources/buttons.json')
manager.get_theme().load_theme('resources/text_boxes.json')
manager.get_theme().load_theme('resources/text_boxes_dark.json')
manager.get_theme().load_theme('resources/vertical_scroll_bar.json')

# import all screens for initialization (Note - must be done after pygame_gui manager is created)
from scripts.screens.all_screens import *

# P Y G A M E
clock = pygame.time.Clock()
pygame.display.set_icon(pygame.image.load('resources/images/icon.png'))

# LOAD cats & clan
if not os.path.exists('saves/clanlist.txt'):
    os.makedirs('saves', exist_ok=True)
    with open('saves/clanlist.txt', 'w') as write_file:
        write_file.write('')
with open('saves/clanlist.txt', 'r') as read_file:
    clan_list = read_file.read()
    if_clans = len(clan_list.strip())
if if_clans > 0:
    game.switches['clan_list'] = clan_list.split('\n')
    try:
        load_cats()
        clan_class.load_clan()
    except Exception as e:
        print("\nERROR MESSAGE:\n",e,"\n")
        if not game.switches['error_message']:
            game.switches[
                'error_message'] = 'There was an error loading the cats file!'
"""
    try:
        game.map_info = load_map('saves/' + game.clan.name)
    except NameError:
        game.map_info = {}
    except:
        game.map_info = load_map("Fallback")
        print("Default map loaded.")
        """

# LOAD settings
if not os.path.exists('saves/settings.txt'):
    with open('saves/settings.txt', 'w') as write_file:
        write_file.write('')
game.load_settings()

# reset brightness to allow for dark mode to not look crap
sprites.load_scars()

start_screen.screen_switches()
while True:
    time_delta = clock.tick(30) / 1000.0
    if game.switches['cur_screen'] not in ['start screen']:
        if game.settings['dark mode']:
            screen.fill((57, 50, 36))
        else:
            screen.fill((206, 194, 168))

    mouse.check_pos()

    # Draw screens
    # This occurs before events are handled to stop pygame_gui buttons from blinking.
    game.all_screens[game.current_screen].on_use()

    # EVENTS
    for event in pygame.event.get():
        game.all_screens[game.current_screen].handle_event(event)

        if event.type == pygame.QUIT:
            # close pygame
            pygame.display.quit()
            pygame.quit()
            sys.exit()

        # MOUSE CLICK
        if event.type == pygame.MOUSEBUTTONDOWN:
            game.clicked = True

        # F2 turns toggles visual debug mode for pygame_gui, allowed for easier bug fixes.
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F2:
                if not manager.visual_debug_active:
                    manager.set_visual_debug_mode(True)
                else:
                    manager.set_visual_debug_mode(False)
        
        manager.process_events(event)

    manager.update(time_delta)

    # update
    game.update_game()
    if game.switch_screens:
        game.all_screens[game.last_screen_forupdate].exit_screen()
        game.all_screens[game.current_screen].screen_switches()
        game.switch_screens = False
    # END FRAME
    manager.draw_ui(screen)

    pygame.display.update()