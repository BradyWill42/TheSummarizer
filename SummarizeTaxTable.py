import os
import base64
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import ImageGrab, Image
import openai
import ctypes
import platform
import google.generativeai as gemini
import re



geminiApiKey = os.environ["API_KEY_GEMINI"]

if geminiApiKey:
    print(geminiApiKey)
else:
    print("API_KEY_GEMINI not set")


myTestApiKey = os.environ["API_KEY"]

if myTestApiKey:
    print(myTestApiKey)
else:
    print("API_KEY not set")

# Set the Gemini API key
gemini.configure(api_key=geminiApiKey)
model = gemini.GenerativeModel("gemini-1.5-flash")


# Set your OpenAI API key - v1
openai.api_key = myTestApiKey

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

# Helper function to format numbers
def format_number(num):
    if 1_000 <= num < 1_000_000:
        return f"{round(num / 1_000)}k"
    elif num >= 1_000_000:
        return f"{round(num / 1_000_000, 1)}MM"
    else:
        return str(num)

# Function to format only numbers with a dollar sign in front
def format_text_with_dollars(text):
    # Use a regex to find and replace dollar-signed numbers
    def replace_dollar_number(match):
        # Extract the numeric part (group 1) and remove commas
        num = float(match.group(1).replace(',', ''))  # Remove commas and convert to float
        return format_number(num)  # Format the number

    # Regex pattern: \$([0-9.,]+) matches a dollar sign followed by a number
    return re.sub(r'\$([0-9.,]+)', lambda m: replace_dollar_number(m), text)


    
def analyze_images_with_gemini(image_paths, prompt):

    uploadedFiles = [gemini.upload_file(path=(img)) for img in image_paths]

    response = model.generate_content([*uploadedFiles, prompt])

    summary = format_text_with_dollars(response.text)
    print("Generated Summary:\n", response.text)
    return summary

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
        summary = format_text_with_dollars(response.choices[0].message.content) 
        print("Generated Summary:\n", summary)
        return summary

    except openai.OpenAIError as e:
        print(f"Error while calling OpenAI API: {e}")
        raise

class ScreenshotSummarizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Tax Document Summarizer")

         # Get the screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        self.root.maxsize(screen_width, screen_height)
        self.root.geometry(f"{(int) (screen_width / 2)}x{(int) (screen_height)}+0+0")


        self.image_paths = []

        # Number of paragraphs input
        tk.Label(root, text="Number of Paragraphs:").pack(pady=5)
        self.num_paragraphs = ttk.Spinbox(root, from_=1, to=10, width=5)
        self.num_paragraphs.pack(pady=5)

        # Tone selection
        tk.Label(root, text="Tone:").pack(pady=5)
        self.tone_var = tk.StringVar(value="JJ")
        ttk.Combobox(root, textvariable=self.tone_var, values=["Formal", "Informal", "JJ"]).pack(pady=5)

        # AI Selection
        tk.Label(root, text="AI Model:").pack(pady=5)
        self.ai_models = tk.StringVar(value="gpt-4o")
        ttk.Combobox(root, textvariable=self.ai_models, values=["gpt-4o", "gemini"]).pack(pady=5)

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

        # --- Dynamic Output Container ---
        # This container will hold the output text widget and an overlaid feedback bar.
        self.dynamic_container = tk.Frame(root)
        self.dynamic_container.pack(fill="both", expand=True, padx=10, pady=5)

        # Output Text Box inside the container
        self.output_text = tk.Text(self.dynamic_container, wrap="word", font=("Arial", 12))
        self.output_text.pack(side="left", fill="both", expand=True)

        # Vertical Scrollbar for the text widget
        scrollbar = tk.Scrollbar(self.dynamic_container, command=self.output_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.output_text.config(yscrollcommand=scrollbar.set)

        # --- Feedback Overlay ---
        self.feedback_frame = tk.Frame(self.dynamic_container, bg="lightgray")
        self.feedback_frame.place(relx=0, rely=1, anchor="sw", relwidth=1, height=50)
        
        # Configure button style
        style = ttk.Style()
        style.configure("Centered.TButton", anchor="center")
        
        # Feedback label
        tk.Label(self.feedback_frame, text="Feedback:", bg="lightgray")\
            .pack(side="left", padx=(5,2), pady=5)
        
        # Feedback entry widget
        self.feedback_var = tk.StringVar()
        self.feedback_entry = tk.Entry(self.feedback_frame, textvariable=self.feedback_var)
        self.feedback_entry.pack(side="left", fill="x", expand=True, padx=(2,2), pady=5)
        
        # Send button
        send_button = ttk.Button(self.feedback_frame, text="Send", 
                                 command=self.send_feedback, style="Centered.TButton")
        send_button.pack(side="right", padx=(2,5), pady=5)
        
        # Set feedback file path
        self.feedback_file = os.path.join(os.getcwd(), "feedback.txt")
        
        # Variables to store the last base prompt and parameters for reprompting with feedback.
        self.last_base_prompt = None
        self.last_tone = None
        self.last_num_paragraphs = None
        self.last_file_path = None

    def send_feedback(self):
        # Get and clean up the feedback text
        feedback_text = self.feedback_var.get().strip()
        
        # Only proceed if there's text to save
        if feedback_text:
            try:
                # Open the file in append mode (it will be created if it doesn't exist)
                with open(self.feedback_file, "a", encoding="utf-8") as file:
                    file.write(feedback_text + "\n")
                
                # Clear the entry field after saving
                self.feedback_var.set("")
                print("Feedback saved successfully!")
            except Exception as e:
                print("An error occurred while saving feedback:", e)
        
        # Create a new prompt by appending the feedback to the stored base prompt.
        new_prompt = self.last_base_prompt + "\n\nFeedback: " + feedback_text
        # Call append_summary with the new prompt and the previously stored parameters.
        self.append_summary(new_prompt, self.last_tone, self.last_num_paragraphs, file_path=self.last_file_path)

    
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
You are a tax professional analyzing a screenshot of a tax year over year comparison to prepare a summary for a client always comparing 2023 to 2024.
Following the tone indicated in the provided rules and paragraphs: {tone_instructions}
Summarize the key information from the document in {self.num_paragraphs.get()} paragraph(s).
            """.strip()

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
You are a tax professional analyzing a screenshot of a tax document to prepare a summary for a client.
Following the tone indicated in the provided rules and paragraphs: {tone_instructions}
Identify the tax form type (e.g., W-2, 1099, etc.) and summarize the key information in {self.num_paragraphs.get()} paragraph(s).
            """.strip()

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
        Also stores the base prompt and parameters so that feedback can be added later.
        Args:
            prompt (str): The AI prompt to use for generating the summary.
            tone (str): The selected tone for the summary.
            num_paragraphs (int): The number of paragraphs in the summary.
            file_path (str, optional): The path to the document being analyzed.
        """
        try:
            # Save the base prompt before any further modification
            base_prompt = prompt
            # Only add the document path if it hasn't already been added.
            if file_path and "Document Path:" not in prompt:
                prompt += f"\n\nDocument Path: {file_path}"

            # Store the base prompt and related parameters for reprompting with feedback
            self.last_base_prompt = base_prompt
            self.last_tone = tone
            self.last_num_paragraphs = num_paragraphs
            self.last_file_path = file_path

            # Call the AI function to generate the summary.
            # (The following code assumes that either analyze_images_with_gemini or analyze_images_with_gpt returns the summary.)
            summary = "Summary Failed"

            if self.ai_models.get() == "gemini":
                summary = analyze_images_with_gemini(self.image_paths, prompt)
            elif self.ai_models.get() == "gpt-4o":
                summary = analyze_images_with_gpt(self.image_paths, prompt)
            else:
                messagebox.showinfo("Invalid AI Model", "Summary Failed")

            # Add the summary and a line break to the text box.
            line_break = "\n-------------------------------------------------------------\n"
            self.output_text.insert(tk.END, "\n\n" + summary + line_break)
            self.output_text.see(tk.END)

            # Save the summary and line break to the file.
            summary_file = os.path.join(os.getcwd(), "gpt4_summary.txt")
            with open(summary_file, "a", encoding="utf-8") as f:
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
            return ("Use a conversational and personalized tone, reflecting a warm and engaging style. "
                    "Highlight key changes with enthusiasm and reframe negative outcomes positively.")
        except Exception as e:
            print(f"Error loading JJ tone instructions: {e}")
            return "Use a conversational and personalized tone with enthusiasm."

    def reset_app(self):
        """Reset the application state including the summary, feedback, and related files."""
        self.image_paths.clear()
        self.output_text.delete("1.0", tk.END)
        # Reset the feedback bar and clear the feedback file.
        self.feedback_var.set("")
        with open(self.feedback_file, "w", encoding="utf-8") as f:
            f.write("")
        # Also clear the stored prompt parameters.
        self.last_base_prompt = None
        self.last_tone = None
        self.last_num_paragraphs = None
        self.last_file_path = None
        messagebox.showinfo("Reset", "The application has been reset.")

# Main Function
def main():
    make_dpi_aware()
    root = tk.Tk()

    app = ScreenshotSummarizerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
