from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.scrollview import ScrollView
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from PyPDF2 import PdfReader, PdfWriter
import os
import io

class PDFTrimmer(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.files = []
        self.cleaned_files = []

        self.label = Label(text="Select PDFs to trim & merge")
        self.add_widget(self.label)

        self.file_chooser = FileChooserListView(filters=["*.pdf"], multiselect=True, path="/sdcard/Download")
        self.add_widget(self.file_chooser)

        self.preview_label = Label(text="Selected Files:")
        self.add_widget(self.preview_label)

        self.preview_box = ScrollView(size_hint=(1, 0.3))
        self.preview_text = Label(text="", size_hint_y=None)
        self.preview_text.bind(texture_size=self.update_height)
        self.preview_box.add_widget(self.preview_text)
        self.add_widget(self.preview_box)

        self.progress = ProgressBar(max=100, value=0, size_hint=(1, 0.1))
        self.add_widget(self.progress)

        self.select_btn = Button(text="Process PDFs", size_hint=(1, 0.2))
        self.select_btn.bind(on_press=self.process_pdfs)
        self.add_widget(self.select_btn)

    def update_height(self, instance, value):
        instance.height = value[1]

    def process_pdfs(self, instance):
        self.files = self.file_chooser.selection
        self.cleaned_files = []

        if not self.files:
            self.label.text = "❌ No files selected."
            return

        self.preview_text.text = "\n".join(os.path.basename(f) for f in self.files)
        self.progress.value = 0
        self.label.text = "Processing..."
        Clock.schedule_once(self._process_pdfs, 0.5)

    def _process_pdfs(self, dt):
        merged_writer = PdfWriter()
        step = 100 / len(self.files)

        for idx, path in enumerate(self.files):
            filename = os.path.basename(path)
            try:
                reader = PdfReader(path)
                writer = PdfWriter()

                if "E-WAY" in filename.upper():
                    writer.add_page(reader.pages[0])
                else:
                    annexure_found = False
                    for i, page in enumerate(reader.pages):
                        text = page.extract_text()
                        if text and "Address Details" in text:
                            writer.add_page(reader.pages[i])  # Keep only the first Annexure page
                            annexure_found = True
                            break
                        writer.add_page(page)
                    if not annexure_found:
                        writer.append_pages_from_reader(reader)

                for page in writer.pages:
                    merged_writer.add_page(page)

                self.progress.value = step * (idx + 1)

            except Exception as e:
                self.label.text = f"❌ Error: {filename}: {str(e)}"
                return

        output_path = "/sdcard/Download/merged_result.pdf"
        try:
            with open(output_path, "wb") as f:
                merged_writer.write(f)
            self.label.text = f"✅ Saved merged PDF to: {output_path}"
        except Exception as e:
            self.label.text = f"❌ Failed to save PDF: {str(e)}"

class TrimmerApp(App):
    def build(self):
        self.icon = "icon.png"  # Optional custom icon if available
        return PDFTrimmer()

if __name__ == "__main__":
    TrimmerApp().run()
