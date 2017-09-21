using MAT
using Winston
using HDF5

############################################################
# Load Bus Data
############################################################


total_stops = 22

vars = matread("full_routes.mat")

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

println("N: ",N)

travel_times = zeros(total_stops-1,N)
for j in 1:N
  full_route = view(full_routes,:,j)

  times = convert(Array{Float64},[x["time"]-full_route[1]["time"] for x in full_route])
  deltas = diff(times)
  travel_times[:,j] = deltas
end


num_training_points = round(Int,N*8/10)

average_travel_times = mean(travel_times,2)
sd_travel_times = std(travel_times,2)
println(average_travel_times)
println(maximum(travel_times,2))
println(sd_travel_times)


p=FramedPlot()
setattr(p,"title","Travel Times Vs Stop Number");
setattr(p,"xlabel","Bus Stop Number");
setattr(p,"ylabel","Travel Time (sec)");
c1 = Curve(1:length(average_travel_times),average_travel_times, "color","purple")
add(p,c1)
MyLegend=Legend(0.5, 0.9, [c1])
add(p,MyLegend)
savefig(p,string("travel_times.png"))

p=FramedPlot()
setattr(p,"title","Standard Deviation in Travel Times Vs Stop Number");
setattr(p,"xlabel","Bus Stop Number");
setattr(p,"ylabel","Standard Deviation (sec)");
c1 = Curve(1:length(sd_travel_times),sd_travel_times, "color","green")
add(p,c1)
MyLegend=Legend(0.5, 0.9, [c1])
add(p,MyLegend)
savefig(p,string("travel_times_sd.png"))
