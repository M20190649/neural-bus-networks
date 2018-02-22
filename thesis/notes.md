## Bus arrival time prediction using artificial neural network model

* ATIS: Advanced Traveler Information Systems
* ITS: Intelligent Transportation Systems

* consider traffic congestion and dwell times
* Chien et al developed an artificial neural network model to predict dynamic bus arrival time [2]. They stated that the back-propagation algorithm, which is the most used algorithm for transportation problems, is hard to apply Online due to the lengthy learning process. Consequently, they developed an adjustment factor to modify travel time prediction with new input of real-time data.
* 6 months of data

* provides time, speed, heading, etc as well as bus location
* Time checkpoint: schedule adherence
340 buses: 240 training, 100 validation

* The input variables are arrival time, dwell time, and schedule adherence at each stop
* In order to consider traffic congestion, the schedule adherence was calculated by subtracting the scheduled arrival time from the actual arrival time

### Historical Model

* For example, model 1 uses the input data from stop 1 (i.e. arrival time, dwell time, and schedule adherence) and predicts the arrival times at stops 2 through 9. In contrast, model 5 uses the input data from the first five stops and predicts arrival times at stops 6 through 9.
Tit=Ai+1,t−(Ait+Dit),forall i=M,N,forall y=1,T

### Regression Model

* Reg.1:TMik=b0+b1DMk
* Reg.2:TMik=b0+b1D2Mk
* Reg.3:TMik=b0+b1D2Mk+b2SMk
* Reg.4:TMik=b0+b1D2Mk+b2S2Mk
* Reg.5:TMik=b0+b1DMk+b2D2Mk+b3SMK


### Neural Networks

* Hyperbolic Tangent Sigmoid
* 15 nuerons
* 1 hidden layer
* The average MAPE of the Bayesian Regularization training function is slightly less than that of the Levenberg-Marquardt Backpropagation training function. However, the running time of the Bayesian Regularization training function was far more than that of the Levenberg-Marquardt Backpropagation training function.
* mean absolute percentage error

### Evaluation

* Clustering is not a siginificant helper for NN
![alt text](http://ieeexplore.ieee.org/mediastore/IEEE/content/media/9625/30418/1399041/1399041-fig-3-small.gif "Graph")


## Dynamic Bus Arrival Time Prediction with Artificial Neural Networks

### Model

One Bus
low variation in route
sensitivity to fluctuations beyond mean
eg season, day of week
which time of day

## 2/23
Seasonailty, correlation of bus route
Study seasonality effects
Something novel
Exploratory
Early or late depending on season (time of day, day of week, season of year)
Correlating bus arrival times with schedule
Periodicity and effect, phase of oscillation
24 hr variation is largest effect
Predict early or lateness w/ neural net
Important modes of variation
Phase relative to every 24 hours
Time delta, early or late performance


hdf5
scheduling jobs on cluster
grid engine
start from scratch.
state of the art now


# Talk with Deniz
knet
flux
gaussian processes
Liquid/echo state machine/network

# Cool papers
Deep Learning for Bus Passenger Demand Prediction Using Big Data

# Autodiff
https://alexey.radul.name/ideas/2013/introduction-to-automatic-differentiation/
