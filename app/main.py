#!/usr/bin/env python3

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib, Gdk, GObject, Gio, Pango
import subprocess
import threading
import json
import urllib.request
import re
import os
from datetime import datetime


class GlassDrop(Adw.Application):

    def __init__(self):
        super().__init__(application_id="com.milas.GlassDrop")
        self.connect("activate", self.on_activate)
        self.fetch_token = 0
        self.download_process = None
        self.is_downloading = False
        self.current_url = ""
        self.current_title = ""
        self.formats_all = []
        self.formats = []
        self.dropdown_format_ids = []
        self.video_format_ids = []
        self.audio_format_id = None
        self.preset_options = []
        self.queue = []
        self.history = []
        self.speed_limit = None

    def on_activate(self, app):

        self.win = Adw.ApplicationWindow(application=app)
        self.win.set_default_size(820, 750)
        self.win.set_title("GlassDrop")

        icon_dir = os.path.join(os.path.dirname(__file__), "assets")
        icon_theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
        icon_theme.add_search_path(icon_dir)
        self.win.set_icon_name("com.milas.GlassDrop")

        self.style_manager = Adw.StyleManager.get_default()
        self.load_css()

        toolbar_view = Adw.ToolbarView()
        header = Adw.HeaderBar()

        menu_model = self.build_menu_model()
        self.install_actions()

        menu_button = Gtk.MenuButton()
        menu_button.add_css_class("logo-menu-button")
        menu_button.set_icon_name("open-menu-symbolic")
        menu_button.set_menu_model(menu_model)
        menu_button.set_tooltip_text("Menu")

        header.set_title_widget(Gtk.Label(label="GlassDrop"))
        header.pack_end(menu_button)
        toolbar_view.add_top_bar(header)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        content.set_margin_top(40)
        content.set_margin_bottom(40)
        content.set_margin_start(40)
        content.set_margin_end(40)
        content.add_css_class("frost-card")
        content.add_css_class("content-wrap")

        # URL Entry (AUTO FETCH)
        self.url_entry = Gtk.Entry()
        self.url_entry.set_placeholder_text("Paste YouTube URL and press Enter...")
        self.url_entry.add_css_class("glass-input")
        self.url_entry.set_hexpand(True)
        self.url_entry.set_has_frame(False)
        self.url_entry.connect("activate", self.fetch_info)

        self.paste_button = Gtk.Button(label="Paste")
        self.paste_button.add_css_class("paste-button")
        self.paste_button.connect("clicked", self.on_paste_clicked)

        self.url_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.url_row.add_css_class("url-row")
        self.url_row.set_hexpand(True)
        self.url_row.append(self.url_entry)
        self.url_row.append(self.paste_button)

        # Thumbnail Container
        self.thumb_container = Gtk.Box()
        self.thumb_container.set_halign(Gtk.Align.CENTER)
        self.thumb_container.add_css_class("thumb-frame")

        self.thumb_frame = Gtk.AspectFrame()
        self.thumb_frame.set_ratio(16 / 9)
        self.thumb_frame.set_obey_child(False)
        self.thumb_frame.set_size_request(520, 292)
        self.thumb_frame.set_halign(Gtk.Align.CENTER)
        self.thumb_frame.set_valign(Gtk.Align.CENTER)

        self.thumbnail = Gtk.Picture()
        self.thumbnail.set_content_fit(Gtk.ContentFit.CONTAIN)
        self.thumbnail.set_can_shrink(True)
        self.thumbnail.set_halign(Gtk.Align.CENTER)
        self.thumbnail.set_valign(Gtk.Align.CENTER)
        self.thumbnail.add_css_class("thumb-preview")

        self.thumb_frame.set_child(self.thumbnail)

        self.thumb_loading_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.thumb_loading_box.set_halign(Gtk.Align.CENTER)
        self.thumb_loading_box.set_valign(Gtk.Align.CENTER)
        self.thumb_loading_box.add_css_class("thumb-loading")

        self.thumb_skeleton = Gtk.Box()
        self.thumb_skeleton.add_css_class("thumb-skeleton")
        self.thumb_skeleton.set_size_request(520, 292)
        self.thumb_loading_label = Gtk.Label(label="Loading thumbnail...")
        self.thumb_loading_box.append(self.thumb_skeleton)
        self.thumb_loading_box.append(self.thumb_loading_label)
        self.thumb_loading_box.set_visible(False)

        self.thumb_overlay = Gtk.Overlay()
        self.thumb_overlay.set_child(self.thumb_frame)
        self.thumb_overlay.add_overlay(self.thumb_loading_box)

        self.thumb_container.append(self.thumb_overlay)

        # Title
        self.title_label = Gtk.Label()
        self.title_label.set_wrap(True)
        self.title_label.set_justify(Gtk.Justification.CENTER)
        self.title_label.set_max_width_chars(70)

        # Presets
        self.presets_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.presets_row.add_css_class("preset-row")
        self.presets_label = Gtk.Label(label="Preset")
        self.presets_label.set_xalign(0.0)
        self.presets_dropdown = Gtk.DropDown.new_from_strings(["Selected format"])
        self.presets_dropdown.connect("notify::selected", self.on_preset_changed)
        self.presets_row.append(self.presets_label)
        self.presets_row.append(self.presets_dropdown)
        self.presets_row.set_sensitive(False)
        self.presets_row.set_hexpand(True)
        self.presets_dropdown.set_hexpand(True)

        # Format Dropdown
        self.format_dropdown = Gtk.DropDown.new_from_strings(["No formats loaded"])
        self.formats = []

        # Speed Limit
        self.speed_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.speed_row.add_css_class("speed-row")
        self.speed_label = Gtk.Label(label="Speed Limit")
        self.speed_label.set_xalign(0.0)
        self.speed_dropdown = Gtk.DropDown.new_from_strings(
            ["No limit", "1M", "2M", "5M"]
        )
        self.speed_dropdown.connect("notify::selected", self.on_speed_changed)
        self.speed_row.append(self.speed_label)
        self.speed_row.append(self.speed_dropdown)
        self.speed_row.set_hexpand(True)
        self.speed_dropdown.set_hexpand(True)

        # Download Button
        self.download_button = Gtk.Button(label="Download")
        self.download_button.add_css_class("glass-button")
        self.download_button.connect("clicked", self.start_download)
        self.download_button.set_sensitive(False)

        # Progress
        self.progress = Gtk.ProgressBar()
        self.status_label = Gtk.Label(label="Idle")

        # Queue + History
        self.queue_label = Gtk.Label(label="Queue")
        self.queue_label.set_xalign(0.0)
        self.queue_list = Gtk.ListBox()
        self.queue_list.add_css_class("queue-list")
        self.queue_list.set_selection_mode(Gtk.SelectionMode.NONE)

        self.history_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.history_label = Gtk.Label(label="History")
        self.history_label.set_xalign(0.0)
        self.history_label.set_hexpand(True)
        self.history_clear_button = Gtk.Button(label="Clear")
        self.history_clear_button.add_css_class("history-clear")
        self.history_clear_button.connect("clicked", self.clear_history)
        self.history_row.append(self.history_label)
        self.history_row.append(self.history_clear_button)

        self.history_list = Gtk.ListBox()
        self.history_list.add_css_class("history-list")
        self.history_list.set_selection_mode(Gtk.SelectionMode.NONE)

        content.append(self.url_row)
        content.append(self.thumb_container)
        content.append(self.title_label)
        content.append(self.presets_row)
        content.append(self.format_dropdown)
        content.append(self.speed_row)
        content.append(self.download_button)
        content.append(self.progress)
        content.append(self.status_label)
        content.append(self.queue_label)
        content.append(self.queue_list)
        content.append(self.history_row)
        content.append(self.history_list)

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroller.set_child(content)

        self.toast_overlay = Adw.ToastOverlay()
        self.toast_overlay.set_child(scroller)
        toolbar_view.set_content(self.toast_overlay)
        self.add_drop_target()
        self.add_key_controller()
        self.win.set_content(toolbar_view)
        self.win.present()
        self.check_clipboard_on_start()
        self.show_disclaimer()

    def yt_dlp_base_cmd(self):
        # In Flatpak, run yt-dlp from host system to avoid bundling/network issues.
        if os.environ.get("FLATPAK_ID"):
            return ["flatpak-spawn", "--host", "yt-dlp"]
        return ["yt-dlp"]

    def build_menu_model(self):
        menu = Gio.Menu()

        main_section = Gio.Menu()
        main_section.append("Donate via UPI", "app.donate")
        main_section.append("Credits", "app.credits")
        main_section.append("License", "app.license")
        main_section.append("Supported Sites", "app.supported_sites")
        main_section.append("Check for Updates", "app.check_updates")
        menu.append_section(None, main_section)

        return menu

    def show_disclaimer(self):
        config_dir = os.path.join(GLib.get_user_config_dir(), "glassdrop")
        os.makedirs(config_dir, exist_ok=True)
        flag_path = os.path.join(config_dir, "disclaimer.ok")
        if os.path.exists(flag_path):
            return

        dialog = Adw.MessageDialog.new(self.win, "Disclaimer", None)
        disclaimer_label = Gtk.Label(
            label=(
                "This app is for downloading content you own or have permission to use.\n\n"
                "If you decide copyright laws are “optional,” that’s your decision and your consequences.\n\n"
                "The developer made the app. What you do with it is on you."
            )
        )
        disclaimer_label.set_wrap(True)
        disclaimer_label.set_xalign(0.0)
        disclaimer_label.set_justify(Gtk.Justification.LEFT)
        dialog.add_response("ok", "I Understand")
        dialog.set_default_response("ok")
        dialog.set_close_response("ok")
        dialog.set_response_enabled("ok", False)

        check = Gtk.CheckButton(label="I agree to behave like a responsible human.")

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.append(disclaimer_label)
        box.append(check)
        dialog.set_extra_child(box)

        def on_toggle(_btn):
            dialog.set_response_enabled("ok", check.get_active())

        check.connect("toggled", on_toggle)
        def on_response(_dlg, response):
            if response == "ok" and check.get_active():
                try:
                    with open(flag_path, "w", encoding="utf-8") as f:
                        f.write("ok")
                except Exception:
                    pass
        dialog.connect("response", on_response)
        dialog.present()

    def install_actions(self):
        self._add_action("donate", self.on_donate)
        self._add_action("credits", self.on_credits)
        self._add_action("license", self.on_license)
        self._add_action("supported_sites", self.on_supported_sites)
        self._add_action("check_updates", self.on_check_updates)

    def _add_action(self, name, callback):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)

    def on_donate(self, _action, _param):
        upi_id = "7868050070@superyes"
        payee = GLib.uri_escape_string("GlassDrop", None, False)
        uri = f"upi://pay?pa={upi_id}&pn={payee}&cu=INR"
        dialog = Adw.MessageDialog.new(self.win, "Support GlassDrop", None)
        dialog.set_body(
            "Scan the QR code with any UPI app or use the UPI ID below.\n"
            f"{upi_id}"
        )

        qr_path = os.path.join(os.path.dirname(__file__), "assets", "Donation.png")
        if os.path.exists(qr_path):
            qr_image = Gtk.Image.new_from_file(qr_path)
            qr_image.set_pixel_size(220)
            qr_image.set_halign(Gtk.Align.CENTER)
            qr_image.set_valign(Gtk.Align.CENTER)
            qr_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            qr_box.set_halign(Gtk.Align.CENTER)
            qr_box.append(qr_image)
            dialog.set_extra_child(qr_box)

        dialog.add_response("copy", "Copy UPI ID")
        dialog.add_response("ok", "OK")
        dialog.set_default_response("ok")
        dialog.set_close_response("ok")

        def on_response(_dlg, response):
            if response == "copy":
                clipboard = Gdk.Display.get_default().get_clipboard()
                clipboard.set(upi_id)
        dialog.connect("response", on_response)
        dialog.present()

    def on_credits(self, _action, _param):
        dialog = Adw.MessageDialog.new(self.win, "Credits", None)
        credits_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        credits_box.set_halign(Gtk.Align.CENTER)

        logo_path = os.path.join(os.path.dirname(__file__), "assets", "GlassDrop.png")
        if os.path.exists(logo_path):
            logo = Gtk.Image.new_from_file(logo_path)
            logo.set_pixel_size(110)
            credits_box.append(logo)

        credits_label = Gtk.Label()
        credits_label.set_use_markup(True)
        credits_label.set_wrap(True)
        credits_label.set_justify(Gtk.Justification.CENTER)
        credits_label.set_xalign(0.5)
        credits_label.set_markup(
            "<b>Built by</b> "
            "<a href=\"https://github.com/Killersparrow1\">Milas</a>\n"
            "<b>Powered by</b> "
            "<a href=\"https://github.com/yt-dlp/yt-dlp\">yt-dlp</a>\n"
            "<b>Assisted by</b> "
            "<a href=\"https://github.com/openai/codex\">Codex</a>\n"
            "<b>Supported sites</b> "
            "<a href=\"https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md\">List</a>"
        )
        credits_box.append(credits_label)
        dialog.set_extra_child(credits_box)
        dialog.add_response("ok", "OK")
        dialog.set_default_response("ok")
        dialog.set_close_response("ok")
        dialog.present()

    def on_license(self, _action, _param):
        dialog = Adw.MessageDialog.new(self.win, "License (MIT)", None)

        license_text = (
            "MIT License\n\n"
            "Copyright (c) 2026 Milas\n\n"
            "Permission is hereby granted, free of charge, to any person obtaining a copy "
            "of this software and associated documentation files (the \"Software\"), to deal "
            "in the Software without restriction, including without limitation the rights "
            "to use, copy, modify, merge, publish, distribute, sublicense, and/or sell "
            "copies of the Software, and to permit persons to whom the Software is "
            "furnished to do so, subject to the following conditions:\n\n"
            "The above copyright notice and this permission notice shall be included in all "
            "copies or substantial portions of the Software.\n\n"
            "THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR "
            "IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, "
            "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE "
            "AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER "
            "LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, "
            "OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE."
        )

        label = Gtk.Label(label=license_text)
        label.set_wrap(True)
        label.set_selectable(True)
        label.set_xalign(0.0)
        label.add_css_class("license-text")

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroller.set_min_content_height(260)
        scroller.set_child(label)

        dialog.set_extra_child(scroller)
        dialog.add_response("ok", "OK")
        dialog.set_default_response("ok")
        dialog.set_close_response("ok")
        dialog.present()

    def on_supported_sites(self, _action, _param):
        dialog = Adw.MessageDialog.new(self.win, "Supported Sites", None)

        text_view = Gtk.TextView()
        text_view.set_editable(False)
        text_view.set_cursor_visible(False)
        text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        text_view.add_css_class("license-text")

        buffer = text_view.get_buffer()
        buffer.set_text("Loading supported sites list...\n")

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroller.set_min_content_height(300)
        scroller.set_child(text_view)

        dialog.set_extra_child(scroller)
        dialog.add_response("ok", "OK")
        dialog.set_default_response("ok")
        dialog.set_close_response("ok")
        dialog.present()

        def load_list():
            url = "https://raw.githubusercontent.com/yt-dlp/yt-dlp/refs/heads/master/supportedsites.md"
            cache_dir = os.path.join(GLib.get_user_cache_dir(), "glassdrop")
            os.makedirs(cache_dir, exist_ok=True)
            cache_path = os.path.join(cache_dir, "supportedsites.txt")
            cache_date_path = os.path.join(cache_dir, "supportedsites.date")
            today = datetime.now().strftime("%Y-%m-%d")

            def read_cache():
                try:
                    with open(cache_path, "r", encoding="utf-8") as f:
                        return f.read()
                except Exception:
                    return None

            def read_cache_date():
                try:
                    with open(cache_date_path, "r", encoding="utf-8") as f:
                        return f.read().strip()
                except Exception:
                    return None

            cached_date = read_cache_date()
            if cached_date == today:
                cached_text = read_cache()
                if cached_text:
                    def apply_cached():
                        buffer.set_text(cached_text)
                        return False
                    GLib.idle_add(apply_cached)
                    return

            try:
                with urllib.request.urlopen(url, timeout=10) as resp:
                    raw = resp.read().decode("utf-8", errors="replace")
            except Exception:
                raw = "Failed to load supported sites list. Check your connection."

            def clean_markdown(text):
                lines = []
                for line in text.splitlines():
                    line = line.strip()
                    if not line:
                        lines.append("")
                        continue
                    if line.startswith("#"):
                        line = line.lstrip("#").strip()
                    if line.startswith(("- ", "* ")):
                        line = line[2:].strip()
                    line = re.sub(r"\[(.+?)\]\((.+?)\)", r"\1", line)
                    line = line.replace("**", "").replace("`", "")
                    lines.append(line)
                return "\n".join(lines).strip()

            text = clean_markdown(raw)
            try:
                with open(cache_path, "w", encoding="utf-8") as f:
                    f.write(text)
                with open(cache_date_path, "w", encoding="utf-8") as f:
                    f.write(today)
            except Exception:
                pass

            def apply_text():
                buffer.set_text(text)
                return False

            GLib.idle_add(apply_text)

        threading.Thread(target=load_list, daemon=True).start()

    def on_check_updates(self, _action, _param):
        url = "https://github.com/Killersparrow1/GlassDrop"
        Gio.AppInfo.launch_default_for_uri(url)

    def set_thumb_loading(self, loading):
        if loading:
            self.thumbnail.remove_css_class("thumb-loaded")
            self.thumb_loading_box.set_visible(True)
        else:
            self.thumb_loading_box.set_visible(False)
            self.thumbnail.add_css_class("thumb-loaded")

    def load_css(self):
        # Flatpak should use runtime theme defaults to avoid host theme/compositor quirks.
        if os.environ.get("FLATPAK_ID"):
            return
        css_path = os.path.join(os.path.dirname(__file__), "ui", "style.css")
        if not os.path.exists(css_path):
            return
        provider = Gtk.CssProvider()
        try:
            provider.load_from_path(css_path)
        except GLib.Error:
            return
        display = Gdk.Display.get_default()
        if display:
            Gtk.StyleContext.add_provider_for_display(
                display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

    def check_clipboard_on_start(self):
        display = Gdk.Display.get_default()
        if not display:
            return
        clipboard = display.get_clipboard()
        clipboard.read_text_async(None, self.on_clipboard_start_text)

    def on_clipboard_start_text(self, clipboard, result):
        try:
            text = clipboard.read_text_finish(result)
        except GLib.Error:
            return
        if not text:
            return
        url = text.strip()
        if not url.startswith("http"):
            return
        toast = Adw.Toast.new("Use clipboard URL?")
        toast.set_button_label("Use")

        def on_use(_toast):
            self.url_entry.set_text(url)
            self.fetch_info(self.url_entry)

        toast.connect("button-clicked", on_use)
        self.toast_overlay.add_toast(toast)


    def on_speed_changed(self, _dropdown, _param):
        selected = self.speed_dropdown.get_selected()
        options = ["No limit", "1M", "2M", "5M"]
        if selected < 0 or selected >= len(options):
            self.speed_limit = None
            return
        choice = options[selected]
        self.speed_limit = None if choice == "No limit" else choice

    def on_preset_changed(self, _dropdown, _param):
        preset = self.get_selected_preset()
        if not preset:
            return
        kind = preset["kind"]
        if kind == "selected":
            return
        if kind == "best":
            if self.video_format_ids:
                self.select_format_id(self.video_format_ids[0])
        elif kind == "worst":
            if self.video_format_ids:
                self.select_format_id(self.video_format_ids[-1])
        elif kind == "audio_best":
            if self.audio_format_id:
                self.select_format_id(self.audio_format_id)
        elif kind == "audio_worst":
            if self.audio_format_id:
                self.select_format_id(self.audio_format_id)

    def select_format_id(self, format_id):
        if not format_id:
            return
        if format_id in self.dropdown_format_ids:
            index = self.dropdown_format_ids.index(format_id)
            self.format_dropdown.set_selected(index)

    def get_selected_format_id(self):
        selected = self.format_dropdown.get_selected()
        if selected < 0 or selected >= len(self.dropdown_format_ids):
            return None
        return self.dropdown_format_ids[selected]

    def get_selected_preset(self):
        selected = self.presets_dropdown.get_selected()
        if selected < 0 or selected >= len(self.preset_options):
            return None
        return self.preset_options[selected]

    def enqueue_download(self, url, format_id, title, format_label, format_selector=None, post_args=None):
        row = Gtk.ListBoxRow()
        row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row_box.add_css_class("queue-row")

        title_label = Gtk.Label(label=title)
        title_label.set_xalign(0.0)
        title_label.set_hexpand(True)
        title_label.set_ellipsize(Pango.EllipsizeMode.END)

        format_label_widget = Gtk.Label(label=format_label)
        format_label_widget.add_css_class("queue-meta")
        format_label_widget.set_ellipsize(Pango.EllipsizeMode.END)

        status_label = Gtk.Label(label="Queued")
        status_label.add_css_class("queue-status")

        row_box.append(title_label)
        row_box.append(format_label_widget)
        row_box.append(status_label)
        row.set_child(row_box)
        self.queue_list.append(row)

        item = {
            "url": url,
            "format_id": format_id,
            "format_selector": format_selector,
            "format_label": format_label,
            "title": title,
            "status_label": status_label,
            "speed_limit": self.speed_limit,
            "post_args": post_args,
        }
        self.queue.append(item)
        self.process_next_download()

    def process_next_download(self):
        if self.is_downloading:
            return
        if not self.queue:
            return
        item = self.queue.pop(0)
        self.is_downloading = True
        item["status_label"].set_text("Downloading")
        threading.Thread(
            target=self.download_video,
            args=(item,),
            daemon=True
        ).start()

    def add_history_item(self, title, path):
        row = Gtk.ListBoxRow()
        row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row_box.add_css_class("history-row")

        title_label = Gtk.Label(label=title)
        title_label.set_xalign(0.0)
        title_label.set_hexpand(True)
        title_label.set_ellipsize(Pango.EllipsizeMode.END)

        open_button = Gtk.Button(label="Open Folder")
        open_button.add_css_class("history-button")

        def on_open(_btn):
            if not path:
                return
            folder = os.path.dirname(path)
            Gio.AppInfo.launch_default_for_uri(f"file://{folder}")

        open_button.connect("clicked", on_open)

        row_box.append(title_label)
        row_box.append(open_button)
        row.set_child(row_box)
        self.history_list.append(row)

    def clear_history(self, _button):
        child = self.history_list.get_first_child()
        while child:
            self.history_list.remove(child)
            child = self.history_list.get_first_child()

    def show_error_popup(self, title, error_text):
        dialog = Adw.MessageDialog.new(self.win, title, None)

        text_view = Gtk.TextView()
        text_view.set_editable(False)
        text_view.set_cursor_visible(False)
        text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        text_view.add_css_class("license-text")

        buffer = text_view.get_buffer()
        buffer.set_text(error_text)

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroller.set_min_content_height(200)
        scroller.set_child(text_view)

        dialog.set_extra_child(scroller)
        dialog.add_response("copy", "Copy")
        dialog.add_response("ok", "OK")
        dialog.set_default_response("ok")
        dialog.set_close_response("ok")

        def on_response(_dlg, response):
            if response == "copy":
                clipboard = Gdk.Display.get_default().get_clipboard()
                clipboard.set(error_text)

        dialog.connect("response", on_response)
        dialog.present()
    def add_key_controller(self):
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self.on_key_pressed)
        self.win.add_controller(key_controller)

    def on_key_pressed(self, _controller, keyval, _keycode, _state):
        if keyval == Gdk.KEY_Escape:
            self.clear_ui()
            return True
        return False

    def add_drop_target(self):
        drop_target = Gtk.DropTarget.new(
            Gdk.ContentFormats.new_for_gtype(GObject.TYPE_STRING),
            Gdk.DragAction.COPY
        )

        def on_drop(_target, value, _x, _y):
            if not value:
                return False
            url = value.strip()
            if url.startswith("http"):
                self.url_entry.set_text(url)
                self.fetch_info(self.url_entry)
                return True
            return False

        drop_target.connect("drop", on_drop)
        self.win.add_controller(drop_target)

    def on_paste_clicked(self, _button):
        display = Gdk.Display.get_default()
        if not display:
            return
        clipboard = display.get_clipboard()
        clipboard.read_text_async(None, self.on_clipboard_text)

    def on_clipboard_text(self, clipboard, result):
        try:
            text = clipboard.read_text_finish(result)
        except GLib.Error:
            return
        if text:
            url = text.strip()
            if url.startswith("http"):
                self.url_entry.set_text(url)
                self.fetch_info(self.url_entry)

    # AUTO FETCH
    def fetch_info(self, entry):

        url = self.url_entry.get_text().strip()
        if not url:
            return

        self.fetch_token += 1
        token = self.fetch_token
        self.current_url = url
        self.set_thumb_loading(True)
        threading.Thread(target=self.get_video_info, args=(url, token), daemon=True).start()

    def safe_idle(self, token, func, *args):
        def _run():
            if token != self.fetch_token:
                return False
            func(*args)
            return False
        GLib.idle_add(_run)

    def get_video_info(self, url, token):

        self.safe_idle(token, self.status_label.set_text, "Fetching info...")

        cmd = self.yt_dlp_base_cmd() + ["-J", url]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            error_text = result.stderr.strip() or result.stdout.strip() or "Unknown error"
            self.safe_idle(token, self.status_label.set_text, "Failed to fetch info")
            self.safe_idle(token, self.set_thumb_loading, False)
            self.safe_idle(token, self.show_error_popup, "Fetch Failed", error_text)
            return

        data = json.loads(result.stdout)

        title = data.get("title", "Unknown Title")
        thumbnail_url = data.get("thumbnail", "")
        formats = data.get("formats", [])

        self.formats_all = formats
        self.video_format_ids = []
        self.audio_format_id = None

        grouped = {}
        for f in formats:
            if not f.get("height"):
                continue
            if f.get("vcodec") == "none":
                continue
            height = f["height"]
            ext = f.get("ext") or "unknown"
            key = (height, ext)
            existing = grouped.get(key)
            if not existing:
                grouped[key] = f
            else:
                existing_tbr = existing.get("tbr") or 0
                candidate_tbr = f.get("tbr") or 0
                if candidate_tbr > existing_tbr:
                    grouped[key] = f

        video_items = []
        for (height, ext), f in grouped.items():
            label = f"{height}p - {ext}"
            video_items.append((height, ext, label, f["format_id"]))

        video_items.sort(key=lambda x: (-x[0], x[1]))
        video_items = [(label, format_id) for _h, _e, label, format_id in video_items]

        audio_candidates = [
            f for f in formats
            if f.get("vcodec") == "none" and f.get("acodec") not in (None, "none")
        ]
        audio_best = None
        if audio_candidates:
            audio_best = max(
                audio_candidates,
                key=lambda f: (f.get("abr") or 0, f.get("tbr") or 0)
            )

        items = list(video_items)
        self.audio_format_id = None
        if audio_best:
            audio_ext = audio_best.get("ext") or "audio"
            audio_label = f"Audio Only - {audio_ext}"
            self.audio_format_id = audio_best.get("format_id")
            items.append((audio_label, self.audio_format_id))

        self.formats = items
        self.dropdown_format_ids = [format_id for _label, format_id in items]
        self.video_format_ids = [format_id for _label, format_id in video_items]

        self.current_title = title
        self.safe_idle(token, self.title_label.set_text, title)

        format_labels = [f[0] for f in items]
        if format_labels:
            dropdown = Gtk.DropDown.new_from_strings(format_labels)
            self.safe_idle(token, self.replace_dropdown, dropdown)
            self.safe_idle(token, self.download_button.set_sensitive, True)
            self.safe_idle(token, self.presets_row.set_sensitive, True)
        else:
            self.safe_idle(token, self.download_button.set_sensitive, False)
            self.safe_idle(token, self.presets_row.set_sensitive, False)

        self.preset_options = [
            {"label": "Selected format", "kind": "selected"},
            {"label": "Best (auto)", "kind": "selector", "format": "best"},
            {"label": "Worst (auto)", "kind": "selector", "format": "worst"},
            {"label": "Best Video + Audio", "kind": "selector",
             "format": "bestvideo+bestaudio/best"},
            {"label": "Audio Only (best)", "kind": "selector", "format": "bestaudio"},
            {"label": "Audio Only (worst)", "kind": "selector", "format": "worstaudio"},
            {"label": "MP3 (audio)", "kind": "audio_format", "format": "bestaudio",
             "post": ["--extract-audio", "--audio-format", "mp3"]},
            {"label": "M4A (audio)", "kind": "audio_format", "format": "bestaudio",
             "post": ["--extract-audio", "--audio-format", "m4a"]},
            {"label": "720p", "kind": "selector",
             "format": "bestvideo[height<=720]+bestaudio/best[height<=720]"},
            {"label": "1080p", "kind": "selector",
             "format": "bestvideo[height<=1080]+bestaudio/best[height<=1080]"},
            {"label": "4K", "kind": "selector",
             "format": "bestvideo[height<=2160]+bestaudio/best[height<=2160]"},
        ]
        preset_labels = [p["label"] for p in self.preset_options]
        preset_dropdown = Gtk.DropDown.new_from_strings(preset_labels)
        self.safe_idle(token, self.replace_preset_dropdown, preset_dropdown)

        # BIGGER Thumbnail
        if thumbnail_url:
            thumb_path = "/tmp/glassdrop_thumb.jpg"
            urllib.request.urlretrieve(thumbnail_url, thumb_path)

            self.safe_idle(token, self.thumbnail.set_filename, thumb_path)
            self.safe_idle(token, self.set_thumb_loading, False)
        else:
            self.safe_idle(token, self.set_thumb_loading, False)

        self.safe_idle(token, self.status_label.set_text, "Info Loaded")

    def replace_dropdown(self, new_dropdown):
        parent = self.format_dropdown.get_parent()
        parent.remove(self.format_dropdown)
        self.format_dropdown = new_dropdown
        parent.insert_child_after(self.format_dropdown, self.presets_row)
        if self.format_dropdown.get_n_items() > 0:
            self.format_dropdown.set_selected(0)

    def replace_preset_dropdown(self, new_dropdown):
        parent = self.presets_dropdown.get_parent()
        parent.remove(self.presets_dropdown)
        self.presets_dropdown = new_dropdown
        self.presets_dropdown.connect("notify::selected", self.on_preset_changed)
        parent.insert_child_after(self.presets_dropdown, self.presets_label)
        if self.presets_dropdown.get_n_items() > 0:
            self.presets_dropdown.set_selected(0)

    def start_download(self, button):

        url = self.current_url or self.url_entry.get_text().strip()
        if not url:
            return

        preset = self.get_selected_preset()
        format_id = None
        format_selector = None
        post_args = None
        preset_label = "Selected format"

        if preset:
            preset_label = preset.get("label", preset_label)
            kind = preset.get("kind")
            if kind == "selected":
                format_id = self.get_selected_format_id()
            elif kind in ("selector", "audio_format"):
                format_selector = preset.get("format")
                post_args = preset.get("post")
            elif kind == "best":
                format_id = self.video_format_ids[0] if self.video_format_ids else None
            elif kind == "worst":
                format_id = self.video_format_ids[-1] if self.video_format_ids else None
            elif kind == "audio_best":
                format_id = self.audio_format_id
            elif kind == "audio_worst":
                format_id = self.audio_format_id

        if not format_id and not format_selector:
            return

        selected = self.format_dropdown.get_selected()
        format_label = (
            self.formats[selected][0]
            if 0 <= selected < len(self.formats)
            else "Format"
        )
        title = self.current_title or url
        display_label = format_label if (preset and preset.get("kind") == "selected") else preset_label
        self.enqueue_download(
            url,
            format_id,
            title,
            display_label,
            format_selector=format_selector,
            post_args=post_args
        )

    def download_video(self, item):

        url = item["url"]
        format_id = item.get("format_id")
        format_selector = item.get("format_selector")
        speed_limit = item.get("speed_limit")
        post_args = item.get("post_args") or []

        GLib.idle_add(self.status_label.set_text, "Downloading...")

        cmd = self.yt_dlp_base_cmd()
        if format_id:
            cmd.extend(["-f", format_id])
        elif format_selector:
            cmd.extend(["-f", format_selector])
        if speed_limit:
            cmd.extend(["--limit-rate", speed_limit])
        if post_args:
            cmd.extend(post_args)
        cmd.append(url)

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        self.download_process = process
        dest_path = None

        error_tail = []
        for line in process.stdout:
            if line:
                error_tail.append(line.rstrip())
                if len(error_tail) > 20:
                    error_tail.pop(0)
            if "%" in line:
                try:
                    percent = float(line.split("%")[0].split()[-1])
                    GLib.idle_add(self.progress.set_fraction, percent / 100)
                except:
                    pass
            if "[download]" in line:
                percent = None
                speed = None
                eta = None

                match_percent = re.search(r"(\d+(?:\.\d+)?)%", line)
                if match_percent:
                    percent = match_percent.group(1)

                match_speed = re.search(r"at\s+([^\s]+)", line)
                if match_speed:
                    speed = match_speed.group(1)

                match_eta = re.search(r"ETA\s+([^\s]+)", line)
                if match_eta:
                    eta = match_eta.group(1)

                parts = ["Downloading..."]
                if percent:
                    parts.append(f"{percent}%")
                if speed:
                    parts.append(speed)
                if eta:
                    parts.append(f"ETA {eta}")
                GLib.idle_add(self.status_label.set_text, " \u2022 ".join(parts))
            match_dest = re.search(r"Destination:\s(.+)", line)
            if match_dest:
                dest_path = match_dest.group(1).strip()

        process.wait()
        self.download_process = None

        if process.returncode != 0:
            error_text = "\n".join(error_tail) if error_tail else "Download failed."
            self.safe_idle(self.fetch_token, self.show_error_popup, "Download Failed", error_text)

        if dest_path:
            dest_path = os.path.abspath(dest_path)
        status_text = "Download Complete" if process.returncode == 0 else "Download Failed"
        GLib.idle_add(self.status_label.set_text, status_text)
        GLib.idle_add(self.progress.set_fraction, 0.0)

        def finish():
            item["status_label"].set_text(
                "Done" if process.returncode == 0 else "Failed"
            )
            if process.returncode == 0:
                self.add_history_item(item["title"], dest_path)
            self.is_downloading = False
            self.process_next_download()

        GLib.idle_add(finish)

    def clear_ui(self):
        self.fetch_token += 1
        if self.download_process and self.download_process.poll() is None:
            try:
                self.download_process.terminate()
            except Exception:
                pass
            self.download_process = None

        self.url_entry.set_text("")
        self.title_label.set_text("")
        self.current_url = ""
        self.current_title = ""
        self.thumbnail.set_filename(None)
        self.set_thumb_loading(False)
        self.progress.set_fraction(0.0)
        self.status_label.set_text("Idle")
        self.download_button.set_sensitive(False)
        self.presets_row.set_sensitive(False)
        self.formats = []
        self.dropdown_format_ids = []
        self.video_format_ids = []
        self.audio_format_id = None
        self.preset_options = []
        old_dropdown = self.format_dropdown
        parent = old_dropdown.get_parent()
        if parent:
            parent.remove(old_dropdown)
        self.format_dropdown = Gtk.DropDown.new_from_strings(["No formats loaded"])
        self.title_label.get_parent().insert_child_after(self.format_dropdown, self.presets_row)
        old_preset = self.presets_dropdown
        parent = old_preset.get_parent()
        if parent:
            parent.remove(old_preset)
        self.presets_dropdown = Gtk.DropDown.new_from_strings(["Selected format"])
        self.presets_dropdown.connect("notify::selected", self.on_preset_changed)
        self.presets_label.get_parent().insert_child_after(self.presets_dropdown, self.presets_label)


app = GlassDrop()
app.run()
