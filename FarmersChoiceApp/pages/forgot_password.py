# This page is for Registering new accounts.
import kivy as ft
import pyqt6
import tkinter as tk


def __view__():
    EmailAddress = ft.TextField(label="Email Address", hint_text="johndoe@gmail.com", width=300,
                                border_radius=25, border_color=ft.colors.BLUE_900)

    login = ft.Container(
        content=ft.Column([
            # Icon that is to move back to the welcome page
            ft.Container(ft.Row([
                ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda e: e.page.go("/login"))
            ], alignment=ft.MainAxisAlignment.START)),

            # Image for the page
            ft.Container(ft.Row([
                ft.Image(src="images/icons/reset_password.png", height=200, width=100),
            ], alignment=ft.MainAxisAlignment.CENTER)),
            # Forgot Password
            ft.Container(ft.Row([
                ft.Text("FORGOT PASSWORD", font_family="ALGER", size=30),
            ], alignment=ft.MainAxisAlignment.CENTER)),
            # Text
            ft.Container(ft.Row([
                ft.Text("Please enter your email address to reset your password"),
            ], alignment=ft.MainAxisAlignment.CENTER)),
            # Email Address TextField
            ft.Container(ft.Row([
                EmailAddress,
            ], alignment=ft.MainAxisAlignment.CENTER)),
            # Submit Button
            ft.Container(ft.Row([
                ft.FilledButton("Submit", width=200),
            ], alignment=ft.MainAxisAlignment.CENTER)),
            # back to login page
            ft.Container(ft.Row([
                ft.Text("Back to Login"),
                ft.IconButton(ft.icons.ARROW_FORWARD, bgcolor=ft.colors.LIGHT_BLUE_700, on_click=lambda e: e.page.go("/login"))
            ], alignment=ft.MainAxisAlignment.CENTER)),
        ]),  # --------column
            gradient=ft.LinearGradient(
            begin=ft.alignment.top_center,
            end=ft.alignment.bottom_center,
            colors=[f"{ft.colors.LIGHT_BLUE_900}", f"{ft.colors.LIGHT_GREEN_900}"]
        ),
        width=400,
        height=580,
        border_radius=40,
    )

    # At this point we return View with no need to create a Build function.
    return ft.View(
        '/login',
        controls=[
            login,
            ft.Text("Copyright © 2024- WabukoWabuko Softwares Dev."),
        ]
    )

