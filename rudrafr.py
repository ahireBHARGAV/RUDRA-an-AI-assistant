import tkinter as tk
from tkinter import ttk, scrolledtext
import threading  
import queue
import pyttsx3
import datetime
import speech_recognition as sr
import wikipedia
import webbrowser
import os
import google.generativeai as genai

class Rudra:
    def __init__(self, root):
        self.root = root
        self.root.title("Rudraa AI Assistant")
        self.root.geometry("800x600")
        self.root.configure(bg="#f0f2f5")

        # Initialize speech engine
        self.engine = pyttsx3.init('sapi5')
        self.voices = self.engine.getProperty('voices')
        self.engine.setProperty('voice', self.voices[1].id)

        # Initialize Gemini
        genai.configure(api_key='AIzaSyCN2vC0PAItlvxQvmGBlKxkcT8yxXVnlQY')
        self.model = genai.GenerativeModel("gemini-1.5-flash")

        self.msg_queue = queue.Queue()

        self.setup_gui()
        self.listening = False

        # Start message processing
        self.process_messages()

        self.wishme()

    def setup_gui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Chat display
        self.chat_display = scrolledtext.ScrolledText(
            main_frame,

            wrap=tk.WORD,
            width=50,
            height=20,
            font=("Helvetica", 10),
            bg="bisque2"
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Status
        self.status_label = ttk.Label(
            main_frame,
            text="Ready",
            font=("Helvetica", 10)
        )
        self.status_label.pack(pady=5)

        # Text input frame
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=5)

        # Text entry
        self.text_entry = ttk.Entry(
            input_frame,
            font=("Helvetica", 10)
        )
        self.text_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.text_entry.bind('<Return>', lambda e: self.send_message())

        # Send button
        send_button = ttk.Button(
            input_frame,
            text="Send",
            command=self.send_message
        )
        send_button.pack(side=tk.RIGHT)

        # Button frame (moved after text input)
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        # Listen button
        self.listen_button = ttk.Button(
            button_frame,
            text="Start Listening",
            command=self.toggle_listening
        )
        self.listen_button.pack(side=tk.LEFT, padx=5)

        # Clear
        clear_button = ttk.Button(
            button_frame,
            text="Clear Chat",
            command=self.clear_chat
        )
        clear_button.pack(side=tk.LEFT, padx=5)

        # Exit
        exit_button = ttk.Button(
            button_frame,
            text="Exit",
            command=self.root.quit
        )
        exit_button.pack(side=tk.RIGHT, padx=5)

    def speak(self, audio):
        def speak_thread():
            try:
                self.engine.say(audio)
                self.engine.runAndWait()
            except RuntimeError:
                # If engine is busy, create a new instance
                engine = pyttsx3.init('sapi5')
                engine.setProperty('voice', self.voices[1].id)
                engine.say(audio)
                engine.runAndWait()

        threading.Thread(target=speak_thread, daemon=True).start()
    
    #greet krne wala fun 
    def wishme(self):
        hour = int(datetime.datetime.now().hour)
        if hour <= 12 and hour > 0:
            greeting = "Good morning My Lord"
        elif hour > 12 and hour < 18:
            greeting = "Good afternoon My Lord"
        else:
            greeting = "Good evening My Lord"

        self.update_chat("Assistant: " + greeting)
        welcome = "Rudraa is at your service. How can I help you?"
        self.update_chat("Assistant: " + welcome)
        self.speak(greeting + ". " + welcome)

    def toggle_listening(self):
        if not self.listening:
            self.listening = True
            self.listen_button.configure(text="Stop Listening")
            self.status_label.configure(text="Listening...")
            threading.Thread(target=self.listen_loop, daemon=True).start()
        else:
            self.listening = False
            self.listen_button.configure(text="Start Listening")
            self.status_label.configure(text="Ready")

    def listen_loop(self):
        while self.listening:
            query = self.audio_command()
            if query != "None":
                self.process_command(query)

    def audio_command(self):
        r = sr.Recognizer()
        with sr.Microphone() as source:
            self.msg_queue.put(("status", "Listening..."))

            r.adjust_for_ambient_noise(source, duration=0.5)
            #duration
            r.pause_threshold = 0.8
            #intencity
            r.energy_threshold = 4000
            try:
                audio = r.listen(source, timeout=5, phrase_time_limit=5)
                self.msg_queue.put(("status", "Recognizing..."))
                query = r.recognize_google(audio, language='en-in')
                self.update_chat(f"You: {query}")
                return query.lower()
            except sr.WaitTimeoutError:
                self.msg_queue.put(("status", "Timeout - No speech detected"))
                return "None"
            except sr.UnknownValueError:
                self.msg_queue.put(("status", "Could not understand audio"))
                return "None"
            except sr.RequestError as e:
                self.msg_queue.put(("status", f"Could not request results; {e}"))
                return "None"
            except Exception as e:
                self.msg_queue.put(("status", "Ready"))
                return "None"

    def process_command(self, query):
        if "tell me about" in query:
            topic = query.replace("tell me about", "").strip()
            try:
                results = wikipedia.summary(topic, sentences=2)
                self.update_chat("Assistant: According to Wikipedia:")
                self.update_chat(results)
                self.speak("According to Wikipedia: " + results)
            except:
                response = "Sorry, I couldn't find information about that topic."
                self.update_chat("Assistant: " + response)
                self.speak(response)

        elif "open" in query:
            # Handle application opening first
            apps = {
                "python ide": "C:\\Program Files\\JetBrains\\PyCharm Community Edition 2024.3.1\\bin\\pycharm64.exe",
                "cap cut": "C:\\Users\\sai\\AppData\\Local\\CapCut\\Apps\\CapCut.exe",
                "brave": "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"
            }

            # Extract word after "open"
            app_name = query.replace("open", "").strip()
            
            # Check for apps first
            for app, path in apps.items():
                if app in app_name:
                    try:
                        os.startfile(path)
                        response = f"Opening {app}"
                        self.update_chat("Assistant: " + response)
                        self.speak(response)
                        return  # Exit the function after opening app
                    except FileNotFoundError:
                        response = f"Sorry, couldn't find {app} at {path}"
                        self.update_chat("Assistant: " + response)
                        self.speak(response)
                        return
                    except Exception as e:
                        response = f"Error opening {app}: {str(e)}"
                        self.update_chat("Assistant: " + response)
                        self.speak(response)
                        return

            # If no app was found, try opening as website
            sites = {
                "youtube": "https://www.youtube.com",
                "linkedin": "https://www.linkedin.com",
                "instagram": "https://www.instagram.com",
                "replit": "https://www.replit.com",
                "high anime": "https://www.hianime.to",
                "spotify": "https://www.spotify.com"
            }

            website = app_name  # Use the same extracted name
            if website in sites:
                url = sites[website]
            elif website.endswith(('.com')):
                url = website
            else:
                url = f"https://www.{website}.com"

            try:
                webbrowser.open(url)
                response = f"Opening {website}"
                self.update_chat("Assistant: " + response)
                self.speak(response)
            except Exception as e:
                response = f"Sorry, I couldn't open {website}"
                self.update_chat("Assistant: " + response)
                self.speak(response)

        elif any(phrase in query for phrase in ["turn off", "power off", "get lost"]):
            response = "Goodbye!"
            self.update_chat("Assistant: " + response)
            self.speak(response)
            self.root.after(2000, self.root.quit)


        else:
            try:
                response = self.model.generate_content(query)
                self.update_chat("Assistant: " + response.text)
                self.speak(response.text)
            except Exception as e:
                response = "I'm sorry, I couldn't process that request."
                self.update_chat("Assistant: " + response)
                self.speak(response)

    def update_chat(self, message):
        self.msg_queue.put(("chat", message))

    def process_messages(self):
        try:
            while True:
                msg_type, message = self.msg_queue.get_nowait()
                if msg_type == "chat":
                    self.chat_display.insert(tk.END, message + "\n")
                    self.chat_display.see(tk.END)
                elif msg_type == "status":
                    self.status_label.configure(text=message)
                self.msg_queue.task_done()
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_messages)

    def clear_chat(self):
        self.chat_display.delete(1.0, tk.END)

    def send_message(self):
        message = self.text_entry.get().strip()
        if message:
            self.update_chat(f"You: {message}")
            self.text_entry.delete(0, tk.END)
            self.process_command(message.lower())

if __name__ == "__main__":
    root = tk.Tk()
    app = Rudra(root)
    root.mainloop()