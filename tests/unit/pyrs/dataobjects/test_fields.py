# Standard and third party libraries
from collections import namedtuple
import numpy as np
import pytest
# PyRs libraries
from pyrs.core.workspaces import HidraWorkspace
from pyrs.dataobjects.fields import ScalarFieldSample, StrainField
from pyrs.core.peak_profile_utility import get_parameter_dtype
from pyrs.peaks import PeakCollection  # type: ignore

SampleMock = namedtuple('SampleMock', 'name values errors x y z')


class TestScalarFieldSample:

    sample1 = SampleMock('lattice',
                         [1.000, 1.010, 1.020, 1.030, 1.040, 1.050, 1.060, 1.070, 1.080, 1.090],  # values
                         [0.000, 0.001, 0.002, 0.003, 0.004, 0.005, 0.006, 0.007, 0.008, 0.009],  # errors
                         [0.000, 1.000, 2.000, 3.000, 4.000, 5.000, 6.000, 7.000, 8.000, 9.000],  # x
                         [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],  # y
                         [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000]  # z
                         )

    # The last three points of sample1 overlaps with the first three points of sample1
    sample2 = SampleMock('lattice',
                         [1.071, 1.081, 1.091, 1.10, 1.11, 1.12, 1.13, 1.14, 1.15, 1.16],  # values
                         [0.008, 0.008, 0.008, 0.00, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06],  # errors
                         [7.009, 8.001, 9.005, 10.00, 11.00, 12.00, 13.00, 14.00, 15.00, 16.00],  # x
                         [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],  # y
                         [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000]  # z
                         )

    def test_init(self):
        ScalarFieldSample(*TestScalarFieldSample.sample1)
        ScalarFieldSample(*TestScalarFieldSample.sample2)
        sample_bad = list(TestScalarFieldSample.sample1)
        sample_bad[1] = [1.000, 1.010, 1.020, 1.030, 1.040, 1.050, 1.060, 1.070, 1.080]  # one less value
        with pytest.raises(AssertionError):
            ScalarFieldSample(*sample_bad)

    def test_len(self):
        assert len(ScalarFieldSample(*TestScalarFieldSample.sample1)) == 10

    def test_values(self):
        field = ScalarFieldSample(*TestScalarFieldSample.sample1)
        assert field.values == pytest.approx(TestScalarFieldSample.sample1.values)

    def test_errors(self):
        field = ScalarFieldSample(*TestScalarFieldSample.sample1)
        assert field.errors == pytest.approx(TestScalarFieldSample.sample1.errors)

    def test_point_list(self):
        field = ScalarFieldSample(*TestScalarFieldSample.sample1)
        field.point_list.vx == pytest.approx(TestScalarFieldSample.sample1.x)

    def test_coordinates(self):
        sample = list(TestScalarFieldSample.sample1)
        field = ScalarFieldSample(*sample)
        field.coordinates == pytest.approx(np.array(sample[2:]).transpose())

    def test_x(self):
        field = ScalarFieldSample(*TestScalarFieldSample.sample1)
        field.x == pytest.approx(TestScalarFieldSample.sample1.x)

    def test_y(self):
        field = ScalarFieldSample(*TestScalarFieldSample.sample1)
        field.y == pytest.approx(TestScalarFieldSample.sample1.y)

    def test_z(self):
        field = ScalarFieldSample(*TestScalarFieldSample.sample1)
        field.z == pytest.approx(TestScalarFieldSample.sample1.z)

    def test_extract(self):
        field = ScalarFieldSample(*TestScalarFieldSample.sample1)
        target_indexes = range(0, 10, 2)
        selection = field.extract(target_indexes)
        selection.name == 'lattice'
        selection.values == pytest.approx([1.000, 1.020, 1.040, 1.060, 1.080])
        selection.errors == pytest.approx([0.000, 0.002, 0.004, 0.006, 0.008])
        selection.x == pytest.approx([0.000, 2.000, 4.000, 6.000, 8.000])

    def test_aggregate(self):
        sample1 = ScalarFieldSample(*TestScalarFieldSample.sample1)
        sample2 = ScalarFieldSample(*TestScalarFieldSample.sample2)
        sample = sample1.aggregate(sample2)
        # index 9 of aggregate sample corresponds to the last point of sample1
        # index 10 of aggregate sample corresponds to the first point of sample2
        assert sample.values[9: 11] == pytest.approx([1.090, 1.071])
        assert sample.errors[9: 11] == pytest.approx([0.009, 0.008])
        assert sample.x[9: 11] == pytest.approx([9.000, 7.009])

    def test_intersection(self):
        sample1 = ScalarFieldSample(*TestScalarFieldSample.sample1)
        sample = sample1.intersection(ScalarFieldSample(*TestScalarFieldSample.sample2))
        assert len(sample) == 6  # three points from sample1 and three points from sample2
        assert sample.name == 'lattice'
        assert sample.values == pytest.approx([1.070, 1.080, 1.090, 1.071, 1.081, 1.091])
        assert sample.errors == pytest.approx([0.007, 0.008, 0.009, 0.008, 0.008, 0.008])
        assert sample.x == pytest.approx([7.000, 8.000, 9.000, 7.009, 8.001, 9.005])

    def test_fuse(self):
        sample1 = ScalarFieldSample(*TestScalarFieldSample.sample1)
        sample = sample1.fuse(ScalarFieldSample(*TestScalarFieldSample.sample2), criterion='min_error')
        assert len(sample) == 17  # discard the last point from sample1 and the first two points from sample2
        assert sample.name == 'lattice'
        # index 6 of aggregate sample corresponds to index 6 of sample1
        # index 11 of aggregate sample corresponds to index 3 of sample2
        assert sample.values[6: 11] == pytest.approx([1.060, 1.070, 1.080, 1.091, 1.10])
        assert sample.errors[6: 11] == pytest.approx([0.006, 0.007, 0.008, 0.008, 0.0])
        assert sample.x[6: 11] == pytest.approx([6.000, 7.000, 8.000, 9.005, 10.00])

    def test_export(self):
        # Create a scalar field
        xyz = [list(range(0, 10)), list(range(10, 20)), list(range(20, 30))]
        xyz = np.vstack(np.meshgrid(*xyz)).reshape(3, -1)  # shape = (3, 1000)
        signal, errors = np.arange(0, 1000, 1, dtype=float), np.zeros(1000, dtype=float)
        sample = ScalarFieldSample('strain', signal, errors, *xyz)

        # Test export to MDHistoWorkspace
        workspace = sample.export(form='MDHistoWorkspace', name='strain1', units='mm')
        assert workspace.name() == 'strain1'

        # Test export to CSV file
        with pytest.raises(NotImplementedError):
            sample.export(form='CSV', file='/tmp/csv.txt')


