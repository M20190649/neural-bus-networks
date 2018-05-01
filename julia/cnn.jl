using Knet
function cnn(w,x)
  n = length(w)-4
  for i=1:2:n
    x = pool(max(0, convolve(w[i],x) .+ w[i+1]))
  end
  x = mat(x)
  for i=n+1:2:length(w)-2
    x = max(0, w[i] * x .+ w[i+1])
  end
  return w[end-1] * x .+ w[end]
end

loss(w,x,y)=0.5*(sum((y-cnn(w,x)).^2) / size(x,2))
lossgradient = grad(loss);
function wcnn(n)
    # 
    wcnn=map(Array{Float32}, [ 0.1*randn(5,1,1,20),  zeros(1,20,1), 
                               0.1*randn(5,20,50), zeros(1,1,50,1),
                               0.1*randn(50,80),  zeros(50,1),
                               0.1*randn(n,50),  zeros(n,1) ]);
end

a = 0.1*randn(5,20)
x = 0.1*rand(5)
function convolve(w,x)
  return [conv(w[:,i],x) for i in 1:size(w)[2]-1]
end

println(convolve(a,x))
#println(conv(a[:,1],x))
