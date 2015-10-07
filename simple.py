import matplotlib

# matplotlib.use('TkAgg')
#[CB 9/5/2015] Note the above line is basically for my windows setup.
#everything is screwy in windows.  In mac or linux, you could probably remove it.
import mne
import matplotlib.pyplot as plt
import numpy as np
import scipy as sp
from scipy.signal import butter, lfilter, freqz
from PIL import Image
import re

#below is filter stuff
#derived from http://stackoverflow.com/questions/25191620/creating-lowpass-filter-in-scipy-understanding-methods-and-units
def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = lfilter(b, a, data)
    return y

def butter_bandpass(lowcutoff, highcutoff, fs, order=5):
    nyq = 0.5 * fs
    low_normal_cutoff = lowcutoff / nyq
    high_normal_cutoff = highcutoff / nyq
    b, a = butter(order, [low_normal_cutoff, high_normal_cutoff], btype='bandpass', analog=False)
    return b, a

def butter_bandpass_filter(data, lowcutoff, highcutoff, fs, order=5):
    b, a = butter_bandpass(lowcutoff, highcutoff, fs, order=order)
    y = lfilter(b, a, data)
    return y

doplot = False
counter = 0;
def myshow():
   """this function is intended to work around the limitations of CB's python setup
     which doesn't work properly with matplotlib interactive mode.  depending on doplot
     this either calls plt.show() or plt.savefig()"""
   global counter
   if (doplot):
       plt.show()
   else:
       fname = "figures/figure"+str(counter)+".png"
       plt.savefig(fname)
       im = Image.open(fname)
       im.show()
       counter=counter+1

def lowpass_stuff():
    # Filter requirements.
    order = 6
    fs = 1024       # sample rate, Hz
    cutoff = 4 # desired cutoff frequency of the filter, Hz

    # Get the filter coefficients so we can check its frequency response.
    b, a = butter_lowpass(cutoff, fs, order)

    # Plot the frequency response.
    w, h = freqz(b, a, worN=8000)
    plt.subplot(2, 1, 1)
    plt.plot(0.5*fs*w/np.pi, np.abs(h), 'b')
    plt.plot(cutoff, 0.5*np.sqrt(2), 'ko')
    plt.axvline(cutoff, color='k')
    plt.xlim(0, 0.5*fs)
    plt.title("Lowpass Filter Frequency Response")
    plt.xlabel('Frequency [Hz]')
    plt.grid()

    # Demonstrate the use of the filter.
    # First make some data to be filtered.
    T = 5.0         # seconds
    n = int(T * fs) # total number of samples
    t = np.linspace(0, T, n, endpoint=False)
    # "Noisy" data.  We want to recover the 1.2 Hz signal from this.
    data = np.sin(1.2*2*np.pi*t) + 1.5*np.cos(9*2*np.pi*t) + 0.5*np.sin(12.0*2*np.pi*t)

    # Filter the data, and plot both the original and filtered signals.
    y = butter_lowpass_filter(data, cutoff, fs, order)

    plt.subplot(2, 1, 2)
    plt.plot(t, data, 'b-', label='data')
    plt.plot(t, y, 'g-', linewidth=2, label='filtered data')
    plt.xlabel('Time [sec]')
    plt.grid()
    plt.legend()

    plt.subplots_adjust(hspace=0.35)
    myshow()

def bandpass_stuff():
    # Filter requirements.
    order = 6
    fs = 1024       # sample rate, Hz
    lowcutoff = 20 # desired cutoff frequency of the filter, Hz
    highcutoff = 80 # high cutoff

    # Get the filter coefficients so we can check its frequency response.
    b, a = butter_bandpass(lowcutoff, highcutoff, fs, order)

    # Plot the frequency response.
    w, h = freqz(b, a, worN=8000)
    plt.subplot(2, 1, 1)
    plt.plot(0.5*fs*w/np.pi, np.abs(h), 'b')
    plt.plot(lowcutoff, 0.5*np.sqrt(2), 'ko')
    plt.plot(highcutoff, 0.5*np.sqrt(2), 'ko')
    plt.axvline(lowcutoff, color='k')
    plt.axvline(highcutoff, color='k')
    plt.xlim(0, 0.5*fs)
    plt.title("Bandpass Filter Frequency Response")
    plt.xlabel('Frequency [Hz]')
    plt.grid()
    myshow()

def dostuff():
    data = mne.io.read_raw_edf("../EEGDATA/CAPSTONE_AB/BASHAREE_TEST.edf",preload=True)
    start, stop = data.time_as_index([100, 200])
    ldata, ltimes = data[2:8, start:stop]
    spikesStructure = stupidIdentifySpikes(ldata, cutoff=0.0005)
    linSpikes = convertSpikesStructureToLinearForm(spikesStructure)
    print linSpikes
    for arr in ldata:
        plt.plot(arr)
    for spike in linSpikes:
        plt.axvline(spike, color='k')
    plt.show()

