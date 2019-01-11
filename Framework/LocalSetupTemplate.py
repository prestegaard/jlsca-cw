import os

###################################################################
# Local setup

# Project info
target      = "psoc6"
crypto      = "mbedtls"
measurement = "cw308_3v3_CM4"
num_traces  = "80000"
num_samples = "1200"

# CW date string from CW Capture output
date_string = "2018.08.10-10.36.05"

ProjectDir, ProjectFile = os.path.split(os.path.realpath(__file__))

TraceDir = os.path.join(
    "traces",
    target,
    crypto,
    measurement)

CWFilesDir = os.path.join(
    ProjectDir,
    num_samples + "_samples_" + num_traces + "_traces_data",
    "traces")

CWKnownKey = os.path.join(CWFilesDir, date_string + "_knownkey.npy")

# Output dirs
LogDir = os.path.join(ProjectDir, "_log")
ReportDir = os.path.join(ProjectDir, "_report")

# Attack parameters going into jlsca backend
AttackParameters = {
    "--sample_range_low"    : 10,
    "--sample_range_high"   : 1000,
    
    "--fft"                  : "",
    "--fft_ref_start"       : 200,
    "--fft_ref_end"         : 600,
    "--fft_max_shift"       : 100,
    "--fft_min_corval"      : 0.3,
    #"--fft_ref_trace"       : 1,
    
    "--cw_knownkey"         : CWKnownKey,
    #"--show_plots"          : "" ,
    #"--multibit_attack"     : ""
}

# traceNumList is used to test different amounts of traces in the provided data set
# traceNumList = [num_traces,'65536','32768','16384','8194','4096','2048','1024','512','256','128','64']
# traceNumList = ['32000', '16000','8000','4000','2000','1000','500','250','125','75']
# traceNumList = [num_traces]
TraceNumList = ['1000']


SHOW_PLOTS_PYTHON = 1