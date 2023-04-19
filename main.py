#!/usr/bin/env python3


# pylint: disable=line-too-long
"""




This file is the main file for the game.
It also contains the main pygame loop
It first sets up logging, then loads the version hash from version.ini (if it exists), then loads the cats and clan.
It then loads the settings, and then loads the start screen.




""" # pylint: enable=line-too-long

import platform
import shutil
import sys
import time
import os
import asyncio
import i18n

async def main():

    # scr = platform.window.document.createElement("script") # pylint: disable=no-member
    # scr.src = "https://cdnjs.cloudflare.com/ajax/libs/localforage/1.10.0/localforage.min.js"
    # platform.window.document.head.appendChild(scr) # pylint: disable=no-member
    # while platform.window.localforage is None: # pylint: disable=no-member
    #     print("Waiting for localforage to load...")
    #     await asyncio.sleep(0.5)


    # im so sorry but pygbag doesnt add -lidbfs.js to compilation so we have to define it manually
    platform.window.fs_loaded = False
    platform.window.eval("""
        window.IDBFS = {
            dbs: {},
            indexedDB: () => {
                if (typeof indexedDB != 'undefined') return indexedDB;
                var ret = null;
                if (typeof window == 'object') ret = window.indexedDB || window.mozIndexedDB || window.webkitIndexedDB || window.msIndexedDB;
                assert(ret, 'IDBFS used, but indexedDB not supported');
                return ret;
            },
            DB_VERSION: 21,
            DB_STORE_NAME: 'FILE_DATA',
            mount: function (mount) {
                // reuse all of the core MEMFS functionality
                return MEMFS.mount.apply(null, arguments);
            },
            syncfs: (mount, populate, callback) => {
                IDBFS.getLocalSet(mount, (err, local) => {
                if (err) return callback(err);

                IDBFS.getRemoteSet(mount, (err, remote) => {
                    if (err) return callback(err);

                    var src = populate ? remote : local;
                    var dst = populate ? local : remote;

                    IDBFS.reconcile(src, dst, callback);
                });
                });
            },
            quit: () => {
                Object.values(IDBFS.dbs).forEach((value) => value.close());
                IDBFS.dbs = {};
            },
            getDB: (name, callback) => {
                // check the cache first
                var db = IDBFS.dbs[name];
                if (db) {
                return callback(null, db);
                }

                var req;
                try {
                req = IDBFS.indexedDB().open(name, IDBFS.DB_VERSION);
                } catch (e) {
                return callback(e);
                }
                if (!req) {
                return callback("Unable to connect to IndexedDB");
                }
                req.onupgradeneeded = (e) => {
                var db = /** @type {IDBDatabase} */ (e.target.result);
                var transaction = e.target.transaction;

                var fileStore;

                if (db.objectStoreNames.contains(IDBFS.DB_STORE_NAME)) {
                    fileStore = transaction.objectStore(IDBFS.DB_STORE_NAME);
                } else {
                    fileStore = db.createObjectStore(IDBFS.DB_STORE_NAME);
                }

                if (!fileStore.indexNames.contains('timestamp')) {
                    fileStore.createIndex('timestamp', 'timestamp', { unique: false });
                }
                };
                req.onsuccess = () => {
                db = /** @type {IDBDatabase} */ (req.result);

                // add to the cache
                IDBFS.dbs[name] = db;
                callback(null, db);
                };
                req.onerror = (e) => {
                callback(this.error);
                e.preventDefault();
                };
            },
            getLocalSet: (mount, callback) => {
                var entries = {};

                function isRealDir(p) {
                return p !== '.' && p !== '..';
                };
                function toAbsolute(root) {
                return (p) => {
                    return PATH.join2(root, p);
                }
                };

                var check = FS.readdir(mount.mountpoint).filter(isRealDir).map(toAbsolute(mount.mountpoint));

                while (check.length) {
                var path = check.pop();
                var stat;

                try {
                    stat = FS.stat(path);
                } catch (e) {
                    return callback(e);
                }

                if (FS.isDir(stat.mode)) {
                    check.push.apply(check, FS.readdir(path).filter(isRealDir).map(toAbsolute(path)));
                }

                entries[path] = { 'timestamp': stat.mtime };
                }

                return callback(null, { type: 'local', entries: entries });
            },
            getRemoteSet: (mount, callback) => {
                var entries = {};

                IDBFS.getDB(mount.mountpoint, (err, db) => {
                if (err) return callback(err);

                try {
                    var transaction = db.transaction([IDBFS.DB_STORE_NAME], 'readonly');
                    transaction.onerror = (e) => {
                    callback(this.error);
                    e.preventDefault();
                    };

                    var store = transaction.objectStore(IDBFS.DB_STORE_NAME);
                    var index = store.index('timestamp');

                    index.openKeyCursor().onsuccess = (event) => {
                    var cursor = event.target.result;

                    if (!cursor) {
                        return callback(null, { type: 'remote', db: db, entries: entries });
                    }

                    entries[cursor.primaryKey] = { 'timestamp': cursor.key };

                    cursor.continue();
                    };
                } catch (e) {
                    return callback(e);
                }
                });
            },
            loadLocalEntry: (path, callback) => {
                var stat, node;

                try {
                var lookup = FS.lookupPath(path);
                node = lookup.node;
                stat = FS.stat(path);
                } catch (e) {
                return callback(e);
                }

                if (FS.isDir(stat.mode)) {
                return callback(null, { 'timestamp': stat.mtime, 'mode': stat.mode });
                } else if (FS.isFile(stat.mode)) {
                // Performance consideration: storing a normal JavaScript array to a IndexedDB is much slower than storing a typed array.
                // Therefore always convert the file contents to a typed array first before writing the data to IndexedDB.
                node.contents = MEMFS.getFileDataAsTypedArray(node);
                return callback(null, { 'timestamp': stat.mtime, 'mode': stat.mode, 'contents': node.contents });
                } else {
                return callback(new Error('node type not supported'));
                }
            },
            storeLocalEntry: (path, entry, callback) => {
                try {
                if (FS.isDir(entry['mode'])) {
                    FS.mkdirTree(path, entry['mode']);
                } else if (FS.isFile(entry['mode'])) {
                    FS.writeFile(path, entry['contents'], { canOwn: true });
                } else {
                    return callback(new Error('node type not supported'));
                }

                FS.chmod(path, entry['mode']);
                FS.utime(path, entry['timestamp'], entry['timestamp']);
                } catch (e) {
                return callback(e);
                }

                callback(null);
            },
            removeLocalEntry: (path, callback) => {
                try {
                var stat = FS.stat(path);

                if (FS.isDir(stat.mode)) {
                    FS.rmdir(path);
                } else if (FS.isFile(stat.mode)) {
                    FS.unlink(path);
                }
                } catch (e) {
                return callback(e);
                }

                callback(null);
            },
            loadRemoteEntry: (store, path, callback) => {
                var req = store.get(path);
                req.onsuccess = (event) => { callback(null, event.target.result); };
                req.onerror = (e) => {
                callback(this.error);
                e.preventDefault();
                };
            },
            storeRemoteEntry: (store, path, entry, callback) => {
                try {
                var req = store.put(entry, path);
                } catch (e) {
                callback(e);
                return;
                }
                req.onsuccess = () => { callback(null); };
                req.onerror = (e) => {
                callback(this.error);
                e.preventDefault();
                };
            },
            removeRemoteEntry: (store, path, callback) => {
                var req = store.delete(path);
                req.onsuccess = () => { callback(null); };
                req.onerror = (e) => {
                callback(this.error);
                e.preventDefault();
                };
            },
            reconcile: (src, dst, callback) => {
                var total = 0;

                var create = [];
                Object.keys(src.entries).forEach(function (key) {
                var e = src.entries[key];
                var e2 = dst.entries[key];
                if (!e2 || e['timestamp'].getTime() != e2['timestamp'].getTime()) {
                    create.push(key);
                    total++;
                }
                });

                var remove = [];
                Object.keys(dst.entries).forEach(function (key) {
                if (!src.entries[key]) {
                    remove.push(key);
                    total++;
                }
                });

                if (!total) {
                return callback(null);
                }

                var errored = false;
                var db = src.type === 'remote' ? src.db : dst.db;
                var transaction = db.transaction([IDBFS.DB_STORE_NAME], 'readwrite');
                var store = transaction.objectStore(IDBFS.DB_STORE_NAME);

                function done(err) {
                if (err && !errored) {
                    errored = true;
                    return callback(err);
                }
                };

                transaction.onerror = (e) => {
                done(this.error);
                e.preventDefault();
                };

                transaction.oncomplete = (e) => {
                if (!errored) {
                    callback(null);
                }
                };

                // sort paths in ascending order so directory entries are created
                // before the files inside them
                create.sort().forEach((path) => {
                if (dst.type === 'local') {
                    IDBFS.loadRemoteEntry(store, path, (err, entry) => {
                    if (err) return done(err);
                    IDBFS.storeLocalEntry(path, entry, done);
                    });
                } else {
                    IDBFS.loadLocalEntry(path, (err, entry) => {
                    if (err) return done(err);
                    IDBFS.storeRemoteEntry(store, path, entry, done);
                    });
                }
                });

                // sort paths in descending order so files are deleted before their
                // parent directories
                remove.sort().reverse().forEach((path) => {
                if (dst.type === 'local') {
                    IDBFS.removeLocalEntry(path, done);
                } else {
                    IDBFS.removeRemoteEntry(store, path, done);
                }
                });
            }
        }

        FS.mkdir('/saves')
        FS.mount(IDBFS, {'root': '.'}, '/saves')
        FS.syncfs(true, (err) => {
            if (err) {console.log(err)}
            else {
                console.log('IndexedDB mounted and synced!')
                window.fs_loaded = true
            }
        })



        window.onbeforeunload = async ()=>{
            FS.syncfs(false, (err) => {console.log(err)})
        }
    """)

    while platform.window.fs_loaded is False: # pylint: disable=no-member
        print("Waiting for fs to load...")
        await asyncio.sleep(0.5)




    from scripts.housekeeping.log_cleanup import prune_logs
    from scripts.stream_duplexer import UnbufferedStreamDuplexer
    from scripts.datadir import get_log_dir, setup_data_dir
    from scripts.version import get_version_info, VERSION_NAME

    # directory = os.path.dirname(__file__)
    # if directory:
    #     os.chdir(directory)


    if os.path.exists("auto-updated"):
        print("Clangen starting, deleting auto-updated file")
        os.remove("auto-updated")
        shutil.rmtree("Downloads", ignore_errors=True)
        print("Update Complete!")
        print("New version: " + get_version_info().version_number)


    setup_data_dir()
    timestr = time.strftime("%Y%m%d_%H%M%S")


    stdout_file = open(get_log_dir() + f'/stdout_{timestr}.log', 'a')
    stderr_file = open(get_log_dir() + f'/stderr_{timestr}.log', 'a')
    sys.stdout = UnbufferedStreamDuplexer(sys.stdout, stdout_file)
    sys.stderr = UnbufferedStreamDuplexer(sys.stderr, stderr_file)

    # Setup logging
    import logging

    formatter = logging.Formatter(
        "%(name)s - %(levelname)s - %(filename)s / %(funcName)s / %(lineno)d - %(message)s"
        )


    # Logging for file
    timestr = time.strftime("%Y%m%d_%H%M%S")
    log_file_name = get_log_dir() + f"/clangen_{timestr}.log"
    file_handler = logging.FileHandler(log_file_name)
    file_handler.setFormatter(formatter)
    # Only log errors to file
    file_handler.setLevel(logging.ERROR)
    # Logging for console
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logging.root.addHandler(file_handler)
    logging.root.addHandler(stream_handler)


    prune_logs(logs_to_keep=5, retain_empty_logs=False)


    def log_crash(logtype, value, tb):
        """
        Log uncaught exceptions to file
        """
        logging.critical("Uncaught exception", exc_info=(logtype, value, tb))
        sys.__excepthook__(type, value, tb)

    sys.excepthook = log_crash

    # if user is developing in a github codespace
    if os.environ.get('CODESPACES'):
        print('')
        print("Github codespace user!!! Sorry, but sound *may* not work :(")
        print("SDL_AUDIODRIVER is dsl. This is to avoid ALSA errors, but it may disable sound.")
        print('')
        print("Web VNC:")
        print(
            f"https://{os.environ.get('CODESPACE_NAME')}-6080"
            + f".{os.environ.get('GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN')}"
            + "/?autoconnect=true&reconnect=true&password=clangen&resize=scale")
        print("(use clangen in fullscreen mode for best results)")
        print('')


    if get_version_info().is_source_build:
        print("Running on source code")
        if get_version_info().version_number == VERSION_NAME:
            print("Failed to get git commit hash, using hardcoded version number instead.")
            print("Hey testers! We recommend you use git to clone the repository, as it makes things easier for everyone.")  # pylint: disable=line-too-long
            print("There are instructions at https://discord.com/channels/1003759225522110524/1054942461178421289/1078170877117616169")  # pylint: disable=line-too-long
    else:
        print("Running on PyInstaller build")

    print("Version Name: ", VERSION_NAME)
    print("Running on commit " + get_version_info().version_number)

    # Load game
    from scripts.game_structure.load_cat import load_cats, version_convert
    from scripts.game_structure.windows import SaveCheck
    from scripts.game_structure.game_essentials import game, MANAGER, screen
    from scripts.game_structure.discord_rpc import _DiscordRPC
    from scripts.cat.sprites import sprites
    from scripts.clan import clan_class
    from scripts.utility import get_text_box_theme, quit, scale  # pylint: disable=redefined-builtin
    import pygame_gui
    import pygame




    # import all screens for initialization (Note - must be done after pygame_gui manager is created)
    from scripts.screens.all_screens import start_screen # pylint: disable=ungrouped-imports

    # P Y G A M E
    clock = pygame.time.Clock()
    pygame.display.set_icon(pygame.image.load('resources/images/icon.png'))

    # LOAD cats & clan
    clan_list = game.read_clans()
    if clan_list:
        game.switches['clan_list'] = clan_list
        try:
            load_cats()
            version_info = clan_class.load_clan()
            version_convert(version_info)
        except Exception as e:
            logging.exception("File failed to load")
            if not game.switches['error_message']:
                game.switches[
                    'error_message'] = 'There was an error loading the cats file!'
                game.switches['traceback'] = e


    # LOAD settings

    sprites.load_scars()

    start_screen.screen_switches()

    if game.settings['fullscreen']:
        version_number = pygame_gui.elements.UILabel(
            pygame.Rect((1500, 1350), (-1, -1)), get_version_info().version_number[0:8],
            object_id=get_text_box_theme())
        # Adjust position
        version_number.set_position(
            (1600 - version_number.get_relative_rect()[2] - 8,
             1400 - version_number.get_relative_rect()[3]))
    else:
        version_number = pygame_gui.elements.UILabel(
            pygame.Rect((700, 650), (-1, -1)), get_version_info().version_number[0:8],
            object_id=get_text_box_theme())
        # Adjust position
        version_number.set_position(
            (800 - version_number.get_relative_rect()[2] - 8,
            700 - version_number.get_relative_rect()[3]))

    if get_version_info().is_source_build or get_version_info().is_dev():
        dev_watermark = pygame_gui.elements.UILabel(
            scale(pygame.Rect((1050, 1321), (600, 100))),
            "Dev Build:",
            object_id="#dev_watermark"
        )


    cursor_img = pygame.image.load('resources/images/cursor.png').convert_alpha()
    cursor = pygame.cursors.Cursor((9,0), cursor_img)
    disabled_cursor = pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_ARROW)

    while True:
        time_delta = clock.tick(30) / 1000.0
        if game.switches['cur_screen'] not in ['start screen']:
            if game.settings['dark mode']:
                screen.fill((57, 50, 36))
            else:
                screen.fill((206, 194, 168))

        if game.settings['custom cursor']:
            if pygame.mouse.get_cursor() == disabled_cursor:
                pygame.mouse.set_cursor(cursor)
        elif pygame.mouse.get_cursor() == cursor:
            pygame.mouse.set_cursor(disabled_cursor)
        # Draw screens
        # This occurs before events are handled to stop pygame_gui buttons from blinking.
        game.all_screens[game.current_screen].on_use()

        # EVENTS
        for event in pygame.event.get():
            game.all_screens[game.current_screen].handle_event(event)

            if event.type == pygame.QUIT:
                # Dont display if on the start screen or there is no clan.
                if (game.switches['cur_screen'] in ['start screen',
                                                    'switch clan screen',
                                                    'settings screen',
                                                    'info screen',
                                                    'make clan screen']
                    or not game.clan):
                    quit(savesettings=False)
                else:
                    SaveCheck(game.switches['cur_screen'], False, None)


            # MOUSE CLICK
            if event.type == pygame.MOUSEBUTTONDOWN:
                game.clicked = True

            # F2 turns toggles visual debug mode for pygame_gui, allowed for easier bug fixes.
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F2:
                    if not MANAGER.visual_debug_active:
                        MANAGER.set_visual_debug_mode(True)
                    else:
                        MANAGER.set_visual_debug_mode(False)

            MANAGER.process_events(event)

        MANAGER.update(time_delta)

        # update
        game.update_game()
        if game.switch_screens:
            game.all_screens[game.last_screen_forupdate].exit_screen()
            game.all_screens[game.current_screen].screen_switches()
            game.switch_screens = False


        # END FRAME
        MANAGER.draw_ui(screen)

        pygame.display.update()
        await asyncio.sleep(0)

asyncio.run(main())