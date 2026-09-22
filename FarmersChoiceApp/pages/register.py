# This page is for Registering new accounts.
import glob
import os

import mysql.connector
import tkinter as tk
import kivy as ft
import time as t
import hashlib
import pyqt6
from flet_core import page

import pages.home as home


def __view__():
    # called only to do a time counter for every TextField entry.
    def timerFunc():
        if FirstName:
            t.sleep(2)
            Text.value = ""
            FirstName.error_text = ""
            Text.update()
            FirstName.update()
        elif SecondName:
            t.sleep(2)
            Text.value = ""
            SecondName.error_text = ""
            Text.update()
            SecondName.update()
        elif EmailAddress:
            t.sleep(2)
            Text.value = ""
            EmailAddress.error_text = ""
            Text.update()
            EmailAddress.update()
        elif Password:
            t.sleep(2)
            Text.value = ""
            Text.update()
        elif ConfirmPassword:
            t.sleep(2)
            Text.value = ""
            Text.update()

    def SubmitRegisterDetails(e):
        # Checking Null values so as to return an error
        if not FirstName.value:
            Text.value = "Please fill your First Name."
            Text.update()
            FirstName.error_text = " "
            FirstName.update()
            t.sleep(2)
            FirstName.error_text, Text.value = "", ""
            FirstName.update()
            Text.update()
            #timerFunc()
        elif not SecondName.value:
            Text.value = "Please fill your Second Name."
            Text.update()
            SecondName.error_text = " "
            SecondName.update()
            t.sleep(2)
            SecondName.error_text, Text.value = "", ""
            SecondName.update()
            #timerFunc()
        elif not EmailAddress.value or " " in EmailAddress.value or "@gmail.com" not in EmailAddress.value:
            Text.value = "Write the correct Email Address"
            Text.update()
            EmailAddress.error_text = " "
            EmailAddress.update()
            t.sleep(2)
            EmailAddress.error_text, Text.value = "", ""
            EmailAddress.update()
            #timerFunc()
        elif not Password.value:
            Text.value = "Insert password"
            Text.update()
            Password.error_text = " "
            Password.update()
            t.sleep(2)
            Password.error_text, Text.value = "", ""
            Password.update()
            #timerFunc()
        elif not ConfirmPassword.value:
            Text.value = "Confirm password"
            Text.update()
            ConfirmPassword.error_text = " "
            ConfirmPassword.update()
            t.sleep(2)
            ConfirmPassword.error_text, Text.value = "", ""
            ConfirmPassword.update()
            #timerFunc()
        elif Password.value != ConfirmPassword.value:
            ConfirmPassword.error_text = "Password does not match!!"
            Password.error_text = "Password does not match!!"
            ConfirmPassword.update()
            Password.update()
            t.sleep(2)
            ConfirmPassword.error_text, Password.error_text = "", ""
            ConfirmPassword.update()
            Password.update()
        else:
            hashing_pass()
            DBConnection()
            FirstName.error_text, FirstName.value = "", ""
            FirstName.update()
            SecondName.error_text, SecondName.value = "", ""
            SecondName.update()
            EmailAddress.error_text, EmailAddress.value = "", ""
            EmailAddress.update()
            Password.error_text, Password.value = "", ""
            Password.update()
            ConfirmPassword.error_text, ConfirmPassword.value = "", ""
            ConfirmPassword.update()
            t.sleep(1)
            Text.value = ""
            Text.update()
            FirstName.autofocus = True

    def DBConnection():
        global connection
        try:
            connection = mysql.connector.connect(host='localhost', database='farmersapp', user='root', password='',
                                                 port=3306)

            myCursor = connection.cursor()
            myCursor.execute(f"SELECT * FROM local_farmer_user WHERE emailaddress = '{EmailAddress.value}';")
            checkEmailAddress = myCursor.fetchone()
            # This command is to confirm if the email entered is already available in the DB or NOT
            if checkEmailAddress:
                Text.value = "Email Address is Already Registered."
                Text.update()
            else:
                myCursor.execute(
                    f"INSERT INTO local_farmer_user VALUES('{FirstName.value}', '{SecondName.value}', '{EmailAddress.value}', '{Password.value}');")
                # Moving to the appropriate page
        except mysql.connector.Error:
            Text.value = "Database Connection Error. Hold on!"
            Text.update()
        finally:
            if connection.is_connected():
                connection.commit()
                connection.close()

    def hashing_pass():
        password_bytes = (Password.value).encode('utf-8')
        Password.value = hashlib.shake_256(password_bytes).hexdigest(20)
        Password.update()

    FirstName = ft.TextField(label="First Name", width=150, height=45, border_radius=25,
                             border_color=ft.colors.BLUE_900, autofocus=True)
    SecondName = ft.TextField(label="Second Name", width=150, height=45, border_radius=25,
                              border_color=ft.colors.BLUE_900)
    EmailAddress = ft.TextField(label="Email Address", hint_text="johndoe@gmail.com", width=300, height=45,
                                border_radius=25, border_color=ft.colors.BLUE_900)
    Password = ft.TextField(label="Password", width=300, height=45, border_radius=25, border_color=ft.colors.BLUE_900,
                            password=True, can_reveal_password=True)
    # Should remove this on_submit= , it is a cooked thing 😂😂😂I just wanna graduate 🚮🥱😴😩😪😫
    ConfirmPassword = ft.TextField(label="Confirm Password", width=300, height=45, border_radius=25,
                                   border_color=ft.colors.BLUE_900, password=True, on_submit=lambda _: _.page.go("/home")) # Upon clicking ENTER key, it performs an action.
    SubmitButton = ft.FilledButton("Register", on_click=SubmitRegisterDetails)
    Text = ft.Text(font_family="timesbi", color=ft.colors.RED_900)

    register = ft.Container(
        content=ft.Column([
            # Icon that is to move back to the welcome page
            ft.Container(ft.Row([
                ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda e: e.page.go("/welcome"))
            ], alignment=ft.MainAxisAlignment.START)),

            # Displays Image of a farmer.
            ft.Container(ft.Row([
                ft.Image(src="images/icons/SecurityRegister.png", height=100, width=150)
            ], alignment=ft.MainAxisAlignment.CENTER)),

            # Displays the info 'Create Account'.
            ft.Container(ft.Row([
                ft.Text("Create Account", font_family="ALGER", size=30)
            ], alignment=ft.MainAxisAlignment.CENTER)),
            # This Container has a row containing First and Second names Text fields.

            ft.Container(
                ft.Row(
                    [
                        FirstName,
                        SecondName,
                    ], alignment=ft.MainAxisAlignment.CENTER)),

            # This Container withholds email address textfield
            ft.Container(ft.Row([
                EmailAddress,
            ], alignment=ft.MainAxisAlignment.CENTER)),

            # This Container withholds password textfield
            ft.Container(ft.Row([
                Password,
            ], alignment=ft.MainAxisAlignment.CENTER)),

            # This Container withholds confirm password textfield
            ft.Container(ft.Row([
                ConfirmPassword,
            ], alignment=ft.MainAxisAlignment.CENTER)),

            # This Container is for displaying the error texts arising.
            ft.Container(ft.Row([
                Text,
            ], alignment=ft.MainAxisAlignment.CENTER)),

            # This Container withholds submit button
            ft.Container(ft.Row([
                SubmitButton,
            ], alignment=ft.MainAxisAlignment.CENTER), ),

            # Don't have an account?
            ft.Container(ft.Row([
                ft.Text("Have an Account? "),
                ft.TextButton("Login", on_click=lambda e: e.page.go("/login"))
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
        '/welcome',
        controls=[
            register,
            ft.Text("Copyright © 2024- WabukoWabuko Softwares Dev.")
        ]
    )
