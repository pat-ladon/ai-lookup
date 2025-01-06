import random
import time
from dataclasses import asdict, dataclass
from typing import Callable, Literal

import mesop as me

# --- Import your new dialog components here ---
from dialog import dialog, dialog_actions

Role = Literal["user", "bot"]

_APP_TITLE = "Fancy Mesop Chat"
_BOT_AVATAR_LETTER = "M"
_EMPTY_CHAT_MESSAGE = "Get started with an example"
_EXAMPLE_USER_QUERIES = (
    "What is Mesop?",
    "Make me a chat app.",
    "How do I make a web component?",
)
_CHAT_MAX_WIDTH = "800px"
_MOBILE_BREAKPOINT = 640


@dataclass(kw_only=True)
class ChatMessage:
    """Chat message metadata."""

    role: Role = "user"
    content: str = ""
    edited: bool = False
    rating: int = 0  # +1 good, -1 bad, 0 none


@me.stateclass
class State:
    input: str
    output: list[ChatMessage]
    in_progress: bool
    sidebar_expanded: bool = False
    history: list[list[dict]]

    # Additional fields
    api_key: str = ""
    show_api_key_dialog: bool = False


def respond_to_chat(input: str, history: list[ChatMessage]):
    """A fake LLM that yields lines with small time delays."""
    lines = [
        "Mesop is a Python-based UI framework designed to simplify web UI development...",
        "It leverages Angular Material components, allowing rapid construction of web demos...",
        "With Mesop, developers can enjoy a fast build-edit-refresh loop...",
        "Deployment is straightforward via standard HTTP hosting...",
    ]
    for line in random.sample(lines, random.randint(2, len(lines))):
        time.sleep(0.3)
        yield line + " "


def on_load(e: me.LoadEvent):
    state = me.state(State)
    me.set_theme_mode("system")

    # If no API key has been set, open the dialog on load
    if not state.api_key:
        state.show_api_key_dialog = True
        print("API Key Dialog should be open now.")
        print("Current state:", state)


@me.page(
    title="Fancy Mesop Demo Chat",
    path="/fancy_chat",
    on_load=on_load,
)
def page():
    state = me.state(State)

    # Top-level layout container
    with me.box(
        style=me.Style(
            background=me.theme_var("surface-container-lowest"),
            display="flex",
            flex_direction="column",
            height="100%",
        )
    ):
        # Main row container
        with me.box(
            style=me.Style(
                display="flex",
                flex_direction="row",
                flex_grow=1,
                overflow="hidden",
            )
        ):
            # Sidebar
            with me.box(
                style=me.Style(
                    background=me.theme_var("surface-container-low"),
                    display="flex",
                    flex_direction="column",
                    flex_shrink=0,
                    position=(
                        "absolute" if state.sidebar_expanded and _is_mobile() else None
                    ),
                    height=(
                        "100%" if state.sidebar_expanded and _is_mobile() else None
                    ),
                    width=(300 if state.sidebar_expanded else None),
                    z_index=2000,
                )
            ):
                sidebar()

            # Right-side content (chat area)
            with me.box(
                style=me.Style(
                    display="flex",
                    flex_direction="column",
                    flex_grow=1,
                    padding=(
                        me.Padding(left=60)
                        if state.sidebar_expanded and _is_mobile()
                        else None
                    ),
                )
            ):
                header()

                # Scrollable chat
                with me.box(
                    style=me.Style(
                        flex_grow=1,
                        overflow_y="scroll",
                    )
                ):
                    if state.output:
                        chat_pane()
                    else:
                        examples_pane()

                chat_input()

    # =====================
    # The API Key Dialog
    # =====================
    api_key_dialog(is_open=state.show_api_key_dialog)


# -----------------------
#  The "API Key" Dialog
# -----------------------
def api_key_dialog(*, is_open: bool):
    state = me.state(State)

    # Use our new `dialog` component with content
    with dialog(is_open=is_open, on_click_background=on_click_api_key_dialog_cancel):
        me.text("Enter your API Key", type="headline-6")

        me.input(
            label="API Key",
            appearance="outline",
            value=state.api_key,
            on_blur=on_api_key_input_blur,
            style=me.Style(margin=me.Margin.symmetric(vertical=16)),
        )

        # Buttons row
        with dialog_actions():
            me.button("Cancel", type="flat", on_click=on_click_api_key_dialog_cancel)
            me.button(
                "Save",
                color="primary",
                type="flat",
                on_click=on_click_api_key_dialog_save,
            )


