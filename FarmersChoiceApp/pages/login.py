# This page is for Registering new accounts.
import kivy_core.page
import mysql.connector
import time as t
import tkinter as tk
import kivy as ft
import hashlib
import main
import pyqt6


def __view__():
    def SubmitLoginDetails(e):
        # Checking if the following requirements are not included in the EmailAddress TextField
        if not EmailAddress.value or " " in EmailAddress.value or "@gmail.com" not in EmailAddress.value:
            Error_Text.value = "Enter a valid Email Address."
            EmailAddress.error_text = " "
            EmailAddress.update()
            Error_Text.update()
            t.sleep(2)
            EmailAddress.error_text, Error_Text.value = "", ""
            EmailAddress.update()
            Error_Text.update()
            #timerFunc()
        elif not Password.value:
            Error_Text.value = "Enter Password."
            Password.error_text = " "
            Password.update()
            Error_Text.update()
            t.sleep(2)
            Password.error_text, Error_Text.value = "", ""
            Password.update()
            Error_Text.update()
            #timerFunc()
        else:
            hashing_pass()
            DBConnection()
            EmailAddress.error_text, EmailAddress.value = "", ""
            EmailAddress.update()
            Password.error_text, Password.value = "", ""
            Password.update()
            t.sleep(4)
            Error_Text.value = ""
            Error_Text.update()

    # Database connection to verify Login credentials
    def DBConnection():
        connection = mysql.connector.connect(host='localhost', database='farmersapp', user='root', password='',
                                             port=3306)
        myCursor = connection.cursor()
        myCursor.execute(f"SELECT password FROM local_farmer_user WHERE emailaddress = '{EmailAddress.value}';")
        passwordFromDB = myCursor.fetchone()
        for row in passwordFromDB:
            if Password.value == row:
                # Insert Code here
                # print(f"{EmailAddress.value} available.")
                # Create a dialogue button
                Success_Text.value = "Login Successful."
                Success_Text.update()
                t.sleep(2)
                Success_Text.value = ""
                Success_Text.update()

            elif Password.value != row:
                #Insert Code Here
                # print(f"{EmailAddress.value} Not Available.")
                Error_Text.value = "Wrong Password or Email."
                Error_Text.update()

    def hashing_pass():
        password_bytes = (Password.value).encode('utf-8')
        Password.value = hashlib.shake_256(password_bytes).hexdigest(20)
        Password.update()

    EmailAddress = ft.TextField(label="Email Address", hint_text="johndoe@gmail.com", width=300,
                                border_radius=25, border_color=ft.colors.BLUE_900)
    # Should remove this on_submit= , it is a cooked thing 😂😂😂I just wanna graduate 🚮🥱😴😩😪😫
    Password = ft.TextField(label="Password", width=300, border_radius=25, border_color=ft.colors.BLUE_900,
                            password=True, can_reveal_password=True, on_submit=lambda _: _.page.go("/home"))

    SubmitButton = ft.FilledButton("Login", on_click=SubmitLoginDetails)
    RememberMe = ft.Checkbox(label="Remember Me", value=False)
    Error_Text = ft.Text(font_family="timesbi", color=ft.colors.RED_900)
    Success_Text = ft.Text(font_family="timesbi", color=ft.colors.BLUE_200)

    login = ft.Container(
        content=ft.Column([
            # Icon that is to move back to the welcome page
            ft.Container(ft.Row([
                ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda e: e.page.go("/welcome"),)
            ], alignment=ft.MainAxisAlignment.START)),
            # Displays Image of a farmer.
            ft.Container(ft.Row([
                ft.Image(src="images/icons/SecurityLogin.png", height=100, width=200)
            ], alignment=ft.MainAxisAlignment.CENTER)),
            # Displays the info 'Create Account'.
            ft.Container(ft.Row([
                ft.Text("LOGIN", font_family="ALGER", size=30)
            ], alignment=ft.MainAxisAlignment.CENTER)),
            # This Container withholds email address textfield
            ft.Container(ft.Row([
                EmailAddress,
            ], alignment=ft.MainAxisAlignment.CENTER)),
            # This Container withholds password textfield
            ft.Container(ft.Row([
                Password,
            ], alignment=ft.MainAxisAlignment.CENTER)),
            # Remember Me
            ft.Container(ft.Row([
                RememberMe,
            ], alignment=ft.MainAxisAlignment.START)),
            # This Container is for displaying the error texts arising.
            ft.Container(ft.Row([
                Error_Text,
                Success_Text,
            ], alignment=ft.MainAxisAlignment.CENTER)),
            # This Container withholds submit button
            ft.Container(ft.Row([
                SubmitButton,
            ], alignment=ft.MainAxisAlignment.CENTER)),
            # Don't have an account?
            ft.Container(ft.Row([
                ft.Text("Don't have an Account? "),
                ft.TextButton("Register", on_click=lambda e: e.page.go("/register"))
            ], alignment=ft.MainAxisAlignment.CENTER)),
            # Forgot your password?
            ft.Container(ft.Row([
                ft.Text("Forgot Password ?"),
                ft.IconButton(ft.icons.ARROW_FORWARD, bgcolor=ft.colors.LIGHT_BLUE_700, on_click=lambda e: e.page.go("/forgot_password"))
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
            ft.Text("Copyright © 2024- WabukoWabuko Softwares Dev.")
        ]
    )
