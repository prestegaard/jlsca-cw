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

sampleLow =     parse(Int, ARGS[2])
sampleHigh =    parse(Int, ARGS[3])
maxShift =      parse(Int, ARGS[4])
corvalMin =     parse(Float64, ARGS[5])
window  =       parse(Int, ARGS[6])
multibit =      parse(Int, ARGS[7])
knownKey = numpy.load("cw_knownkey.npy");

print("\n*************\n")

trs = InspectorTrace("$(prefix)")


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
  

if multibit == 1
    params.analysis.leakages = [Bit(i) for i in 0:7]
    println("multibit = ", multibit)
end



# run the attack


numberOfTraces = length(Main.trs)
addSamplePass(trs, x -> x[sampleLow:sampleHigh])
exepectedSamplePoints = [36,104,128,78,34,81,146,54,21,114,132,74,13,109,160,44]

for i in 1:1:16

    referencestart = exepectedSamplePoints[i] - window
    if referencestart <= 0
        referencestart = 1
    end
    referenceend = exepectedSamplePoints[i] + window

    reference = trs[1][2][referencestart:referenceend]
    alignstate = CorrelationAlignFFT(reference, referencestart, maxShift)
    addSamplePass(trs, x -> ((shift,corval) = correlationAlign(x, alignstate); corval > corvalMin ? circshift(x, shift) : Vector{eltype(x)}(0)))

    params.targetOffsets = [i]

    addSamplePass(trs, x -> x[referencestart:referenceend])

    setPostProcessor(trs, IncrementalCorrelation(SplitByTracesBlock()))
    rankData = sca(DistributedTrace(), params, 1, numberOfTraces)

    key = getKey(params,rankData)
    print("\nfound key: ", key)
    print("\nknown key: ", knownKey)
    
    popSamplePass(trs)
    popSamplePass(trs)
end

popSamplePass(trs)
close(trs)
