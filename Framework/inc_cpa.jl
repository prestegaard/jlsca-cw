# load the tools
using Jlsca.Sca
using Jlsca.Trs
using Jlsca.Align
#using Jlsca.Aes

using PyCall
import PyPlot
#using Plots
@pyimport numpy

using ArgParse

#using Distributed
global numTraces
# trsfile identifying the capture, bulky as it is
# (so far have been lazy to automate based on ChipWhisperer config file)
#trsfile = "standard_aes_measure_on_3v3_internal_regulator_on_data/traces/2018.05.16-10.11.16_"

#using Logging

function parse_commandline()
    s = ArgParseSettings()
    @add_arg_table s begin
        # Sample Range Parameters
        "--sample_range_low"
            help = "Trim traces to range"
            arg_type = Int
            default = 1
        "--sample_range_high"
            help = "Trim traces to range"
            arg_type = Int
            default = 0 # Defaults to use all samples

        # FFT Parameters
        "--fft"
            help = "Enable fft"
            action = :store_true

        "--fft_ref_start"
            help = "fft reference start"
            arg_type = Int
            default = 0

        "--fft_ref_end" 
            help = "fft reference end"
            arg_type = Int
            default = 0

        "--fft_max_shift" 
            help = "fft max shift"
            arg_type = Int
            default = 0
        "--fft_min_corval" 
            help = "fft min correlation value"
            arg_type = Float64
            default = 0.0
        "--fft_ref_trace"
            help = "fft reference trace, default 1"
            arg_type = Int
            default = 1   

        # Additional options
        "--show_plots"
            help = "Show plots before, and after alignment"
            action = :store_true
        "--num_traces_to_plot"
            help = "Set number of traces to plot"
            arg_type = Int
            default = 100
        "--multibit_attack"
            help = "Use multibit attack"
            action =:store_true
        "--cw_knownkey"
            help = "CW knownKey file containing key used"
            required = true

        # Trace file in .trs format
        "trs"
            help = "Trace file path, format must be .trs"
            arg_type = String
            required = true
    end

    return parse_args(s)
end

