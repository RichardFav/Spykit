# module import
import os
import time
import mmap
import pathlib
import functools
import numpy as np
from pathlib import Path
from copy import deepcopy

# bombcell packages
import BombCellPkg
import bombcell as bc

# spike pipeline imports
import spykit.common.common_func as cf
import spykit.common.common_widget as cw
from spykit.info.utils import InfoWidgetPara
from spykit.threads.utils import ThreadWorker

# pyqt6 module import
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QWidget, QMessageBox, QGroupBox,
                             QTabWidget, QFormLayout, QSizePolicy, QTreeWidget, QFrame, QLineEdit,
                             QCheckBox, QComboBox)
from PyQt6.QtCore import (Qt, QTimer, pyqtSignal)
from PyQt6.QtGui import (QFont)

# ----------------------------------------------------------------------------------------------------------------------

"""
    BombCellPara:  class for managing the BombCell parameters
"""

# combobox lists
p_method = ['Llobet', 'Hill'];
p_fit = ['Exponential', 'Linear'];

# parameter description tooltip strings
p_tooltip = {
    # ---------------------------------------------------------------------------
    # Quality Parameters
    # ---------------------------------------------------------------------------

    # plotting parameters
    'plotDetails': None,
    'plotGlobal': None,
    'verbose': None,
    'reextractRaw': 'Re-extracts the raw waveforms.',

    # saving parameters
    'saveAsTSV': None,
    'unitType_for_phy': None,
    'saveMatFileForGUI': None,

    # duplicate spikes parameters
    'removeDuplicateSpikes': 'Removes duplicate spikes.',
    'saveSpikes_withoutDuplicates': 'Saves spike data without duplicate spikes.',
    'recomputeDuplicateSpikes': 'Recomputes the duplicate spikes.',
    'duplicateSpikeWindow_s': 'Duration window within which duplicate spikes are detected.',

    # amplitude/raw waveform parameters
    'detrendWaveform': ('If this is selected, each raw extracted spike is detrended (the best '
                        'straight-fit line is removed from the spike) using the MATLAB built-in '
                        'function "detrend".'),
    'nRawSpikesToExtract': 'Number of raw spikes to be extracted for each unit.',
    'saveMultipleRaw': ('Save the raw spikes (as defined by the "Raw Spike Extraction Count"). '
                        'This is required if you want to run unit matching over multiple experiments.'),
    'decompressData': 'Whether to decompress the .cbin ephys data.',
    'spikeWidth': 'Number of samples comprising the raw spike waveform.',
    'extractRaw': 'Determines whether raw waveforms are to be extracted.',
    'probeType': ('Only applicable if using SpikeGLX and the meta data file does not contain the probe '
                  'type. Note that "1" denotes 1.0 (3Bs) and "2" for 2.0 (single or 4-shanks).'),
    'computeSpatialDecay': 'Flag indicating whether to computer spatial decay.',

    # signal to noise ratio parameters
    'waveformBaselineNoiseWindow': ('Number of samples preceeding a waveform that '
                                    'is used to calculate the mean baseline.'),

    # refractory period parameters
    'tauR_valuesMin': ('Minimum refractory period time in seconds. If this value is different from '
                       '"Max Refactory Period", then Bombcell will estimate the refactory time period '
                       'taking possible values Min/Max Refactory Time Periods in steps of '
                       '"Refactory Period Time-Steps".'),
    'tauR_valuesStep': ('Refractory period time steps in seconds. This is only considered if Min/Max '
                        'Refactory Time Periods are not equal.'),
    'tauR_valuesMax': 'Refractory time period in seconds.',
    'tauC': 'Censored time period in seconds. This is to prevent duplicate spike detection.',

    # percentage spikes missing parameters
    'hillOrLlobetMethod': 'Method for detecting refactory period violations.',
    'computeTimeChunks':('Computes the refractory period violation fraction and the missing spike '
                         'percentage for different time chunks.'),
    'deltaTimeChunk': 'Time chunk duration in seconds.',

    # presence ratio
    'presenceRatioBinSize': 'Presence ratio bin size in seconds.',

    # drift estimate
    'driftBinSize': 'Drift estimation bin size in seconds.',
    'computeDrift': ('Whether to compute the drift for each unit. Note that this is a critically slow '
                     'step that takes around 2 seconds per unit.'),

    # waveform parameters
    'waveformBaselineWindowStart': 'Waveform baseline window start index.',
    'waveformBaselineWindowStop': 'Waveform baseline window finish index.',
    'minThreshDetectPeaksTroughs': ('This value is multiplied by the max value in a units waveform '
                                    'to give the minimum prominence to detect peaks using the MATLAB '
                                    'built-in function "findpeaks".'),
    'normalizeSpDecay': ('Whether to normalise spatial decay points relative to the maximum. This '
                         'makes the spatrial decay slope calculations more invariant to the '
                         'spike-sorting algorithm used.'),
    'spDecayLinFit': ('If selected, a linear fit is used to estimate spatial decay (otherwise, an '
                      'exponential fit is used).'),

    # recording parameters
    'ephys_sample_rate': 'Recording sample rate in Hertz.',
    'nChannels': 'Number of recorded channels (including any sync channels) recorded in the raw data file.',
    'nSyncChannels': 'Number of synchronisation channels.',
    'ephysMetaFile': 'Path of the EPhys meta data file.',
    'gain_to_uV': 'Gain to micro-Volt scale factor.',
    'rawFile': 'Path of the raw data file.',

    # distance metric parameters
    'computeDistanceMetrics': 'Whether to compute distance metrics. Note that this can be time consuming.',
    'nChannelsIsoDist': 'Number of nearby channels to use in the distance metric calculations.',

    # ---------------------------------------------------------------------------
    # Classification Parameters
    # ---------------------------------------------------------------------------

    # unit classification parameters
    'splitGoodAndMua_NonSomatic': 'Whether non-somatic unit are further separated into multi-unit and good units.',

    # noise waveform parameters
    'maxNPeaks': 'Maximum number of peaks.',
    'maxNTroughs': 'Maximum number of troughs.',
    'somatic': 'Whether to only keep somatic units (ie, non-somatic units are rejected).',
    'minWvDuration': 'Minimum waveform duration in micro-seconds.',
    'maxWvDuration': 'Maximum waveform duration in micro-seconds.',
    'minSpatialDecaySlope': 'Minimum linear spatial decay slope.',
    'minSpatialDecaySlopeExp': 'Minimum exponential spatial decay slope.',
    'maxSpatialDecaySlopeExp': 'Maximum exponential spatial decay slope.',
    'maxWvBaselineFraction': ('The maximum absolute waveform baseline value as a '
                              'fraction of the waveform''s absolute peak value.'),
    'maxScndPeakToTroughRatio_noise': 'Maximum second peak to trough ratio threshold.',

    # non-somatic waveform parameters
    'maxPeak1ToPeak2Ratio_nonSomatic': ('For units that have an initial peak before the trough, the '
                                        'main peak to trough ratio must be larger than this to be '
                                        'considered a non-somatic unit.'),
    'maxMainPeakToTroughRatio_nonSomatic':'Maximum main peak to trough ratio threshold.',
    'minWidthFirstPeak_nonSomatic': 'Minimum main peak width duration in samples.',
    'minWidthMainTrough_nonSomatic': 'Minimum main trough width duration in samples.',
    'minTroughToPeak2Ratio_nonSomatic': 'Minimum trough to main peak ratio.',

    # distance metric parameters
    'isoDmin': 'Minimum isolation distance value.',
    'lratioMax': 'Maximum l-ratio value.',
    'ssMin': 'Minimum silhouette score.',

    # other classification parameters
    'minAmplitude': 'Minimum waveform amplitude in uV.',
    'maxRPVviolations':'Maximum refactory period violation fraction.',
    'maxPercSpikesMissing': 'Maximum missing spike percentage.',
    'minNumSpikes': 'Minimum number of spikes per unit.',
    'maxDrift': 'Maximum drift distance in microns.',
    'minPresenceRatio': 'Minimum presence proportion.',
    'minSNR': 'Minimum signal-to-noise ratio.',
}

