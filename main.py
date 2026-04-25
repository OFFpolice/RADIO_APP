import threading
import json
import os

import flet as ft
import flet_audio as fa
import flet_permission_handler as fph
from pyradios import RadioBrowser

BG    = "#0b0f1a"
CARD  = "#0f172a"
CARD2 = "#111827"
BORDER = "#1f2937"
ACCENT = "#3b82f6"
MUTED  = "#8a8f9c"

FAVORITES_PATH = "/storage/emulated/0/Download/.radio_favorites.json"

CATEGORIES = [
    ("Все",       ""),
    ("Pop",       "pop"),
    ("Rock",      "rock"),
    ("Jazz",      "jazz"),
    ("Classical", "classical"),
    ("Electronic","electronic"),
    ("Hip-Hop",   "hip-hop"),
    ("R&B",       "rnb"),
    ("Metal",     "metal"),
    ("Country",   "country"),
    ("Lofi",      "lofi"),
    ("News",      "news"),
    ("Talk",      "talk"),
    ("Dance",     "dance"),
    ("Reggae",    "reggae"),
    ("Blues",     "blues"),
    ("Soul",      "soul"),
    ("Ambient",   "ambient"),
    ("Chillout",  "chillout"),
    ("Latin",     "latin"),
]


# ──────────────────────────────────────────────
#  Favourites helpers
# ──────────────────────────────────────────────

