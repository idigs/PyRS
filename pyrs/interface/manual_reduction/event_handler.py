import os
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QApplication
from pyrs.interface.gui_helper import pop_message, parse_line_edit,  browse_file, browse_dir, parse_combo_box
from mantidqt.utils.asynchronous import BlockingAsyncTaskWithCallback
from pyrs.interface.manual_reduction.pyrs_api import ReductionController
from pyrs.dataobjects.constants import HidraConstants


class EventHandler(object):
    """Class to handle the event sent from UI widget
    """
    def __init__(self, parent):
        """Init

        Parameters
        ----------
        parent : qtpy.QtWidgets.QMainWindow
            GUI main Window
        """
        self.parent = parent
        self.ui = self.parent.ui

        # controller
        self._controller = ReductionController()

        return

    @property
    def controller(self):
        return self._controller

    def _retrieve_ipts_number(self):
        """Get IPTS number from

        Returns
        -------
        int or None
            IPTS number

        """
        run_number = parse_line_edit(self.ui.lineEdit_runNumbersList, int, False, default=None)
        if run_number is None:
            return None

        ipts_number = self._controller.get_ipts_from_run(run_number)

        return ipts_number

    def _set_sub_run_numbers(self, sub_runs):
        """Set sub run numbers to (1) Table and (2) Combo box

        Parameters
        ----------
        sub_runs

        Returns
        -------

        """
        # TODO - ASAP
        return

    # TEST: Use menu bar to load a file
    def browse_load_nexus(self):
        """Allow users to manually determine a NeXus file by browsing for a nexus file to convert to project file

        Returns
        -------

        """
        # Get default directory
        ipts_number = self._retrieve_ipts_number()
        if ipts_number is None:
            default_dir = self._controller.working_dir
        else:
            default_dir = self._controller.get_nexus_dir(ipts_number)

        # If specified information is not sufficient, browse
        nexus_file = browse_file(self.parent,
                                 caption='Select a NeXus file',
                                 default_dir=default_dir,
                                 file_filter='NeXus (*.nxs.h5)',
                                 file_list=False, save_file=False)

        # Return if it is cancelled
        if nexus_file is None:
            return

        # Load Nexus
        self._controller.load_nexus_file(nexus_file)

        # sub runs
        sub_runs = self._controller.get_sub_runs()

        # set sub runs to (1) Table and (2) Combo box
        self._set_sub_run_numbers(sub_runs)

    def browse_load_hidra(self):
        """Allow users to browse for a HiDRA project file

        Returns
        -------

        """
        # Get default directory
        ipts_number = self._retrieve_ipts_number()
        if ipts_number is None:
            default_dir = self._controller.working_dir
        else:
            default_dir = self._controller.get_hidra_project_dir(ipts_number, is_auto=True)

        # Browse
        hidra_file = browse_file(self.parent,
                                 caption='Select a HIDRA project file',
                                 default_dir=default_dir,
                                 file_filter='HiDRA project (*.h5)',
                                 file_list=False, save_file=False)

        # Load Nexus
        try:
            self._controller.load_project_file(hidra_file, load_counts=False, load_pattern=True)
        except RuntimeError as run_err:
            pop_message(self.parent, 'Loading {} failed.\nTry to load diffraction only!'.format(hidra_file),
                        detailed_message='{}'.format(run_err),
                        message_type='error')
            return

        # sub runs
        sub_runs = self._controller.get_sub_runs()

        # set sub runs to (1) Table and (2) Combo box
        self._set_sub_run_numbers(sub_runs)
        # Set to first sub run and plot
        self.ui.comboBox_sub_runs.setCurrentIndex(0)
        # Fill in self.ui.frame_subRunInfoTable
        meta_data_array = self._controller.get_sample_logs_values([HidraConstants.SUB_RUNS, HidraConstants.TWO_THETA])
        self.ui.rawDataTable.add_subruns_info(meta_data_array, clear_table=True)

    def browse_calibration_file(self):
        """

        Returns
        -------

        """
        calibration_file = browse_file(self, caption='Choose and set up the calibration file',
                                       default_dir=self._controller.get_default_calibration_dir(),
                                       file_filter='hdf5 (*hdf)', file_list=False, save_file=False)
        if calibration_file is None or calibration_file == '':
            # operation canceled
            return

        # set to the browser
        self.ui.lineEdit_calibratonFile.setText(calibration_file)

    def browse_idf(self):
        """

        Returns
        -------

        """
        idf_name = browse_file(self, 'Instrument definition file', os.getcwd(),
                               'Text (*.txt);;XML (*.xml)', False, False)
        if len(idf_name) == 0:
            return   # user cancels operation
        else:
            self.ui.lineEdit_idfName.setText(idf_name)
        # END-IF

    def browse_mask_file(self):
        """Browse masking file

        Returns
        -------

        """
        mask_file_name = browse_file(self.parent, 'Hidra Mask File', self._controller.get_default_mask_dir(),
                                     'Mantid Mask(*.xml)', False, False)
        self.ui.lineEdit_maskFile.setText(mask_file_name)
        return

    def browse_output_dir(self):
        """Browse output directory

        Returns
        -------

        """
        # TODO - good run number!
        run_number = 1060
        output_dir = browse_dir(self, caption='Output directory for reduced data',
                                default_dir=self._controller.get_default_output_dir(run_number))
        if output_dir != '':
            self.ui.lineEdit_outputDir.setText(output_dir)

    def slice_nexus(self):
        """Slice NeXus file by arbitrary log sample parameter

        Returns
        -------

        """
        # if self.ui.radioButton_chopByTime.isChecked():
        #     # set up slicers by time
        #     self.set_slicers_by_time()
        # elif self.ui.radioButton_chopByLogValue.isChecked():
        #     # set up slicers by sample log value
        #     self.set_slicers_by_sample_log_value()
        # else:
        #     # set from the table
        #     self.set_slicers_manually()
        # # END-IF-ELSE
        #
        # try:
        #     data_key = self._core.reduction_service.chop_data()
        # except RuntimeError as run_err:
        #     pop_message(self, message='Unable to slice data', detailed_message=str(run_err),
        #                            message_type='error')
        #     return
        #
        # try:
        #     self._core.reduction_service.reduced_chopped_data(data_key)
        # except RuntimeError as run_err:
        #     pop_message(self, message='Failed to reduce sliced data', detailed_message=str(run_err),
        #                            message_type='error')
        #     return
        #
        # # fill the run numbers to plot selection
        # self._setup_plot_selection(append_mode=False, item_list=self._core.reduction_service.get_chopped_names())
        #
        # # plot
        # self._plot_data()

        raise RuntimeError('Shall be combined with Async slice and reduce with sub runs')

    def plot_detector_counts(self):
        """

        Returns
        -------

        """
        # Get valid sub run
        sub_run = parse_combo_box(self.ui.comboBox_runs, int)
        if sub_run is None:
            return

        # Get counts
        try:
            counts_matrix = self._controller.get_detector_counts(sub_run, output_matrix=True)
        except RuntimeError as run_err:
            pop_message(self.parent, 'Unable to plot sub run {} counts on detector view'.format(sub_run),
                        str(run_err), message_type='error')
            return

        # Plot
        # set information
        det_2theta = self._controller.get_sample_log_value(HidraConstants.TWO_THETA, sub_run)
        info = 'sub-run: {}, 2theta = {}'.format(sub_run, det_2theta)

        # mask ID is not None
        # if mask_id is not None:
        #     # Get mask in array and do a AND operation to detector counts (array)
        #     mask_array = self._core.reduction_service.get_mask_array(self._curr_project_name, mask_id)
        #     detector_counts_array *= mask_array
        #     info += ', mask ID = {}'.format(mask_id)

        # Set information
        self.ui.lineEdit_detViewInfo.setText(info)

        # Plot:
        self.ui.graphicsView_detectorView.plot_detector_view(counts_matrix, (sub_run, None))

    def plot_powder_pattern(self):
        """

        Returns
        -------

        """
        # Get valid sub run
        sub_run = parse_combo_box(self.ui.comboBox_runs, int)
        print('[TEST-OUTPUT] sub run = {},  type = {}'.format(sub_run, type(sub_run)))
        if sub_run is None:
            return

        # Get diffraction pattern
        try:
            pattern = self._controller.get_powder_pattern(sub_run)
        except RuntimeError as run_err:
            pop_message(self.parent, 'Unable to plot sub run {} histogram/powder pattern'.format(sub_run),
                        str(run_err), message_type='error')
            return

        # Get detector 2theta of this sub run
        det_2theta = self._controller.get_sample_log_value(HidraConstants.TWO_THETA, sub_run)
        info = 'sub-run: {}, 2theta = {}'.format(sub_run, det_2theta)

        # Plot
        self.ui.graphicsView_1DPlot.plot_diffraction(pattern[0], pattern[1], '2theta', 'intensity',
                                                     line_label=info, keep_prev=False)

    def _set_sub_runs(self):
        """ set the sub runs to comboBox_sub_runs
        :return:
        """
        # sub_runs = self._core.reduction_manager.get_sub_runs(data_id)
        #
        # self.ui.comboBox_sub_runs.clear()
        # for sub_run in sorted(sub_runs):
        #     self.ui.comboBox_sub_runs.addItem('{:04}'.format(sub_run))
        #
        #
        # """
        # """
        # #
        sub_runs = self._controller.get_sub_runs()
        sub_runs.sort()

        # set sub runs: lock and release
        self._mutexPlotRuns = True
        # clear and set
        self.ui.comboBox_sub_runs.clear()
        for sub_run in sub_runs:
            self.ui.comboBox_sub_runs.addItem('{:04}'.format(sub_run))
        self._mutexPlotRuns = False

        return

    def _setup_plot_runs(self, append_mode, run_number_list):
        """ set the runs (or sliced runs to plot)
        :param append_mode:
        :param run_number_list:
        :return:
        """
        # checkdatatypes.check_list('Run numbers', run_number_list)

        # non-append mode
        self._plot_run_numbers_mutex = True
        if not append_mode:
            self.ui.comboBox_runs.clear()

        # add run numbers
        for run_number in run_number_list:
            self.ui.comboBox_runs.addItem('{}'.format(run_number))

        # open
        self._plot_run_numbers_mutex = False

        # if append-mode, then set to first run
        if append_mode:
            self.ui.comboBox_runs.setCurrentIndex(0)

        return

    def _setup_plot_selection(self, append_mode, item_list):
        """
        set up the combobox to select items to plot
        :param append_mode:
        :param item_list:
        :return:
        """
        # checkdatatypes.check_bool_variable('Flag for appending the items to current combo-box or from start',
        #                                    append_mode)
        # checkdatatypes.check_list('Combo-box item list', item_list)

        # turn on mutex lock
        self._plot_selection_mutex = True
        if append_mode is False:
            self.ui.comboBox_sampleLogNames.clear()
        for item in item_list:
            self.ui.comboBox_sampleLogNames.addItem(item)
        if append_mode is False:
            self.ui.comboBox_sampleLogNames.setCurrentIndex(0)
        self._plot_selection_mutex = False
        return

    def manual_reduce_run(self):
        """

        (simply) reduce a list of runs in same experiment in a batch

        Returns
        -------

        """
        # Get run number
        run_number = self.ui.spinBox_runNumber.text().strip()
        # No need: self.update_output_dir(run_number)

        # Files names: NeXus, (output) project, mask, calibration
        nexus_file = self._controller.get_nexus_file_by_run(run_number)
        project_file = str(self.ui.lineEdit_outputDirectory.text().strip())
        # mask file
        mask_file = str(self.ui.lineEdit_maskFile.text().strip())
        if mask_file == '':
            mask_file = None
        # calibration file
        calibration_file = str(self.ui.lineEdit_calibrationFile.text().strip())
        if calibration_file == '':
            calibration_file = None

        # Start task
        task = BlockingAsyncTaskWithCallback(self._controller.reduce_hidra_workflow,
                                             args=(nexus_file, project_file, self.ui.progressBar),
                                             kwargs={'mask': mask_file, 'calibration': calibration_file},
                                             blocking_cb=QApplication.processEvents)
        # TODO - catch RuntimeError! ...
        # FIXME - check output directory
        task.start()

        # Update table
        # TODO - Need to fill the table!
        for sub_run in list():
            self.ui.rawDataTable.update_reduction_state(sub_run, True)

        return

    def save_project(self):
        self._controller.save_project()

    def set_mask_file_widgets(self, state):
        """Set the default value of HB2B mask XML

        Parameters
        ----------
        state : Qt.State
            Qt state as unchecked or checked

        Returns
        -------
        None

        """

        if state != Qt.Unchecked:
            self.ui.lineEdit_maskFile.setText(self._controller.get_default_mask_dir() + 'HB2B_MASK_Latest.xml')
        self.ui.lineEdit_maskFile.setEnabled(state == Qt.Unchecked)
        self.ui.pushButton_browseMaskFile.setEnabled(state == Qt.Unchecked)

    def set_calibration_file_widgets(self, state):
        """Set the default value of HB2B geometry calibration file

        Parameters
        ----------
        state : Qt.State
            Qt state as unchecked or checked

        Returns
        -------

        """
        if state != Qt.Unchecked:
            self.ui.lineEdit_calibrationFile.setText(self._controller.get_default_calibration_dir() +
                                                     'HB2B_Latest.json')
        self.ui.lineEdit_calibrationFile.setEnabled(state == Qt.Unchecked)
        self.ui.pushButton_browseCalibrationFile.setEnabled(state == Qt.Unchecked)

    def set_output_dir_widgets(self, state):
        """Set the default value of directory for output files

        Parameters
        ----------
        state : Qt.State
            Qt state as unchecked or checked

        Returns
        -------
        None

        """
        if state != Qt.Unchecked:
            self.update_run_changed(self.ui.spinBox_runNumber.value())
        self.ui.lineEdit_outputDirectory.setEnabled(state == Qt.Unchecked)
        self.ui.pushButton_browseOutputDirectory.setEnabled(state == Qt.Unchecked)

    def update_run_changed(self, run_number):
        """Update widgets including output directory and etc due to change of run number

        Parameters
        ----------
        run_number : int
            run number

        Returns
        -------
        None

        """
        try:
            ipts = self._controller.get_ipts_from_run(run_number)
            if ipts is None:
                return
        except RuntimeError:
            # wrong run number
            return

        # new default
        project_dir = self._controller.get_default_output_dir(run_number)
        # set to line edit
        if project_dir is not None:
            self.ui.lineEdit_outputDirectory.setText(project_dir)
