# module import
import os
import struct
import numpy as np
from pathlib import Path

from PyQt6.QtCore import pyqtSignal, QObject

# ----------------------------------------------------------------------------------------------------------------------

"""
    PostMemMap:  post-processing data memory map 
"""

class PostMemMap(QObject):
    # pyqtsignal functions
    progress_fcn = pyqtSignal(int, int)

    # dimension fields
    n_hdr_mua = 4
    n_hdr_noise = 6
    n_hdr_nonsoma = 2
    n_dim_para = 11

    def __init__(self):
        super(PostMemMap, self).__init__()

        # field initialsiation
        self.mmap_file = None

    def set_mmap_file(self, mmap_file_new):

        # sets the input arguments
        self.mmap_file = mmap_file_new.replace('\\', '/')

    def write_mem_map(self, bc_data):

        # field retrieval
        p_fcn = bc_data.get_para_value

        # array dimensions
        n_unit = int(bc_data.array_dim['nUnit'])
        n_pts = int(bc_data.array_dim['nPts'])
        n_ch = int(bc_data.array_dim['nCh'])
        n_ch_full = int(bc_data.array_dim['nChFull'])
        n_spike = int(bc_data.array_dim['nSpike'])
        n_qual_met = int(bc_data.array_dim['nQualMet'])
        n_hdr_max = int(bc_data.array_dim['nHdrMax'])
        n_peak_max = int(bc_data.array_dim['nPeakMax'])
        n_trough_max = int(bc_data.array_dim['nTroughMax'])
        n_hist_max = int(bc_data.array_dim['nHistMax'])
        n_decay_loc = int(bc_data.array_dim['nDecayLoc'])

        # structure dtype
        dt = self.get_dtype((n_unit, n_pts, n_ch, n_ch_full, n_spike, n_qual_met,
                             n_hdr_max, n_peak_max, n_trough_max, n_hist_max, n_decay_loc))
        m_map = np.memmap(self.mmap_file, dtype=dt, mode='w+', shape=(1,))

        # sets the memory map fields
        n_fld = len(dt.names)
        for i_fld, dt_n in enumerate(dt.names):
            # progress update
            self.progress_fcn.emit(i_fld, n_fld)

            # parameter field value
            p_val_new = p_fcn(dt_n)
            if p_val_new is None:
                # case is a local variable
                m_map[dt_n] = eval(dt_n)

            else:
                # case is a bombcell data field
                m_map[dt_n] = p_val_new

        # flushes data to disk
        m_map.flush()
        return m_map

    def read_mem_map(self):

        with open(self.mmap_file, 'rb') as f:
            # reads the first n_dim_para
            data_bytes = f.read(4 * self.n_dim_para)
            dim_vals = struct.unpack(f'{self.n_dim_para}i', data_bytes)

            # returns the memory map
            return np.memmap(self.mmap_file, dtype=self.get_dtype(), mode='r', shape=(1,))

    def get_array_dim(self):

        with open(self.mmap_file, 'rb') as f:
            # reads the first n_dim_para
            data_bytes = f.read(4 * self.n_dim_para)
            return struct.unpack(f'{self.n_dim_para}i', data_bytes)

    def get_dtype(self, dim_arr=None):

        # sets up the data type struct
        if dim_arr is None:
            (n_unit, n_pts, n_ch, n_ch_full, n_spike, n_qual_met, n_hdr_max,
             n_peak_max, n_trough_max, n_hist_max, n_decay_loc) = self.get_array_dim()
        else:
            (n_unit, n_pts, n_ch, n_ch_full, n_spike, n_qual_met, n_hdr_max,
             n_peak_max, n_trough_max, n_hist_max, n_decay_loc) = dim_arr

        dt_type = np.dtype([
            # case is array dimensions
            ('n_unit', 'i4'),
            ('n_pts', 'i4'),
            ('n_ch', 'i4'),
            ('n_ch_full', 'i4'),
            ('n_spike', 'i4'),
            ('n_qual_met', 'i4'),
            ('n_hdr_max', 'i4'),
            ('n_peak_max', 'i4'),
            ('n_trough_max', 'i4'),
            ('n_hist_max', 'i4'),
            ('n_decay_loc', 'i4'),

            # case is ephys data
            ('i_spike', 'f4', (n_spike, 1)),
            ('spk_cluster', 'i4', (n_spike, 1)),
            ('t_wform', 'f4', (n_unit, n_pts, n_ch)),
            ('t_amp', 'f4', (n_spike, 1)),
            ('ch_pos', 'f4', (n_ch, 2)),
            ('s_rate', 'i4'),
            ('T_wform', 'f4', (1, n_pts)),
            ('t_spike', 'f4', (n_spike, 1)),
            ('p_unit', 'f4', (n_unit, 2)),

            # case is quality metrics
            ('q_hdr', f'U{n_hdr_max}', (1, n_qual_met)),
            ('q_met', 'f4', (n_unit, n_qual_met)),

            # case is raw waveforms
            ('avg_sig', 'f4', (n_unit, n_ch_full, n_pts)),
            ('pk_ch', 'f4', (n_unit, 1)),

            # case is other gui data fields
            ('x_bin_amp', 'f4', (n_unit, n_hist_max)),
            ('y_bin_amp', 'f4', (n_unit, n_hist_max)),
            ('y_gauss_amp', 'f4', (n_unit, n_hist_max)),
            ('x_peak', 'f4', (n_unit, n_peak_max)),
            ('x_trough', 'f4', (n_unit, n_trough_max)),
            ('x_decay_sp', 'f4', (n_unit, n_decay_loc)),
            ('y_decay_sp', 'f4', (n_unit, n_decay_loc)),
            ('k_decay_sp', 'f4', (n_unit, 1)),
            ('y_spike_unit', 'f4', (n_unit, n_pts)),

            # case is miscellaneous field
            ('unit_type', 'i4', (n_unit, 1)),
            ('t_unique', 'i4', (n_unit, 1)),

            # case is the bombcell parameters
            ("plotDetails", "f4"),
            ("plotGlobal", "f4"),
            ("verbose", "bool"),
            ("reextractRaw", "f4"),
            ("saveAsTSV", "f4"),
            ("unitType_for_phy", "f4"),
            ("saveMatFileForGUI", "f4"),
            ("removeDuplicateSpikes", "f4"),
            ("saveSpikes_withoutDuplicates", "f4"),
            ("recomputeDuplicateSpikes", "f4"),
            ("duplicateSpikeWindow_s", "f4"),
            ("detrendWaveform", "f4"),
            ("nRawSpikesToExtract", "f4"),
            ("saveMultipleRaw", "f4"),
            ("decompressData", "f4"),
            ("spikeWidth", "f4"),
            ("extractRaw", "f4"),
            ("probeType", "f4"),
            ("computeSpatialDecay", "f4"),
            ("waveformBaselineNoiseWindow", "f4"),
            ("tauR_valuesMin", "f4"),
            ("tauR_valuesStep", "f4"),
            ("tauR_valuesMax", "f4"),
            ("tauC", "f4"),
            ("hillOrLlobetMethod", "f4"),
            ("computeTimeChunks", "f4"),
            ("deltaTimeChunk", "f4"),
            ("presenceRatioBinSize", "f4"),
            ("driftBinSize", "f4"),
            ("computeDrift", "f4"),
            ("waveformBaselineWindowStart", "f4"),
            ("waveformBaselineWindowStop", "f4"),
            ("minThreshDetectPeaksTroughs", "f4"),
            ("normalizeSpDecay", "f4"),
            ("spDecayLinFit", "f4"),
            ("ephys_sample_rate", "f4"),
            ("nChannels", "f4"),
            ("nSyncChannels", "f4"),
            ("gain_to_uV", "f4"),
            ("computeDistanceMetrics", "f4"),
            ("nChannelsIsoDist", "f4"),
            ("splitGoodAndMua_NonSomatic", "f4"),
            ("maxNPeaks", "f4"),
            ("maxNTroughs", "f4"),
            ("somatic", "f4"),
            ("minWvDuration", "f4"),
            ("maxWvDuration", "f4"),
            ("minSpatialDecaySlope", "f4"),
            ("minSpatialDecaySlopeExp", "f4"),
            ("maxSpatialDecaySlopeExp", "f4"),
            ("maxWvBaselineFraction", "f4"),
            ("maxScndPeakToTroughRatio_noise", "f4"),
            ("maxPeak1ToPeak2Ratio_nonSomatic", "f4"),
            ("maxMainPeakToTroughRatio_nonSomatic", "f4"),
            ("minWidthFirstPeak_nonSomatic", "f4"),
            ("minWidthMainTrough_nonSomatic", "f4"),
            ("minTroughToPeak2Ratio_nonSomatic", "f4"),
            ("isoDmin", "f4"),
            ("lratioMax", "f4"),
            ("ssMin", "f4"),
            ("minAmplitude", "f4"),
            ("maxRPVviolations", "f4"),
            ("maxPercSpikesMissing", "f4"),
            ("minNumSpikes", "f4"),
            ("maxDrift", "f4"),
            ("minPresenceRatio", "f4"),
            ("minSNR", "f4"),
        ])

        return dt_type