import sys
import os
from PyQt5.QtWidgets import QApplication, QDialog
from ui.main_window import MainWindow
from ui.appraiser_company_info import AppraiserCompanyInfo
from ui.appraiser_man import AppraiserManInfo

from logic.paths import get_settings_path


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()

    
 
   
    # Главное окно
    main_window = MainWindow()
    

    # Вызов диалогов при первом запуске (если нет файла настроек)
    # if not os.path.exists(get_settings_path()):
    #     company_dialog = AppraiserCompanyInfo(main_window)
    #     if company_dialog.exec_() != QDialog.Accepted:
    #         sys.exit()

    #     man_dialog = AppraiserManInfo(main_window)
    #     if man_dialog.exec_() != QDialog.Accepted:
    #         sys.exit()

    # Отображение главного окна и
    main_window.show()
    sys.exit(app.exec_())


