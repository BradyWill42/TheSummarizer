import os
import base64
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import ImageGrab, Image
import openai
import ctypes
import platform

# Set your OpenAI API key - v1
openai.api_key = ""

# Ensure DPI awareness for accurate screen capture on Windows
def make_dpi_aware():
    """
    Sets DPI awareness for Windows systems to improve screen region selection accuracy.
    Does nothing on non-Windows platforms.
    """
    try:
        if platform.system() == "Windows":
            ctypes.windll.user32.SetProcessDPIAware()
    except AttributeError:
        print("Failed to set DPI awareness: 'ctypes.windll' not available on this platform.")
    except Exception as e:
        print(f"Unexpected error while setting DPI awareness: {e}")


# Function to select a screen region
def select_region():
    region = {"x1": None, "y1": None, "x2": None, "y2": None}

    def on_click(event):
        region["x1"], region["y1"] = event.x_root, event.y_root

    def on_drag(event):
        region["x2"], region["y2"] = event.x_root, event.y_root
        canvas.delete("rect")
        canvas.create_rectangle(region["x1"], region["y1"], region["x2"], region["y2"], outline="red", width=2)

    def on_release(event):
        region["x2"], region["y2"] = event.x_root, event.y_root
        root.quit()

    root = tk.Tk()
    root.attributes("-alpha", 0.3)
    root.attributes("-fullscreen", True)
    root.configure(bg="white")
    root.overrideredirect(True)
    root.lift()
    root.attributes("-topmost", True)

    canvas = tk.Canvas(root, bg="white", highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    canvas.bind("<ButtonPress-1>", on_click)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)

    root.mainloop()
    root.destroy()

    if None in (region["x1"], region["y1"], region["x2"], region["y2"]):
        return None
    left = min(region["x1"], region["x2"])
    top = min(region["y1"], region["y2"])
    width = abs(region["x2"] - region["x1"])
    height = abs(region["y2"] - region["y1"])
    return (left, top, width, height)

def take_screenshot(region, file_name):
    """
    Takes a screenshot of the specified region and saves it with the given file name.
    Args:
        region (tuple): A tuple (left, top, width, height) specifying the region.
        file_name (str): The name of the file to save the screenshot.
    Returns:
        str: Path to the saved screenshot.
    """
    left, top, width, height = region
    right = left + width
    bottom = top + height

    # Capture and save the screenshot
    screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
    screenshot_path = os.path.join(os.getcwd(), file_name)
    screenshot.save(screenshot_path)
    print(f"Screenshot saved to: {screenshot_path}")
    return screenshot_path

# Function to encode image in base64
def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def analyze_images_with_gpt(image_paths, prompt):
    """
    Sends the provided images and prompt to GPT-4 Vision for analysis and summary generation.
    Args:
        image_paths (list): List of file paths for images to be analyzed.
        prompt (str): The dynamically constructed prompt for GPT-4 Vision.
    Returns:
        str: The generated summary.
    """
    print("Analyzing images with GPT-4 Vision...")

    # Convert each image to a base64-encoded string
    base64_images = [encode_image_to_base64(path) for path in image_paths]

    # Prepare content for the API request
    content = [{"type": "text", "text": prompt}]
    for img in base64_images:
        content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img}"}})

    try:
        # Send the request to GPT-4 Vision
        response = openai.chat.completions.create(
            model="gpt-4o",  # Use the appropriate model with vision capabilities
            messages=[
                {"role": "system", "content": "You are a professional summarizing financial data."},
                {"role": "user", "content": content}
            ],
            max_tokens=1000,  # Adjust as needed
        )

        # Extract and return the summary
        summary = response.choices[0].message.content
        print("Generated Summary:\n", summary)
        return summary

    except openai.OpenAIError as e:
        print(f"Error while calling OpenAI API: {e}")
        raise

class ScreenshotSummarizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Tax Document Summarizer")
        self.root.geometry("600x400")
        self.image_paths = []

        # Number of paragraphs input
        tk.Label(root, text="Number of Paragraphs:").pack(pady=5)
        self.num_paragraphs = ttk.Spinbox(root, from_=1, to=10, width=5)
        self.num_paragraphs.pack(pady=5)

        # Tone selection
        tk.Label(root, text="Tone:").pack(pady=5)
        self.tone_var = tk.StringVar(value="Formal")
        ttk.Combobox(root, textvariable=self.tone_var, values=["Formal", "Informal", "JJ"]).pack(pady=5)

        # Buttons
        ttk.Button(
            root,
            text="Generate Tax Summary",
            command=self.generate_tax_summary
        ).pack(pady=10)

        ttk.Button(
            root,
            text="Analyze Tax Document",
            command=self.analyze_tax_document_screenshot
        ).pack(pady=10)

        ttk.Button(
            root, 
            text="Reset", 
            command=self.reset_app
        ).pack(pady=10)


        # Output Text Box
        tk.Label(root, text="Generated Summary:").pack(pady=5, anchor="w")
        output_frame = tk.Frame(root)
        output_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.output_text = tk.Text(output_frame, wrap="word", font=("Arial", 12))
        self.output_text.pack(side="left", fill="both", expand=True)
        scrollbar = tk.Scrollbar(output_frame, command=self.output_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.output_text.config(yscrollcommand=scrollbar.set)

    def generate_tax_summary(self):
        """
        Combines taking a screenshot and generating a summary in a single button.
        """
        # Step 1: Select region and take a screenshot
        region = select_region()
        if not region:
            messagebox.showwarning("No Selection", "No region was selected.")
            return

        try:
            # Save the screenshot
            file_name = f"tax_summary_{len(self.image_paths) + 1}.png"
            path = take_screenshot(region, file_name)
            self.image_paths.append(path)

            # Step 2: Prepare the prompt for summarizing the screenshot
            tone = self.tone_var.get()
            tone_instructions = self.get_tone_instructions(tone)

            prompt = f"""
            You are a great tax expert analyzing a screenshot of a financial or tax document.  
            Following the tone indicated in the provided paragraphs: {tone_instructions}
            Summarize the key information from the document in {self.num_paragraphs.get()} paragraph(s).
            """

            # Step 3: Generate and display the summary
            self.append_summary(prompt, tone, num_paragraphs=int(self.num_paragraphs.get()), file_path=path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate tax summary: {e}")

    def analyze_tax_document_screenshot(self):
        """
        Select a screen region, analyze it as a tax document, determine the form type,
        and summarize it based on the tone selected.
        """
        region = select_region()
        if not region:
            messagebox.showwarning("No Selection", "No region was selected.")
            return

        try:
            # Capture the screenshot of the tax document
            file_name = f"tax_form_{len(self.image_paths) + 1}.png"
            path = take_screenshot(region, file_name)
            self.image_paths.append(path)

            # Prepare the prompt for tax document analysis
            tone = self.tone_var.get()
            tone_instructions = self.get_tone_instructions(tone)

            prompt = f"""
            You are a tax professional analyzing a screenshot of a tax document.
            Following the tone indicated in the provided paragraphs: {tone_instructions}
            Identify the tax form type (e.g., W-2, 1099, etc.) and summarize the key information in {self.num_paragraphs.get()} paragraph(s).
            """

            self.append_summary(prompt, tone, num_paragraphs=int(self.num_paragraphs.get()), file_path=path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to analyze the tax document screenshot: {e}")

    def get_tone_instructions(self, tone):
        """
        Return tone-specific instructions for the selected tone.
        """
        if tone == "JJ":
            return self.load_jj_tone_instructions()
        elif tone == "Formal":
            return "Use a formal tone suitable for professional communication."
        elif tone == "Informal":
            return "Use an informal and conversational tone."
        return "Use a neutral tone."

    def append_summary(self, prompt, tone, num_paragraphs, file_path=None):
        """
        Generates a summary based on the provided prompt and appends it to the output text box.
        Adds a line break after each summary for better separation.
        Args:
            prompt (str): The AI prompt to use for generating the summary.
            tone (str): The selected tone for the summary.
            num_paragraphs (int): The number of paragraphs in the summary.
            file_path (str, optional): The path to the document being analyzed.
        """
        try:
            if file_path:
                prompt += f"\n\nDocument Path: {file_path}"

            # Call GPT function to analyze and generate summary
            summary = analyze_images_with_gpt(self.image_paths, prompt)

            # Add the summary and a line break to the text box
            line_break = "\n-------------------------------------------------------------\n"
            self.output_text.insert(tk.END, "\n\n" + summary + line_break)
            self.output_text.see(tk.END)

            # Save the summary and line break to the file
            summary_file = os.path.join(os.getcwd(), "gpt4_summary.txt")
            with open(summary_file, "a") as f:
                f.write("\n\n" + summary + line_break)

            messagebox.showinfo("Summary Generated", "The summary has been successfully added!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate summary: {e}")


    def load_jj_tone_instructions(self):
        """
        Load tone-specific instructions for 'JJ' tone. These instructions can be
        customized to mimic a specific writing style.
        """
        try:
            with open("gpt_rules.txt", "r", encoding="utf-8") as file:
                instructions = file.read()
            return instructions
        except FileNotFoundError:
            return "Use a conversational and personalized tone, reflecting a warm and engaging style. Highlight key changes with enthusiasm and reframe negative outcomes positively."
        except Exception as e:
            print(f"Error loading JJ tone instructions: {e}")
            return "Use a conversational and personalized tone with enthusiasm."
        
    def reset_app(self):
        self.image_paths.clear()
        self.output_text.delete("1.0", tk.END)
        messagebox.showinfo("Reset", "The application has been reset.")




# Main Function
def main():
    make_dpi_aware()
    root = tk.Tk()
    app = ScreenshotSummarizerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
