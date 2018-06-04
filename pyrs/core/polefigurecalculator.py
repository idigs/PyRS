# This module is to calculate Pole Figure
import mantid_fit_peak
import peakfitengine
import rshelper
import numpy


def rotation_matrix_x(angle, is_degree=False):
    """
    calculate rotation matrix X
    :param angle:
    :param is_degree: flag show that the angle is in degree but not radius
    :return:
    """
    if is_degree:
        angle = angle / 180. * numpy.pi

    rotation_matrix = numpy.matrix([[1., 0, 0],
                                    [0, numpy.cos(angle), -numpy.sin(angle)],
                                    [0, numpy.sin(angle), numpy.cos(angle)]], dtype='float')

    return rotation_matrix


def rotation_matrix_y(angle, is_degree=False):
    """
    calculate rotation matrix Y
    :param angle:
    :param is_degree: flag show that the angle is in degree but not radius
    :return:
    """
    if is_degree:
        angle = angle / 180. * numpy.pi

    rotation_matrix = numpy.matrix([[numpy.cos(angle), 0, numpy.sin(angle)],
                                    [0, 1., 0.],
                                    [-numpy.sin(angle), 0., numpy.cos(angle)]], dtype='float')

    return rotation_matrix


def rotation_matrix_z(angle, is_degree=False):
    """
    calculate rotation matrix Z
    :param angle:
    :param is_degree: flag show that the angle is in degree but not radius
    :return:
    """
    if is_degree:
        angle = angle / 180. * numpy.pi

    rotation_matrix = numpy.matrix([[numpy.cos(angle), -numpy.sin(angle), 0.],
                                    [numpy.sin(angle), numpy.cos(angle), 0.],
                                    [0., 0., 1.]], dtype='float')

    return rotation_matrix


class PoleFigureCalculator(object):
    """
    A container for a workflow to calculate Pole Figure
    """
    def __init__(self):
        """
        initialization
        """
        # initialize class instances
        self._data_set = None

        self._cal_successful = False

        return

    def calculate_pole_figure(self, peak_intensity_dict):
        """

        :return:
        """
        rshelper.check_dict('(class variable) data set', self._data_set)

        pole_figure_list = list()

        for index, scan_index in enumerate(self._data_set.keys()):
            # check fitting result
            if scan_index in peak_intensity_dict:
                intensity_i = peak_intensity_dict[scan_index]
            else:
                continue

            # rotate Q from instrument coordinate to sample coordinate
            two_theta_i = self._data_set[scan_index]['2theta']
            omega_i = self._data_set[scan_index]['omega']
            chi_i = self._data_set[scan_index]['chi']
            phi_i = self._data_set[scan_index]['phi']
            alpha, beta = self.rotate_project_q(two_theta_i, omega_i, chi_i, phi_i)

            pole_figure_list.append([alpha, beta, intensity_i])
        # END-FOR

        # convert
        self._pole_figure = numpy.array(pole_figure_list)


    def execute(self):
        """
        calculate pole figure
        :return:
        """
        # fit peaks
        # choose peak fit engine
        if use_mantid:
            fit_engine = mantid_fit_peak.MantidPeakFitEngine(self._data_set)
        else:
            fit_engine = peakfitengine.ScipyPeakFitEngine(self._data_set)

        # fit peaks
        fit_engine.fit_peaks(peak_function_name=profile_type, background_function_name=background_type,
                             fit_range=peak_range)

        # check result
        fit_engine.mask_bad_fit(max_chi2=self._maxChi2)

        # get fitted peak parameters from engine
        self._peak_intensity_dict = fit_engine.get_intensities()

        # calculate pole figure
        self._cal_successful = self.calculate_pole_figure(peak_intensity_dict)

        return

    def export_pole_figure(self, file_name):
        """
        exported the calculated pole figure
        :param file_name:
        :return:
        """
        rshelper.check_file_name(file_name, check_exist=False, check_writable=True)

        # TODO - Implement
        raise NotImplementedError('ASAP')

        return

    def get_pole_figure(self):
        """
        return Pole figure in a numpy 2D array
        :return:
        """

        return self._pole_figure

    def rotate_project_q(self, two_theta, omega, chi, phi):
        """
        Rotate Q from instrument coordinate to sample coordinate defined by goniometer angles
        and project rotation Q to (001) and (100)
        :param two_theta:
        :param omega:
        :param chi:
        :param phi:
        :return: 2-tuple as the projection (alpha, beta)
        """
        # rotate Q
        vec_q = numpy.array([0., 1., 0.])
        vec_q = rotation_matrix_z(-(180. - two_theta)*0.5, is_degree=True) * vec_q
        vec_q_prime = rotation_matrix_z(-omega, True) * rotation_matrix_x(chi, True) * rotation_matrix_z(phi, True) * \
                      vec_q

        # project
        import math
        alpha = math.acos(numpy.dot(vec_q_prime, numpy.array([0., 0., 1.])))
        beta = math.acos(numpy.dot(vec_q_prime, numpy.array([1., 0., 0.])))

        return alpha, beta
