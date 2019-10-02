# This is the virtual base class as the fitting frame
import numpy
import math
from pyrs.core import workspaces
from pyrs.utilities import rs_project_file
from pyrs.utilities import checkdatatypes

NATIVE_PEAK_PARAMETERS = {'Gaussian': ['Height', 'PeakCentre', 'Sigma', 'A0', 'A1'],
                          'PseudoVoigt': ['Mixing', 'Intensity', 'PeakCentre', 'FWHM', 'A0', 'A1'],
                          'Voigt': ['LorentzAmp', 'LorentzPos', 'LorentzFWHM', 'GaussianFWHM',
                                    'A0', 'A1']}
EFFECTIVE_PEAK_PARAMETERS = ['Center', 'Height', 'FWHM', 'A0', 'A1']


class PeakFitEngine(object):
    """
    Virtual peak fit engine
    """
    def __init__(self, workspace, mask_name):
        """
        initialization
        :param workspace: HidraWorksapce containing the diffraction data
        :param mask_name: name of mask ID (or main/None) for reduced diffraction data
        """
        # check
        checkdatatypes.check_type('Diffraction workspace', workspace, workspaces.HidraWorkspace)

        # for scipy: keep the numpy array will be good enough
        self._hd_workspace = workspace  # hd == HiDra
        self._mask_name = mask_name

        # for fitted result
        self._peak_center_vec = None  # 2D vector for observed center of mass and highest data point
        self._peak_center_d_vec = None  # 1D vector for calculated center in d-spacing

        # Peak function
        self._peak_function_name = None

        return

    def calculate_peak_position_d(self, wave_length):
        """ Calculate peak positions in d-spacing
        Output: result will be saved to self._peak_center_d_vec
        Parameters
        ----------
        wave_length: float or numpy.ndarray(dtype=float)
            uniform wave length or wave length for each sub run
        Returns
        -------
        None
        """
        # TODO/FIXME - #80+ - Must have a better way than try and guess
        try:
            r = self.get_fitted_params(param_name_list=['PeakCentre'], including_error=True)
        except KeyError:
            r = self.get_fitted_params(param_name_list=['centre'], including_error=True)
        sub_run_vec = r[0]
        params_vec = r[2]

        # Other parameters
        num_sub_runs = sub_run_vec.shape[0]

        # Process wave length
        if isinstance(wave_length, numpy.ndarray):
            assert wave_length.shape[0] == num_sub_runs
            various_wl = True
            wl = 0
        else:
            various_wl = False
            wl = wave_length

        # init vector for peak center in d-spacing with error
        self._peak_center_d_vec = numpy.ndarray((params_vec.shape[1], 2), params_vec.dtype)

        for sb_index in range(num_sub_runs):
            # convert to d-spacing: both fitted value and fitting error
            # set wave length if various to sub runs
            if various_wl:
                wl = wave_length[sb_index]

            # calculate peak position and propagating fitting error
            for sub_index in range(2):
                peak_i_2theta_j = params_vec[0][sb_index][0]
                try:
                    peak_i_d_j = wl * 0.5 / math.sin(peak_i_2theta_j * 0.5 * math.pi / 180.)
                except ZeroDivisionError as zero_err:
                    print ('Peak(i) @ {}'.format(peak_i_2theta_j))
                    raise zero_err
                self._peak_center_d_vec[sb_index][0] = peak_i_d_j
        # END-FOR

        return

    def export_fit_result(self, file_name, peak_tag):
        """
        export fit result for all the peaks
        :return: a dictionary of fitted peak information
        """
        hidra_file = rs_project_file.HydraProjectFile(file_name, rs_project_file.HydraProjectFileMode.READWRITE)

        param_names = self.get_peak_param_names(self._peak_function_name, is_effective=False)
        print ('[DB...BAT] Parameter names: {}'.format(param_names))

        # Get parameter values
        sub_run_vec, chi2_vec, param_names, param_matrix = self.get_fitted_params(param_names, including_error=True)

        hidra_file.set_peak_fit_result(peak_tag, self._peak_function_name, param_names, sub_run_vec, chi2_vec,
                                       param_matrix)

        return

    def fit_peaks(self, sub_run_range, peak_function_name, background_function_name, peak_center, peak_range,
                  cal_center_d):
        """ Fit peaks with option to calculate peak center in d-spacing
        :param sub_run_range: range of sub runs (including both end) to refine
        :param peak_function_name:
        :param background_function_name:
        :param peak_center:
        :param peak_range:
        :param cal_center_d:
        :return:
        """
        raise NotImplementedError('Virtual base class member method fit_peaks()')

    @staticmethod
    def _fit_peaks_checks(sub_run_range, peak_function_name, background_function_name, peak_center, peak_range,
                          cal_center_d):
        return

    def get_calculated_peak(self, scan_log_index):
        """
        get the calculated peak's value
        :return:
        """
        raise NotImplementedError('Virtual base class member method get_calculated_peak()')

    def get_fit_cost(self, max_chi2):
        raise NotImplementedError('This is virtual')

    def _get_fitted_parameters_value(self, spectrum_index_vec, parameter_name_list, parameter_value_matrix):
        raise NotImplementedError('This is virtual')

    def get_fitted_params(self, param_name_list, including_error, max_chi2=1.E20):
        """ Get specified parameters' fitted value and optionally error with optionally filtered value
        :param param_name_list:
        :param including_error:
        :param max_chi2: Default is including all.
        :return: 3-tuple: (1) (n, ) vector for sub run number (2) costs
                          (3) (p, n, 1) or (p, n, 2) vector for parameter values
                            and
                            optionally fitting error: p = number of parameters , n = number of sub runs
        """
        # Deal with multiple default
        if max_chi2 is None:
            max_chi2 = 1.E20

        # Check inputs
        checkdatatypes.check_list('Function parameters', param_name_list)
        checkdatatypes.check_bool_variable('Flag to output fitting error', including_error)
        checkdatatypes.check_float_variable('Maximum cost chi^2', max_chi2, (1, None))

        # Get number of sub-runs meets the requirement
        spec_index_vec, fit_cost_vec = self.get_fit_cost(max_chi2)

        # init parameters
        num_sub_runs = fit_cost_vec.shape[0]
        num_params = len(param_name_list)
        if including_error:
            num_items = 2
        else:
            num_items = 1
        param_value_array = numpy.zeros(shape=(num_params, num_sub_runs, num_items), dtype='float')

        # Set values of parameters
        self._get_fitted_parameters_value(spec_index_vec, param_name_list, param_value_array)

        # Convert
        sub_runs_vec = self._hd_workspace.get_sub_runs_from_spectrum(spec_index_vec)

        return sub_runs_vec, fit_cost_vec, param_value_array

    def get_fitted_effective_params(self, effective_params_list, including_error, max_chi2=1.E20):
        """
        Get the effective peak parameters including
        peak position, peak height, peak intensity, FWHM and Mixing

        Parameters
        ----------
        effective_params_list: list of string
            effective parameter names
        including_error: boolean
            returned will include fitting error
        max_chi2: float
            filtering with chi2

        Returns
        -------
        ndarray, ndarray, ndarray
            (n,) for sub run numbers
            (n,) for fitting cost
            (p, n, 1) or (p, n, 2) for fitted parameters value,
            p = number of parameters , n = number of sub runs, 2 containing fitting error
        """
        # Create native -> effective parameters converter
        from pyrs.core import peak_profile_utility
        print('[DB...BAT] Current peak function: {}'.format(self._peak_function_name))
        converter = peak_profile_utility.get_effective_parameters_converter(self._peak_function_name)

        # Get raw peak parameters
        param_name_list = converter.get_native_peak_param_names()
        sub_run_array, fit_cost_array, param_value_array = self.get_fitted_params(param_name_list,
                                                                                  including_error,
                                                                                  max_chi2)

        # Convert
        effective_param_value_array = converter.calculate_effective_parameters(effective_params_list, param_value_array)

        return sub_run_array, fit_cost_array, effective_param_value_array

    def get_number_scans(self):
        """ Get number of scans in input data to fit
        :return:
        """
        raise NotImplementedError('Virtual base class member method get_number_scans()')

    def get_hidra_workspace(self):
        """
        Get the HidraWorkspace instance associated with this peak fit engine
        :return:
        """
        assert self._hd_workspace is not None, 'No HidraWorkspace has been set up.'

        return self._hd_workspace

    def get_peak_param_names(self, peak_function, is_effective):
        """ Get the peak parameter names
        :param peak_function: None for default/current peak function
        :param is_effective:
        :return:
        """
        # Default
        if peak_function is None:
            peak_function = self._peak_function_name

        if is_effective:
            # Effective parameters
            param_names = EFFECTIVE_PEAK_PARAMETERS[:]
            if peak_function == 'PseudoVoigt':
                param_names.append('Mixing')

        else:
            # Native parameters
            try:
                param_names = NATIVE_PEAK_PARAMETERS[peak_function][:]
            except KeyError as key_err:
                raise RuntimeError('Peak type {} not supported.  The supported peak functions are {}.  FYI: {}'
                                   ''.format(peak_function, NATIVE_PEAK_PARAMETERS.keys(), key_err))

        return param_names

    def set_wavelength(self, wavelengths):
        """

        :param wavelengths:
        :return:
        """
        # TODO - #80 NOW - Implement
        self._wavelength_dict = wavelengths

        return

    def write_result(self):
        """
        write (append) the peak fitting result to input HDF5 for further data reduction such as
        calculating stress/strain.
        The file format shall be documented as a standard
        :return:
        """
        # TODO - 20180727 - Implement!

