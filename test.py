import threading
import json

import flet as ft
import flet_permission_handler as fph
from pyradios import RadioBrowser

FAVORITES_KEY = "favorites"
BG = "#0b0f1a"
CARD = "#0f172a"
CARD2 = "#111827"
BORDER = "#1f2937"
ACCENT = "#3b82f6"
MUTED = "#8a8f9c"

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
        import os
        path = "/storage/emulated/0/Download/.radio_favorites.json"
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return []


def save_favorites(favs: list[dict]):
    try:
        import os
        os.makedirs("/storage/emulated/0/Download", exist_ok=True)
        with open("/storage/emulated/0/Download/.radio_favorites.json", "w") as f:
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
    selected_category = [""]

    def show_snackbar(msg: str):
        page.snack_bar = ft.SnackBar(ft.Text(msg), open=True)
        page.update()

    def is_favorite(station: dict) -> bool:
        return any(f.get("stationuuid") == station.get("stationuuid") for f in favorites)

    def toggle_favorite(station: dict):
        uuid = station.get("stationuuid")
        existing = next((f for f in favorites if f.get("stationuuid") == uuid), None)
        if existing:
            favorites.remove(existing)
            show_snackbar(f"Удалено из избранного")
        else:
            favorites.insert(0, station)
            show_snackbar(f"Добавлено в избранное")
        save_favorites(favorites)
        refresh_current_page()

    def play_station(station: dict):
        nonlocal current_station
        current_station = station
        update_player(station)

    def update_player(station: dict | None):
        if station is None:
            player_name.value = "Ничего не играет"
            player_sub.value = "Выберите станцию"
            player_fav_btn.icon = ft.Icons.FAVORITE_BORDER
        else:
            player_name.value = station.get("name", "—")
            player_sub.value = f"{station.get('country', '')} · {station.get('codec', '')}".strip(" ·")
            player_fav_btn.icon = ft.Icons.FAVORITE if is_favorite(station) else ft.Icons.FAVORITE_BORDER
        page.update()

    def on_fav_from_player(e):
        if current_station:
            toggle_favorite(current_station)
            update_player(current_station)

    player_name = ft.Text("Ничего не играет", size=13, weight="bold", no_wrap=True, expand=True)
    player_sub = ft.Text("Выберите станцию", size=11, color=MUTED, no_wrap=True, expand=True)
    player_fav_btn = ft.IconButton(
        icon=ft.Icons.FAVORITE_BORDER,
        icon_color=ACCENT,
        icon_size=20,
        on_click=on_fav_from_player,
    )

    player_bar = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.RADIO, color=ACCENT, size=28),
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
                    on_click=lambda e: page.launch_url(current_station.get("homepage", "")) if current_station and current_station.get("homepage") else None,
                    tooltip="Сайт станции",
                ),
            ],
            spacing=10,
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
        tags_short = ", ".join(t.strip() for t in tags.split(",")[:3] if t.strip()) if tags else ""
        fav = is_favorite(station)

        def on_fav(e, s=station):
            toggle_favorite(s)

        def on_play(e, s=station):
            play_station(s)
            show_snackbar(f"▶ {s.get('name', '')}")

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
                            ft.Text(name, size=13, weight="bold", no_wrap=True, max_lines=1),
                            ft.Text(
                                f"{country}{' · ' + language if language else ''}{' · ' + codec if codec else ''}",
                                size=11,
                                color=MUTED,
                                no_wrap=True,
                                max_lines=1,
                            ),
                            ft.Text(tags_short, size=10, color="#4b5563", no_wrap=True, max_lines=1) if tags_short else ft.Container(height=0),
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

    stations_column = ft.Column(spacing=8)
    stations_loading = ft.Row(
        [ft.ProgressRing(color=ACCENT, width=24, height=24), ft.Text("Загрузка...", color=MUTED)],
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

    def set_loading_state(loading: bool):
        if loading:
            stations_container.content = stations_loading
            page.update()

    def fetch_stations(query: str = "", tag: str = ""):
        set_loading_state(True)

        def run():
            try:
                kwargs = {"limit": 50, "order": "votes", "reverse": True, "hidebroken": True}
                if query:
                    kwargs["name"] = query
                if tag:
                    kwargs["tag"] = tag
                results = rb.search(**kwargs)
                items = []
                for r in results:
                    d = dict(r) if not isinstance(r, dict) else r
                    items.append(d)
                page.call_from_thread(lambda i=items: set_stations(i))
            except Exception as ex:
                page.call_from_thread(lambda: show_snackbar(f"Ошибка: {ex}"))
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
        on_submit=lambda e: fetch_stations(query=e.control.value.strip(), tag=selected_category[0]),
    )

    def on_search(e):
        fetch_stations(query=search_input.value.strip(), tag=selected_category[0])

    search_btn = ft.IconButton(
        icon=ft.Icons.SEARCH,
        icon_color="white",
        bgcolor=ACCENT,
        on_click=on_search,
    )

    def build_category_chip(label: str, tag: str) -> ft.Container:
        selected = selected_category[0] == tag

        def on_tap(e, t=tag):
            selected_category[0] = t
            rebuild_categories()
            fetch_stations(query=search_input.value.strip(), tag=t)

        return ft.Container(
            content=ft.Text(label, size=12, color="white" if selected else MUTED, weight="bold" if selected else "normal"),
            padding=ft.padding.symmetric(horizontal=14, vertical=7),
            bgcolor=ACCENT if selected else CARD2,
            border_radius=20,
            border=ft.border.all(1, ACCENT if selected else BORDER),
            on_click=on_tap,
            ink=True,
        )

    categories_row = ft.Row(
        scroll=ft.ScrollMode.AUTO,
        spacing=8,
    )

    def rebuild_categories():
        categories_row.controls.clear()
        for label, tag in CATEGORIES:
            categories_row.controls.append(build_category_chip(label, tag))
        page.update()

    def refresh_current_page():
        if current_page[0] == 0:
            fetch_stations(query=search_input.value.strip(), tag=selected_category[0])
        elif current_page[0] == 1:
            show_favorites_page()
        page.update()

    search_page_content = ft.Column(
        [
            ft.Row([search_input, search_btn], spacing=8),
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
                content=ft.Column([ft.Text("Избранное", size=16, weight="bold"), fav_container]),
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
                                    alignment=ft.Alignment(0, 0),
                                ),
                                ft.Column(
                                    [
                                        ft.Text("RADIO APP", size=20, weight="bold"),
                                        ft.Text("by OFFpolice", size=12, color=MUTED),
                                    ],
                                    spacing=2,
                                ),
                            ],
                            spacing=15,
                        ),
                        ft.Divider(color=BORDER),
                        ft.Text(
                            "RADIO APP — приложение для прослушивания интернет-радиостанций со всего мира. "
                            "Поиск по названию, фильтрация по жанру, избранные станции.",
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
                        ft.Text("Связь с разработчиком", size=14, weight="bold"),
                        ft.Container(
                            content=ft.Row(
                                [ft.Icon(ft.Icons.SEND, color=ACCENT, size=20), ft.Text("Telegram — @OFFpolice", size=13, expand=True), ft.Icon(ft.Icons.OPEN_IN_NEW, color=MUTED, size=16)],
                                spacing=12,
                            ),
                            padding=ft.padding.symmetric(horizontal=15, vertical=12),
                            bgcolor=CARD2,
                            border_radius=10,
                            on_click=lambda e: page.launch_url("https://t.me/OFFpolice"),
                            ink=True,
                        ),
                        ft.Container(
                            content=ft.Row(
                                [ft.Icon(ft.Icons.SEND, color=ACCENT, size=20), ft.Text("X (Twitter) — @OFFpolice2077", size=13, expand=True), ft.Icon(ft.Icons.OPEN_IN_NEW, color=MUTED, size=16)],
                                spacing=12,
                            ),
                            padding=ft.padding.symmetric(horizontal=15, vertical=12),
                            bgcolor=CARD2,
                            border_radius=10,
                            on_click=lambda e: page.launch_url("https://x.com/OFFpolice2077"),
                            ink=True,
                        ),
                        ft.Container(
                            content=ft.Row(
                                [ft.Icon(ft.Icons.SEND, color=ACCENT, size=20), ft.Text("Instagram — @OFFpolice2077", size=13, expand=True), ft.Icon(ft.Icons.OPEN_IN_NEW, color=MUTED, size=16)],
                                spacing=12,
                            ),
                            padding=ft.padding.symmetric(horizontal=15, vertical=12),
                            bgcolor=CARD2,
                            border_radius=10,
                            on_click=lambda e: page.launch_url("https://instagram.com/OFFpolice2077"),
                            ink=True,
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

    current_page = [0]
    body = ft.Container(expand=True)

    header_title = ft.Row(
        [
            ft.Text("RADIO", size=28, weight="bold", color=ACCENT),
            ft.Text("APP", size=28, weight="bold"),
        ]
    )
    header = ft.Row([header_title], alignment=ft.MainAxisAlignment.START)

    nav = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.RADIO_OUTLINED, label="Радио"),
            ft.NavigationBarDestination(icon=ft.Icons.FAVORITE, label="Избранное"),
            ft.NavigationBarDestination(icon=ft.Icons.INFO_OUTLINE, label="О нас"),
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

    content = ft.SafeArea(
        content=ft.Container(
            content=ft.Column(
                [header, body],
                spacing=15,
                expand=True,
            ),
            padding=20,
            expand=True,
        )
    )

    page.add(content)
    page.navigation_bar = nav
    rebuild_categories()
    show_page(0)
    fetch_stations()


ft.run(main, assets_dir="assets")