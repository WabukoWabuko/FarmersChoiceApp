from __future__ import annotations

import os
from pathlib import Path

import flet as ft

from services.auth import AuthError, AuthService, User
from services.commerce import CommerceService
from services.recommendation import CropRecommender, FEATURES

ROOT = Path(__file__).resolve().parent
auth = AuthService(os.getenv("DATABASE_PATH", str(ROOT / "user_data.db")))
recommender = CropRecommender(
    ROOT / "Crop_recommendation.csv",
    os.getenv("RECOMMENDATION_DATABASE_PATH", str(ROOT / "recommendation_data.db")),
)
commerce = CommerceService()


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
        role = ft.Dropdown(label="How will you use Farmers' Choice?", value="Farmer", options=[
            ft.dropdown.Option("Farmer"),
            ft.dropdown.Option("Laborer"),
            ft.dropdown.Option("Buyer"),
            ft.dropdown.Option("Seller"),
            ft.dropdown.Option("Sponsor"),
        ])
        password, confirm = field("Password (8+ characters)", True), field("Confirm password", True)
        def submit(_: ft.ControlEvent) -> None:
            if password.value != confirm.value:
                show("Passwords do not match.", True)
                return
            try:
                session["user"] = auth.register(name.value, email.value, password.value, department.value, semester.value, role.value)
                navigate("/home")
            except AuthError as error:
                show(str(error), True)
        return ft.View("/register", [ft.Column([
            ft.TextButton("Back", icon=ft.Icons.ARROW_BACK, on_click=lambda _: navigate("/")),
            header("Create your account", "Choose a workspace and start with only the information you want to share."), name, email, department, semester, role, password, confirm,
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
            maize_base = maize_sim["economic_scenarios"][1]
            sorghum_base = sorghum_sim["economic_scenarios"][1]
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
                        ft.Text(f"Base revenue: KSh {maize_base['revenue']['low']:,}–{maize_base['revenue']['high']:,} • Margin: KSh {maize_base['margin']['low']:,}–{maize_base['margin']['high']:,}", size=12, color="#526257"),
                    ], spacing=2),
                    padding=10,
                    bgcolor="#F7FAF7",
                    border_radius=12,
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text("What if I plant sorghum?", size=13, weight=ft.FontWeight.BOLD, color="#173E2B"),
                        ft.Text(f"Suitability: {sorghum_sim['suitability']}/100 • Water: {sorghum_sim['water_requirement']} • Risk: {sorghum_sim['weather_risk']}", size=12, color="#526257"),
                        ft.Text(f"Base revenue: KSh {sorghum_base['revenue']['low']:,}–{sorghum_base['revenue']['high']:,} • Margin: KSh {sorghum_base['margin']['low']:,}–{sorghum_base['margin']['high']:,}", size=12, color="#526257"),
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

        def worker_card(worker) -> ft.Container:
            review = ft.TextField(label="Add a recommendation", dense=True, expand=True)

            def recommend_worker(_: ft.ControlEvent) -> None:
                if review.value.strip():
                    worker.recommendations.insert(0, review.value.strip())
                    review.value = ""
                    show(f"Recommendation added for {worker.name}.")
                    page.update()

            return ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Column([
                            ft.Text(worker.name, size=16, weight=ft.FontWeight.BOLD, color="#173E2B"),
                            ft.Text(f"{worker.trade} • {worker.location}", size=12, color="#526257"),
                        ], expand=True),
                        ft.Text(f"★ {worker.rating:.1f}", size=14, weight=ft.FontWeight.BOLD, color="#D9822B"),
                    ]),
                    ft.Text(worker.bio, size=12, color="#526257"),
                    ft.Text(" • ".join(worker.skills), size=12, color="#2B7A4B"),
                    ft.Text(f"{worker.completed_jobs} completed jobs • {'Verified profile' if worker.verified else 'Unverified'}", size=11, color="#6A7A72"),
                    ft.Text("Recent comments", size=12, weight=ft.FontWeight.BOLD, color="#214336"),
                    *[ft.Text(f'“{comment}”', size=12, color="#526257") for comment in worker.comments[:2]],
                    ft.Row([review, ft.IconButton(ft.Icons.SEND, tooltip="Recommend this worker", on_click=recommend_worker)], spacing=6),
                ], spacing=8),
                padding=14,
                bgcolor="#F7FAF7",
                border_radius=14,
            )

        worker_search = ft.TextField(label="Search workers by skill or location", prefix_icon=ft.Icons.SEARCH, expand=True)
        worker_results = ft.Column([worker_card(worker) for worker in commerce.search_workers()], spacing=10)

        def search_workers(_: ft.ControlEvent) -> None:
            worker_results.controls = [worker_card(worker) for worker in commerce.search_workers(worker_search.value)]
            page.update()

        listing_search = ft.TextField(label="Search products, inputs, or equipment", prefix_icon=ft.Icons.SEARCH, expand=True)
        listing_results = ft.Column([], spacing=10)
        order_rows = ft.Column([], spacing=8)

        def listing_card(listing) -> ft.Container:
            quantity = ft.TextField(label="Qty", value="1", width=70, dense=True)

            def checkout(_: ft.ControlEvent) -> None:
                try:
                    order = commerce.create_order(user.name, listing, int(quantity.value))
                    order_rows.controls.insert(0, ft.Container(content=ft.Column([
                        ft.Text(f"{order.product} • {order.quantity} unit(s) • KES {order.total:,.0f}", weight=ft.FontWeight.BOLD, color="#173E2B"),
                        ft.Text(f"{order.status} • Escrow: {order.escrow_status} • Delivery: {order.delivery_status}", size=12, color="#526257"),
                        ft.Row([
                            ft.TextButton("Fund escrow", icon=ft.Icons.LOCK, on_click=lambda _: commerce.fund_escrow(order)),
                            ft.TextButton("Report issue", icon=ft.Icons.FLAG, on_click=lambda _: commerce.report_order(order)),
                        ]),
                    ], spacing=4), padding=10, bgcolor="#F7FAF7", border_radius=10))
                    show("Order created. Review the order panel to continue checkout.")
                    page.update()
                except (ValueError, TypeError):
                    show("Choose an available quantity.", True)

            return ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text(listing.title, size=15, weight=ft.FontWeight.BOLD, color="#173E2B"),
                        ft.Text(f"{listing.category} • {listing.seller} • {listing.location}", size=12, color="#526257"),
                        ft.Text(listing.description, size=12, color="#526257"),
                        ft.Text(f"{listing.stock} available • {listing.unit}", size=11, color="#6A7A72"),
                    ], expand=True),
                    ft.Column([
                        ft.Text(f"KES {listing.price:,.0f}", size=16, weight=ft.FontWeight.BOLD, color="#2B7A4B"),
                        ft.Row([quantity, ft.IconButton(ft.Icons.SHOPPING_CART_CHECKOUT, tooltip="Checkout", on_click=checkout)], spacing=4),
                    ], horizontal_alignment=ft.CrossAxisAlignment.END),
                ], spacing=12),
                padding=14,
                bgcolor="#F7FAF7",
                border_radius=14,
            )

        def search_listings(_: ft.ControlEvent) -> None:
            listing_results.controls = [listing_card(listing) for listing in commerce.search_listings(listing_search.value)]
            page.update()

        listing_results.controls = [listing_card(listing) for listing in commerce.listings]
        buyer_product = ft.TextField(label="Product wanted", expand=True)
        buyer_quantity = ft.TextField(label="Quantity", width=150)
        buyer_location = ft.TextField(label="Delivery location", expand=True)
        request_rows = ft.Column([], spacing=8)

        def create_buyer_request(_: ft.ControlEvent) -> None:
            if not buyer_product.value.strip() or not buyer_quantity.value.strip() or not buyer_location.value.strip():
                show("Complete the buyer request details.", True)
                return
            request = commerce.create_buyer_request(user.name, buyer_product.value, buyer_quantity.value, buyer_location.value)
            request_rows.controls.insert(0, ft.Text(f"{request.product} • {request.quantity} • {request.location} • {request.status}", color="#526257"))
            buyer_product.value = buyer_quantity.value = buyer_location.value = ""
            show("Buyer request published.")
            page.update()

        payment_amount = ft.TextField(label="Amount (KES)", keyboard_type=ft.KeyboardType.NUMBER, expand=True)
        payment_recipient = ft.TextField(label="Recipient or seller", expand=True)
        payment_method = ft.Dropdown(label="Payment method", value="Mobile money", options=[ft.dropdown.Option("Mobile money"), ft.dropdown.Option("Bank transfer"), ft.dropdown.Option("Card")], expand=True)
        payment_rows = ft.Column([], spacing=8)

        def create_payment(_: ft.ControlEvent) -> None:
            try:
                payment = commerce.create_payment(float(payment_amount.value), payment_recipient.value.strip(), payment_method.value)
                payment_rows.controls.insert(0, ft.Text(f"{payment.reference} • KES {payment.amount:,.0f} • {payment.status}", color="#526257"))
                show(f"Payment request {payment.reference} created.")
                page.update()
            except (ValueError, TypeError):
                show("Enter a valid amount and recipient.", True)

        qr_label = ft.TextField(label="QR label", value="North field harvest batch", expand=True)
        qr_result = ft.Text("No QR payload created yet.", color="#526257", selectable=True)

        def create_qr(_: ft.ControlEvent) -> None:
            qr_result.value = commerce.qr_payload("farm", f"user-{user.id}", qr_label.value.strip() or "farm")
            page.update()

        plan_value = ft.Text("Professional plan", size=18, weight=ft.FontWeight.BOLD, color="#173E2B")

        def choose_upgrade(plan: str) -> None:
            plan_value.value = f"Selected plan: {plan}"
            show(f"{plan} selected. Connect billing to activate it.")
            page.update()

        automation_toggle = ft.Switch(label="Automatic data refresh", value=True)
        alerts_toggle = ft.Switch(label="Actionable alerts", value=True)
        language = ft.Dropdown(label="Language", value="English", options=[ft.dropdown.Option("English"), ft.dropdown.Option("Kiswahili")], width=220)

        workforce_page = ft.Column([
            ft.Text("Trusted farm workforce", size=22, weight=ft.FontWeight.BOLD, color="#173E2B"),
            ft.Text("Find skilled people, inspect their work history, and leave useful recommendations.", color="#526257"),
            ft.Row([worker_search, ft.FilledButton("Search", icon=ft.Icons.SEARCH, on_click=search_workers)], expand=True),
            worker_results,
        ], spacing=12, scroll=ft.ScrollMode.AUTO)

        marketplace_page = ft.Column([
            ft.Text("Farm marketplace", size=22, weight=ft.FontWeight.BOLD, color="#173E2B"),
            ft.Text("Buy inputs and equipment, or connect with verified sellers.", color="#526257"),
            ft.Row([listing_search, ft.FilledButton("Search", icon=ft.Icons.SEARCH, on_click=search_listings)], expand=True),
            listing_results,
            ft.Text("Orders and secure checkout", size=18, weight=ft.FontWeight.BOLD, color="#173E2B"),
            order_rows,
            ft.Divider(),
            ft.Text("Publish a buyer request", size=18, weight=ft.FontWeight.BOLD, color="#173E2B"),
            ft.Row([buyer_product, buyer_quantity, buyer_location, ft.FilledButton("Publish", icon=ft.Icons.POST_ADD, on_click=create_buyer_request)], wrap=True),
            request_rows,
        ], spacing=12, scroll=ft.ScrollMode.AUTO)

        sponsors_page = ft.Column([
            ft.Text("Sponsors and farm funding", size=22, weight=ft.FontWeight.BOLD, color="#173E2B"),
            ft.Text("Discover programs that support resilient farms and farmer livelihoods.", color="#526257"),
            *[ft.Container(content=ft.Column([
                ft.Row([ft.Text(sponsor.name, size=16, weight=ft.FontWeight.BOLD, color="#173E2B"), ft.Text("Verified", color="#2B7A4B")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Text(f"{sponsor.focus} • {sponsor.location}", size=12, color="#D9822B"),
                ft.Text(sponsor.description, size=12, color="#526257"),
                ft.TextButton("View eligibility", icon=ft.Icons.OPEN_IN_NEW, on_click=lambda _, name=sponsor.name: show(f"Eligibility checklist opened for {name}.")),
            ], spacing=6), padding=14, bgcolor="#F7FAF7", border_radius=14) for sponsor in commerce.sponsors],
        ], spacing=12, scroll=ft.ScrollMode.AUTO)

        payments_page = ft.Column([
            ft.Text("Payments and traceability", size=22, weight=ft.FontWeight.BOLD, color="#173E2B"),
            ft.Text("Create payment requests and generate scannable farm identity payloads.", color="#526257"),
            ft.Text("New payment", size=18, weight=ft.FontWeight.BOLD, color="#173E2B"),
            ft.Row([payment_amount, payment_recipient, payment_method, ft.FilledButton("Create request", icon=ft.Icons.PAYMENTS, on_click=create_payment)], wrap=True),
            payment_rows,
            ft.Divider(),
            ft.Text("QR identity and product traceability", size=18, weight=ft.FontWeight.BOLD, color="#173E2B"),
            ft.Row([qr_label, ft.FilledButton("Generate QR payload", icon=ft.Icons.QR_CODE_2, on_click=create_qr)], expand=True),
            qr_result,
        ], spacing=12, scroll=ft.ScrollMode.AUTO)

        settings_page = ft.Column([
            ft.Text("Settings and account", size=22, weight=ft.FontWeight.BOLD, color="#173E2B"),
            ft.Text("Control automation, language, security, and your commercial workspace.", color="#526257"),
            ft.Container(content=ft.Column([
                ft.Text("Automation", size=16, weight=ft.FontWeight.BOLD, color="#173E2B"), automation_toggle, alerts_toggle,
                ft.Text("These controls affect how the workspace presents synchronized data and alerts.", size=12, color="#526257"),
            ], spacing=8), padding=14, bgcolor="#F7FAF7", border_radius=14),
            ft.Container(content=ft.Column([
                ft.Text("Language and access", size=16, weight=ft.FontWeight.BOLD, color="#173E2B"), language,
                ft.Text("Sign in faster", size=14, weight=ft.FontWeight.BOLD, color="#214336"),
                ft.Row([ft.OutlinedButton("Continue with Google", icon=ft.Icons.ACCOUNT_CIRCLE, on_click=lambda _: show("OAuth provider connection is ready for configuration.")), ft.OutlinedButton("Continue with Microsoft", icon=ft.Icons.WORKSPACE_PREMIUM, on_click=lambda _: show("OAuth provider connection is ready for configuration."))], wrap=True),
            ], spacing=8), padding=14, bgcolor="#F7FAF7", border_radius=14),
            ft.Container(content=ft.Column([
                ft.Text("Plans and upgrades", size=16, weight=ft.FontWeight.BOLD, color="#173E2B"), plan_value,
                ft.Text("Unlock team workspaces, exportable reports, and advanced market monitoring.", size=12, color="#526257"),
                ft.Row([ft.OutlinedButton("Starter", on_click=lambda _: choose_upgrade("Starter")), ft.OutlinedButton("Professional", on_click=lambda _: choose_upgrade("Professional")), ft.FilledButton("Cooperative", icon=ft.Icons.GROUPS, on_click=lambda _: choose_upgrade("Cooperative"))], wrap=True),
            ], spacing=8), padding=14, bgcolor="#F7FAF7", border_radius=14),
        ], spacing=12, scroll=ft.ScrollMode.AUTO)

        job_title = ft.TextField(label="Work needed", expand=True)
        job_location = ft.TextField(label="Location", width=150)
        job_budget = ft.TextField(label="Budget", width=120)
        job_schedule = ft.TextField(label="Schedule", width=150)
        job_rows = ft.Column([], spacing=8)

        def refresh_jobs() -> None:
            job_rows.controls = []
            for job in commerce.jobs:
                job_rows.controls.append(ft.Container(content=ft.Row([
                    ft.Column([
                        ft.Text(job.title, size=14, weight=ft.FontWeight.BOLD, color="#173E2B"),
                        ft.Text(f"{job.location} • {job.schedule} • Budget {job.budget}", size=12, color="#526257"),
                        ft.Text(f"{len(job.applicants)} applicant(s) • {job.status}", size=11, color="#6A7A72"),
                    ], expand=True),
                    ft.FilledButton("Apply", icon=ft.Icons.HANDSHAKE, on_click=lambda _, item=job: (commerce.apply_for_job(item, user.name), show("Application submitted."), page.update())),
                ], spacing=10), padding=12, bgcolor="#F7FAF7", border_radius=12))

        def post_job(_: ft.ControlEvent) -> None:
            if not all(value.value.strip() for value in (job_title, job_location, job_budget, job_schedule)):
                show("Complete all job details.", True)
                return
            commerce.create_job(user.name, job_title.value, job_location.value, job_budget.value, job_schedule.value)
            for value in (job_title, job_location, job_budget, job_schedule):
                value.value = ""
            refresh_jobs()
            show("Job posted to the workforce.")
            page.update()

        refresh_jobs()
        jobs_page = ft.Column([
            ft.Text("Jobs and bookings", size=22, weight=ft.FontWeight.BOLD, color="#173E2B"),
            ft.Text("Farmers can post work; laborers can discover and apply.", color="#526257"),
            ft.Container(content=ft.Column([
                ft.Text("Post a job", size=16, weight=ft.FontWeight.BOLD, color="#173E2B"),
                ft.Row([job_title, job_location, job_budget, job_schedule, ft.FilledButton("Post job", icon=ft.Icons.POST_ADD, on_click=post_job)], wrap=True),
            ], spacing=8), padding=14, bgcolor="#F7FAF7", border_radius=14),
            job_rows,
        ], spacing=12, scroll=ft.ScrollMode.AUTO)

        notifications_page = ft.Column([
            ft.Text("Notification center", size=22, weight=ft.FontWeight.BOLD, color="#173E2B"),
            ft.Text("Grouped updates for orders, jobs, sponsors, alerts, and account activity.", color="#526257"),
            *[ft.Container(content=ft.Row([
                ft.Icon(ft.Icons.NOTIFICATIONS_ACTIVE if not notification.read else ft.Icons.NOTIFICATIONS_NONE, color="#2B7A4B"),
                ft.Column([ft.Text(notification.title, weight=ft.FontWeight.BOLD, color="#173E2B"), ft.Text(notification.message, size=12, color="#526257")], expand=True),
                ft.Text(notification.category, size=11, color="#D9822B"),
            ], spacing=10), padding=12, bgcolor="#F7FAF7", border_radius=12) for notification in commerce.notifications],
            ft.Divider(),
            ft.Text("Delivery channels", size=16, weight=ft.FontWeight.BOLD, color="#173E2B"),
            ft.Switch(label="Push notifications", value=True),
            ft.Switch(label="Email summaries", value=True),
            ft.Switch(label="SMS for payments and delivery", value=False),
        ], spacing=10, scroll=ft.ScrollMode.AUTO)

        admin_page = ft.Column([
            ft.Text("Admin command center", size=22, weight=ft.FontWeight.BOLD, color="#173E2B"),
            ft.Text("Moderate trust signals, review activity, and control platform features.", color="#526257"),
            ft.Row([
                build_metric_card("Users", "Active", "#2B7A4B", ft.Icons.PEOPLE),
                build_metric_card("Orders", str(len(commerce.orders)), "#2563EB", ft.Icons.SHOPPING_BAG),
                build_metric_card("Audit logs", str(len(commerce.audit_logs)), "#D9822B", ft.Icons.HISTORY),
            ], wrap=True),
            ft.Text("Feature flags", size=16, weight=ft.FontWeight.BOLD, color="#173E2B"),
            ft.Switch(label="Marketplace checkout", value=True),
            ft.Switch(label="Sponsor matching", value=True),
            ft.Switch(label="Automated alerts", value=True),
            ft.Text("Trust and moderation queue", size=16, weight=ft.FontWeight.BOLD, color="#173E2B"),
            ft.Text("No unresolved reports. New user reports, disputed orders, and review flags will appear here.", color="#526257"),
            ft.Text("Recent audit activity", size=16, weight=ft.FontWeight.BOLD, color="#173E2B"),
            *[ft.Text(f"{log.actor} • {log.action} • {log.target}", size=12, color="#526257") for log in commerce.audit_logs[:10]],
        ], spacing=10, scroll=ft.ScrollMode.AUTO)

        help_page = ft.Column([
            ft.Text("Help and support", size=22, weight=ft.FontWeight.BOLD, color="#173E2B"),
            ft.Text("Answers for everyday farm, marketplace, and account questions.", color="#526257"),
            ft.ExpansionTile(title=ft.Text("How do payments work?"), controls=[ft.Text("Payments are created as protected requests. Escrow should be funded before work or delivery begins.", color="#526257")]),
            ft.ExpansionTile(title=ft.Text("How do I trust a laborer or seller?"), controls=[ft.Text("Look for verified badges, completed work, ratings, written reviews, and the dispute path.", color="#526257")]),
            ft.ExpansionTile(title=ft.Text("Can I use the app offline?"), controls=[ft.Text("Recent recommendations, tasks, and account settings remain available locally. Sync integrations can be enabled as providers are configured.", color="#526257")]),
            ft.FilledButton("Contact support", icon=ft.Icons.SUPPORT_AGENT, on_click=lambda _: show("Support request started. A support channel can be connected in deployment.")),
            ft.TextButton("Terms of Service", on_click=lambda _: show("Terms page is ready for your organization policy.")),
            ft.TextButton("Privacy Policy", on_click=lambda _: show("Privacy page is ready for your organization policy.")),
        ], spacing=10, scroll=ft.ScrollMode.AUTO)

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

        common_tabs = [
            ft.Tab(text="Notifications", icon=ft.Icons.NOTIFICATIONS, content=notifications_page),
            ft.Tab(text="Help", icon=ft.Icons.HELP_OUTLINE, content=help_page),
            ft.Tab(text="Settings", icon=ft.Icons.SETTINGS, content=settings_page),
            ft.Tab(text="Profile", icon=ft.Icons.PERSON, content=ft.Column([name, department, semester, ft.FilledButton("Save profile", icon=ft.Icons.SAVE, on_click=update)], spacing=12)),
        ]
        role_tabs = [
            ft.Tab(text="Dashboard", icon=ft.Icons.HOME, content=dashboard),
            ft.Tab(text="Recommendation", icon=ft.Icons.SPA, content=ft.Column([ft.Text("Soil and climate inputs", size=20, weight=ft.FontWeight.BOLD), *inputs.values(), ft.FilledButton("Recommend a crop", icon=ft.Icons.AUTO_AWESOME, on_click=recommend), result, details], spacing=10)),
            ft.Tab(text="Workforce", icon=ft.Icons.GROUPS, content=workforce_page),
            ft.Tab(text="Jobs", icon=ft.Icons.WORK_HISTORY, content=jobs_page),
            ft.Tab(text="Marketplace", icon=ft.Icons.STORE, content=marketplace_page),
            ft.Tab(text="Sponsors", icon=ft.Icons.VOLUNTEER_ACTIVISM, content=sponsors_page),
            ft.Tab(text="Payments", icon=ft.Icons.PAYMENTS, content=payments_page),
        ]
        if user.role in {"Laborer", "Buyer", "Seller", "Sponsor"}:
            role_tabs = [tab for tab in role_tabs if tab.text not in {"Dashboard", "Recommendation"}]
        if user.role == "Laborer":
            role_tabs = [tab for tab in role_tabs if tab.text not in {"Sponsors"}]
        elif user.role == "Buyer":
            role_tabs = [tab for tab in role_tabs if tab.text not in {"Recommendation", "Sponsors", "Workforce"}]
        elif user.role == "Seller":
            role_tabs = [tab for tab in role_tabs if tab.text not in {"Recommendation", "Sponsors", "Workforce"}]
        elif user.role == "Sponsor":
            role_tabs = [tab for tab in role_tabs if tab.text not in {"Recommendation", "Workforce", "Jobs", "Marketplace"}]
        if user.role == "Admin":
            role_tabs = [ft.Tab(text="Admin", icon=ft.Icons.ADMIN_PANEL_SETTINGS, content=admin_page)] + role_tabs

        return ft.View("/home", [ft.Column([
            ft.Row([ft.Column([ft.Text(f"Hello, {user.name}", size=26, weight=ft.FontWeight.BOLD), ft.Text(f"{user.email} • {user.role} workspace", color="#526257")]), ft.TextButton("Log out", icon=ft.Icons.LOGOUT, on_click=logout)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Tabs(tabs=role_tabs + common_tabs, expand=1),
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
