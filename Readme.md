#Knapsack Solver
Python Version: 3.10.6
This repo includes both the solver instance and solver router logic.<br>

##Running tests
<b>Make sure docker is installed on your computer<br></b>
First run these 2 commands:<br>
* <code>docker run --rm -d --name rabbitmq -p 15672:15672 -p 15671:15671 -p 5672:5672 rabbitmq:3.8.7-management-alpine</code><br>
* <code>docker run --rm --name redis -p 6379:6379 -d redis</code>

Then, execute the following command(while on the repo dir):<br>
<code>pytest</code>

##Changing default ports
Take a look at <code>component_factory.py</code> to see what environment variables needs to be changed in order for this component to work properly.

##Running with docker
Make sure you have docker installed
* clone the subscription handler repository: <url>https://github.com/avivaloni10/subscriptions_handler</url>
* <code>cd</code> into the cloned directory.
* execute <code>docker build -t driveup-subscription-handler:0.0.1 .</code>
* <code>cd</code> into the knapsack-solver project directory.
* execute <code>docker build -t knapsack-engine:0.0.1 .</code>
* execute <code>docker-compose up -d</code>
  * If you wish to stop the dockers, execute: <code>docker-compose down</code>