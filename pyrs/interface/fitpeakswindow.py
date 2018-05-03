try:
    from PyQt5.QtWidgets import QMainWindow, QFileDialog
except ImportError:
    from PyQt4.QtGui import QMainWindow, QFileDialog
import ui.ui_peakfitwindow
import os
import gui_helper
import numpy


class FitPeaksWindow(QMainWindow):
    """
    GUI window for user to fit peaks
    """
    def __init__(self, parent):
        """
        initialization
        :param parent:
        """
        super(FitPeaksWindow, self).__init__(parent)

        # class variables
        self._core = None

        # set up UI
        self.ui = ui.ui_peakfitwindow.Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.graphicsView_fitResult.set_subplots(1, 1)
        self.ui.graphicsView_fitSetup.set_subplots(1, 1)

        # set up handling
        self.ui.pushButton_loadHDF.clicked.connect(self.do_load_scans)
        self.ui.pushButton_browseHDF.clicked.connect(self.do_browse_hdf)
        self.ui.pushButton_plotPeaks.clicked.connect(self.do_plot_diff_data)

        self.ui.actionQuit.triggered.connect(self.do_quit)

        # TODO
        self.ui.comboBox_xaxisNames.currentIndexChanged.connect(self.do_plot_meta_data)
        self.ui.comboBox_yaxisNames.currentIndexChanged.connect(self.do_plot_meta_data)

        # mutexes
        self._sample_log_names_mutex = False

        return

    def _check_core(self):
        """
        check whether PyRs.Core has been set to this window
        :return:
        """
        if self._core is None:
            raise RuntimeError('Not set up yet!')

    def _get_default_hdf(self):
        """
        use IPTS and Exp to determine
        :return:
        """
        try:
            ipts_number = gui_helper.parse_integer(self.ui.lineEdit_iptsNumber)
            exp_number = gui_helper.parse_integer(self.ui.lineEdit_expNumber)
        except RuntimeError as run_err:
            gui_helper.pop_message(self, 'Unable to parse IPTS or Exp due to {0}'.format(run_err))
            return None

        # TODO - NEED TO FIND OUT HOW TO DEFINE hdf FROM IPTS and EXP

        return None

    def do_browse_hdf(self):
        """
        browse HDF file
        :return:
        """
        self._check_core()

        default_dir = self._get_default_hdf()
        if default_dir is None:
            default_dir = self._core.working_dir

        file_filter = 'HDF(*.h5);;All Files(*.*)'
        open_value = QFileDialog.getOpenFileName(self, 'HB2B Raw HDF File', default_dir, file_filter)
        print open_value

        if isinstance(open_value, tuple):
            # PyQt5
            hdf_name = str(open_value[0])
        else:
            hdf_name = str(open_value)

        if len(hdf_name) == 0:
            # use cancel
            return

        if os.path.exists(hdf_name):
            self.ui.lineEdit_expFileName.setText(hdf_name)
        else:
            # pass
            raise RuntimeError('File {0} does not exist.'.format(hdf_name))

        return

    def do_load_scans(self):
        """
        load scan's reduced files
        :return:
        """
        self._check_core()

        # get file
        rs_file_name = str(self.ui.lineEdit_expFileName.text())

        # load file
        data_key, message = self._core.load_rs_raw(rs_file_name)

        # edit information
        self.ui.label_loadedFileInfo.setText(message)

        # get the range of log indexes
        log_range = self._core.data_center.get_scan_range(data_key)
        self.ui.label_logIndexMin.setText(str(log_range[0]))
        self.ui.label_logIndexMax.setText(str(log_range[-1]))

        # get the sample logs
        sample_log_names = self._core.data_center.get_sample_logs_list(data_key, can_plot=True)

        self._sample_log_names_mutex = True
        self.ui.comboBox_xaxisNames.clear()
        self.ui.comboBox_yaxisNames.clear()
        self.ui.comboBox_xaxisNames.addItem('Log Index')
        for sample_log in sample_log_names:
            self.ui.comboBox_xaxisNames.addItem(sample_log)
            self.ui.comboBox_yaxisNames.addItem(sample_log)
        self._sample_log_names_mutex = False

        return

    def do_plot_diff_data(self):
        """
        plot diffraction data
        :return:
        """
        # gather the information
        scan_log_index_list = gui_helper.parse_integers(str(self.ui.lineEdit_scanNUmbers.text()))
        if len(scan_log_index_list) == 0:
            gui_helper.pop_message(self, 'There is not scan-log index input', 'error')

        # possibly clean the previous
        keep_prev = self.ui.checkBox_keepPrevPlot.isChecked()
        if keep_prev is False:
            self.ui.graphicsView_fitSetup.clear_all_lines(include_right=False)

        # get data and plot
        err_msg = ''
        for scan_log_index in scan_log_index_list:
            try:
                diff_data_set = self._core.get_diff_data(data_key=None, scan_log_index=scan_log_index)
                self.ui.graphicsView_fitSetup.plot_diff_data(diff_data_set)
            except RuntimeError as run_err:
                err_msg += '{0}\n'.format(run_err)
        # END-FOR

        return

    def do_plot_meta_data(self):
        """
        plot the meta/fit result data on the right side GUI
        :return:
        """
        if self._sample_log_names_mutex:
            return

        if self.ui.checkBox_keepPrevPlotRight.isChecked() is False:
            self.ui.graphicsView_fitResult.clear_all_lines(include_right=False)

        # get the sample log/meta data name
        x_axis_name = str(self.ui.comboBox_xaxisNames.currentText())
        y_axis_name = str(self.ui.comboBox_yaxisNames.currentText())

        vec_x = self.get_meta_sample_data(x_axis_name)
        vec_y = self.get_meta_sample_data(y_axis_name)

        self.ui.graphicsView_fitResult.plot_scatter(vec_x, vec_y, x_axis_name, y_axis_name)

        return

    def do_quit(self):
        """
        close the window and quit
        :return:
        """
        self.close()

        return

    def get_meta_sample_data(self, name):
        """
        get meta data to plot.
        the meta data can contain sample log data and fitted peak parameters
        :param name:
        :return:
        """
        # get data key
        data_key = self._core.current_data_reference_id
        if data_key is None:
            gui_helper.pop_message(self, 'No data loaded', 'error')
            return

        if name == 'Log Index':
            value_vector = numpy.array(self._core.data_center.get_scan_range(data_key))
        elif self._core.data_center.has_sample_log(data_key, name):
            value_vector = self._core.data_center.get_sample_log_values(data_key, name)
        else:
            # this is for fitted data parameters
            raise NotImplementedError('ASAP')

        return value_vector

    def setup_window(self, pyrs_core):
        """

        :param pyrs_core:
        :return:
        """
        # check
        # blabla

        self._core = pyrs_core

        return
