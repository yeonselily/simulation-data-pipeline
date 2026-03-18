# Tuberculosis

The purpose of the simulation is to model the interaction between Mycobacterium Tuberculosis and the immune system’s response inside a human lung.

Tuberculosis bacteria in the center grow every 10 days while macrophage and t-cells enter through the blood vessels to cooperate and kill bacteria.

## Running the Program

To build and run the Tuberculosis application, first run `make develop`. Once the development environment is setup, run `make build` and then `make test` to ensure all tests are passing properly. Once built, a `Tuberculosis` executable will be placed within the `./bin` directory, and can be used to run the simulation.

Running the application with the `--help` flag will provide a description of the application and options that can be used to define simulation parameters.

Specifying an output interval, by using the `--interval` flag will tell the program to output the simulation to a `.viz` file every `<interval>` steps. This simulation file can be played using the MASS SimViz application for a graphical visualization of the simulation space. To build the simviz application, run `make build-simviz`.

In the examples below, each environmentPlace is represented by a 2 by 2 grid. The top left pixel represents bacteria (navy blue if present). The top right pixel represents the macrophage (resting - green, infected - yellow, activated - light blue, chronically infected - dark purple). The bottom left pixel represents tcells (bright blue if present). The bottom right pixel represents the chemokine level (1 - orange, 2 - red).

_Example output with a simulation space of 40x40_


![Tuberculosis (40x40)](./img/tuberculosis_40x40.gif)


```
## Command to reproduce the above simulation
/bin/Tuberculosis --size=40 --total_days=100 --init_macro_num=2 --seed=1663480004 --interval=1
```

_Example output with a simulation space of 100x100_

![Tuberculosis (100x100)](./img/tuberculosis_100x100.gif)

```
## Command to reproduce the above simulation
./bin/Tuberculosis --size=100 --total_days=500 --init_macro_num=2 --seed=1680577073 --interval=5
```

python3 /home/NETID/seyeon/simulation-data-pipeline/Tuberculosis/tb_viz_to_csv.py \
  /home/NETID/seyeon/simulation-data-pipeline/Tuberculosis/tuberculosis.viz \
  /home/NETID/seyeon/simulation-data-pipeline/Tuberculosis/tb_csv \
  1