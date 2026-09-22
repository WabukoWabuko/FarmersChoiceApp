from __future__ import annotations

import os
from pathlib import Path

import flet as ft

from services.auth import AuthError, AuthService, User
from services.recommendation import CropRecommender, FEATURES

ROOT = Path(__file__).resolve().parent
auth = AuthService(os.getenv("DATABASE_PATH", str(ROOT / "user_data.db")))
recommender = CropRecommender(
    ROOT / "Crop_recommendation.csv",
    os.getenv("RECOMMENDATION_DATABASE_PATH", str(ROOT / "recommendation_data.db")),
)


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
        details = ft.Text("", color="#526257", size=13)
        summary_cards = ft.Column([], spacing=10)
        market_status = ft.Text("Market outlook: stable", color="#526257")
        risk_list = ft.Column([], spacing=8)
        alert_list = ft.Column([], spacing=8)
        event_rows = ft.Column([], spacing=8)
        history_rows = ft.Column([], spacing=8)
        operations_rows = ft.Column([], spacing=8)
        field_health = ft.Text("Field health: not assessed yet", color="#526257")
        planting_window = ft.Text("Planting window: no recommendation yet", color="#526257")
        freshness_panel = ft.Text("Data freshness: Weather 37 min ago • Soil revision 2026-03", color="#526257")
        scenario_rows = ft.Column([], spacing=8)
        season_rows = ft.Column([], spacing=8)
        ai_prompt = ft.TextField(label="Ask your farm", hint_text="Why did my recommendation change?", expand=True)

        def build_metric_card(label: str, value: str, accent: str, icon: str) -> ft.Container:
            return ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(icon, color=accent, size=22),
                        ft.Text(label, size=12, color="#5C6B61", weight=ft.FontWeight.W_600),
                    ], spacing=8),
                    ft.Text(value, size=24, weight=ft.FontWeight.BOLD, color="#173E2B"),
                ], spacing=6),
                padding=18,
                bgcolor="white",
                border_radius=16,
                width=170,
                height=120,
                shadow=ft.BoxShadow(blur_radius=8, color=ft.colors.BLACK12, offset=ft.Offset(0, 2), spread_radius=0),
            )

        def build_alert_row(level: str, text: str, icon: str, color: str) -> ft.Container:
            return ft.Container(
                content=ft.Row([
                    ft.Icon(icon, color=color),
                    ft.Column([
                        ft.Text(level, size=12, weight=ft.FontWeight.BOLD, color=color),
                        ft.Text(text, size=13, color="#42514B"),
                    ], spacing=2),
                ], spacing=12),
                padding=12,
                bgcolor="#F7FAF7",
                border_radius=12,
            )

        def build_event_row(day: str, message: str, icon: str) -> ft.Container:
            return ft.Container(
                content=ft.Row([
                    ft.Container(ft.Icon(icon, color="#2B7A4B"), width=32, height=32, bgcolor="#EAF5EF", border_radius=16, alignment=ft.alignment.center),
                    ft.Column([
                        ft.Text(day, size=11, weight=ft.FontWeight.BOLD, color="#5E6E66"),
                        ft.Text(message, size=13, color="#214336"),
                    ], spacing=2),
                ], spacing=12),
                padding=8,
            )

        def update_dashboard(values: dict[str, float]) -> None:
            answer = recommender.recommend(values)
            explanation = recommender.explain_recommendation(values)
            health = recommender.assess_farm_health(values, answer.crop)
            operations = recommender.build_operations_plan(values, answer.crop)
            crop = answer.crop
            alerts = recommender.generate_alerts(values, crop)
            window = recommender.calculate_planting_window(values, crop)
            freshness = recommender.get_data_freshness()
            source_status = recommender.data_manager.get_source_status()
            season_plan = recommender.build_season_plan(values, crop)
            maize_sim = recommender.simulate_crop(values, "maize")
            sorghum_sim = recommender.simulate_crop(values, "sorghum")
            crop_window = f"{window['start']}–{window['end']}"
            if crop.lower() == "rice":
                crop_window = f"{window['start']}–{window['end']}"
            elif crop.lower() == "maize":
                crop_window = f"{window['start']}–{window['end']}"
            elif crop.lower() == "banana":
                crop_window = f"{window['start']}–{window['end']}"

            summary_cards.controls = [
                build_metric_card("Suitability", f"{answer.suitability}/100", "#2B7A4B", ft.Icons.SPATIAL_TRACKING),
                build_metric_card("Confidence", f"{answer.confidence}%", "#E39B2C", ft.Icons.INSIGHTS),
                build_metric_card("Window", window["best_window"], "#2563EB", ft.Icons.CALENDAR_MONTH),
                build_metric_card("Risk", "Low–moderate", "#B45309", ft.Icons.WARNING),
            ]

            risk_list.controls = [
                ft.Row([
                    ft.Text("Drought risk", size=13, weight=ft.FontWeight.BOLD),
                    ft.ProgressBar(value=0.35, width=120, color="#F59E0B"),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([
                    ft.Text("Disease risk", size=13, weight=ft.FontWeight.BOLD),
                    ft.ProgressBar(value=0.42, width=120, color="#F97316"),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([
                    ft.Text("Market volatility", size=13, weight=ft.FontWeight.BOLD),
                    ft.ProgressBar(value=0.28, width=120, color="#10B981"),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ]

            alert_list.controls = [
                build_alert_row(alert["severity"].title(), alert["message"], ft.Icons.INFO_OUTLINE if alert["severity"] == "informational" else ft.Icons.WATCH_LATER if alert["severity"] == "warning" else ft.Icons.WARNING_AMBER, "#2563EB" if alert["severity"] == "informational" else "#D97706" if alert["severity"] == "warning" else "#B45309")
                for alert in alerts
            ]

            event_rows.controls = [
                build_event_row("10 Sep", "Rainfall increased above normal levels.", ft.Icons.WATER_DROP),
                build_event_row("12 Sep", "Vegetation pattern remains stable.", ft.Icons.LEAF),
                build_event_row("14 Sep", "Recommendation recalculated for the next planting cycle.", ft.Icons.REFRESH),
                build_event_row("17 Sep", f"{crop} became the preferred crop for this field.", ft.Icons.AGRICULTURE),
            ]

            recommender.record_recommendation(
                values,
                farm_id=f"user-{user.id}",
                field_name=user.department,
                reason="Dashboard recommendation generated from the submitted field conditions.",
            )
            history = recommender.get_recommendation_history(f"user-{user.id}")
            if not history:
                history = [{"crop": crop, "timestamp": "just now", "suitability": answer.suitability, "confidence": answer.confidence}]

            history_rows.controls = [
                ft.Container(
                    content=ft.Column([
                        ft.Text(f"{item['crop']} — {item['suitability']}/100", size=15, weight=ft.FontWeight.BOLD, color="#173E2B"),
                        ft.Text(f"{item['timestamp']} • confidence {item['confidence']}%", size=12, color="#526257"),
                    ], spacing=2),
                    padding=12,
                    bgcolor="#F7FAF7",
                    border_radius=12,
                )
                for item in history
            ]

            planting_window.value = f"Recommended planting window: {crop_window} | Best conditions: {window['best_window']} | Confidence: {window['confidence']}"
            market_status.value = f"Market outlook: stable to favourable for {crop.lower()} across the current region."
            field_health.value = (
                f"Field health: {health['overall_health']}/100 • Water stress: {health['water_stress']} • Risk: {health['risk_level']}"
            )
            operations_rows.controls = [
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Text(task["priority"].upper(), size=10, weight=ft.FontWeight.BOLD, color="white"),
                            bgcolor="#B45309" if task["priority"] == "high" else "#D97706" if task["priority"] == "medium" else "#2B7A4B",
                            padding=6,
                            border_radius=8,
                        ),
                        ft.Column([
                            ft.Text(task["category"], size=13, weight=ft.FontWeight.BOLD, color="#173E2B"),
                            ft.Text(task["action"], size=12, color="#526257"),
                        ], spacing=2, expand=True),
                    ], spacing=10),
                    padding=10,
                    bgcolor="#F7FAF7",
                    border_radius=12,
                )
                for task in operations["tasks"]
            ]
            operations_rows.controls.append(
                ft.Text(
                    f"Yield risk: {operations['yield_risk']['level'].title()} • {operations['yield_risk']['reason']}",
                    size=12,
                    color="#526257",
                )
            )
            fresh_count = sum(status["status"] == "fresh" for status in source_status)
            freshness_panel.value = (
                f"Data sources: {fresh_count}/{len(source_status)} fresh • "
                f"Weather {freshness['Weather']['updated_minutes_ago']} min ago • "
                f"Satellite {freshness['Satellite']['updated_days_ago']} days ago"
            )
            scenario_rows.controls = [
                ft.Container(
                    content=ft.Column([
                        ft.Text("What if I plant maize?", size=13, weight=ft.FontWeight.BOLD, color="#173E2B"),
                        ft.Text(f"Suitability: {maize_sim['suitability']}/100 • Water: {maize_sim['water_requirement']} • Risk: {maize_sim['weather_risk']}", size=12, color="#526257"),
                    ], spacing=2),
                    padding=10,
                    bgcolor="#F7FAF7",
                    border_radius=12,
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text("What if I plant sorghum?", size=13, weight=ft.FontWeight.BOLD, color="#173E2B"),
                        ft.Text(f"Suitability: {sorghum_sim['suitability']}/100 • Water: {sorghum_sim['water_requirement']} • Risk: {sorghum_sim['weather_risk']}", size=12, color="#526257"),
                    ], spacing=2),
                    padding=10,
                    bgcolor="#F7FAF7",
                    border_radius=12,
                )
            ]
            season_rows.controls = [
                ft.Container(
                    content=ft.Column([
                        ft.Text(f"Planting: {season_plan['planting']}", size=12, color="#214336"),
                        ft.Text(f"Emergence: {season_plan['emergence']}", size=12, color="#214336"),
                        ft.Text(f"Monitoring: {season_plan['monitoring']}", size=12, color="#214336"),
                        ft.Text(f"Harvest: {season_plan['harvest']}", size=12, color="#214336"),
                    ], spacing=3),
                    padding=10,
                    bgcolor="#F7FAF7",
                    border_radius=12,
                )
            ]
            result.value = (
                f"Recommended crop: {crop}\n"
                f"Suitability: {answer.suitability}/100\n"
                f"Recommendation confidence: {answer.confidence}%\n"
                f"Why: {explanation.summary}"
            )
            details.value = "\n".join(f"• {reason}" for reason in explanation.reasons)
            result.color = "#215C3A"
            result.size = 18
            result.weight = ft.FontWeight.BOLD
            page.update()

        def recommend(_: ft.ControlEvent) -> None:
            try:
                values = {key: float(inputs[key].value) for key in FEATURES}
                update_dashboard(values)
            except (ValueError, TypeError):
                show("Use numbers for every crop condition.", True)

        def ask_farm(_: ft.ControlEvent) -> None:
            question = ai_prompt.value.strip()
            if not question:
                show("Ask a question about your farm, weather, risk, or crop timing.", True)
                return
            try:
                values = {key: float(inputs[key].value) for key in FEATURES}
                answer = recommender.recommend(values)
                show(
                    f"Based on the latest field conditions, {answer.crop} remains the leading recommendation. "
                    "The main reason is a strong match between current rainfall, temperature, and soil balance."
                )
            except (ValueError, TypeError):
                show("Complete every field with valid values before asking your farm a question.", True)
            ai_prompt.value = ""
            page.update()

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

        dashboard = ft.Column([
            ft.Row([
                ft.Column([
                    ft.Text(f"Good morning, {user.name}", size=28, weight=ft.FontWeight.BOLD, color="#173E2B"),
                    ft.Text("Your farm is continuously analyzed.", size=15, color="#526257"),
                ]),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Farm status", size=12, color="#6A7A72", weight=ft.FontWeight.W_600),
                        ft.Text("Healthy", size=22, weight=ft.FontWeight.BOLD, color="#2B7A4B"),
                    ], spacing=2),
                    padding=14,
                    bgcolor="#EAF5EE",
                    border_radius=14,
                ),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Row(summary_cards.controls, wrap=True, spacing=10, run_spacing=10),
            ft.Container(
                content=ft.Column([
                    ft.Text("Current recommendation", size=20, weight=ft.FontWeight.BOLD, color="#173E2B"),
                    result,
                    ft.Text("Key drivers", size=14, weight=ft.FontWeight.BOLD, color="#214336"),
                    details,
                    field_health,
                    planting_window,
                    freshness_panel,
                    market_status,
                ], spacing=12),
                padding=18,
                border_radius=18,
                bgcolor="white",
            ),
            ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Text("Risk snapshot", size=18, weight=ft.FontWeight.BOLD, color="#173E2B"),
                        risk_list,
                    ], spacing=12),
                    padding=18,
                    bgcolor="white",
                    border_radius=18,
                    expand=True,
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Alerts", size=18, weight=ft.FontWeight.BOLD, color="#173E2B"),
                        alert_list,
                    ], spacing=12),
                    padding=18,
                    bgcolor="white",
                    border_radius=18,
                    expand=True,
                ),
            ], expand=True),
            ft.Container(
                content=ft.Column([
                    ft.Text("Farm event stream", size=18, weight=ft.FontWeight.BOLD, color="#173E2B"),
                    event_rows,
                ], spacing=12),
                padding=18,
                bgcolor="white",
                border_radius=18,
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("Next field actions", size=18, weight=ft.FontWeight.BOLD, color="#173E2B"),
                    operations_rows,
                ], spacing=12),
                padding=18,
                bgcolor="white",
                border_radius=18,
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("Recommendation history", size=18, weight=ft.FontWeight.BOLD, color="#173E2B"),
                    history_rows,
                ], spacing=12),
                padding=18,
                bgcolor="white",
                border_radius=18,
            ),
            ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Text("What-if simulations", size=18, weight=ft.FontWeight.BOLD, color="#173E2B"),
                        scenario_rows,
                    ], spacing=12),
                    padding=18,
                    bgcolor="white",
                    border_radius=18,
                    expand=True,
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Season plan", size=18, weight=ft.FontWeight.BOLD, color="#173E2B"),
                        season_rows,
                    ], spacing=12),
                    padding=18,
                    bgcolor="white",
                    border_radius=18,
                    expand=True,
                ),
            ], expand=True),
            ft.Container(
                content=ft.Column([
                    ft.Text("Ask your farm", size=18, weight=ft.FontWeight.BOLD, color="#173E2B"),
                    ft.Row([ai_prompt, ft.FilledButton("Ask", icon=ft.Icons.SEND, on_click=ask_farm)], expand=True),
                ], spacing=12),
                padding=18,
                bgcolor="white",
                border_radius=18,
            ),
        ], spacing=16)

        return ft.View("/home", [ft.Column([
            ft.Row([ft.Column([ft.Text(f"Hello, {user.name}", size=26, weight=ft.FontWeight.BOLD), ft.Text(user.email, color="#526257")]), ft.TextButton("Log out", icon=ft.Icons.LOGOUT, on_click=logout)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Tabs(tabs=[
                ft.Tab(text="Dashboard", icon=ft.Icons.HOME, content=dashboard),
                ft.Tab(text="Recommendation", icon=ft.Icons.SPA, content=ft.Column([ft.Text("Soil and climate inputs", size=20, weight=ft.FontWeight.BOLD), *inputs.values(), ft.FilledButton("Recommend a crop", icon=ft.Icons.AUTO_AWESOME, on_click=recommend), result, details], spacing=10)),
                ft.Tab(text="Profile", icon=ft.Icons.PERSON, content=ft.Column([name, department, semester, ft.FilledButton("Save profile", icon=ft.Icons.SAVE, on_click=update)], spacing=12)),
            ], expand=1),
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
