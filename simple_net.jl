using MAT
using Winston
using HDF5

############################################################
# Load Bus Data
############################################################

num_predictions = 10

dataset_errors = []

datasets = ["full_routes.mat","full_routes_2.mat"]
for dataset in datasets
  errors = []
  for i in 1:num_predictions
    total_stops = 22
    num_input_stops = 10
    stops_to_predict = 1
    stops_ahead_to_predict = i

    vars = matread(dataset)

    all_data_points = []

    for j in [1:length(vars["time"]);]
        data_point = Dict{String,Any}()
        for key in keys(vars)
            data_point[key] = vars[key][j]
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
    for j in 1:N
      full_route = view(full_routes,:,j)

      # Use deltas from the beginning of the route instead of the actual unix time
      times = convert(Array{Float64},[x["time"]-full_route[1]["time"] for x in full_route])
      deltas = diff(times)

      input_times = deltas[1:num_input_stops]
      offset = sum(deltas[num_input_stops+1:num_input_stops+stops_to_predict-1])
      output_times = [x+offset for x in deltas[num_input_stops+stops_ahead_to_predict:num_input_stops+stops_ahead_to_predict+stops_to_predict-1]]

      input_data[:,j] = input_times
      output_data[:,j] = output_times
    end


    num_training_points = round(Int,N*8/10)
    train_input_data = input_data[:,1:num_training_points]
    train_output_data = output_data[:,1:num_training_points]
    test_input_data = input_data[:,num_training_points+1:end]
    test_output_data = output_data[:,num_training_points+1:end]

    ############################################################
    # Define network
    ############################################################

    using Mocha

    backend = DefaultBackend()
    init(backend)

    data_layer = MemoryDataLayer(batch_size=20, data=Array[train_input_data,train_output_data])
    weight_layer_1 = InnerProductLayer(name="ip1",output_dim=25, tops=[:mid], bottoms=[:data],neuron=Neurons.Sigmoid())
    weight_layer_2 = InnerProductLayer(name="ip2",output_dim=25, tops=[:final], bottoms=[:mid],neuron=Neurons.Sigmoid())
    weight_layer_3 = InnerProductLayer(name="out",output_dim=stops_to_predict, tops=[:pred], bottoms=[:final],neuron=Neurons.Sigmoid())
    loss_layer = SquareLossLayer(name="loss", bottoms=[:pred, :label])

    net = Net("TEST", backend, [loss_layer, weight_layer_1, weight_layer_2, weight_layer_3, data_layer])
    println(net)

    ############################################################
    # Train
    ############################################################

    method = SGD()
    params = make_solver_parameters(method, max_iter=1000, regu_coef=0.0005,
        mom_policy=MomPolicy.Fixed(0.9),
        lr_policy=LRPolicy.Fixed(0.0001))
    solver = Solver(method, params)

    add_coffee_break(solver, TrainingSummary(), every_n_iter=10)
    solve(solver, net)
    Mocha.dump_statistics(solver.coffee_lounge, get_layer_state(net, "loss"), true)


    ############################################################
    # Test
    ############################################################

    data_layer_test = MemoryDataLayer(name="test-data", data=Array[test_input_data,test_output_data], batch_size=100)
    acc_layer = AccuracyLayer(name="test-accuracy", bottoms=[:pred, :label], report_error=true)
    test_net = Net("MNIST-test", backend, [acc_layer, weight_layer_3, weight_layer_2, weight_layer_1, data_layer_test])
    add_coffee_break(solver, ValidationPerformance(test_net), every_n_iter=600)

    solve(solver, net)
    #solve(solver, test_net)



    println(solver.coffee_lounge)
    println(solver.coffee_lounge.statistics["loss-square-loss"])
    push!(errors,collect(values(solver.coffee_lounge.statistics["loss-square-loss"]))[1])




    destroy(net)
    #destroy(test_net)
    shutdown(backend)
  end

  push!(dataset_errors,errors)


end

errors_1 = dataset_errors[1][1:end-1]
errors_2 = dataset_errors[2][1:end-1]
println(mean(errors_1))
println(mean(errors_2))
p=FramedPlot()
setattr(p,"title","RMSE vs bus stop number");
setattr(p,"xlabel","bus stop number");
setattr(p,"ylabel","RMSE");
c1 = Curve(1:length(errors_1),[sqrt(x) for x in errors_1], "color","blue")
c2 = Curve(1:length(errors_2),[sqrt(x) for x in errors_2], "color","red")
add(p,c1)
add(p,c2)
setattr(c1, "label", "Same day");
setattr(c2, "label", "Different day");
MyLegend=Legend(0.5, 0.9, [c1,c2])
add(p,MyLegend)
savefig(p,string("RMSEs.png"))
