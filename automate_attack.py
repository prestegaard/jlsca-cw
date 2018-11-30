import subprocess, os

os.putenv('JULIA_NUM_THREADS', '6')
os.popen("SET")
print ("### Set JULIA_NUM_THREADS=6")

# Traces should be stored in traces/target/crypto/measurement

## Local setup
cw_knownkey = "cw_knownkey.npy"
target      = "psoc6"
crypto      = "mbedtls"
measurement = "cw308_3v3_CM4"
num_traces  = "80000"
num_samples = "1200"
date_string = "2018.08.10-10.36.05" 

trace_location = os.path.join("traces",target,crypto,measurement,num_samples+"_samples_"+num_traces+"_traces_data","traces", date_string)
log_location = os.path.join("log",target,crypto,measurement)
results_log_file = os.path.join(log_location, 'results_brute_force.log')

if not os.path.exists(log_location):
    os.makedirs(log_location)

SKIP_TRS_GENERATION = 0
ALIGN = 0
FFT_ENABLED = 1


#Samples to FFT aligning referenced new bordes from sample trim
FFT_reference_start = 200
FFT_reference_stop =  600
FFT_max_shift = 100
FFT_corVal_min = 0.3
FFT_window = 30 # Only for specific MBEDTLS attack

#Trim sample range
Sample_low = 10  
Sample_high = 1000 


attack = 'inc_cpa'
normal_attack = True
multibit_attack = 0

if multibit_attack:
  attack = 'multibit'

MBEDTLS_ATTACK = False
if MBEDTLS_ATTACK:
  normal_attack = False

SHOW_PLOTS_JLSCA = 1
SHOW_PLOTS_PYTHON = 1

# Prepare results file with new test params
result_file = open(results_log_file, 'a')
test_param_str = "New test {} with params: ".format(attack)

  
test_param_str += "from{}_to{}".format(Sample_low, Sample_high)

if FFT_ENABLED and not MBEDTLS_ATTACK:
  test_param_str +=  "with_fft_start{}_end{}_shift{}_corval{}_from{}_to{}_{}".format(
    FFT_reference_start, \
    FFT_reference_stop, \
    FFT_max_shift, \
    FFT_corVal_min, \
    Sample_low, \
    Sample_high, \
    attack)

if MBEDTLS_ATTACK:
  test_param_str += "mbedtls_Specific_with_shift{}_corval{}_window{}_from{}_to{}_{}".format(
    FFT_max_shift, \
    FFT_corVal_min, \
    FFT_window, \
    Sample_low, \
    Sample_high, \
    attack)

result_file.write(test_param_str)
result_file.write("\n")
result_file.close()


# traceNumList is used to test different amounts of traces in the provided data set
#traceNumList = [num_traces,'65536','32768','16384','8194','4096','2048','1024','512','256','128','64']
#traceNumList = ['32000', '16000','8000','4000','2000','1000','500','250','125','75']
#traceNumList = [num_traces]
traceNumList = ['1000']
if ALIGN:
  print ("### Align and convert trs to cwp")
  trs_file = os.path.join("traces",target,crypto,measurement,num_samples+"_samples_"+num_traces+"_traces_data.trs")
  #cmd = "julia inc_cpa.jl {} {} {} {} {} {} {} {} {} {}".format(
  julia_dir = os.path.join("C:/","","Users","hapr","AppData","Local","Julia-0.6.4","bin","julia.exe")
  #julia_dir = "julia"
  cmd = "{} align_and_convert_to_cwp.jl {} {} {} {} {} {} {} {} {} {}".format(
      julia_dir, \
      trs_file, \
      num_traces, 
      FFT_ENABLED, \
      FFT_reference_start, \
      FFT_reference_stop, \
      FFT_max_shift, \
      FFT_corVal_min, \
      Sample_low, \
      Sample_high, \
      SHOW_PLOTS_JLSCA)
  print ("### cmd: {}".format(cmd))
  subprocess.call(cmd)
  exit()

