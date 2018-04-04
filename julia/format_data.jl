using MAT
using HDF5
############################################################
# Load Bus Data
############################################################
function get_routes(file, training_proportion, num_input_stops, stops_ahead_to_predict, stops_to_predict)
  total_stops = 22
  vars = matread(file)
  print(keys(vars))
  all_data_points = Array{Dict{String,Any}}(length(vars["time"]))
  for j in [1:length(vars["time"]);]
    data_point = Dict{String,Any}()
    for key in keys(vars)
      data_point[key] = vars[key][j]
    end
    all_data_points[j] = data_point
  end
  full_routes = reshape(all_data_points,total_stops,round(Int,length(all_data_points)/total_stops))
  N = size(full_routes)[2]
  input_data = zeros(num_input_stops,N)
  output_data = zeros(stops_to_predict,N)
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
  num_training_points = round(Int,N*training_proportion)
  train_input_data = input_data[:,1:num_training_points]
  train_output_data = output_data[:,1:num_training_points]
  test_input_data = input_data[:,num_training_points+1:end]
  test_output_data = output_data[:,num_training_points+1:end]
  output = Dict{String,Any}()
  output["train_input_data"] = train_input_data
  output["train_output_data"] = train_output_data
  output["test_input_data"] = test_input_data
  output["test_output_data"] = test_output_data
  return output
end
