# load the tools
using Jlsca.Sca
using Jlsca.Trs
using Jlsca.Align
using Jlsca.Aes
using PyCall
#using PyPlot.plot,PyPlot.figure

@pyimport numpy

using ArgParse


function parse_commandline()
    s = ArgParseSettings()
    @add_arg_table s begin
        "--cw_date_string"
            help = "CW date string"
            arg_type = String
            required = true

        "--cw_trace_location"
            help = "CW trace directory"
            arg_type = String
            required = true

        "--num_traces"
            help = "Num traces to include in trs file"
            arg_type = Int
            required = true

        "trs"
            help = "Trace file output, must include path"
            arg_type = String
            required = true
    end

    return parse_args(s)
end

function main()
    # prefix identifying the capture, bulky as it is
    # (so far have been lazy to automate based on ChipWhisperer config file)
    #prefix = "standard_aes_measure_on_3v3_internal_regulator_on_data/traces/2018.05.16-10.11.16_"
    args = parse_commandline()
    println("JLSCA: Parsed args in cw_to_trs.jl: ")
    for(arg,val) in args
        println("JLSCA: --$arg = $val")
    end


    # read the data from chipwhisperer capture
    samples = numpy.load("$(args["cw_trace_location"])/$(args["cw_date_string"])_traces.npy");
    input = numpy.load("$(args["cw_trace_location"])/$(args["cw_date_string"])_textin.npy");
    output = numpy.load("$(args["cw_trace_location"])/$(args["cw_date_string"])_textout.npy");
    knownKey = numpy.load("$(args["cw_trace_location"])/$(args["cw_date_string"])_knownKey.npy");

    print("Known key: ", knownKey)
    print("\n")

    numberOfSamples = size(samples)[2]
    dataSpace = size(input)[2] + size(output)[2]
    sampleType = Float32;

    # create and save the trs
    trs = InspectorTrace("$(args["trs"])", dataSpace, sampleType, numberOfSamples)
    for t in 1:args["num_traces"]
        trs[t] = (vcat(input[t,:],output[t,:]), map(Float32, samples[t,:]))
    end
    #
    close(trs)
end

main()