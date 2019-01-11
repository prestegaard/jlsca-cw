import os
import importlib.util
import logging
import Framework.Utility as Utility
import Framework.JlscaBruteForceCalculation as JlscaBruteForceCalculation
from python_log_indenter import IndentedLoggerAdapter

logger = IndentedLoggerAdapter(logging.getLogger())


def cw_to_trs(root_dir, cw_dir, cw_date_string, trs_file, num_traces_to_test):
    cmd = "julia "
    cmd += os.path.join(root_dir, 'Framework', 'cw_to_trs.jl') + " "
    cmd += "--cw_date_string {} ".format(cw_date_string)
    cmd += "--cw_trace_location {} ".format(cw_dir)
    cmd += "--num_traces {} ".format(num_traces_to_test)
    cmd += trs_file
    Utility.execute(cmd)

def attack_inc_cpa(root_dir, trs_file, attack_params, jlsca_log_file):
    cmd = "julia" + " "
    cmd += os.path.join(root_dir, 'Framework', 'inc_cpa.jl') + " "
    for key, value in attack_params.items():
        cmd += str(key)+ " "
        cmd += str(value) + " "
    cmd += trs_file
    Utility.execute(cmd, jlsca_log_file)

def jlsca_analysis(root_dir, ProjectDir, local_setup):
    logger = IndentedLoggerAdapter(logging.getLogger())
    logger.add()
    # Load LocalSetup from user input
    spec = importlib.util.spec_from_file_location(local_setup, os.path.join(os.getcwd(), local_setup))
    LocalSetup = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(LocalSetup)
    logger.info("Using parameters from LocalSetup:")
    logger.add()
    for key, value in LocalSetup.AttackParameters.items():
        logger.info(key + " " + str(value))
    logger.sub()
    # Prepare cw files to trs files if not already converted
    for num_traces_to_test in LocalSetup.TraceNumList:
        # Trace file to be generated and used in attack
        trs_file = os.path.join(
            LocalSetup.TraceDir,
            LocalSetup.num_samples + "_samples_" + num_traces_to_test + "_traces_data.trs")

        # Log file to be generated from attack and used in brute force calculation
        jlsca_log_file = os.path.join(
            LocalSetup.ProjectDir,
            '_log',
            'jlsca_' + num_traces_to_test + '_traces.log'
        )
        logger.info("Jlsca attack using {:>6} traces:".format(num_traces_to_test))
        logger.add()
        if not os.path.isfile(trs_file):
            logger.info("Converting CW project to JlSca trs format")
            cw_to_trs(root_dir, LocalSetup.CWFilesDir, LocalSetup.date_string, trs_file, num_traces_to_test)
            logger.info("CW files converted into .trs file")

        logger.info("Running attack Incremental Correlation Power Analysis using Julia")
        attack_inc_cpa(root_dir, trs_file, LocalSetup.AttackParameters, jlsca_log_file)
        logger.info("Attack Incremental Correlation Power Analysis completed")

        logger.info("Running calculation on number of guesses needed based on brute force algorithm")
        num_of_guesses = JlscaBruteForceCalculation.calculate(jlsca_log_file,
                                                              LocalSetup.CWKnownKey,
                                                              "--show-plots" in LocalSetup.AttackParameters)

        logger.info("Number of guesses calculation completed")
        logger.info("Number of guesses needed using {:>6} traces: {}".format(num_traces_to_test, num_of_guesses))
        logger.sub()
    logger.sub()