from __future__ import annotations

import os
from pathlib import Path

import flet as ft

from services.auth import AuthError, AuthService, User
from services.recommendation import CropRecommender, FEATURES

ROOT = Path(__file__).resolve().parent
auth = AuthService(os.getenv("DATABASE_PATH", str(ROOT / "user_data.db")))
recommender = CropRecommender(ROOT / "Crop_recommendation.csv")


def main(page: ft.Page) -> None:
    page.title = "Farmers' Choice"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 24
    page.bgcolor = "#F4F7F1"
    page.window_width = 460
    page.window_height = 760
    session: dict[str, User | None] = {"user": None}

    def show(message: str, error: bool = False) -> None:
        page.snack_bar = ft.SnackBar(ft.Text(message), bgcolor="#B42318" if error else "#26734D", open=True)
        page.update()

    def field(label: str, password: bool = False) -> ft.TextField:
        return ft.TextField(label=label, password=password, can_reveal_password=password, border_radius=10)

    def header(title: str, subtitle: str) -> ft.Column:
        return ft.Column([ft.Text(title, size=32, weight=ft.FontWeight.BOLD, color="#215C3A"), ft.Text(subtitle, color="#526257")], spacing=4)

    def navigate(route: str) -> None:
        page.go(route)

    def welcome() -> ft.View:
        return ft.View("/", [ft.Container(ft.Column([
            ft.Text("FARMERS'", size=42, weight=ft.FontWeight.BOLD, color="#215C3A"),
            ft.Text("CHOICE", size=42, weight=ft.FontWeight.BOLD, color="#D9822B"),
            ft.Text("Better crop decisions, grounded in your soil and climate.", size=18, color="#526257"),
            ft.Divider(),
            ft.FilledButton("Create an account", icon=ft.Icons.PERSON_ADD, on_click=lambda _: navigate("/register"), width=280),
            ft.OutlinedButton("Log in", icon=ft.Icons.LOGIN, on_click=lambda _: navigate("/login"), width=280),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=18), padding=35, border_radius=18, bgcolor="white")])

    def login_view() -> ft.View:
        email, password = field("Email"), field("Password", True)
        def submit(_: ft.ControlEvent) -> None:
            try:
                session["user"] = auth.login(email.value, password.value)
                navigate("/home")
            except AuthError as error:
                show(str(error), True)
        return ft.View("/login", [ft.Column([
            ft.TextButton("Back", icon=ft.Icons.ARROW_BACK, on_click=lambda _: navigate("/")),
            header("Welcome back", "Sign in to your farm dashboard."), email, password,
            ft.FilledButton("Log in", icon=ft.Icons.LOGIN, on_click=submit, width=220),
            ft.TextButton("Forgot password?", on_click=lambda _: navigate("/forgot")),
            ft.TextButton("Create an account", on_click=lambda _: navigate("/register")),
        ], spacing=16)])

    def register_view() -> ft.View:
        name, email = field("Full name"), field("Email")
        department, semester = field("Farm / department"), field("Experience or season")
        password, confirm = field("Password (8+ characters)", True), field("Confirm password", True)
        def submit(_: ft.ControlEvent) -> None:
            if password.value != confirm.value:
                show("Passwords do not match.", True)
                return
            try:
                session["user"] = auth.register(name.value, email.value, password.value, department.value, semester.value)
                navigate("/home")
            except AuthError as error:
                show(str(error), True)
        return ft.View("/register", [ft.Column([
            ft.TextButton("Back", icon=ft.Icons.ARROW_BACK, on_click=lambda _: navigate("/")),
            header("Create your account", "Your recommendations stay in your local database."), name, email, department, semester, password, confirm,
            ft.FilledButton("Register", icon=ft.Icons.PERSON_ADD, on_click=submit, width=220),
            ft.TextButton("Already registered? Log in", on_click=lambda _: navigate("/login")),
        ], spacing=12)])

    def forgot_view() -> ft.View:
        email, token, password = field("Account email"), field("Reset code"), field("New password (8+ characters)", True)
        def request(_: ft.ControlEvent) -> None:
            try:
                token.value = auth.create_reset_token(email.value)
                token.visible = True
                password.visible = True
                reset.visible = True
                show("Reset code generated. In production, deliver this code by email.")
                page.update()
            except AuthError as error:
                show(str(error), True)
        def reset_password(_: ft.ControlEvent) -> None:
            try:
                auth.reset_password(token.value, password.value)
                show("Password updated. You can log in now.")
                navigate("/login")
            except AuthError as error:
                show(str(error), True)
        reset = ft.FilledButton("Set new password", icon=ft.Icons.CHECK, on_click=reset_password, visible=False, width=220)
        token.visible = password.visible = False
        return ft.View("/forgot", [ft.Column([
            ft.TextButton("Back", icon=ft.Icons.ARROW_BACK, on_click=lambda _: navigate("/login")), header("Reset password", "Generate a one-time reset code for your account."), email,
            ft.FilledButton("Generate reset code", icon=ft.Icons.MARK_EMAIL_READ, on_click=request, width=240), token, password, reset,
        ], spacing=14)])

    def home_view() -> ft.View:
        user = session["user"]
        if not user:
            navigate("/login")
            return ft.View("/", [])
        inputs = {key: field(key.replace("_", " ").title()) for key in FEATURES}
        result = ft.Text("Enter your conditions to get a data-based recommendation.", color="#526257")
        def recommend(_: ft.ControlEvent) -> None:
            try:
                values = {key: float(inputs[key].value) for key in FEATURES}
                answer = recommender.recommend(values)
                result.value = f"Recommended crop: {answer.crop}\nModel confidence: {answer.confidence}% ({answer.sample_count} nearest dataset samples)"
                result.color = "#215C3A"
                result.size = 18
                result.weight = ft.FontWeight.BOLD
                page.update()
            except (ValueError, TypeError):
                show("Use numbers for every crop condition.", True)
        name, department, semester = field("Full name"), field("Farm / department"), field("Experience or season")
        name.value, department.value, semester.value = user.name, user.department, user.semester
        def update(_: ft.ControlEvent) -> None:
            nonlocal user
            try:
                user = auth.update_profile(user.id, name.value, department.value, semester.value)
                session["user"] = user
                show("Profile saved.")
            except AuthError as error:
                show(str(error), True)
        def logout(_: ft.ControlEvent) -> None:
            session["user"] = None
            navigate("/")
        return ft.View("/home", [ft.Column([
            ft.Row([ft.Column([ft.Text(f"Hello, {user.name}", size=26, weight=ft.FontWeight.BOLD), ft.Text(user.email, color="#526257")]), ft.TextButton("Log out", icon=ft.Icons.LOGOUT, on_click=logout)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Tabs(tabs=[ft.Tab(text="Recommendation", icon=ft.Icons.SPA, content=ft.Column([ft.Text("Soil and climate inputs", size=20, weight=ft.FontWeight.BOLD), *inputs.values(), ft.FilledButton("Recommend a crop", icon=ft.Icons.AUTO_AWESOME, on_click=recommend), result], spacing=10)), ft.Tab(text="Profile", icon=ft.Icons.PERSON, content=ft.Column([name, department, semester, ft.FilledButton("Save profile", icon=ft.Icons.SAVE, on_click=update)], spacing=12))], expand=1),
        ], spacing=18)])

    def route_change(_: ft.RouteChangeEvent) -> None:
        page.views.clear()
        routes = {"/": welcome, "/login": login_view, "/register": register_view, "/forgot": forgot_view, "/home": home_view}
        page.views.append(routes.get(page.route, welcome)())
        page.update()

    page.on_route_change = route_change
    page.go("/")


if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=int(os.getenv("PORT", "8550")))
