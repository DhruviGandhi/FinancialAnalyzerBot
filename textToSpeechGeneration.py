# use genai_env

from gtts import gTTS

text = input("Enter text to convert into speech: ")

if text.strip() == "":
    print("Please enter some text.")
else:
    tts = gTTS(text=text, lang="en")
    tts.save("user_speech.mp3")
    print("Speech saved as user_speech.mp3")