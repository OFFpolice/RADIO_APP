import os
import threading
import json

import flet as ft
import flet_audio as fta
from pyradios import RadioBrowser

BG = "#0b0f1a"
CARD = "#0f172a"
CARD2 = "#111827"
BORDER = "#1f2937"
ACCENT = "#3b82f6"
MUTED = "#8a8f9c"
FAVORITES_PATH = "/storage/emulated/0/Download/.radio_favorites.json"

CATEGORIES = [
    ("Все", ""),
    ("Pop", "pop"),
    ("Rock", "rock"),
    ("Jazz", "jazz"),
    ("Classical", "classical"),
    ("Electronic", "electronic"),
    ("Hip-Hop", "hip-hop"),
    ("R&B", "rnb"),
    ("Metal", "metal"),
    ("Country", "country"),
    ("Lofi", "lofi"),
    ("News", "news"),
    ("Talk", "talk"),
    ("Dance", "dance"),
    ("Reggae", "reggae"),
    ("Blues", "blues"),
    ("Soul", "soul"),
    ("Ambient", "ambient"),
    ("Chillout", "chillout"),
    ("Latin", "latin"),
]


def load_favorites() -> list[dict]:
    try:
        if os.path.exists(FAVORITES_PATH):
            with open(FAVORITES_PATH, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return []


def save_favorites(favs: list[dict]):
    try:
        os.makedirs(os.path.dirname(FAVORITES_PATH), exist_ok=True)
        with open(FAVORITES_PATH, "w") as f:
            json.dump(favs, f)
    except Exception:
        pass


def main(page: ft.Page):
    page.title = "RADIO APP"
    page.bgcolor = BG
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.scroll = ft.ScrollMode.AUTO

    rb = RadioBrowser()
    favorites: list[dict] = load_favorites()
    current_station: dict | None = None
    is_playing: list[bool] = [False]
    selected_category: list[str] = [""]
    current_page: list[int] = [0]

    def show_snackbar(msg: str):
        page.snack_bar = ft.SnackBar(ft.Text(msg), open=True)
        page.update()

    def is_fav(station: dict) -> bool:
        return any(
            f.get("stationuuid") == station.get("stationuuid") for f in favorites
        )

    def on_audio_state_change(e):
        state = str(e.data).lower() if hasattr(e, "data") and e.data else ""
        if state == "playing":
            is_playing[0] = True
            play_btn.icon = ft.Icons.PAUSE_CIRCLE
            page.update()
        elif state in ("stopped", "completed", "disposed", "idle"):
            is_playing[0] = False
            play_btn.icon = ft.Icons.PLAY_CIRCLE
            page.update()

    audio = fta.Audio(
        src="",
        autoplay=False,
        volume=1.0,
        on_state_change=on_audio_state_change,
    )
    page.overlay.append(audio)

    async def _play():
        await audio.play_async()

    async def _pause():
        await audio.pause_async()

    async def _resume():
        await audio.resume_async()

    async def _release():
        await audio.release_async()

    def toggle_favorite(station: dict):
        uuid = station.get("stationuuid")
        existing = next(
            (f for f in favorites if f.get("stationuuid") == uuid), None
        )
        if existing:
            favorites.remove(existing)
            show_snackbar("Удалено из избранного")
        else:
            favorites.insert(0, station)
            show_snackbar("Добавлено в избранное")
        save_favorites(favorites)
        if current_station and current_station.get("stationuuid") == uuid:
            player_fav_btn.icon = (
                ft.Icons.FAVORITE if is_fav(station) else ft.Icons.FAVORITE_BORDER
            )
            page.update()
        if current_page[0] == 1:
            show_favorites_page()

    def play_station(station: dict):
        nonlocal current_station
        url = station.get("url", "")
        if not url:
            show_snackbar("У станции нет URL потока")
            return
        current_station = station
        player_name.value = station.get("name", "—")
        parts = [
            p for p in [station.get("country", ""), station.get("codec", "")] if p
        ]
        player_sub.value = " · ".join(parts) if parts else "Онлайн"
        player_fav_btn.icon = (
            ft.Icons.FAVORITE if is_fav(station) else ft.Icons.FAVORITE_BORDER
        )
        play_btn.icon = ft.Icons.PAUSE_CIRCLE
        page.update()

        async def start():
            try:
                await _release()
                audio.src = url
                page.update()
                await _play()
            except Exception as ex:
                show_snackbar(f"Ошибка воспроизведения: {ex}")

        page.run_task(start)

    def toggle_play(e):
        if current_station is None:
            show_snackbar("Сначала выберите станцию")
            return

        async def run():
            try:
                if is_playing[0]:
                    await _pause()
                else:
                    await _resume()
            except Exception as ex:
                show_snackbar(f"Ошибка: {ex}")

        page.run_task(run)

    player_name = ft.Text(
        "Ничего не играет",
        size=13,
        weight="bold",
        no_wrap=True,
        expand=True,
    )
    player_sub = ft.Text(
        "Выберите станцию",
        size=11,
        color=MUTED,
        no_wrap=True,
        expand=True,
    )
    play_btn = ft.IconButton(
        icon=ft.Icons.PLAY_CIRCLE,
        icon_color=ACCENT,
        icon_size=32,
        on_click=toggle_play,
    )
    player_fav_btn = ft.IconButton(
        icon=ft.Icons.FAVORITE_BORDER,
        icon_color=ACCENT,
        icon_size=20,
        on_click=lambda e: toggle_favorite(current_station)
        if current_station
        else None,
    )

    player_bar = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.RADIO, color=ACCENT, size=24),
                ft.Column(
                    [player_name, player_sub],
                    spacing=2,
                    expand=True,
                ),
                player_fav_btn,
                ft.IconButton(
                    icon=ft.Icons.OPEN_IN_BROWSER,
                    icon_color=MUTED,
                    icon_size=20,
                    tooltip="Сайт станции",
                    on_click=lambda e: page.launch_url(current_station["homepage"])
                    if current_station and current_station.get("homepage")
                    else None,
                ),
                play_btn,
            ],
            spacing=8,
        ),
        padding=ft.padding.symmetric(horizontal=15, vertical=10),
        bgcolor=CARD,
        border=ft.border.only(top=ft.border.BorderSide(1, BORDER)),
    )

    def build_station_card(station: dict) -> ft.Container:
        name = station.get("name", "Без названия")
        country = station.get("country", "")
        language = station.get("language", "")
        codec = station.get("codec", "")
        tags = station.get("tags", "")
        tags_short = (
            ", ".join(t.strip() for t in tags.split(",")[:3] if t.strip())
            if tags
            else ""
        )
        meta_parts = [p for p in [country, language, codec] if p]
        meta_str = " · ".join(meta_parts)

        fav_icon = ft.IconButton(
            icon=ft.Icons.FAVORITE if is_fav(station) else ft.Icons.FAVORITE_BORDER,
            icon_color=ACCENT,
            icon_size=18,
        )

        def on_fav_click(e, s=station, btn=fav_icon):
            toggle_favorite(s)
            btn.icon = ft.Icons.FAVORITE if is_fav(s) else ft.Icons.FAVORITE_BORDER
            page.update()

        fav_icon.on_click = on_fav_click

        return ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        content=ft.Icon(ft.Icons.RADIO, color=ACCENT, size=22),
                        width=44,
                        height=44,
                        bgcolor=BORDER,
                        border_radius=22,
                        alignment=ft.Alignment(0, 0),
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                name,
                                size=13,
                                weight="bold",
                                no_wrap=True,
                                max_lines=1,
                            ),
                            ft.Text(
                                meta_str,
                                size=11,
                                color=MUTED,
                                no_wrap=True,
                                max_lines=1,
                            )
                            if meta_str
                            else ft.Container(height=0),
                            ft.Text(
                                tags_short,
                                size=10,
                                color="#4b5563",
                                no_wrap=True,
                                max_lines=1,
                            )
                            if tags_short
                            else ft.Container(height=0),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    fav_icon,
                    ft.IconButton(
                        icon=ft.Icons.PLAY_CIRCLE_OUTLINE,
                        icon_color=ACCENT,
                        icon_size=24,
                        on_click=lambda e, s=station: play_station(s),
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
            ft.Text("Станций не найдено"),
            ft.Text("Попробуйте другой запрос", size=12, color=MUTED),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
    stations_container = ft.Container(
        content=stations_loading,
        padding=20,
        alignment=ft.Alignment(0, 0),
    )

    def set_stations(items: list[dict]):
        stations_column.controls.clear()
        if items:
            for s in items:
                stations_column.controls.append(build_station_card(s))
            stations_container.content = stations_column
        else:
            stations_container.content = stations_empty
        page.update()

    def fetch_stations(query: str = "", tag: str = ""):
        stations_container.content = stations_loading
        page.update()

        def run():
            try:
                kwargs: dict = {
                    "limit": 50,
                    "order": "votes",
                    "reverse": True,
                    "hidebroken": True,
                }
                if query:
                    kwargs["name"] = query
                if tag:
                    kwargs["tag"] = tag
                results = rb.search(**kwargs)
                items = [dict(r) if not isinstance(r, dict) else r for r in results]
                page.call_from_thread(lambda i=items: set_stations(i))
            except Exception as ex:
                page.call_from_thread(
                    lambda: show_snackbar(f"Ошибка загрузки: {ex}")
                )
                page.call_from_thread(lambda: set_stations([]))

        threading.Thread(target=run, daemon=True).start()

    search_input = ft.TextField(
        hint_text="Поиск станций...",
        expand=True,
        bgcolor=CARD2,
        border_radius=12,
        border_color=BORDER,
        color="white",
        prefix_icon=ft.Icons.SEARCH,
        on_submit=lambda e: fetch_stations(
            query=e.control.value.strip(),
            tag=selected_category[0],
        ),
    )

    categories_row = ft.Row(scroll=ft.ScrollMode.AUTO, spacing=8)

    def build_category_chip(label: str, tag: str) -> ft.Container:
        active = selected_category[0] == tag

        def on_tap(e, t=tag):
            selected_category[0] = t
            rebuild_categories()
            fetch_stations(query=search_input.value.strip(), tag=t)

        return ft.Container(
            content=ft.Text(
                label,
                size=12,
                color="white" if active else MUTED,
                weight="bold" if active else "normal",
            ),
            padding=ft.padding.symmetric(horizontal=14, vertical=7),
            bgcolor=ACCENT if active else CARD2,
            border_radius=20,
            border=ft.border.all(1, ACCENT if active else BORDER),
            on_click=on_tap,
            ink=True,
        )

    def rebuild_categories():
        categories_row.controls.clear()
        for label, tag in CATEGORIES:
            categories_row.controls.append(build_category_chip(label, tag))
        page.update()

    search_page_content = ft.Column(
        [
            ft.Row(
                [
                    search_input,
                    ft.IconButton(
                        icon=ft.Icons.SEARCH,
                        icon_color="white",
                        bgcolor=ACCENT,
                        on_click=lambda e: fetch_stations(
                            query=search_input.value.strip(),
                            tag=selected_category[0],
                        ),
                    ),
                ],
                spacing=8,
            ),
            categories_row,
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Радиостанции", size=16, weight="bold"),
                        stations_container,
                    ]
                ),
                padding=15,
                border_radius=20,
                bgcolor=CARD,
            ),
        ],
        spacing=15,
    )

    fav_column = ft.Column(spacing=8)
    fav_empty = ft.Column(
        [
            ft.Icon(ft.Icons.FAVORITE_BORDER, size=50, color=ACCENT),
            ft.Text("Нет избранных"),
            ft.Text("Нажмите ♥ чтобы добавить станцию", size=12, color=MUTED),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
    fav_container = ft.Container(
        content=fav_empty,
        padding=20,
        alignment=ft.Alignment(0, 0),
    )
    fav_page_content = ft.Column(
        [
            ft.Container(
                content=ft.Column(
                    [ft.Text("Избранное", size=16, weight="bold"), fav_container]
                ),
                padding=15,
                border_radius=20,
                bgcolor=CARD,
            )
        ],
        spacing=15,
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

    def make_link(icon, label: str, url: str) -> ft.Container:
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(icon, color=ACCENT, size=20),
                    ft.Text(label, size=13, expand=True),
                    ft.Icon(ft.Icons.OPEN_IN_NEW, color=MUTED, size=16),
                ],
                spacing=12,
            ),
            padding=ft.padding.symmetric(horizontal=15, vertical=12),
            bgcolor=CARD2,
            border_radius=10,
            on_click=lambda e, u=url: page.launch_url(u),
            ink=True,
        )

    about_page_content = ft.Column(
        [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Container(
                                    content=ft.Icon(
                                        ft.Icons.RADIO, color="white", size=30
                                    ),
                                    width=64,
                                    height=64,
                                    bgcolor=ACCENT,
                                    border_radius=16,
                                    alignment=ft.Alignment(0, 0),
                                ),
                                ft.Column(
                                    [
                                        ft.Text(
                                            "RADIO APP", size=20, weight="bold"
                                        ),
                                        ft.Text(
                                            "by OFFpolice", size=12, color=MUTED
                                        ),
                                    ],
                                    spacing=2,
                                ),
                            ],
                            spacing=15,
                        ),
                        ft.Divider(color=BORDER),
                        ft.Text(
                            "RADIO APP — приложение для прослушивания интернет-радиостанций "
                            "со всего мира. Поиск по названию, фильтрация по жанру, "
                            "избранные станции.",
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
                        ft.Text("Разработчик", size=14, weight="bold"),
                        make_link(
                            ft.Icons.SEND,
                            "Telegram — @OFFpolice",
                            "https://t.me/OFFpolice",
                        ),
                        make_link(
                            ft.Icons.ALTERNATE_EMAIL,
                            "Twitter/X — @OFFpolice2077",
                            "https://x.com/OFFpolice2077",
                        ),
                        make_link(
                            ft.Icons.CAMERA_ALT,
                            "Instagram — @OFFpolice2077",
                            "https://instagram.com/OFFpolice2077",
                        ),
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

    body = ft.Container(expand=True)

    header = ft.Row(
        [
            ft.Row(
                [
                    ft.Text("RADIO", size=28, weight="bold", color=ACCENT),
                    ft.Text("APP", size=28, weight="bold"),
                ]
            )
        ],
        alignment=ft.MainAxisAlignment.START,
    )

    nav = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(
                icon=ft.Icons.RADIO_OUTLINED, label="Радио"
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.FAVORITE, label="Избранное"
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.INFO_OUTLINE, label="О нас"
            ),
        ],
        bgcolor=CARD,
        on_change=lambda e: show_page(e.control.selected_index),
    )

    def show_page(index: int):
        current_page[0] = index
        nav.selected_index = index
        if index == 0:
            body.content = search_page_content
        elif index == 1:
            show_favorites_page()
            body.content = fav_page_content
        elif index == 2:
            body.content = about_page_content
        page.update()

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
                        padding=ft.padding.only(left=20, right=20, top=20),
                        expand=True,
                    ),
                    player_bar,
                ],
                spacing=0,
                expand=True,
            ),
            expand=True,
        )
    )
    page.navigation_bar = nav
    rebuild_categories()
    show_page(0)
    fetch_stations()


ft.run(main, assets_dir="assets")