def on_api_key_input_blur(e: me.InputBlurEvent):
    """Capture typed text into the 'api_key' state field."""
    state = me.state(State)
    state.api_key = e.value


def on_click_api_key_dialog_cancel(e: me.ClickEvent):
    """Close the dialog without saving."""
    state = me.state(State)
    state.show_api_key_dialog = False


def on_click_api_key_dialog_save(e: me.ClickEvent):
    """Close the dialog after saving the input."""
    state = me.state(State)
    # The 'api_key' is already captured on blur.
    state.show_api_key_dialog = False


# --------------------------------------
# The rest of your chat & layout code
# --------------------------------------


def sidebar():
    state = me.state(State)
    with me.box(
        style=me.Style(
            display="flex",
            flex_direction="column",
            flex_grow=1,
        )
    ):
        with me.box(style=me.Style(display="flex", gap=20)):
            menu_icon(icon="menu", tooltip="Menu", on_click=on_click_menu_icon)
            if state.sidebar_expanded:
                me.text(
                    _APP_TITLE,
                    style=me.Style(margin=me.Margin(bottom=0, top=14)),
                    type="headline-6",
                )

        if state.sidebar_expanded:
            menu_item(icon="add", label="New chat", on_click=on_click_new_chat)
        else:
            menu_icon(icon="add", tooltip="New chat", on_click=on_click_new_chat)

        if state.sidebar_expanded:
            history_pane()


def history_pane():
    state = me.state(State)
    for index, chat in enumerate(state.history):
        with me.box(
            key=f"chat-{index}",
            on_click=on_click_history,
            style=me.Style(
                background=me.theme_var("surface-container"),
                border=me.Border.all(
                    me.BorderSide(
                        width=1, color=me.theme_var("outline-variant"), style="solid"
                    )
                ),
                border_radius=5,
                cursor="pointer",
                margin=me.Margin.symmetric(horizontal=10, vertical=10),
                padding=me.Padding.all(10),
                text_overflow="ellipsis",
            ),
        ):
            me.text(_truncate_text(chat[0]["content"]))


def header():
    state = me.state(State)
    with me.box(
        style=me.Style(
            align_items="center",
            background=me.theme_var("surface-container-lowest"),
            display="flex",
            gap=5,
            justify_content="space-between",
            padding=me.Padding.symmetric(horizontal=20, vertical=10),
        )
    ):
        with me.box(style=me.Style(display="flex", gap=5)):
            if not state.sidebar_expanded:
                me.text(
                    _APP_TITLE,
                    style=me.Style(margin=me.Margin(bottom=0)),
                    type="headline-6",
                )

        # Right side icons
        with me.box(style=me.Style(display="flex", gap=5)):
            icon_button(
                key="theme-switch",
                icon="dark_mode" if me.theme_brightness() == "light" else "light_mode",
                tooltip=(
                    "Dark mode" if me.theme_brightness() == "light" else "Light mode"
                ),
                on_click=on_click_theme_brightness,
            )


def examples_pane():
    with me.box(
        style=me.Style(
            margin=me.Margin.symmetric(horizontal="auto"),
            padding=me.Padding.all(15),
            width=f"min({_CHAT_MAX_WIDTH}, 100%)",
        )
    ):
        with me.box(style=me.Style(margin=me.Margin(top=25), font_size=24)):
            me.text(_EMPTY_CHAT_MESSAGE)

        with me.box(
            style=me.Style(
                display="flex",
                flex_direction="column" if _is_mobile() else "row",
                gap=20,
                margin=me.Margin(top=25),
            )
        ):
            for index, query in enumerate(_EXAMPLE_USER_QUERIES):
                with me.box(
                    key=f"query-{index}",
                    on_click=on_click_example_user_query,
                    style=me.Style(
                        background=me.theme_var("surface-container-highest"),
                        border_radius=15,
                        padding=me.Padding.all(20),
                        cursor="pointer",
                    ),
                ):
                    me.text(query)


def chat_pane():
    state = me.state(State)
    with me.box(
        style=me.Style(
            background=me.theme_var("surface-container-lowest"),
            color=me.theme_var("on-surface"),
            display="flex",
            flex_direction="column",
            margin=me.Margin.symmetric(horizontal="auto"),
            padding=me.Padding.all(15),
            width=f"min({_CHAT_MAX_WIDTH}, 100%)",
        )
    ):
        for index, msg in enumerate(state.output):
            if msg.role == "user":
                user_message(message=msg)
            else:
                bot_message(message_index=index, message=msg)

        # In-progress filler
        if state.in_progress:
            with me.box(key="scroll-to", style=me.Style(height=250)):
                pass


