# PyRS data workflow

The PyRS software is a combined data reduction/analysis of event data measured at the High Intensity Diffractometer for Residual stress Analysis (HIDRA) at the Hight Flux Isotope Reactor at Oak Ridge National Laboratory. PyRS includes modules for analysis and visualization of residual stresses, as well as functionality to export angular dependent diffraction data for further analysis (e.g., pole figure inversion using MTEX and Rietveld analysis using MAUD).

#### Definitions
* Nexus file: data file with as measured neutron and sample log event data
* Project file: hdf5 file used to store reduced neutron data (sample logs and 1-D intensity vs scattering angle data) and data analysis results (single peak fitting via PeakCollections)
* Reduction: process of converting event data into histogrammed data
  *  Default process is to compress event data based using the incrementing sub_run log
  *  Event neutron data is first compressed in time (2D data) then further compressed by scattering angle (1D)
* Data analysis: 
  * PyRS using single peak fitting (Gaussian, Pseudo Voigt, or Lorentzian peak shape functions) to precisely determine the position and intensity of a diffraction peak.
* Post-processing:
  * Analyzed diffraction data are "post-processed" by combing multiple strain directions to determine residual stresses or exported for texture analysis using 3rd party software.

## Data workflow
* User(s) setup their experimental plan to measure the needed mapping points in a sample (table scan, cuboid tool, ...)
* (reduction): Event data (logs and neutron data) are time filtered to aggregate sample logs (Mantid filtering) and neutron data (direct hdf5 read) into the respective sublog (as defined by the sub_run log)
  * Optional inputs
    *  MASK: defines pixels on the detector to exclude
       *  (default mask "HB2B_Mask_12-18-19.xml" excludes data near the edge of the detector)
    *  VANADIUM_FILE: Vanadium file used to normalize intensity variations on the detector
    *  CALIBRATION_FILE: json file with inputs to correctly position the detector in (x, y, z) space
    *  INSTRUMENT_FILE: override default instrument definition 
       *  number of pixels, size of each pixel, (x, y, z) position of detector center
    *  ETA_MASK_ANGLE: Defines if reduction will subsample each sublong based on the out-of-plane (about y) angle
       *  used to study angular dependent phenomena (i.e., crystallographic texture)
 
* (data analysis): Reduced diffraction data are analyzed by single peak fitting (Gaussian, Pseudo Voigt, or Lorentzian peak shape functions) to precisely determine the position and intensity of a diffraction peak. Data analysis can run as part of the data autoreduction or as a secondary step using the PyRS GUI.
  * autoreduction:
    * Users can define peak fitting setup (peak name and 2theta bounds) as part of the autoreduction workflow
  * PyRS GUI
    * A user can either setup the peak fitting engine by graphically defining bounds for each diffraction peak in the field of view or load the setup exported from a prior analysis.
* (post-processing): Reduced data are post-processed using different approaches based on the needs of the experiment
  * (Residual stress analysis): A user will define 2 or 3 project files representing different scattering directions in a sample using the Residual Stress Analysis GUI. The UI includes modules for visualizing residual stresses.
  * (Texture): Users can export PeakCollections for texture analysis using MTEX or export 1-D diffraction data for Rietveld texture analysis using MAUD.
