# This page is for Registering new accounts.
from datetime import datetime, timedelta, date
import kivy as ft
import mysql.connector
import time as t
import random
import pyqt6
import tkinter as tk


def __view__():
    def RandomCropPrediction():
        """Creates a new array of 7 integer values, performs a random operation for crop prediction,
           and generates an output with recommended crop and planting timespan."""

        # Create a new array with 7 random integer values (replace with actual data input if available)
        data_array = [random.randint(1, 100) for _ in range(7)]

        # Perform a random operation for crop prediction (replace with your actual prediction logic)
        predicted_crop = random.choice(["Banana", "Jute", "Coffee", "Orange", "Papaya", "Coconut", "Grapes", "Watermelon", "Muskmelon", "Apple", "Mango", "Rice", "Chick Pea", "Maize", "Kidney Beans", "Pigeon Peas", "Moth Beans", "Mungbean", "Blackgram", "Lentil", "pomegranate", ""])
        timespan_of_planting_crop_in_weeks = random.randint(1, 4)
        timespan_of_planting_crop_in_days = random.randint(1, 20)
        date_request = date.today()

        # Generate the output with recommended crop and planting timespan
        output = f"""Plant {predicted_crop} between {date_request} and {date_request + timedelta(weeks=timespan_of_planting_crop_in_weeks, days=timespan_of_planting_crop_in_days)}."""
        randomCrop.value = f"{output}"
        randomCrop.update()
        print(output)

    def RaiseErrorOnString(e): # Remove this later on.
        Text.value = "Check your inputs, should be in integer form."
        Text.update()
        t.sleep(2)
        Text.value = ""
        Text.update()

    def CollectData(e):
        # Checking Null values so a to return an error
        """elif not ph.value:
                    ph.error_text = " "
                    ph.update()
                    t.sleep(2)
                    ph.error_text, Text.value = "", ""
                    ph.update()
        if not temperature.value:
            temperature.error_text = " "
            temperature.update()
            t.sleep(2)
            temperature.error_text, Text.value = "", ""
            temperature.update()
            Text.update()
        if not humidity.value:
            Text.value = "Please insert humidity values."
            Text.update()
            humidity.error_text = " "
            humidity.update()
            t.sleep(2)
            humidity.error_text, Text.value = "", ""
            humidity.update()
            Text.update()"""

        if not rainfall.value:
            Text.value = "Please insert humidity values."
            Text.update()
            rainfall.error_text = " "
            rainfall.update()
            t.sleep(2)
            rainfall.error_text, Text.value = "", ""
            rainfall.update()
            Text.update()
        elif not nitrogen.value:
            Text.value = "Please insert nitrogen values."
            Text.update()
            nitrogen.error_text = " "
            nitrogen.update()
            t.sleep(2)
            nitrogen.error_text, Text.value = "", ""
            nitrogen.update()
            Text.update()
            # timerFunc()
        elif not phosphorus.value:
            Text.value = "Please insert phosphorus values."
            Text.update()
            phosphorus.error_text = " "
            phosphorus.update()
            t.sleep(2)
            phosphorus.error_text, Text.value = "", ""
            phosphorus.update()
            Text.update()
            # timerFunc()
        elif not potassium.value:
            Text.value = "Please insert potassium values."
            Text.update()
            potassium.error_text = " "
            potassium.update()
            t.sleep(2)
            potassium.error_text, Text.value = "", ""
            potassium.update()
            Text.update()
            # timerFunc()
        else:
            DBConnection()
            temperature.error_text, temperature.value = "", ""
            temperature.update()
            humidity.error_text, humidity.value = "", ""
            humidity.update()
            rainfall.error_text, rainfall.value = "", ""
            rainfall.update()
            ph.error_text, ph.value = "", ""
            ph.update()
            nitrogen.error_text, nitrogen.value = "", ""
            nitrogen.update()
            phosphorus.error_text, phosphorus.value = "", ""
            phosphorus.update()
            potassium.error_text, potassium.value = "", ""
            potassium.update()
            t.sleep(1)
            Text.value = ""
            Text.update()

    # Database connection to insert user data
    def DBConnection():
        global connection
        try:
            connection = mysql.connector.connect(host='localhost', database='farmersapp', user='root', password='',
                                                 port=3306)

            myCursor = connection.cursor()
            sql = ("INSERT INTO previous_predictions (temperature, humidity, rainfall, ph, nitrogen, phosphorus, "
                   "potassium) VALUES (%s, %s, %s, %s, %s, %s, %s)")
            values = (temperature.value, humidity.value, rainfall.value, ph.value, nitrogen.value, phosphorus.value,
                      potassium.value)
            myCursor.execute(sql, values)
            connection.commit()  # Commit the changes to the database
            myCursor.close()
            connection.close()
            RandomCropPrediction()
            # Moving to the appropriate page
        except mysql.connector.Error:
            Text.value = "Error connecting to Database."
        finally:
            if connection.is_connected():
                connection.commit()
                connection.close()

    temperature = ft.Slider(label="{value}°C", width=270, height=40, min=0, max=90, divisions=45)
    humidity = ft.Slider(label="{value}%", width=270, height=40, min=0, max=100, divisions=100)
    rainfall = ft.TextField(label="rainfall", width=270, height=40,
                            border_radius=30, border_color=ft.colors.BLUE_900, suffix_text="in mm")
    ph = ft.Slider(label="{value}", width=270, height=40, min=0, max=14, divisions=14)
    nitrogen = ft.TextField(label="nitrogen", width=270, height=40,
                            border_radius=30, border_color=ft.colors.BLUE_900, suffix_text="in kg/ha")
    phosphorus = ft.TextField(label="phosphorus", width=270, height=40,
                              border_radius=30, border_color=ft.colors.BLUE_900, suffix_text="in kg/ha")
    potassium = ft.TextField(label="potassium", width=270, height=40, on_submit=RaiseErrorOnString,
                             border_radius=30, border_color=ft.colors.BLUE_900, suffix_text="in kg/ha")
    Text = ft.Text(font_family="timesbi", color=ft.colors.RED_900)
    randomCrop = ft.Text(font_family="timesbi", color=ft.colors.WHITE70)

    recommendationButton = ft.FilledButton("Recommendations", on_click=CollectData)

    home = ft.Container(
        content=ft.Column([
            # Icon that is to move back to the welcome page
            ft.Container(ft.Row([
                ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda e: e.page.go("/login"))
            ], alignment=ft.MainAxisAlignment.START)),

            ft.Container(ft.Row([
                ft.Text("Generate Crop Recommendation", font_family="ALGER", size=20),
            ], alignment=ft.MainAxisAlignment.CENTER)),

            ft.Container(ft.Row([
                ft.Column([
                    ft.Text("temperature", size=10),
                    ft.Image(src="images/icons/celsius.png", height=30, width=30),
                ]),
                temperature
            ], alignment=ft.MainAxisAlignment.SPACE_EVENLY)),

            ft.Container(ft.Row([
                ft.Image(src="images/icons/humidity.png", height=30, width=30),
                humidity
            ], alignment=ft.MainAxisAlignment.SPACE_EVENLY)),

            ft.Container(ft.Row([
                ft.Image(src="images/icons/rainfall.png", height=30, width=30),
                rainfall
            ], alignment=ft.MainAxisAlignment.SPACE_EVENLY)),

            ft.Container(ft.Row([
                ft.Image(src="images/icons/ph-meter.png", height=30, width=30),
                ph
            ], alignment=ft.MainAxisAlignment.SPACE_EVENLY)),

            ft.Container(ft.Row([
                ft.Image(src="images/icons/nitrogen.png", height=30, width=30),
                nitrogen
            ], alignment=ft.MainAxisAlignment.SPACE_EVENLY)),

            ft.Container(ft.Row([
                ft.Image(src="images/icons/phosphorus.png", height=30, width=30),
                phosphorus
            ], alignment=ft.MainAxisAlignment.SPACE_EVENLY)),

            ft.Container(ft.Row([
                ft.Image(src="images/icons/potassium.png", height=30, width=30),
                potassium
            ], alignment=ft.MainAxisAlignment.SPACE_EVENLY)),

            ft.Container(ft.Row([
                Text,
            ], alignment=ft.MainAxisAlignment.SPACE_EVENLY)),

            ft.Container(ft.Row([
                recommendationButton
            ], alignment=ft.MainAxisAlignment.CENTER)),

            ft.Container(ft.Row([
                randomCrop,
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
        '/home',
        controls=[
            home,
            ft.Text("Copyright © 2024- WabukoWabuko Softwares Dev.")
        ]
    )