class BombCellPara(object):
    # pyqtsignal functions
    setup_para_groups = pyqtSignal()

    def __init__(self, main_obj, expt_dir):
        super(BombCellPara, self).__init__()

        # input arguments
        self.main_obj = main_obj
        self.expt_dir = expt_dir

        # main class fields
        self.p_map = {}
        self.p_grp = {}
        self.p_fld = {}
        self.p_info = {}
        self.p_update = {}

        # retrieves the default parameter dictionary
        self.sort_dir = self.main_obj.session_obj.get_sorting_folder_paths()[0, 0]

        # creates the threadworker object
        self.t_worker_para = ThreadWorker(self, self.init_bombcell_para, None)
        self.t_worker_para.work_finished.connect(self.init_bombcell_para_complete)
        self.t_worker_para.start()

    def init_bombcell_para(self, _):

        # runs the experiment folder diagnosis
        err_str = self.check_expt_dir()
        if err_str is None:
            # if feasible, initialise all parameter fields
            self.init_para_fields()

        return err_str

    def init_bombcell_para_complete(self, err_str):

        if err_str is not None:
            # expt is infeasible
            self.is_ok = False
            cf.show_error(err_str, 'BombCell Error')
            self.setup_para_groups.emit()

        else:
            # otherwise, create the parameter groups
            self.setup_para_groups.emit()

    def check_expt_dir(self):

        # field retrieval
        s_props = self.main_obj.session_obj.session.get_session_props()

        # initialisations
        self.n_run = self.main_obj.session_obj.session.get_run_count()
        self.n_shank = self.main_obj.session_obj.get_shank_count()
        self.is_concat = self.main_obj.session_obj.is_concat_run()
        self.is_per_shank = self.main_obj.session_obj.is_per_shank()
        self.sub_name = os.path.split(s_props['subject_path'])[1]
        self.ses_name = s_props["session_name"]

        # ---------------------------------------------------------------------------
        # Base Data Directory Check
        # ---------------------------------------------------------------------------

        # retrieves the information from experiment directory
        sdir_path = [x for x in Path(self.expt_dir).rglob('*') if x.is_dir()]
        sdir_name = [x.parts[-1] for x in sdir_path]

        # ensures the correct folders are present (exit with error otherwise)
        if ('rawdata' not in sdir_name) or ('derivatives' not in sdir_name):
            return 'Specified folder does not contain "derivative" or "rawdata" sub-folders.'

        # ---------------------------------------------------------------------------
        # Raw/Metafile Check
        # ---------------------------------------------------------------------------

        # memory allocation
        self.raw_file = np.empty(self.n_run, dtype=object)
        self.meta_file = np.empty(self.n_run, dtype=object)

        for i_run in range(self.n_run):
            # determines if the binary/meta data files exist somewhere in the expt folder
            r_file = [x for x in Path(self.expt_dir).rglob(f'**\\run-00{i_run + 1}*.ap.bin')]
            m_file = [x for x in Path(self.expt_dir).rglob(f'**\\run-00{i_run + 1}*.ap.meta')]

            if bool(len(r_file)) and bool(len(m_file)):
                # if successful, set the file names
                self.raw_file[i_run] = r_file[0]
                self.meta_file[i_run] = m_file[0]

            else:
                # otherwise, set the error message
                err_str = 'The following raw experimental data files are missing\n\n'

                # case is missing run binary file
                if not bool(len(r_file)):
                    err_str += ' * raw binary (*.ap.bin) file\n'

                # case is missing run binary file
                if not bool(len(m_file)):
                    err_str += ' * metadata (*.ap.meta) file\n'

                return err_str

        # ---------------------------------------------------------------------------
        # Sorter Folder Check
        # ---------------------------------------------------------------------------

        # initialisations
        n_run_s = 1 + (self.n_run - 1) * int(not self.is_concat)
        n_shank_s = 1 + (self.n_shank - 1) * int(self.is_per_shank)
        self.k_sort = np.empty((n_run_s, n_shank_s), dtype=object)
        self.s_dir = np.empty((n_run_s, n_shank_s), dtype=object)

        # base sorting directory path
        s_dir_base = os.path.join(self.expt_dir, "derivatives", self.sub_name, self.ses_name, "ephys")

        for i_run in range(n_run_s):
            # sets the run-dependent path string
            if self.is_concat:
                # case is concatenated run
                r_dir0 = os.path.join('concat_run', 'sorting')
            else:
                # case is individual run
                r_dir0 = os.path.join(f'run-00{i_run + 1}*', 'sorting')

            # sets the search directory for each shank
            for i_shank in range(n_shank_s):
                # appends the shank index to the path string
                if self.is_per_shank:
                    r_dir = os.path.join(deepcopy(r_dir0), f'shank_{i_shank}', 'sorter_output')
                else:
                    r_dir = os.path.join(deepcopy(r_dir0), 'sorter_output')

                # determines if the sorter output directory exists
                s_info_d = [x for x in Path(self.expt_dir).rglob(r_dir)]
                if bool(len(s_info_d)):
                    # case is the directory exists
                    self.k_sort[i_run, i_shank] = s_info_d[0]
                    self.s_dir[i_run, i_shank] = os.path.join(s_info_d[0], 'BombCell');

                else:
                    # otherwise, set the output string and exit
                    return 'The spike sorting folders are missing for this experiment'

        # flag that there was no error
        return None

    def init_para_fields(self):

        # parameter field initialisation
        self.bc_para = bc.get_default_parameters(self.sort_dir)
        self.bc_para0 = deepcopy(self.bc_para)

        # ---------------------------------------------------------------------------
        # Quality Parameters
        # ---------------------------------------------------------------------------

        # plotting parameters
        self.add_para_field('Quality', 'Plotting', 'plotDetails', 0)
        self.add_para_field('Quality', 'Plotting', 'plotGlobal', 1)
        self.add_para_field('Quality', 'Plotting', 'verbose', 1)
        self.add_para_field('Quality', 'Plotting', 'reextractRaw', 1, 'Re-extract Raw Waveforms?')

        # saving parameters
        self.add_para_field('Quality', 'Saving', 'saveAsTSV', 1)
        self.add_para_field('Quality', 'Saving', 'unitType_for_phy', 1)
        self.add_para_field('Quality', 'Saving', 'saveMatFileForGUI', 1)

        # duplicate spikes parameters
        self.add_para_field('Quality', 'Spike Duplication', 'removeDuplicateSpikes', 0,
                            'Remove Duplicate Spikes?')
        self.add_para_field('Quality', 'Spike Duplication', 'saveSpikes_withoutDuplicates', 1,
                            'Save Spikes Without Duplicates?')
        self.add_para_field('Quality', 'Spike Duplication', 'recomputeDuplicateSpikes', 0,
                            'Recompute Duplicate Spikes?')
        self.add_para_field('Quality', 'Spike Duplication', 'duplicateSpikeWindow_s', 1e-5,
                            'Duplicate Spike Window (s)', 'EditF', p_lim=[1e-6, 1e-4])

        # amplitude/raw waveform parameters
        self.add_para_field('Quality', 'Amplitude/Raw Waveforms', 'detrendWaveform', 1,
                            'Detrend Waveforms?')
        self.add_para_field('Quality', 'Amplitude/Raw Waveforms', 'nRawSpikesToExtract', 100,
                            'Raw Spike Extraction Count', 'Edit', p_lim=[1, 10000])
        self.add_para_field('Quality', 'Amplitude/Raw Waveforms', 'saveMultipleRaw', 0,
                            'Save Extracted Raw Spikes?')
        self.add_para_field('Quality', 'Amplitude/Raw Waveforms', 'decompressData', 0,
                            'Decompress Data?')
        self.add_para_field('Quality', 'Amplitude/Raw Waveforms', 'spikeWidth', 61,
                            'Spike Width (Samples)', 'Edit', p_lim=[1, 1001])
        self.add_para_field('Quality', 'Amplitude/Raw Waveforms', 'extractRaw', 1,
                            'Extract Raw Waveforms?')
        self.add_para_field('Quality', 'Amplitude/Raw Waveforms', 'probeType', 1,
                            'Probe Type', 'Edit')
        self.add_para_field('Quality', 'Amplitude/Raw Waveforms', 'computeSpatialDecay', 1,
                            'Compute Spatial Decay?')

        # signal to noise ratio parameters
        self.add_para_field('Quality', 'SNR', 'waveformBaselineNoiseWindow', 10,
                            'Baseline Noise Sample Size', 'Edit', p_lim=[1, 100])

        # refractory period parameters
        self.add_para_field('Quality', 'Refactory Period', 'tauR_valuesMin', 2e-3,
                            'Min Refactory Time Period (s)', 'EditF', p_lim=[1e-5, 1e-2])
        self.add_para_field('Quality', 'Refactory Period', 'tauR_valuesStep', 5e-4,
                            'Refactory Period Time-Steps (s)', 'EditF', p_lim=[1e-6, 1e-2])
        self.add_para_field('Quality', 'Refactory Period', 'tauR_valuesMax', 2e-3,
                            'Max Refactory Time Period (s)', 'EditF', p_lim=[1e-5, 1e-2])
        self.add_para_field('Quality', 'Refactory Period', 'tauC', 1e-4,
                            'Censored Time Period (s)', 'EditF', p_lim=[1e-5, 1e-3])
        self.add_para_field('Quality', 'Refactory Period', 'hillOrLlobetMethod', 1,
                            'Refactory Period Violation Method', 'Popup', p_list=p_method)

        # percentage spikes missing parameters
        self.add_para_field('Quality', 'Missing Spike Percentage', 'computeTimeChunks', 0,
                            'Computer Time Chunk Duration?')
        self.add_para_field('Quality', 'Missing Spike Percentage', 'deltaTimeChunk', 360,
                            'Time Chunk Duration (s)', 'EditF', p_lim=[60, 900])

        # presence ratio
        self.add_para_field('Quality', 'Presence Ratio', 'presenceRatioBinSize', 60,
                            'Presence Ratio Bin-Size (s)', 'EditF', p_lim=[10, 300])

        # drift estimate
        self.add_para_field('Quality', 'Drift Correction', 'driftBinSize', 60,
                            'Drift Window Bin-Size (s)', 'EditF', p_lim=[10, 300])
        self.add_para_field('Quality', 'Drift Correction', 'computeDrift', 0, 'Compute Unit Drift?')

        # waveform parameters
        self.add_para_field('Quality', 'Waveform', 'waveformBaselineWindowStart', 1,
                            'Waveform Window Start Index', 'Edit', p_lim=[1, 100],
                            p_dep={2, 'waveformBaselineWindowStop'})
        self.add_para_field('Quality', 'Waveform', 'waveformBaselineWindowStop', 11,
                            'Waveform Window Finish Index', 'Edit', p_lim=[1, 100],
                            p_dep={1, 'waveformBaselineWindowStart'})
        self.add_para_field('Quality', 'Waveform', 'minThreshDetectPeaksTroughs', 0.2,
                            'Min Peak Detection Threshold', 'EditF', p_lim=[0.01, 0.99])
        self.add_para_field('Quality', 'Waveform', 'normalizeSpDecay', 1,
                            'Normalise Spatial Decay?')
        self.add_para_field('Quality', 'Waveform', 'spDecayLinFit', 0,
                            'Spatial Decay Fit Type', 'Popup', p_list=p_fit)

        # recording parameters
        self.add_para_field('Quality', 'Recording', 'ephys_sample_rate', 30000,
                            'Sample Rate (Hz)', 'Edit', is_fixed=True)
        self.add_para_field('Quality', 'Recording', 'nChannels', 385,
                            'Recording Channel Count', 'Edit', is_fixed=True)
        self.add_para_field('Quality', 'Recording', 'nSyncChannels', 1,
                            'Sync Channel Count', 'Edit', is_fixed=True)
        self.add_para_field('Quality', 'Recording', 'ephysMetaFile', self.meta_file[0],
                            'Meta File Path', 'EditS', is_fixed=True)
        self.add_para_field('Quality', 'Recording', 'gain_to_uV', np.nan,
                            'Gain to uV Scale Factor', 'EditF')
        self.add_para_field('Quality', 'Recording', 'rawFile', self.raw_file[0],
                            'Raw File Path', 'EditS', is_fixed=True)

        # distance metric parameters
        self.add_para_field('Quality', 'Distance Metrics', 'computeDistanceMetrics', 0,
                            'Compute Distance Metrics?')
        self.add_para_field('Quality', 'Distance Metrics', 'nChannelsIsoDist', 4,
                            'Channel Neighbourhood Size', 'Edit', p_lim=[1, 10])

        # ---------------------------------------------------------------------------
        # Classification Parameters
        # ---------------------------------------------------------------------------

        # unit classification parameters
        self.add_para_field('Classification', 'Non-Somatic Units', 'splitGoodAndMua_NonSomatic', 0,
                            'Classify Non-Somatic Units?')

        # noise waveform parameters
        self.add_para_field('Classification', 'Waveform (Noise)', 'maxNPeaks', 2,
                            'Max Peak Count', 'Edit', p_lim=[2, 5])
        self.add_para_field('Classification', 'Waveform (Noise)', 'maxNTroughs', 1,
                            'Max Trough Count', 'Edit', p_lim=[1, 5])
        self.add_para_field('Classification', 'Waveform (Noise)', 'somatic', 1,
                            'Keep Somatic Units Only?')
        self.add_para_field('Classification', 'Waveform (Noise)', 'minWvDuration', 100,
                            'Min Waveform Duration (us)', 'EditF', p_lim=[10, 2000],
                            p_dep={2, 'maxWvDuration'})
        self.add_para_field('Classification', 'Waveform (Noise)', 'maxWvDuration', 1150,
                            'Max Waveform Duration (us)', 'EditF', p_lim=[10, 4000],
                            p_dep={1, 'minWvDuration'})
        self.add_para_field('Classification', 'Waveform (Noise)', 'minSpatialDecaySlope', -0.008,
                            'Min Linear Decay Slope (1/um)', 'EditF', p_lim=[-0.1, -1e-5])
        self.add_para_field('Classification', 'Waveform (Noise)', 'minSpatialDecaySlopeExp', 0.01,
                            'Min Exponential Decay Slope (1/um)', 'EditF', p_lim=[1e-4, 1],
                            p_dep={2, 'maxSpatialDecaySlopeExp'})
        self.add_para_field('Classification', 'Waveform (Noise)', 'maxSpatialDecaySlopeExp', 0.1,
                            'Max Exponential Decay Slope (1/um)', 'EditF', p_lim=[1e-3, 10],
                            p_dep={1, 'minSpatialDecaySlopeExp'})
        self.add_para_field('Classification', 'Waveform (Noise)', 'maxWvBaselineFraction', 0.3,
                            'Max Waveform Baseline Fraction', 'EditF', p_lim=[0.01, 0.99])
        self.add_para_field('Classification', 'Waveform (Noise)', 'maxScndPeakToTroughRatio_noise', 0.8,
                            'Max Peak To Trough Ratio', 'EditF', p_lim=[0.01, 10])

        # non-somatic waveform parameters
        self.add_para_field('Classification', 'Waveform (Non-Somatic)', 'maxPeak1ToPeak2Ratio_nonSomatic', 3,
                            'Max Peak To Peak Ratio', 'EditF', p_lim=[0.01, 10])
        self.add_para_field('Classification', 'Waveform (Non-Somatic)', 'maxMainPeakToTroughRatio_nonSomatic', 0.8,
                            'Max Peak To Trough Ratio', 'EditF', p_lim=[0.01, 10])
        self.add_para_field('Classification', 'Waveform (Non-Somatic)', 'minWidthFirstPeak_nonSomatic', 4,
                            'Min Peak Width (Samples)', 'Edit', p_lim=[1, 20])
        self.add_para_field('Classification', 'Waveform (Non-Somatic)', 'minWidthMainTrough_nonSomatic', 5,
                            'Min Trough Width (Samples)', 'Edit', p_lim=[1, 20])
        self.add_para_field('Classification', 'Waveform (Non-Somatic)', 'minTroughToPeak2Ratio_nonSomatic', 5,
                            'Min Trough To Peak Ratio', 'EditF', p_lim=[0.1, 100])

        # distance metric parameters
        self.add_para_field('Classification', 'Distance Metrics', 'isoDmin', 20,
                            'Min Isolation Distance', 'Edit', p_lim=[1, 200])
        self.add_para_field('Classification', 'Distance Metrics', 'lratioMax', 0.1,
                            'Max L-Ratio Value', 'EditF', p_lim=[0.01, 1])
        self.add_para_field('Classification', 'Distance Metrics', 'ssMin', np.nan,
                            'Min Silhouette Score', 'EditF', p_lim=[0, 100])

        # other classification parameters
        self.add_para_field('Classification', 'Other Parameters', 'minAmplitude', 20,
                            'Min Amplitude (uV)', 'EditF', p_lim=[1, 100])
        self.add_para_field('Classification', 'Other Parameters', 'maxRPVviolations', 0.1,
                            'Max RPV Violations', 'EditF', p_lim=[0.01, 0.99])
        self.add_para_field('Classification', 'Other Parameters', 'maxPercSpikesMissing', 20,
                            'Max Missing Spike (%)', 'EditF', p_lim=[1, 99])
        self.add_para_field('Classification', 'Other Parameters', 'minNumSpikes', 300,
                            'Min Spike Count', 'Edit', p_lim=[100, 3000])
        self.add_para_field('Classification', 'Other Parameters', 'maxDrift', 100,
                            'Max Drift Distance (um)', 'EditF', p_lim=[10, 1000])
        self.add_para_field('Classification', 'Other Parameters', 'minPresenceRatio', 0.7,
                            'Min Presence Ratio', 'EditF', p_lim=[0.01, 0.99])
        self.add_para_field('Classification', 'Other Parameters', 'minSNR', 1,
                            'Min Signal-To-Noise Ratio', 'EditF', p_lim=[0.01, 100])

    def add_para_field(self, p_grp_p, p_grp_s0, p_fld, p_val, p_desc=None, p_type='Checkbox',
                       p_lim=None, p_list=None, p_dep=None, is_fixed=False):

        # sets up the parameter mapping field
        p_grp_s = self.convert_para_field(p_grp_s0)

        # parameter group name mapping dictionary
        if p_grp_s not in self.p_map:
            self.p_map[p_grp_s] = p_grp_s0

        # primary group field memory allocation
        if p_grp_p not in self.p_grp:
            self.p_grp[p_grp_p] = {}

        # secondary group field memory allocation
        if p_grp_s not in self.p_grp[p_grp_p]:
            self.p_grp[p_grp_p][p_grp_s] = []

        # sets the group field names
        self.p_grp[p_grp_p][p_grp_s].append(p_fld)

        # sets the parameter field information
        self.p_info[p_fld] = {
            'p_type': p_type,
            'p_desc': p_desc,
            'p_list': p_list,
            'p_lim': p_lim,
            'p_dep': p_dep,
            'is_fixed': is_fixed,
            'tt_str': p_tooltip[p_fld],
        }

        # updates the bombcell parameter field
        self.bc_para[p_fld] = p_val

    @staticmethod
    def convert_para_field(p_str):

        # character replacement with underscores
        for p_u in '/- ':
            p_str = p_str.replace(p_u, '_')

        # character removal
        for p_r in '{}':
            p_str = p_str.replace(p_r, '')

        return p_str

