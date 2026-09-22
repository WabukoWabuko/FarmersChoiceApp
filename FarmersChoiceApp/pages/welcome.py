# This page is for showing users a Welcome-to-The-App message/info.
import kivy as ft
import pyqt6
import tkinter as tk


def __view__():
    # At this point we return View with no need to create a Build function.
    return ft.View(
        '/welcome',
        controls=[
            ft.Column([
                # This Container is used to Display the 'Welcome' word
                    ft.Container(
                        alignment=ft.alignment.center,
                        content=ft.Column([
                            ft.Text("Welcome", font_family="ALGER", size=40),
                        ], alignment=ft.MainAxisAlignment.CENTER)
                    ),
                # This Container is used to Display the 'to' word
                    ft.Container(
                        alignment=ft.alignment.center,
                        content=ft.Column([
                            ft.Text("to", font_family="ALGER", size=25),
                        ], alignment=ft.MainAxisAlignment.CENTER)
                    ),
                # This Container is used to Display the "farmer's" word
                    ft.Container(
                        alignment=ft.alignment.center,
                        content=ft.Column([
                            ft.Text("Farmers' Choice App", font_family="ALGER", size=30),
                        ], alignment=ft.MainAxisAlignment.CENTER)
                    ),
                # This Container withholds an image.
                ft.Container(
                    alignment=ft.alignment.center,
                    content=ft.Image(
                        src="images/CropPicture.jpg", height=150, width=150
                    )
                ),
                # This Container contains all that junk info explaining about the App
                ft.Container(
                    alignment=ft.alignment.center,
                    content=ft.Text(
                        "This Farmers' app aids in \n"
                        "contribution to global food security\n"
                        " with a significant step towards \n"
                        "a more holistic and data-driven\n"
                        " approach to soil assessment \n"
                        "for bumper crop production."
                    , font_family="timesbi")
                ),
                # This container holds a button to move to the LOGIN/REGISTER page.
                    ft.Container(
                        alignment=ft.alignment.center,
                        content=ft.Row([
                            ft.Container(
                                content=ft.Column([
                                    ft.FilledButton(
                                        width=120,
                                        height=40,
                                        content=ft.Text("REGISTER"),
                                        on_click=lambda e: e.page.go("/register"),
                                    )
                                ]),
                            ),
                            ft.Container(
                                content=ft.Column([
                                    ft.FilledButton(
                                        width=120,
                                        height=40,
                                        content=ft.Text("LOGIN"),
                                        on_click=lambda e: e.page.go("/login"),
                                    )
                                ]),
                            ),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                    )
            ], alignment=ft.MainAxisAlignment.CENTER,
        )
    ]
)