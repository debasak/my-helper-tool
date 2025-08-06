import os
import glob
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox

def process_files():
    folder_path = filedialog.askdirectory(title="Select Folder with .txt Files")

    if not folder_path:
        return

    try:
        # Step 1: Merge all .txt files
        txt_files = glob.glob(os.path.join(folder_path, "*.txt"))
        if not txt_files:
            messagebox.showwarning("No Files", "No .txt files found in selected folder.")
            return

        consolidated_path = os.path.join(folder_path, "consolidated.txt")
        with open(consolidated_path, "w", encoding="utf-8") as outfile:
            for file in txt_files:
                with open(file, "r", encoding="utf-8") as infile:
                    outfile.write(infile.read())

        # Step 2: Convert to CSV
        df = pd.read_csv(consolidated_path, sep=";")
        output_csv_path = os.path.join(folder_path, "output.csv")
        df.to_csv(output_csv_path, index=False)

        messagebox.showinfo("Success", f"CSV file saved as:\n{output_csv_path}")
    except Exception as e:
        messagebox.showerror("Error", str(e))

# GUI setup
root = tk.Tk()
root.title("TXT to CSV Converter")
root.geometry("400x200")

label = tk.Label(root, text="Click the button below to process .txt files", pady=20)
label.pack()

btn = tk.Button(root, text="Select Folder & Convert", command=process_files, height=2, width=25)
btn.pack()

root.mainloop()
