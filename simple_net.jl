using MAT
using HDF5

############################################################
# Load Bus Data
############################################################

total_stops = 22
num_input_stops = 15
stops_to_predict = 3
num_predictions = 1

vars = matread("full_routes.mat")

all_data_points = []

for i in [1:length(vars["time"]);]
    data_point = Dict{String,Any}()
    for key in keys(vars)
        data_point[key] = vars[key][i]
    end
    push!(all_data_points,data_point)
end

full_routes = reshape(all_data_points,total_stops,round(Int,length(all_data_points)/total_stops))

N = size(full_routes)[2]
#N=50

println("N: ",N)
input_data = zeros(num_input_stops,N)
output_data = zeros(stops_to_predict,N)

labels = []
for i in 1:N
  full_route = view(full_routes,:,i)

  # Use deltas from the beginning of the route instead of the actual unix time
  times = convert(Array{Float64},[x["time"]-full_route[1]["time"] for x in full_route])
  deltas = diff(times)

  input_times = deltas[1:num_input_stops]
  output_times = deltas[num_input_stops+1:num_input_stops+stops_to_predict]

  input_data[:,i] = input_times
  output_data[:,i] = output_times
end

############################################################
# Define network
############################################################

using Mocha

backend = DefaultBackend()
init(backend)

data_layer = MemoryDataLayer(batch_size=16, data=Array[input_data,output_data])
weight_layer_1 = InnerProductLayer(name="ip1",output_dim=50, tops=[:mid], bottoms=[:data],neuron=Neurons.ReLU())
weight_layer_2 = InnerProductLayer(name="ip2",output_dim=stops_to_predict, tops=[:pred], bottoms=[:mid],neuron=Neurons.ReLU())
loss_layer = SquareLossLayer(name="loss", bottoms=[:pred, :label])

net = Net("TEST", backend, [loss_layer, weight_layer_1, weight_layer_2, data_layer])
println(net)

############################################################
# Solve
############################################################

method = SGD()
params = make_solver_parameters(method, max_iter=10000, regu_coef=0.0005,
    mom_policy=MomPolicy.Fixed(0.9),
    lr_policy=LRPolicy.Fixed(0.0001))
solver = Solver(method, params)

add_coffee_break(solver, TrainingSummary(), every_n_iter=10)
solve(solver, net)
Mocha.dump_statistics(solver.coffee_lounge, get_layer_state(net, "loss"), true)
shutdown(backend)
