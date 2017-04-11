using MAT
using HDF5
using Mocha
vars = matread("full_routes.mat")

all_data_points = []

# Separate the data into chunks, which represent periods of time
# where buses come at regular intervals

for i in [1:length(vars["time"]);]
    data_point = Dict{String,Any}()
    for key in keys(vars)
        data_point[key] = vars[key][i]
    end
    push!(all_data_points,data_point)
end

full_routes = reshape(all_data_points,22,round(Int,length(all_data_points)/22))
#data = Array{Array{Float64}}[]
data =[]
labels = []
for i in 1:size(full_routes,2)
  full_route = view(full_routes,:,i)
  route_ids = [x["stop_idx"] for x in full_route]
  times = convert(Array{Float64},[x["time"]-full_route[1]["time"] for x in full_route])
  input_times = times[1:length(times)-1]
  output_times = [times[end]]
  push!(data,input_times)
  push!(labels,output_times)
end

data = convert(Array{Array{}},data)
labels = convert(Array{Array{}},labels)
input_data = []
push!(input_data,data)
push!(input_data,labels)
input_data = convert(Array{Array{}},input_data)
println(input_data)

println(length(input_data))

input_layer =  MemoryDataLayer(name="train-data",data=input_data,batch_size=4)
fc1   = InnerProductLayer(name="ip1",output_dim=1,neuron=Neurons.ReLU(),bottoms=[:data],tops=[:ip1])
hl = SquareLossLayer(bottoms=[:ip1,:label])

backend = DefaultBackend()
init(backend)
common_layers = [fc1]
net = Net("Test", backend, [input_layer, common_layers..., hl])
