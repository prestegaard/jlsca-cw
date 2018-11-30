# load the tools
using Jlsca.Sca
using Jlsca.Trs
using Jlsca.Align
#using Jlsca.Aes

using PyCall
import PyPlot
#using Plots
@pyimport numpy

NUM_TRACES_TO_PLOT = 100
#using Distributed

# prefix identifying the capture, bulky as it is
# (so far have been lazy to automate based on ChipWhisperer config file)
#prefix = "standard_aes_measure_on_3v3_internal_regulator_on_data/traces/2018.05.16-10.11.16_"
prefix = ARGS[1]
FFT_ENABLED = parse(Int,ARGS[3])
referencestart = parse(Int,ARGS[4])
referenceend = parse(Int,ARGS[5])
maxShift = parse(Int,ARGS[6])
corvalMin = parse(Float64,ARGS[7])
sampleLow = parse(Int, ARGS[8])
sampleHigh = parse(Int, ARGS[9])
show_plot = parse(Int, ARGS[10])

knownKey = numpy.load("cw_knownkey.npy");

print("\n*************\n")


# Export a minimal readable ChipWhisperer project
function exportCwp(name, traces, textin, textout)
    
    (numTraces, numSamples) = size(traces)
    (numInputs,) = size(textin)
    (numOutputs,) = size(textout)
    
    # Minimal correctness check
    if numTraces != numInputs || numTraces != numOutputs
        error("Input data size mismatch")
    end
    
    # Create directory structure
    # Existing project with the same name will be overwritten
    #  without a full cleanup, supersorry
    if !isdir(name)
        mkpath("$name/traces")
    else
        if !isdir("$name/traces")
            mkdir("$name/traces")
        end
    end

    # Write a universal project config file template
    cwpConfig = """
    [Trace Management]
    tracefile0=traces/config.cfg
    enabled0=True"""
    f = open("$name/config.cwp", "w")
    println(f, cwpConfig)
    close(f)
    
    # Write the main data files
    numpy.save("$name/traces/traces.npy", traces)
    numpy.save("$name/traces/textin.npy", textin)
    numpy.save("$name/traces/textout.npy", textout)

    # Write traceset config file
    f = open("$name/traces/config.cfg", "w")
    println(f, "[Trace Config]")
    println(f, "numTraces = $numTraces")
    println(f, "format = native")
    println(f, "numPoints = $numSamples")
    println(f, "prefix = ")
    println(f, """notes = "AckPattern: Basic (Key=Fixed:2B 7E 15 16 28 AE D2 A6 AB F7 15 88 09 CF 4F 3C, Plaintext=Random); Aux: set_prefixbefore_capturebefore_tracebefore_armafter_armafter_traceafter_capture" """)
    close(f)

end




trs = InspectorTrace("$(prefix)")

fig3 = PyPlot.figure("from trs before filter")
PyPlot.plot(trs[1][2][:])
PyPlot.plot(trs[12000][2][:])
PyPlot.show()



# read 10 traces# read  
if show_plot == 2
    ((data,samples),eof) = readTraces(trs, 1:NUM_TRACES_TO_PLOT)
    fig1 = PyPlot.figure("Before alignment")
    for i in 1:1:NUM_TRACES_TO_PLOT
        a = 0
        PyPlot.plot(samples[i,:])
    end
    #PyPlot.show()
end

numTraces = length(trs)
if FFT_ENABLED == 1
    
    
    # selecting the reference pattern in the first traces
    print("USING FFT: \n")
    print("referencestart: ", referencestart, "\n")
    print("referenceend: ", referenceend, "\n")
    print("maxShift: ", maxShift, "\n")
    print("corvalMin: ", corvalMin, "\n")

    reference = trs[1][2][referencestart:referenceend]
    alignstate = CorrelationAlignFFT(reference, referencestart, maxShift)
    addSamplePass(trs, x -> ((shift,corval) = correlationAlign(x, alignstate); corval > corvalMin ? circshift(x, shift) : Vector{eltype(x)}(0)))

    #reference = trs[1][2][1000:1200]
    #alignstate = CorrelationAlignFFT(reference, 1000, maxShift)
    #addSamplePass(trs, x -> ((shift,corval) = correlationAlign(x, alignstate); corval > corvalMin ? circshift(x, shift) : Vector{eltype(x)}(0)))


   #reference = trs[1][2][200:300]
   #alignstate = CorrelationAlignFFT(reference, 200, maxShift)
   #addSamplePass(trs, x -> ((shift,corval) = correlationAlign(x, alignstate); corval > corvalMin ? circshift(x, shift) : Vector{eltype(x)}(0)))

    #referencestart = 500
    #referenceend = 800
    #maxShift = 400
    #corvalMin = 0.3
    #reference = trs[1][2][referencestart:referenceend]
    #alignstate = CorrelationAlignFFT(reference, referencestart, maxShift)
    #addSamplePass(trs, x -> ((shift,corval) = correlationAlign(x, alignstate); corval > corvalMin ? circshift(x, shift) : Vector{eltype(x)}(0)))
    # find number of approved samples for i in 1:numTraces
    (_,samples) = trs[1]
    numSamples = length(samples)
    sampleType = eltype(samples)
    tmp_traces = Array{sampleType}(numTraces,numSamples)
    for i in 1:numTraces
        try
            (data,samples) = trs[i]
            tmp_traces[i,:] = samples
        catch
            print("Number of traces after filter = ", i, "\n")
            numTraces = i
            break
        end

    end
   
    # read 10 traces
    if show_plot == 1
        ((data2,samples2),eof) = readTraces(trs, 1:NUM_TRACES_TO_PLOT)
        fig2 = PyPlot.figure("After alignment")
        for i in 1:1:NUM_TRACES_TO_PLOT-1
            try
                PyPlot.plot(samples2[i,:])
            catch
                print("No more traces left, i = ", i, "\n")
                break
            end
            if (i % 3000) == 0
                print("i = ", i, "\n")
                fig2 = PyPlot.figure("After alignment")
            end
        end
        PyPlot.show()
    end
end

# throwing away samples to speed up the LRA analysis (removing this pass does not affect the attack outcome)
addSamplePass(trs, x -> x[sampleLow:sampleHigh])
reset(trs) # Reset conditional averaging but doesn't remove sample passes

# read traceset and get it parameters
# we assume that number of data bytes is 32, of which first 16 are input and last 16 are output
(_,samples) = trs[1]
numSamples = length(samples)
sampleType = eltype(samples)

fig3 = PyPlot.figure("from trs after filter")
PyPlot.plot(trs[1][2][:])
PyPlot.plot(trs[12000][2][:])
PyPlot.show()


fig3 = PyPlot.figure("from trs")
for i in 1:1:NUM_TRACES_TO_PLOT-1
    try
        PyPlot.plot(trs[i][2][:])
    catch
        print("No more traces left, i = ", i, "\n")
        break
    end
end
PyPlot.show()



# preallocate arrays
traces = Array{sampleType}(numTraces,numSamples)
textin = Array{UInt8}(numTraces,16)
textout = Array{UInt8}(numTraces,16)


# populate arrays from trs
for i in 1:numTraces-1
    try
        (data,samples) = trs[i]
        traces[i,:] = samples
        textin[i,:] = data[1:16]
        textout[i,:] = data[17:32]
    catch
        print("No more traces left, i = ", i, "\n")
        break
    end

end
close(trs)

# export to CWP
(projectName, ) = splitext(prefix)
exportCwp("$(projectName)-aligned-cwp", traces, textin, textout)



# graceful completion
popSamplePass(trs)
popSamplePass(trs)
close(trs)
