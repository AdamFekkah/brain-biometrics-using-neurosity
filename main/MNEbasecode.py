from pathlib import Path
import mne
from mne.datasets import sample
import matplotlib.pyplot as plt
import pandas as pd


# New code to convert CSV to FIF
def csv_to_fif(csv_file, fif_file):
    df = pd.read_csv(csv_file)

    # Create MNE info structure
    sfreq = 250  # Example sampling frequency
    ch_names = ['Cz']  # Example channel name, modify as per your data
    ch_types = ['eeg']  # Channel type

    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types=ch_types)

    # Convert the data to an MNE RawArray
    data = df['Value'].values.reshape((1, len(df)))
    raw = mne.io.RawArray(data, info)

    # Save the data to a .fif file
    raw.save(fif_file, overwrite=True)
    return raw


# Define the CSV and FIF file paths
csv_file = 'neurosity_readings.csv'
fif_file = 'output_file.fif'

# Convert CSV to FIF
raw = csv_to_fif(csv_file, fif_file)

# Existing code to process the FIF file
data_path = Path(sample.data_path())
raw = mne.io.read_raw_fif(data_path / 'MEG' / 'sample' / 'sample_audvis_raw.fif', preload=True)

montage = mne.channels.make_standard_montage('standard_1020')
raw.set_montage(montage, match_case=False, on_missing='ignore')

raw.filter(0.1, 72, fir_design='firwin')

events = mne.find_events(raw, stim_channel='STI 014')

event_id = {'semantic_incongruity': 1}
tmin, tmax = -0.2, 0.8

epochs = mne.Epochs(raw, events, event_id=event_id, tmin=tmin, tmax=tmax, baseline=(None, 0), preload=True)
epochs.drop_bad()

evoked = epochs.average()
evoked.plot()

n400_peak = evoked.get_peak(tmin=0.3, tmax=0.5, mode='neg')
n400_amplitude = n400_peak[0]
n400_latency = n400_peak[1]

print(f"N400 Amplitude: {n400_amplitude} µV")
print(f"N400 Latency: {n400_latency} ms")

n400_auc = evoked.copy().crop(tmin=0.3, tmax=0.5).data.mean(axis=1).sum()
print(f"N400 Area Under Curve (AUC): {n400_auc}")

# Compute power spectral density for the N400 time window
psd, freqs = mne.time_frequency.psd_welch(epochs, tmin=0.3, tmax=0.5, fmin=1, fmax=30, n_fft=256)

plt.plot(freqs, psd.mean(axis=0).T)
plt.xlabel('Frequency (Hz)')
plt.ylabel('Power Spectral Density (µV²/Hz)')
plt.show()

src = mne.setup_source_space('sample', spacing='oct6', subjects_dir=data_path / 'subjects')
bem = mne.make_bem_model(subject='sample', ico=4, subjects_dir=data_path / 'subjects')
bem_sol = mne.make_bem_solution(bem)
trans = data_path / 'MEG' / 'sample' / 'sample_audvis_raw-trans.fif'

fwd = mne.make_forward_solution(raw.info, trans=trans, src=src, bem=bem_sol, meg=False, eeg=True)

cov = mne.compute_covariance(epochs, tmax=0)

inv = mne.minimum_norm.make_inverse_operator(raw.info, fwd, cov, loose=0.2, depth=0.8)

stc = mne.minimum_norm.apply_inverse(evoked, inv, lambda2=1 / 9., method='dSPM')

brain = stc.plot(hemi='both', subjects_dir=data_path / 'subjects', initial_time=0.4, time_viewer=True)

print(raw.info)

data, times = raw.get_data(return_times=True)
