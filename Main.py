from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.graphics.texture import Texture
import cv2
import mediapipe as mp
from PIL import Image as PILImage
from kivy.core.window import Window
from kivy.core.text import LabelBase

# Import libraries for Arabic reshaping and bidirectional text
import arabic_reshaper
from bidi.algorithm import get_display

# Register an Arabic-supported font
LabelBase.register(name="arabic", fn_regular="Amiri-Regular.ttf")  # Ensure the font file is available

# Set the window size
Window.size = (400, 600)

class SignLanguageApp(App):

    def build(self):
        # Set up layout
        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        # Camera view for live video feed
        self.img = Image(size_hint=(1, .8))
        layout.add_widget(self.img)

        # Label to show detected sign with Arabic font
        self.status = Label(text=self.get_rtl_text('لم يتم اكتشاف إشارة'), size_hint=(1, .1), font_size='20sp', font_name="arabic", halign="right")
        layout.add_widget(self.status)

        # Live and Exit buttons with Arabic font
        btn_layout = BoxLayout(size_hint=(1, .1))
        self.btn_live = Button(text=self.get_rtl_text("ابدأ مباشرة"), on_press=self.start_camera, font_name="arabic")
        btn_exit = Button(text=self.get_rtl_text("خروج"), on_press=self.stop_camera, font_name="arabic")
        btn_layout.add_widget(self.btn_live)
        btn_layout.add_widget(btn_exit)

        layout.add_widget(btn_layout)

        # Initialize MediaPipe and Camera
        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands()
        self.cap = cv2.VideoCapture(0)

        return layout

    def get_rtl_text(self, text):
        # Reshape and reverse text for proper display in Arabic
        reshaped_text = arabic_reshaper.reshape(text)  # Reshape letters
        bidi_text = get_display(reshaped_text)  # Get bidirectional text
        return bidi_text

    def start_camera(self, *args):
        # Disable the "Live" button
        self.btn_live.disabled = True

        # Schedule live feed updates
        Clock.schedule_interval(self.update_frame, 1.0 / 30.0)

    def stop_camera(self, *args):
        # Stop the app and camera feed
        self.cap.release()
        self.stop()

        # Re-enable the "Live" button when the camera stops
        self.btn_live.disabled = False
        
    def update_frame(self, *args):
        ret, frame = self.cap.read()
        if not ret:
            return

        # Convert the frame to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process the frame for hand detection
        results = self.hands.process(frame_rgb)

        message = self.get_rtl_text("لم يتم اكتشاف إشارة")
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Get landmarks and detect sign
                lm_list = [lm for lm in hand_landmarks.landmark]
                message = self.get_rtl_text(self.detect_sign(lm_list))

        # Convert to PIL image to update Kivy image widget
        buf = cv2.flip(frame, 0).tostring()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='rgb')
        texture.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')
        self.img.texture = texture

        # Update the status label with the detected sign
        self.status.text = message

    def detect_sign(self, lm_list):
        """ Detect signs based on landmarks. """
        if lm_list[8].y < lm_list[7].y and lm_list[12].y < lm_list[11].y:  # Peace sign
            if lm_list[16].y > lm_list[15].y and lm_list[20].y > lm_list[19].y:
                return "نعم، لقد فزنا."

        if lm_list[8].y < lm_list[7].y and lm_list[20].y < lm_list[19].y:  # I love you sign
            if lm_list[12].y > lm_list[11].y and lm_list[16].y > lm_list[15].y:
                if lm_list[4].x < lm_list[3].x:
                    return "أنا أحبك!"

        if lm_list[4].y < lm_list[3].y:  # Thumbs up
            if lm_list[8].y > lm_list[6].y and lm_list[12].y > lm_list[10].y:
                return "أعجبني!"
            
        if lm_list[4].y > lm_list[3].y:  # Thumb pointing down
            if lm_list[8].y > lm_list[6].y and lm_list[12].y > lm_list[10].y and lm_list[16].y > lm_list[14].y and lm_list[20].y > lm_list[18].y:  # Other fingers folded down
                return "لم يعجبني"
    
    # Check for "Stop" gesture (All fingers straight up)
        if lm_list[8].y < lm_list[6].y and lm_list[12].y < lm_list[10].y:  # Index and middle up
            if lm_list[16].y < lm_list[14].y and lm_list[20].y < lm_list[18].y:  # Ring and pinky up
                if lm_list[4].x < lm_list[3].x:  # Thumb extended
                    return "توقف!"  # Stop gesture detected
    
    # Check for "OK" (👌) sign (Thumb and index finger form a circle, others stretched)
        if lm_list[4].x - lm_list[8].x < 0.03 and lm_list[4].y - lm_list[8].y < 0.03:  # Thumb and index tips are close
            if lm_list[12].y < lm_list[10].y and lm_list[16].y < lm_list[14].y and lm_list[20].y < lm_list[18].y:  # Other fingers are stretched
                return "ممتاز!"  # OK sign detected

        return "لم يتم اكتشاف إشارة"

if __name__ == '__main__':
    SignLanguageApp().run()
