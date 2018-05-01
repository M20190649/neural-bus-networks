using JSON

DAYS_IN_WEEK = 7
DAYS_OF_WEEK = 0:6
HOURS_OF_DAY = 0:23
HOURS_IN_DAY = 24

function contiguous(x, start)
  idx = 0
  started = false
  has_key = haskey(x,string(start))
  if !has_key
    return 0
  end
  for i in start:28
    has_key = haskey(x,string(i))
    if has_key
      if !started
        started = true
      end
      idx+=1
    elseif started && !has_key
      return idx
    end
  end
  return idx
end

function one_hot(element,list)
  o = zeros(length(list))
  o[findfirst(list,element)] = 1
  return o
end

function get_routes(files, training_proportion, num_input_stops, stops_ahead_to_predict, stops_to_predict, features, normalize=true)
  total_stops_needed = num_input_stops + stops_ahead_to_predict + stops_to_predict
  data = []
  for file in files
    data = [data; JSON.parsefile(file)]
  end

  # Let's get random
  shuffle(data)
  # Start from the 11th stop yo, seems to have the most coverage
  START_STOP = 11
  data = filter((x)->contiguous(x["arrival_times"],START_STOP) > total_stops_needed, data)
  #data = filter((x)->contiguous(x["traffic_estimates"],START_STOP+num_input_stops) >= stops_ahead_to_predict+1, data)
  N = length(data)
  bus_ids = sort(collect(Set([x["bus_id"] for x in data])))

  size_of_x = num_input_stops
  size_of_x += if ("day_of_week" in features) DAYS_IN_WEEK else 0 end
  size_of_x += if ("hour" in features) HOURS_IN_DAY else 0 end
  size_of_x += if ("bus_id" in features) length(bus_ids) else 0 end

  input_data = zeros(size_of_x,N)
  output_data = zeros(stops_to_predict,N)
  travel_time_data = zeros(num_input_stops,N)
  for (i,x) in enumerate(data)
    times = [x["arrival_times"][string(i)] for i in START_STOP:START_STOP+total_stops_needed]
    travel_times = diff(times)
    input_times = travel_times[1:num_input_stops]
    output_times = travel_times[num_input_stops+stops_ahead_to_predict+1:end]
    travel_time_data[:,i] = input_times
    output_data[:,i] = output_times
  end
  if normalize
    travel_time_data = (travel_time_data .- mean(travel_time_data,2))./std(travel_time_data,2);
  end
  for (i,x) in enumerate(data)
    day_encoding = "day_of_week" in features ? one_hot(x["day_of_week"],DAYS_OF_WEEK) : []
    hour_encoding = "hour" in features ? one_hot(x["hour"],HOURS_OF_DAY) : []
    bus_id_encoding = "bus_id" in features ? one_hot(x["bus_id"],bus_ids) : []
    #traffic_encoding = "traffic_estimates" in features ? [x["traffic_estimates"][string(i)] for i in START_STOP+num_input_stops:START_STOP+num_input_stops+stops_ahead_to_predict] : []
    input_data[:,i] = [travel_time_data[:,i]; day_encoding; hour_encoding; bus_id_encoding]
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


#file= "/Volumes/Infinity/mbta/h5/2014/mbta_trajectories_2014_15.json"
#routes = print(get_routes("/Users/Cooper/Desktop/mbta_trajectories_2014_15.json",0.8,5,0,1,["traffic_estimates"],true))

