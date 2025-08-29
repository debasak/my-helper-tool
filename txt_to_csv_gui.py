import os
import glob
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import date
import re
from io import StringIO
from datetime import datetime

class TINMatchProcessor:
    def __init__(self, root):
        self.root = root
        self.root.title("TIN Match Flag Consolidation Tool")
        self.root.geometry("400x300")
        self.root.resizable(False, False)
        
        # Center the window
        self.center_window()
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="TIN Match Flag Consolidation", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # Description
        desc_label = ttk.Label(main_frame, 
                              text="This tool consolidates TIN match output files\nand processes flag reports into final output files.",
                              justify=tk.CENTER)
        desc_label.grid(row=1, column=0, pady=(0, 30))
        
        # Process button
        self.process_btn = ttk.Button(main_frame, text="TIN Match Flag Consolidation", 
                                     command=self.process_files, style="Accent.TButton")
        self.process_btn.grid(row=2, column=0, pady=10, ipadx=20, ipady=10)
        
        # Progress bar (initially hidden)
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=3, column=0, pady=10, sticky=(tk.W, tk.E))
        self.progress.grid_remove()  # Hide initially
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready to process files", 
                                     foreground="green")
        self.status_label.grid(row=4, column=0, pady=10)
        
        # Configure grid weights
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)

    def center_window(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.root.winfo_screenheight() // 2) - (300 // 2)
        self.root.geometry(f"400x300+{x}+{y}")

    def process_files(self):
        try:
            # Disable button and show progress
            self.process_btn.config(state="disabled")
            self.progress.grid()
            self.progress.start()
            self.status_label.config(text="Processing...", foreground="blue")
            self.root.update()

            # Step 1: Select folder for TIN Match files
            self.status_label.config(text="Select Folder for TIN Match Consolidation")
            self.root.update()
            
            folder_path = filedialog.askdirectory(title="Select Folder for TIN Match Consolidation")
            
            if not folder_path:
                self.reset_ui()
                return

            # Check for .txt files
            txt_files = glob.glob(os.path.join(folder_path, "*.txt"))
            if not txt_files:
                messagebox.showwarning("No Files", "No .txt files found in selected folder.")
                self.reset_ui()
                return
            
            # Prepare list to store all data with dates
            all_data = []

            for file in txt_files:
                # Extract date from filename
                filename = os.path.basename(file)
                # Use regex to find the date pattern after "output_"
                date_match = re.search(r'output_(\d{8})', filename)
                
                if date_match:
                    file_date = date_match.group(1)  # YYYYMMDD format
                else:
                    # Fallback if date pattern not found
                    file_date = "Unknown"
                
                # Read file content
                with open(file, "r", encoding="utf-8") as infile:
                    lines = infile.readlines()
                    lines = [line.rstrip('\n') for line in lines]  # Strip existing newlines
                    
                    # Add date column to each line
                    for line in lines:
                        if line.strip():  # Skip empty lines
                            all_data.append(line + ";" + file_date)

            # Write consolidated file with date column (commented out - in memory only)
            # consolidated_path = os.path.join(folder_path, "consolidated.txt")
            # with open(consolidated_path, "w", encoding="utf-8") as outfile:
            #     outfile.write("\n".join(all_data))

            # Step 2: Convert to CSV (in memory only)
            
            # Create DataFrame directly from all_data string
            consolidated_data = "\n".join(all_data)
            df1 = pd.read_csv(StringIO(consolidated_data), sep=";", header=None, skiprows=0)
            df1.columns = ["tin_type", "tin", "name","account_number","error_codes", "tin_match_date"]  # Update with actual names/length
            df1 = df1.drop_duplicates()
            
            # Track statistics for readme
            original_row_count = len(all_data)  # Use all_data length instead of reading file
            duplicates_removed = original_row_count - len(df1)
            num_files_processed = len(txt_files)

            # Commented out - no intermediate CSV file creation
            # output_csv_path = os.path.join(folder_path, "consolidated_output.csv")
            # df1.to_csv(output_csv_path, index=False)

            # Step 3: Select flag report file
            self.status_label.config(text="Select the Flag Report test file")
            self.root.update()
            
            file_path_flag = filedialog.askopenfilename(
                title="Select the Flag Report test file",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            
            if not file_path_flag:
                messagebox.showwarning("No File Selected", "No flag report file selected. Process cancelled.")
                self.reset_ui()
                return

            # Get the folder path for saving final outputs
            folder_path_flag = os.path.dirname(file_path_flag)

            # Date from the flag report
            # Use regex to find the date pattern after "accounts_"
            flag_date_match = re.search(r'accounts_(\d{8})', file_path_flag)

            if flag_date_match:
                flag_date = flag_date_match.group(1)  # Extract just the date digits
            else:
                flag_date = "Unknown"

            self.status_label.config(text="Processing flag report...")
            self.root.update()

            df2 = pd.read_csv(file_path_flag, sep=";", header=0, skiprows=0)

            #Step 4: Apply business logic to qc_check
            #4.1 standard mapping:

            df2['error_codes']= None
            df2['tin_match_date'] = flag_date

            qc_check_mapping = {
                'qc_check_1': '1',
                'qc_check_2': '1',
                'qc_check_3': '2',
                'qc_check_4': '3'
            }

            df2['error_codes'] = df2['qc_check'].map(qc_check_mapping)
            

            # Create a set of Name+TIN combinations from df1 for fast lookup
            df1_name_tin_set = set(zip(df1['name'].str.strip().str.upper(), 
                                    df1['tin'].astype(str).str.strip()))

            # Find df2 records with qc_check = 'qc_check_8' (string)
            qc8_mask = df2['qc_check'] == 'qc_check_8'

            for idx in df2.index[qc8_mask]:
                name_clean = str(df2.loc[idx, 'name']).strip().upper()
                tin_clean = str(df2.loc[idx, 'tin']).strip()
                
                if (name_clean, tin_clean) in df1_name_tin_set:
                    df2.loc[idx, 'error_codes'] = '3'

            # Count matches after the loop- for debugging
            matches_count = ((df2['qc_check'] == 'qc_check_8') & (df2['error_codes'] == '3')).sum()

            #5. Update to match the column names similar to the consolidated & drop the other columns

            # Create a copy of df2
            df3 = df2.copy()

            # Remove rows where 'Error Codes' is NaN
            df3 = df3.dropna(subset=['error_codes'])
            df3 = df3[['tin_type', 'tin', 'name', 'account_number', 'error_codes','tin_match_date']]

            # Update tin_type from 'SSN' to '2'
            df3.loc[df2['tin_type'] == 'SSN', 'tin_type'] = '2'

            # Commented out - no intermediate flag results file creation
            # output_csv_path = os.path.join(folder_path_flag, "Flag_Result_output.csv")
            # df3.to_csv(output_csv_path, index=False)
            
            #6. Combine the Consolidated file & Flag_Results
            self.status_label.config(text="Combining data and creating final files...")
            self.root.update()
            
            # Combine df1 and df3, keeping df1's headers
            df_combined = pd.concat([df1, df3], ignore_index=True)

            #drop columns that are not required
            df_combined = df_combined.drop(columns=['tin_type', 'tin', 'name'])

            # Convert tin_match_date from YYYYMMDD to MM/DD/YYYY format
            df_combined['tin_match_date'] = pd.to_datetime(df_combined['tin_match_date'], format='%Y%m%d', errors='coerce').dt.strftime('%m/%d/%Y')

            #save to CSV and TXT with date stamps
            today_date = date.today().strftime('%Y%m%d')  # Format: 20250814
            output_csv_path = os.path.join(folder_path_flag, f"Final_consolidated_output_{today_date}.csv")
            output_txt_path = os.path.join(folder_path_flag, f"Final_consolidated_output_{today_date}.txt")
            
            df_combined.to_csv(output_csv_path, index=False)
            df_combined.to_csv(output_txt_path, sep=";", index=False)

            # Create README.txt file with statistics
            readme_content = f"""Consolidated TIN Match Output:
Total consolidated {int(num_files_processed):,} tin_match_output files.
Total consolidated population = {int(len(df1)):,}
No. of duplicates removed: {int(duplicates_removed):,}

Flag Report:
Total population added to final results: {int(len(df3)):,}
Population with qc_check_1: {int((df2['qc_check'] == 'qc_check_1').sum()):,}
Population with qc_check_2: {int((df2['qc_check'] == 'qc_check_2').sum()):,}
Population with qc_check_3: {int((df2['qc_check'] == 'qc_check_3').sum()):,}
Population with qc_check_4: {int((df2['qc_check'] == 'qc_check_4').sum()):,}
Population with qc_check_8 with Name, TIN match in the consolidated file: {int(matches_count):,}

Final population: {int(len(df_combined)):,}

Processing completed on: {datetime.now().strftime('%m/%d/%Y at %I:%M %p')}
"""

            readme_path = os.path.join(folder_path_flag, "README.txt")
            with open(readme_path, "w", encoding="utf-8") as readme_file:
                readme_file.write(readme_content)

            # Success - reset UI
            self.status_label.config(text="Processing completed successfully!", foreground="green")
            self.reset_ui()

        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.reset_ui()

    def reset_ui(self):
        self.process_btn.config(state="normal")
        self.progress.stop()
        self.progress.grid_remove()
        if "successfully" not in self.status_label.cget("text"):
            self.status_label.config(text="Ready to process files", foreground="green")

def main():
    root = tk.Tk()
    app = TINMatchProcessor(root)
    root.mainloop()

if __name__ == "__main__":
    main()
