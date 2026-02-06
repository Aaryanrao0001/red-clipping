"""
Modern UI for Video Clipping System
A customtkinter-based interface with modern, dark-mode friendly design
"""
import os
import sys
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import logging
import yaml
from pathlib import Path
import shutil

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

# Import main system
from main import VideoClippingSystem

# Set appearance mode and default color theme
ctk.set_appearance_mode("dark")  # Modes: "System" (default), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (default), "green", "dark-blue"


class ModernVideoClippingUI:
    """Modern UI for controlling the video clipping system"""
    
    def __init__(self, root):
        """Initialize the UI"""
        self.root = root
        self.root.title("Autonomous Video Clipping System")
        self.root.geometry("1200x800")
        
        # System instance (will be created when processing starts)
        self.system = None
        self.processing_thread = None
        self.is_processing = False
        
        # Config file path
        self.config_path = Path(__file__).parent.parent / 'config' / 'settings.yaml'
        self.input_videos_path = Path(__file__).parent.parent / 'input' / 'videos'
        
        # Ensure input directory exists
        self.input_videos_path.mkdir(parents=True, exist_ok=True)
        
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
        # Configure grid weight
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        
        # Create sidebar for navigation
        self.sidebar = ctk.CTkFrame(self.root, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar.grid_rowconfigure(7, weight=1)
        
        # Logo/Title
        self.logo_label = ctk.CTkLabel(
            self.sidebar, 
            text="🎬 Video Clipper",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Version label
        self.version_label = ctk.CTkLabel(
            self.sidebar,
            text="v2.0 - Modern UI",
            font=ctk.CTkFont(size=10)
        )
        self.version_label.grid(row=1, column=0, padx=20, pady=(0, 20))
        
        # File Selection Button
        self.select_files_btn = ctk.CTkButton(
            self.sidebar,
            text="📁 Select Videos",
            command=self.select_video_files,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        self.select_files_btn.grid(row=2, column=0, padx=20, pady=10)
        
        # Start Button
        self.start_btn = ctk.CTkButton(
            self.sidebar,
            text="▶ Start Processing",
            command=self.start_processing,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="green",
            hover_color="darkgreen"
        )
        self.start_btn.grid(row=3, column=0, padx=20, pady=10)
        
        # Stop Button
        self.stop_btn = ctk.CTkButton(
            self.sidebar,
            text="⏹ Stop Processing",
            command=self.stop_processing,
            height=40,
            font=ctk.CTkFont(size=14),
            fg_color="red",
            hover_color="darkred",
            state="disabled"
        )
        self.stop_btn.grid(row=4, column=0, padx=20, pady=10)
        
        # Save Config Button
        self.save_config_btn = ctk.CTkButton(
            self.sidebar,
            text="💾 Save Config",
            command=self.save_config,
            height=35,
            font=ctk.CTkFont(size=13)
        )
        self.save_config_btn.grid(row=5, column=0, padx=20, pady=10)
        
        # Clear Logs Button
        self.clear_logs_btn = ctk.CTkButton(
            self.sidebar,
            text="🗑 Clear Logs",
            command=self.clear_logs,
            height=35,
            font=ctk.CTkFont(size=13)
        )
        self.clear_logs_btn.grid(row=6, column=0, padx=20, pady=10)
        
        # Appearance mode switch
        self.appearance_label = ctk.CTkLabel(self.sidebar, text="Appearance Mode:", anchor="w")
        self.appearance_label.grid(row=8, column=0, padx=20, pady=(10, 0))
        
        self.appearance_mode = ctk.CTkOptionMenu(
            self.sidebar,
            values=["Dark", "Light", "System"],
            command=self.change_appearance_mode
        )
        self.appearance_mode.grid(row=9, column=0, padx=20, pady=(0, 20))
        self.appearance_mode.set("Dark")
        
        # Main content area
        self.main_frame = ctk.CTkFrame(self.root, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="Configuration Dashboard",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.grid(row=0, column=0, pady=(0, 20), sticky="w", padx=20)
        
        # Create tabview for different sections
        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        
        # Add tabs
        self.tabview.add("Configuration")
        self.tabview.add("Logs")
        
        # Setup Configuration tab
        self.setup_configuration_tab()
        
        # Setup Logs tab
        self.setup_logs_tab()
        
        # Status bar at bottom
        self.status_frame = ctk.CTkFrame(self.root, height=40, corner_radius=0)
        self.status_frame.grid(row=1, column=1, sticky="ew", padx=0, pady=0)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="● Status: Ready",
            font=ctk.CTkFont(size=12),
            anchor="w"
        )
        self.status_label.pack(side="left", padx=20, pady=10)
    
    def setup_configuration_tab(self):
        """Setup the configuration tab"""
        config_tab = self.tabview.tab("Configuration")
        config_tab.grid_columnconfigure(0, weight=1)
        
        # Create scrollable frame
        scrollable_frame = ctk.CTkScrollableFrame(config_tab)
        scrollable_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        scrollable_frame.grid_columnconfigure(0, weight=1)
        
        # Metadata Section
        metadata_frame = ctk.CTkFrame(scrollable_frame)
        metadata_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        metadata_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            metadata_frame,
            text="Metadata Settings",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 5))
        
        # Default Description
        ctk.CTkLabel(
            metadata_frame,
            text="Default Description:",
            font=ctk.CTkFont(size=12)
        ).grid(row=1, column=0, sticky="w", padx=10, pady=(10, 5))
        
        self.description_text = ctk.CTkTextbox(
            metadata_frame,
            height=100,
            wrap="word"
        )
        self.description_text.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        
        # Default Hashtags
        ctk.CTkLabel(
            metadata_frame,
            text="Default Hashtags (comma-separated):",
            font=ctk.CTkFont(size=12)
        ).grid(row=3, column=0, sticky="w", padx=10, pady=(10, 5))
        
        self.hashtags_entry = ctk.CTkEntry(
            metadata_frame,
            placeholder_text="viral, trending, shorts"
        )
        self.hashtags_entry.grid(row=4, column=0, sticky="ew", padx=10, pady=(0, 20))
        
        # Processing Parameters Section
        params_frame = ctk.CTkFrame(scrollable_frame)
        params_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        params_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            params_frame,
            text="Processing Parameters",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 15))
        
        # Min Viral Score
        ctk.CTkLabel(
            params_frame,
            text="Min Viral Score Threshold:",
            font=ctk.CTkFont(size=12)
        ).grid(row=1, column=0, sticky="w", padx=10, pady=10)
        
        self.viral_score_frame = ctk.CTkFrame(params_frame)
        self.viral_score_frame.grid(row=1, column=1, sticky="ew", padx=10, pady=10)
        
        self.viral_score_slider = ctk.CTkSlider(
            self.viral_score_frame,
            from_=0,
            to=100,
            number_of_steps=100,
            command=self.update_viral_score_label
        )
        self.viral_score_slider.set(70)
        self.viral_score_slider.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.viral_score_label = ctk.CTkLabel(
            self.viral_score_frame,
            text="70",
            width=40
        )
        self.viral_score_label.pack(side="left")
        
        # Max Clips
        ctk.CTkLabel(
            params_frame,
            text="Max Clips per Video:",
            font=ctk.CTkFont(size=12)
        ).grid(row=2, column=0, sticky="w", padx=10, pady=10)
        
        self.max_clips_frame = ctk.CTkFrame(params_frame)
        self.max_clips_frame.grid(row=2, column=1, sticky="ew", padx=10, pady=10)
        
        self.max_clips_slider = ctk.CTkSlider(
            self.max_clips_frame,
            from_=1,
            to=10,
            number_of_steps=9,
            command=self.update_max_clips_label
        )
        self.max_clips_slider.set(5)
        self.max_clips_slider.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.max_clips_label = ctk.CTkLabel(
            self.max_clips_frame,
            text="5",
            width=40
        )
        self.max_clips_label.pack(side="left")
        
        # Platform Selection Section
        platform_frame = ctk.CTkFrame(scrollable_frame)
        platform_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        platform_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            platform_frame,
            text="Target Platforms",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 15))
        
        # Platform checkboxes
        self.instagram_var = ctk.BooleanVar(value=True)
        self.instagram_check = ctk.CTkCheckBox(
            platform_frame,
            text="📷 Instagram Reels",
            variable=self.instagram_var,
            font=ctk.CTkFont(size=13)
        )
        self.instagram_check.grid(row=1, column=0, sticky="w", padx=20, pady=5)
        
        self.youtube_var = ctk.BooleanVar(value=True)
        self.youtube_check = ctk.CTkCheckBox(
            platform_frame,
            text="▶ YouTube Shorts",
            variable=self.youtube_var,
            font=ctk.CTkFont(size=13)
        )
        self.youtube_check.grid(row=2, column=0, sticky="w", padx=20, pady=5)
        
        self.tiktok_var = ctk.BooleanVar(value=True)
        self.tiktok_check = ctk.CTkCheckBox(
            platform_frame,
            text="🎵 TikTok",
            variable=self.tiktok_var,
            font=ctk.CTkFont(size=13)
        )
        self.tiktok_check.grid(row=3, column=0, sticky="w", padx=20, pady=(5, 20))
        
        # Auto-upload checkbox
        self.auto_upload_var = ctk.BooleanVar(value=True)
        self.auto_upload_check = ctk.CTkCheckBox(
            scrollable_frame,
            text="🚀 Auto-schedule uploads after processing",
            variable=self.auto_upload_var,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.auto_upload_check.grid(row=3, column=0, sticky="w", padx=20, pady=20)
    
    def setup_logs_tab(self):
        """Setup the logs tab"""
        logs_tab = self.tabview.tab("Logs")
        logs_tab.grid_columnconfigure(0, weight=1)
        logs_tab.grid_rowconfigure(0, weight=1)
        
        # Log text area
        self.log_text = ctk.CTkTextbox(
            logs_tab,
            wrap="word",
            font=ctk.CTkFont(family="Courier", size=11)
        )
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    
    def update_viral_score_label(self, value):
        """Update viral score label"""
        self.viral_score_label.configure(text=f"{int(value)}")
    
    def update_max_clips_label(self, value):
        """Update max clips label"""
        self.max_clips_label.configure(text=f"{int(value)}")
    
    def change_appearance_mode(self, new_mode):
        """Change appearance mode"""
        ctk.set_appearance_mode(new_mode)
    
    def select_video_files(self):
        """Open file dialog to select video files and copy to input directory"""
        filetypes = [
            ("Video files", "*.mp4 *.mov *.avi *.mkv"),
            ("All files", "*.*")
        ]
        
        filenames = filedialog.askopenfilenames(
            title="Select Video Files",
            filetypes=filetypes
        )
        
        if filenames:
            copied_count = 0
            for file_path in filenames:
                try:
                    # Copy file to input directory
                    filename = os.path.basename(file_path)
                    dest_path = self.input_videos_path / filename
                    
                    shutil.copy2(file_path, dest_path)
                    copied_count += 1
                    self.log_message(f"Copied: {filename} -> {dest_path}")
                
                except Exception as e:
                    self.log_message(f"Error copying {file_path}: {e}")
            
            if copied_count > 0:
                messagebox.showinfo(
                    "Success",
                    f"Successfully copied {copied_count} video(s) to {self.input_videos_path}"
                )
                self.log_message(f"\n✓ {copied_count} video file(s) ready for processing\n")
    
    def load_config_values(self):
        """Load current configuration values from settings.yaml"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            metadata = config.get('metadata', {})
            
            # Load default description
            default_desc = metadata.get('default_description', '')
            if default_desc:
                self.description_text.delete('1.0', 'end')
                self.description_text.insert('1.0', default_desc)
            
            # Load default hashtags override
            default_hashtags = metadata.get('default_hashtags_override', '')
            if default_hashtags:
                self.hashtags_entry.delete(0, 'end')
                self.hashtags_entry.insert(0, default_hashtags)
            
            self.log_message("✓ Configuration loaded successfully\n")
        
        except Exception as e:
            self.log_message(f"⚠ Error loading configuration: {e}\n")
    
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
            default_desc = self.description_text.get('1.0', 'end').strip()
            default_hashtags = self.hashtags_entry.get().strip()
            
            # Update config
            config['metadata']['default_description'] = default_desc
            config['metadata']['default_hashtags_override'] = default_hashtags
            
            # Write back to file
            with open(self.config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            
            self.log_message("✓ Configuration saved successfully!\n")
            messagebox.showinfo("Success", "Configuration saved successfully!")
        
        except Exception as e:
            error_msg = f"⚠ Error saving configuration: {e}"
            self.log_message(error_msg + "\n")
            messagebox.showerror("Error", error_msg)
    
    def start_processing(self):
        """Start the video processing in a separate thread"""
        if self.is_processing:
            messagebox.showwarning("Warning", "Processing is already running!")
            return
        
        # Get selected platforms
        platforms = []
        if self.instagram_var.get():
            platforms.append('instagram')
        if self.youtube_var.get():
            platforms.append('youtube')
        if self.tiktok_var.get():
            platforms.append('tiktok')
        
        if not platforms:
            messagebox.showwarning("Warning", "Please select at least one platform!")
            return
        
        # Get processing parameters
        self.min_viral_score = int(self.viral_score_slider.get())
        self.max_clips = int(self.max_clips_slider.get())
        self.selected_platforms = platforms
        self.auto_upload = self.auto_upload_var.get()
        
        # Update UI state
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.status_label.configure(text="● Status: Processing...")
        self.tabview.set("Logs")  # Switch to logs tab
        
        # Start processing in a separate thread
        self.processing_thread = threading.Thread(target=self.run_processing, daemon=True)
        self.processing_thread.start()
        
        self.is_processing = True
    
    def run_processing(self):
        """Run the video processing (executed in separate thread)"""
        try:
            self.log_message("=" * 80)
            self.log_message("🚀 Starting Video Clipping System...")
            self.log_message("=" * 80)
            self.log_message(f"Target Platforms: {', '.join(self.selected_platforms)}")
            self.log_message(f"Min Viral Score: {self.min_viral_score}")
            self.log_message(f"Max Clips: {self.max_clips}")
            self.log_message(f"Auto-upload: {'Enabled' if self.auto_upload else 'Disabled'}")
            self.log_message("=" * 80 + "\n")
            
            # Initialize system
            self.system = VideoClippingSystem()
            self.log_message("✓ System initialized successfully\n")
            
            # Start scheduler if auto-upload is enabled
            if self.auto_upload:
                self.system.start_scheduler()
                self.log_message("✓ Upload scheduler started\n")
            
            # Discover videos
            videos = self.system.discover_videos()
            if not videos:
                self.log_message("⚠ No videos found in input directory\n")
                self.update_status_safe("Status: No videos found")
                return
            
            self.log_message(f"📹 Found {len(videos)} video(s) to process\n")
            
            # Process videos
            results = []
            for i, video_path in enumerate(videos, 1):
                self.log_message(f"\n{'='*80}")
                self.log_message(f"Processing video {i}/{len(videos)}: {os.path.basename(video_path)}")
                self.log_message(f"{'='*80}\n")
                
                # Update the process_video call to use our parameters
                result = self.process_video_with_params(video_path)
                results.append(result)
            
            # Log final results
            total_clips = sum(len(r['clips']) for r in results)
            total_uploads = sum(len(r['scheduled_uploads']) for r in results)
            
            self.log_message("\n" + "=" * 80)
            self.log_message("🎉 Processing Complete!")
            self.log_message("=" * 80)
            self.log_message(f"Videos processed: {len(results)}")
            self.log_message(f"Clips extracted: {total_clips}")
            self.log_message(f"Uploads scheduled: {total_uploads}")
            self.log_message("=" * 80 + "\n")
            
            # Update status
            self.update_status_safe(
                f"Status: Complete ({total_clips} clips, {total_uploads} uploads)"
            )
        
        except Exception as e:
            error_msg = f"⚠ Error during processing: {e}"
            self.log_message(error_msg + "\n")
            self.update_status_safe("Status: Error")
            # Show error in main thread
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        
        finally:
            # Stop scheduler if it was started
            if self.system and self.auto_upload:
                try:
                    self.system.stop_scheduler()
                    self.log_message("✓ Upload scheduler stopped\n")
                except Exception as e:
                    self.log_message(f"⚠ Error stopping scheduler: {e}\n")
            
            # Re-enable controls
            self.root.after(0, lambda: self.start_btn.configure(state="normal"))
            self.root.after(0, lambda: self.stop_btn.configure(state="disabled"))
            self.is_processing = False
    
    def process_video_with_params(self, video_path):
        """Process video with custom parameters from UI"""
        results = {
            'video_path': video_path,
            'clips': [],
            'scheduled_uploads': []
        }
        
        try:
            # Step 1: Analyze video with custom min_score and max_segments
            self.log_message("Step 1: Analyzing video...")
            segments = self.system.video_analyzer.get_best_segments(
                video_path,
                min_score=self.min_viral_score,
                max_segments=self.max_clips
            )
            
            if not segments:
                self.log_message("⚠ No viral segments found in video\n")
                return results
            
            self.log_message(f"✓ Found {len(segments)} viral segment(s)\n")
            
            # Step 2: Extract clips
            self.log_message("Step 2: Extracting clips...")
            output_dir = self.system.settings['paths']['output_clips']
            clips = self.system.clip_extractor.extract_clips(video_path, segments, output_dir)
            
            if not clips:
                self.log_message("⚠ No clips extracted\n")
                return results
            
            results['clips'] = clips
            self.log_message(f"✓ Extracted {len(clips)} clip(s)\n")
            
            # Step 3: Optimize and generate metadata for each platform
            self.log_message("Step 3: Optimizing clips and generating metadata...")
            for clip_info in clips:
                clip_path = clip_info['path']
                
                # Generate metadata for selected platforms
                metadata = self.system.metadata_generator.generate_metadata_for_clip(
                    clip_info,
                    self.selected_platforms
                )
                
                # Optimize for each platform
                for platform in self.selected_platforms:
                    optimized_path = self.system.format_optimizer.optimize_for_platform(
                        clip_path,
                        platform
                    )
                    
                    if optimized_path and self.auto_upload:
                        # Create upload task
                        upload_task = {
                            'video_path': video_path,
                            'clip_path': optimized_path,
                            'platform': platform,
                            'metadata': metadata.get(platform, {})
                        }
                        
                        # Schedule upload
                        upload_function = self.system._get_upload_function(platform)
                        if upload_function:
                            job_id = self.system.upload_scheduler.schedule_upload(
                                upload_task,
                                upload_function
                            )
                            results['scheduled_uploads'].append({
                                'job_id': job_id,
                                'platform': platform,
                                'clip_path': optimized_path
                            })
            
            self.log_message(
                f"✓ Processing complete: {len(clips)} clips, "
                f"{len(results['scheduled_uploads'])} uploads scheduled\n"
            )
            return results
        
        except Exception as e:
            self.log_message(f"⚠ Error processing video: {e}\n")
            return results
    
    def stop_processing(self):
        """Stop the video processing"""
        if not self.is_processing:
            return
        
        if messagebox.askyesno("Confirm", "Are you sure you want to stop processing?"):
            self.log_message("\n⚠ Stopping processing...\n")
            # The processing will stop after the current video
            self.is_processing = False
            
            if self.system:
                try:
                    self.system.stop_scheduler()
                except Exception as e:
                    self.log_message(f"⚠ Error stopping scheduler: {e}\n")
            
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
            self.update_status_safe("Status: Stopped by user")
    
    def setup_logging(self):
        """Setup logging to redirect to UI text area"""
        # Create custom handler
        class TextHandler(logging.Handler):
            def __init__(self, text_widget, root):
                logging.Handler.__init__(self)
                self.text_widget = text_widget
                self.root = root
            
            def emit(self, record):
                msg = self.format(record)
                def append():
                    self.text_widget.insert('end', msg + '\n')
                    self.text_widget.see('end')
                # Schedule on main thread
                self.root.after(0, append)
        
        # Add handler to root logger
        text_handler = TextHandler(self.log_text, self.root)
        text_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s',
                            datefmt='%H:%M:%S')
        )
        logging.getLogger().addHandler(text_handler)
        logging.getLogger().setLevel(logging.INFO)
    
    def log_message(self, message):
        """Log a message to the text area"""
        def append():
            self.log_text.insert('end', message + '\n')
            self.log_text.see('end')
        
        # Schedule on main thread
        self.root.after(0, append)
    
    def update_status_safe(self, status_text):
        """Safely update status from any thread"""
        self.root.after(0, lambda: self.status_label.configure(text=f"● {status_text}"))
    
    def clear_logs(self):
        """Clear the log text area"""
        self.log_text.delete('1.0', 'end')
        self.log_message("Logs cleared.\n")
    
    def on_closing(self):
        """Handle window close event"""
        if self.is_processing:
            if messagebox.askokcancel(
                "Quit",
                "Processing is still running. Do you want to stop and quit?"
            ):
                # Stop the system if it's running
                if self.system:
                    try:
                        self.system.stop_scheduler()
                        self.log_message("✓ System stopped by user\n")
                    except Exception as e:
                        self.log_message(f"⚠ Error stopping system: {e}\n")
                
                self.is_processing = False
                self.root.destroy()
        else:
            self.root.destroy()


def main():
    """Main entry point for the UI"""
    root = ctk.CTk()
    app = ModernVideoClippingUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