# In [17]: log97entry.create_group('peak_fit')
# Out[17]: <HDF5 group "/Diffraction Data/Log 97/peak_fit" (0 members)>
#
# In [18]: peak_fit_97 = log
# %logoff     %logon      %logstart   %logstate   %logstop    log97entry  log98entry
#
# In [18]: peak_fit_97 = log97entry['peak_fit']
#
# In [19]: peak_fit_97['type'
#    ....: ] = 'Gaussian'
#
# In [20]: peak_fit_97['Height'] = 45.0
#
# In [21]: peak_fit_97['Chi2'] = 56.3
#
# In [22]: rwfile.close()


def gaussian(x, a, sigma, x0):
    """
    Gaussian with linear background
    :param x:
    :param a:
    :param sigma:
    :param x0:
    :return:
    """
    return a * numpy.exp(-((x - x0)/sigma)**2)


def loranzian(x, a, sigma, x0):
    """
    Lorentian
    :param x:
    :param a:
    :param sigma:
    :param x0:
    :return:
    """
    return


def quadratic_background(x, b0, b1, b2, b3):
    """
    up to 3rd order
    :param x:
    :param b0:
    :param b1:
    :param b2:
    :param b3:
    :return:
    """
    return b0 + b1*x + b2*x**2 + b3*x**3


def fit_peak(peak_func, vec_x, obs_vec_y, p0, p_range):
    """

    :param peak_func:
    :param vec_x:
    :param obs_vec_y:
    :param p0:
    :param p_range: example  # bounds=([a, b, c, x0], [a, b, c, x0])
    :return:
    """
    def calculate_chi2(covariance_matrix):
        """

        :param covariance_matrix:
        :return:
        """
        # TODO
        return 1.

    # check input
    checkdatatypes.check_numpy_arrays('Vec X and observed vec Y', [vec_x, obs_vec_y], 1, check_same_shape=True)

    # fit
    fit_results = scipy.optimize.curve_fit(peak_func, vec_x, obs_vec_y, p0=p0, bounds=p_range)

    fit_params = fit_results[0]
    fit_covmatrix = fit_results[1]
    cost = calculate_chi2(fit_covmatrix)

    return cost, fit_params, fit_covmatrix