function main()
    args = parse_commandline()
    println("Parsed args in inc_cpa.jl: ")
    for(arg,val) in args
        println("--$arg = $val")
    end

    
    #exit()

    #trsfile = ARGS[1]
    #FFT_ENABLED = parse(Int,ARGS[2])
    #referencestart = parse(Int,ARGS[3])
    #referenceend = parse(Int,ARGS[4])
    #maxShift = parse(Int,ARGS[5])
    #corvalMin = parse(Float64,ARGS[6])
    #sampleLow = parse(Int, ARGS[7])
    #sampleHigh = parse(Int, ARGS[8])
    #multibit = parse(Int, ARGS[9])
    #show_plot = parse(Int, ARGS[10])

    knownKey = numpy.load(args["cw_knownkey"]);

    print("\n*************\n")

    trs = InspectorTrace("$(args["trs"])")


    if args["show_plots"]
        ((data,samples),eof) = readTraces(args["trs"], 1:NUM_TRACES_TO_PLOT)
        fig1 = PyPlot.figure("Before alignment")
        for i in 1:1:NUM_TRACES_TO_PLOT
            PyPlot.plot(samples[i,:])
        end
    end
    #plot(samples[1][1:,:],samples[2][1:,1],samples[3][1:,:]',linewidth=.3) # note the transpose when plotting multiple traces

    numTraces = length(trs)
    println("Number of traces: ", numTraces)
    if args["fft"]
        println("Using FFT: ")
        println("fft_ref_start: ", args["fft_ref_start"])
        println("fft_ref_end: ", args["fft_ref_end"])
        println("fft_max_shift: ", args["fft_max_shift"])
        println("fft_min_corval: ", args["fft_min_corval"])

        # selecting the reference pattern in the first traces
        reference = trs[1][2][args["fft_ref_start"]:args["fft_ref_end"]]
        alignstate = CorrelationAlignFFT(reference, args["fft_ref_start"], args["fft_max_shift"])
        addSamplePass(trs, x -> ((shift,corval) = correlationAlign(x, alignstate); corval > args["fft_min_corval"] ? circshift(x, shift) : Vector{eltype(x)}(0)))
      
        # Ugly hack to find out how many samples are left after FFT filtering
        (_,samples) = trs[1]
        numSamples = length(samples)
        sampleType = eltype(samples)
        #tmp_traces = Array{Float32}(numTraces,numSamples)

        for i in 1:numTraces
            try
                (data,samples) = trs[i]
                #tmp_traces[i,:] = samples
            catch
                print("Number of traces after filter = ", i-1, "\n")
                numTraces = i -1
                #tmpNumTraces = deepcopy(i)
                break
            end
        end

        if args["num_traces_to_plot"] > numTraces
            args["num_traces_to_plot"] = numTraces
        end

        if args["show_plots"] == 1
            ((data2,samples2),eof) = readTraces(trs, 1:NUM_TRACES_TO_PLOT)
            fig2 = PyPlot.figure("After alignment")
            for i in 1:1:NUM_TRACES_TO_PLOT-1
                try
                    PyPlot.plot(samples2[i,:])
                catch
                    println("No more traces left, i = ", i)
                    break
                end
            end
            PyPlot.show()
        end
      
        reset(trs) # Reset conditional averaging but doesn't remove sample passes
    end

    # Remove samples outside interesting area to speed up attack, and sort out non-interesting false positives
    addSamplePass(trs, x -> x[args["sample_range_low"]:args["sample_range_high"]])
    println("Sample range: ", args["sample_range_low"], ":", args["sample_range_high"])




    backward = false
    multibit = false
    hd = false
    lra = false
    condavg = false
    inccpa = true


    println("backward = ", backward)
    println("multibit = ", multibit)
    println("hd = ", hd)
    println("lra = ", lra)
    println("condavg = ", condavg)
    println("inccpa = ", inccpa)



    # Attack
    attack = AesSboxAttack()
    attack.mode = CIPHER
    attack.keyLength = KL128
    attack.direction = FORWARD
    analysis = IncrementalCPA()
    #analysis.leakages = [HW()]
    params = DpaAttack(attack,analysis)
    params.knownKey = knownKey
    params.targetOffsets = collect(1:16)
    params.dataOffset = 1

    #if default
        #params.targetOffsets = [1,6,11,16]
        #params.targetOffsets = [15]
        #params.maximization = GlobalMaximization()
    #end

    if backward
        params.attack.direction = BACKWARD
        params.dataOffset = 17
     end      

    if multibit == 1
        params.analysis.leakages = [Bit(i) for i in 0:7]
    end

    if hd
        params.attack.xor = true  # Hamming Distance
    end

    if condavg
        params.analysis = CPA()
        setPostProcessor(trs, CondAvg(SplitByTracesBlock()))
    end

    if lra
        params.analysis = LRA()
        params.analysis.basisModel = x -> basisModelSingleBits(x, 8)
        setPostProcessor(trs, CondAvg(SplitByTracesBlock()))
    end

    #analysis = LRA() #LRA
    # combine the two in a DpaAttack. The attack field is now also accessible
    # through params.attack, same for params.analysis.

    if inccpa
        #params.analysis = IncrementalCPA()
        # use incremental correlation computation (like in Daredevil or Inspector)
        setPostProcessor(trs, IncrementalCorrelation(SplitByTracesBlock()))
    end

    # run the attack
    println("Running attack with # traces: ", numTraces)
    rankData = sca(trs, params, 1, numTraces)


    key = getKey(params,rankData)
    println("found key: ", key)
    println("known key: ", knownKey)
    println("MATCH ? ", key == knownKey)

    for i in 1:1:16
        if i<=10
        	println("Match on keyByte  ", i-1, " : ", key[i] == knownKey[i])
        else
        	println("Match on keyByte ", i-1, " : ", key[i] == knownKey[i])
        end
    end





    # graceful completion
    popSamplePass(trs)
    popSamplePass(trs)
    close(trs)
end

main()