# ----------------------------------------------------------------------------------------------------------------------

"""
    BombCellInfoTab:
"""

class BombCellInfoTab(InfoWidgetPara):
    # parameter field lists
    p_str_d = ['ephys_sample_rate', 'nChannels', 'nSyncChannels', 'ephysMetaFile', 'rawFile']

    # removal parameters
    p_rmv = {
        'verbose': False,
    }

    def __init__(self, t_str, main_obj, p_tab):
        super(BombCellInfoTab, self).__init__(t_str, main_obj, layout=QFormLayout)

        # sets the input arguments
        self.p_tab = p_tab
        self.main_obj = main_obj

        # initialises the major widget groups
        self.setup_prop_fields()
        self.init_filter_edit()
        self.init_property_frame()
        self.init_other_props()

        # other class properties
        self.p_props0 = deepcopy(self.p_props)

        # connects the property update function
        self.prop_updated.connect(self.solver_para_updated)

    def init_other_props(self):

        # disables the listed parameters
        for ps in self.p_str_d:
            h_obj = self.findChild(QLineEdit, name=ps)
            if h_obj is not None:
                h_obj.setEnabled(False)

    # ---------------------------------------------------------------------------
    # Class Property Widget Setup Functions
    # ---------------------------------------------------------------------------

    def setup_prop_fields(self):

        # parameter fields
        self.p_map_fld = {}

        # sets up the fields for each parameter group
        for pg, ps in self.p_tab.items():
            # if no valid parameters in block then continue
            if not np.any([(self.main_obj.p_info[x]['p_desc'] is not None) for x in ps]):
                continue

            # memory allocation
            p_props_g = {}
            self.p_props[pg] = {}

            # sets up the properties for each parameter in the group
            for _ps in ps:
                # determines if the parameter is visible (otherwise continue)
                p_info = self.main_obj.p_info[_ps]
                if p_info['p_desc'] is None:
                    self.main_obj.p_update[_ps] = self.main_obj.bc_para[_ps]
                    continue

                # creates the parameter field
                p_info = self.main_obj.p_info[_ps]
                p_value = self.main_obj.bc_para[_ps]
                p_desc, p_type = p_info['p_desc'], p_info['p_type']

                # sets the parameter-group mapping value
                self.p_map_fld[_ps] = pg

                match p_type:
                    case 'Checkbox':
                        # case is a checkbox
                        p_props_g[_ps] = self.create_para_field(p_desc, 'checkbox', bool(p_value))

                    case 'Popup':
                        # case is a popup menu
                        p_list = p_info['p_list']
                        p_value = p_list[int(p_value)]
                        p_props_g[_ps] = self.create_para_field(p_desc, 'combobox', p_value, p_list=p_list)

                    case _:
                        # case is an editbox

                        # parameter specific updates
                        if (p_type == 'Edit'):
                            # case is an integer editbox
                            p_value = int(p_value)

                        elif (p_type == 'EditS'):
                            if isinstance(p_value, pathlib.WindowsPath):
                                # converts from a path to string
                                p_value = str(p_value)

                            elif (len(p_value) == 0):
                                # case is an empty string
                                p_value = ''

                        # case is an editbox
                        p_props_g[_ps] = self.create_para_field(p_desc, 'edit', p_value)

                # updates the property value field
                self.p_props[pg][_ps] = p_props_g[_ps]['value']

            # sets the parameter group property fields
            self.p_prop_flds[pg] = {
                'name': self.main_obj.p_map[pg],
                'props': p_props_g,
            }

    # ---------------------------------------------------------------------------
    # Static Methods
    # ---------------------------------------------------------------------------

    @staticmethod
    def create_para_field(name, obj_type, value, p_fld=None, p_list=None, p_misc=None, ch_fld=None):

        return {'name': name, 'type': obj_type, 'value': value, 'p_fld': p_fld,
                'p_list': p_list, 'p_misc': p_misc, 'ch_fld': ch_fld}

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def solver_para_updated(self, p_str):

        if self.is_updating:
            return

        # updates the reset parameters button props
        self.main_obj.check_para_reset()

        # updates the model parameter value
        p_value = self.p_props[p_str[0]][p_str[1]]
        p_props = self.p_prop_flds[p_str[0]]['props'][p_str[1]]
        if (p_props['type'] == 'combobox'):
            # case is a combobox
            i_sel = p_props['p_list'].index(p_value)
            self.main_obj.bc_pkg.BombCellFcn('setParaValue', p_str[1], i_sel)

        else:
            # case the other parameter types
            self.main_obj.bc_pkg.BombCellFcn('setParaValue', p_str[1], p_value)

