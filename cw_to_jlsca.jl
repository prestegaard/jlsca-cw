# load the tools
using Jlsca.Sca
using Jlsca.Trs
using Jlsca.Align
using Jlsca.Aes
using PyCall
#using PyPlot.plot,PyPlot.figure

@pyimport numpy

# prefix identifying the capture, bulky as it is
# (so far have been lazy to automate based on ChipWhisperer config file)
#prefix = "standard_aes_measure_on_3v3_internal_regulator_on_data/traces/2018.05.16-10.11.16_"
trace_location = ARGS[1]
trs_file = ARGS[2]
num_traces = parse(Int,ARGS[3])

# read the data from chipwhisperer capture
samples = numpy.load("$(trace_location)_traces.npy");
input = numpy.load("$(trace_location)_textin.npy");
output = numpy.load("$(trace_location)_textout.npy");
knownKey = numpy.load("$(trace_location)_knownKey.npy");

# get sizes# get s 
print("\n")
print(size(samples))
print("\n")
print(size(input))
print("\n")
print(size(output))
print("\n")
print("Known key: ", knownKey)
print("\n")




numberOfSamples = size(samples)[2]
dataSpace = size(input)[2] + size(output)[2]
sampleType = Float32;

# create and save the trs
trs = InspectorTrace("$(trs_file)", dataSpace, sampleType, numberOfSamples)
for t in 1:num_traces
 	trs[t] = (vcat(input[t,:],output[t,:]), map(Float32, samples[t,:]))
end
# 
close(trs)