for traceNum in traceNumList:
  trs_file = os.path.join("traces",target,crypto,measurement,num_samples+"_samples_"+traceNum+"_traces_data.trs")
  if not SKIP_TRS_GENERATION:
    print ("### Converting CW project to JlSca trs format")
    cmd = "julia cw_to_jlsca.jl {} {} {}".format(
      trace_location, \
      trs_file, \
      traceNum)
    print ("### cmd: {}".format(cmd))
    subprocess.call(cmd)
  
  logFileAttack = os.path.join(log_location, "{}_samples_{}_traces_{}_jlsca.log".format(num_samples, traceNum, attack))
  
  if normal_attack:
    print ("### Execute attack Incremental Correlation Power Analysis")
    #julia_dir = os.path.join("C:/","","Users","hapr","AppData","Local","Julia-0.6.4","bin","julia.exe")
    julia_dir = "julia"
    cmd = "{} inc_cpa.jl {} {} {} {} {} {} {} {} {} {}".format(
        julia_dir, \
        trs_file, \
        FFT_ENABLED, \
        FFT_reference_start, \
        FFT_reference_stop, \
        FFT_max_shift, \
        FFT_corVal_min, \
        Sample_low, \
        Sample_high, \
        multibit_attack, \
        SHOW_PLOTS_JLSCA)

    if FFT_ENABLED:
      path, filename = os.path.split(logFileAttack)
      filename = filename.replace("_{}_jlsca.log".format(attack), "_with_fft_start{}_end{}_shift{}_corval{}_from{}_to{}_{}_jlsca.log".format(
        FFT_reference_start, \
        FFT_reference_stop, \
        FFT_max_shift, \
        FFT_corVal_min, \
        Sample_low, \
        Sample_high, \
        attack))
      logFileAttack = os.path.join(path, filename)
    
  if MBEDTLS_ATTACK:
    print ("### Execute attack MBED TLS specific incremental Correlation Power Analysis")
    julia_dir = os.path.join("C:/","","Users","hapr","AppData","Local","Julia-0.6.4","bin","julia.exe")
    cmd = "{} inc_cpa_mbedtls_specific.jl {} {} {} {} {} {} {} ".format(
      julia_dir, \
      trs_file, \
      Sample_low, \
      Sample_high, \
      FFT_max_shift, \
      FFT_corVal_min, \
      FFT_window, \
      multibit_attack)

    path, filename = os.path.split(logFileAttack)
    filename = filename.replace("_{}_jlsca.log".format(attack), "_MBEDTLS_SPECIAL_shift{}_corval{}_from{}_to{}_windows{}_{}_jlsca.log".format(
      FFT_max_shift, \
      FFT_corVal_min, \
      Sample_low, \
      Sample_high, \
      FFT_window, \
      attack))
    logFileAttack = os.path.join(path, filename)

  f = open(logFileAttack, "w")
  print ("### cmd: {}".format(cmd))
  subprocess.call(cmd, stdout=f)
  f.close()
  f = open(logFileAttack, "r")
  for line in f:
    if "target: 1" in line:
        break
    print line,
  f.close()

  print ("### Parse logs and execute brute force attack")
  cmd = "python3 brute_force.py -i {} -k {} -p {}".format(logFileAttack, cw_knownkey, SHOW_PLOTS_PYTHON)

  path, filename = os.path.split(logFileAttack)
  filename = filename.replace("_jlsca.log", "_results.log")
  logFileBruteForce = os.path.join(path, filename)
  f = open(logFileBruteForce, "w")
  print ("### cmd: {}".format(cmd))
  subprocess.call(cmd, stdout=f)
  f.close()
  f = open(logFileBruteForce, "r")
  for line in f:
   if "Fill out global list G" in line:
       break
   print line,
  f.close()
  
  
  #print ("### Create results file from all attacks")
  #cmd = "python create_results_file.py --log_dir {}".format(log_location)

  print ("### Append results file from all attacks")
  cmd = "python append_results_file.py --result_log {} --attack_log {}".format(results_log_file, logFileBruteForce)
  print ("### cmd: {}".format(cmd))
  subprocess.call(cmd)


result_file = open(results_log_file, 'a')
result_file.write("\n")
result_file.close()