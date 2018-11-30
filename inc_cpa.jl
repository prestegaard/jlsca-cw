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

# trsfile identifying the capture, bulky as it is
# (so far have been lazy to automate based on ChipWhisperer config file)
#trsfile = "standard_aes_measure_on_3v3_internal_regulator_on_data/traces/2018.05.16-10.11.16_"
trsfile = ARGS[1]
FFT_ENABLED = parse(Int,ARGS[2])
referencestart = parse(Int,ARGS[3])
referenceend = parse(Int,ARGS[4])
maxShift = parse(Int,ARGS[5])
corvalMin = parse(Float64,ARGS[6])
sampleLow = parse(Int, ARGS[7])
sampleHigh = parse(Int, ARGS[8])
multibit = parse(Int, ARGS[9])
show_plot = parse(Int, ARGS[10])

knownKey = numpy.load("cw_knownkey.npy");

print("\n*************\n")

trs = InspectorTrace("$(trsfile)")



if show_plot == 1
    ((data,samples),eof) = readTraces(trs, 1:NUM_TRACES_TO_PLOT)
    fig1 = PyPlot.figure("Before alignment")
    for i in 1:1:NUM_TRACES_TO_PLOT
        PyPlot.plot(samples[i,:])
    end
end
#plot(samples[1][1:,:],samples[2][1:,1],samples[3][1:,:]',linewidth=.3) # note the transpose when plotting multiple traces

numTraces = length(trs)
println("Number of traces: ", numTraces)
if FFT_ENABLED == 1
    println("Using FFT: ")
    println("referencestart: ", referencestart)
    println("referenceend: ", referenceend)
    println("maxShift: ", maxShift)
    println("corvalMin: ", corvalMin)

    # selecting the reference pattern in the first traces
    reference = trs[1][2][referencestart:referenceend]
    alignstate = CorrelationAlignFFT(reference, referencestart, maxShift)
    addSamplePass(trs, x -> ((shift,corval) = correlationAlign(x, alignstate); corval > corvalMin ? circshift(x, shift) : Vector{eltype(x)}(0)))
  
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
            global numTraces = i -1
            #tmpNumTraces = deepcopy(i)
            break
        end
    end

    if NUM_TRACES_TO_PLOT > numTraces
        NUM_TRACES_TO_PLOT = numTraces
    end

    if show_plot == 1
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
addSamplePass(trs, x -> x[sampleLow:sampleHigh])
print("Sample range: ", sampleLow, ":", sampleHigh, "\n")




backward = false
#multibit = true
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
rankData = sca(DistributedTrace(), params, 1, numTraces)


key = getKey(params,rankData)
print("\nfound key: ", key)
print("\nknown key: ", knownKey)
print("\nMATCH ? ", key == knownKey)

print("\n\n####")
for i in 1:1:16
    if i<=10
    	print("\nMatch on keyByte  ", i-1, " : ", key[i] == knownKey[i])
    else
    	print("\nMatch on keyByte ", i-1, " : ", key[i] == knownKey[i])
    end
end


# graceful completion
popSamplePass(trs)
popSamplePass(trs)
close(trs)