# ----------------------------------------------------------------------------------------------------------------------

"""
    BombCellSoln:  class for storing BombCell calculated data 
"""

class BombCellSoln(object):
    # parameter mapping dictionary
    p_map_bc = {
        # array dimensions
        'n_unit': 'nUnit',
        'n_pts': 'nPts',
        'n_ch': 'nCh',
        'n_ch_full': 'nChFull',
        'n_spike': 'nSpike',
        'n_qual_met': 'nQualMet',
        'n_hdr_max': 'nHdrMax',
        'n_peak_max': 'nPeakMax',
        'n_trough_max': 'nTroughMax',
        'n_hist_max': 'nHistMax',
        'n_decay_loc': 'nDecayLoc',

        # ephys data metrics
        'i_spike': 'iSpike',
        'spk_cluster': 'spkCluster',
        't_wform': 'tWForm',
        't_amp': 'tAmp',
        'ch_pos': 'chPos',
        's_rate': 'sRate',
        'T_wform': 'TWForm',
        't_spike': 'tSpike',
        'p_unit': 'pUnit',

        # quality metrics
        'q_hdr': 'Hdr',
        'q_met': 'Met',

        # raw waveform metrics
        'avg_sig': 'average',
        'pk_ch': 'peakChan',

        # gui data fields
        'x_bin_amp': 'ampliBinCenters',
        'y_bin_amp': 'ampliBinCounts',
        'y_gauss_amp': 'ampliGaussianFit',
        'x_peak': 'peakLocs',
        'x_trough': 'troughLocs',
        'x_decay_sp': 'spatialDecayPoints',
        'y_decay_sp': 'spatialDecayPoints_loc',
        'k_decay_sp': 'spatialDecayFit',
        'y_spike_unit': 'tempWv',

        # miscellaneous metrics
        'unit_type': 'unitType',
        't_unique': 'tUnique',
    }

    # character/integer parameters
    int_para = ['spk_cluster', 's_rate', 'unit_type', 't_unique']

    def __init__(self, bc_pkg_fcn):
        super(BombCellSoln, self).__init__()

        # ephys data metrics
        self.array_dim = bc_pkg_fcn('getClassField','arrDim')
        self.ephys_data = bc_pkg_fcn('getClassField','ephysData')
        self.gui_data = bc_pkg_fcn('getClassField','guiData')
        self.q_metric = bc_pkg_fcn('getClassField','qMetric')
        self.raw_form = bc_pkg_fcn('getClassField','rawForm')
        self.unit_type = bc_pkg_fcn('getClassField','unitType')
        self.t_unique = bc_pkg_fcn('getClassField', 'tUnique')

        # bombcell parameter setup
        # self.p_value = {}
        self.bc_para = bc_pkg_fcn('getClassField', 'bcPara')
        for k, v in self.bc_para.items():
            if not isinstance(v, str):
                self.p_map_bc[k] = k

        # other fields
        self.meta_data = bc_pkg_fcn('getClassField','metaData')

    def get_para_value(self, p_fld_bc):

        if hasattr(self, p_fld_bc):
            p_val = getattr(self, p_fld_bc)

        else:
            if p_fld_bc in self.p_map_bc:
                p_fld = self.p_map_bc[p_fld_bc]
            else:
                return None

            if p_fld in self.array_dim:
                p_val = self.array_dim[p_fld]

            elif p_fld in self.ephys_data:
                p_val = self.ephys_data[p_fld]

            elif p_fld in self.gui_data:
                p_val = self.gui_data[p_fld]

            elif p_fld in self.q_metric:
                p_val = self.q_metric[p_fld]

            elif p_fld in self.raw_form:
                p_val = self.raw_form[p_fld]

            elif p_fld in self.bc_para:
                p_val = self.bc_para[p_fld]

        # converts and returns the final values
        if p_fld_bc in self.int_para:
            # case is int32 type
            return np.int32(p_val)

        else:
            # case is float64 type
            return p_val

