"""
Object to contain peak parameters (names and values) of a collection of peaks for sub runs
"""
import numpy as np
from pyrs.utilities import checkdatatypes
from pyrs.core.peak_profile_utility import get_effective_parameters_converter, PeakShape, BackgroundFunction

__all__ = ['PeakCollection']


class PeakCollection(object):
    """
    Class for a collection of peaks
    """
    def __init__(self, peak_tag, peak_profile, background_type):
        """Initialization

        Parameters
        ----------
        peak_tag : str
            tag for the peak such as 'Si111'
        peak_profile : str
            Peak profile
        background_type : str
            Background type

        """
        # Init variables from input
        self._tag = peak_tag

        # Init other parameters
        self._peak_profile = PeakShape.getShape(peak_profile)
        self._background_type = BackgroundFunction.getFunction(background_type)

        # sub run numbers: 1D array
        self._sub_run_array = None
        # parameter values: numpy structured array
        self._params_value_array = None
        # parameter fitting error: numpy structured array
        self._params_error_array = None
        # fitting cost (chi2): numpy 1D array
        self._fit_cost_array = None

    def apply_fitting_cost_criteria(self, max_chi2):
        sub_run_index_tuple = np.where((np.isinf(self._fit_cost_array)) | (np.isnan(self._fit_cost_array)) |
                                       (self._fit_cost_array > max_chi2))[0]
        for i in sub_run_index_tuple:
            # values and errors are different length arrays
            for j in range(len(self._params_value_array[i])):
                self._params_value_array[i][j] = np.nan

            for j in range(len(self._params_error_array[i])):
                self._params_error_array[i][j] = np.nan

    def apply_intensity_criteria(self, min_peak_intensity):

        # TODO - NEXT
        peak_intensities = self._params_value_array
        assert min_peak_intensity is not None
        assert peak_intensities is not None

        return

    def apply_peak_position_criteria(self, expected_peak_center, max_allowed_peak_shift):

        # TODO - NEXT
        peak_centers = self._params_value_array
        expected_peak_center + max_allowed_peak_shift
        expected_peak_center - max_allowed_peak_shift
        assert peak_centers is not None

        return

    @property
    def peak_tag(self):
        """Peak tag

        Returns
        -------
        str
            Peak tag

        """
        return self._tag

    @property
    def peak_profile(self):
        """Get peak profile name

        Returns
        -------
        str
            peak profile name such as Gaussian

        """
        return str(self._peak_profile)

    @property
    def background_type(self):
        """Get background type

        Returns
        -------
        str
            background type of the profile such as Linear

        """
        return str(self._background_type)

    @property
    def sub_runs(self):
        return self._sub_run_array

    @property
    def parameters_values(self):
        return self._params_value_array

    @property
    def parameters_errors(self):
        return self._params_error_array

    @property
    def fitting_costs(self):
        return self._fit_cost_array

    def set_peak_fitting_values(self, sub_runs, parameter_values, parameter_errors, fit_costs):
        """Set peak fitting values

        Parameters
        ----------
        sub_runs : numpy.array
            1D numpy array for sub run numbers
        parameter_values : numpy.ndarray
            numpy structured array for peak/background parameter values
        parameter_errors : numpy.ndarray
            numpy structured array for peak/background parameter fitted error
        fit_costs : numpy.ndarray
            numpy 1D array for

        Returns
        -------

        """
        self._sub_run_array = np.copy(sub_runs)
        self._params_value_array = np.copy(parameter_values)
        self._params_error_array = np.copy(parameter_errors)
        self._fit_cost_array = np.copy(fit_costs)

        return

    def get_parameters_values(self, param_name_list, max_chi2=None):
        """Get specified parameters' fitted value and optionally error with optionally filtered value

        The outputs will NOT be numpy structured array but ordered with parameters given in the list

        Parameters
        ----------
        param_name_list : List
            list of parameter names
            If None, use the native parameters
        max_chi2 : None or float
            Default is including all
        Returns
        -------
        (numpy.ndarray, numpy.ndarray, numpy.ndarray, numpy.ndarray)
            4-tuple: (1) (n, ) vector for sub run number
                     (2) costs
                     (3) (p, n) array for parameter values
                     (4) (p, n) array for parameter fitting error
            p = number of parameters , n = number of sub runs

        """
        # Check inputs
        checkdatatypes.check_list('Function parameters', param_name_list)
        if max_chi2 is not None:
            checkdatatypes.check_float_variable('Maximum cost chi^2', max_chi2, (1, None))

        num_params = len(param_name_list)

        # Create unfiltered output values
        chi2_vec = np.copy(self._fit_cost_array)
        sub_runs_vec = np.copy(self._sub_run_array)

        # array size: (P, N)  P = number of parameters, N = number of sub runs
        param_value_array = np.zeros(shape=(num_params, sub_runs_vec.shape[0]), dtype='float')
        param_error_array = np.zeros(shape=(num_params, sub_runs_vec.shape[0]), dtype='float')
        # Set value (unfiltered)

        # import pprint
        # pprint.pprint("--> param_name_list: {}".format(param_name_list))
        # pprint.pprint("*****************")
        # pprint.pprint("self._params_value_array: {}".format(self._params_value_array))

        # THIS BELOW CAN NOT WORK !!!!!

        for iparam, param_name in enumerate(param_name_list):
            try:
                param_value_array[iparam] = self._params_value_array[param_name]
                param_error_array[iparam] = self._params_error_array[param_name]
            except ValueError as key_err:
                raise ValueError('{}\n{}'.format(key_err, param_value_array))
        # END-FOR

        # Set filter and create chi2 vector and sub run nun vector
        if max_chi2 is not None and max_chi2 < np.max(self._fit_cost_array):
            # There are runs to be filtered out
            good_fit_indexes = np.where(chi2_vec < max_chi2)
            # Filter
            chi2_vec = chi2_vec[good_fit_indexes]
            sub_runs_vec = sub_runs_vec[good_fit_indexes]
            # parameter values: [P, N] -> [N, P] for filtering -> [P, N']
            param_value_array = param_value_array.transpose()[good_fit_indexes].transpose()
            param_error_array = param_error_array.transpose()[good_fit_indexes].transpose()
        # END-IF

        return sub_runs_vec, chi2_vec, param_value_array, param_error_array

    def get_sub_run_params(self, sub_run_number):
        """Retrieve the native peak parameters' value of a particular sub run

        Parameters
        ----------
        sub_run_number : integer
            sub run number

        Returns
        -------
        dict
            key: parameter name, value: parameter value

        """
        # Locate the index of the sub run
        sub_run_index = np.abs(self._sub_run_array - sub_run_number).argmin()

        # Create the workspace
        param_value_dict = dict()
        for param_name in self._params_value_array.dtype.names:
            param_value_dict[param_name] = self._params_value_array[param_name][sub_run_index]

        return param_value_dict

    def get_effective_parameters_values(self, max_chi2=None):
        """
        Get the effective peak parameters including
        peak position, peak height, peak intensity, FWHM and Mixing

        Parameters
        ----------
        max_chi2: float or None
            filtering with chi2

        Returns
        -------
        5-tuple:
                 (0) List as effective peak and background function parameters
                 (1) (n, ) vector for sub run number
                 (2) costs
                 (3) (p, n) array for parameter values
                 (4) (p, n) array for parameter fitting error
            p = number of parameters , n = number of sub runs
        """
        # Create native -> effective parameters converter
        converter = get_effective_parameters_converter(self._peak_profile)

        # Get raw peak parameters
        param_name_list = converter.get_native_peak_param_names()
        param_name_list.extend(converter.get_native_background_names())
        sub_run_array, fit_cost_array, param_value_array, param_error_array = \
            self.get_parameters_values(param_name_list, max_chi2)

        # Convert
        eff_params_list, eff_param_value_array, eff_param_error_array =\
            converter.calculate_effective_parameters(param_name_list, param_value_array, param_error_array)

        return eff_params_list, sub_run_array, fit_cost_array, eff_param_value_array, eff_param_error_array