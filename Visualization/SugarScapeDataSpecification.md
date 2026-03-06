# SugarScape Data Specification

## Design Principle
All data required for visualization is precomputed by the simulation.  
The visualization layer should not perform any additional simulation logic or derived calculations beyond basic rendering (i.e: If this boolean is true, draw this).

---

# Grid

**Agent ID and Sugar Count for each grid cell**.
**Maximum Grid Size Possible: 1000x1000**
## Format
LIBRARY_RUN#(Zero-padded to 6)_TIMESTEP(Zero-padded to 6)_GRID.csv

**Example**  
CILK_000001_000001_GRID.csv

## Data in File
row,col,sugarCount

## Notes
- sugarCount is the amount of sugar in the cell at the end of the timestep  
- Row and col are 0-indexed  

---

# Agents

## Format
LIBRARY_RUN#(Zero-padded to 6)_TIMESTEP(Zero-padded to 6)_AGENT.csv

**Example**  
CILK_000001_000001_AGENT.csv

## Data in File
agentID,row,col,wealth,age,deathAge,isMale,isFertile

## Notes
- Unique agentID is guaranteed  
- Row and col are unique for each agent  
- Row and col are 0-indexed  
- Agents that died this step will not show up in this timestep  
- wealth is the agent’s current wealth  
- age is the agent’s current age  
- deathAge is after how many timesteps an agent is guaranteed to die (age == deathAge → death)  
- isMale is a boolean indicator of sex  
- isFertile is a boolean indicator of whether the agent is within the fertility age range  

---

# Specific Visualizations

- If agent is fertile (isFertile = 1), a heart should be displayed on the agent model, blue if male, red if female  
- If the agent is NOT fertile (isFertile = 0), the heart as described above should be greyed out with the sex’s respective color outline  

---

# Meta

Contains constants (Properties set once and never changed)

## Format
LibraryName_RUN#(0-padded size 6)_META.csv

**Example**  
CILK_000001_META.csv

## Data in File
Height,width,timesteps,growthRate,sugarCapacityMin,sugarCapacityMax,initialAgentCount,metabolismMin,metabolismMax,visionMin,visionMax,deathAgeMin,deathAgeMax,fertilityAgeMin,fertilityAgeMax,reproThreshold,inheritanceFraction,initialWealth,seedSugar,seedMetabolism,seedVision,seedCoord,seedAge,seedSex,seedWealth

## Notes
- Height is the number of grid rows  
- width is the number of grid columns  
- timesteps is the total number of simulation timesteps executed  
- growthRate is the amount of sugar added to each cell per timestep, capped by that cell’s sugar capacity  
- sugarCapacityMin and sugarCapacityMax define the inclusive range used to initialize each cell’s maximum sugar capacity  
- initialAgentCount is the number of agents created at timestep 0  
- metabolismMin and metabolismMax define the inclusive range used to initialize each agent’s metabolism, which is the amount of wealth consumed per timestep  
- visionMin and visionMax define the inclusive range used to initialize each agent’s vision, which is the maximum Manhattan distance searched in the four cardinal directions  
- deathAgeMin and deathAgeMax define the inclusive range used to initialize each agent’s natural death age  
- fertilityAgeMin and fertilityAgeMax define the inclusive age range during which agents are eligible to reproduce  
- reproThreshold is the minimum wealth required for an agent to be eligible to reproduce  
- inheritanceFraction is the fraction of each parent’s wealth transferred to the offspring during reproduction, and this value is between 0 and 1  
- initialWealth is the starting wealth assigned to agents, and if set to a sentinel value such as UINT_MAX, wealth is randomly initialized based on the agent’s metabolism  
- seedSugar, seedMetabolism, seedVision, seedCoord, seedAge, seedSex, and seedWealth are the random number generator seeds used for initializing sugar, metabolism, vision, initial placement, age, sex, and wealth respectively  

---

# Timestep Data

Variables that don’t belong to grid or agent files, but still matter. Essentially, data gathered from grid and agent data.

## Format
LibraryName_RUN#(0-padded size 6)_TIMESTEP(0-padded size 6)_TIMESTEPCONSTANTS.csv

## Data in File
timestep,liveAgentCount,birthCount,deathCount,totalWealth,averageWealth,totalSugarOnGrid,conflictCount,meanVision,meanMetabolism,sexRatio,fertileCount,giniWealth

## Notes
- timestep is the current simulation timestep index corresponding to this record  
- liveAgentCount is the number of agents alive at the end of the timestep  
- birthCount is the number of new agents created during the timestep  
- deathCount is the number of agents removed during the timestep due to wealth depletion or reaching deathAge  
- totalWealth is the sum of wealth across all live agents at the end of the timestep  
- averageWealth is totalWealth divided by liveAgentCount, or 0 if liveAgentCount is 0  
- totalSugarOnGrid is the sum of sugarCount across all grid cells at the end of the timestep  
- conflictCount is the number of movement conflicts that occurred during target resolution in the timestep  
- meanVision is the average vision value across all live agents at the end of the timestep  
- meanMetabolism is the average metabolism value across all live agents at the end of the timestep  
- sexRatio is the fraction of live agents that are male, defined as maleCount divided by liveAgentCount  
- fertileCount is the number of live agents whose age is within the fertilityAgeMin to fertilityAgeMax range and whose wealth exceeds reproThreshold at the end of the timestep  
- giniWealth is the Gini coefficient computed over the wealth distribution of live agents at the end of the timestep, where 0 indicates perfect equality and values closer to 1 indicate higher inequality  

---

# Visualization Parameters

## Format
visualization_parameters.csv

## Data in File
gradientStartHex,gradientEndHex,showGridLine,gridLineHex,gridLineThickness

## Notes
- gradientStartHex & gradientEndHex define the range of the gradient used for visualizing the sugar count of the grid cells, where startHex is the cell color for minimum sugar, and endHex is for the cell with the most sugar  
- showGridLine is a boolean that determines whether the grid lines should be visible or not  
- gridLineHex & gridLineThickness determine the color and the thickness of the grid lines  
