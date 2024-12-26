from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLineEdit, QPushButton, QLabel, QFrame, QSizePolicy,
                            QScrollArea, QInputDialog, QTextEdit)
from modules.Search_by_name import FacebookPageSearcher
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect, QTimer, QEasingCurve, QSize, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QMovie
import sys
import os

"""
in section 2 will  have title called Scraping then TextEdit to apper logging the in the left will bw small icon btn to scrping from file
i want  to remove file_btn and replace it with stop btn
"""
class SearchWorker(QThread):
    finished = pyqtSignal(list)  # Signal to emit when search is complete
    progress = pyqtSignal(str)   # Signal to emit progress updates
    
    def __init__(self, search_query, num_results):
        super().__init__()
        self.search_query = search_query
        self.num_results = num_results
        
    def run(self):
        try:
            searcher = FacebookPageSearcher()
            # Create a wrapper function to capture the log messages
            def log_callback(message):
                self.progress.emit(message)
            
            results = searcher.search_pages(self.search_query, self.num_results, log_callback)
            self.finished.emit(results)
        except Exception as e:
            self.progress.emit(f"Error during search: {str(e)}\n")
            self.finished.emit([])


class ModernGUI(QWidget):
    def __init__(self):
        super().__init__()

        # Initialize window
        self.setWindowTitle("PODER")
        self.setGeometry(100, 100, 1000, 600)  # Set the window size (wide)

        # Set window background color
        self.setStyleSheet("background-color: white;")

        # Create the main layout
        main_layout = QHBoxLayout()  # Use HBox for horizontal layout
        
        # Create timer for history updates
        self.history_timer = QTimer()
        self.history_timer.timeout.connect(self.update_history)
        self.history_timer.start(1000)  # Update every second

        # Create the sidebar
        self.sidebar = QFrame(self)
        self.sidebar.setStyleSheet("""
            QFrame {
                background-color: #0a0a0a;
                color: white;
                border: none;
                position: absolute;
            }
        """)
        
        # Set the sidebar to stay on top
        self.sidebar.raise_()

        # Create a layout for sidebar buttons
        sidebar_layout = QVBoxLayout()
        
        # Add developer info at the top
        dev_info_frame = QFrame()
        dev_info_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border-radius: 5px;
                margin: 5px;
                padding: 5px;
            }
            QLabel {
                color: #888;
                font-size: 9px;
                margin: 1px;
            }
        """)
        dev_info_layout = QVBoxLayout()
        dev_info_layout.setSpacing(0)  # Reduce spacing between elements
        
        # App name and version
        app_name = QLabel("PODER")
        app_name.setStyleSheet("""
            color: white;
            font-size: 11px;
            font-weight: bold;
            padding-bottom: 2px;
        """)

        app_version = QLabel("Version 0.2.1")
        
        # Developer info
        dev_name = QLabel("by: Youssef Mohamad Abdallah")
        github = QLabel("GitHub: github.com/lordpaoloo")
        
        dev_info_layout.addWidget(app_name)
        dev_info_layout.addWidget(app_version)
        dev_info_layout.addWidget(dev_name)
        dev_info_layout.addWidget(github)

        
        dev_info_frame.setLayout(dev_info_layout)
        sidebar_layout.addWidget(dev_info_frame)
        
        # Add a stretch to push the toggle button to the bottom
        sidebar_layout.addStretch()

        # Add auto-scraping toggle (On/Off switch)

        self.auto_scraping_toggle = QPushButton("Auto Scraping: Off", self)

        self.auto_scraping_toggle.setCheckable(True)  # Make it toggleable
        self.auto_scraping_toggle.setStyleSheet("""
            QPushButton {
                background-color: black;
                border: 2px solid white;
                color: white;
                font-size: 12px;
                padding: 5px;
                margin: 10px;
                text-align: center;
                border-radius: 15px;
                max-width: 150px;
                min-height: 30px;
            }
            QPushButton:checked {
                background-color: white;
                color: black;
                border: 2px solid black;
            }
            QPushButton:focus {
                outline: none;
            }
        """)
        self.auto_scraping_toggle.toggled.connect(self.toggle_auto_scraping)
        sidebar_layout.addWidget(self.auto_scraping_toggle, 0, Qt.AlignCenter)  # Center align the button
        
        # Add some padding at the bottom
        sidebar_layout.addSpacing(10)

        self.sidebar.setLayout(sidebar_layout)

        # Create the main content area
        content_layout = QVBoxLayout()

        # Create a layout for the search bar and button
        search_layout = QHBoxLayout()

        # Search bar
        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Enter search query...")
        self.search_bar.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                font-size: 16px;
                border: 1px solid #D1D9E6;
                border-radius: 5px;
            }
            QLineEdit:focus {
                border: 1px solid #000000;
            }
        """)

        # Search button
        self.search_button = QPushButton("Search", self)
        self.search_button.setStyleSheet("""
            QPushButton {
                padding: 10px 15px;
                background-color: #0a0a0a;
                color: white;
                border-radius: 5px;
                border: 1px solid #000000;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #ffffff;
                color: #000000;
            }
        """)
        self.search_button.clicked.connect(self.handle_search)

        # Add search bar and button to search layout
        search_layout.addWidget(self.search_bar)
        search_layout.addWidget(self.search_button)

        # Add search layout to main content layout
        content_layout.addLayout(search_layout)

        # Create sections layout

        sections_layout = QHBoxLayout()
        
        # Create history section (vertical on right)
        history_frame = QFrame()
        history_frame.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border-radius: 10px;
                margin: 5px;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
            QScrollBar:vertical {
                width: 8px;
                background: #f0f0f0;
            }
            QScrollBar::handle:vertical {
                background: #888;
                border-radius: 4px;
            }
        """)
        history_layout = QVBoxLayout()
        
        # Add history label
        history_label = QLabel("History")
        history_label.setStyleSheet("font-weight: bold; font-size: 16px; padding: 10px;")
        history_label.setAlignment(Qt.AlignCenter)
        history_layout.addWidget(history_label)
        
        # Create scroll area for vertical cards
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Create widget to hold cards
        cards_widget = QWidget()
        self.cards_layout = QVBoxLayout()  # Changed to VBoxLayout for vertical arrangement
        self.cards_layout.setSpacing(10)
        
        # Load results from the results folder
        results_dir = 'results'
        if os.path.exists(results_dir):
            result_files = [f for f in os.listdir(results_dir) ]
            
            # Sort files by modification time (newest first)
            result_files.sort(key=lambda x: os.path.getmtime(os.path.join(results_dir, x)), reverse=True)
            
            for filename in result_files:
                # Parse filename
                parts = filename.replace('.txt', '').split('&')
                if len(parts) >= 4:
                    query = parts[0]
                    count = parts[1]
                    date_str = parts[2]
                    time_str = parts[3]
                else:
                    continue  # Skip invalid filenames
                
                card = QFrame()
                card.setStyleSheet("""
                    QFrame {
                        background-color: white;
                        border-radius: 6px;
                        min-width: 120px;
                        max-width: 500px;
                        min-height: 60px;
                        max-height: 120px;
                        margin: 3px;
                        padding: 5px;
                    }
                """)
                card_layout = QVBoxLayout()
                card_layout.setSpacing(2)
                
                # Query as title
                title = QLabel(f"Search: {query}")
                title.setStyleSheet("""
                    font-weight: bold;
                    color: #333;
                    font-size: 12px;
                    padding-bottom: 2px;
                """)
                title.setAlignment(Qt.AlignLeft)
                
                # Results count and datetime
                content = QLabel(f"Results: {count}\nDate: {date_str} {time_str}")
                content.setWordWrap(True)
                content.setStyleSheet("color: #666; font-size: 10px;")
                
                # Button container
                button_container = QHBoxLayout()
                button_container.addStretch()
                
                # Folder button
                folder_btn = QPushButton()
                folder_btn.setIcon(QIcon("folder_icon.png"))
                folder_btn.setIconSize(QSize(16, 16))
                folder_btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        border: none;
                        padding: 2px;
                        max-width: 16px;
                        max-height: 16px;
                    }
                    QPushButton:hover {
                        background-color: #f0f0f0;
                        border-radius: 3px;
                    }
                """)
                folder_btn.clicked.connect(lambda checked, f=filename: self.open_folder(f))
                button_container.addWidget(folder_btn)
                
                # Add elements to card
                card_layout.addWidget(title)
                card_layout.addWidget(content)
                card_layout.addLayout(button_container)
                
                card_layout.setContentsMargins(5, 5, 5, 5)
                card.setLayout(card_layout)
                self.cards_layout.addWidget(card)
        else:
            # Show message if no results folder exists
            no_results = QLabel("No search results found")
            no_results.setStyleSheet("color: #666; font-size: 12px; padding: 20px;")
            no_results.setAlignment(Qt.AlignCenter)
            self.cards_layout.addWidget(no_results)
        
        # Add stretch at the end to align cards to the top
        self.cards_layout.addStretch()
        
        cards_widget.setLayout(self.cards_layout)
        scroll_area.setWidget(cards_widget)
        history_layout.addWidget(scroll_area)
        
        history_frame.setLayout(history_layout)
        
        # Create left sections container
        left_sections = QVBoxLayout()
        
        # Create top two sections in a horizontal layout
        top_sections = QHBoxLayout()
        
        # First top section
        section1_frame = QFrame()
        section1_frame.setStyleSheet("""
            QFrame {
                background-color: #e8e8e8;
                border-radius: 10px;
                margin: 5px;
            }
        """)
        section1_layout = QVBoxLayout()
        section1_label = QLabel("SEARCH ")
        section1_label.setStyleSheet("font-weight: bold; font-size: 15px; padding: 5px;")
        section1_label.setAlignment(Qt.AlignCenter)
        
        # Create log display area
        self.log_display = QTextEdit()
        self.log_display.setMinimumHeight(300)  # Set minimum height  # Set minimum width
        self.log_display.setReadOnly(True)
        self.log_display.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Consolas', monospace;
                font-size: 12px;
            }
        """)
        
        # Create loading overlay
        self.loading_overlay = QLabel(self.log_display)
        self.loading_overlay.setAlignment(Qt.AlignCenter)
        self.loading_movie = QMovie("loading.gif")  # Make sure to have this file
        self.loading_overlay.setMovie(self.loading_movie)
        self.loading_overlay.hide()  # Initially hidden
        
        # Style the overlay
        self.loading_overlay.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 0.7);
                border-radius: 5px;
            }
        """)
        
        section1_layout.addWidget(section1_label)
        section1_layout.addWidget(self.log_display)
        section1_frame.setLayout(section1_layout)
        
        # Second top section
        section2_frame = QFrame()
        section2_frame.setStyleSheet("""
            QFrame {
                background-color: #e8e8e8;
                border-radius: 10px;
                margin: 5px;
            }
        """)
        section2_layout = QVBoxLayout()
        section2_label = QLabel("SCRAPING")
        section2_label.setStyleSheet("font-weight: bold; font-size: 16px; padding: 10px;")
        section2_label.setAlignment(Qt.AlignCenter)
        
        # Create log display area
        self.scraping_log_display= QTextEdit()
        self.scraping_log_display.setMinimumHeight(300)  # Set minimum height  # Set minimum width
        self.scraping_log_display.setReadOnly(True)
        self.scraping_log_display.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Consolas', monospace;
                font-size: 12px;
            }
        """)
        file_button_container = QHBoxLayout()
        file_button_container.addStretch()
        file_button_container_widget = QWidget()
        file_button_container_widget.setStyleSheet("""
        QWidget {
                background-color: #ffffff;
                border-radius: 10px;
                margin: 5px;
                padding: 5px;
                min-height: 40px;
            }
        """)

        # scraping from file btn
        file_scraping_btn=QPushButton()
        file_scraping_btn.setIconSize(QSize(16, 16))
        file_scraping_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 2px;
                max-width: 100px;
                max-height: 16px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
                border-radius: 3px;
            }
        """)
        # stop button
        stop_btn = QPushButton("Stop")  # Changed to use text instead of icon
        stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff5252;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 5px 10px;
                min-width: 200px;
                max-width: 700px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #ff1744;
            }
        """)
        file_button_container.addWidget(stop_btn)
        file_button_container.addWidget(file_scraping_btn)
        file_button_container_widget.setLayout(file_button_container)

        section2_layout.addWidget(section2_label)
        section2_layout.addWidget(self.scraping_log_display)
        section2_layout.addWidget(file_button_container_widget)
        section2_frame.setLayout(section2_layout)
        
        # Add top sections to their layout
        top_sections.addWidget(section1_frame)
        top_sections.addWidget(section2_frame)
        
        # Create bottom section
        section3_frame = QFrame()
        section3_frame.setStyleSheet("""
            QFrame {
                background-color: #e8e8e8;
                border-radius: 10px;
                margin: 5px;
            }
        """)
        section3_layout = QVBoxLayout()
        section3_label = QLabel("Section 3")
        section3_label.setStyleSheet("font-weight: bold; font-size: 16px; padding: 10px;")
        section3_label.setAlignment(Qt.AlignCenter)
        section3_layout.addWidget(section3_label)
        section3_frame.setLayout(section3_layout)
        
        # Add all sections to their respective layouts
        left_sections.addLayout(top_sections)
        left_sections.addWidget(section3_frame)
        
        # Add left sections and history to main sections layout
        sections_layout.addLayout(left_sections, 2)  # Stretch factor of 2
        sections_layout.addWidget(history_frame, 1)  # Stretch factor of 1
        
        # Add sections layout to main content layout
        content_layout.addLayout(sections_layout)

        # Set size policies for better layout management
        history_frame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        section1_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        section2_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        section3_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Create a frame to contain the main content area (to separate from sidebar)
        content_frame = QFrame(self)
        content_frame.setLayout(content_layout)

        # Add content to the main layout (sidebar will float)
        main_layout.addWidget(content_frame)


        # Set the main layout
        self.setLayout(main_layout)

        # Set up hover effect for the sidebar (hide and show on hover)
        self.setMouseTracking(True)  # Enable mouse tracking for hover effect

        # Sidebar animation for smooth transitions
        self.sidebar_anim = QPropertyAnimation(self.sidebar, b"geometry")
        self.sidebar_anim.setDuration(150)  # Fast animation for responsiveness
        self.sidebar_anim.setEasingCurve(QEasingCurve.InOutQuad)




        self.sidebar_width = 200  # Width of the sidebar
        self.sidebar_hidden_x = -self.sidebar_width  # Hidden position
        self.sidebar_visible_x = 0  # Visible position

        # Initially hide the sidebar
        self.sidebar.setGeometry(self.sidebar_hidden_x, 0, self.sidebar_width, self.height())

    def set_loading(self, loading):
        if loading:
            # Position the overlay in the center of log_display
            self.loading_overlay.resize(self.log_display.size())
            self.loading_movie.start()
            self.loading_overlay.show()
        else:
            self.loading_movie.stop()
            self.loading_overlay.hide()

    def mouseMoveEvent(self, event):
        # Get the mouse position relative to the window
        mouse_pos = event.pos()
        sidebar_rect = self.sidebar.geometry()
        
        # Define the sensitive area (2 pixels from the left edge)
        sensitive_area = 2
        
        # Show sidebar only when mouse is in the sensitive area or within sidebar
        if mouse_pos.x() <= sensitive_area or sidebar_rect.contains(mouse_pos):
            self.show_sidebar()
        elif mouse_pos.x() > sidebar_rect.right():
            # Hide sidebar immediately when mouse moves away from it
            self.hide_sidebar()

    def open_folder(self, filename):
        """Open the folder containing the results file and select it"""
        filepath = os.path.join('results', filename)
        if os.path.exists(filepath):
            # Use explorer to open folder and select the file
            os.system(f'explorer /select,"{os.path.abspath(filepath)}"')
    def handle_search(self):
        # Get search query
        search_query = self.search_bar.text().strip()
        
        if not search_query:
            from PyQt5.QtWidgets import QMessageBox
            alert = QMessageBox()
            alert.setWindowTitle('Error')
            alert.setText('Please enter a search query')
            alert.setIcon(QMessageBox.Warning)
            alert.setStyleSheet("""
                QMessageBox {
                    background-color: white;
                }
                QLabel {
                    font-size: 16px;
                    padding: 10px;
                    color: #000000;
                    min-width: 200px;
                }
                QPushButton {
                    padding: 10px 15px;
                    background-color: #0a0a0a;
                    color: white;
                    border-radius: 5px;
                    border: 1px solid #000000;
                    font-size: 16px;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #ffffff;
                    color: #000000;
                }
            """)
            alert.exec_()
            return

        # Create styled input dialog for number of results
        dialog = QInputDialog(self)
        dialog.setWindowTitle('Number of Results')
        dialog.setLabelText('How many results do you want?')
        dialog.setIntRange(1, 100)
        dialog.setIntValue(10)
        
        # Apply modern styling
        dialog.setStyleSheet("""
            QLabel {
                font-size: 16px;
                padding: 10px;
                color: #000000;
            }
            QSpinBox {
                padding: 10px;
                font-size: 16px;
                border: 1px solid #D1D9E6;
                border-radius: 5px;
                min-width: 150px;
            }
            QSpinBox:focus {
                border: 1px solid #000000;
            }
            QPushButton {
                padding: 10px 15px;
                background-color: #0a0a0a;
                color: white;
                border-radius: 5px;
                border: 1px solid #000000;
                font-size: 16px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #ffffff;
                color: #000000;
            }
        """)
        
        ok = dialog.exec_()
        num_results = dialog.intValue()
        
        if not ok:
            return  # User cancelled

        # Show loading animation
        self.set_loading(True)
        self.log_display.append(f"Starting search for: {search_query}")
        self.log_display.append(f"Requested results: {num_results}")

        # Create and start worker thread
        self.search_worker = SearchWorker(search_query, num_results)
        self.search_worker.progress.connect(self.log_display.append)
        self.search_worker.finished.connect(self.handle_search_complete)
        self.search_worker.start()

    def handle_search_complete(self, results):
        if results:
            self.log_display.append(f"Found {len(results)} results")
            for result in results:
                self.log_display.append(f"Found: {result['page_link']}")
        else:
            self.log_display.append("No results found")
        
        self.log_display.append("Search completed\n")
        self.set_loading(False)
            

    def toggle_auto_scraping(self, checked):
        if checked:
            self.auto_scraping_toggle.setText("Auto Scraping: On")
            print("Auto Scraping Enabled")
        else:
            self.auto_scraping_toggle.setText("Auto Scraping: Off")


        print(f"Opening folder for history item {index + 1}")
        # Add your folder opening logic here


    def show_sidebar(self):
        # Only show if it's not already visible
        if self.sidebar.geometry().x() != self.sidebar_visible_x:
            self.sidebar.raise_()
            self.sidebar_anim.stop()
            self.sidebar_anim.setStartValue(QRect(self.sidebar_hidden_x, 0, self.sidebar_width, self.height()))
            self.sidebar_anim.setEndValue(QRect(self.sidebar_visible_x, 0, self.sidebar_width, self.height()))
            self.sidebar_anim.start()

    def hide_sidebar(self):
        # Only hide if it's not already hidden
        if self.sidebar.geometry().x() != self.sidebar_hidden_x:
            self.sidebar_anim.stop()
            self.sidebar_anim.setStartValue(QRect(self.sidebar_visible_x, 0, self.sidebar_width, self.height()))
            self.sidebar_anim.setEndValue(QRect(self.sidebar_hidden_x, 0, self.sidebar_width, self.height()))
            self.sidebar_anim.start()
            
    def update_history(self):
        """Update the history section with latest results"""
        # Clear existing cards
        for i in reversed(range(self.cards_layout.count())):
            widget = self.cards_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
                
        # Load results from the results folder
        results_dir = 'results'
        if os.path.exists(results_dir):
            result_files = [f for f in os.listdir(results_dir)]
            
            # Sort files by modification time (newest first)
            result_files.sort(key=lambda x: os.path.getmtime(os.path.join(results_dir, x)), reverse=True)
            
            for filename in result_files:
                # Parse filename
                parts = filename.replace('.txt', '').split('&')
                if len(parts) >= 4:
                    query = parts[0]
                    count = parts[1]
                    date_str = parts[2]
                    time_str = parts[3]
                else:
                    continue  # Skip invalid filenames
                
                card = QFrame()
                card.setStyleSheet("""
                    QFrame {
                        background-color: white;
                        border-radius: 6px;
                        min-width: 120px;
                        max-width: 500px;
                        min-height: 60px;
                        max-height: 120px;
                        margin: 3px;
                        padding: 5px;
                    }
                """)
                card_layout = QVBoxLayout()
                card_layout.setSpacing(2)
                
                # Query as title
                title = QLabel(f"Search: {query}")
                title.setStyleSheet("""
                    font-weight: bold;
                    color: #333;
                    font-size: 12px;
                    padding-bottom: 2px;
                """)
                title.setAlignment(Qt.AlignLeft)
                
                # Results count and datetime
                content = QLabel(f"Results: {count}\nDate: {date_str} {time_str}")
                content.setWordWrap(True)
                content.setStyleSheet("color: #666; font-size: 10px;")
                
                # Button container
                button_container = QHBoxLayout()
                button_container.addStretch()
                
                # Folder button
                folder_btn = QPushButton()
                folder_btn.setIcon(QIcon("folder_icon.png"))
                folder_btn.setIconSize(QSize(16, 16))
                folder_btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        border: none;
                        padding: 2px;
                        max-width: 16px;
                        max-height: 16px;
                    }
                    QPushButton:hover {
                        background-color: #f0f0f0;
                        border-radius: 3px;
                    }
                """)
                folder_btn.clicked.connect(lambda checked, f=filename: self.open_folder(f))
                button_container.addWidget(folder_btn)
                # Add elements to card
                card_layout.addWidget(title)
                card_layout.addWidget(content)
                card_layout.addLayout(button_container)
                card_layout.setContentsMargins(5, 5, 5, 5)
                card.setLayout(card_layout)
                self.cards_layout.addWidget(card)
        else:
            # Show message if no results folder exists
            no_results = QLabel("No search results found")
            no_results.setStyleSheet("color: #666; font-size: 12px; padding: 20px;")
            no_results.setAlignment(Qt.AlignCenter)
            self.cards_layout.addWidget(no_results)        
        # Add stretch at the end to align cards to the top
        self.cards_layout.addStretch()
    def toggle_auto_scraping(self, checked):
        if checked:
            self.auto_scraping_toggle.setText("Auto Scraping: On")
            print("Auto Scraping Enabled")
        else:
            self.auto_scraping_toggle.setText("Auto Scraping: Off")
            print("Auto Scraping Disabled")

# Run the application
if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Apply a global style for a clean, modern theme
    app.setStyleSheet("""
        QWidget {
            font-family: 'Arial', sans-serif;
            font-size: 14px;
        }
    """)
    # Create and show the window
    window = ModernGUI()
    window.show()
    sys.exit(app.exec_())
