"""
Simple UI for Video Clipping System
A tkinter-based interface for controlling the automation and configuring default metadata
"""
import os
import sys
import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import logging
import yaml
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

# Import main system
from main import VideoClippingSystem


class VideoClippingUI:
    """Simple UI for controlling the video clipping system"""
    
    def __init__(self, root):
        """Initialize the UI"""
        self.root = root
        self.root.title("Autonomous Video Clipping System")
        self.root.geometry("800x600")
        
        # System instance (will be created when processing starts)
        self.system = None
        self.processing_thread = None
        self.is_processing = False
        
        # Config file path
        self.config_path = Path(__file__).parent.parent / 'config' / 'settings.yaml'
        
        # Setup UI components
        self.setup_ui()
        
        # Load current config values
        self.load_config_values()
        
        # Setup logging to redirect to text area
        self.setup_logging()
        
        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_ui(self):
        """Setup UI components"""
        # Main frame
        main_frame = tk.Frame(self.root, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(
            main_frame, 
            text="Autonomous Video Clipping System", 
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=10)
        
        # Configuration Section
        config_frame = tk.LabelFrame(main_frame, text="Configuration", padx=10, pady=10)
        config_frame.pack(fill=tk.X, pady=5)
        
        # Default Description
        desc_label = tk.Label(config_frame, text="Default Description:")
        desc_label.grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.description_text = scrolledtext.ScrolledText(
            config_frame, 
            height=4, 
            width=60,
            wrap=tk.WORD
        )
        self.description_text.grid(row=1, column=0, columnspan=2, pady=5)
        
        # Default Hashtags
        hashtags_label = tk.Label(config_frame, text="Default Hashtags (comma-separated):")
        hashtags_label.grid(row=2, column=0, sticky=tk.W, pady=5)
        
        self.hashtags_entry = tk.Entry(config_frame, width=70)
        self.hashtags_entry.grid(row=3, column=0, columnspan=2, pady=5)
        
        # Save Button
        self.save_button = tk.Button(
            config_frame, 
            text="Save Configuration", 
            command=self.save_config,
            bg="#4CAF50",
            fg="white",
            padx=20,
            pady=5
        )
        self.save_button.grid(row=4, column=0, columnspan=2, pady=10)
        
        # Control Section
        control_frame = tk.LabelFrame(main_frame, text="Control", padx=10, pady=10)
        control_frame.pack(fill=tk.X, pady=5)
        
        # Start Processing Button
        self.start_button = tk.Button(
            control_frame,
            text="Start Processing",
            command=self.start_processing,
            bg="#2196F3",
            fg="white",
            padx=30,
            pady=10,
            font=("Arial", 12, "bold")
        )
        self.start_button.pack(pady=10)
        
        # Status Label
        self.status_label = tk.Label(
            control_frame,
            text="Status: Ready",
            font=("Arial", 10)
        )
        self.status_label.pack()
        
        # Logs Section
        logs_frame = tk.LabelFrame(main_frame, text="Logs", padx=10, pady=10)
        logs_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Log Text Area
        self.log_text = scrolledtext.ScrolledText(
            logs_frame,
            height=15,
            width=80,
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Clear Logs Button
        clear_button = tk.Button(
            logs_frame,
            text="Clear Logs",
            command=self.clear_logs
        )
        clear_button.pack(pady=5)
    
    def load_config_values(self):
        """Load current configuration values from settings.yaml"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            metadata = config.get('metadata', {})
            
            # Load default description
            default_desc = metadata.get('default_description', '')
            if default_desc:
                self.description_text.delete('1.0', tk.END)
                self.description_text.insert('1.0', default_desc)
            
            # Load default hashtags override
            default_hashtags = metadata.get('default_hashtags_override', '')
            if default_hashtags:
                self.hashtags_entry.delete(0, tk.END)
                self.hashtags_entry.insert(0, default_hashtags)
            
            self.log_message("Configuration loaded successfully")
        
        except Exception as e:
            self.log_message(f"Error loading configuration: {e}")
    
    def save_config(self):
        """Save configuration to settings.yaml"""
        try:
            # Read current config
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Update metadata section
            if 'metadata' not in config:
                config['metadata'] = {}
            
            # Get values from UI
            default_desc = self.description_text.get('1.0', tk.END).strip()
            default_hashtags = self.hashtags_entry.get().strip()
            
            # Update config
            config['metadata']['default_description'] = default_desc
            config['metadata']['default_hashtags_override'] = default_hashtags
            
            # Write back to file
            with open(self.config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            
            self.log_message("Configuration saved successfully!")
            messagebox.showinfo("Success", "Configuration saved successfully!")
        
        except Exception as e:
            error_msg = f"Error saving configuration: {e}"
            self.log_message(error_msg)
            messagebox.showerror("Error", error_msg)
    
    def start_processing(self):
        """Start the video processing in a separate thread"""
        if self.is_processing:
            messagebox.showwarning("Warning", "Processing is already running!")
            return
        
        # Disable start button
        self.start_button.config(state=tk.DISABLED)
        self.status_label.config(text="Status: Processing...")
        
        # Start processing in a separate thread
        self.processing_thread = threading.Thread(target=self.run_processing)
        self.processing_thread.start()
        
        self.is_processing = True
    
    def run_processing(self):
        """Run the video processing (executed in separate thread)"""
        try:
            self.log_message("=" * 60)
            self.log_message("Starting Video Clipping System...")
            self.log_message("=" * 60)
            
            # Initialize system
            self.system = VideoClippingSystem()
            self.log_message("System initialized successfully")
            
            # Start scheduler
            self.system.start_scheduler()
            self.log_message("Upload scheduler started")
            
            # Process all videos with auto-upload enabled
            self.log_message("\nProcessing videos...")
            results = self.system.process_all_videos(
                platforms=['instagram', 'youtube', 'tiktok'],
                auto_upload=True
            )
            
            # Log results
            total_clips = sum(len(r['clips']) for r in results)
            total_uploads = sum(len(r['scheduled_uploads']) for r in results)
            
            self.log_message(f"\nProcessing Complete!")
            self.log_message(f"Videos processed: {len(results)}")
            self.log_message(f"Clips extracted: {total_clips}")
            self.log_message(f"Uploads scheduled: {total_uploads}")
            
            # Update status
            self.root.after(0, lambda: self.status_label.config(
                text=f"Status: Complete ({total_clips} clips, {total_uploads} uploads)"
            ))
        
        except Exception as e:
            error_msg = f"Error during processing: {e}"
            self.log_message(error_msg)
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
            self.root.after(0, lambda: self.status_label.config(text="Status: Error"))
        
        finally:
            # Stop scheduler if it was started
            if self.system:
                try:
                    self.system.stop_scheduler()
                    self.log_message("Upload scheduler stopped")
                except Exception as e:
                    self.log_message(f"Error stopping scheduler: {e}")
            
            # Re-enable start button
            self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
            self.is_processing = False
    
    def setup_logging(self):
        """Setup logging to redirect to UI text area"""
        # Create custom handler
        class TextHandler(logging.Handler):
            def __init__(self, text_widget):
                logging.Handler.__init__(self)
                self.text_widget = text_widget
            
            def emit(self, record):
                msg = self.format(record)
                def append():
                    self.text_widget.config(state=tk.NORMAL)
                    self.text_widget.insert(tk.END, msg + '\n')
                    self.text_widget.see(tk.END)
                    self.text_widget.config(state=tk.DISABLED)
                # Schedule on main thread
                self.text_widget.after(0, append)
        
        # Add handler to root logger
        text_handler = TextHandler(self.log_text)
        text_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        logging.getLogger().addHandler(text_handler)
        logging.getLogger().setLevel(logging.INFO)
    
    def log_message(self, message):
        """Log a message to the text area"""
        def append():
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, message + '\n')
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        
        # Schedule on main thread
        self.root.after(0, append)
    
    def clear_logs(self):
        """Clear the log text area"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete('1.0', tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def on_closing(self):
        """Handle window close event"""
        if self.is_processing:
            if messagebox.askokcancel("Quit", "Processing is still running. Do you want to stop and quit?"):
                # Stop the system if it's running
                if self.system:
                    try:
                        self.system.stop_scheduler()
                        self.log_message("System stopped by user")
                    except Exception as e:
                        self.log_message(f"Error stopping system: {e}")
                
                self.is_processing = False
                self.root.destroy()
        else:
            self.root.destroy()


def main():
    """Main entry point for the UI"""
    root = tk.Tk()
    app = VideoClippingUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
