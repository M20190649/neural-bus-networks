using JSON

DAYS_IN_WEEK = 7
DAYS_OF_WEEK = 0:6
HOURS_OF_DAY = 0:23
HOURS_IN_DAY = 24

function contiguous(x, start)
  idx = 0
  started = false
  str = string("stop_",start)
  has_key = haskey(x,str)
  if !has_key
    return 0
  end
  for i in start:28
    str = string("stop_",i)
    #println(str)
    has_key = haskey(x,str)
    if !started && has_key
      started = true
      idx+=1
    elseif started && has_key
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

function get_routes(file, training_proportion, num_input_stops, stops_ahead_to_predict, stops_to_predict, features, normalize=true)
  total_stops_needed = num_input_stops + stops_ahead_to_predict + stops_to_predict
  data = JSON.parsefile(file)
  # Let's get random
  shuffle(data)
  LENGTH_CUTOFF = 20
  data = filter((x)->length(x)>LENGTH_CUTOFF,data)
  # Start from the 11th stop yo, seems to have the most coverage
  START_STOP = 11
  data = filter((x)->contiguous(x,START_STOP) > total_stops_needed, data)
  N = length(data)
  bus_ids = sort(collect(Set([x["bus_id"] for x in data])))
  size_of_x = num_input_stops
  println(size_of_x)
  println(stops_to_predict)
  if "day_of_week" in features
    size_of_x += DAYS_IN_WEEK
  end
  if "hour" in features
    size_of_x += HOURS_IN_DAY
  end
  if "bus_id" in features
    size_of_x += length(bus_ids)
  end
  input_data = zeros(size_of_x,N)
  output_data = zeros(stops_to_predict,N)
  travel_time_data = zeros(num_input_stops,N)
  println(size(input_data))
  println(size(output_data))
  for (i,x) in enumerate(data)
    times = x["arrival_times"]
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
    day_encoding =[]
    hour_encoding =[]
    bus_id_encoding =[]
    if "day_of_week" in features
      day_encoding = one_hot(x["day_of_week"],DAYS_OF_WEEK)
    end
    if "hour" in features
      hour_encoding = one_hot(x["hour"],HOURS_OF_DAY)
    end
    if "bus_id" in features
      bus_id_encoding = one_hot(x["bus_id"],bus_ids)
    end
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
#routes = get_routes("/Users/Cooper/Desktop/mbta_trajectories_2014_13.json",0.8,9,1,2,["day_of_week","bus_id","hour"],true);