# ----------------------------------------------------------------------------------------------------------------------

"""
    BombCellSolver: dialog window for running the BombCell solver
"""

class BombCellSolver(BombCellPara, QDialog):
    # widget dimensions
    x_gap = 5
    width_dlg = 425
    hght_fspec = 60
    hght_para = 480
    hght_button = 40
    t_timer_per = 250

    # string class fields
    mmap_name = 'mMapProg.bin'

    # array class fields
    p_str_u = ['ephysMetaFile', 'rawFile']
    tab_str = ['Quality', 'Classification']
    but_str = ['Run Solver', 'Reset Parameters', 'Close Window']

    # stylesheets
    border_style = "border: 1px solid;"
    no_border_style = "border: 0px; padding-top: 3px;"
    frame_border_style = """
        QFrame {
            border: 1px solid;
        }
    """

    def __init__(self, main_obj, expt_dir=None):
        # boolean class fields
        self.has_bc = False
        self.init_complete = False
        self.is_updating = False
        self.is_running = False
        self.can_close = False
        self.is_new_soln = False
        self.is_ok = True

        super(BombCellSolver, self).__init__(main_obj, expt_dir)
        self.setup_para_groups.connect(self.init_para_groups)

        # # input arguments
        # self.main_obj = main_obj
        # self.expt_dir = expt_dir

        # class widgets
        self.h_tab_para = []
        self.cont_button = []
        self.fspec_group = QGroupBox("EXPERIMENT PARENT FOLDER")
        self.para_group = QGroupBox("SOLVER PARAMETERS")
        self.para_tab = cw.create_tab_group(None)
        self.prog_bar = cw.QDialogProgress(font=cw.font_lbl, is_task=True)
        self.progress_frame = QFrame()
        self.button_frame = QFrame()
        self.solver_timer = QTimer()

        # class layouts
        self.main_layout = QVBoxLayout()
        self.fspec_layout = QHBoxLayout()
        self.para_layout = QVBoxLayout()
        self.progress_layout = QVBoxLayout()
        self.button_layout = QHBoxLayout()

        # folder/file path fields
        self.mmap_file = None

        # other class fields
        self.i_tab = 0
        self.i_run = 1
        self.i_unit = 0
        self.bc_pkg = None
        self.bc_para_c = None
        self.hght_dlg = 6 * self.x_gap + (self.hght_fspec + self.hght_para + self.hght_button)

        # initialises the class fields
        self.init_class_fields()
        self.init_fspec_group()
        self.init_para_group()
        self.init_progress_frame()
        self.init_cont_buttons()

        # initialises the bombcell fields
        self.init_bomb_cell()

    # ---------------------------------------------------------------------------
    # Class Widget Initialisation Functions
    # ---------------------------------------------------------------------------

    def init_class_fields(self):

        # sets the dialog window properties
        self.setFixedSize(self.width_dlg, self.hght_dlg)
        self.setWindowTitle('BombCell Solver')
        self.setLayout(self.main_layout)

        # adds the main group widgets to the dialog
        self.main_layout.addWidget(self.fspec_group)
        self.main_layout.addWidget(self.para_group)
        self.main_layout.addWidget(self.progress_frame)
        self.main_layout.addWidget(self.button_frame)

        # solver timer callback function
        self.solver_timer.timeout.connect(self.solver_timer_fcn)

    def init_fspec_group(self):

        # creates the groupbox object
        self.fspec_group.setLayout(self.fspec_layout)
        self.fspec_group.setFont(cw.font_panel)
        self.fspec_group.setFixedHeight(self.hght_fspec)

        # sets up the slot functions
        self.fspec_edit = cw.create_line_edit(None, "", align='right')
        self.fspec_layout.addWidget(self.fspec_edit)
        self.fspec_edit.setFixedHeight(cf.but_height)
        self.fspec_edit.setEnabled(False)
        self.fspec_edit.setReadOnly(True)

    def init_para_group(self):

        # creates the groupbox object
        self.para_group.setLayout(self.para_layout)
        self.para_group.setFont(cw.font_panel)

        # adds the tab object to the parmaeter layout
        self.para_layout.addWidget(self.para_tab)

        # resets the channel table style
        tab_style = cw.CheckBoxStyle(self.para_tab.style())
        self.para_tab.setStyle(tab_style)

    def init_progress_frame(self):

        # sets the frame/layout properties
        self.progress_frame.setContentsMargins(0, 0, 0, 0)
        self.progress_frame.setLayout(self.progress_layout)
        self.progress_frame.setStyleSheet(self.frame_border_style)
        self.progress_layout.setContentsMargins(0, 0, 0, 0)
        self.progress_layout.setSpacing(0)
        self.progress_layout.addWidget(self.prog_bar)

        # creates the progressbar widgets
        self.prog_bar.set_enabled(False)
        self.prog_bar.setContentsMargins(self.x_gap, self.x_gap, self.x_gap, self.x_gap)

        # progressbar label properties
        self.prog_bar.lbl_obj.setContentsMargins(0, self.x_gap - 1, 0, 0)
        self.prog_bar.lbl_obj.setStyleSheet(self.no_border_style)

    def init_cont_buttons(self):

        # initialisations
        cb_fcn = [self.run_solver, self.reset_solver_para, self.close_window]

        # sets the button widget properties
        self.button_frame.setContentsMargins(self.x_gap, self.x_gap, self.x_gap, self.x_gap)
        self.button_frame.setLayout(self.button_layout)
        self.button_frame.setStyleSheet(self.frame_border_style)

        # sets the layout properties
        self.button_layout.setSpacing(2 * self.x_gap)
        self.button_layout.setContentsMargins(0, 0, 0, 0)

        for ib, (bs, cb) in enumerate(zip(self.but_str, cb_fcn)):
            # creates the control button widgets
            obj_but = cw.create_push_button(None, bs, cw.font_lbl)
            self.button_layout.addWidget(obj_but)
            self.cont_button.append(obj_but)

            # sets the other button properties
            obj_but.clicked.connect(cb)
            obj_but.setEnabled(ib == 2)
            obj_but.setAutoDefault(False)
            obj_but.setFixedHeight(cf.but_height)
            obj_but.setStyleSheet(self.border_style)

        # sets the control button properties
        self.cont_button[0].setCheckable(True)

    def init_para_groups(self):

        # determines if the experiment is feasible for analysis (exit if not)
        if not self.is_ok:
            # stops the package initialisation worker
            self.t_worker_pkg.force_quit()
            self.solver_timer.stop()
            time.sleep(0.01)

            # if not, then close the window
            self.close_window(True)
            return

        # case is the experiment is feasible
        self.fspec_edit.setEnabled(True)
        self.fspec_edit.setText(self.expt_dir)
        self.fspec_edit.setToolTip(self.expt_dir)

        # creates the tab objects
        for ts, p_tab in self.p_grp.items():
            tab_widget = BombCellInfoTab(ts, self, p_tab)
            self.para_tab.addTab(tab_widget, ts)
            self.h_tab_para.append(tab_widget)

        # tab change callback function
        self.para_tab.currentChanged.connect(self.on_tab_changed)

    # ---------------------------------------------------------------------------
    # BombCell Package/Solver Functions
    # ---------------------------------------------------------------------------

    def init_bomb_cell(self):

        # updates the progressbar
        self.prog_bar.set_label("Initialising BombCell")
        self.prog_bar.set_progbar_state(True)
        time.sleep(0.1)

        # creates the threadworker object
        self.t_worker_pkg = ThreadWorker(self, self.init_bombcell_package, None)
        self.t_worker_pkg.work_finished.connect(self.init_bombcell_package_complete)

        # progressbar flag update
        self.prog_bar.is_task = True
        self.prog_bar.timer_lbl = True

        # starts the worker object
        self.is_running = True
        self.t_worker_pkg.start()

    def init_bombcell_package(self, _):

        # initialises the bombcell package
        self.bc_pkg = BombCellPkg.initialize()
        self.bc_pkg_fcn = self.bc_pkg.BombCellFcn

        # creates the bombcell matlab object
        self.bc_pkg_fcn('initBombCell')

        # retrieves the parameter information/groupings
        self.p_map = self.bc_pkg_fcn('getParaField', 'pMap')
        self.p_grp = self.bc_pkg_fcn('getParaField', 'pGrp')
        self.p_fld = self.bc_pkg_fcn('getClassField', 'pFld')

        # other class field initialisations
        self.bc_pkg_fcn('setClassField', 'useSpykit', True)

    def init_bombcell_package_complete(self):

        # performs the post-processing parameter check
        self.post_processing_para_check()

        # sets up the memory map file
        self.create_solver_mmap(str(self.sort_dir))
        self.setup_expt_dir()

        # intiialises the parameter groups
        self.cont_button[0].setEnabled(True)

        # stops and updates the progressbar
        self.is_running = False
        self.init_complete = True
        self.prog_bar.set_progbar_state(False)

    # ---------------------------------------------------------------------------
    # BombCell Solver Functions
    # ---------------------------------------------------------------------------

    def run_bombcell_solver(self, _):

        # field retrieval
        is_concat = self.main_obj.session_obj.is_concat_run()
        is_per_shank = self.main_obj.session_obj.is_per_shank()
        n_shank_s = self.main_obj.session_obj.get_shank_count() if is_per_shank else 1

        # memory allocation
        bc_data_nw = np.empty((self.n_run, n_shank_s), dtype=object)
        s_info = {
            "iRun": 1,
            "iShank": 1,
            "isConcat": is_concat,
        }

        for i_run in range(self.n_run):
            # updates the run index
            s_info['iRun'] = i_run + 1
            for i_shank in range(n_shank_s):
                # updates the shank index
                s_info['iShank'] = i_shank + 1

                # runs the bombcell solver
                err_str = self.bc_pkg_fcn('runCalc', s_info)
                if len(err_str):
                    # case is there is an error in the calculations
                    return err_str

                elif self.mmap['s_flag']:
                    # if successful, stores the results from the solver
                    bc_data_nw[i_run, i_shank] = BombCellSoln(self.bc_pkg_fcn)

                else:
                    # otherwise, exit the loop
                    return 'BombCell calculation output error.'

        # stores the data struct within the class
        self.bc_data = bc_data_nw
        return []

    def run_bombcell_solver_complete(self, error_msg):

        # stops the solver timer
        self.solver_timer.stop()

        # stops and updates the progressbar
        self.prog_bar.stop_timer()

        # resets the button text
        self.cont_button[0].setChecked(False)
        self.cont_button[0].setText('Run Solver')

        if len(error_msg):
            # case is there was a BombCell calculation error
            cf.show_error(error_msg, 'BombCell Calculation Error', True)
            self.prog_bar.set_progbar_state(False)

        else:
            # otherwise, reset the new solution flag
            self.has_bc = True
            self.is_new_soln = True

            # resets the progressbar
            self.prog_bar.set_label('Solver Complete')
            self.prog_bar.set_full_prog()

            # updates the boolean flags
            self.bc_para_c = deepcopy(self.bc_pkg_fcn('getClassField', 'bcPara'))

        # resets the button properties
        self.is_running = False
        self.set_button_props(True)

    def run_solver(self):

        # resets the button state
        self.is_running = self.cont_button[0].isChecked()
        time.sleep(0.05)

        if self.is_running:
            if not self.check_solver_overwrite():
                # if the user cancelled, then exit the function
                self.is_updating = True
                self.cont_button[0].setChecked(False)
                self.is_updating = False

                # exits the function
                return

            # disables the panel properties
            self.set_button_props(False)
            self.cont_button[0].setChecked(True)
            self.cont_button[0].setText('Cancel Solver')

            # updates the progressbar
            self.prog_bar.is_task = False
            self.prog_bar.timer_lbl = False
            self.prog_bar.set_label("Initialising Solver")
            self.prog_bar.set_enabled(True)
            time.sleep(0.1)

            # flag that the solver is running
            self.mmap['i_unit'] = np.int16(0)
            self.mmap['s_flag'] = np.int16(1)

            # creates the threadworker object
            self.t_worker_solver = ThreadWorker(self, self.run_bombcell_solver, None)
            self.t_worker_solver.work_finished.connect(self.run_bombcell_solver_complete)

            # starts the worker object
            self.t_worker_solver.start()
            self.solver_timer.start(self.t_timer_per)

        else:
            # stops the worker
            self.t_worker_solver.force_quit()
            self.solver_timer.stop()
            time.sleep(0.01)

            # deletes the memory map file
            self.mmap['s_flag'] = np.int16(0)
            self.set_button_props(True, chk_para=True)

            # disables the progressbar fields
            self.prog_bar.set_progbar_state(False)
            self.cont_button[0].setText('Run Solver')

    def check_solver_overwrite(self, chk_para=True):

        if (not self.has_bc):
            # if there is no solution, then continue
            return True

        else:
            # case is there is a solution
            if chk_para:
                # if the parameters have changed, then continue
                if self.check_para_change(self.bc_para_c):
                    return True

            # otherwise, prompt the user to overwrite
            q_str = 'BombCell solution already calculated. Do you want to overwrite?'
            u_choice = QMessageBox.question(self.main_obj, 'Overwrite Folder?', q_str, cf.q_yes_no, cf.q_yes)
            return u_choice == cf.q_yes

    # ---------------------------------------------------------------------------
    # Memory Map Functions
    # ---------------------------------------------------------------------------

    def create_solver_mmap(self, sort_dir):

        # initialisations
        n_fld = 3
        self.mmap_file = os.path.join(sort_dir, self.mmap_name)

        # sets the memory map data type
        dt = np.dtype([
            ('s_flag', 'i2'),
            ('i_unit', 'i2'),
            ('n_unit', 'i2'),
        ])

        # deletes any previous memory mapping file
        for p in Path('.').rglob(self.mmap_name):
            try:
                os.remove(p)
                time.sleep(0.1)
            except:
                pass

        # creates the memory map file
        self.mmap = np.memmap(self.mmap_file, dtype=dt, mode='w+', shape=(1,))
        self.mmap['s_flag'] = np.int16(0)
        self.mmap['i_unit'] = np.int16(0)
        self.mmap['n_unit'] = np.int16(0)

        # pauses for a little bit...
        time.sleep(0.1)

    def delete_solver_mmap(self):

        # deletes the file (if it exists)
        if os.path.exists(self.mmap_file):
            os.remove(self.mmap_file)

    # ---------------------------------------------------------------------------
    # Class Widget Event Functions
    # ---------------------------------------------------------------------------

    def on_tab_changed(self):

        self.i_tab = self.para_tab.currentIndex()
        self.h_tab_para[self.i_tab].repaint()

    def setup_expt_dir(self):

        # experimental information dictionary
        exp_info = {
            "exDir": self.expt_dir.replace('//', '/'),
            "nRun": self.n_run,
            "nShank": self.main_obj.session_obj.get_shank_count(),
            "isConcat": self.main_obj.session_obj.is_concat_run(),
            "isPerShank": self.main_obj.session_obj.is_per_shank(),
        }

        # runs the experiment folder diagnosis
        self.bc_pkg_fcn('setupExptDir', exp_info)
        for i_run in range(self.k_sort.shape[0]):
            # raw/meta data files
            self.bc_pkg_fcn('setClassArrayField', 'rFile0', str(self.raw_file[i_run]), i_run + 1)
            self.bc_pkg_fcn('setClassArrayField', 'mFile0', str(self.meta_file[i_run]), i_run + 1)

            # bombcell save/kilosort directories
            for i_shank in range(self.k_sort.shape[1]):
                self.bc_pkg_fcn('setClassArrayField', 'sDir0', str(self.s_dir[i_run, i_shank]),
                                i_run + 1, i_shank + 1)
                self.bc_pkg_fcn('setClassArrayField', 'kSortD0', str(self.k_sort[i_run, i_shank]),
                                i_run + 1, i_shank + 1)

    def solver_timer_fcn(self):

        if (self.i_unit != self.mmap['i_unit'][0]):
            # updates the unit index
            self.i_unit = self.mmap['i_unit'][0]

            # unit/progress value fields
            i_unit_pr = self.i_unit
            pr_val = float(self.i_unit) / (2 * float(self.mmap['n_unit'][0]))

            # solver procedure specific updates
            if (self.i_unit == 2 * self.mmap['n_unit'][0]):
                # case is the solver has finished
                pr_str = 'Finalising Solver Results...'

            else:
                if (self.i_unit <= self.mmap['n_unit'][0]):
                    # case is extracting waveforms
                    pr_pref = 'Extracting Waveforms'

                else:
                    # case is quality metric calculations
                    pr_pref = 'Calculating Metrics'
                    i_unit_pr -= self.mmap['n_unit'][0]

                # updates the progressbar
                pr_str = '{0} ({1}/{2})'.format(pr_pref, i_unit_pr, self.mmap['n_unit'][0])

            # updates the progressbar string/value
            self.prog_bar.update_prog_fields(pr_str, pr_val)

    def post_processing_soln_change(self):

        # determines if any parameters are altered
        para_changed = self.post_processing_para_check()
        if len(para_changed):
            # flag that the fields are being manually updated
            self.is_updating = False
            bc_para = self.bc_pkg_fcn('getClassField', 'bcPara')

            # resets the widget fields
            for pc in para_changed:
                self.set_widget_para_value(pc, bc_para[pc])

            # resets the update flag
            self.is_updating = False

    def set_button_props(self, state, chk_para=False):

        if state:
            # resets the button properties
            if self.has_bc or chk_para:
                self.check_para_reset(self.bc_para_c)
            else:
                self.check_para_reset()

        else:
            # force disable reset button
            self.cont_button[1].setEnabled(False)

        # sets the close window button
        self.cont_button[2].setEnabled(state)

    # ---------------------------------------------------------------------------
    # Class Event Functions
    # ---------------------------------------------------------------------------

    def closeEvent(self, event):

        if self.can_close:
            # force close
            event.accept()

        else:
            # user confirmed close
            q_str = "Are you sure you want to close the window?"
            u_choice = QMessageBox.question(
                self, 'Confirm Close?', q_str, cf.q_yes_no, cf.q_yes)
            if u_choice == cf.q_yes:
                event.accept()
            else:
                event.ignore()

    # ---------------------------------------------------------------------------
    # Window I/O Functions
    # ---------------------------------------------------------------------------

    def show_window(self):

        # restarts initialisation (if not complete)
        if not self.init_complete:
            self.init_bomb_cell()

        # makes the window visible
        self.setVisible(True)

    def close_window(self, force_close=False):

        # stops the thread worker (if running)
        if self.is_running:
            # resets the boolean flags
            self.is_running = False

            # stops the progressbar and thread worker
            self.prog_bar.set_progbar_state(False)
            self.t_worker_solver.force_quit()

        if force_close:
            # terminates the package
            if self.bc_pkg is not None:
                # clears/terminates the bombcell matlab object
                self.bc_pkg_fcn('closeBombCell')
                self.bc_pkg.terminate()
                self.bc_pkg = None

            # closes the dialog window
            self.main_obj.bombcell_dlg = None
            self.can_close = True
            self.close()

        else:
            # initialisations
            t_worker = None

            # check if a new solution has been calculated
            if self.is_new_soln:
                # prompt the user if they want to keep the new data
                q_str = 'Do you want to keep the calculated post-processing data?'
                u_choice = QMessageBox.question(self, 'Update Post-Processing Data?', q_str, cf.q_yes_no, cf.q_yes)
                if u_choice == cf.q_yes:
                    # if so, then update the post processing data
                    t_worker = self.main_obj.setup_postprocessing_worker(self.bc_data, True)

                # resets the new solution flag
                self.is_new_soln = False

            # makes the window invisible again
            self.setVisible(False)

            # starts the memory map output thread worker
            if t_worker is not None:
                t_worker.start()

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def reset_solver_para(self):

        # flag that manual updating is taking place
        self.is_updating = True

        # field retrieval
        bc_para = self.bc_pkg_fcn('getClassField', 'bcPara')
        bc_para0 = self.bc_pkg_fcn('getClassField', 'bcPara0')

        for pf, pv0 in bc_para0.items():
            pv = bc_para[pf]
            if (pv0 != pv) and (not np.isnan(pv)):
                # resets the class object parameter values
                self.bc_pkg_fcn('setParaValue', pf, pv0)
                self.set_widget_para_value(pf, pv0)

        # disables the button
        self.is_updating = False
        self.cont_button[1].setEnabled(False)

    def check_para_reset(self, bc_para0=None):

        # field retrieval
        self.cont_button[1].setEnabled(self.check_para_change(bc_para0))

    def check_para_change(self, bc_para0=None):

        if self.bc_pkg_fcn is None:
            return False

        elif bc_para0 is None:
            # retrieves the comparison parameter struct (if not provided)
            bc_para0 = self.bc_pkg_fcn('getClassField', 'bcPara0')

        # checks all current/comparison fields
        bc_para = self.bc_pkg_fcn('getClassField', 'bcPara')
        for pf, pv in bc_para0.items():
            if (isinstance(pv,float) and np.isnan(pv)):
                continue

            elif (pf in self.p_str_u):
                continue

            elif (pv != bc_para[pf]):
                return True

        # flag that there is no difference
        return False

    def set_widget_para_value(self, pf, pv):

        # resets the parameter field
        h_obj = self.para_tab.findChild(QWidget, name=pf)
        if isinstance(h_obj, QCheckBox):
            # case is a checkbox
            h_obj.setChecked(bool(pv))

        elif isinstance(h_obj, QLineEdit):
            # case is an editbox
            p_info = self.bc_pkg_fcn('getParaInfo', pf)
            if p_info['pType'] == 'EditS':
                # case is a string editbox
                h_obj.setText(pv)

            elif np.isnan(pv):
                # case is a NaN value
                h_obj.setText(str(pv))

            else:
                # case is a numeric editbox
                h_obj.setText('%g' % int(pv))

        elif isinstance(h_obj, QComboBox):
            # case is a combobox
            h_obj.setCurrentIndex(int(pv))

    def post_processing_para_check(self):

        # field retrieval
        para_changed = []
        s_obj = self.main_obj.session_obj

        # updates any outstanding parameter fields
        for ps, pv in self.p_update.items():
            self.bc_pkg_fcn('setClassField', ps, pv)

        # check if there is any existing post-processing data loaded
        if (s_obj.post_data is not None) and len(s_obj.post_data.mmap):
            # resets the parameters to match the post-processing dataset
            bc_para = self.bc_pkg_fcn('getClassField', 'bcPara')
            for k in bc_para.keys():
                if k not in self.p_str_u:
                    # if the parameters do not match, then reset the value
                    p_val_pp = s_obj.get_mem_map_field(k)
                    if (p_val_pp != bc_para[k]) and (not np.isnan(bc_para[k])):
                        para_changed.append(k)
                        bc_para[k] = p_val_pp
                        self.bc_pkg_fcn('setParaValue', k, p_val_pp)

            # resets the parameter struct (if a change is made)
            if len(para_changed):
                self.bc_pkg_fcn('setClassField', 'bcPara', bc_para)

        # returns the altered parameters
        return para_changed