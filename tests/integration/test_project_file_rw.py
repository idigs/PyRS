from pyrs.core import workspaces
from pyrs.projectfile import HidraProjectFile  # type: ignore
from pyrs.core.instrument_geometry import HidraSetup  # type: ignore
import os
import pytest


def test_rw_raw(test_data_dir):
    """Test read a project to workspace and write in the scope of raw data

    Returns
    -------

    """
    raw_project_name = os.path.join(test_data_dir, 'HZB_Raw_Project.h5')

    # Read to workspace
    source_project = HidraProjectFile(raw_project_name, 'r')

    # To the workspace
    source_workspace = workspaces.HidraWorkspace('Source HZB')
    source_workspace.load_hidra_project(source_project, load_raw_counts=True,
                                        load_reduced_diffraction=False)

    # Export
    target_project = HidraProjectFile('HZB_HiDra_Test.h5', 'w')
    # Experiment data
    source_workspace.save_experimental_data(target_project, sub_runs=range(1, 41))

    # Instrument
    detector_setup = source_workspace.get_instrument_setup()
    instrument_setup = HidraSetup(detector_setup=detector_setup)
    target_project.write_instrument_geometry(instrument_setup)

    # Save
    target_project.save(True)

    return


if __name__ == '__main__':
    pytest.main([__file__])
