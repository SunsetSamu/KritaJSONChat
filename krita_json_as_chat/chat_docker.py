from krita import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor, QTextCharFormat, QFont, QSyntaxHighlighter
from PyQt5.QtCore import Qt, QTimer, QDateTime, QRegularExpression
import json
import os
import platform
import subprocess

class ChatHighlighter(QSyntaxHighlighter):
    def __init__(self, parent, theme_color_tag, theme_color_user):
        super().__init__(parent)
        self.theme_color_tag = theme_color_tag
        self.theme_color_user = theme_color_user
        
    def highlightBlock(self, text):
        # Expresión regular para capturar: [tag] opcional + usuario + mensaje
        pattern = QRegularExpression(r'(?:\[([^\]]+)\]\s)?([^:]+):(.+)')
        match = pattern.match(text)
        
        if match.hasMatch():
            tag = match.captured(1)  # Grupo 1: el tag sin corchetes
            user_start = match.capturedStart(2)  # Posición inicial del usuario
            user_length = match.capturedLength(2)
            
            # 1. Colorear el tag si existe
            if tag:
                tag_format = QTextCharFormat()
                tag_format.setForeground(self.theme_color_tag)
                # El tag real en el texto incluye los corchetes
                tag_pattern = QRegularExpression(r'\[[^\]]+\]')
                tag_match = tag_pattern.match(text)
                if tag_match.hasMatch():
                    self.setFormat(tag_match.capturedStart(), tag_match.capturedLength(), tag_format)
            
            # 2. Colorear solo el nombre de usuario
            user_format = QTextCharFormat()
            user_format.setForeground(self.theme_color_user)
            self.setFormat(user_start, user_length, user_format)

class JsonViewerDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chat Viewer")
        self.current_file_path = None
        self.last_file_mtime = None
        self.message_limit = 50  # Valor por defecto
        
        # Widget principal y layout
        self.mainWidget = QWidget()
        self.mainLayout = QVBoxLayout(self.mainWidget)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        
        # --- BARRA SUPERIOR CON CONTROLES ---
        self.controlBar = QWidget()
        self.controlLayout = QHBoxLayout(self.controlBar)
        self.controlLayout.setContentsMargins(0, 0, 0, 0)
        self.controlLayout.setSpacing(2)
        
        # Botón para cargar archivo
        self.loadButton = QPushButton("Load Chat JSON...")
        self.loadButton.clicked.connect(self.load_json_file)
        self.controlLayout.addWidget(self.loadButton)
        
        # Nuevo botón Toggle Send
        self.toggleSendButton = QPushButton("Toggle Send")
        self.toggleSendButton.setCheckable(True)
        self.toggleSendButton.clicked.connect(self.toggle_send_bar)
        self.controlLayout.addWidget(self.toggleSendButton)
        
        # Espaciador
        self.controlLayout.addStretch()
        
        # Etiqueta para el selector
        self.limitLabel = QLabel("Max:")
        self.controlLayout.addWidget(self.limitLabel)
        
        # Selector numérico (QSpinBox)
        self.limitSpinBox = QSpinBox()
        self.limitSpinBox.setRange(3, 100) 
        self.limitSpinBox.setSingleStep(1)   # Incrementos de 1
        self.limitSpinBox.setValue(self.message_limit)
        self.limitSpinBox.setFixedWidth(40)   # Ancho fijo
        self.limitSpinBox.valueChanged.connect(self.on_limit_changed)
        self.controlLayout.addWidget(self.limitSpinBox)
        
        self.mainLayout.addWidget(self.controlBar)
        
        # --- ÁREA DE TEXTO ---
        self.textDisplay = QTextEdit()
        self.textDisplay.setReadOnly(True)
        self.textDisplay.setPlaceholderText("Chat will appear here...")
        
        font = QFont("Arial", 10)
        font.setStyleHint(QFont.TypeWriter)
        self.textDisplay.setFont(font)
        
        # Colores del tema
        theme_color_tag = QColor(22, 163, 74)
        theme_color_user = QColor(0, 194, 209) 
        
        self.highlighter = ChatHighlighter(self.textDisplay.document(), 
                                           theme_color_tag, theme_color_user)
        
        self.mainLayout.addWidget(self.textDisplay)
        
        # --- BARRA INFERIOR DE ENVÍO (inicialmente oculta) ---
        self.sendBar = QWidget()
        self.sendLayout = QHBoxLayout(self.sendBar)
        self.sendLayout.setContentsMargins(0, 0, 0, 0)
        self.sendLayout.setSpacing(0)
        
        # Botón para abrir carpeta
        self.folderButton = QPushButton("📁")
        self.folderButton.setToolTip("Open output folder")
        self.folderButton.setFixedWidth(25)
        self.folderButton.clicked.connect(self.open_output_file)
        self.sendLayout.addWidget(self.folderButton)
        
        # Campo de texto para entrada
        self.inputField = QLineEdit()
        self.inputField.setPlaceholderText("Type message here...")
        self.inputField.textChanged.connect(self.update_send_button_state)
        self.sendLayout.addWidget(self.inputField)
        
        # Botón de envío
        self.sendButton = QPushButton("Send")
        self.sendButton.clicked.connect(self.send_message)
        self.sendButton.setEnabled(False)
        self.sendButton.setFixedWidth(50)
        self.sendLayout.addWidget(self.sendButton)
        
        self.mainLayout.addWidget(self.sendBar)
        self.sendBar.setVisible(False)  # Oculto por defecto
        
        self.setWidget(self.mainWidget)
        
        # Determinar ruta del archivo de salida
        self.output_file_name = "krita_chat_output.json"
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.output_file_path = os.path.join(script_dir, self.output_file_name)
        
        # Timer para auto-recarga
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_file_update)
        self.timer.start(3000)
        
        # Cargar configuración de sesión anterior
        self.load_session_settings()
    
    # def get_output_path(self):
    #     """Obtiene la ruta para el archivo de salida en la carpeta de documentos."""
    #     documents_path = os.path.expanduser("~/Documents")
    #     # Si no existe Documents, usar la carpeta home
    #     if not os.path.exists(documents_path):
    #         documents_path = os.path.expanduser("~")
    #     output_path = os.path.join(documents_path, self.output_file_name)
    #     return output_path

    def toggle_send_bar(self):
        """Alterna la visibilidad de la barra de envío."""
        is_visible = self.sendBar.isVisible()
        self.sendBar.setVisible(not is_visible)
        
    def update_send_button_state(self):
        """Habilita/deshabilita el botón Send basado en si hay texto."""
        has_text = len(self.inputField.text().strip()) > 0
        self.sendButton.setEnabled(has_text)
        
    def send_message(self):
        """Crea/sobrescribe el archivo JSON con el texto del input."""
        text = self.inputField.text().strip()
        if not text:
            return
            
        try:
            # Crear el objeto JSON
            output_data = {"output": text}
            
            # Escribir el archivo
            with open(self.output_file_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            # Limpiar el campo de entrada
            self.inputField.clear()
            
        except Exception as e:
            print(f"Error writing output file: {e}")
            
    def open_output_file(self):
        """Abre la carpeta contenedora del archivo de salida."""
        if not os.path.exists(self.output_file_path):
            return
            
        folder_path = os.path.dirname(self.output_file_path)
        
        # Intentar abrir la carpeta y seleccionar el archivo (multiplataforma)
        try:
            system = platform.system()
            
            if system == "Windows":
                # Windows: explorer /select, "ruta\archivo"
                cmd = f'explorer /select,"{self.output_file_path}"'
                subprocess.Popen(cmd, shell=True)
                
            elif system == "Darwin":
                # macOS: open -R "ruta/archivo"
                subprocess.Popen(["open", "-R", self.output_file_path])
                
            else:
                # Linux y otros: abrir la carpeta con xdg-open
                # (no se puede seleccionar el archivo específico)
                subprocess.Popen(["xdg-open", folder_path])
                
        except Exception as e:
            print(f"Error opening folder: {e}")


    def load_session_settings(self):
        """Carga el último archivo y límite de mensajes guardados."""
        settings = Krita.instance().readSetting("", "chat_viewer_settings", "")
        if settings:
            try:
                data = json.loads(settings)
                file_path = data.get("last_file", "")
                limit = data.get("message_limit", 50)
                
                # Aplicar límite
                self.message_limit = limit
                if hasattr(self, 'limitSpinBox'):
                    self.limitSpinBox.setValue(limit)
                
                # Cargar archivo si existe
                if file_path and os.path.exists(file_path):
                    self.current_file_path = file_path
                    self.load_json_from_path(file_path, update_session=False)
                    
            except:
                pass  # Si hay error, usar valores por defecto

    def save_session_settings(self):
        """Guarda la configuración actual para la próxima sesión."""
        if not hasattr(self, 'limitSpinBox'):
            return
            
        data = {
            "last_file": self.current_file_path or "",
            "message_limit": self.limitSpinBox.value()
        }
        Krita.instance().writeSetting("", "chat_viewer_settings", json.dumps(data))

    def on_limit_changed(self, value):
        """Se ejecuta cuando cambia el valor del spinbox."""
        self.message_limit = value
        self.save_session_settings()
        
        # Recargar el archivo actual si hay uno cargado
        if self.current_file_path and os.path.exists(self.current_file_path):
            self.load_json_from_path(self.current_file_path, update_session=False)

    def load_json_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self.mainWidget, "Select a Chat JSON File",
            "", "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            self.load_json_from_path(file_path)

    def load_json_from_path(self, file_path, update_session=True):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            formatted_text = self._format_chat_json(json_data)
            self.textDisplay.setText(formatted_text)
            
            self.current_file_path = file_path
            self.last_file_mtime = os.path.getmtime(file_path)
            
            if update_session:
                self.save_session_settings()
                
        except Exception as e:
            self.textDisplay.setText(f"ERROR: {str(e)}")

    def check_file_update(self):
        if not self.current_file_path or not os.path.exists(self.current_file_path):
            return
        
        try:
            current_mtime = os.path.getmtime(self.current_file_path)
            
            if self.last_file_mtime != current_mtime:
                self.last_file_mtime = current_mtime
                self.load_json_from_path(self.current_file_path, update_session=False)
        except:
            pass

    def _format_chat_json(self, data):
        formatted_lines = []
        
        if not isinstance(data, dict) or 'chat' not in data:
            return "ERROR: JSON debe contener clave 'chat'."
        
        chat_list = data['chat']
        if not isinstance(chat_list, list):
            return "ERROR: 'chat' debe ser una lista."
        
        # Tomar solo los últimos N mensajes según el límite
        start_index = max(0, len(chat_list) - self.message_limit)
        
        for i in range(start_index, len(chat_list)):
            entry = chat_list[i]
            
            if not isinstance(entry, list) or len(entry) != 3:
                continue
            
            role, user, message = entry
            
            if role:
                line = f"[{role}] {user}: {message}"
            else:
                line = f"{user}: {message}"
            
            formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)

    def canvasChanged(self, canvas):
        pass

# Registrar el docker
Krita.instance().addDockWidgetFactory(
    DockWidgetFactory("chatViewerDocker",
                      DockWidgetFactoryBase.DockRight,
                      JsonViewerDocker)
)