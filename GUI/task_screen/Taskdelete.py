from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton)


class TaskDeleteDialog(QDialog):
    """
    完全にカスタマイズされた確認ダイアログ。
    QMessageBoxの代わりに使う。
    """
    def __init__(self, title, text, informative_text="", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(350)

        # --- スタイルの設定 ---
        self.setStyleSheet("""
            QDialog {
                background-color: #282828;
                border: 1px solid #555;
                font-size: 14px;
            }
            QLabel#mainTextLabel {
                color: #ffffff;
                font-weight: bold; /* メインテキストを太字に */
            }
            QLabel#infoTextLabel {
                color: #bbbbbb; /* 詳細テキストを少し薄い色に */
            }
            QPushButton { /* ボタンの共通スタイル */
                border-radius: 4px;
                padding: 8px 12px;
                min-width: 90px;
                font-size: 13px;
            }
            QPushButton#okButton {
                background-color: #555; /* "はい"ボタンのスタイル */
                color: #ffffff;
            }
            QPushButton#okButton:hover {
                background-color: #e91e63;
            }
            QPushButton#cancelButton {
                background-color: #555; /* "キャンセル"ボタンのスタイル */
                color: #ffffff;
            }
            QPushButton#cancelButton:hover {
                background-color: #666;
            }
        """)

        # --- レイアウトとウィジェットの配置 ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # 1. メインテキスト
        self.main_text_label = QLabel(text)
        self.main_text_label.setObjectName("mainTextLabel")
        self.main_text_label.setWordWrap(True)
        main_layout.addWidget(self.main_text_label)

        # 2. 詳細テキスト (空でなければ追加)
        if informative_text:
            self.informative_text_label = QLabel(informative_text)
            self.informative_text_label.setObjectName("infoTextLabel")
            self.informative_text_label.setWordWrap(True)
            main_layout.addWidget(self.informative_text_label)

        # 3. ボタンのレイアウト
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.ok_button = QPushButton("はい")
        self.ok_button.setObjectName("okButton")
        self.ok_button.clicked.connect(self.accept)

        self.cancel_button = QPushButton("キャンセル")
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)

        main_layout.addLayout(button_layout)

        # 最初はキャンセルボタンにフォーカスを当てる
        self.cancel_button.setFocus()