def user_message(*, message: ChatMessage):
    with me.box(
        style=me.Style(
            display="flex",
            gap=15,
            justify_content="end",
            margin=me.Margin.all(20),
        )
    ):
        with me.box(
            style=me.Style(
                background=me.theme_var("surface-container-low"),
                border_radius=10,
                color=me.theme_var("on-surface-variant"),
                padding=me.Padding.symmetric(vertical=0, horizontal=10),
                width="66%",
            )
        ):
            me.markdown(message.content)


def bot_message(*, message_index: int, message: ChatMessage):
    with me.box(style=me.Style(display="flex", gap=15, margin=me.Margin.all(20))):
        text_avatar(
            background=me.theme_var("primary"),
            color=me.theme_var("on-primary"),
            label=_BOT_AVATAR_LETTER,
        )
        with me.box(style=me.Style(display="flex", flex_direction="column")):
            me.markdown(
                message.content, style=me.Style(color=me.theme_var("on-surface"))
            )

            with me.box():
                icon_button(
                    key=f"thumb_up-{message_index}",
                    icon="thumb_up",
                    is_selected=(message.rating == 1),
                    tooltip="Good response",
                    on_click=on_click_thumb_up,
                )
                icon_button(
                    key=f"thumb_down-{message_index}",
                    icon="thumb_down",
                    is_selected=(message.rating == -1),
                    tooltip="Bad response",
                    on_click=on_click_thumb_down,
                )
                icon_button(
                    key=f"restart-{message_index}",
                    icon="restart_alt",
                    tooltip="Regenerate answer",
                    on_click=on_click_regenerate,
                )


def on_click_example_user_query(e: me.ClickEvent):
    state = me.state(State)
    _, example_index = e.key.split("-")
    state.input = _EXAMPLE_USER_QUERIES[int(example_index)]
    me.focus_component(key="chat_input")


def on_click_thumb_up(e: me.ClickEvent):
    state = me.state(State)
    _, msg_index = e.key.split("-")
    msg_index = int(msg_index)
    state.output[msg_index].rating = 1


def on_click_thumb_down(e: me.ClickEvent):
    state = me.state(State)
    _, msg_index = e.key.split("-")
    msg_index = int(msg_index)
    state.output[msg_index].rating = -1


def on_click_new_chat(e: me.ClickEvent):
    state = me.state(State)
    if state.output:
        state.history.insert(0, [asdict(m) for m in state.output])
    state.output = []
    me.focus_component(key="chat_input")


def on_click_history(e: me.ClickEvent):
    state = me.state(State)
    _, chat_index = e.key.split("-")
    chat_messages = [ChatMessage(**d) for d in state.history.pop(int(chat_index))]
    if state.output:
        state.history.insert(0, [asdict(m) for m in state.output])
    state.output = chat_messages
    me.focus_component(key="chat_input")


def on_click_theme_brightness(e: me.ClickEvent):
    if me.theme_brightness() == "light":
        me.set_theme_mode("dark")
    else:
        me.set_theme_mode("light")


def on_click_menu_icon(e: me.ClickEvent):
    state = me.state(State)
    state.sidebar_expanded = not state.sidebar_expanded


def on_chat_input(e: me.InputBlurEvent):
    state = me.state(State)
    state.input = e.value


def chat_input():
    """
    A helper function to render a text input area for chat messages.
    We add an additional icon that opens the API key dialog.
    """
    state = me.state(State)

    with me.box(
        style=me.Style(
            background=(
                me.theme_var("surface-container")
                if _is_mobile()
                else me.theme_var("surface-container")
            ),
            border_radius=16,
            display="flex",
            margin=me.Margin.symmetric(horizontal="auto", vertical=15),
            padding=me.Padding.all(8),
            width=f"min({_CHAT_MAX_WIDTH}, 90%)",
        )
    ):
        # The text area
        with me.box(style=me.Style(flex_grow=1)):
            me.native_textarea(
                autosize=True,
                key="chat_input",
                min_rows=4,
                on_blur=on_chat_input,
                shortcuts={
                    me.Shortcut(shift=True, key="Enter"): on_submit_chat_msg,
                },
                placeholder="Enter your prompt",
                style=me.Style(
                    background=(me.theme_var("surface-container")),
                    border=me.Border.all(me.BorderSide(style="none")),
                    color=me.theme_var("on-surface-variant"),
                    outline="none",
                    overflow_y="auto",
                    padding=me.Padding(top=16, left=16),
                    width="100%",
                ),
                value=state.input,
            )

        # Icon to open the API key dialog
        with me.content_button(
            type="icon",
            on_click=on_click_open_api_dialog,
        ):
            me.icon("vpn_key")  # Your custom icon for demonstration

        # Send button
        with me.content_button(
            disabled=state.in_progress,
            on_click=on_click_submit_chat_msg,
            type="icon",
        ):
            me.icon("send")


