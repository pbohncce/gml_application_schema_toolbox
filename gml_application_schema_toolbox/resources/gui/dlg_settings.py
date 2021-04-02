#! python3  # noqa: E265

"""
    Plugin settings dialog.
"""

# standard
import logging
from pathlib import Path

# PyQGIS
from qgis.core import QgsSettings
from qgis.gui import QgsOptionsPageWidget, QgsOptionsWidgetFactory
from qgis.PyQt import uic
from qgis.PyQt.QtCore import pyqtSlot
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QFileDialog, QVBoxLayout, QWidget

# project
from gml_application_schema_toolbox.__about__ import (
    DIR_PLUGIN_ROOT,
    __title__,
    __version__,
)
from gml_application_schema_toolbox.toolbelt import PlgLogger, PlgOptionsManager

# ############################################################################
# ########## Globals ###############
# ##################################

logger = logging.getLogger(__name__)
FORM_CLASS, _ = uic.loadUiType(
    Path(__file__).parent / "{}.ui".format(Path(__file__).stem)
)


# ############################################################################
# ########## Classes ###############
# ##################################


class SettingsDialog(QWidget, FORM_CLASS):
    """Form dialog to allow user change plugin settings.

    Options codes:

        - Import method:
            1 = "GMLAS"
            2 = "XML"
        - Database type:
            1 = "SQLite"
            2 = "PostgreSQL"
        - Access mode:
            1 = "Create"
            2 = "Update"
            2 = "Append"
            2 = "Overwrite"

    :param QWidget: [description]
    :type QWidget: [type]
    :param FORM_CLASS: [description]
    :type FORM_CLASS: [type]
    """

    DEFAULT_PREFERENCES: dict = {
        # download
        "default_maxfeatures": 100,
        "default_gmlas_config": str(DIR_PLUGIN_ROOT / "conf" / "gmlasconf.xml"),
        "default_wfs2_service": None,
        "wfs2_services": [],
        # import/export
        "impex_access_mode": None,
        "impex_db_type": "SQLite",
        "impex_import_method": "gmlas",
        "impex_language": "en",
        # usage
        # global
        "debug_mode": False,
    }

    def __init__(self, parent=None):
        """Constructor."""
        super(SettingsDialog, self).__init__(parent)
        self.setupUi(self)
        self.log = PlgLogger().log

        # set radio button ids to ensure consistency through launches
        self.opt_group_access.addButton(self.createRadioButton, 1)
        self.opt_group_access.addButton(self.updateRadioButton, 2)
        self.opt_group_access.addButton(self.appendRadioButton, 3)
        self.opt_group_access.addButton(self.overwriteRadioButton, 4)

        self.opt_group_db_type.addButton(self.pgsqlRadioButton, 1)
        self.opt_group_db_type.addButton(self.sqliteRadioButton, 2)

        self.opt_group_import_method.addButton(self.gmlasRadioButton, 1)
        self.opt_group_import_method.addButton(self.xmlRadioButton, 2)

        # load previously saved settings
        self.load_settings()

    def closeEvent(self, event):
        """Map on plugin close.

        :param event: [description]
        :type event: [type]
        """
        self.closingPlugin.emit()
        event.accept()

    def load_settings(self):
        """Load options from QgsSettings into UI form."""
        # open settings group
        settings = QgsSettings()
        settings.beginGroup(__title__)

        # download
        self.featureLimitBox.setValue(
            settings.value(key="network_max_features", defaultValue=100, type=int)
        )
        self.httpUserAgentEdit.setText(
            settings.value(
                key="network_http_user_agent",
                defaultValue=f"{__title__}/{__version__}",
                type=str,
            )
        )

        # import - export
        self.languageLineEdit.setText(
            settings.value(key="impex_language", defaultValue="en", type=str)
        )

        self.opt_group_access.button(
            abs(settings.value(key="impex_access_mode", defaultValue=1, type=int))
        ).setChecked(True)
        self.opt_group_db_type.button(
            abs(settings.value(key="impex_db_type", defaultValue=1, type=int))
        ).setChecked(True)
        self.opt_group_import_method.button(
            abs(settings.value(key="impex_import_method", defaultValue=1, type=int))
        ).setChecked(True)

        # global
        self.opt_debug.setChecked(
            settings.value("debug_mode", defaultValue=0, type=bool)
        )

        # end
        settings.endGroup()

    def save_settings(self):
        """Save options from UI form into QSettings."""
        # open settings group
        settings = QgsSettings()
        settings.beginGroup(__title__)

        # download
        settings.setValue("network_max_features", self.featureLimitBox.value())
        settings.setValue("network_http_user_agent", self.httpUserAgentEdit.text())

        # import - export
        settings.setValue("impex_language", self.languageLineEdit.text())
        settings.setValue("impex_access_mode", abs(self.opt_group_access.checkedId()))
        settings.setValue("impex_db_type", abs(self.opt_group_db_type.checkedId()))
        settings.setValue(
            "impex_import_method", abs(self.opt_group_import_method.checkedId())
        )

        # global
        settings.setValue("debug_mode", self.opt_debug.isChecked())

        # invisible
        settings.setValue("version", __version__)

        # end
        settings.endGroup()

        if __debug__:
            self.log(
                message="DEBUG - Settings successfully saved.",
                log_level=4,
            )

    @pyqtSlot()
    def on_gmlasConfigButton_clicked(self):
        path, suffix_filter = QFileDialog.getOpenFileName(
            self,
            self.tr("Open GMLAS config file"),
            self.gmlasConfigLineEdit.text(),
            self.tr("XML Files (*.xml)"),
        )
        if path:
            self.gmlasConfigLineEdit.setText(path)

    # -- Buttons box signals -----------------------------------------------------------
    def accept(self):
        self.save_settings()
        super(SettingsDialog, self).accept()

    def reject(self):
        super(SettingsDialog, self).reject()


class PlgOptionsFactory(QgsOptionsWidgetFactory):
    def __init__(self):
        super().__init__()

    def icon(self):
        return QIcon(str(DIR_PLUGIN_ROOT / "resources/images/mActionAddGMLLayer.svg"))

    def createWidget(self, parent):
        return ConfigOptionsPage(parent)

    def title(self):
        return "GMLAS Toolbox"


class ConfigOptionsPage(QgsOptionsPageWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.dlg_settings = SettingsDialog(self)
        self.dlg_settings.buttonBox.hide()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.dlg_settings.setLayout(layout)
        self.setLayout(layout)
        self.setObjectName("mOptionsPage{}".format(__title__))

    def apply(self):
        """Called to permanently apply the settings shown in the options page (e.g. \
        save them to QgsSettings objects). This is usually called when the options \
        dialog is accepted."""
        self.dlg_settings.save_settings()