def convertSpikesStructureToLinearForm(spikesstructure):
    """converts a spikesStructure which identifies spikes "detected" on each
    channel into a simple array of sample nos where spikes were detected"""
    spikeSet = set()
    for arr in spikesstructure:
        for item in arr:
            spikeSet.add(item)
    out = list(spikeSet)
    out.sort()
    return out

def stupidIdentifySpikes(data, spikekernellength=128, cutoff=0.0133):
    thekernel = sp.signal.morlet(spikekernellength)
    #[CB 9/5/2015] So this kernel is only for "detecting" spikes of a given format.
    #a.k.a. it sucks.

    #plt.plot(thekernel)
    #plt.show()
    #ldata2, times2 = data[2:20:3, start:stop]

    accumulator = []
    for arr in data:
        correlated = sp.signal.correlate(arr, thekernel)
        accumulator.append(correlated)
    accumulated = np.vstack(accumulator)

    #for arr in accumulated:
    #    plt.plot(arr)
    #plt.show()

    spikesout = []
    for i in range(0, len(accumulated)):
        spikesout.append([])
        for i2 in range(0, len(accumulated[i])):
            if(accumulated[i][i2]>=cutoff):
                spikesout[i].append(i2)
    return spikesout


def amplitude_adjust_data(dataSeries, amplitudeFactor):
    out = map(lambda x: x*amplitudeFactor, dataSeries)

def getDisplayData(realData, start_time, end_time, amplitude_adjust, lowpass, highpass, channels=range(1,15)):
    """given some real EEG data, getDisplayData processes it in a way that is useful for display
      purposes and returns the results"""
    start, stop = realData.time_as_index([start_time, end_time])
    ldata, ltimes = realData[channels, start:stop]
    #spikesStructure = stupidIdentifySpikes(ldata, cutoff=0.0005)
    #linSpikes = convertSpikesStructureToLinearForm(spikesStructure)
    #avgdata = np.average(np.array(ldata),0)
    ldata2 = map(lambda x: amplitude_adjust*butter_bandpass_filter(x,lowpass,highpass,256), ldata)
    return (ldata2,ltimes)

# def show_data(start_time, end_time, amplitude_adjust, lowpass ,highpass):

# t = np.arange(0, len(data))
# ticklocs = []
# ax = plt.subplot(212)
# plt.xlim(0,10)
# plt.xticks(np.arange(10))
# dmin = data.min()
# dmax = data.max()
# dr = (dmax - dmin)*0.7 # Crowd them a bit.
# y0 = dmin
# y1 = (47-1) * dr + dmax
# plt.ylim(y0, y1)

# segs = []
# for i in range(47):
#     segs.append(np.hstack((t[:,np.newaxis], data[:,i,np.newaxis])))
#     ticklocs.append(i*dr)

# offsets = np.zeros((numRows,2), dtype=float)
# offsets[:,1] = ticklocs

# lines = LineCollection(segs, offsets=offsets,
#                        transOffset=None,
#                        )

# ax.add_collection(lines)

# # set the yticks to use axes coords on the y axis
# ax.set_yticks(ticklocs)
# ax.set_yticklabels(['PG3', 'PG5', 'PG7', 'PG9'])

# xlabel('time (s)')

# reads annotation data from disk to and creates tuples of the data
# returns list of (time, duration, title) 
#  time is (hour, minute, second)

def load_raw_annotations(rawAnnotationsPath):
    myfile = open(rawAnnotationsPath, 'r')
    startFound = False
    annotations = []
    for line in myfile:
        if not startFound:
            if re.match('\s*Time\s+Duration\s+Title', line) != None:
                startFound = True
        else:
            #note this assumes there is no duration in the file
            matches = re.match('(\d*):(\d*):(\d*)  \t\t(.*)', line)
            #print matches.groups()
            entry = ((int(matches.group(1)),int(matches.group(2)),int(matches.group(3))), None , matches.group(4))
            annotations.append(entry)
    myfile.close()
    return annotations

# truth is (time,duration,title)
# predictions is [time]
#  time is (hour, minute, second)
# returns (truePositives, falsePositives, falseNegatives)
def score_predictions(truth, predictions):
    spikeList = [] #tuple of (time, duration)
    for time,duration,title in truth:
        if title == 'spike':
            if duration is None: duration = (0,0,1)
            spikeList.append((time, duration))
    numSpikes = len(spikeList)
    numPredictions = len(predictions)
    numCorrect = 0
    for (spikehr,spikemin,spikesec),spikedur in spikeList:
        spiketime = (spikehr * 3600) + (spikemin * 60) + spikesec
        found = False
        for pred in predictions:
            predtime = (pred[0] * 3600) + (pred[1] * 60) + pred[2]
            if (spiketime+spikedur >= predtime and spiketime-spikedur <= predtime):
                found = True
                break
        if found:
            numCorrect += 1
    return (numCorrect, numPredictions - numCorrect, numSpikes - numCorrect)

#data = mne.io.read_raw_edf("../EEGDATA/CAPSTONE_AB/BASHAREE_TEST.edf",preload=True)