def on_click_open_api_dialog(e: me.ClickEvent):
    """Open the API Key dialog when user clicks the custom icon."""
    state = me.state(State)
    state.show_api_key_dialog = True


def on_click_submit_chat_msg(e: me.ClickEvent):
    yield from _submit_chat_msg()


def _submit_chat_msg():
    state = me.state(State)
    if state.in_progress or not state.input:
        return
    user_input = state.input
    state.input = ""
    yield

    output = state.output or []
    output.append(ChatMessage(role="user", content=user_input))
    state.in_progress = True
    me.scroll_into_view(key="scroll-to")
    yield

    start_time = time.time()
    response_chunks = respond_to_chat(user_input, state.output)
    bot_message_obj = ChatMessage(role="bot")
    output.append(bot_message_obj)
    state.output = output

    for chunk in response_chunks:
        bot_message_obj.content += chunk
        if (time.time() - start_time) >= 0.25:
            start_time = time.time()
            yield

    state.in_progress = False
    me.focus_component(key="chat_input")
    yield


def on_submit_chat_msg(e: me.TextareaShortcutEvent):
    state = me.state(State)
    state.input = e.value
    yield
    yield from _submit_chat_msg()


def on_click_regenerate(e: me.ClickEvent):
    state = me.state(State)
    _, msg_index = e.key.split("-")
    msg_index = int(msg_index)

    # The user message is the one before the bot message:
    user_msg = state.output[msg_index - 1]
    bot_msg = state.output[msg_index]
    bot_msg.content = ""
    state.in_progress = True
    yield

    start_time = time.time()
    output_chunk = respond_to_chat(user_msg.content, state.output[:msg_index])
    for text_chunk in output_chunk:
        bot_msg.content += text_chunk
        if (time.time() - start_time) >= 0.25:
            start_time = time.time()
            yield

    state.in_progress = False
    me.focus_component(key="chat_input")
    yield


def on_submit_chat_msg(e: me.TextareaShortcutEvent):
    state = me.state(State)
    state.input = e.value
    yield
    yield from _submit_chat_msg()


def _is_mobile():
    return me.viewport_size().width < _MOBILE_BREAKPOINT


def _truncate_text(text, char_limit=100):
    if len(text) <= char_limit:
        return text
    truncated = text[:char_limit].rsplit(" ", 1)[0]
    return truncated.rstrip(".,!?;:") + "..."


# -----------
# Components
# -----------
@me.component
def text_avatar(*, label: str, background: str, color: str):
    me.text(
        label,
        style=me.Style(
            background=background,
            border_radius="50%",
            color=color,
            font_size=20,
            height=40,
            line_height="1",
            margin=me.Margin(top=16),
            padding=me.Padding(top=10),
            text_align="center",
            width="40px",
        ),
    )


@me.component
def icon_button(
    *,
    icon: str,
    tooltip: str,
    key: str = "",
    is_selected: bool = False,
    on_click: Callable | None = None,
):
    selected_style = me.Style(
        background=me.theme_var("surface-container-low") if is_selected else None,
        color=me.theme_var("on-surface-variant") if is_selected else None,
    )
    with me.tooltip(message=tooltip):
        with me.content_button(
            type="icon", key=key, on_click=on_click, style=selected_style
        ):
            me.icon(icon)


@me.component
def menu_icon(
    *, icon: str, tooltip: str, key: str = "", on_click: Callable | None = None
):
    with me.tooltip(message=tooltip):
        with me.content_button(
            key=key,
            on_click=on_click,
            style=me.Style(margin=me.Margin.all(10)),
            type="icon",
        ):
            me.icon(icon)


@me.component
def menu_item(
    *, icon: str, label: str, key: str = "", on_click: Callable | None = None
):
    with me.box(on_click=on_click):
        with me.box(
            style=me.Style(
                background=me.theme_var("surface-container-high"),
                border_radius=20,
                cursor="pointer",
                display="inline-flex",
                gap=10,
                line_height=1,
                margin=me.Margin.all(10),
                padding=me.Padding(top=10, left=10, right=20, bottom=10),
            )
        ):
            me.icon(icon)
            me.text(label, style=me.Style(height=24, line_height="24px"))