def load_favorites() -> list:
    try:
        if os.path.exists(FAVORITES_PATH):
            with open(FAVORITES_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
    except Exception:
        pass
    return []


def save_favorites(favs: list):
    try:
        os.makedirs(os.path.dirname(FAVORITES_PATH), exist_ok=True)
        with open(FAVORITES_PATH, "w", encoding="utf-8") as f:
            json.dump(favs, f, ensure_ascii=False)
    except Exception:
        pass


# ──────────────────────────────────────────────
#  Main app
# ──────────────────────────────────────────────

def main(page: ft.Page):
    page.title = "RADIO APP"
    page.bgcolor = BG
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0

    # ── Audio player ──────────────────────────
    audio = fa.Audio(
        src="",
        autoplay=False,
        on_state_changed=lambda e: None,
    )
    page.overlay.append(audio)

    # ── Permissions (Android) ─────────────────
    ph = fph.PermissionHandler()
    page.overlay.append(ph)

    def request_permissions():
        try:
            ph.request_permission(fph.PermissionType.MICROPHONE)  # triggers audio focus
        except Exception:
            pass

    threading.Thread(target=request_permissions, daemon=True).start()

    # ── State ─────────────────────────────────
    rb = RadioBrowser()
    favorites: list = load_favorites()
    state = {
        "current_station": None,
        "is_playing": False,
        "current_page": 0,
        "selected_category": "",
    }

    # ── Snackbar ──────────────────────────────
    def show_snackbar(msg: str):
        page.snack_bar = ft.SnackBar(ft.Text(msg), open=True)
        page.update()

    # ── Favourites logic ──────────────────────
    def is_favorite(station: dict) -> bool:
        return any(
            f.get("stationuuid") == station.get("stationuuid")
            for f in favorites
        )

    def toggle_favorite(station: dict):
        uuid = station.get("stationuuid")
        existing = next((f for f in favorites if f.get("stationuuid") == uuid), None)
        if existing:
            favorites.remove(existing)
            show_snackbar("Удалено из избранного")
        else:
            favorites.insert(0, station)
            show_snackbar("Добавлено в избранное")
        save_favorites(favorites)
        refresh_current_page()

    # ── Player bar ────────────────────────────
    player_name = ft.Text(
        "Ничего не играет", size=13, weight="bold",
        no_wrap=True, expand=True, color="white",
    )
    player_sub = ft.Text(
        "Выберите станцию", size=11, color=MUTED,
        no_wrap=True, expand=True,
    )
    player_fav_btn = ft.IconButton(
        icon=ft.Icons.FAVORITE_BORDER,
        icon_color=ACCENT,
        icon_size=20,
    )
    player_play_btn = ft.IconButton(
        icon=ft.Icons.PLAY_CIRCLE,
        icon_color=ACCENT,
        icon_size=28,
    )

    def update_player():
        station = state["current_station"]
        if station is None:
            player_name.value = "Ничего не играет"
            player_sub.value  = "Выберите станцию"
            player_fav_btn.icon = ft.Icons.FAVORITE_BORDER
            player_play_btn.icon = ft.Icons.PLAY_CIRCLE
        else:
            player_name.value = station.get("name", "—")
            country = station.get("country", "")
            codec   = station.get("codec", "")
            parts   = [p for p in [country, codec] if p]
            player_sub.value  = " · ".join(parts) if parts else "—"
            player_fav_btn.icon = (
                ft.Icons.FAVORITE if is_favorite(station)
                else ft.Icons.FAVORITE_BORDER
            )
            player_play_btn.icon = (
                ft.Icons.PAUSE_CIRCLE if state["is_playing"]
                else ft.Icons.PLAY_CIRCLE
            )
        page.update()

    def on_fav_from_player(e):
        if state["current_station"]:
            toggle_favorite(state["current_station"])
            update_player()

    def on_play_pause(e):
        station = state["current_station"]
        if not station:
            return
        if state["is_playing"]:
            audio.pause()
            state["is_playing"] = False
        else:
            url = station.get("url_resolved") or station.get("url", "")
            if url:
                audio.src = url
                audio.play()
                state["is_playing"] = True
        update_player()

    player_fav_btn.on_click  = on_fav_from_player
    player_play_btn.on_click = on_play_pause

    player_bar = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.RADIO, color=ACCENT, size=26),
                ft.Column(
                    [player_name, player_sub],
                    spacing=2,
                    expand=True,
                ),
                player_fav_btn,
                player_play_btn,
                ft.IconButton(
                    icon=ft.Icons.OPEN_IN_BROWSER,
                    icon_color=MUTED,
                    icon_size=20,
                    tooltip="Сайт станции",
                    on_click=lambda e: (
                        page.launch_url(state["current_station"].get("homepage", ""))
                        if state["current_station"] and state["current_station"].get("homepage")
                        else None
                    ),
                ),
            ],
            spacing=8,
        ),
        padding=ft.padding.symmetric(horizontal=14, vertical=10),
        bgcolor=CARD,
        border=ft.border.only(top=ft.border.BorderSide(1, BORDER)),
    )

    # ── Station card ──────────────────────────
    def build_station_card(station: dict) -> ft.Container:
        name     = station.get("name", "Без названия")
        country  = station.get("country", "")
        language = station.get("language", "")
        codec    = station.get("codec", "")
        tags     = station.get("tags", "") or ""
        tags_short = ", ".join(
            t.strip() for t in tags.split(",")[:3] if t.strip()
        )

        def on_fav(e, s=station):
            toggle_favorite(s)
            # Refresh card icons in list
            refresh_current_page()

        def on_play(e, s=station):
            # Stop previous
            try:
                audio.pause()
            except Exception:
                pass

            state["current_station"] = s
            state["is_playing"] = True

            url = s.get("url_resolved") or s.get("url", "")
            if url:
                audio.src = url
                audio.play()
            update_player()
            show_snackbar(f"▶ {s.get('name', '')}")

        info_parts = [p for p in [country, language, codec] if p]
        info_str   = " · ".join(info_parts)

        fav = is_favorite(station)
        return ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        content=ft.Icon(ft.Icons.RADIO, color=ACCENT, size=22),
                        width=44,
                        height=44,
                        bgcolor=BORDER,
                        border_radius=22,
                        alignment=ft.alignment.center,
                    ),
                    ft.Column(
                        [
                            ft.Text(name, size=13, weight="bold",
                                    no_wrap=True, max_lines=1, color="white"),
                            ft.Text(info_str, size=11, color=MUTED,
                                    no_wrap=True, max_lines=1),
                            ft.Text(tags_short, size=10, color="#4b5563",
                                    no_wrap=True, max_lines=1)
                            if tags_short else ft.Container(height=0),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.FAVORITE if fav else ft.Icons.FAVORITE_BORDER,
                        icon_color=ACCENT,
                        icon_size=18,
                        on_click=on_fav,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.PLAY_CIRCLE_OUTLINE,
                        icon_color=ACCENT,
                        icon_size=24,
                        on_click=on_play,
                    ),
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=12, vertical=10),
            bgcolor=CARD2,
            border_radius=12,
            border=ft.border.all(1, BORDER),
        )

    # ── Stations list ─────────────────────────
    stations_column = ft.Column(spacing=8)
    stations_loading = ft.Row(
        [
            ft.ProgressRing(color=ACCENT, width=24, height=24),
            ft.Text("Загрузка...", color=MUTED),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
    )
    stations_empty = ft.Column(
        [
            ft.Icon(ft.Icons.RADIO_OUTLINED, size=50, color=ACCENT),
            ft.Text("Станций не найдено", color="white"),
            ft.Text("Попробуйте другой запрос", size=12, color=MUTED),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
    stations_container = ft.Container(
        content=stations_loading,
        padding=20,
        alignment=ft.alignment.center,
    )

    def set_stations(items: list):
        stations_column.controls.clear()
        if items:
            for s in items:
                stations_column.controls.append(build_station_card(s))
            stations_container.content = stations_column
        else:
            stations_container.content = stations_empty
        page.update()

    def set_loading():
        stations_container.content = stations_loading
        page.update()

    def fetch_stations(query: str = "", tag: str = ""):
        set_loading()

        def run():
            try:
                kwargs = {
                    "limit": 50,
                    "order": "votes",
                    "reverse": True,
                    "hidebroken": True,
                }
                if query:
                    kwargs["name"] = query
                if tag:
                    kwargs["tag"] = tag

                raw = rb.search(**kwargs)
                items = []
                for r in raw:
                    if isinstance(r, dict):
                        items.append(r)
                    else:
                        # pyradios may return namedtuple-like objects
                        try:
                            items.append(r._asdict())
                        except AttributeError:
                            items.append(vars(r))

                # page.run_thread is not available in 0.84 —
                # schedule UI update from background thread:
                def _update():
                    set_stations(items)
                page.invoke_method("__noop__")  # wake event loop (safe no-op)
                # Direct call is safe when page.update() is called inside:
                set_stations(items)
            except Exception as ex:
                def _err():
                    show_snackbar(f"Ошибка: {ex}")
                    set_stations([])
                _err()

        threading.Thread(target=run, daemon=True).start()

    # ── Search bar & categories ───────────────
    search_input = ft.TextField(
        hint_text="Поиск станций...",
        expand=True,
        bgcolor=CARD2,
        border_radius=12,
        border_color=BORDER,
        color="white",
        hint_style=ft.TextStyle(color=MUTED),
        prefix_icon=ft.Icons.SEARCH,
        on_submit=lambda e: fetch_stations(
            query=e.control.value.strip(),
            tag=state["selected_category"],
        ),
    )

    def on_search(e):
        fetch_stations(
            query=search_input.value.strip(),
            tag=state["selected_category"],
        )

    search_btn = ft.IconButton(
        icon=ft.Icons.SEARCH,
        icon_color="white",
        bgcolor=ACCENT,
        on_click=on_search,
    )

    categories_row = ft.Row(scroll=ft.ScrollMode.AUTO, spacing=8)

    def build_category_chip(label: str, tag: str) -> ft.Container:
        selected = state["selected_category"] == tag

        def on_tap(e, t=tag):
            state["selected_category"] = t
            rebuild_categories()
            fetch_stations(query=search_input.value.strip(), tag=t)

        return ft.Container(
            content=ft.Text(
                label,
                size=12,
                color="white" if selected else MUTED,
                weight="bold" if selected else "normal",
            ),
            padding=ft.padding.symmetric(horizontal=14, vertical=7),
            bgcolor=ACCENT if selected else CARD2,
            border_radius=20,
            border=ft.border.all(1, ACCENT if selected else BORDER),
            on_click=on_tap,
            ink=True,
        )

    def rebuild_categories():
        categories_row.controls.clear()
        for label, tag in CATEGORIES:
            categories_row.controls.append(build_category_chip(label, tag))
        page.update()

    # ── Pages ─────────────────────────────────
    search_page_content = ft.Column(
        [
            ft.Row([search_input, search_btn], spacing=8),
            categories_row,
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Радиостанции", size=16, weight="bold", color="white"),
                        stations_container,
                    ],
                    spacing=10,
                ),
                padding=15,
                border_radius=20,
                bgcolor=CARD,
            ),
        ],
        spacing=15,
        scroll=ft.ScrollMode.AUTO,
    )

    # ── Favourites page ───────────────────────
    fav_column = ft.Column(spacing=8)
    fav_empty = ft.Column(
        [
            ft.Icon(ft.Icons.FAVORITE_BORDER, size=50, color=ACCENT),
            ft.Text("Нет избранных", color="white"),
            ft.Text("Нажмите ♥ чтобы добавить станцию", size=12, color=MUTED),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
    fav_container = ft.Container(
        content=fav_empty,
        padding=20,
        alignment=ft.alignment.center,
    )
    fav_page_content = ft.Column(
        [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Избранное", size=16, weight="bold", color="white"),
                        fav_container,
                    ],
                    spacing=10,
                ),
                padding=15,
                border_radius=20,
                bgcolor=CARD,
            )
        ],
        spacing=15,
        scroll=ft.ScrollMode.AUTO,
    )

    def show_favorites_page():
        fav_column.controls.clear()
        if favorites:
            for s in favorites:
                fav_column.controls.append(build_station_card(s))
            fav_container.content = fav_column
        else:
            fav_container.content = fav_empty
        page.update()

    # ── About page ────────────────────────────
    about_page_content = ft.Column(
        [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Container(
                                    content=ft.Icon(ft.Icons.RADIO, color="white", size=30),
                                    width=64,
                                    height=64,
                                    bgcolor=ACCENT,
                                    border_radius=16,
                                    alignment=ft.alignment.center,
                                ),
                                ft.Column(
                                    [
                                        ft.Text("RADIO APP", size=20, weight="bold", color="white"),
                                        ft.Text("by OFFpolice", size=12, color=MUTED),
                                    ],
                                    spacing=2,
                                ),
                            ],
                            spacing=15,
                        ),
                        ft.Divider(color=BORDER),
                        ft.Text(
                            "RADIO APP — приложение для прослушивания интернет-радиостанций "
                            "со всего мира. Поиск по названию, фильтрация по жанру, избранные станции.",
                            size=13,
                            color=MUTED,
                        ),
                    ],
                    spacing=12,
                ),
                padding=15,
                border_radius=15,
                bgcolor=CARD,
                border=ft.border.all(1, BORDER),
            ),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Связь с разработчиком", size=14, weight="bold", color="white"),
                        _link_tile("Telegram — @OFFpolice",      "https://t.me/OFFpolice",           page),
                        _link_tile("X (Twitter) — @OFFpolice2077","https://x.com/OFFpolice2077",     page),
                        _link_tile("Instagram — @OFFpolice2077",  "https://instagram.com/OFFpolice2077", page),
                    ],
                    spacing=10,
                ),
                padding=15,
                border_radius=15,
                bgcolor=CARD,
                border=ft.border.all(1, BORDER),
            ),
        ],
        spacing=15,
        scroll=ft.ScrollMode.AUTO,
    )

    # ── Navigation ────────────────────────────
    body = ft.Container(expand=True)

    def refresh_current_page():
        idx = state["current_page"]
        if idx == 0:
            fetch_stations(
                query=search_input.value.strip(),
                tag=state["selected_category"],
            )
        elif idx == 1:
            show_favorites_page()

    def show_page(index: int):
        state["current_page"] = index
        nav.selected_index = index
        if index == 0:
            body.content = search_page_content
        elif index == 1:
            show_favorites_page()
            body.content = fav_page_content
        elif index == 2:
            body.content = about_page_content
        page.update()

    nav = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.RADIO_OUTLINED,  label="Радио"),
            ft.NavigationBarDestination(icon=ft.Icons.FAVORITE,         label="Избранное"),
            ft.NavigationBarDestination(icon=ft.Icons.INFO_OUTLINE,     label="О нас"),
        ],
        bgcolor=CARD,
        on_change=lambda e: show_page(e.control.selected_index),
    )
    page.navigation_bar = nav

    header = ft.Row(
        [
            ft.Text("RADIO", size=28, weight="bold", color=ACCENT),
            ft.Text("APP",   size=28, weight="bold", color="white"),
        ]
    )

    page.add(
        ft.SafeArea(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Column(
                            [header, body],
                            spacing=15,
                            expand=True,
                        ),
                        padding=20,
                        expand=True,
                    ),
                    player_bar,   # ← player bar внизу, над nav bar
                ],
                expand=True,
                spacing=0,
            ),
            expand=True,
        )
    )

    rebuild_categories()
    show_page(0)
    fetch_stations()


# ── Helper outside main ────────────────────────

def _link_tile(label: str, url: str, page: ft.Page) -> ft.Container:
    return ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.SEND, color="#3b82f6", size=20),
                ft.Text(label, size=13, expand=True, color="white"),
                ft.Icon(ft.Icons.OPEN_IN_NEW, color="#8a8f9c", size=16),
            ],
            spacing=12,
        ),
        padding=ft.padding.symmetric(horizontal=15, vertical=12),
        bgcolor="#111827",
        border_radius=10,
        on_click=lambda e, u=url: page.launch_url(u),
        ink=True,
    )


ft.app(target=main, assets_dir="assets")