def test_create_strain_field():
    # 2 points in each direction
    subruns = np.arange(1, 9, dtype=int)

    # create the test peak collection - d-refernce is 1 to make checks easier
    # uncertainties are all zero
    peaks_array = np.zeros(subruns.size, dtype=get_parameter_dtype('gaussian', 'Linear'))
    peaks_array['PeakCentre'][:] = 180.  # position of two-theta in degrees
    peaks_error = np.zeros(subruns.size, dtype=get_parameter_dtype('gaussian', 'Linear'))
    peak_collection = PeakCollection('dummy', 'gaussian', 'linear', wavelength=2.,
                                     d_reference=1., d_reference_error=0.)
    peak_collection.set_peak_fitting_values(subruns, peaks_array, parameter_errors=peaks_error,
                                            fit_costs=np.zeros(subruns.size, dtype=float))

    # create the test workspace - only sample logs are needed
    workspace = HidraWorkspace()
    workspace.set_sub_runs(subruns)
    # arbitray points in space
    workspace.set_sample_log('vx', subruns, np.arange(1, 9, dtype=int))
    workspace.set_sample_log('vy', subruns, np.arange(11, 19, dtype=int))
    workspace.set_sample_log('vz', subruns, np.arange(21, 29, dtype=int))

    # call the function
    strain = StrainField(workspace, peak_collection)

    # test the result
    assert strain
    assert len(strain) == subruns.size
    np.testing.assert_almost_equal(strain.values, 0.)
    np.testing.assert_equal(strain.errors, np.zeros(subruns.size, dtype=float))


if __name__ == '__main__':
    pytest.main()