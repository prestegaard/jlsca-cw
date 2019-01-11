import subprocess
import os
import argparse
import importlib.util
import time
import logging
import Framework.JlscaAnalysis as JlscaAnalysis
from Framework.Utility import WrappedFixedIndentingLog as WrappedFormatting
from python_log_indenter import IndentedLoggerAdapter


root_dir, root_file = os.path.split(os.path.realpath(__file__))


# Fixed paths for toolchain
#JuliaIncCpaAttack = os.path.join(root_dir, "Framework", "inc_cpa.jl")
#JuliaCwToTrs = os.path.join(root_dir, "Framework", "cw_to_trs.jl")


def parse_command_line():

    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--local_setup',      action='store',      help="Project LocalSetup file")
    parser.add_argument('-v', '--verbose',          action='store_true', help="Enable verbose printing to log")
    return parser.parse_args()

def logger_setup(ProjectDir, args):
    # Output dirs
    LogDir = os.path.join(ProjectDir, "_log")
    ReportDir = os.path.join(ProjectDir, "_report")

    # Create log and report directories  if necessary
    if not os.path.exists(LogDir):
        os.makedirs(LogDir)

    if not os.path.exists(ReportDir):
        os.makedirs(ReportDir)

    timestr = time.strftime("%Y%m%d-%H%M%S")
    #logfile = os.path.join(LogDir, "analysis-{}.log".format(timestr))
    logfile = os.path.join(LogDir, "_log.log")

    logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")
    rootLogger =logging.getLogger()
    #rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.DEBUG)

    fileHandler = logging.FileHandler(logfile)
    fileHandler.setFormatter(logFormatter)
    fileHandler.setLevel(logging.DEBUG)
    rootLogger.addHandler(fileHandler)

    consoleHandler = logging.StreamHandler()
    #consoleHandler.setFormatter(logFormatter)
    consoleHandler.setFormatter(WrappedFormatting(fmt='%(asctime)-8s %(levelname)-8s %(message)s',
                                                  datefmt='%H:%M:%S',
                                                  width=150,
                                                  indent=18))
    if args.verbose:
        consoleHandler.setLevel(logging.DEBUG)
    else:
        consoleHandler.setLevel(logging.INFO)
    rootLogger.addHandler(consoleHandler)

def main():
    args = parse_command_line()

    # Load LocalSetup from user input
    spec = importlib.util.spec_from_file_location(args.local_setup, os.path.join(os.getcwd(), args.local_setup))
    LocalSetup = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(LocalSetup)

    # Setup and start logging
    logger_setup(LocalSetup.ProjectDir, args)
    logger = logging.getLogger()

    # Prepare for Julia execution
    logger.info("Preparing OS Env to run Julia with 8 cores")
    logger.debug("Calling OS: SET JULIA_NUM_THREADS=8")
    os.putenv('JULIA_NUM_THREADS', '8')

    logger.info("Running JLSCA analysis")
    # Select attack backend, at some point use LocalSetup?
    JlscaAnalysis.jlsca_analysis(root_dir, LocalSetup.ProjectDir, args.local_setup)



    # Exit program
    logger.info("End of program")
    exit(0)
'''
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

for traceNum in traceNumList:
  trs_file = os.path.join("traces",target,crypto,measurement,num_samples+"_samples_"+traceNum+"_traces_data.trs")

  
  logFileAttack = os.path.join(log_location, "{}_samples_{}_traces_{}_jlsca.log".format(num_samples, traceNum, attack))
  
  if normal_attack:
    a = 2
    
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


  for line in f:
    if "target: 1" in line:
        break
    print(line)
  f.close()

  print ("### Parse logs and execute brute force attack")
  cmd = "python3 JlscaBruteForceCalculation.py -i {} -k {} -p {}".format(logFileAttack, cw_knownkey, SHOW_PLOTS_PYTHON)

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
   print(line)
  f.close()
  
  
  #print ("### Create results file from all attacks")
  #cmd = "python create_results_file.py --log_dir {}".format(log_location)

  print ("### Append results file from all attacks")
  cmd = "python append_results_file.py --result_log {} --attack_log {}".format(results_log_file, logFileBruteForce)
  print ("### cmd: {}".format(cmd))
  subprocess.call(cmd)


result_file = open(results_log_file, 'a')
result_file.write("\n")
result_file.close()'' \

'''

if __name__ == "__main__":
    # execute only if run as a script
    main()